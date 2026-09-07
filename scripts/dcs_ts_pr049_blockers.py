#!/usr/bin/env python
"""DCS-PR-049 BLOCKING pre-analysis items Y1, Y2, Y3.  CPU only.

configs/dcs_ts_pr049.json declares three items as `blocking: true, done: false`:

  Y1  recompute the power analysis for a 2-WAY estimator at chance 0.5 on 23 TEST
      domains.  PR-048's analysis (scripts/dcs_ts_power.py) is a 3-WAY analysis at
      chance 1/3 and DOES NOT TRANSFER.
  Y2  re-derive the hedge-free stratum row counts on ts116m.  The 115/212/195 figures
      quoted in the preregistration were measured on the SUPERSEDED ts116n corpus and
      may not be quoted.
  Y3  re-measure the hedge-only / register-only / length-only baselines RESTRICTED to
      knife-vs-gun on ts116m, and evaluate the preregistered KILL CONDITION.

No GPU, no model weights, no SLURM, no network.  The Llama tokenizer is loaded from the
local HF cache with HF_HUB_OFFLINE=1 purely to count tokens (Y3d); if it is unavailable
the token check FAILS rather than silently falling back to characters.

DISCIPLINE (this repository has shipped four verifier harnesses whose checks passed over
empty sets, and twice published a threshold that no code path ever read):
  * every check binds to a COUNTED set and a check that binds zero rows is a FAIL;
  * every number is re-derived from the RAW bank JSONL rows -- never from a
    producer-written summary field (`n_concept_occurrences`, `n_chars`, `_meta.json`);
  * every gate value (alpha, n_perm, chance, the grids, the split, the population
    filters, the kill threshold) is fetched through Prereg.require(), which refuses
    rather than defaulting;
  * splits are DOMAIN-GROUPED and the disjointness assertion is itself mutated;
  * `--mutate` demonstrates each check going RED under a deliberate defect.

usage:
    python scripts/dcs_ts_pr049_blockers.py
    python scripts/dcs_ts_pr049_blockers.py --mutate
    python scripts/dcs_ts_pr049_blockers.py --reps 200 --json OUT.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from collections import Counter, OrderedDict, defaultdict

import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

# The preregistration loader (enforces FROZEN status and every pinned hash) and the
# PR-048 power machinery.  REUSED, not re-implemented: t_mde / t_power / sign_power /
# perm_p / clopper_pearson are the same estimators PR-048's analysis rests on, so a
# difference between the 3-way and the 2-way numbers is a difference of DESIGN, not of
# arithmetic.
from dcs_ts_prereg import PreregError, load as load_prereg           # noqa: E402
import dcs_ts_power as P                                             # noqa: E402

BANKDIR = os.path.join(REPO, "data", "boombness_prompts")
PR049 = "configs/dcs_ts_pr049.json"
PR048 = "configs/dcs_ts_pr048.json"

# --- the narrow five-family hedge definition -------------------------------------
# READ OUT OF THE EXISTING AUDIT SCRIPTS, NOT INVENTED HERE.  Identical (modulo the
# `\b` on `drills?`, which both spellings carry) to:
#   scripts/dcs_ts116n_audit_leakage.py::HEDGE_PATTERNS
#   scripts/dcs_ts116m_audit_concept_backing.py::HEDGE_NARROW
# and to the five families quoted in configs/dcs_ts_pr049.json's _register_asymmetry
# block: resembl*, simulat*, drill, false alarm, looks like.
HEDGE_PATTERNS = OrderedDict([
    ("resembl", re.compile(r"resembl\w*", re.IGNORECASE)),
    ("simulat", re.compile(r"simulat\w*", re.IGNORECASE)),
    ("drill", re.compile(r"\bdrills?\b", re.IGNORECASE)),
    ("false_alarm", re.compile(r"false alarm", re.IGNORECASE)),
    ("looks_like", re.compile(r"look(s|ed|ing)? like", re.IGNORECASE)),
])
# cross-check against the audit script's own source, so a drift there is visible here
HEDGE_SOURCE_FILES = ["scripts/dcs_ts116n_audit_leakage.py",
                      "scripts/dcs_ts116m_audit_concept_backing.py"]

PUNCT_CHARS = [",", ".", ";", ":", "-", "'", '"', "(", "?"]
_WORD_RE = re.compile(r"[A-Za-z']+")
_SENT_SPLIT = re.compile(r"[.!?]+\s|\n")

CODEWORDS = ("button", "basket")
ALL_CONCEPTS = ("bomb", "knife", "gun")


class ZeroBinding(RuntimeError):
    """Raised whenever a computation would evaluate over an empty set."""


def require_nonempty(n, what):
    if not n:
        raise ZeroBinding("BOUND ZERO ROWS: %s" % what)
    return n


class Checks(object):
    def __init__(self):
        self.rows = OrderedDict()

    def add(self, name, claim, ok, n_bound, detail=""):
        """A check that bound zero rows is a FAIL, never a PASS."""
        if not n_bound:
            ok = False
            detail = "BOUND ZERO ROWS (vacuous check) -- " + str(detail)
        self.rows[name] = dict(claim=claim, ok=bool(ok), n_bound=int(n_bound or 0),
                               detail=str(detail))
        return ok

    @property
    def n_fail(self):
        return sum(0 if r["ok"] else 1 for r in self.rows.values())

    def report(self, fh=sys.stdout):
        for k, r in self.rows.items():
            fh.write("  [%s] %-9s n=%-6d %s\n"
                     % ("PASS" if r["ok"] else "FAIL", k, r["n_bound"], r["claim"]))
            if r["detail"]:
                fh.write("            %s\n" % r["detail"])


# ================================================================= population
def bank_path(family, codeword, concept):
    return os.path.join(BANKDIR, "boombness_prompt_bank_%s_%s_%s.jsonl"
                        % (family, codeword, concept))


def load_probe_rows(pr, mut=None):
    """Bind the PR-049 probe population from RAW bank rows.

    Every selector comes from the preregistration through require().  The cell is
    selected on the FIELD `cell`, per the preregistration's _cell_note; whether the
    `condition` spelling would have bound the same rows on THIS corpus is measured
    separately by POP-03 rather than assumed either way.
    """
    family = pr.require("population", "bank_family")
    cell = pr.require("population", "cell")
    qk = pr.require("population", "query_kind_primary")
    nex = pr.require("population", "n_examples_primary")

    excluded = set()
    for ex in pr.require("population", "preregistered_exclusions"):
        if "ENTIRE analysis population" in ex.get("scope", ""):
            excluded.add(ex["domain"])
    if mut == "keep_excluded_domains":
        excluded = set()

    sel_field, sel_val = "cell", cell
    nex_ok = (lambda v: v == nex)
    if mut == "pool_doses":
        nex_ok = (lambda v: v in (nex, pr.require("population", "n_examples_replication")))
    if mut == "empty_population":
        sel_field, sel_val = "cell", "Z"

    rows, n_excluded = [], 0
    for cw in CODEWORDS:
        for cc in ALL_CONCEPTS:
            p = bank_path(family, cw, cc)
            if not os.path.exists(p):
                raise ZeroBinding("bank file missing: %s" % p)
            with open(p) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    r = json.loads(line)
                    if r.get(sel_field) != sel_val:
                        continue
                    if r.get("query_kind") != qk or not nex_ok(r.get("n_examples")):
                        continue
                    if r["domain"] in excluded:
                        n_excluded += 1
                        continue
                    # re-derive, never trust: concept/codeword come from the FILE we
                    # opened, not from the row's self-description
                    d = dict(domain=r["domain"], concept=cc, codeword=cw,
                             prompt_id=r["prompt_id"], bank_block=r.get("bank_block"),
                             demo_block=r["demo_block"], full_prompt=r["full_prompt"],
                             family_slot=r.get("family_slot"))
                    if r["demo_block"] not in r["full_prompt"]:
                        raise ZeroBinding("demo_block is not a substring of full_prompt "
                                          "in %s -- the corpus is not what this script "
                                          "believes it is" % r["prompt_id"])
                    if mut == "hedge_leak" and cc == "gun":
                        d["demo_block"] = d["demo_block"] + " It resembled a device."
                        d["full_prompt"] = d["full_prompt"] + " It resembled a device."
                    rows.append(d)
    return rows, n_excluded, sorted(excluded)


def load_split(pr, mut=None):
    manifest = os.path.join(REPO, pr.require("split", "manifest"))
    field = pr.require("split", "field")
    with open(manifest) as fh:
        m = json.load(fh)
    if m.get("field_name") != field:
        raise ZeroBinding("split manifest field_name %r != preregistered %r"
                          % (m.get("field_name"), field))
    assign = dict(m["assign"])
    require_nonempty(len(assign), "split manifest assign")
    if mut == "corrupt_split":
        # five TEST domains also declared TRAIN: the groups overlap
        te = sorted(d for d, s in assign.items() if s == "test")[:5]
        for d in te:
            assign[d] = "train"
            assign[d + "__ghost"] = "test"
    return m, assign


# ================================================================= features
def hedge_counts(t):
    return [float(len(p.findall(t))) for p in HEDGE_PATTERNS.values()]


def has_hedge(t):
    return any(p.search(t) for p in HEDGE_PATTERNS.values())


def register_features_lengthfree(t):
    """Register with every LENGTH channel removed: composition only.

    register_features() carries mean sentence length, sentence count and word count,
    all of which are length.  If the register advantage were simply length wearing a
    different name, this variant would collapse toward chance.  Punctuation is
    normalised per word for the same reason.
    """
    words = _WORD_RE.findall(t.lower())
    n_words = max(len(words), 1)
    feats = [float(sum(hedge_counts(t))) / n_words,
             len(set(words)) / float(n_words),
             float(np.mean([len(w) for w in words])) if words else 0.0]
    feats += [float(t.count(c)) / n_words for c in PUNCT_CHARS]
    feats += [float(sum(ch.isdigit() for ch in t)) / n_words,
              float(sum(ch.isupper() for ch in t)) / n_words]
    return feats


def register_features(t):
    """Surface register: hedge count, mean sentence length, TTR, punctuation counts."""
    sents = [s for s in _SENT_SPLIT.split(t) if s.strip()]
    words = _WORD_RE.findall(t.lower())
    n_words = max(len(words), 1)
    feats = [float(sum(hedge_counts(t))),
             float(np.mean([len(s) for s in sents])) if sents else 0.0,
             float(len(sents)),
             float(len(words)),
             len(set(words)) / float(n_words),
             float(np.mean([len(w) for w in words])) if words else 0.0]
    feats += [float(t.count(c)) for c in PUNCT_CHARS]
    feats += [float(sum(ch.isdigit() for ch in t)),
              float(sum(ch.isupper() for ch in t))]
    return feats


def fit_eval_2way(rows_tr, rows_te, featfn, pos_class, seed=0, mut=None):
    """Domain-grouped 2-way baseline.  Standardiser fit on TRAIN domains only (D1)."""
    require_nonempty(len(rows_tr), "baseline train rows")
    require_nonempty(len(rows_te), "baseline test rows")
    tr_d = set(r["domain"] for r in rows_tr)
    te_d = set(r["domain"] for r in rows_te)
    if tr_d & te_d:
        raise ZeroBinding("TRAIN and TEST share %d domain(s) -- a domain's rows were "
                          "split across the boundary: %s"
                          % (len(tr_d & te_d), sorted(tr_d & te_d)[:5]))
    Xtr = np.asarray([featfn(r) for r in rows_tr], dtype=float)
    Xte = np.asarray([featfn(r) for r in rows_te], dtype=float)
    ytr = np.asarray([r["concept"] for r in rows_tr])
    yte = np.asarray([r["concept"] for r in rows_te])
    if len(set(ytr)) != 2 or len(set(yte)) != 2:
        raise ZeroBinding("a 2-way baseline needs exactly 2 classes, got train=%s test=%s"
                          % (sorted(set(ytr)), sorted(set(yte))))
    sc = StandardScaler()
    A = sc.fit_transform(Xtr)
    B = sc.transform(Xte)
    clf = LogisticRegression(max_iter=4000, random_state=seed)
    clf.fit(A, ytr)
    pred = clf.predict(B)
    proba = clf.predict_proba(B)
    j = list(clf.classes_).index(pos_class)
    acc = float(accuracy_score(yte, pred))
    auc = float(roc_auc_score((yte == pos_class).astype(int), proba[:, j]))
    per = defaultdict(list)
    for r, p, t in zip(rows_te, pred, yte):
        per[r["domain"]].append(1.0 if p == t else 0.0)
    dom = {d: float(np.mean(v)) for d, v in per.items()}
    return dict(acc=acc, advantage=acc - 0.5, auroc=auc,
                domain_mean_acc=float(np.mean(list(dom.values()))),
                n_train=len(rows_tr), n_test=len(rows_te),
                n_train_domains=len(tr_d), n_test_domains=len(te_d),
                n_features=int(Xtr.shape[1]),
                class_balance_test=dict(Counter(yte.tolist())),
                per_domain=dom)


# ================================================================= Y1
def two_way_sign_floor(n):
    """Attainable two-sided p of an exact sign test at p0=0.5 with n domains."""
    return P.sign_floor_two_sided(n)


def sign_floor_bruteforce_2way(n):
    """Independent re-derivation: enumerate all 2^n sign patterns and take the
    two-sided tail mass of the most extreme outcome."""
    if n > 24:
        raise ValueError("brute force only for n<=24")
    total = 1 << n
    cnt = sum(1 for mask in range(total) if bin(mask).count("1") in (0, n))
    return cnt / float(total)


def simulate_pipeline_2way(n_domains=114, n_train=68, n_val=23, n_test=23,
                           n_per_concept=20, dim=8, layer_grid=(6, 7, 8, 9, 10, 11, 12, 13, 14),
                           c_grid=(0.01, 0.1, 1.0, 10.0), tau_domain=1.0, tau_group=1.2,
                           n_perm=200, rng=None, perm_unit="group",
                           arm="validation", chance=0.5):
    """One replicate of the FULL 2-way pipeline on PURE-NOISE features.

    No concept signal exists anywhere.  Features carry a domain random effect (shared by
    every row of a domain at every layer) and a (layer, domain, concept) group random
    effect -- the nuisance structure the real bank has, since all rows of one concept in
    one domain share a demonstration pool.  The selection grid is the REAL one from the
    preregistration: |layer_grid| x |C_grid| candidates, selected on VALIDATION.

    A correctly calibrated pipeline must reject at ~alpha.
    """
    rng = rng or np.random.default_rng(0)
    doms = np.arange(n_domains)
    rng.shuffle(doms)
    tr, va, te = doms[:n_train], doms[n_train:n_train + n_val], \
        doms[n_train + n_val:n_train + n_val + n_test]
    require_nonempty(te.size, "simulated test domains")

    n_rows = n_domains * 2 * n_per_concept
    y = np.tile(np.repeat(np.arange(2), n_per_concept), n_domains)
    g = np.repeat(np.arange(n_domains), 2 * n_per_concept)
    u = rng.normal(0, tau_domain, size=(n_domains, dim))
    Xs = []
    for _L in layer_grid:
        v = rng.normal(0, tau_group, size=(n_domains, 2, dim))
        Xs.append(u[g] + v[g, y] + rng.normal(0, 1.0, size=(n_rows, dim)))

    mtr, mva, mte = np.isin(g, tr), np.isin(g, va), np.isin(g, te)
    require_nonempty(int(mtr.sum()), "simulated train rows")
    require_nonempty(int(mte.sum()), "simulated test rows")

    def per_domain_acc(pred, ytrue, gg, ds):
        out = []
        for d in ds:
            sel = gg == d
            if sel.sum() == 0:
                raise ZeroBinding("simulated domain %d bound zero rows" % d)
            out.append(float((pred[sel] == ytrue[sel]).mean()))
        return np.array(out)

    cands = {}
    for li in range(len(layer_grid)):
        X = Xs[li]
        mu, sd = X[mtr].mean(0), X[mtr].std(0)
        sd[sd < 1e-8] = 1.0
        Z = (X - mu) / sd
        for C in c_grid:
            clf = LogisticRegression(C=C, max_iter=1000)
            clf.fit(Z[mtr], y[mtr])
            cands[(li, C)] = dict(
                val=float(per_domain_acc(clf.predict(Z[mva]), y[mva], g[mva], va).mean()),
                test_pred=clf.predict(Z[mte]),
                test=float(per_domain_acc(clf.predict(Z[mte]), y[mte], g[mte], te).mean()))
    require_nonempty(len(cands), "candidate (layer, C) grid")

    y_te, g_te = y[mte], g[mte]
    key = "val" if arm == "validation" else "test"
    star = max(cands, key=lambda k: cands[k][key])
    pred_te = cands[star]["test_pred"]
    obs_pd = per_domain_acc(pred_te, y_te, g_te, te)
    obs = float(obs_pd.mean())
    null = np.empty(n_perm)
    for b in range(n_perm):
        if perm_unit == "group":
            y_perm = y_te.copy()
            for d in te:
                sel = g_te == d
                if rng.integers(2):                 # the 2! relabels of a 2-class arm
                    y_perm[sel] = 1 - y_te[sel]
        elif perm_unit == "row":                    # mutation: ignores intra-domain corr
            y_perm = rng.permutation(y_te)
        else:
            raise ValueError(perm_unit)
        null[b] = per_domain_acc(pred_te, y_perm, g_te, te).mean()
    return dict(p=P.perm_p(obs, null), obs=obs, cand=(layer_grid[star[0]], star[1]),
                n_candidates=len(cands),
                frac_domains_above_chance=float((obs_pd > chance).mean()))


def y1(pr, C, reps=200, n_perm=200, seed=20260907, mut=None, quick=False):
    alpha = pr.require("primary", "alpha")
    chance = pr.require("primary", "chance")
    n_perm_pre = pr.require("primary", "n_perm")
    n_test = pr.require("primary", "n_test_domains")
    lg = pr.require("read_site", "layer_grid")
    cg = pr.require("read_site", "C_grid")
    out = dict(alpha=alpha, chance=chance, n_perm_preregistered=n_perm_pre,
               n_test_domains=n_test)

    C.add("Y1-00", "the preregistered 2-way chance is 0.5 and PR-048's is 1/3, so the "
                   "PR-048 power analysis cannot be transferred",
          abs(chance - 0.5) < 1e-12, 1,
          "PR-049 chance=%.4f ; PR-048 chance=%.6f" % (chance, 1.0 / 3.0))

    # ---- (a) sign-test floor -----------------------------------------------------
    fl = two_way_sign_floor(n_test)
    bf = sign_floor_bruteforce_2way(n_test)
    out["sign"] = dict(n=n_test, floor_two_sided=fl, floor_bruteforce=bf,
                       floor_one_sided=P.sign_floor_two_sided(n_test, one_sided=True),
                       n_distinct_p_values=n_test + 1,
                       k_needed=min(k for k in range(n_test + 1)
                                    if k > n_test / 2.0
                                    and P.binom_test_two_sided(k, n_test, 0.5) <= alpha),
                       mde_pi=P.sign_mde(n_test),
                       by_n={n: dict(floor=two_way_sign_floor(n),
                                     k_needed=min(k for k in range(n + 1)
                                                  if k > n / 2.0
                                                  and P.binom_test_two_sided(k, n, 0.5) <= alpha),
                                     mde_pi=P.sign_mde(n))
                             for n in (12, 23, 29, 46)})
    C.add("Y1-a", "the two-sided sign-test floor at n=%d test domains is closed-form "
                  "2*0.5^n and agrees with brute-force enumeration of all 2^n patterns, "
                  "and is below alpha" % n_test,
          abs(fl - bf) < 1e-15 and fl < alpha, n_test,
          "floor=%.3e (brute force %.3e), alpha=%g, k needed = %d/%d, sign-test MDE "
          "pi=%.3f" % (fl, bf, alpha, out["sign"]["k_needed"], n_test, out["sign"]["mde_pi"]))

    # ---- (b) permutation floor ---------------------------------------------------
    perm = {}
    for B in (200, 2000, 10000):
        perm[B] = dict(floor=P.perm_floor(B), smallest_measured=2.0 / (B + 1.0),
                       floor_below_alpha=P.perm_floor(B) < alpha,
                       mc_se_at_p05=math.sqrt(0.05 * 0.95 / B))
    out["perm"] = perm
    ok_b = (n_perm_pre == 10000 and abs(perm[10000]["floor"] - 1.0 / 10001) < 1e-12
            and all(perm[B]["floor_below_alpha"] for B in perm))
    if mut == "perm_floor_naive":
        ok_b = (P.perm_floor(10000, naive=True) > 0)     # the naive estimator has floor 0
    C.add("Y1-b", "the permutation floor is 1/(B+1) at every B, and the preregistration "
                  "fixes B=10000 (floor 9.999e-05)",
          ok_b, len(perm),
          "B=200 -> %.6f ; B=2000 -> %.3e ; B=10000 -> %.4e ; primary.n_perm=%s"
          % (perm[200]["floor"], perm[2000]["floor"], perm[10000]["floor"], n_perm_pre))

    # ---- (c) MDE across a BRACKET of assumed between-domain SDs -------------------
    # There is NO 2-way per-domain accuracy anywhere in the record, so the SD is an
    # ASSUMPTION, not a measurement.  It is bracketed and every entry is labelled.
    m_rows = (pr.require("population", "rows_per_domain_per_concept")
              * len(pr.require("population", "concepts")) * len(CODEWORDS))
    sd_grid = OrderedDict([
        (0.05, "ASSUMPTION -- optimistic, tightly clustered domains"),
        (0.10, "ASSUMPTION -- moderate"),
        (0.1406, "ASSUMPTION -- PR-048's projected 3-WAY SD, carried over unchanged; "
                 "a 3-way SD is not a 2-way SD and this is a borrowed value"),
        (0.15, "ASSUMPTION -- pessimistic"),
        (0.20, "ASSUMPTION -- very pessimistic"),
        (0.25, "DISTRIBUTION-FREE CEILING for per-domain accuracies confined to "
               "[0.5,1]: max sample SD = (1-0.5)/2"),
        (0.3439, "ASSUMPTION -- PR-048's chi-square 95% upper bound on a SD estimated "
                 "from SIX domains; EXCEEDS the [0.5,1] ceiling, so it is only "
                 "attainable if some test domains fall BELOW chance"),
        (0.5, "DISTRIBUTION-FREE CEILING on [0,1]: half the domains at 0, half at 1"),
    ])
    # Holm across the two primaries: the later-tested member is read at alpha/1 only if
    # the other one already rejected; the CONSERVATIVE planning alpha is alpha/2.
    alpha_holm = alpha / 2.0
    mde = OrderedDict()
    for sd, why in sd_grid.items():
        row = dict(assumption=why,
                   mde_alpha05=P.t_mde(n_test, sd, alpha=alpha),
                   mde_alpha_holm=P.t_mde(n_test, sd, alpha=alpha_holm),
                   projected_sd_with_binomial_noise=math.sqrt(
                       sd ** 2 + 0.5 * 0.5 / m_rows))
        if mut == "mde_drop_beta":
            row["mde_alpha05"] = P.t_mde(n_test, sd, alpha=alpha, drop_beta=True)
        mde[sd] = row
    out["mde"] = dict(n_test=n_test, alpha=alpha, alpha_holm=alpha_holm, power=0.80,
                      m_rows_per_domain=m_rows, by_sd=mde,
                      _m_note="knife+gun, %d rows per domain per concept, both codewords"
                              % pr.require("population", "rows_per_domain_per_concept"))
    vals = [mde[s]["mde_alpha05"] for s in sd_grid]
    mono = all(vals[i] < vals[i + 1] for i in range(len(vals) - 1))
    C.add("Y1-c", "the MDE above 0.5 at alpha=%g, power 0.8, n=%d rises monotonically "
                  "with the assumed between-domain SD and every SD in the bracket is "
                  "declared an ASSUMPTION or a distribution-free ceiling" % (alpha, n_test),
          mono and all(v > 0 for v in vals), len(sd_grid),
          "MDE: sd=0.05 -> %.4f ; sd=0.1406 -> %.4f ; sd=0.25 (ceiling on [0.5,1]) -> "
          "%.4f ; sd=0.3439 -> %.4f | Holm alpha=%.4f: %.4f at the 0.25 ceiling"
          % (mde[0.05]["mde_alpha05"], mde[0.1406]["mde_alpha05"],
             mde[0.25]["mde_alpha05"], mde[0.3439]["mde_alpha05"],
             alpha_holm, mde[0.25]["mde_alpha_holm"]))

    # The MDE is only an MDE if the design actually has 80% power AT it.  Y1-c above
    # would pass for any monotone increasing function of the SD -- including one that
    # drops the type-II term, which is exactly how an MDE gets published 40% too small.
    attained = {("%.4f" % sd): P.t_power(n_test, mde[sd]["mde_alpha05"], sd, alpha=alpha)
                for sd in sd_grid}
    out["mde"]["attained_power_at_mde"] = attained
    ok_c2 = all(abs(v - 0.80) < 5e-3 for v in attained.values())
    C.add("Y1-c2", "each reported MDE ATTAINS 0.800 power by construction -- the "
                   "definition is round-tripped, not asserted",
          ok_c2, len(attained),
          "attained power at the reported MDE: min %.4f, max %.4f over %d SDs"
          % (min(attained.values()), max(attained.values()), len(attained)))

    # ---- (d) power curves over n_test --------------------------------------------
    n_list = (12, 23, 29, 46)
    deltas = (0.05, 0.075, 0.10, 0.15, 0.20, 0.25)
    curves = {}
    for sd in sd_grid:
        for n in n_list:
            for d in deltas:
                curves["%.4f|%d|%.3f" % (sd, n, d)] = P.t_power(n, d, sd, alpha=alpha)
    mde_n = {"%.4f|%d" % (sd, n): P.t_mde(n, sd, alpha=alpha)
             for sd in sd_grid for n in n_list}
    out["curves"] = dict(power=curves, mde=mde_n, n_list=list(n_list),
                         deltas=list(deltas), sd_list=list(sd_grid))
    # power must rise with n at fixed (sd, delta)
    rises = all(curves["%.4f|%d|%.3f" % (sd, n_list[i], d)]
                <= curves["%.4f|%d|%.3f" % (sd, n_list[i + 1], d)] + 1e-12
                for sd in sd_grid for d in deltas for i in range(len(n_list) - 1))
    C.add("Y1-d", "power rises monotonically with n_test in {12,23,29,46} at every "
                  "(SD, delta) in the bracket",
          rises, len(curves),
          "at sd=0.1406, delta=0.10: n=12 %.3f / n=23 %.3f / n=29 %.3f / n=46 %.3f"
          % tuple(curves["0.1406|%d|0.100" % n] for n in n_list))

    # ---- (e) FPR calibration on pure noise through the FULL pipeline --------------
    t0 = time.time()
    rng = np.random.default_rng(seed)
    perm_unit = "row" if mut == "row_level_permutation" else "group"
    arm = "test" if mut == "test_selected_hyperparams" else "validation"
    ps, obss, aboves = [], [], []
    ncand = None
    n_reps = min(100, reps) if quick else reps
    for _ in range(n_reps):
        r = simulate_pipeline_2way(rng=rng, n_perm=n_perm, perm_unit=perm_unit, arm=arm,
                                   layer_grid=lg, c_grid=cg, chance=chance,
                                   n_test=n_test)
        ps.append(r["p"]); obss.append(r["obs"]); aboves.append(r["frac_domains_above_chance"])
        ncand = r["n_candidates"]
    ps = np.asarray(ps)
    require_nonempty(ps.size, "FPR replicates")
    k = int((ps <= alpha).sum())
    lo, hi = P.clopper_pearson(k, n_reps)
    out["fpr"] = dict(reps=n_reps, n_perm=n_perm, n_candidates=ncand, arm=arm,
                      perm_unit=perm_unit, n_reject=k, fpr=k / float(n_reps),
                      ci95=(lo, hi), covers_nominal=bool(lo <= alpha <= hi),
                      median_p=float(np.median(ps)),
                      null_mean_obs_acc=float(np.mean(obss)),
                      mean_frac_domains_above_chance=float(np.mean(aboves)),
                      seconds=round(time.time() - t0, 1))
    C.add("Y1-e", "on PURE NOISE, the full 2-way pipeline (domain-grouped split, "
                  "%d-candidate grid selected on VALIDATION, domain-level group "
                  "permutation) rejects at the nominal alpha, and the null domain-mean "
                  "accuracy sits at chance 0.5" % (len(lg) * len(cg)),
          (out["fpr"]["covers_nominal"] and out["fpr"]["fpr"] <= 2 * alpha
           and abs(out["fpr"]["null_mean_obs_acc"] - 0.5) < 0.03),
          n_reps,
          "FPR %d/%d = %.4f, 95%% CI [%.4f, %.4f] (nominal %g); null mean acc %.4f; "
          "%d reps x %d perms in %.0fs"
          % (k, n_reps, k / float(n_reps), lo, hi, alpha,
             out["fpr"]["null_mean_obs_acc"], n_reps, n_perm, out["fpr"]["seconds"]))

    # ---- the CONJUNCTIVE success rule ---------------------------------------------
    # primary.success is a CONJUNCTION: "significantly above 0.5 by domain-level group
    # permutation AND above chance in a majority of test domains by two-sided sign
    # test".  Powering only the permutation arm overstates the design's power, because
    # the sign arm needs k>=17 of 23 domains and is the harsher requirement at large
    # between-domain SD.  Model per-domain accuracy as Normal(0.5+delta, sd); then the
    # per-domain probability of landing above chance is Phi(delta/sd) and the sign arm's
    # power is exact-binomial.  The two arms are positively correlated (both read the
    # same per-domain vector), so min() is an UPPER bound on the conjunction and the
    # product is a LOWER bound.  Both are reported; the verdict uses min(), the
    # generous one, so an inadequate call cannot be an artefact of the bound.
    def conj_power(n, delta, sd, a=alpha):
        pw_t = P.t_power(n, delta, sd, alpha=a)
        pi = float(stats.norm.cdf(delta / sd)) if sd > 0 else 1.0
        pw_s = P.sign_power(n, pi, 0.5, a)
        return dict(t_arm=pw_t, sign_arm=pw_s, pi=pi,
                    upper_bound=min(pw_t, pw_s), lower_bound=pw_t * pw_s)

    # Declared here, BEFORE any test read, exactly as the preregistration requires.
    # The bar: the co-primary must be able to detect an effect that would count as
    # evidence of concept identity.  The record's only anchor -- the old 3-way probe at
    # domain-mean 0.7485 against chance 1/3, i.e. +0.415 -- is far larger; the planning
    # bar taken here is deliberately much smaller, delta = +0.15, i.e. a domain-mean of
    # 0.65 on a 2-way contrast.
    bar_delta = 0.15
    # The only between-domain SD anchor anywhere in the record.  It is PR-048's
    # PROJECTED 3-WAY value, borrowed; there is no measured 2-way SD, and saying so is
    # part of the answer.
    sd_working = 0.1406
    sd_ceiling = 0.25                 # distribution-free ceiling on [0.5,1]

    conj = {sd: conj_power(n_test, bar_delta, sd) for sd in sd_grid}
    conj_holm = {sd: conj_power(n_test, bar_delta, sd, a=alpha_holm) for sd in sd_grid}

    # The SD at which the conjunction falls below 0.8 -- the point where this contrast
    # stops being a co-primary.  PR-048 already requires a TRAIN-only nested-LODO SD
    # measurement before the confirmatory run, so this breakpoint is CHECKABLE BEFORE
    # ANY TEST READ and is recorded here as a contingency, not as a hope.
    def breakpoint(a):
        lo, hi = 1e-4, 1.0
        if conj_power(n_test, bar_delta, lo, a)["upper_bound"] < 0.80:
            return float("nan")
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if conj_power(n_test, bar_delta, mid, a)["upper_bound"] >= 0.80:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    sd_break = breakpoint(alpha)
    sd_break_holm = breakpoint(alpha_holm)

    mde_work = mde[sd_working]["mde_alpha05"]
    mde_work_holm = mde[sd_working]["mde_alpha_holm"]
    powered = (conj[sd_working]["upper_bound"] >= 0.80
               and conj_holm[sd_working]["upper_bound"] >= 0.80
               and mde_work <= bar_delta
               and math.isfinite(sd_break))
    out["conjunctive_power"] = dict(
        bar_delta=bar_delta,
        at_alpha05={("%.4f" % s): conj[s] for s in sd_grid},
        at_alpha_holm={("%.4f" % s): conj_holm[s] for s in sd_grid},
        sd_breakpoint_alpha05=sd_break, sd_breakpoint_holm=sd_break_holm,
        _note="min() is an upper bound on the conjunction, the product a lower bound")
    out["verdict"] = dict(
        call="CO-PRIMARY" if powered else "EXPLORATORY",
        bar_delta=bar_delta,
        sd_working_assumption=sd_working,
        sd_working_provenance="PR-048's PROJECTED 3-WAY between-domain SD, borrowed. "
                              "There is NO measured 2-way per-domain accuracy anywhere "
                              "in the record; this is an assumption, not a measurement.",
        sd_distribution_free_ceiling=sd_ceiling,
        mde_at_working_sd=mde_work, mde_at_working_sd_holm=mde_work_holm,
        mde_at_ceiling_sd=mde[sd_ceiling]["mde_alpha05"],
        mde_at_ceiling_sd_holm=mde[sd_ceiling]["mde_alpha_holm"],
        conjunctive_power_at_working_sd=conj[sd_working]["upper_bound"],
        conjunctive_power_at_working_sd_holm=conj_holm[sd_working]["upper_bound"],
        conjunctive_power_at_ceiling_sd=conj[sd_ceiling]["upper_bound"],
        sign_test_pi_needed_for_80pct=out["sign"]["mde_pi"],
        sign_test_k_needed=out["sign"]["k_needed"],
        binding_arm=("sign test" if conj[sd_working]["sign_arm"] < conj[sd_working]["t_arm"]
                     else "permutation/t"),
        flip_to_exploratory_if="the TRAIN-only nested-LODO between-domain SD of the "
                               "knife-vs-gun per-domain accuracies exceeds %.3f "
                               "(%.3f under the Holm-corrected alpha). PR-048 already "
                               "requires that TRAIN-only SD measurement before the "
                               "confirmatory run, so this is checkable before any TEST "
                               "read." % (sd_break, sd_break_holm),
        adequately_powered_as_coprimary=bool(powered))
    C.add("Y1-V", "VERDICT: at n=%d the knife-vs-gun contrast clears 0.8 power for a "
                  "delta of +%.2f under the CONJUNCTIVE success rule (permutation AND "
                  "sign test) at the working between-domain SD, at both alpha=%g and "
                  "the Holm-corrected alpha=%.3f -- so it is declared CO-PRIMARY, with "
                  "a TRAIN-checkable SD breakpoint at which it flips to EXPLORATORY"
                  % (n_test, bar_delta, alpha, alpha_holm),
          powered, n_test,
          "at sd=%.4f (BORROWED 3-way assumption): MDE=%.4f (Holm %.4f), conjunctive "
          "power %.3f (t arm %.3f, sign arm %.3f; Holm %.3f) | at the [0.5,1] ceiling "
          "sd=%.2f: MDE=%.4f, conjunctive power %.3f -- BELOW 0.8, and the binding arm "
          "is the sign test needing k>=%d/%d | breakpoint sd=%.3f (Holm %.3f)"
          % (sd_working, mde_work, mde_work_holm, conj[sd_working]["upper_bound"],
             conj[sd_working]["t_arm"], conj[sd_working]["sign_arm"],
             conj_holm[sd_working]["upper_bound"], sd_ceiling,
             mde[sd_ceiling]["mde_alpha05"], conj[sd_ceiling]["upper_bound"],
             out["sign"]["k_needed"], n_test, sd_break, sd_break_holm))
    return out


# ================================================================= Y2
def y2(pr, C, rows, assign, mut=None):
    """Hedge-free stratum, re-derived on ts116m from raw demonstration blocks."""
    dead = [k for k, p in HEDGE_PATTERNS.items()
            if not any(p.search(r["demo_block"]) for r in rows)]
    if mut == "dead_hedge_lexicon":
        dead = list(HEDGE_PATTERNS)
    live_hits = sum(1 for r in rows if has_hedge(r["demo_block"]))
    C.add("Y2-live", "all five narrow hedge families (resembl*, simulat*, drill, "
                     "false alarm, looks like) are LIVE on the ts116m probe population "
                     "-- a hedge-free count computed from a dead lexicon is vacuous",
          not dead and live_hits > 0, live_hits,
          ("DEAD families: %s" % dead) if dead else
          "%d/%d probe rows carry >=1 hedge in their demonstration block"
          % (live_hits, len(rows)))

    def strat(split_name):
        sel = [r for r in rows if assign.get(r["domain"]) == split_name]
        require_nonempty(len(sel), "%s-split probe rows" % split_name)
        per = {}
        for c in ALL_CONCEPTS:
            cr = [r for r in sel if r["concept"] == c]
            free = [r for r in cr if not has_hedge(r["demo_block"])]
            fd = Counter(r["domain"] for r in free)
            per[c] = dict(n_rows=len(cr), n_hedge_free=len(free),
                          pct_hedge_free=100.0 * len(free) / max(len(cr), 1),
                          n_domains=len(set(r["domain"] for r in cr)),
                          n_domains_with_any_hedge_free=len(fd),
                          rows_per_domain=dict(fd))
        return per, sel

    test_per, test_rows = strat("test")
    train_per, _ = strat("train")

    # domain-level feasibility: a domain is usable only if EVERY concept in the contrast
    # has at least one hedge-free row there.  A stratum that exists only at row level is
    # not usable at the domain level, which is the independence unit.
    def usable_domains(concepts):
        ds = None
        for c in concepts:
            have = set(d for d, n in test_per[c]["rows_per_domain"].items() if n > 0)
            ds = have if ds is None else (ds & have)
        return sorted(ds or [])

    kg = usable_domains(("knife", "gun"))
    bkg = usable_domains(ALL_CONCEPTS)
    bal_rows_2way = 2 * min(test_per["knife"]["n_hedge_free"], test_per["gun"]["n_hedge_free"])
    bal_rows_3way = 3 * min(test_per[c]["n_hedge_free"] for c in ALL_CONCEPTS)

    # domain-balanced N: within each usable domain, take min over concepts
    def balanced_rows_over_domains(concepts, doms):
        return sum(len(concepts) * min(test_per[c]["rows_per_domain"].get(d, 0)
                                       for c in concepts) for d in doms)

    out = dict(test=test_per, train=train_per,
               n_test_domains=len(set(r["domain"] for r in test_rows)),
               n_test_rows=len(test_rows),
               superseded_figures_not_quoted=dict(bomb=115, knife=212, gun=195,
                                                  corpus="ts116n (SUPERSEDED)"),
               knife_gun_usable_domains=kg, n_knife_gun_usable_domains=len(kg),
               all3_usable_domains=bkg, n_all3_usable_domains=len(bkg),
               balanced_usable_N_rowlevel_2way=bal_rows_2way,
               balanced_usable_N_rowlevel_3way=bal_rows_3way,
               balanced_usable_N_domainbalanced_2way=balanced_rows_over_domains(
                   ("knife", "gun"), kg),
               balanced_usable_N_domainbalanced_3way=balanced_rows_over_domains(
                   ALL_CONCEPTS, bkg))

    n_bound = sum(test_per[c]["n_rows"] for c in ALL_CONCEPTS)
    C.add("Y2-count", "TEST-domain hedge-free probe rows are re-derived per concept from "
                      "the raw demonstration blocks of ts116m, with denominators",
          n_bound > 0 and out["n_test_domains"] == pr.require("split", "n_test"),
          n_bound,
          "hedge-free / total: bomb %d/%d (%.1f%%), knife %d/%d (%.1f%%), gun %d/%d "
          "(%.1f%%) over %d TEST domains"
          % (test_per["bomb"]["n_hedge_free"], test_per["bomb"]["n_rows"],
             test_per["bomb"]["pct_hedge_free"],
             test_per["knife"]["n_hedge_free"], test_per["knife"]["n_rows"],
             test_per["knife"]["pct_hedge_free"],
             test_per["gun"]["n_hedge_free"], test_per["gun"]["n_rows"],
             test_per["gun"]["pct_hedge_free"], out["n_test_domains"]))

    # feasibility verdict: the independence unit is the DOMAIN, so the stratum is
    # feasible only if enough domains survive for the domain-level test to run.
    min_domains = 12       # below this the sign-test floor alone (2*0.5^12 = 4.9e-4) is
    #                        still under alpha but the t-arm's MDE has blown up
    feasible_2way = len(kg) >= min_domains
    out["feasibility"] = dict(
        min_domains_required=min_domains,
        n_domains_knife_gun=len(kg), feasible_2way=bool(feasible_2way),
        n_domains_all3=len(bkg), feasible_3way=bool(len(bkg) >= min_domains),
        mde_at_n_domains_sd0_1406=(P.t_mde(len(kg), 0.1406) if len(kg) >= 2 else None),
        mde_at_n_domains_sd0_25=(P.t_mde(len(kg), 0.25) if len(kg) >= 2 else None))
    C.add("Y2-feas", "the hedge-free stratum survives at the DOMAIN level for "
                     "knife-vs-gun (>=%d TEST domains have >=1 hedge-free row in BOTH "
                     "arms), not merely at row level" % min_domains,
          feasible_2way, max(len(kg), 0),
          "knife-vs-gun: %d/%d TEST domains usable, balanced row-level N=%d, "
          "domain-balanced N=%d | all three concepts: %d/%d domains, balanced N=%d"
          % (len(kg), out["n_test_domains"], bal_rows_2way,
             out["balanced_usable_N_domainbalanced_2way"], len(bkg),
             out["n_test_domains"], bal_rows_3way))
    return out


# ================================================================= Y3
def get_tokenizer(pr):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(pr.require("model", "hf_id"))


def y3(pr, C, rows, assign, mut=None):
    kill_thresh = 0.10          # declared in configs/dcs_ts_pr049.json:kill_condition
    kc_text = pr.require("kill_condition")
    if "0.10" not in kc_text and "+0.10" not in kc_text:
        raise ZeroBinding("the preregistration's kill_condition no longer names +0.10: %r"
                          % kc_text)

    tr = [r for r in rows if assign.get(r["domain"]) == "train"]
    te = [r for r in rows if assign.get(r["domain"]) == "test"]
    require_nonempty(len(tr), "TRAIN probe rows")
    require_nonempty(len(te), "TEST probe rows")
    va = [r for r in rows if assign.get(r["domain"]) == "validation"]
    C.add("Y3-split", "TRAIN and TEST are DOMAIN-GROUPED and disjoint, and VALIDATION is "
                      "carried but never read by any baseline here",
          not (set(r["domain"] for r in tr) & set(r["domain"] for r in te)),
          len(tr) + len(te),
          "train %d rows / %d domains ; test %d rows / %d domains ; validation %d rows "
          "/ %d domains UNTOUCHED"
          % (len(tr), len(set(r["domain"] for r in tr)), len(te),
             len(set(r["domain"] for r in te)), len(va),
             len(set(r["domain"] for r in va))))

    # tokenizer -- a real requirement, not a nicety: C-084 recorded that the character
    # figure and the token figure disagree and the TOKEN figure is the honest one.
    tok, tok_err = None, None
    try:
        tok = get_tokenizer(pr)
    except Exception as e:                                    # noqa: BLE001
        tok_err = "%s: %s" % (type(e).__name__, e)
    if mut == "no_tokenizer":
        tok, tok_err = None, "mutation: tokenizer withheld"
    tok_cache = {}
    if tok is not None:
        allp = [r["full_prompt"] for r in rows]
        enc = tok(allp, add_special_tokens=False)["input_ids"]
        for p, ids in zip(allp, enc):
            tok_cache[p] = len(ids)
    C.add("Y3-tok", "the Llama-3.1-8B-Instruct tokenizer loads OFFLINE and token counts "
                    "are available, so the length baseline can be measured in TOKENS "
                    "and not only in characters (C-084)",
          tok is not None, len(tok_cache), tok_err or
          "%d distinct prompts tokenized" % len(tok_cache))

    def pair(a, b):
        t = [r for r in tr if r["concept"] in (a, b)]
        s = [r for r in te if r["concept"] in (a, b)]
        require_nonempty(len(t), "train rows for %s-vs-%s" % (a, b))
        require_nonempty(len(s), "test rows for %s-vs-%s" % (a, b))
        return t, s

    F_hedge_demo = lambda r: hedge_counts(r["demo_block"])                    # noqa: E731
    F_hedge_full = lambda r: hedge_counts(r["full_prompt"])                   # noqa: E731
    F_reg = lambda r: register_features(r["demo_block"])                      # noqa: E731
    F_len_chars = lambda r: [float(len(r["full_prompt"])),                    # noqa: E731
                             float(len(r["demo_block"]))]
    F_len_tok = lambda r: [float(tok_cache[r["full_prompt"]])]                # noqa: E731

    res = {}
    for a, b in (("knife", "gun"), ("bomb", "knife"), ("bomb", "gun")):
        t, s = pair(a, b)
        key = "%s_vs_%s" % (a, b)
        res[key] = dict(
            hedge_only_demo=fit_eval_2way(t, s, F_hedge_demo, b, mut=mut),
            hedge_only_fullprompt=fit_eval_2way(t, s, F_hedge_full, b, mut=mut),
            n_train=len(t), n_test=len(s))
        if (a, b) == ("knife", "gun"):
            res[key]["register_only"] = fit_eval_2way(t, s, F_reg, b, mut=mut)
            res[key]["register_only_lengthfree"] = fit_eval_2way(
                t, s, lambda r: register_features_lengthfree(r["demo_block"]), b, mut=mut)
            res[key]["length_only_chars"] = fit_eval_2way(t, s, F_len_chars, b, mut=mut)
            if tok is not None:
                res[key]["length_only_tokens"] = fit_eval_2way(t, s, F_len_tok, b, mut=mut)

    kg = res["knife_vs_gun"]["hedge_only_demo"]
    adv = kg["advantage"]
    survive = adv <= kill_thresh
    res["kill_condition"] = dict(
        threshold=kill_thresh, statistic="hedge-only knife-vs-gun accuracy - 0.5",
        measured_advantage=adv, measured_accuracy=kg["acc"], measured_auroc=kg["auroc"],
        domain_mean_advantage=kg["domain_mean_acc"] - 0.5,
        verdict="SURVIVE" if survive else "KILL",
        superseded_ts116n_figures_not_quoted=dict(bomb_vs_knife=0.211, knife_vs_gun=0.037))
    C.add("Y3-kill", "KILL CONDITION (declared in configs/dcs_ts_pr049.json before this "
                     "measurement existed): the hedge-only advantage on knife-vs-gun "
                     "does NOT exceed +%.2f, so the contrast is register-clean and "
                     "PR-049 stands" % kill_thresh,
          survive, kg["n_test"],
          "%s: hedge-only knife-vs-gun advantage = %+.4f (acc %.4f, AUROC %.4f, "
          "domain-mean advantage %+.4f) vs threshold +%.2f"
          % (res["kill_condition"]["verdict"], adv, kg["acc"], kg["auroc"],
             kg["domain_mean_acc"] - 0.5, kill_thresh))

    bk = res["bomb_vs_knife"]["hedge_only_demo"]["advantage"]
    bg = res["bomb_vs_gun"]["hedge_only_demo"]["advantage"]
    C.add("Y3-asym", "the register axis is a BOMB-vs-REST severity axis and not a "
                     "uniform nuisance: hedge-only buys materially more on the bomb "
                     "contrasts than on knife-vs-gun",
          (bk > adv) and (bg > adv), kg["n_test"],
          "advantages: bomb-vs-knife %+.4f, bomb-vs-gun %+.4f, knife-vs-gun %+.4f"
          % (bk, bg, adv))

    rg = res["knife_vs_gun"]["register_only"]
    rlf = res["knife_vs_gun"]["register_only_lengthfree"]
    lc = res["knife_vs_gun"]["length_only_chars"]
    lt = res["knife_vs_gun"].get("length_only_tokens")
    C.add("Y3-reg", "the register-only and length-only baselines on knife-vs-gun are "
                    "measured with denominators, in TOKENS as well as characters",
          lt is not None, rg["n_test"],
          "register-only %+.4f (AUROC %.4f) ; register-only LENGTH-FREE %+.4f (AUROC "
          "%.4f) ; length chars %+.4f (AUROC %.4f) ; length TOKENS %s"
          % (rg["advantage"], rg["auroc"], rlf["advantage"], rlf["auroc"],
             lc["advantage"], lc["auroc"],
             ("%+.4f (AUROC %.4f)" % (lt["advantage"], lt["auroc"])) if lt else "UNAVAILABLE"))

    # The kill condition names the HEDGE-ONLY classifier and nothing else.  It is
    # answered above.  This check answers the DIFFERENT question the same measurement
    # raises, and it is recorded whichever way it comes out rather than being folded
    # into the kill verdict it was not written to govern.
    surface_clean = rg["advantage"] <= kill_thresh
    res["surface_caveat"] = dict(
        register_only_advantage=rg["advantage"],
        register_only_lengthfree_advantage=rlf["advantage"],
        length_chars_advantage=lc["advantage"],
        length_tokens_advantage=(lt["advantage"] if lt else None),
        exceeds_kill_threshold=not surface_clean,
        _scope="the preregistered kill condition governs the HEDGE-ONLY classifier "
               "only; this is reported as a separate, live limitation and does NOT "
               "trigger the kill")
    C.add("Y3-surf", "SEPARATE FROM THE KILL CONDITION, which governs the hedge-only "
                     "classifier alone: the broader register-only surface classifier "
                     "on knife-vs-gun ALSO stays within +%.2f, so 'register-clean in "
                     "the hedge sense' and 'surface-clean' would be the same verdict "
                     "on this contrast" % kill_thresh,
          surface_clean, rg["n_test"],
          "register-only %+.4f (%s +%.2f) ; length-free %+.4f ; length chars %+.4f ; "
          "length tokens %s -- whatever this number is, it does NOT trigger the kill "
          "condition, which is written about hedges"
          % (rg["advantage"], "within" if surface_clean else "EXCEEDS", kill_thresh,
             rlf["advantage"], lc["advantage"],
             ("%+.4f" % lt["advantage"]) if lt else "n/a"))
    return res


# ================================================================= driver
MUTATIONS = OrderedDict([
    ("pool_doses", "pool the n_examples=8 replication dose into the primary cell, "
                   "which the preregistration's _dose_rule forbids"),
    ("empty_population", "select cell 'Z' so the probe population binds zero rows"),
    ("keep_excluded_domains", "stop excluding restaurant_kitchen and subway_station"),
    ("corrupt_split", "put 5 TEST domains into TRAIN as well, so the groups overlap"),
    ("dead_hedge_lexicon", "a hedge lexicon that matches nothing"),
    ("hedge_leak", "append 'It resembled a device.' to every GUN demonstration block"),
    ("row_level_permutation", "permute labels at ROW level in the FPR simulation"),
    ("test_selected_hyperparams", "select the layer/C candidate on TEST, not VALIDATION"),
    ("mde_drop_beta", "compute the MDE without the type-II term"),
    ("perm_floor_naive", "use the naive #{null>=obs}/B permutation p (floor 0)"),
    ("no_tokenizer", "withhold the tokenizer so length is measurable only in characters"),
])


def run(pr, reps, n_perm, seed, mut=None, quick=False):
    C = Checks()
    res = dict(mutation=mut)

    # --- population -------------------------------------------------------------
    rows, n_excl, excluded = load_probe_rows(pr, mut=mut)
    manifest, assign = load_split(pr, mut=mut)
    doms = sorted(set(r["domain"] for r in rows))
    by_split = Counter(assign.get(r["domain"], "UNASSIGNED") for r in rows)
    per_concept = Counter(r["concept"] for r in rows)
    want = dict(train=pr.require("split", "n_train"),
                validation=pr.require("split", "n_validation"),
                test=pr.require("split", "n_test"))
    got = {s: len(set(r["domain"] for r in rows if assign.get(r["domain"]) == s))
           for s in want}
    n_dom_want = pr.require("split", "n_domains_analysed")
    n_rows_want = (pr.require("population", "rows_per_domain_per_concept")
                   * n_dom_want * len(ALL_CONCEPTS) * len(CODEWORDS))
    C.add("POP-01", "the probe population binds on the FIELD `cell`=='C' x "
                    "semantic_one_word x n_examples=4 (the primary DOSE ONLY -- doses "
                    "are separate preregistered cells and are never pooled) over all "
                    "six ts116m banks, at exactly %d rows = %d domains x %d rows x 3 "
                    "concepts x 2 codewords, with both preregistered prompt-only "
                    "exclusions removed"
                    % (n_rows_want, n_dom_want,
                       pr.require("population", "rows_per_domain_per_concept")),
          len(rows) == n_rows_want and len(doms) == n_dom_want
          and len(set(per_concept.values())) == 1,
          len(rows),
          "%d rows (want %d) over %d domains (want %d), %d rows dropped for %s; per "
          "concept %s"
          % (len(rows), n_rows_want, len(doms), n_dom_want, n_excl, excluded,
             dict(per_concept)))
    C.add("POP-02", "the analysed split is %d train / %d validation / %d test DOMAINS "
                    "and no row is unassigned" % (want["train"], want["validation"],
                                                  want["test"]),
          got == want and by_split.get("UNASSIGNED", 0) == 0, len(rows),
          "domains %s (want %s); rows by split %s" % (got, want, dict(by_split)))
    n_cond = 0
    family = pr.require("population", "bank_family")
    cond_ids = set()
    cell_ids = set((r["codeword"], r["concept"], r["prompt_id"]) for r in rows)
    excl_set = set(excluded)
    for cw in CODEWORDS:
        for cc in ALL_CONCEPTS:
            with open(bank_path(family, cw, cc)) as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    r2 = json.loads(line)
                    if (r2.get("condition") == "natural_doublespeak"
                            and r2.get("query_kind") == pr.require("population",
                                                                   "query_kind_primary")
                            and r2.get("n_examples") == pr.require("population",
                                                                   "n_examples_primary")
                            and r2["domain"] not in excl_set):
                        cond_ids.add((cw, cc, r2["prompt_id"]))
                        n_cond += 1
    same = (cond_ids == cell_ids)
    C.add("POP-03", "A-039 is MEASURED on ts116m rather than inherited: the "
                    "`condition`=='natural_doublespeak' spelling of the selector is "
                    "checked against the preregistered `cell`=='C' spelling, and the "
                    "result is reported whichever way it comes out",
          n_cond > 0 and len(cell_ids) == len(rows), n_cond,
          "on ts116m the two selectors bind the SAME %d rows (set-identical on "
          "(codeword, concept, prompt_id): %s) -- "
          "A-039's zero-binding failure does NOT reproduce on this corpus, so the "
          "preregistration's _cell_note is a correct instruction whose stated "
          "consequence is corpus-specific"
          % (n_cond, same))

    res["selector_equivalence"] = dict(n_rows_condition=n_cond,
                                       n_rows_cell=len(cell_ids),
                                       set_identical=bool(same))
    res["population"] = dict(n_rows=len(rows), n_domains=len(doms),
                             n_excluded_rows=n_excl, excluded_domains=excluded,
                             per_concept=dict(per_concept),
                             domains_by_split=got, rows_by_split=dict(by_split))

    # --- Y1 / Y2 / Y3 -------------------------------------------------------------
    res["Y1"] = y1(pr, C, reps=reps, n_perm=n_perm, seed=seed, mut=mut, quick=quick)
    res["Y2"] = y2(pr, C, rows, assign, mut=mut)
    res["Y3"] = y3(pr, C, rows, assign, mut=mut)
    res["checks"] = C.rows
    res["n_fail"] = C.n_fail
    return C, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200,
                    help="FPR replicates (preregistration asks for at least 200)")
    ap.add_argument("--n-perm", type=int, default=200,
                    help="permutations per FPR replicate (the FPR sim's own B; the "
                         "CONFIRMATORY run uses primary.n_perm=10000)")
    ap.add_argument("--seed", type=int, default=20260907)
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    try:
        pr = load_prereg(PR049)
        pr48 = load_prereg(PR048)
    except PreregError as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        return 2
    print("=== DCS-PR-049 blocking pre-analysis items Y1/Y2/Y3 ===")
    print("prereg %s (%s, FROZEN %s) and companion %s both load with every pinned hash "
          "verified" % (PR049, pr.require("id"), pr.require("frozen_at"), PR048))
    print("PR-048 chance %.6f (3-way) vs PR-049 chance %.4f (2-way) -- the reason Y1 exists"
          % (pr48.require("primary", "chance"), pr.require("primary", "chance")))
    # the hedge definition is READ OUT OF the audit scripts, and a drift there is visible
    for f in HEDGE_SOURCE_FILES:
        src = open(os.path.join(REPO, f)).read()
        for k in ("resembl", "simulat", "false alarm"):
            if k not in src:
                print("WARNING: hedge family %r is absent from %s" % (k, f))

    C, res = run(pr, a.reps, a.n_perm, a.seed)
    print("\n--- checks ---")
    C.report()
    print("[real] %d/%d checks FAIL" % (C.n_fail, len(C.rows)))
    if C.n_fail:
        print("       FAILING: %s" % ", ".join(k for k, v in C.rows.items() if not v["ok"]))
        print("       A failing check here is a MEASUREMENT, not a broken harness: the "
              "claim it states was tested against the corpus and did not hold. It is "
              "reported as such and is NOT edited to make the run green.")

    print("\n--- headline numbers ---")
    y = res["Y1"]
    print("Y1  sign floor n=23: %.4e (k>=%d needed) | perm floor B=10000: %.4e"
          % (y["sign"]["floor_two_sided"], y["sign"]["k_needed"],
             y["perm"][10000]["floor"]))
    print("Y1  MDE at sd 0.1406/0.25/0.3439: %.4f / %.4f / %.4f | FPR %.4f CI %s"
          % (y["mde"]["by_sd"][0.1406]["mde_alpha05"],
             y["mde"]["by_sd"][0.25]["mde_alpha05"],
             y["mde"]["by_sd"][0.3439]["mde_alpha05"],
             y["fpr"]["fpr"], tuple(round(v, 4) for v in y["fpr"]["ci95"])))
    print("Y1  VERDICT: %s -- conjunctive power %.3f at sd=%.4f (Holm %.3f); "
          "flips to EXPLORATORY above sd=%.3f"
          % (y["verdict"]["call"], y["verdict"]["conjunctive_power_at_working_sd"],
             y["verdict"]["sd_working_assumption"],
             y["verdict"]["conjunctive_power_at_working_sd_holm"],
             y["conjunctive_power"]["sd_breakpoint_alpha05"]))
    t = res["Y2"]["test"]
    print("Y2  TEST hedge-free rows: bomb %d/%d, knife %d/%d, gun %d/%d ; knife-gun "
          "usable domains %d/%d"
          % (t["bomb"]["n_hedge_free"], t["bomb"]["n_rows"],
             t["knife"]["n_hedge_free"], t["knife"]["n_rows"],
             t["gun"]["n_hedge_free"], t["gun"]["n_rows"],
             res["Y2"]["n_knife_gun_usable_domains"], res["Y2"]["n_test_domains"]))
    k = res["Y3"]["kill_condition"]
    print("Y3  hedge-only knife-vs-gun advantage %+.4f vs threshold +%.2f -> %s"
          % (k["measured_advantage"], k["threshold"], k["verdict"]))

    n_red = 0
    if a.mutate:
        print("\n=== mutation harness: every check must be reachable ===")
        baseline_green = set(k2 for k2, v in C.rows.items() if v["ok"])
        print("  (a mutation counts as caught only if it turns RED one of the %d checks "
              "that are GREEN on the real corpus; Y3-surf is RED there and is excluded)"
              % len(baseline_green))
        muts = {}
        for name, why in MUTATIONS.items():
            try:
                Cm, _ = run(pr, min(a.reps, 100), max(a.n_perm // 2, 100), a.seed,
                            mut=name, quick=True)
                failed = [k2 for k2, v in Cm.rows.items()
                          if not v["ok"] and k2 in baseline_green]
                red = bool(failed)
                detail = "checks RED: %s" % ",".join(failed[:6])
            except (ZeroBinding, ValueError, KeyError) as e:
                red = True
                detail = "RAISED %s: %s" % (type(e).__name__, str(e)[:90])
            n_red += red
            print("  %-5s %-26s %s" % ("RED" if red else "GREEN", name, detail))
            if not red:
                print("        ^^ THIS MUTATION DID NOT TURN ANY CHECK RED -- an "
                      "unreachable check is not a guard")
        print("[mutate] %d/%d mutations turned a check RED" % (n_red, len(MUTATIONS)))
        res["mutations"] = dict(n=len(MUTATIONS), n_red=n_red,
                                names=list(MUTATIONS))

    if a.json:
        with open(a.json, "w") as fh:
            json.dump(res, fh, indent=1, default=str)
        print("\nwrote %s" % a.json)
    if C.n_fail:
        return 1
    if a.mutate and n_red != len(MUTATIONS):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
