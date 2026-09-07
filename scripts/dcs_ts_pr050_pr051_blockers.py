#!/usr/bin/env python
"""DCS PR-050 / PR-051 BLOCKING pre-analysis items W3, Z1, Z2.  CPU only.

`configs/dcs_ts_pr051.json` declares W3 and `configs/dcs_ts_pr050.json` declares Z1 and
Z2 as `blocking: true, done: false`:

  W3  (PR-051) verify the CONTROL SITE.  PR-051's control is `--position last`, the final
      prompt position.  reports/DCS_TS116M_TOKEN_ROLE_MAP.md verified `rel_end = -9`; it
      did NOT verify `rel_end = -1`, and it was computed on 115 domains before C-087
      excluded `subway_station`.  Re-derived here on the 114-domain population against
      the four criteria PR-048 X2 uses, plus the question the map does not ask: WHAT IS
      THE TOKEN, and is it scaffold or content.

  Z1  (PR-050) can the stratification even work?  Fit the 17-feature register/surface
      classifier on TRAIN domains, score VALIDATION rows, stratify by the predicted-
      probability vector, and measure the surface classifier's accuracy WITHIN strata.
      PR-050's kill condition asks whether ANY stratification with usable n drives the
      surface classifier to chance.  Answered for the 3-way (chance 1/3) and for
      knife-vs-gun (chance 0.5).

  Z2  (PR-050) power WITHIN strata.  Strata shrink the rows per domain, which inflates
      the binomial component of the between-domain SD.  Neither PR-048's 3-way power nor
      PR-049's 2-way power transfers.

*** THIS SCRIPT NEVER READS A TEST LABEL AND NEVER COMPUTES A TEST-SET OUTCOME. ***
Every fit is on TRAIN domains and every evaluation is on VALIDATION domains.  A hard
guard (`GUARD-TEST`) asserts on every analysed row set that no `test` domain is in it,
and the guard is itself mutated.  W3 is prompt-only and therefore binds the whole
population, TEST included -- reading a PROMPT is not reading a LABEL or an OUTCOME, and
that distinction is stated rather than assumed.

NO GPU, NO MODEL WEIGHTS, NO SLURM, NO NETWORK.  The Llama-3.1-8B-Instruct TOKENIZER is
loaded from the local HF cache with HF_HUB_OFFLINE=1, purely to tokenize prompt text.  If
it is unavailable W3 FAILS rather than falling back to characters.

DISCIPLINE (this repository has shipped four verifier harnesses whose checks passed over
empty sets, and twice published a threshold that no code path ever read):
  * every check binds to a COUNTED set; a check that binds zero rows is a FAIL;
  * every number is re-derived from the RAW bank JSONL rows and a REAL tokenization --
    never from a producer-written summary field, never from the token-role map's tables;
  * every gate value comes out of the preregistration through Prereg.require();
  * splits are DOMAIN-GROUPED and the disjointness assertion is itself mutated;
  * `--mutate` demonstrates each check going RED under a deliberate defect.

REUSE, not re-implementation: the 17 surface features, the population loader, the split
loader and the Checks ledger are IMPORTED from scripts/dcs_ts_pr049_blockers.py, and the
power estimators from scripts/dcs_ts_power.py.  A difference between these numbers and
PR-049's is therefore a difference of DESIGN, not of arithmetic.

usage:
    python scripts/dcs_ts_pr050_pr051_blockers.py
    python scripts/dcs_ts_pr050_pr051_blockers.py --mutate
    python scripts/dcs_ts_pr050_pr051_blockers.py --json OUT.json
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
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))

from dcs_ts_prereg import load as load_prereg                        # noqa: E402
import dcs_ts_power as P                                             # noqa: E402
import dcs_ts_pr049_blockers as B                                    # noqa: E402

# The 17 surface features, read off the DEMONSTRATION BLOCK exactly as PR-049 Y3 read
# them (`lambda r: register_features(r["demo_block"])`, dcs_ts_pr049_blockers.py:848).
def FEAT(r):
    return register_features(r["demo_block"])


def FEAT_LENGTHFREE(r):
    return register_features_lengthfree(r["demo_block"])


Checks = B.Checks
ZeroBinding = B.ZeroBinding
require_nonempty = B.require_nonempty
register_features = B.register_features
register_features_lengthfree = B.register_features_lengthfree
HEDGE_PATTERNS = B.HEDGE_PATTERNS

PR050 = "configs/dcs_ts_pr050.json"
PR051 = "configs/dcs_ts_pr051.json"
PR048 = "configs/dcs_ts_pr048.json"

TOKENIZER_ID = "meta-llama/Llama-3.1-8B-Instruct"

# Inflection-aware concept surfaces, for criterion (c).  Substring-permissive on purpose:
# criterion (c) asks whether the control token CONTAINS a concept name, so a rule that is
# stricter than the substituter's would under-credit exactly the way C-076 did.
CONCEPT_SURFACES = ("bomb", "knif", "knive", "gun")

# ---------------------------------------------------------------- declared BEFORE scoring
# The candidate stratifications.  Fixed in source before any predicted probability exists,
# so that "which stratification" cannot be chosen after seeing which one is convenient.
STRAT_SPECS = [
    ("maxprob_q2",  "maxprob", 2),
    ("maxprob_q3",  "maxprob", 3),
    ("maxprob_q4",  "maxprob", 4),
    ("maxprob_q5",  "maxprob", 5),
    ("maxprob_q10", "maxprob", 10),
    ("margin_q2",   "margin",  2),
    ("margin_q3",   "margin",  3),
    ("margin_q4",   "margin",  4),
    ("margin_q5",   "margin",  5),
    ("margin_q10",  "margin",  10),
    ("margin_lo10", "margin_tail", 10),   # bottom 10% of the margin, one stratum
    ("margin_lo25", "margin_tail", 25),
    ("margin_lo50", "margin_tail", 50),
    # PROPENSITY-STYLE: equal-frequency bins on the predicted probability of ONE fixed
    # reference class.  This is the textbook propensity stratification and it is a
    # genuinely different partition from maxprob/margin, which bin on |p - chance|.
    ("pref_q3", "pref", 3),
    ("pref_q5", "pref", 5),
    # JOINT: coarsen EVERY coordinate of the predicted-probability vector into t tiers and
    # take the cross-product cells.  This is the strongest reading of "stratify by the
    # predicted-probability vector" -- the whole vector, not a scalar summary of it.
    ("simplex_t2", "simplex", 2),
    ("simplex_t3", "simplex", 3),
]

# "AT CHANCE", declared before the numbers exist.  Two tiers, both reported:
#   COVERS  -- the 95% Clopper-Pearson CI on the stratum accuracy covers chance.
#              This is weak: a small stratum covers chance because it is small.
#   EQUIV   -- |acc - chance| <= 0.03 AND the CI upper bound <= chance + 0.05.
#              This is the tier the kill condition is read against, because it is the one
#              that says the surface classifier is ACTUALLY uninformative rather than
#              merely unmeasurable.
CHANCE_TOL = 0.03
CHANCE_UPPER_SLACK = 0.05

# "USABLE n", declared before the numbers exist.  A stratum whose per-domain unit is
# broken cannot feed a domain-mean estimator, whatever its row count.
USABLE_MIN_DOMAINS = 23          # all held-out domains must be represented
USABLE_MIN_ROWS_PER_DOMAIN = 4   # a per-domain accuracy on <4 rows is quantised to 1/3s
USABLE_MIN_ROWS = 230            # 10 per domain

BAR_DELTA = 0.15                 # PR-049 Y1's planning bar, reused unchanged
SD_BETWEEN_WORKING = 0.1406      # PR-048's PROJECTED 3-way between-domain SD. AN ASSUMPTION.
SD_BETWEEN_CEILING = 0.3439      # its 95% upper bound (5 df), from PR-048 power block


def clopper_pearson(k, n, alpha=0.05):
    return P.clopper_pearson(k, n, alpha)


def dsplit_of(assign, domain):
    return assign.get(domain)


def guard_no_test(rows, assign, what, mut=None):
    """Refuse to compute anything on a TEST domain.  Mutated by `read_test`."""
    bad = sorted(set(r["domain"] for r in rows if dsplit_of(assign, r["domain"]) == "test"))
    if bad:
        raise ZeroBinding("TEST DOMAINS ENTERED %s: %s -- refusing" % (what, bad[:5]))
    return bad, True


# ================================================================= tokenizer
_TOK = [None]


def get_tokenizer():
    if _TOK[0] is None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        from transformers import AutoTokenizer
        _TOK[0] = AutoTokenizer.from_pretrained(TOKENIZER_ID)
    return _TOK[0]


# ================================================================= W3
def w3_tokenize(rows, C):
    """Re-derive, for every matched prompt, EXACTLY what --position last reads.

    src/boombness/extract_boombness.py:
        templated = dc.apply_template(tok, row["full_prompt"], enable_thinking=None)
        ids       = tok(templated, add_special_tokens=False)["input_ids"]
        pos       = len(ids) - 1                       # --position last
    reproduced here line for line, so the site verified is the site extracted.
    """
    import doublespeak_causality.ds_common as dc
    tok = get_tokenizer()

    # What the generation prompt ADDS.  Determined by differencing the template with and
    # without add_generation_prompt on a real row -- not by pattern-matching a string
    # literal, which would be a claim about the template rather than a measurement of it.
    probe = rows[0]["full_prompt"]
    t_gen = dc.apply_template(tok, probe, add_generation_prompt=True)
    t_nogen = dc.apply_template(tok, probe, add_generation_prompt=False)
    if not t_gen.startswith(t_nogen):
        raise ZeroBinding("the generation prompt is not a pure SUFFIX of the template; "
                          "the scaffold/content split below would be wrong")
    gen_suffix = t_gen[len(t_nogen):]
    n_gen_tokens = (len(tok(t_gen, add_special_tokens=False)["input_ids"])
                    - len(tok(t_nogen, add_special_tokens=False)["input_ids"]))

    out = []
    for r in rows:
        templated = dc.apply_template(tok, r["full_prompt"])   # enable_thinking default = None
        ids = tok(templated, add_special_tokens=False)["input_ids"]
        require_nonempty(len(ids), "tokenization of %s" % r["prompt_id"])
        hit = dc.find_word_occurrences_in_text(tok, templated, r["codeword"],
                                               add_special_tokens=False)
        last_cw = int(hit.last_idx[-1]) if len(hit.last_idx) else None
        n_ids = len(ids)
        out.append(dict(
            domain=r["domain"], concept=r["concept"], codeword=r["codeword"],
            prompt_id=r["prompt_id"], seq_len=n_ids,
            last_tok_id=int(ids[-1]),
            last_tok_str=tok.decode([ids[-1]]),
            last_pos=n_ids - 1,
            cw_last_pos=last_cw,
            cw_last_rel_end=(last_cw - n_ids) if last_cw is not None else None,
            n_cw_occ=len(hit.last_idx),
            tail_ids=[int(x) for x in ids[-max(n_gen_tokens + 2, 6):]],
        ))
    C.add("W3-tok", "the control site is re-derived by REPRODUCING the extractor's own "
                    "tokenization path (dc.apply_template -> tok(add_special_tokens=False) "
                    "-> index len(ids)-1), not by trusting the token-role map",
          len(out) == len(rows), len(out),
          "tokenized %d prompts; generation prompt adds %d tokens (%r)"
          % (len(out), n_gen_tokens, gen_suffix))
    return out, gen_suffix, n_gen_tokens, tok


def w3(pr51, C, toks, gen_suffix, n_gen_tokens, tok, mut=None):
    """The four PR-048-X2 criteria at rel_end = -1, plus the scaffold/content question."""
    T = [dict(t) for t in toks]

    if mut == "w3_perturb_final_token":
        for t in T:
            if t["concept"] == "knife":
                t["last_tok_id"] = t["last_tok_id"] + 1
                t["last_tok_str"] = tok.decode([t["last_tok_id"]])
                break
    if mut == "w3_codeword_at_end":
        T[0]["cw_last_pos"] = T[0]["last_pos"]
        T[0]["cw_last_rel_end"] = -1
    if mut == "w3_concept_at_end":
        T[1]["last_tok_str"] = " bomb"
    if mut == "w3_drop_arm":
        key = (T[0]["codeword"], T[0]["prompt_id"])
        T = [t for t in T if not (t["codeword"] == key[0] and t["prompt_id"] == key[1]
                                  and t["concept"] == "gun")]
    if mut == "w3_no_generation_prompt":
        n_gen_tokens = 0
    if mut == "empty_population":
        T = []

    n = len(T)

    # --- (d) exists in every matched prompt, and every prompt_id has all three arms ----
    by_key = defaultdict(dict)
    for t in T:
        by_key[(t["codeword"], t["prompt_id"])][t["concept"]] = t
    triples = {k: v for k, v in by_key.items() if len(v) == 3}
    n_keys = len(by_key)
    n_present = sum(1 for t in T if t["seq_len"] >= 1 and t["last_pos"] == t["seq_len"] - 1)
    C.add("W3-d", "(d) the final prompt position EXISTS in every matched prompt, and every "
                  "(codeword, prompt_id) key carries all three concept arms so the site is "
                  "comparable at matched prompt_id",
          n_present == n and len(triples) == n_keys and n_keys > 0, n,
          "present %d/%d prompts; complete triples %d/%d keys"
          % (n_present, n, len(triples), n_keys))

    # --- (a) token-identical across the three concepts at matched prompt_id -----------
    ident = sum(1 for v in triples.values()
                if len(set(v[c]["last_tok_id"] for c in v)) == 1)
    C.add("W3-a", "(a) the final prompt position is TOKEN-IDENTICAL across the three "
                  "concepts at matched (codeword, prompt_id)",
          ident == len(triples) and len(triples) > 0, len(triples),
          "%d/%d triples identical" % (ident, len(triples)))

    # --- (b) strictly after every codeword occurrence ---------------------------------
    after = sum(1 for t in T
                if t["cw_last_pos"] is not None and t["last_pos"] > t["cw_last_pos"])
    no_occ = sum(1 for t in T if t["cw_last_pos"] is None)
    C.add("W3-b", "(b) the final prompt position is STRICTLY AFTER every codeword "
                  "occurrence, re-derived by locating every occurrence in the templated "
                  "text (offset-based, left-strict / right-permissive)",
          after == n and no_occ == 0 and n > 0, n,
          "%d/%d strictly after; %d prompts with NO located occurrence" % (after, n, no_occ))

    # --- (c) contains none of bomb/knife/gun ------------------------------------------
    decodings = Counter(t["last_tok_str"] for t in T)
    dirty = sorted(s for s in decodings
                   if any(w in s.lower() for w in CONCEPT_SURFACES))
    C.add("W3-c", "(c) the decoding of the final prompt position contains NO concept "
                  "surface (bomb / knif* / knive* / gun), inflection- and "
                  "substring-permissive",
          not dirty and n > 0, n,
          "%d distinct decoding(s) over %d prompts: %s%s"
          % (len(decodings), n,
             ", ".join("%r x%d" % (k, v) for k, v in decodings.most_common(5)),
             ("  DIRTY: %s" % dirty) if dirty else ""))

    # --- scaffold or content ----------------------------------------------------------
    # The final position is inside the generation-prompt suffix iff its distance from the
    # end is less than the number of tokens that suffix adds.  n_gen_tokens is MEASURED
    # above by differencing the two templates.
    in_gen = sum(1 for t in T if n_gen_tokens >= 1)
    C.add("W3-scaffold", "the final prompt position lies INSIDE the generation-prompt "
                         "suffix that add_generation_prompt appends -- i.e. it is chat "
                         "scaffold, not query content",
          n_gen_tokens >= 1 and in_gen == n and n > 0, n,
          "generation suffix = %r = %d tokens; the final position is its last token in "
          "%d/%d prompts" % (gen_suffix, n_gen_tokens, in_gen, n))

    # distance from the preregistered PRIMARY site
    rels = Counter(t["cw_last_rel_end"] for t in T if t["cw_last_rel_end"] is not None)
    gaps = [(-1) - t["cw_last_rel_end"] for t in T if t["cw_last_rel_end"] is not None]
    C.add("W3-gap", "the control site sits a CONSTANT number of tokens downstream of the "
                    "preregistered primary site codeword_last, so the paired contrast is "
                    "between two fixed offsets and not between two moving ones",
          len(set(gaps)) == 1 and len(gaps) > 0, len(gaps),
          "codeword_last rel_end distribution %s; control is %s tokens downstream"
          % (dict(rels), sorted(set(gaps))))

    tail_roles = []
    if T:
        tail_ids = T[0]["tail_ids"]
        tail_roles = [(i - len(tail_ids), int(x), tok.decode([x])) for i, x in enumerate(tail_ids)]

    return dict(
        n_prompts=n, n_triples=len(triples), n_keys=n_keys,
        criterion_a=dict(n_identical=ident, n=len(triples)),
        criterion_b=dict(n_after=after, n=n, n_no_occurrence=no_occ),
        criterion_c=dict(distinct_decodings=dict(decodings), dirty=dirty),
        criterion_d=dict(n_present=n_present, n=n,
                         n_complete_triples=len(triples), n_keys=n_keys),
        decoded=dict(decodings.most_common()),
        generation_suffix=gen_suffix, n_generation_tokens=n_gen_tokens,
        codeword_last_rel_end=dict(rels), gap_to_primary=sorted(set(gaps)),
        tail=tail_roles,
        seq_len=dict(mean=float(np.mean([t["seq_len"] for t in T])) if T else float("nan"),
                     min=int(min(t["seq_len"] for t in T)) if T else 0,
                     max=int(max(t["seq_len"] for t in T)) if T else 0),
    )


# ================================================================= Z1
def _fit_surface(rows_tr, rows_va, classes, featfn, seed=0, mut=None):
    """TRAIN-fit surface classifier, scored on VALIDATION.  Standardiser fit on TRAIN only."""
    tr = [r for r in rows_tr if r["concept"] in classes]
    va = [r for r in rows_va if r["concept"] in classes]
    require_nonempty(len(tr), "surface-classifier TRAIN rows for %s" % (classes,))
    require_nonempty(len(va), "surface-classifier VALIDATION rows for %s" % (classes,))
    tr_d, va_d = set(r["domain"] for r in tr), set(r["domain"] for r in va)
    if tr_d & va_d:
        raise ZeroBinding("TRAIN and VALIDATION share %d domain(s): %s"
                          % (len(tr_d & va_d), sorted(tr_d & va_d)[:5]))
    Xtr = np.asarray([featfn(r) for r in tr], dtype=float)
    Xva = np.asarray([featfn(r) for r in va], dtype=float)
    ytr = np.asarray([r["concept"] for r in tr])
    if mut == "shuffle_labels":
        # The canonical null: the TRAIN labels are permuted against their own features, so
        # there is nothing left to learn and the held-out accuracy must fall to chance.
        # (An earlier version permuted the feature ROWS instead; on this corpus that left
        # enough residual structure that the check stayed GREEN, i.e. the mutation was too
        # weak to be a demonstration. Recorded because a mutation that does not go RED is
        # supposed to mean the check cannot fail, and here it meant the mutation was bad.)
        ytr = np.random.RandomState(0).permutation(ytr)
    yva = np.asarray([r["concept"] for r in va])
    sc = StandardScaler()
    A = sc.fit_transform(Xtr)
    Bm = sc.transform(Xva)
    clf = LogisticRegression(max_iter=4000, random_state=seed)
    clf.fit(A, ytr)
    proba = clf.predict_proba(Bm)
    pred = clf.classes_[np.argmax(proba, axis=1)]
    srt = np.sort(proba, axis=1)
    return dict(rows=va, y=yva, pred=pred, proba=proba, classes=list(clf.classes_),
                maxprob=srt[:, -1], margin=srt[:, -1] - srt[:, -2],
                n_train=len(tr), n_train_domains=len(tr_d),
                n_val=len(va), n_val_domains=len(va_d),
                n_features=int(Xtr.shape[1]),
                acc=float(accuracy_score(yva, pred)),
                bal=float(balanced_accuracy_score(yva, pred)))


def _strata_vector(proba, classes, kind, q, mut=None):
    """Stratifications that read the WHOLE predicted-probability vector."""
    n = proba.shape[0]
    if mut == "strat_one_bin":
        return [("all", np.ones(n, dtype=bool))]
    out = []
    if kind == "pref":
        for j, cname in enumerate(classes):
            col = proba[:, j]
            edges = np.quantile(col, np.linspace(0, 1, q + 1))
            edges[0], edges[-1] = -np.inf, np.inf
            for i in range(q):
                m = (col > edges[i]) & (col <= edges[i + 1]) if i else (col <= edges[1])
                if m.sum():
                    out.append(("p(%s) bin%d/%d" % (cname, i + 1, q), m))
        return out
    if kind == "simplex":
        tiers = np.zeros_like(proba, dtype=int)
        for j in range(proba.shape[1]):
            edges = np.quantile(proba[:, j], np.linspace(0, 1, q + 1)[1:-1])
            tiers[:, j] = np.digitize(proba[:, j], edges)
        keys = [tuple(row) for row in tiers]
        for k in sorted(set(keys)):
            m = np.asarray([kk == k for kk in keys])
            if m.sum():
                out.append(("cell%s" % (list(k),), m))
        return out
    raise ZeroBinding("unknown vector stratification kind %r" % kind)


def _strata(stat, kind, q, mut=None):
    """Equal-frequency bins (or a single lower tail) on a scalar statistic."""
    if mut == "strat_one_bin":
        return [("all", np.ones(len(stat), dtype=bool))]
    if kind == "margin_tail":
        thr = float(np.percentile(stat, q))
        return [("margin<=p%d" % q, stat <= thr)]
    edges = np.quantile(stat, np.linspace(0, 1, q + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    out = []
    for i in range(q):
        m = (stat > edges[i]) & (stat <= edges[i + 1]) if i else (stat <= edges[1])
        out.append(("bin%d/%d" % (i + 1, q), m))
    return out


def _stratum_stats(fit, mask, chance, refit=True, featfn=None, seed=0):
    rows = [r for r, m in zip(fit["rows"], mask) if m]
    if not rows:
        return None
    y = fit["y"][mask]
    pred = fit["pred"][mask]
    k = int((y == pred).sum())
    n = int(len(y))
    lo, hi = clopper_pearson(k, n)
    per = defaultdict(list)
    for r, p, t in zip(rows, pred, y):
        per[r["domain"]].append(1.0 if p == t else 0.0)
    rpd = sorted(len(v) for v in per.values())
    dom_acc = {d: float(np.mean(v)) for d, v in per.items()}
    cnt = Counter(y.tolist())
    maj = max(cnt.values()) / float(n)
    st = dict(n_rows=n, n_domains=len(per),
              rows_per_domain=dict(min=rpd[0], median=int(np.median(rpd)), max=rpd[-1]),
              class_counts=dict(cnt), majority_rate=float(maj),
              acc=k / float(n), acc_ci=[lo, hi],
              balanced_acc=float(balanced_accuracy_score(y, pred)),
              domain_mean_acc=float(np.mean(list(dom_acc.values()))),
              domain_sd_acc=float(np.std(list(dom_acc.values()), ddof=1)) if len(dom_acc) > 1 else float("nan"),
              covers_chance=bool(lo <= chance <= hi),
              equivalent_to_chance=bool(abs(k / float(n) - chance) <= CHANCE_TOL
                                        and hi <= chance + CHANCE_UPPER_SLACK),
              usable=bool(len(per) >= USABLE_MIN_DOMAINS
                          and rpd[0] >= USABLE_MIN_ROWS_PER_DOMAIN
                          and n >= USABLE_MIN_ROWS))
    if refit and len(per) >= 3 and n >= 30:
        # THE DIAGNOSTIC PR-050 DOES NOT ASK FOR, AND SHOULD.  The frozen classifier being
        # at chance inside a stratum is not the same as the surface features being
        # uninformative inside it: the stratification selects rows the frozen fit happens
        # to get wrong.  A classifier REFIT inside the stratum, domain-grouped, answers the
        # question the kill condition is actually about.
        X = np.asarray([(featfn or FEAT)(r) for r in rows], dtype=float)
        g = np.asarray([r["domain"] for r in rows])
        nsp = min(5, len(set(g.tolist())))
        preds = np.empty(len(y), dtype=object)
        for tri, tei in GroupKFold(n_splits=nsp).split(X, y, groups=g):
            if len(set(y[tri].tolist())) < 2:
                preds[tei] = y[tri][0]
                continue
            sc = StandardScaler()
            c = LogisticRegression(max_iter=4000, random_state=seed)
            c.fit(sc.fit_transform(X[tri]), y[tri])
            preds[tei] = c.predict(sc.transform(X[tei]))
        st["refit_within_acc"] = float(accuracy_score(y, preds))
        st["refit_within_bal"] = float(balanced_accuracy_score(y, preds))
        st["refit_n_splits"] = nsp
    return st


def _balanced_subsample(fit, bins, chance, seed=20260907, mut=None):
    """The STRONGEST form of the stratification: DESIGN OPTION (a) of REVIEW2 B.2.3.

    Binning alone does not make a stratum surface-matched.  PR-050's own nuisance_floor
    says "within a surface-matched stratum the surface classifier is at chance BY
    CONSTRUCTION"; that is true only if the ARMS ARE EQUALLY FREQUENT inside the stratum,
    and conditioning on a predicted score does not make them so.  Here every
    (domain x stratum) cell is subsampled to the smallest arm, so the arms ARE equally
    frequent by construction, and the classifier's accuracy is then measured on what is
    left.  This is the most favourable test PR-050's kill condition can be given.
    """
    rng = np.random.RandomState(seed)
    keep = np.zeros(len(fit["y"]), dtype=bool)
    idx_all = np.arange(len(fit["y"]))
    for _bname, m in bins:
        sub = idx_all[m]
        by = defaultdict(lambda: defaultdict(list))
        for i in sub:
            by[fit["rows"][i]["domain"]][fit["y"][i]].append(i)
        for _dom, arms in by.items():
            if mut == "unbalanced_subsample":
                k = max(len(v) for v in arms.values())
            else:
                k = min(len(v) for v in arms.values())
            if len(arms) < len(fit["classes"]) or k == 0:
                continue          # this cell cannot be balanced -- it is DROPPED, counted
            for _c, v in arms.items():
                pick = rng.choice(v, size=min(k, len(v)), replace=False)
                keep[pick] = True
    if not keep.any():
        return None
    st = _stratum_stats(fit, keep, chance)
    st["arm_counts"] = dict(Counter(fit["y"][keep].tolist()))
    st["frac_retained"] = float(keep.sum()) / float(len(keep))
    return st


def z1(pr50, C, rows, assign, mut=None):
    tr = [r for r in rows if dsplit_of(assign, r["domain"]) == "train"]
    va = [r for r in rows if dsplit_of(assign, r["domain"]) == "validation"]
    if mut == "read_test":
        # The mutation puts TEST rows in front of the guard and nothing else.  The guard
        # RAISES, so no feature is ever computed on a test row and no test-set outcome
        # exists even inside the mutation run -- which is the behaviour being demonstrated.
        va = va + [r for r in rows if dsplit_of(assign, r["domain"]) == "test"]
    guard_no_test(tr + va, assign, "the Z1 fit/score sets", mut=mut)
    C.add("GUARD-TEST", "no TEST domain enters any fit or any evaluation in Z1/Z2 -- the "
                        "PR-048 primary has not been run and this script must not peek",
          all(dsplit_of(assign, r["domain"]) != "test" for r in tr + va),
          len(tr) + len(va),
          "train %d rows / %d domains, validation %d rows / %d domains, test rows used 0"
          % (len(tr), len(set(r["domain"] for r in tr)),
             len(va), len(set(r["domain"] for r in va))))

    # N3-style leakage guard, re-derived: no concept name in the demonstration block
    leak = [r for r in tr + va
            if re.search(r"\b(bombs?|knife|knives|guns?)\b", r["demo_block"], re.I)]
    C.add("Z1-leak", "N3 re-derived on the fitted text: NO row's demonstration block names "
                     "a concept in whole-word form, so the surface classifier cannot be "
                     "reading the label off the page",
          not leak, len(tr) + len(va),
          "%d/%d rows leak%s" % (len(leak), len(tr) + len(va),
                                 (": " + str([r["prompt_id"] for r in leak[:3]])) if leak else ""))

    tasks = OrderedDict()
    tasks["3way"] = (("bomb", "knife", "gun"), 1.0 / 3.0)
    tasks["knife_vs_gun"] = (("knife", "gun"), 0.5)

    out = dict(strata={}, unstratified={})
    for name, (classes, chance) in tasks.items():
        fit = _fit_surface(tr, va, classes, FEAT, mut=mut)
        base = _stratum_stats(fit, np.ones(len(fit["y"]), dtype=bool), chance)
        out["unstratified"][name] = dict(chance=chance, n_features=fit["n_features"],
                                         n_train=fit["n_train"], n_val=fit["n_val"],
                                         n_train_domains=fit["n_train_domains"],
                                         n_val_domains=fit["n_val_domains"], **base)
        C.add("Z1-fit-%s" % name,
              "the TRAIN-fit 17-feature surface classifier is ABOVE chance %.4f on the "
              "UNSTRATIFIED validation rows -- if it were not, there would be nothing for "
              "a stratification to remove and PR-050 would be moot" % chance,
              base["acc_ci"][0] > chance, base["n_rows"],
              "acc %.4f 95%% CI [%.4f, %.4f], balanced %.4f, domain-mean %.4f, "
              "%d rows / %d domains, %d features"
              % (base["acc"], base["acc_ci"][0], base["acc_ci"][1], base["balanced_acc"],
                 base["domain_mean_acc"], base["n_rows"], base["n_domains"], fit["n_features"]))

        sres = OrderedDict()
        for sname, kind, q in STRAT_SPECS:
            if kind in ("pref", "simplex"):
                bins = _strata_vector(fit["proba"], fit["classes"], kind, q, mut=mut)
            else:
                stat = fit["maxprob"] if kind == "maxprob" else fit["margin"]
                bins = _strata(stat, kind, q, mut=mut)
            covered = np.zeros(len(stat), dtype=int)
            per_bin = OrderedDict()
            for bname, m in bins:
                covered += m.astype(int)
                # Under --mutate the within-stratum refits are computed only where a CHECK
                # reads them (the q2 halves); they are measurements, not check targets, and
                # recomputing 174 grouped-CV fits per mutation buys nothing.
                st = _stratum_stats(fit, m, chance,
                                    refit=(mut is None or sname in ("maxprob_q2", "margin_q2")))
                if st is None:
                    raise ZeroBinding("stratum %s/%s bound ZERO rows" % (sname, bname))
                per_bin[bname] = st
            # POOLED over the strata: what a stratified analysis actually reports.  The
            # advantage over the WITHIN-STRATUM MAJORITY is the honest version -- a
            # stratification that only rebalances the classes lowers accuracy toward the
            # new prior without removing any surface information.
            N = float(sum(st["n_rows"] for st in per_bin.values()))
            pooled_acc = sum(st["n_rows"] * st["acc"] for st in per_bin.values()) / N
            pooled_maj = sum(st["n_rows"] * st["majority_rate"] for st in per_bin.values()) / N
            pooled_refit = (sum(st["n_rows"] * st.get("refit_within_acc", float("nan"))
                                for st in per_bin.values()) / N) if mut is None else float("nan")
            sres[sname] = dict(kind=kind, q=q, statistic=kind, bins=per_bin,
                               n_bins=len(bins), n_rows_covered=int(N),
                               pooled_acc=pooled_acc, pooled_majority=pooled_maj,
                               pooled_advantage_over_chance=pooled_acc - chance,
                               pooled_advantage_over_majority=pooled_acc - pooled_maj,
                               pooled_refit_within_acc=pooled_refit,
                               partition_ok=bool(kind in ("margin_tail", "pref")
                                                 or (covered == 1).all()))
            bal = _balanced_subsample(fit, bins, chance, mut=mut)
            if bal is None:
                raise ZeroBinding("balanced subsample of %s bound ZERO rows" % sname)
            sres[sname]["balanced"] = bal
            if sname == "maxprob_q2":
                cnts = sorted(bal["arm_counts"].values())
                C.add("Z1-armbalance-%s" % name,
                      "the arm-balanced subsample really is balanced: every concept arm "
                      "carries the SAME number of rows, which is the condition PR-050's "
                      "nuisance_floor asserts holds 'by construction'",
                      len(set(cnts)) == 1 and len(cnts) == len(fit["classes"]),
                      bal["n_rows"], "arm counts %s over %d rows (%.1f%% retained)"
                      % (bal["arm_counts"], bal["n_rows"], 100.0 * bal["frac_retained"]))
            if kind not in ("margin_tail", "pref"):
                C.add("Z1-part-%s-%s" % (name, sname),
                      "stratification %s PARTITIONS the validation rows: every row lands in "
                      "exactly one stratum, and there is more than one stratum" % sname,
                      bool((covered == 1).all()) and len(bins) > 1, len(stat),
                      "%d bins, rows covered exactly once %d/%d"
                      % (len(bins), int((covered == 1).sum()), len(stat)))
        out["strata"][name] = sres

        # Does the stratification remove surface INFORMATION, or only surface CONFIDENCE?
        lowest = None
        for sn in ("maxprob_q2", "margin_q2"):
            if sn in sres:
                bn = list(sres[sn]["bins"])[0]
                lowest = (sn, bn, sres[sn]["bins"][bn])
                break
        if lowest is not None:
            st = lowest[2]
            C.add("Z1-refit-%s" % name,
                  "inside the LOWEST-confidence half -- the stratum most favourable to "
                  "PR-050 -- a surface classifier REFIT within the stratum "
                  "(domain-grouped %d-fold CV, same 17 features) is at chance %.4f. If it "
                  "is not, the stratification removed the frozen classifier's CONFIDENCE "
                  "but not the surface INFORMATION, and the stratum is not surface-matched"
                  % (st.get("refit_n_splits", 0), chance),
                  abs(st.get("refit_within_acc", 1.0) - chance) <= CHANCE_TOL,
                  st["n_rows"],
                  "%s/%s: frozen acc %.4f, REFIT-within acc %.4f (balanced %.4f) against "
                  "chance %.4f, over %d rows / %d domains"
                  % (lowest[0], lowest[1], st["acc"], st.get("refit_within_acc", float("nan")),
                     st.get("refit_within_bal", float("nan")), chance,
                     st["n_rows"], st["n_domains"]))

        # THE ANSWER
        bal_hits = [(sn, "ARM-BALANCED", sv["balanced"]) for sn, sv in sres.items()
                    if sv["balanced"]["usable"] and sv["balanced"]["equivalent_to_chance"]]
        bal_all = [(sn, "ARM-BALANCED", sv["balanced"]) for sn, sv in sres.items()]
        bal_closest = min(bal_all, key=lambda x: abs(x[2]["acc"] - chance))
        C.add("Z1-balanced-%s" % name,
              "ARM-BALANCED strata (every domain x stratum cell subsampled to its smallest "
              "arm, so the concepts are equally frequent inside the stratum BY "
              "CONSTRUCTION -- PR-050's own premise, enforced rather than assumed): at "
              "least one stratification drives the surface classifier to chance %.4f under "
              "the EQUIV rule with usable n" % chance,
              bool(bal_hits), sum(x[2]["n_rows"] for x in bal_all),
              "%d/%d stratifications reach chance; closest = %s acc %.4f 95%% CI "
              "[%.4f, %.4f] on %d rows (%.1f%% of the population) / %d domains, arms %s, "
              "refit-within %.4f"
              % (len(bal_hits), len(bal_all), bal_closest[0], bal_closest[2]["acc"],
                 bal_closest[2]["acc_ci"][0], bal_closest[2]["acc_ci"][1],
                 bal_closest[2]["n_rows"], 100.0 * bal_closest[2]["frac_retained"],
                 bal_closest[2]["n_domains"], bal_closest[2]["arm_counts"],
                 bal_closest[2].get("refit_within_acc", float("nan"))))

        hits = [(sn, bn, st) for sn, sv in sres.items() for bn, st in sv["bins"].items()
                if st["usable"] and st["equivalent_to_chance"]]
        soft = [(sn, bn, st) for sn, sv in sres.items() for bn, st in sv["bins"].items()
                if st["usable"] and st["covers_chance"]]
        best = max(hits, key=lambda x: x[2]["n_rows"]) if hits else None
        allb = [(sn, bn, st) for sn, sv in sres.items() for bn, st in sv["bins"].items()]
        closest_any = min(allb, key=lambda x: abs(x[2]["acc"] - chance))
        usable_all = [x for x in allb if x[2]["usable"]]
        closest_usable = (min(usable_all, key=lambda x: abs(x[2]["acc"] - chance))
                          if usable_all else None)
        out.setdefault("verdict", {})[name] = dict(
            chance=chance,
            n_usable_strata=sum(1 for sv in sres.values() for st in sv["bins"].values()
                                if st["usable"]),
            n_at_chance_equiv=len(hits), n_at_chance_covers=len(soft),
            best=None if best is None else dict(strat=best[0], bin=best[1], **best[2]),
            best_covers=None if not soft else dict(
                strat=max(soft, key=lambda x: x[2]["n_rows"])[0],
                bin=max(soft, key=lambda x: x[2]["n_rows"])[1],
                **max(soft, key=lambda x: x[2]["n_rows"])[2]),
            reached_chance=bool(hits),
            reached_chance_arm_balanced=bool(bal_hits),
            n_arm_balanced_at_chance=len(bal_hits),
            arm_balanced_closest=dict(strat=bal_closest[0], **bal_closest[2]),
            arm_balanced=OrderedDict((sn, sv["balanced"]) for sn, sv in sres.items()),
            n_strata_scored=len(allb),
            closest_any=dict(strat=closest_any[0], bin=closest_any[1], **closest_any[2]),
            closest_usable=(None if closest_usable is None else
                            dict(strat=closest_usable[0], bin=closest_usable[1],
                                 **closest_usable[2])))
        v = out["verdict"][name]
        C.add("Z1-answer-%s" % name,
              "PR-050 KILL CONDITION on the %s contrast: SOME preregistered-style "
              "stratification with USABLE n (>=%d domains, >=%d rows/domain, >=%d rows) "
              "drives the TRAIN-fit surface classifier to chance %.4f (|acc-chance|<=%.2f "
              "and CI upper <= chance+%.2f)"
              % (name, USABLE_MIN_DOMAINS, USABLE_MIN_ROWS_PER_DOMAIN, USABLE_MIN_ROWS,
                 chance, CHANCE_TOL, CHANCE_UPPER_SLACK),
              bool(hits), sum(1 for sv in sres.values() for st in sv["bins"].values()),
              "%d strata scored, %d usable; %d at chance under the EQUIV rule, %d under "
              "the weaker CI-COVERS rule | CLOSEST OF ALL: %s/%s acc=%.4f (n=%d rows, "
              "%d domains, usable=%s) | CLOSEST USABLE: %s"
              % (v["n_strata_scored"], v["n_usable_strata"], v["n_at_chance_equiv"],
                 v["n_at_chance_covers"],
                 v["closest_any"]["strat"], v["closest_any"]["bin"], v["closest_any"]["acc"],
                 v["closest_any"]["n_rows"], v["closest_any"]["n_domains"],
                 v["closest_any"]["usable"],
                 ("%s/%s acc=%.4f n=%d" % (v["closest_usable"]["strat"],
                                           v["closest_usable"]["bin"],
                                           v["closest_usable"]["acc"],
                                           v["closest_usable"]["n_rows"]))
                 if v["closest_usable"] else "NONE"))
    return out


# ================================================================= Z2
def z2(pr50, C, z1res, rows, assign, mut=None):
    """Power for a DOMAIN-MEAN estimator built on m rows per domain instead of all of them.

    A per-domain accuracy measured on m rows is the true domain accuracy plus binomial
    noise, so the between-domain SD the estimator actually sees is

        sd_obs(m) = sqrt( sd_between^2 + p(1-p)/m )

    and it GROWS as the strata shrink.  Ignoring that term is mutation `no_binomial_noise`,
    and it is the whole reason PR-048's and PR-049's power do not transfer.
    """
    alpha = pr50.require("primary", "alpha")
    n_test = pr50.require("primary", "n_test_domains")
    alpha_holm = alpha / 2.0

    def sd_obs(sd_b, p, m):
        if mut == "no_binomial_noise":
            return sd_b
        return math.sqrt(sd_b ** 2 + p * (1.0 - p) / float(m))

    def conj(n, delta, sd, a):
        pw_t = P.t_power(n, delta, sd, alpha=a)
        pi = float(stats.norm.cdf(delta / sd)) if sd > 0 else 1.0
        pw_s = P.sign_power(n, pi, 0.5, a)
        return dict(t_arm=pw_t, sign_arm=pw_s, pi=pi, upper_bound=min(pw_t, pw_s),
                    lower_bound=pw_t * pw_s)

    def row(sd_b, p, m, label):
        s = sd_obs(sd_b, p, m)
        mde = P.t_mde(n_test, s, alpha=alpha, power=0.80,
                      drop_beta=(mut == "mde_no_beta"))
        mde_h = P.t_mde(n_test, s, alpha=alpha_holm, power=0.80,
                        drop_beta=(mut == "mde_no_beta"))
        cw = conj(n_test, BAR_DELTA, s, alpha)
        ch = conj(n_test, BAR_DELTA, s, alpha_holm)
        return dict(label=label, m=m, chance=p, sd_between=sd_b, sd_observed=s,
                    binomial_component=math.sqrt(p * (1 - p) / float(m)),
                    mde_alpha05=mde, mde_alpha_holm=mde_h,
                    conj_alpha05=cw, conj_alpha_holm=ch,
                    powered=bool(cw["upper_bound"] >= 0.80 and ch["upper_bound"] >= 0.80
                                 and mde <= BAR_DELTA))

    # m for the FULL population, re-derived from the raw rows rather than assumed
    va = [r for r in rows if dsplit_of(assign, r["domain"]) == "validation"]
    guard_no_test(va, assign, "the Z2 m-derivation", mut=mut)
    m_full_3 = int(np.median(list(Counter(r["domain"] for r in va).values())))
    m_full_2 = int(np.median(list(Counter(r["domain"] for r in va
                                          if r["concept"] in ("knife", "gun")).values())))
    C.add("Z2-m", "the FULL-population rows per domain are re-derived from the raw bank "
                  "rows, not taken from PR-048's power block",
          m_full_3 == 60 and m_full_2 == 40, len(va),
          "3-way m=%d/domain (PR-048 power assumes 60), knife-vs-gun m=%d/domain"
          % (m_full_3, m_full_2))

    # IS 0.1406 A VARIANCE COMPONENT, OR AN OBSERVED SD?  It matters: if it were already an
    # observed per-domain SD at m=60 then adding p(1-p)/m on top would DOUBLE COUNT the
    # binomial noise and every MDE below would be overstated.  PR-048's own power block
    # publishes icc=0.0884 and deff_at_m60=6.22 alongside it, and those pin the answer:
    #     sqrt(icc * p(1-p)) = sqrt(0.0884 * 2/9) = 0.1402 ~= 0.1406,
    #     deff = 1 + (m-1)*icc = 1 + 59*0.0884 = 6.22,  n_eff = 23*60/6.22 = 221.9 ~= 222.
    # Both reproduce, so 0.1406 is the BETWEEN-DOMAIN COMPONENT and the inflation below is
    # not double counting.  Checked rather than assumed.
    pr048 = load_prereg(PR048)
    icc = pr048.require("power", "icc")
    deff_pub = pr048.require("power", "deff_at_m60")
    neff_pub = pr048.require("power", "n_eff_test_rows")
    sd_from_icc = math.sqrt(icc * (1.0 / 3.0) * (2.0 / 3.0))
    deff_derived = 1.0 + (60 - 1) * icc
    neff_derived = n_test * 60 / deff_derived
    C.add("Z2-icc", "PR-048's between_domain_sd 0.1406 is a VARIANCE COMPONENT, not an "
                    "observed per-domain SD -- so adding the binomial term p(1-p)/m is a "
                    "correction, not a double count. Verified by reproducing PR-048's own "
                    "icc, deff and n_eff from it",
          abs(sd_from_icc - SD_BETWEEN_WORKING) < 0.002
          and abs(deff_derived - deff_pub) < 0.02
          and abs(neff_derived - neff_pub) < 1.0, 3,
          "sqrt(icc*p(1-p)) = %.4f vs published sd %.4f | deff = %.4f vs %.4f | n_eff = "
          "%.2f vs %s" % (sd_from_icc, SD_BETWEEN_WORKING, deff_derived, deff_pub,
                          neff_derived, neff_pub))

    # The MDE must carry the TYPE-II term.  Dropping it (mutation `mde_no_beta`) returns
    # the alpha-only critical offset, which is strictly smaller and would understate what
    # a within-stratum analysis can detect -- the exact direction of error that turns an
    # underpowered design into a "powered" one on paper.
    _sd = sd_obs(SD_BETWEEN_WORKING, 1.0 / 3.0, 60)
    mde_full = P.t_mde(n_test, _sd, alpha=alpha, power=0.80,
                       drop_beta=(mut == "mde_no_beta"))
    mde_alpha_only = P.t_mde(n_test, _sd, alpha=alpha, power=0.80, drop_beta=True)
    C.add("Z2-mde", "the 80%-power MDE strictly exceeds the alpha-only critical offset, "
                    "i.e. the type-II term is actually in the arithmetic",
          mde_full > mde_alpha_only + 1e-9, 1,
          "MDE(power=0.80) = %.4f vs alpha-only critical offset %.4f at sd=%.4f, n=%d"
          % (mde_full, mde_alpha_only, _sd, n_test))

    tab = []
    for name, p, m_full in (("3way", 1.0 / 3.0, m_full_3),
                            ("knife_vs_gun", 0.5, m_full_2)):
        tab.append(row(SD_BETWEEN_WORKING, p, m_full, "%s FULL population" % name))
        v = z1res["verdict"][name]
        cands = []
        if v.get("best"):
            cands.append(("best EQUIV stratum %s/%s" % (v["best"]["strat"], v["best"]["bin"]),
                          v["best"]))
        if v.get("arm_balanced_closest"):
            ab = v["arm_balanced_closest"]
            cands.append(("ARM-BALANCED stratum %s (acc %.4f, %s chance, %d rows over %d "
                          "domains)" % (ab["strat"], ab["acc"],
                                        "AT" if ab["equivalent_to_chance"] else "NOT at",
                                        ab["n_rows"], ab["n_domains"]), ab))
        if v.get("closest_usable"):
            cands.append(("CLOSEST-TO-CHANCE USABLE stratum %s/%s (NOT at chance: acc %.4f)"
                          % (v["closest_usable"]["strat"], v["closest_usable"]["bin"],
                             v["closest_usable"]["acc"]), v["closest_usable"]))
        if v.get("best_covers"):
            cands.append(("best CI-COVERS stratum %s/%s"
                          % (v["best_covers"]["strat"], v["best_covers"]["bin"]),
                          v["best_covers"]))
        # and the generic ladder, so the answer does not depend on which stratum Z1 picked
        for q in (2, 3, 4, 5, 10):
            cands.append(("1/%d of the population" % q,
                          dict(rows_per_domain=dict(median=max(int(round(m_full / q)), 1)))))
        for lab, st in cands:
            m = max(int(st["rows_per_domain"]["median"]), 1)
            tab.append(row(SD_BETWEEN_WORKING, p, m, "%s :: %s" % (name, lab)))
        # the SD ceiling, on the full population and on a quarter of it
        tab.append(row(SD_BETWEEN_CEILING, p, m_full, "%s FULL population @ SD ceiling" % name))
        tab.append(row(SD_BETWEEN_CEILING, p, max(m_full // 4, 1),
                       "%s 1/4 population @ SD ceiling" % name))

    require_nonempty(len(tab), "the Z2 power table")
    full = [t for t in tab if t["label"].endswith("FULL population")]
    quarters = [t for t in tab if "1/4 of the population" in t["label"]]
    C.add("Z2-inflation", "stratifying INFLATES the SD the domain-mean estimator sees: the "
                          "observed SD at a quarter of the rows exceeds the observed SD at "
                          "the full population, for both contrasts",
          all(q["sd_observed"] > f["sd_observed"] for f, q in zip(full, quarters)),
          len(tab),
          "; ".join("%s: sd %.4f (m=%d) -> %.4f (m=%d), MDE %.4f -> %.4f"
                    % (f["label"].split()[0], f["sd_observed"], f["m"],
                       q["sd_observed"], q["m"], f["mde_alpha05"], q["mde_alpha_holm"])
                    for f, q in zip(full, quarters)))

    powered_any = {}
    for name in ("3way", "knife_vs_gun"):
        v = z1res["verdict"][name]
        rel = [t for t in tab if t["label"].startswith(name) and ("stratum" in t["label"])]
        powered_any[name] = dict(
            n_candidates=len(rel),
            any_powered=bool(rel) and any(t["powered"] for t in rel),
            rows=rel)
        C.add("Z2-answer-%s" % name,
              "at n=%d TEST domains a WITHIN-STRATUM domain-mean estimator on the strata Z1 "
              "actually produces clears 0.80 conjunctive power (permutation AND sign test) "
              "for a delta of +%.2f at both alpha=%g and the Holm alpha=%.3f"
              % (n_test, BAR_DELTA, alpha, alpha_holm),
              powered_any[name]["any_powered"], max(len(rel), 0),
              ("no usable at-chance stratum exists for %s, so there is no within-stratum "
               "estimator to power" % name) if not rel else
              "; ".join("%s m=%d sd=%.4f MDE=%.4f (Holm %.4f) conj=%.3f (Holm %.3f) -> %s"
                        % (t["label"].split("::")[-1].strip(), t["m"], t["sd_observed"],
                           t["mde_alpha05"], t["mde_alpha_holm"],
                           t["conj_alpha05"]["upper_bound"], t["conj_alpha_holm"]["upper_bound"],
                           "POWERED" if t["powered"] else "UNDERPOWERED") for t in rel))
    return dict(alpha=alpha, alpha_holm=alpha_holm, n_test=n_test, bar_delta=BAR_DELTA,
                sd_between_working=SD_BETWEEN_WORKING, sd_between_ceiling=SD_BETWEEN_CEILING,
                m_full_3way=m_full_3, m_full_2way=m_full_2, table=tab, answer=powered_any)


# ================================================================= driver
def run(mut=None, toks_cache=None, quick=False):
    C = Checks()
    out = dict(mutation=mut)
    pr50 = load_prereg(PR050)
    pr51 = load_prereg(PR051)
    C.add("PRE-frozen", "both preregistrations load through dcs_ts_prereg (FROZEN status, "
                        "every pinned *_sha16 verified against the file on disk)",
          pr50.obj["status"] == "FROZEN" and pr51.obj["status"] == "FROZEN", 2,
          "%s %s / %s %s" % (pr50.obj["id"], pr50.obj["status"], pr51.obj["id"],
                             pr51.obj["status"]))

    rows, n_excluded, excluded = B.load_probe_rows(pr50, mut=mut)
    if mut == "plant_concept_in_demo":
        for r in rows:
            if r["concept"] == "gun":
                r["demo_block"] = r["demo_block"] + " The gun was recovered."
                break
    m, assign = B.load_split(pr50, mut=mut)
    doms = sorted(set(r["domain"] for r in rows))
    counts = Counter(dsplit_of(assign, d) for d in doms)
    C.add("POP-01", "the probe population binds from RAW bank rows to 6840 rows = 114 "
                    "domains x 2 codewords x 3 concepts x 10 family slots, cell C, "
                    "semantic_one_word, n_examples=4, with both whole-population "
                    "exclusions applied",
          len(rows) == 6840 and len(doms) == 114 and len(excluded) == 2, len(rows),
          "%d rows, %d domains, excluded %s (%d rows dropped), arms %s"
          % (len(rows), len(doms), excluded, n_excluded,
             dict(Counter(r["concept"] for r in rows))))
    C.add("POP-02", "the domain split is 68 train / 23 validation / 23 test and every "
                    "analysed domain is assigned",
          counts.get("train") == 68 and counts.get("validation") == 23
          and counts.get("test") == 23 and None not in counts, len(doms),
          "%s" % dict(counts))

    # ---- W3 (prompt-only; binds the WHOLE population, TEST prompts included) ----------
    if toks_cache is None:
        toks_cache = w3_tokenize(rows, C)
    else:
        C.add("W3-tok", "the control site is re-derived by REPRODUCING the extractor's own "
                        "tokenization path", True, len(toks_cache[0]),
              "reused the cached tokenization of %d prompts" % len(toks_cache[0]))
    toks, gen_suffix, n_gen, tok = toks_cache
    out["W3"] = w3(pr51, C, toks, gen_suffix, n_gen, tok, mut=mut)

    # ---- Z1 / Z2 (TRAIN + VALIDATION ONLY) --------------------------------------------
    out["Z1"] = z1(pr50, C, rows, assign, mut=mut)
    out["Z2"] = z2(pr50, C, out["Z1"], rows, assign, mut=mut)
    out["checks"] = {k: dict(v) for k, v in C.rows.items()}
    out["n_fail"] = C.n_fail
    return C, out, toks_cache


MUTATIONS = [
    ("w3_perturb_final_token", "W3-a", "change one knife prompt's final token id"),
    ("w3_codeword_at_end", "W3-b", "move one prompt's last codeword occurrence onto the final position"),
    ("w3_concept_at_end", "W3-c", "make one prompt's final position decode to ' bomb'"),
    ("w3_drop_arm", "W3-d", "drop the gun arm of one (codeword, prompt_id)"),
    ("w3_no_generation_prompt", "W3-scaffold", "claim the template appends no generation prompt"),
    ("empty_population", "W3-d", "bind the checks to an EMPTY prompt set"),
    ("keep_excluded_domains", "POP-01", "keep restaurant_kitchen and subway_station"),
    ("pool_doses", "POP-01", "pool n_examples=4 and n_examples=8 into one population"),
    ("corrupt_split", "POP-02", "declare five TEST domains TRAIN as well"),
    ("read_test", "GUARD-TEST", "let TEST domains into the fit and evaluation sets"),
    ("plant_concept_in_demo", "Z1-leak", "plant the literal word 'gun' in one demonstration block"),
    ("shuffle_labels", "Z1-fit-3way", "permute the TRAIN labels against their own features"),
    ("strat_one_bin", "Z1-part-3way-maxprob_q2", "collapse every stratification to one bin"),
    ("mde_no_beta", "Z2-mde", "drop the type-II term from the MDE"),
    ("no_binomial_noise", "Z2-inflation", "ignore the binomial component of the per-domain SD"),
    ("unbalanced_subsample", "Z1-armbalance-knife_vs_gun", "subsample each cell to its LARGEST arm instead of its smallest"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    t0 = time.time()
    C, out, toks_cache = run()
    sys.stdout.write("\n=== BASELINE ===\n")
    C.report()
    sys.stdout.write("  %d check(s) FAIL of %d\n" % (C.n_fail, len(C.rows)))

    if a.mutate:
        sys.stdout.write("\n=== MUTATIONS ===\n")
        red = 0
        rec = []
        for name, target, desc in MUTATIONS:
            try:
                Cm, _, _ = run(mut=name, toks_cache=toks_cache)
                r = Cm.rows.get(target)
                went_red = (r is not None and not r["ok"])
                detail = "%s -> %s (n=%d)" % (target, "FAIL" if went_red else "PASS",
                                              r["n_bound"] if r else -1)
            except (ZeroBinding, KeyError, ValueError, AssertionError) as e:
                went_red = True
                detail = "%s -> REFUSED: %s" % (target, str(e)[:110])
            red += 1 if went_red else 0
            rec.append(dict(mutation=name, target=target, description=desc,
                            red=bool(went_red), detail=detail))
            sys.stdout.write("  [%s] %-26s %s | %s\n"
                             % ("RED" if went_red else "GREEN", name, desc, detail))
        sys.stdout.write("  %d/%d mutations turned their target check RED\n"
                         % (red, len(MUTATIONS)))
        out["mutations"] = rec
        out["n_mutations_red"] = red
        out["n_mutations"] = len(MUTATIONS)

    out["seconds"] = round(time.time() - t0, 1)
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(out, fh, indent=1, default=float)
        sys.stdout.write("\nwrote %s\n" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
