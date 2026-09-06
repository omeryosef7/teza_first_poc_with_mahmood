#!/usr/bin/env python3
"""DCS-PR-035 INDEPENDENT VERIFIER — rebuilt after `C-049` §22.5 and `C-053` §28.9.

WHY THIS FILE EXISTS
--------------------
`C-053` §28.9 records: *"No `PR-035` result may be promoted until the verifier is rebuilt, since a
verifier that reads the producer's derived fields proves nothing."*  `A-021` (§13) failed exactly
that way — it re-read the same derived JSON fields the producer wrote, so a broken producer and a
broken verifier agreed.  And its mutation harness passed on a corruption it never detected, because
it only required that *some* check failed (`C-049` §22.5).

RULES THIS FILE OBEYS, AND WHERE THEY COME FROM
-----------------------------------------------
1. It imports NOTHING from `scripts/dcs_bombness_specificity.py`.  Every quantity it needs is
   re-implemented here from the preregistration text.
2. It re-derives from LOWER-LEVEL artifacts only:
     * the bank `.jsonl` files under `data/boombness_prompts/`
     * each run's `metadata.json`, `DONE.json` and `results.jsonl`
     * each run's `cache/final_occurrence_reps.pt`
   The producer JSON is treated as a CLAIM to be tested, never as evidence.  The only producer
   fields read as *inputs* rather than claims are the ones §23.5's verdict rule is a function of
   (check `C8`), and that is stated explicitly there.
3. Its mutation harness (`--mutate`) matches every injected defect to the ONE check designated to
   catch it, and passes only if EVERY mutation is caught by ITS OWN check.  "Some check failed" is
   not acceptance here; that is the `C-049` §22.5 defect being corrected.

PRODUCER UNDER TEST
-------------------
  scripts/dcs_bombness_specificity.py, FROZEN at commit 1483f9c1
  sha256 = 50e2dde621bf89fcf706bb896f0e96ceb72a31af72d2cd9ee2ab1c75c18e7674
  output  = outputs/boombness/dcs_analysis/dcs_bombness_specificity.json

This verifier was written BLIND to that output — the file did not exist when this was written.

USAGE
-----
  python scripts/dcs_verify_pr035.py --self-test          # synthetic only, no real artifacts
  python scripts/dcs_verify_pr035.py --mutate             # prove each check can FAIL
  python scripts/dcs_verify_pr035.py                      # verify the real producer JSON
Exit codes: 0 = VERIFIED, 1 = REJECTED, 2 = CANNOT VERIFY (artifacts absent).
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import math
import os
import random
import re
import shutil
import sys
import tempfile

import numpy as np

# ------------------------------------------------------------------ preregistered constants
# Re-declared here on purpose.  Importing them from the producer would make a producer that
# changed a constant agree with a verifier that changed with it.
CODEWORDS         = ("button", "basket")
CONCEPTS          = ("bomb", "knife", "gun", "club")
PRIMARY_CLASSES   = ("bomb", "knife", "gun")     # club excluded from the primary, A-020 §8.3
PRIMARY_CODEWORD  = "button"
PRIMARY_CHANNEL   = "semantic_one_word"          # PR-031c §9
PRIMARY_NEXAMPLES = (4, 8)                       # PR-031 §6.2
NULL_NEXAMPLES    = (0,)                         # PR-035 §23.2, the BLOCKING control
LAYER_BAND        = tuple(range(6, 15))          # PR-035 §23.6: L6-14, inclusive
C_GRID            = (0.01, 0.1, 1.0, 10.0)       # PR-031 §6.3
ALPHA             = 0.05
N_DOMAINS_EXPECTED = 6                           # §23.6: the independence unit is the DOMAIN
EXPECT_ROWS_PER_BANK = 2736                      # A-019 §2.2

# §23.1 / §28.1 population names, and the (cells, n_examples) each one is
POPULATIONS = (
    ("C",    ("C",), PRIMARY_NEXAMPLES),
    ("B",    ("B",), PRIMARY_NEXAMPLES),
    ("A",    ("A",), PRIMARY_NEXAMPLES),
    ("F",    ("F",), PRIMARY_NEXAMPLES),
    ("C_n0", ("C",), NULL_NEXAMPLES),
)

# ------------------------------------------------------------------ tolerances, with justification
#
# ACC_TOL — held-out accuracies.  Given the same rows, the same frozen (layer, C) picks and the same
# estimator, the pipeline is DETERMINISTIC; `R-080` §27.1 documents this pipeline reproducing to the
# last printed digit across three days and different hardware.  Per-domain accuracy is a rational
# k/n with n >= 12 on the real null population, so ANY genuine procedural difference moves the mean
# by at least 1/(6*12) = 0.0139.  1e-6 therefore absorbs float32 accumulation-order noise and
# nothing else: it is five orders of magnitude below the smallest real difference.
ACC_TOL = 1e-6
#
# Permutation p is a MONTE-CARLO estimate, and this verifier deliberately draws its own permutations
# from its own seed, so exact agreement is neither expected nor desirable (agreeing exactly would
# mean the verifier had copied the producer's RNG rather than re-implemented the test).  Two
# independent estimates of the same p from n draws each have Var(p1 - p2) = 2p(1-p)/n, so a 3-sigma
# band is 3*sqrt(2*pbar*(1-pbar)/n).  It is floored at 3/(n+1), the granularity of the estimator
# itself (p can only take values (1+k)/(1+n)).  Agreement WITHIN that band is all that can be
# demanded.  Separately, and this is the part that actually protects the run, the two estimates must
# agree on the DECISION p <= ALPHA; if the decision is inside the band it is not resolvable at this
# n_perm and the check FAILS asking for more permutations rather than guessing.
def mc_tolerance(p1: float, p2: float, n_perm: int) -> float:
    pbar = 0.5 * (p1 + p2)
    se = math.sqrt(max(pbar * (1.0 - pbar), 1e-12) * 2.0 / max(n_perm, 1))
    return max(3.0 * se, 3.0 / (n_perm + 1.0))


# ------------------------------------------------------------------ report plumbing
class Report:
    """An ordered list of independent checks.  Every check can FAIL on its own."""

    def __init__(self):
        self.rows = []            # (check_id, status, message)
        self.notes = []

    def add(self, cid, ok, msg):
        self.rows.append((cid, "PASS" if ok else "FAIL", msg))
        return ok

    def note(self, msg):
        self.notes.append(msg)

    def failed(self):
        return [c for c, s, _ in self.rows if s == "FAIL"]

    def status_of(self, cid):
        for c, s, _ in self.rows:
            if c == cid:
                return s
        return "ABSENT"

    def ok(self):
        return bool(self.rows) and not self.failed()

    def print(self, title="PR-035 VERIFIER"):
        w = max([len(c) for c, _, _ in self.rows] + [10])
        print(f"\n=== {title} ===")
        for c, s, m in self.rows:
            print(f"  [{s}] {c:<{w}}  {m}")
        for n in self.notes:
            print(f"  (note) {n}")
        print(f"  ---> {'VERIFIED' if self.ok() else 'REJECTED'}"
              + ("" if self.ok() else f"  failing: {', '.join(self.failed())}"))


# ------------------------------------------------------------------ artifact loading (LOW LEVEL)
def sha16_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def load_bank(path):
    with open(path) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def bank_path(bank_dir, cw, cc):
    return os.path.join(bank_dir, f"boombness_prompt_bank_{cw}_{cc}.jsonl")


def resolve_runs(root, prefix):
    """Same tag convention as the extractor: <prefix>_<codeword>_<concept>_<stamp>."""
    out = {}
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            hits = sorted(glob.glob(os.path.join(root, f"{prefix}_{cw}_{cc}_*")))
            if hits:
                out[(cw, cc)] = hits[-1]
    return out


_BLOB_INFO = {}


def blob_info(run_dir):
    """(layers, blob-level metadata, set of prompt_ids) for a run's rep cache.  Cached: the real
    caches are ~200 MB each and several checks need only their shape."""
    key = os.path.realpath(run_dir)
    st = os.stat(os.path.join(run_dir, "cache", "final_occurrence_reps.pt"))
    stamp = (st.st_size, st.st_mtime_ns)
    if _BLOB_INFO.get(key, (None,))[0] != stamp:
        import torch
        blob = torch.load(os.path.join(run_dir, "cache", "final_occurrence_reps.pt"),
                          map_location="cpu")
        info = (list(blob["layers"]), {k: blob[k] for k in blob if k != "reps"},
                set(blob["reps"].keys()))
        _BLOB_INFO[key] = (stamp, info)
        del blob
    return _BLOB_INFO[key][1]


def load_reps_subset(run_dir, pids):
    """{pid: np.float32[len(layers), H]} for `pids` only, so memory stays bounded."""
    import torch
    blob = torch.load(os.path.join(run_dir, "cache", "final_occurrence_reps.pt"), map_location="cpu")
    out = {k: v.float().numpy() for k, v in blob["reps"].items() if k in pids}
    layers = list(blob["layers"])
    del blob
    return layers, out


# ------------------------------------------------------------------ §23.1 / §28.1 exclusion rule
def concept_pattern(concept):
    return re.compile(r"\b" + re.escape(concept) + r"\b", re.IGNORECASE)


def is_excluded(row, pat, concept):
    """C-053 §28.1's UNIFORM rule, re-implemented from the log text, not from the producer:

        EXCLUDE every row whose `full_prompt` contains its bank's concept word on word boundaries
        (case-insensitively) AND whose `target_surface` is not that word.

    Prompt text + one design field.  No cell is named; no outcome is read.
    """
    return bool(pat.search(row.get("full_prompt", ""))) and row.get("target_surface") != concept


def population_rows(bank, concept, channel, cells, nexamples):
    """Independently select the PR-035 population and split it retained/excluded."""
    pat = concept_pattern(concept)
    kept, dropped = [], []
    for r in bank:
        if r.get("query_kind") != channel or r.get("cell") not in cells:
            continue
        if nexamples is not None and r.get("n_examples") not in nexamples:
            continue
        (dropped if is_excluded(r, pat, concept) else kept).append(r)
    return kept, dropped


def count_key(r):
    """The producer's own reporting key shape: '<cell>/<bank_block>/n<n_examples>'."""
    return f'{r["cell"]}/{r.get("bank_block")}/n{r["n_examples"]}'


def counter_of(rows):
    return dict(collections.Counter(count_key(r) for r in rows))


# ==================================================================================================
# INDEPENDENT RE-IMPLEMENTATION OF THE DECLARED STATISTIC
# Written from the preregistration text (PR-031 §6.3, PR-031a §7.6, PR-031d §10.3, PR-035 §23.2,
# §23.6, C-053 §28.2), not from the producer source.
# ==================================================================================================
def _X(rows, layer, layers):
    j = layers.index(layer)
    return np.stack([r["vec"][j] for r in rows])


def fit_score(train, test, layer, layers, C, classes, label_of):
    """L2 multinomial logistic regression, standardised on TRAINING-fold statistics only.

    Returns held-out accuracy, or None when the training fold does not carry >= 2 classes.
    """
    from sklearn.linear_model import LogisticRegression
    ytr = np.array([classes.index(label_of(r)) for r in train])
    yte = np.array([classes.index(label_of(r)) for r in test])
    if len(set(ytr.tolist())) < 2:
        return None
    Xtr, Xte = _X(train, layer, layers), _X(test, layer, layers)
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd = np.where(sd < 1e-8, 1.0, sd)
    Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd
    clf = LogisticRegression(C=C, max_iter=3000)
    clf.fit(Xtr, ytr)
    return float((clf.predict(Xte) == yte).mean())


def select_layer_C(sel_rows, layers, classes, label_of):
    """PR-031 §6.3: inner leave-one-domain-out over the SELECTION population only.

    Tie-breaking is first-wins in (layer ascending, C in the declared grid order), matching the
    strict `>` the preregistration's grid search implies.  The selection quantity is accuracy on the
    SELECTION cell — never on the confirmation cell.  That is the whole point of §23.6 and of
    C-053 §28.2, and `C5b` below tests that the producer actually did it.
    """
    doms = sorted({r["domain"] for r in sel_rows})
    best, best_acc = None, -1.0
    for L in LAYER_BAND:
        if L not in layers:
            continue
        for C in C_GRID:
            accs = []
            for d in doms:
                tr = [r for r in sel_rows if r["domain"] != d]
                te = [r for r in sel_rows if r["domain"] == d]
                if not tr or not te:
                    continue
                a = fit_score(tr, te, L, layers, C, classes, label_of)
                if a is not None:
                    accs.append(a)
            if accs and float(np.mean(accs)) > best_acc:
                best_acc, best = float(np.mean(accs)), (L, C)
    return best, best_acc


def loo_domain(rows, layers, classes, label_of, selection_rows, group="domain"):
    """Outer leave-one-GROUP-out with the (layer, C) picked on `selection_rows` MINUS that group.

    The held-out group is removed from BOTH the training population and the selection population,
    so no group is ever on both sides of the fold — the property `C5` asserts against the producer.
    """
    groups = sorted({r[group] for r in rows})
    per, picks, train_fold = {}, {}, {}
    for d in groups:
        tr = [r for r in rows if r.get(group) != d]
        te = [r for r in rows if r.get(group) == d]
        if not tr or not te:
            continue
        if len({label_of(r) for r in tr}) < len(classes):
            continue           # refuse a reduced class set (C-049 §22.5's fourth defect)
        sel = [r for r in selection_rows if r.get(group) != d]
        pick, _ = select_layer_C(sel, layers, classes, label_of)
        if pick is None:
            continue
        L, C = pick
        a = fit_score(tr, te, L, layers, C, classes, label_of)
        if a is None:
            continue
        per[d] = a
        picks[d] = dict(layer=L, C=C, n_test=len(te), n_train=len(tr))
        s = fit_score(tr, tr, L, layers, C, classes, label_of)
        if s is not None:
            train_fold[d] = s
    ch = 1.0 / len(classes)
    return dict(per_domain=per, picks=picks, train_fold_acc=train_fold, chance=ch, group=group,
                n_domains=len(per),
                mean_acc=(float(np.mean(list(per.values()))) if per else None),
                n_above_chance=int(sum(1 for v in per.values() if v > ch)))


def group_permute_labels(rows, rng, classes, group="domain"):
    """PR-031d §10.3 exchangeability: within each domain, relabel the whole CONCEPT GROUPS by a
    random permutation of the class set.  Whole groups, never rows — permuting rows would destroy
    the within-(domain, concept) correlation that a shared demonstration pool creates and would
    build an ANTI-CONSERVATIVE null."""
    lab = {}
    for d in sorted({r[group] for r in rows}):
        perm = list(classes)
        rng.shuffle(perm)
        lab[d] = dict(zip(classes, perm))
    return [dict(r, perm_label=lab[r[group]][r["concept"]]) for r in rows]


def permutation_p(rows, layers, classes, picks, n_perm, seed, observed_mean, group="domain"):
    """One-sided permutation p on the mean held-out accuracy, picks FROZEN.

    Freezing is licensed because the picks are selected on cell B (§23.6), which this permutation
    does not touch — the property `C5b` verifies rather than assumes.
    """
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(n_perm):
        prows = group_permute_labels(rows, rng, list(classes), group=group)
        per = {}
        for d in sorted({r[group] for r in prows}):
            if d not in picks:
                continue
            tr = [r for r in prows if r.get(group) != d]
            te = [r for r in prows if r.get(group) == d]
            if not tr or not te or len({r["perm_label"] for r in tr}) < len(classes):
                continue
            a = fit_score(tr, te, picks[d]["layer"], layers, picks[d]["C"], classes,
                          lambda r: r["perm_label"])
            if a is not None:
                per[d] = a
        if per:
            null.append(float(np.mean(list(per.values()))))
    if not null:
        return dict(n_perm=0, p_one_sided=None, null_mean=None)
    arr = np.array(null)
    return dict(n_perm=len(arr),
                p_one_sided=(1.0 + float((arr >= observed_mean).sum())) / (1.0 + len(arr)),
                null_mean=float(arr.mean()), null_sd=float(arr.std()),
                null_q95=float(np.quantile(arr, 0.95)))


# ==================================================================================================
# §23.5 VERDICT RULE, re-implemented from the LOG TEXT
# ==================================================================================================
VERDICT_CATEGORIES = ("VOID", "CANNOT ANSWER", "POSITIVE", "NOT ATTRIBUTABLE", "NEGATIVE")


def verdict_category(s):
    if not isinstance(s, str):
        return None
    t = s.strip().lstrip("⛔ ").strip()
    for c in VERDICT_CATEGORIES:
        if t.upper().startswith(c):
            return c
    return None


def derive_verdict(*, null_p, fit_capable, length_acc, probe_null_q95, primary_p, above_null,
                   ctrl_p, primary_present):
    """PR-035 §23.5's five clauses, in the order the preregistration fixes them.

    Clause 1 (the blocking null) comes first and is absolute: a fired null means VOID and NO primary
    (§23.2).  Clause 2 (class-set completeness) is check `C0`, not a number, and is folded in by the
    caller.  Clauses 3-5 are the 3-way, the knife-vs-club control and the length-only control.
    """
    if null_p is not None and null_p <= ALPHA:
        return "VOID", "blocking n_examples=0 null FIRED (§23.2)"
    if not primary_present:
        return "VOID", "no primary reported"
    if not fit_capable:
        return "VOID", "P2's fit does not beat chance on its own training fold (PR-031a §7.6)"
    length_ok = (length_acc is None or probe_null_q95 is None or length_acc <= probe_null_q95)
    if not length_ok:
        return "VOID", "length-only control reaches the probe's significance band (§23.5 clause 5)"
    if primary_p is None:
        return "CANNOT ANSWER", "the primary permutation produced no p"
    if ctrl_p is None and primary_p <= ALPHA and above_null:
        return "CANNOT ANSWER", "knife-vs-club control WAS NOT COMPUTED (§28.4)"
    if primary_p <= ALPHA and above_null and ctrl_p is not None and ctrl_p <= ALPHA:
        return "POSITIVE", "3-way clears and the bomb-absent control clears"
    if primary_p <= ALPHA and above_null:
        return "NOT ATTRIBUTABLE", "3-way clears, bomb-absent control does not (R-078 §21.2)"
    return "NEGATIVE", "the codeword state does not carry which concept was installed"


# ==================================================================================================
# THE CHECKS
# ==================================================================================================
CHECK_DOC = {
    "C0_CLASS_SET_COMPLETE":   "every declared class has a DONE-complete run, and the producer used exactly those runs (§23.3 / §28.4)",
    "C1_POPULATION_IDENTITY":  "retained/excluded row counts re-derived from the banks match the producer, per bank/cell/block/n (§23.1)",
    "C1b_EXCLUSION_BALANCE":   "the exclusion removes EQUAL counts from bomb/knife/gun, so it cannot itself induce a class asymmetry (§23.1)",
    "C2a_BANK_JOIN_METADATA":  "each run's metadata bank_file_sha16 / bank_path / bank_n_rows match the bank it is joined to (§28.3)",
    "C2b_REP_CACHE_BINDING":   "each rep cache belongs to ITS OWN run: ||rep[pid][L]|| equals that run's own results.jsonl hnorm|L (§28.3)",
    "C2c_ID_COLLISION_SHOWN":  "the 8-way prompt_id collision is demonstrated, not assumed, so C2a/C2b are shown to be NECESSARY (§28.3)",
    "C3_CONFIG_IDENTITY":      "layers, model, dtype, position, seed, tokenizer and layer convention identical across all runs",
    "C4_LAYER_BAND":           "every layer in every metadata, rep cache and reported pick lies in L6-14 (§23.6)",
    "C5_FOLD_DISCIPLINE":      "no test group appears in its own training fold: every pick's n_train/n_test re-derive from the banks",
    "C5b_SELECTION_POPULATION": "the blocking null's (layer, C) were selected on cell B, not on the null's own labels (§28.2)",
    "C6_BLOCKING_NULL":        "the n_examples=0 held-out accuracy and its group-permutation p reproduce independently (§23.2)",
    "C7_INDEPENDENCE_UNIT":    "every domain-level statistic reports n_domains = 6 and folds over domains, never over rows (§23.6)",
    "C8_VERDICT_CONSISTENCY":  "the §23.5 five-clause verdict re-derived from the producer's INPUT numbers equals its printed category",
    "C9_DERIVED_FIELD_RECOMPUTE": "the producer's own summary fields recompute from its per-fold numbers (mean_acc, chance, fit_capable, ...)",
}


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _walk(obj, path=""):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def _stage_a(cfg, rep):
    """Checks C0-C4: provenance, population, joins, config, layer band.

    Returns a context dict for `_stage_b`, or None when the producer JSON is absent."""
    # -------------------------------------------------- producer JSON: the CLAIM under test
    if not os.path.exists(cfg.json_path):
        rep.note(f"producer JSON absent: {cfg.json_path}")
        return None
    with open(cfg.json_path) as fh:
        res = json.load(fh)

    runs = resolve_runs(cfg.runs_root, cfg.run_prefix)

    # -------------------------------------------------- C0  class-set completeness
    need = [(PRIMARY_CODEWORD, c) for c in PRIMARY_CLASSES] + [(PRIMARY_CODEWORD, "club")]
    missing = [k for k in need if k not in runs]
    incomplete = [f"{cw}_{cc}" for (cw, cc), d in runs.items()
                  if not os.path.exists(os.path.join(d, "DONE.json"))]
    prov = res.get("provenance", {})
    prov_keys = set(prov)
    mine_keys = {f"{cw}_{cc}" for cw, cc in runs}
    same_runs = all(os.path.realpath(prov.get(f"{cw}_{cc}", {}).get("run_dir", "")) ==
                    os.path.realpath(d) for (cw, cc), d in runs.items()
                    if f"{cw}_{cc}" in prov)
    rep.add("C0_CLASS_SET_COMPLETE",
            not missing and not incomplete and prov_keys == mine_keys and same_runs,
            f"required={len(need)} missing={missing or 'none'} no_DONE={incomplete or 'none'} "
            f"producer_runs=={sorted(prov_keys) == sorted(mine_keys)} same_dirs={same_runs}")

    # -------------------------------------------------- load banks and re-derive populations
    banks, shas, pools, excl_mine, keep_mine = {}, {}, {}, {}, {}
    for (cw, cc) in sorted(runs):
        bp = bank_path(cfg.bank_dir, cw, cc)
        banks[(cw, cc)] = load_bank(bp)
        shas[(cw, cc)] = sha16_of_file(bp)
        for name, cells, nex in POPULATIONS:
            kept, dropped = population_rows(banks[(cw, cc)], cc, cfg.channel, cells, nex)
            pools[(cw, cc, name)] = kept
            keep_mine[f"{cw}_{cc}/{name}"] = counter_of(kept)
            if dropped:
                excl_mine[f"{cw}_{cc}/{name}"] = counter_of(dropped)

    # -------------------------------------------------- C1  population identity
    p_keep = res.get("retained_rows", {})
    p_excl = res.get("excluded_concept_word_rows", {})
    diffs = []
    for k in sorted(set(keep_mine) | set(p_keep)):
        if keep_mine.get(k, {}) != p_keep.get(k, {}):
            diffs.append(f"retained[{k}] mine={keep_mine.get(k)} producer={p_keep.get(k)}")
    for k in sorted(set(excl_mine) | set(p_excl)):
        if excl_mine.get(k, {}) != p_excl.get(k, {}):
            diffs.append(f"excluded[{k}] mine={excl_mine.get(k)} producer={p_excl.get(k)}")
    tot_c = sum(sum(v.values()) for k, v in keep_mine.items() if k.endswith("/C"))
    tot_x = sum(sum(v.values()) for k, v in excl_mine.items())
    rep.add("C1_POPULATION_IDENTITY", not diffs,
            (f"re-derived {len(keep_mine)} populations from {len(banks)} banks "
             f"(retained cell-C rows={tot_c}, excluded rows total={tot_x}); "
             + ("all counts agree" if not diffs else f"{len(diffs)} MISMATCH: " + " | ".join(diffs[:4]))))

    # -------------------------------------------------- C1b exclusion balance across classes
    bad_bal = []
    for cw in CODEWORDS:
        for name in ("C", "C_n0"):
            if not all((cw, c, name) in pools for c in PRIMARY_CLASSES):
                continue
            ex = {c: sum(excl_mine.get(f"{cw}_{c}/{name}", {}).values()) for c in PRIMARY_CLASSES}
            ke = {c: len(pools[(cw, c, name)]) for c in PRIMARY_CLASSES}
            if len(set(ex.values())) != 1:
                bad_bal.append(f"{cw}/{name} excluded UNBALANCED {ex}")
            if len(set(ke.values())) != 1:
                bad_bal.append(f"{cw}/{name} retained UNBALANCED {ke}")
    shown = {c: sum(excl_mine.get(f"{PRIMARY_CODEWORD}_{c}/C", {}).values()) for c in PRIMARY_CLASSES}
    rep.add("C1b_EXCLUSION_BALANCE", not bad_bal,
            (f"button cell-C excluded per class = {shown}; "
             + ("balanced in every codeword x {C, C_n0}" if not bad_bal else "; ".join(bad_bal[:4]))))

    # -------------------------------------------------- C2a bank-join metadata
    metas, join_bad = {}, []
    for (cw, cc), d in sorted(runs.items()):
        mp = os.path.join(d, "metadata.json")
        if not os.path.exists(mp):
            join_bad.append(f"{cw}_{cc}: no metadata.json")
            continue
        with open(mp) as fh:
            m = json.load(fh)
        metas[(cw, cc)] = m
        bp = bank_path(cfg.bank_dir, cw, cc)
        if m.get("bank_file_sha16") != shas[(cw, cc)]:
            join_bad.append(f"{cw}_{cc}: bank_file_sha16 {m.get('bank_file_sha16')} != {shas[(cw, cc)]}")
        if os.path.basename(str(m.get("bank_path", ""))) != os.path.basename(bp):
            join_bad.append(f"{cw}_{cc}: bank_path basename {os.path.basename(str(m.get('bank_path')))}")
        if int(m.get("bank_n_rows", -1)) != len(banks[(cw, cc)]):
            join_bad.append(f"{cw}_{cc}: bank_n_rows {m.get('bank_n_rows')} != {len(banks[(cw, cc)])}")
        if cfg.expect_rows and len(banks[(cw, cc)]) != cfg.expect_rows:
            join_bad.append(f"{cw}_{cc}: bank has {len(banks[(cw, cc)])} rows, expected {cfg.expect_rows}")
    rep.add("C2a_BANK_JOIN_METADATA", not join_bad,
            (f"{len(metas)} runs declare the bank they were extracted from and it matches "
             f"byte-for-byte" if not join_bad else "; ".join(join_bad[:4])))

    # -------------------------------------------------- C2b rep cache <-> its own run
    # The metadata check above cannot see a rep cache that was physically swapped between two run
    # directories: metadata.json would still name the right bank.  This ties the cache to the run's
    # OWN per-row scalar table: results.jsonl records hnorm|L<k> for every final occurrence, which
    # is the norm of exactly the vector the cache stores.
    bind_bad, bind_stat = [], []
    for (cw, cc), d in sorted(runs.items()):
        rjs = os.path.join(d, "results.jsonl")
        if not os.path.exists(rjs):
            bind_bad.append(f"{cw}_{cc}: no results.jsonl -- cache cannot be tied to its run")
            continue
        layers, blobmeta, keys = blob_info(d)
        sample = {}
        with open(rjs) as fh:
            for i, line in enumerate(fh):
                if i % cfg.hnorm_stride:
                    continue
                r = json.loads(line)
                if not r.get("is_final_occurrence"):
                    continue
                pid = r.get("prompt_id")
                if pid in keys and pid not in sample:
                    sample[pid] = {L: r.get(f"hnorm|L{L}") for L in layers}
                if len(sample) >= cfg.hnorm_rows:
                    break
        if not sample:
            bind_bad.append(f"{cw}_{cc}: no comparable hnorm rows")
            continue
        _, reps = load_reps_subset(d, set(sample))
        rel = []
        for pid, hs in sample.items():
            v = reps.get(pid)
            if v is None:
                continue
            for j, L in enumerate(layers):
                hn = hs.get(L)
                if hn is None:
                    continue
                rel.append(abs(float(np.linalg.norm(v[j])) - float(hn)) / max(abs(float(hn)), 1e-9))
        rel = np.array(rel) if rel else np.array([1.0])
        frac = float((rel > 1e-3).mean())
        bind_stat.append(f"{cw}_{cc}:q95={np.quantile(rel, 0.95):.1e}")
        if frac > 0.01 or float(np.quantile(rel, 0.95)) > 1e-3:
            bind_bad.append(f"{cw}_{cc}: rep cache does NOT match its own results.jsonl "
                            f"({frac:.1%} of (row,layer) pairs off by >1e-3, "
                            f"q95 rel.err={np.quantile(rel, 0.95):.2e}) -- CROSS-RUN CACHE")
        del reps
    rep.add("C2b_REP_CACHE_BINDING", not bind_bad,
            ("every rep cache reproduces its own run's hnorm columns  " + " ".join(bind_stat)
             if not bind_bad else "; ".join(bind_bad[:3])))

    # -------------------------------------------------- C2c the collision is REAL (necessity)
    all_ids, per_bank_ids = set(), {}
    for (cw, cc), b in banks.items():
        ids = {r["prompt_id"] for r in b}
        per_bank_ids[(cw, cc)] = ids
        all_ids |= ids
    total_rows = sum(len(b) for b in banks.values())
    id_sets_identical = len({frozenset(v) for v in per_bank_ids.values()}) == 1
    collides = len(all_ids) < total_rows and len(banks) > 1
    rep.add("C2c_ID_COLLISION_SHOWN", bool(collides and id_sets_identical),
            (f"{len(all_ids)} distinct prompt_ids over {total_rows} rows in {len(banks)} banks; "
             f"all banks share an identical id set = {id_sets_identical} "
             f"=> prompt_id alone is NOT a key, so C2a/C2b are necessary"))

    # -------------------------------------------------- C3 config identity
    def cfgsig(cw, cc):
        m = metas.get((cw, cc), {})
        layers, blobmeta, _ = blob_info(runs[(cw, cc)])
        return dict(layers=list(m.get("layers", [])), rep_layers=list(layers),
                    model=m.get("model"), dtype=str(m.get("dtype")),
                    rep_dtype=str(blobmeta.get("dtype")),
                    position=str(blobmeta.get("position")),
                    seed=m.get("seed"), attn=m.get("attn_implementation"),
                    tok=m.get("tokenizer_files_sha16"),
                    conv=m.get("layer_convention") or blobmeta.get("layer_convention"),
                    model_commit=m.get("model_revision_resolved_commit"),
                    hidden=m.get("hidden_size"), nlayers=m.get("num_layers"))
    sigs = {f"{cw}_{cc}": cfgsig(cw, cc) for (cw, cc) in sorted(runs)}
    ref_k = sorted(sigs)[0]
    mismatch = []
    for k, s in sorted(sigs.items()):
        for f in sigs[ref_k]:
            if s[f] != sigs[ref_k][f]:
                mismatch.append(f"{k}.{f}={s[f]!r} != {ref_k}.{f}={sigs[ref_k][f]!r}")
    rep.add("C3_CONFIG_IDENTITY", not mismatch,
            (f"{len(sigs)} runs agree on layers/model/dtype/position/seed/tokenizer/convention "
             f"(model={sigs[ref_k]['model']}, position={sigs[ref_k]['position']}, "
             f"seed={sigs[ref_k]['seed']})" if not mismatch
             else "VOID -- " + "; ".join(mismatch[:4])))

    # -------------------------------------------------- C4 layer band
    band_bad, seen_layers = [], set()
    for k, s in sigs.items():
        for L in list(s["layers"]) + list(s["rep_layers"]):
            seen_layers.add(int(L))
            if int(L) not in LAYER_BAND:
                band_bad.append(f"{k}: extracted layer {L} outside L6-14")
    for path, node in _walk(res):
        if isinstance(node, dict) and "layer" in node and _num(node.get("layer")) is not None:
            L = int(node["layer"])
            seen_layers.add(L)
            if L not in LAYER_BAND:
                band_bad.append(f"{path}.layer = {L} outside L6-14")
    for k, v in prov.items():
        for L in list(v.get("layers", []) if isinstance(v, dict) else []):
            seen_layers.add(int(L))
            if int(L) not in LAYER_BAND:
                band_bad.append(f"provenance.{k}: layer {L} outside L6-14")
    rep.add("C4_LAYER_BAND", not band_bad,
            (f"every layer used is in L6-14 (seen {sorted(seen_layers)})" if not band_bad
             else "; ".join(band_bad[:4])))
    return dict(res=res, runs=runs, banks=banks, shas=shas, pools=pools, metas=metas, sigs=sigs)


# ------------------------------------------------------------------ helpers for stage B
def get_path(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def gather(pools, cw, classes, name):
    return [r for c in classes for r in pools.get((cw, c, name), [])]


GROUP_FIELD = {"domain": "domain", "block": "bank_block"}


def instrument_table(pools):
    """Which lower-level population each producer instrument is, re-derived from the banks.

    This is what makes `C5` a re-derivation rather than a re-read: the fold sizes the producer
    reports must equal the fold sizes these populations imply.
    """
    P, PC = PRIMARY_CODEWORD, PRIMARY_CLASSES
    t = {
        "P2_primary":
            dict(test=gather(pools, P, PC, "C"), train=None, group="domain"),
        "null_n_examples_0.observed":
            dict(test=gather(pools, P, PC, "C_n0"), train=None, group="domain"),
        "P2_bomb_vs_knife_2way_gun_excluded":
            dict(test=gather(pools, P, ("bomb", "knife"), "C"), train=None, group="domain"),
        "P2_knife_vs_club_CONTROL_bomb_absent":
            dict(test=gather(pools, P, ("knife", "club"), "C"), train=None, group="domain"),
        "P1_trainB_testC":
            dict(test=gather(pools, P, PC, "C"),
                 train=gather(pools, P, PC, "B") + gather(pools, P, PC, "A"), group="domain"),
        "P1_capability_heldout_B":
            dict(test=gather(pools, P, PC, "B"), train=None, group="domain"),
        "P2_leave_one_block_out":
            dict(test=gather(pools, P, PC, "C"), train=None, group="block"),
        "P2_basket_lexical_transfer":
            dict(test=gather(pools, "basket", PC, "C"), train=None, group="domain"),
        "P2_bomb_vs_benign_remap":
            dict(test=pools.get((P, "bomb", "C"), []) + pools.get((P, "bomb", "F"), []),
                 train=None, group="domain"),
    }
    return t


def _stage_b(cfg, rep, ctx):
    res, runs, banks, pools = ctx["res"], ctx["runs"], ctx["banks"], ctx["pools"]

    # -------------------------------------------------- C5  fold discipline
    table = instrument_table(pools)
    fold_bad, fold_ok = [], []
    for key, spec in table.items():
        node = get_path(res, key)
        if not isinstance(node, dict) or not isinstance(node.get("picks"), dict):
            continue
        gf = GROUP_FIELD[spec["group"]]
        test_rows = spec["test"]
        train_pool = spec["train"] if spec["train"] is not None else test_rows
        if not test_rows:
            continue
        if node.get("group") not in (spec["group"], None):
            fold_bad.append(f"{key}: group={node.get('group')!r}, expected {spec['group']!r}")
        n_by_g_test = collections.Counter(r[gf] for r in test_rows)
        n_by_g_train = collections.Counter(r[gf] for r in train_pool)
        pool_total = len(train_pool)
        for d, pk in sorted(node["picks"].items()):
            if d not in n_by_g_test:
                fold_bad.append(f"{key}: fold {d!r} is not a {spec['group']} of this population")
                continue
            want_test = n_by_g_test[d]
            want_train = pool_total - n_by_g_train.get(d, 0)
            if int(pk.get("n_test", -1)) != want_test:
                fold_bad.append(f"{key}/{d}: n_test={pk.get('n_test')} but the bank gives {want_test}")
            if int(pk.get("n_train", -1)) != want_train:
                leak = int(pk.get("n_train", -1)) == pool_total
                fold_bad.append(
                    f"{key}/{d}: n_train={pk.get('n_train')} but leave-one-{spec['group']}-out on "
                    f"{pool_total} rows gives {want_train}"
                    + ("  <== the held-out group IS IN ITS OWN TRAINING FOLD" if leak else ""))
        fold_ok.append(f"{key}({len(node['picks'])} folds)")
    rep.add("C5_FOLD_DISCIPLINE", not fold_bad,
            ("every reported fold's n_train/n_test re-derives from the banks as strict "
             f"leave-one-group-out: {', '.join(fold_ok) or 'no instrument present'}"
             if not fold_bad else "; ".join(fold_bad[:4])))

    # -------------------------------------------------- C6 / C5b  the BLOCKING null, recomputed
    null_node = res.get("null_n_examples_0")
    n_perm = int(cfg.n_perm or res.get("n_perm") or 200)
    if not isinstance(null_node, dict):
        rep.add("C6_BLOCKING_NULL", False,
                f"the blocking null is absent from the producer JSON (value={null_node!r}); "
                f"PR-035 §23.2 makes it mandatory and BLOCKING")
        rep.add("C5b_SELECTION_POPULATION", False, "no null picks to test")
        mine_obs = mine_p = None
    else:
        need_by_run = {}
        for c in PRIMARY_CLASSES:
            key = (PRIMARY_CODEWORD, c)
            need_by_run[key] = ({r["prompt_id"] for r in pools.get((*key, "B"), [])} |
                                {r["prompt_id"] for r in pools.get((*key, "C_n0"), [])})
        rows_B, rows_n0, layers_ref, n_missing = [], [], None, 0
        for c in PRIMARY_CLASSES:
            key = (PRIMARY_CODEWORD, c)
            if key not in runs:
                continue
            layers, reps = load_reps_subset(runs[key], need_by_run[key])
            layers_ref = layers_ref or layers
            for name, sink in (("B", rows_B), ("C_n0", rows_n0)):
                for r in pools.get((*key, name), []):
                    v = reps.get(r["prompt_id"])
                    if v is None:
                        n_missing += 1
                        continue
                    sink.append(dict(domain=r["domain"], bank_block=r.get("bank_block"),
                                     concept=c, vec=v))
            del reps
        lab = lambda r: r["concept"]
        obs = loo_domain(rows_n0, layers_ref, PRIMARY_CLASSES, lab, selection_rows=rows_B)
        mine_obs = obs["mean_acc"]
        pt = permutation_p(rows_n0, layers_ref, PRIMARY_CLASSES, obs["picks"], n_perm,
                           cfg.perm_seed, obs["mean_acc"])
        mine_p = pt["p_one_sided"]

        # ---- C5b: were the null's picks selected on cell B (§28.2) or on the null's own labels?
        prod_picks = get_path(res, "null_n_examples_0.observed.picks") or {}
        agree = {d: (int(prod_picks[d]["layer"]) == obs["picks"][d]["layer"] and
                     float(prod_picks[d]["C"]) == obs["picks"][d]["C"])
                 for d in sorted(set(prod_picks) & set(obs["picks"]))}
        sel_ok = bool(agree) and all(agree.values()) and set(prod_picks) == set(obs["picks"])
        diag = ""
        if not sel_ok:
            self_sel = loo_domain(rows_n0, layers_ref, PRIMARY_CLASSES, lab,
                                  selection_rows=rows_n0)
            self_agree = all(int(prod_picks.get(d, {}).get("layer", -1)) == self_sel["picks"][d]["layer"]
                             and float(prod_picks.get(d, {}).get("C", -1)) == self_sel["picks"][d]["C"]
                             for d in self_sel["picks"]) and set(prod_picks) == set(self_sel["picks"])
            diag = ("  <== they match selection on the NULL'S OWN TRUE LABELS, the C-053 §28.2 "
                    "defect: freezing picks across permutations is then unlicensed"
                    if self_agree else "  <== they match neither cell-B nor self-selection")
        rep.add("C5b_SELECTION_POPULATION", sel_ok,
                (f"the null's (layer, C) picks reproduce exactly when selected on cell B "
                 f"({len(agree)}/{len(agree)} folds): "
                 + ", ".join(f"{d}:L{obs['picks'][d]['layer']}/C{obs['picks'][d]['C']}"
                             for d in sorted(obs['picks']))
                 if sel_ok else
                 f"producer null picks != cell-B selection ({sum(agree.values())}/{len(agree)} "
                 f"folds agree){diag}"))

        # ---- C6 itself
        p_obs = get_path(res, "null_n_examples_0.observed.mean_acc")
        p_p = get_path(res, "null_n_examples_0.permutation.p_one_sided")
        msgs, ok = [], True
        if n_missing:
            ok = False
            msgs.append(f"{n_missing} null/selection rows have no hidden state in the cache")
        if _num(p_obs) is None or mine_obs is None:
            ok = False
            msgs.append(f"cannot compare accuracy (producer={p_obs!r}, mine={mine_obs!r})")
        else:
            dacc = abs(float(p_obs) - mine_obs)
            if dacc > ACC_TOL:
                ok = False
            msgs.append(f"held-out acc mine={mine_obs:.6f} producer={float(p_obs):.6f} "
                        f"|d|={dacc:.2e} (tol {ACC_TOL:.0e}: the pipeline is deterministic given "
                        f"identical rows and frozen picks, and one flipped test row would move "
                        f"this by >=1/(6*{min(v['n_test'] for v in obs['picks'].values()) if obs['picks'] else 1}))")
        if _num(p_p) is None or mine_p is None:
            ok = False
            msgs.append(f"cannot compare permutation p (producer={p_p!r}, mine={mine_p!r})")
        else:
            tol = mc_tolerance(float(p_p), mine_p, n_perm)
            same_decision = (float(p_p) <= ALPHA) == (mine_p <= ALPHA)
            resolvable = abs(0.5 * (float(p_p) + mine_p) - ALPHA) > tol
            if abs(float(p_p) - mine_p) > tol or not same_decision:
                ok = False
            if not resolvable:
                ok = False
            msgs.append(f"perm p mine={mine_p:.4f} (seed {cfg.perm_seed}) producer={float(p_p):.4f} "
                        f"|d|={abs(float(p_p) - mine_p):.4f} <= MC tol {tol:.4f} "
                        f"[3*sqrt(2p(1-p)/{n_perm}), floored at 3/(n+1)]; "
                        f"decision agrees={same_decision}; resolvable at alpha={resolvable}; "
                        f"null {'FIRES -> VOID' if mine_p <= ALPHA else 'passes'}")
        rep.add("C6_BLOCKING_NULL", ok, "; ".join(msgs))

    # -------------------------------------------------- C7 independence unit
    real_domains = sorted({r["domain"] for r in pools.get((PRIMARY_CODEWORD, "bomb", "C"), [])})
    real_blocks = sorted({r.get("bank_block") for r in pools.get((PRIMARY_CODEWORD, "bomb", "C"), [])})
    ind_bad, ind_seen = [], []
    for path, node in _walk(res):
        if not isinstance(node, dict) or "n_domains" not in node:
            continue
        nd, g, per = node.get("n_domains"), node.get("group"), node.get("per_domain")
        ind_seen.append(f"{path}:n={nd}/{g}")
        if not isinstance(per, dict):
            ind_bad.append(f"{path}: n_domains={nd} with no per-fold table to back it")
            continue
        if int(nd) != len(per):
            ind_bad.append(f"{path}: n_domains={nd} but per_domain has {len(per)} entries")
        if g == "domain" or g is None:
            if int(nd) != N_DOMAINS_EXPECTED:
                ind_bad.append(f"{path}: n_domains={nd}, but §23.6 fixes the independence unit at "
                               f"the DOMAIN and there are {N_DOMAINS_EXPECTED} domains "
                               f"({real_domains}) -- a larger n is rows treated as independent")
            extra = sorted(set(per) - set(real_domains))
            if extra:
                ind_bad.append(f"{path}: per_domain keys are not domains: {extra[:5]}")
        elif g == "block":
            extra = sorted(set(per) - set(real_blocks))
            if extra:
                ind_bad.append(f"{path}: per_domain keys are not bank_blocks: {extra[:5]}")
            if int(nd) > len(real_blocks):
                ind_bad.append(f"{path}: n_domains={nd} > {len(real_blocks)} blocks")
    rep.add("C7_INDEPENDENCE_UNIT", not ind_bad,
            (f"{len(ind_seen)} reported group-level statistics all fold over "
             f"{N_DOMAINS_EXPECTED} domains {real_domains} (or over the {len(real_blocks)} "
             f"bank_blocks for the LOBO secondary)" if not ind_bad else "; ".join(ind_bad[:4])))

    # -------------------------------------------------- C9 derived-field recompute
    der_bad, der_n = [], 0
    for path, node in _walk(res):
        if not isinstance(node, dict):
            continue
        per = node.get("per_domain")
        if isinstance(per, dict) and per and all(_num(v) is not None for v in per.values()):
            der_n += 1
            vals = [float(v) for v in per.values()]
            if _num(node.get("mean_acc")) is not None and \
                    abs(float(node["mean_acc"]) - float(np.mean(vals))) > 1e-9:
                der_bad.append(f"{path}.mean_acc={node['mean_acc']} != mean(per_domain)="
                               f"{float(np.mean(vals)):.9f}")
            cls = node.get("classes")
            if isinstance(cls, list) and cls and _num(node.get("chance")) is not None and \
                    abs(float(node["chance"]) - 1.0 / len(cls)) > 1e-12:
                der_bad.append(f"{path}.chance={node['chance']} != 1/{len(cls)}")
            if _num(node.get("chance")) is not None and _num(node.get("n_above_chance")) is not None:
                want = int(sum(1 for v in vals if v > float(node["chance"])))
                if int(node["n_above_chance"]) != want:
                    der_bad.append(f"{path}.n_above_chance={node['n_above_chance']} != {want}")
            tfa = node.get("train_fold_acc")
            if isinstance(tfa, dict) and tfa:
                m = float(np.mean([float(v) for v in tfa.values()]))
                if _num(node.get("mean_train_fold_acc")) is not None and \
                        abs(float(node["mean_train_fold_acc"]) - m) > 1e-9:
                    der_bad.append(f"{path}.mean_train_fold_acc != mean(train_fold_acc)")
                if "fit_capable" in node and _num(node.get("chance")) is not None:
                    want = bool(m > float(node["chance"]))
                    if bool(node["fit_capable"]) != want:
                        der_bad.append(f"{path}.fit_capable={node['fit_capable']} != {want}")
        if _num(node.get("n_perm")) and _num(node.get("p_floor")) is not None:
            der_n += 1
            if abs(float(node["p_floor"]) - 1.0 / (1.0 + float(node["n_perm"]))) > 1e-12:
                der_bad.append(f"{path}.p_floor != 1/(1+n_perm)")
        if _num(node.get("excess_over_null")) is not None and \
                _num(node.get("observed_mean")) is not None and _num(node.get("null_mean")) is not None:
            if abs(float(node["excess_over_null"]) -
                   (float(node["observed_mean"]) - float(node["null_mean"]))) > 1e-9:
                der_bad.append(f"{path}.excess_over_null != observed_mean - null_mean")
    rep.add("C9_DERIVED_FIELD_RECOMPUTE", not der_bad,
            (f"{der_n} summary blocks recompute from their own per-fold tables"
             if not der_bad else "; ".join(der_bad[:4])))

    # -------------------------------------------------- C8 verdict consistency
    # These are the §23.5 INPUT numbers.  They are read as inputs, not as evidence: every one of
    # them is itself checked above (C6 recomputes the null p; C9 recomputes mean_acc, chance and
    # fit_capable from the per-fold tables; C5/C7 check the folds those tables came from).
    prim = res.get("P2_primary")
    primp = res.get("P2_primary_permutation") or {}
    ctrlp = res.get("P2_knife_vs_club_CONTROL_bomb_absent_permutation") or {}
    lenc = (res.get("length_only_control") or {})
    null_p = get_path(res, "null_n_examples_0.permutation.p_one_sided")
    fit_capable = None
    if isinstance(prim, dict):
        tfa = prim.get("train_fold_acc") or {}
        ch = _num(prim.get("chance"))
        if ch is None and isinstance(prim.get("classes"), list) and prim["classes"]:
            ch = 1.0 / len(prim["classes"])
        fit_capable = bool(tfa) and ch is not None and \
            float(np.mean([float(v) for v in tfa.values()])) > ch
    obs_mean = None
    if isinstance(prim, dict) and isinstance(prim.get("per_domain"), dict) and prim["per_domain"]:
        obs_mean = float(np.mean([float(v) for v in prim["per_domain"].values()]))
    above = (obs_mean is not None and _num(primp.get("null_mean")) is not None
             and obs_mean > float(primp["null_mean"]))
    cat, why = derive_verdict(
        null_p=_num(null_p), fit_capable=fit_capable,
        length_acc=_num(lenc.get("mean_acc")), probe_null_q95=_num(primp.get("null_q95")),
        primary_p=_num(primp.get("p_one_sided")), above_null=above,
        ctrl_p=_num(ctrlp.get("p_one_sided")),
        primary_present=isinstance(prim, dict) and obs_mean is not None)
    printed = verdict_category(res.get("verdict"))
    rep.add("C8_VERDICT_CONSISTENCY", cat == printed,
            (f"re-derived '{cat}' ({why}) from inputs "
             f"[null_p={null_p}, fit_capable={fit_capable}, P2_p={primp.get('p_one_sided')}, "
             f"above_null={above}, ctrl_p={ctrlp.get('p_one_sided')}, "
             f"len_acc={lenc.get('mean_acc')}, null_q95={primp.get('null_q95')}]; "
             f"producer printed '{printed}'"
             + ("" if cat == printed else "  <== VERDICT DOES NOT FOLLOW FROM ITS OWN INPUTS")))
    return rep


def verify(cfg, rep):
    ctx = _stage_a(cfg, rep)
    if ctx is None:
        return None
    _stage_b(cfg, rep, ctx)
    return ctx


# ==================================================================================================
# SYNTHETIC FIXTURE — a complete, self-consistent artifact universe with no real data in it
# Used by --self-test (must VERIFY) and by --mutate (each injected defect must be REJECTED by its
# OWN check).  It reproduces the real schema exactly, including the properties the checks exist for:
#   * the 8-way prompt_id collision (prompt_id depends on family_id + condition only, A-019 §2.2)
#   * 240 primary cell-C rows / 36 null rows per bank, with 12 concept-word leaks in each, all in
#     `bank_block = strength` (C-049 §22.1, C-053 §28.1)
#   * cell B whose surface IS the concept word, so §28.1's AND clause retains all 48
#   * per-run results.jsonl carrying hnorm|L<k> for every final occurrence
# ==================================================================================================
FIX_DOMAINS = ("city_bridge", "farm_storage", "game_manual", "instructional", "lab_safety",
               "news_report")
FIX_H = 16
FIX_LAYERS = list(LAYER_BAND)
FIX_NPERM = 100


def _pid(family_id, condition):
    """The real generator's rule: sha256(family_id + '|' + condition)[:16].  It depends on neither
    the codeword nor the concept, which is WHY the ids collide 8-way."""
    return hashlib.sha256(f"{family_id}|{condition}".encode()).hexdigest()[:16]


def _fix_bank(cw, cc):
    rows, seq = [], [0]

    def add(cell, block, nex, qk, target_surface, body, dom, cond):
        seq[0] += 1
        fam = f"{dom}|dev|slot{seq[0]}|n{nex}|{block}|{qk}|{cell}"
        rows.append(dict(prompt_id=_pid(fam, cond), prompt_sha16=_pid(fam, cond + "s"),
                         family_id=fam, cell=cell, domain=dom, split="dev", condition=cond,
                         n_examples=nex, bank_block=block, query_kind=qk,
                         target_surface=target_surface, target_semantic=cc,
                         codeword=cw, concept=cc, full_prompt=body, n_chars=len(body),
                         final_query_text=f"what does the word {cw} actually refer to?",
                         occurrence_analysis_safe=True))

    clean = lambda dom, i: (f"The {dom} log lists the {cw} in aisle {i}. "
                            f"Answer with exactly one word and nothing else. "
                            f"In the text above, what does the word {cw} actually refer to?")
    leak = lambda dom, i: (f"The {dom} log lists the {cw} in aisle {i}. "
                           f"Every occurrence of {cw} must be interpreted as {cc}. "
                           f"Answer with exactly one word and nothing else. "
                           f"In the text above, what does the word {cw} actually refer to?")

    # cell C, the primary: 240 rows, block mix as in the real banks, 12 concept-word leaks
    plan_C = (("role_style", 20), ("consistency", 6), ("core2x2", 4), ("core2x2_slot3", 4),
              ("strength", 4), ("position", 2))
    for dom in FIX_DOMAINS:
        i = 0
        for block, per in plan_C:
            for j in range(per):
                nex = 4 if j % 2 == 0 else 8
                leaking = (block == "strength" and j < 2)      # 2 per domain x 6 = 12 per bank
                add("C", block, nex, PRIMARY_CHANNEL, cw,
                    (leak if leaking else clean)(dom, i), dom, "natural_doublespeak")
                i += 1
    # cell C at n_examples = 0, the blocking null: 36 rows, 12 leaks (all in `strength`)
    for dom in FIX_DOMAINS:
        for block, per in (("strength", 2), ("core2x2", 2), ("role_style", 2)):
            for j in range(per):
                add("C", block, 0, PRIMARY_CHANNEL, cw,
                    (leak if block == "strength" else clean)(dom, 90 + j), dom,
                    "natural_doublespeak")
    # cell B: the concept word IS the surface, so §28.1's AND clause retains all 48
    for dom in FIX_DOMAINS:
        for j in range(8):
            add("B", "core2x2", 4 if j % 2 == 0 else 8, PRIMARY_CHANNEL, cc,
                f"The {dom} report names the {cc} directly in line {j}. "
                f"In the text above, what does the word {cc} actually refer to?", dom,
                "explicit_concept")
    # cell A (literal) and cell F (benign remap, bicycle) carry no concept word
    for dom in FIX_DOMAINS:
        for j in range(28):
            add("A", "core2x2", 4 if j % 2 == 0 else 8, PRIMARY_CHANNEL, cw,
                f"The {dom} inventory mentions the {cw} on shelf {j}.", dom, "benign_literal")
        for j in range(4):
            add("F", "extra_conditions", 4 if j % 2 == 0 else 8, PRIMARY_CHANNEL, cw,
                f"In {dom}, every {cw} is to be read as the two-wheeled vehicle, item {j}.", dom,
                "benign_remap")
    # filler in other channels, so the bank has the real 2736 rows
    j = 0
    while len(rows) < EXPECT_ROWS_PER_BANK:
        dom = FIX_DOMAINS[j % len(FIX_DOMAINS)]
        qk = ("behavioral", "comprehension_usage", "semantic_forced_choice")[j % 3]
        add("D", "core2x2", (0, 4, 8)[j % 3], qk, cw,
            f"Filler {j} for {dom}: the {cw} is on shelf {j}.", dom, "filler")
        j += 1
    return rows


def _fix_write(root, seed=20260906, n_perm=FIX_NPERM, verbose=False):
    """Materialise banks, rep caches, run metadata, results.jsonl and a producer-style JSON.

    The producer JSON is generated by THIS file's re-implementation, i.e. it is the output of a
    producer that agreed with the verifier.  That is the correct baseline for a mutation harness:
    the question it answers is not "is the producer right" but "does each check FIRE when, and only
    when, its own defect is present".
    """
    bank_dir = os.path.join(root, "data")
    runs_root = os.path.join(root, "runs")
    os.makedirs(bank_dir, exist_ok=True)
    os.makedirs(runs_root, exist_ok=True)
    import torch

    banks, pools, run_dirs, reps_all = {}, {}, {}, {}
    for ci, cw in enumerate(CODEWORDS):
        for cj, cc in enumerate(CONCEPTS):
            bank = _fix_bank(cw, cc)
            bp = bank_path(bank_dir, cw, cc)
            with open(bp, "w") as fh:
                for r in bank:
                    fh.write(json.dumps(r) + "\n")
            banks[(cw, cc)] = bank
            for name, cells, nex in POPULATIONS:
                pools[(cw, cc, name)] = population_rows(bank, cc, PRIMARY_CHANNEL, cells, nex)[0]

            rng = np.random.default_rng(seed + 100 * ci + cj)
            centre = rng.normal(0, 1, FIX_H)
            reps = {}
            for r in bank:
                v = rng.normal(0, 1, (len(FIX_LAYERS), FIX_H))
                if r["cell"] == "B":
                    v = v + 1.6 * centre[None, :]          # cell B carries a real class signal
                reps[r["prompt_id"]] = torch.tensor(v, dtype=torch.float16)
            reps_all[(cw, cc)] = reps

            d = os.path.join(runs_root, f"bombspec_{cw}_{cc}_20260906_000000_1")
            os.makedirs(os.path.join(d, "cache"), exist_ok=True)
            run_dirs[(cw, cc)] = d
            torch.save(dict(layers=list(FIX_LAYERS), position="codeword_last", dtype="float16",
                            layer_convention="block_L == hidden_states[L+1]", reps=reps),
                       os.path.join(d, "cache", "final_occurrence_reps.pt"))
            with open(os.path.join(d, "results.jsonl"), "w") as fh:
                for r in bank:
                    v = reps[r["prompt_id"]].float().numpy()
                    row = dict(prompt_id=r["prompt_id"], cell=r["cell"], domain=r["domain"],
                               query_kind=r["query_kind"], is_final_occurrence=True)
                    for j, L in enumerate(FIX_LAYERS):
                        row[f"hnorm|L{L}"] = float(np.linalg.norm(v[j]))
                    fh.write(json.dumps(row) + "\n")
            json.dump(dict(schema="DONE/1", status="ok"), open(os.path.join(d, "DONE.json"), "w"))
            json.dump(dict(
                schema="BOOMBNESS_META/1", run_id=os.path.basename(d),
                bank_path=os.path.abspath(bp), bank_file_sha16=sha16_of_file(bp),
                bank_n_rows=len(bank), layers=list(FIX_LAYERS),
                model="synthetic/fixture-model", dtype="torch.bfloat16", seed=20260905,
                attn_implementation="sdpa", tokenizer_files_sha16="fixture000tok",
                layer_convention="block_L == hidden_states[L+1]",
                model_revision_resolved_commit="fixturecommit", hidden_size=FIX_H, num_layers=32),
                open(os.path.join(d, "metadata.json"), "w"), indent=1)

    # ---- build the producer-style JSON with this file's own re-implementation
    def vecrows(cw, classes, name):
        out = []
        for c in classes:
            for r in pools[(cw, c, name)]:
                out.append(dict(domain=r["domain"], bank_block=r.get("bank_block"), concept=c,
                                n_chars=len(r["full_prompt"]),
                                vec=reps_all[(cw, c)][r["prompt_id"]].float().numpy()))
        return out

    lab = lambda r: r["concept"]
    P = PRIMARY_CODEWORD
    B = vecrows(P, PRIMARY_CLASSES, "B")
    n0 = vecrows(P, PRIMARY_CLASSES, "C_n0")
    Crows = vecrows(P, PRIMARY_CLASSES, "C")

    def block(obs, classes, tag):
        obs = dict(obs)
        obs["classes"] = list(classes)
        obs["tag"] = tag
        obs["metric"] = "accuracy"
        obs["balanced"] = False
        obs["mean_train_fold_acc"] = (float(np.mean(list(obs["train_fold_acc"].values())))
                                      if obs["train_fold_acc"] else None)
        obs["fit_capable"] = bool(obs["train_fold_acc"] and
                                  obs["mean_train_fold_acc"] > obs["chance"])
        return obs

    obs0 = block(loo_domain(n0, FIX_LAYERS, PRIMARY_CLASSES, lab, selection_rows=B),
                 PRIMARY_CLASSES, "null_n0")
    p0 = permutation_p(n0, FIX_LAYERS, PRIMARY_CLASSES, obs0["picks"], n_perm, 4242,
                       obs0["mean_acc"])
    prim = block(loo_domain(Crows, FIX_LAYERS, PRIMARY_CLASSES, lab, selection_rows=B),
                 PRIMARY_CLASSES, "P2_primary_button_3way")
    pp = permutation_p(Crows, FIX_LAYERS, PRIMARY_CLASSES, prim["picks"], n_perm, 4243,
                       prim["mean_acc"])
    kc_rows = vecrows(P, ("knife", "club"), "C")
    kc_sel = vecrows(P, ("knife", "club"), "B")
    kc = block(loo_domain(kc_rows, FIX_LAYERS, ("knife", "club"), lab, selection_rows=kc_sel),
               ("knife", "club"), "knife_vs_club")
    kcp = permutation_p(kc_rows, FIX_LAYERS, ("knife", "club"), kc["picks"], n_perm, 4244,
                        kc["mean_acc"])

    # length-only control (PR-031c), nearest class mean on prompt length, same folds
    per_len = {}
    for d in sorted({r["domain"] for r in Crows}):
        tr = [r for r in Crows if r["domain"] != d]
        te = [r for r in Crows if r["domain"] == d]
        means = {c: float(np.mean([r["n_chars"] for r in tr if r["concept"] == c]))
                 for c in PRIMARY_CLASSES if any(r["concept"] == c for r in tr)}
        per_len[d] = sum(1 for r in te
                         if min(means, key=lambda c: abs(r["n_chars"] - means[c])) == r["concept"]) / len(te)
    lenc = dict(tag="length_only", chance=1.0 / 3, per_domain=per_len,
                mean_acc=float(np.mean(list(per_len.values()))))

    def perm_json(pt, obs_mean):
        out = dict(pt)
        out["p_floor"] = 1.0 / (1.0 + pt["n_perm"])
        out["observed_mean"] = obs_mean
        out["excess_over_null"] = obs_mean - pt["null_mean"]
        return out

    fit_capable = prim["fit_capable"]
    above = prim["mean_acc"] > pp["null_mean"]
    cat, why = derive_verdict(null_p=p0["p_one_sided"], fit_capable=fit_capable,
                              length_acc=lenc["mean_acc"], probe_null_q95=pp["null_q95"],
                              primary_p=pp["p_one_sided"], above_null=above,
                              ctrl_p=kcp["p_one_sided"], primary_present=True)
    res = dict(
        preregistration="DCS-PR-035 (fixture)", channel=PRIMARY_CHANNEL, primary_codeword=P,
        primary_classes=list(PRIMARY_CLASSES), alpha=ALPHA, n_perm=n_perm,
        n_examples_primary=list(PRIMARY_NEXAMPLES), occurrence_failure_frac=0.0,
        provenance={f"{cw}_{cc}": dict(bank=bank_path(bank_dir, cw, cc),
                                       bank_sha16=sha16_of_file(bank_path(bank_dir, cw, cc)),
                                       run_dir=run_dirs[(cw, cc)], layers=list(FIX_LAYERS))
                    for (cw, cc) in run_dirs},
        bank_join_verified={f"{cw}_{cc}": dict(bank_file_sha16=sha16_of_file(bank_path(bank_dir, cw, cc)),
                                               verified=True) for (cw, cc) in run_dirs},
        retained_rows={f"{cw}_{cc}/{n}": counter_of(pools[(cw, cc, n)])
                       for (cw, cc) in run_dirs for n, _, _ in POPULATIONS},
        excluded_concept_word_rows={
            f"{cw}_{cc}/{n}": counter_of(population_rows(banks[(cw, cc)], cc, PRIMARY_CHANNEL,
                                                         cells, nex)[1])
            for (cw, cc) in run_dirs for n, cells, nex in POPULATIONS
            if population_rows(banks[(cw, cc)], cc, PRIMARY_CHANNEL, cells, nex)[1]},
        null_n_examples_0=dict(observed=obs0, permutation=perm_json(p0, obs0["mean_acc"])),
        P2_primary=prim, P2_primary_permutation=perm_json(pp, prim["mean_acc"]),
        length_only_control=lenc,
        P2_knife_vs_club_CONTROL_bomb_absent=kc,
        P2_knife_vs_club_CONTROL_bomb_absent_permutation=perm_json(kcp, kc["mean_acc"]),
        length_only_clause=dict(length_acc=lenc["mean_acc"], probe_null_q95=pp["null_q95"],
                                passes=bool(lenc["mean_acc"] <= pp["null_q95"])),
        verdict=f"{cat} — {why}",
        verdict_inputs=dict(P2_perm_p=pp["p_one_sided"], knife_club_ctrl_p=kcp["p_one_sided"],
                            above_null=bool(above), fit_capable=bool(fit_capable),
                            null_control_passed=bool(p0["p_one_sided"] > ALPHA)))
    out = os.path.join(root, "producer.json")
    json.dump(res, open(out, "w"), indent=1, default=str)
    if verbose:
        print(f"[fixture] null p={p0['p_one_sided']:.3f} acc={obs0['mean_acc']:.4f} | "
              f"primary p={pp['p_one_sided']:.3f} acc={prim['mean_acc']:.4f} | verdict {cat}")
    return dict(root=root, bank_dir=bank_dir, runs_root=runs_root, json_path=out,
                null_p=p0["p_one_sided"])


class Cfg:
    def __init__(self, **kw):
        self.bank_dir = "data/boombness_prompts"
        self.runs_root = "outputs/boombness/extract_boombness"
        self.run_prefix = "bombspec"
        self.json_path = "outputs/boombness/dcs_analysis/dcs_bombness_specificity.json"
        self.channel = PRIMARY_CHANNEL
        self.n_perm = 0
        self.perm_seed = 815          # deliberately NOT the producer's 20260905
        self.hnorm_rows = 300
        self.hnorm_stride = 7
        self.expect_rows = EXPECT_ROWS_PER_BANK
        self.__dict__.update(kw)


def build_fixture(root, seed=20260906, n_perm=FIX_NPERM, verbose=False):
    """Build a fixture whose blocking null does NOT fire and is resolvable at this n_perm, so the
    baseline exercises the full §23.5 verdict path.  Seeds are tried in a fixed order, so the
    fixture is deterministic."""
    for k in range(12):
        shutil.rmtree(root, ignore_errors=True)
        os.makedirs(root, exist_ok=True)
        _BLOB_INFO.clear()
        info = _fix_write(root, seed=seed + 1000 * k, n_perm=n_perm, verbose=verbose)
        if info["null_p"] is not None and info["null_p"] >= 0.40:
            info["seed"] = seed + 1000 * k
            return info
    raise SystemExit("fixture: could not build a baseline whose blocking null passes")


# ==================================================================================================
# MUTATION HARNESS
# C-049 §22.5: the previous harness "only checks `rep.failed == 0` over all six checks, so any
# unrelated failure satisfies it".  This one names, for every injected defect, the ONE check that
# must catch it, and passes only if EVERY defect is caught by ITS OWN check.  A defect caught only
# by some other check is reported as NOT CAUGHT.
# ==================================================================================================
def _load_res(root):
    with open(os.path.join(root, "producer.json")) as fh:
        return json.load(fh)


def _save_res(root, res):
    with open(os.path.join(root, "producer.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=str)


def _fix_pools(root):
    pools, banks = {}, {}
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            b = load_bank(bank_path(os.path.join(root, "data"), cw, cc))
            banks[(cw, cc)] = b
            for name, cells, nex in POPULATIONS:
                pools[(cw, cc, name)] = population_rows(b, cc, PRIMARY_CHANNEL, cells, nex)[0]
    return banks, pools


def _refresh_pick_counts(res, pools):
    """Re-state every instrument's per-fold n_test/n_train from the (possibly mutated) banks, so a
    bank-level injection does not incidentally trip the fold check as well."""
    for key, spec in instrument_table(pools).items():
        node = get_path(res, key)
        if not isinstance(node, dict) or not isinstance(node.get("picks"), dict):
            continue
        gf = GROUP_FIELD[spec["group"]]
        pool = spec["train"] if spec["train"] is not None else spec["test"]
        by_test = collections.Counter(r[gf] for r in spec["test"])
        by_pool = collections.Counter(r[gf] for r in pool)
        for d, pk in node["picks"].items():
            pk["n_test"] = int(by_test.get(d, 0))
            pk["n_train"] = int(len(pool) - by_pool.get(d, 0))


def _run_dir(root, cw, cc):
    return sorted(glob.glob(os.path.join(root, "runs", f"bombspec_{cw}_{cc}_*")))[-1]


def _rebase_fixture(root):
    """A copied fixture lives at a new path; re-point the producer JSON's provenance and each run's
    `bank_path` at it, so that copying alone injects no defect and every failure below is the
    injected one."""
    res = _load_res(root)
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            k = f"{cw}_{cc}"
            d = _run_dir(root, cw, cc)
            bp = os.path.abspath(bank_path(os.path.join(root, "data"), cw, cc))
            if k in res.get("provenance", {}):
                res["provenance"][k]["run_dir"] = d
                res["provenance"][k]["bank"] = bp
            mp = os.path.join(d, "metadata.json")
            m = json.load(open(mp))
            m["bank_path"] = bp
            json.dump(m, open(mp, "w"), indent=1)
    _save_res(root, res)


def m1_swap_rep_cache(root):
    """§28.3: point one run at ANOTHER bank's hidden states.  metadata.json still names the right
    bank, prompt_id collides 8-way so the join reports ZERO missing rows, and no VOID is raised."""
    a = os.path.join(_run_dir(root, "button", "bomb"), "cache", "final_occurrence_reps.pt")
    b = os.path.join(_run_dir(root, "button", "knife"), "cache", "final_occurrence_reps.pt")
    tmp = a + ".swap"
    os.replace(a, tmp); os.replace(b, a); os.replace(tmp, b)


def m2_drop_exclusion(root):
    """§23.1 dropped: the 12 leaking `strength` rows per bank are back in the population."""
    res = _load_res(root)
    for k, ex in list(res.get("excluded_concept_word_rows", {}).items()):
        keep = res["retained_rows"].setdefault(k, {})
        for kk, v in ex.items():
            keep[kk] = keep.get(kk, 0) + v
    res["excluded_concept_word_rows"] = {}
    _save_res(root, res)


def m3_unbalance_exclusion(root):
    """The exclusion still runs, and the producer still reports it faithfully -- but it now removes
    18 rows from `knife` and 12 from bomb/gun, so the exclusion ITSELF induces a class asymmetry."""
    bp = bank_path(os.path.join(root, "data"), "button", "knife")
    rows = [json.loads(l) for l in open(bp)]
    n = 0
    for r in rows:
        if (n < 6 and r["query_kind"] == PRIMARY_CHANNEL and r["cell"] == "C"
                and r["n_examples"] in PRIMARY_NEXAMPLES and r["bank_block"] == "consistency"):
            r["full_prompt"] = r["full_prompt"] + " The knife is mentioned here."
            n += 1
    with open(bp, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    d = _run_dir(root, "button", "knife")
    m = json.load(open(os.path.join(d, "metadata.json")))
    m["bank_file_sha16"] = sha16_of_file(bp)
    json.dump(m, open(os.path.join(d, "metadata.json"), "w"), indent=1)
    banks, pools = _fix_pools(root)
    res = _load_res(root)
    res["provenance"]["button_knife"]["bank_sha16"] = m["bank_file_sha16"]
    res["bank_join_verified"]["button_knife"]["bank_file_sha16"] = m["bank_file_sha16"]
    for name, cells, nex in POPULATIONS:
        kept, dropped = population_rows(banks[("button", "knife")], "knife", PRIMARY_CHANNEL,
                                        cells, nex)
        res["retained_rows"][f"button_knife/{name}"] = counter_of(kept)
        if dropped:
            res["excluded_concept_word_rows"][f"button_knife/{name}"] = counter_of(dropped)
        else:
            res["excluded_concept_word_rows"].pop(f"button_knife/{name}", None)
    _refresh_pick_counts(res, pools)
    _save_res(root, res)


def m4_wrong_bank_sha(root):
    """§28.3: a run that declares a different bank than the one it is joined to."""
    d = _run_dir(root, "button", "gun")
    p = os.path.join(d, "metadata.json")
    m = json.load(open(p))
    m["bank_file_sha16"] = "deadbeefdeadbeef"
    json.dump(m, open(p, "w"), indent=1)


def m5_domain_in_own_fold(root):
    """Fold discipline broken: one held-out domain is left in its own training fold."""
    res = _load_res(root)
    picks = res["P2_primary"]["picks"]
    d = sorted(picks)[0]
    picks[d]["n_train"] = picks[d]["n_train"] + picks[d]["n_test"]
    _save_res(root, res)


def m6_rows_as_domains(root):
    """§23.6's independence unit swapped for rows: n = 240 instead of n = 6."""
    res = _load_res(root)
    res["P2_primary"]["n_domains"] = 240
    _save_res(root, res)


def m7_flip_verdict(root):
    """The §23.5 verdict string no longer follows from the numbers it is a function of."""
    res = _load_res(root)
    cur = verdict_category(res["verdict"])
    other = "POSITIVE" if cur != "POSITIVE" else "NEGATIVE"
    res["verdict"] = res["verdict"].replace(cur, other, 1)
    _save_res(root, res)


def m8_layer_out_of_band(root):
    """A layer outside the inherited L6-14 band (§23.6)."""
    res = _load_res(root)
    d = sorted(res["P2_primary"]["picks"])[0]
    res["P2_primary"]["picks"][d]["layer"] = 20
    _save_res(root, res)


def m9_wrong_null_accuracy(root):
    """The blocking null's own held-out accuracies are misreported, self-consistently: the summary
    still recomputes from its per-fold table, so ONLY an independent recomputation can see it."""
    res = _load_res(root)
    obs = res["null_n_examples_0"]["observed"]
    obs["per_domain"] = {d: 0.9 for d in obs["per_domain"]}
    obs["mean_acc"] = 0.9
    obs["n_above_chance"] = sum(1 for v in obs["per_domain"].values() if v > obs["chance"])
    perm = res["null_n_examples_0"]["permutation"]
    perm["observed_mean"] = 0.9
    perm["excess_over_null"] = 0.9 - perm["null_mean"]
    _save_res(root, res)


def m10_config_drift(root):
    """One run was extracted with a different layer list -- still inside L6-14, so only a
    cross-run config comparison can see it."""
    d = _run_dir(root, "basket", "club")
    p = os.path.join(d, "metadata.json")
    m = json.load(open(p))
    m["layers"] = [6, 7, 8, 9, 10, 11, 12, 13]
    json.dump(m, open(p, "w"), indent=1)


def m11_null_picks_not_from_B(root):
    """C-053 §28.2: the blocking null's (layer, C) were not selected on cell B.  The picks stay
    inside the band, so only a re-selection on cell B can see it."""
    res = _load_res(root)
    for d, pk in res["null_n_examples_0"]["observed"]["picks"].items():
        pk["layer"] = 14 if int(pk["layer"]) != 14 else 13
        pk["C"] = 10.0
    _save_res(root, res)


MUTATIONS = [
    ("M1", "swap one bank's rep cache for another bank's (the §28.3 cross-bank join)",
     m1_swap_rep_cache, "C2b_REP_CACHE_BINDING"),
    ("M2", "drop the §23.1 exclusion (the 12 leaking rows per bank come back)",
     m2_drop_exclusion, "C1_POPULATION_IDENTITY"),
    ("M3", "make the exclusion unbalanced across classes (18 knife vs 12 bomb/gun)",
     m3_unbalance_exclusion, "C1b_EXCLUSION_BALANCE"),
    ("M4", "change one run's recorded bank_file_sha16",
     m4_wrong_bank_sha, "C2a_BANK_JOIN_METADATA"),
    ("M5", "put a test domain into its own training fold",
     m5_domain_in_own_fold, "C5_FOLD_DISCIPLINE"),
    ("M6", "report n_domains = 240 instead of 6 (rows treated as independent)",
     m6_rows_as_domains, "C7_INDEPENDENCE_UNIT"),
    ("M7", "flip the verdict string, leaving its input numbers unchanged",
     m7_flip_verdict, "C8_VERDICT_CONSISTENCY"),
    ("M8", "alter one reported layer to 20, outside the L6-14 band",
     m8_layer_out_of_band, "C4_LAYER_BAND"),
    # --- beyond the eight required, so that C3, C5b and C6 are exercised too
    ("M9", "misreport the blocking null's held-out accuracies, self-consistently",
     m9_wrong_null_accuracy, "C6_BLOCKING_NULL"),
    ("M10", "one run extracted with a different (still in-band) layer list",
     m10_config_drift, "C3_CONFIG_IDENTITY"),
    ("M11", "the blocking null's (layer, C) were not selected on cell B (§28.2)",
     m11_null_picks_not_from_B, "C5b_SELECTION_POPULATION"),
]


def run_verify_on_fixture(root, n_perm=FIX_NPERM, perm_seed=815):
    _BLOB_INFO.clear()
    cfg = Cfg(bank_dir=os.path.join(root, "data"), runs_root=os.path.join(root, "runs"),
              run_prefix="bombspec", json_path=os.path.join(root, "producer.json"),
              n_perm=n_perm, perm_seed=perm_seed, hnorm_rows=120, hnorm_stride=11,
              expect_rows=EXPECT_ROWS_PER_BANK)
    rep = Report()
    verify(cfg, rep)
    return rep


def cmd_mutate(work, keep=False, n_perm=FIX_NPERM):
    base = os.path.join(work, "baseline")
    print("[mutate] building the synthetic fixture (no real artifacts are read or written)...")
    build_fixture(base, verbose=True)
    rep0 = run_verify_on_fixture(base, n_perm=n_perm)
    rep0.print("BASELINE (unmutated fixture) — must VERIFY")
    if not rep0.ok():
        print("\nFAIL — the unmutated fixture does not verify, so no mutation result would mean "
              "anything.")
        return 1
    print("\n[mutate] each defect must be caught by ITS OWN designated check.  A defect caught only "
          "by some other check counts as NOT CAUGHT (C-049 §22.5).\n")
    rows, allok = [], True
    for mid, desc, fn, designated in MUTATIONS:
        mroot = os.path.join(work, f"mut_{mid}")
        shutil.rmtree(mroot, ignore_errors=True)
        shutil.copytree(base, mroot)
        _rebase_fixture(mroot)
        fn(mroot)
        rep = run_verify_on_fixture(mroot, n_perm=n_perm)
        st = rep.status_of(designated)
        caught = (st == "FAIL")
        allok &= caught
        others = [c for c in rep.failed() if c != designated]
        rows.append((mid, desc, designated, st, others))
        detail = next((m for c, s, m in rep.rows if c == designated), "")
        print(f"  {mid}  {'CAUGHT' if caught else '*** NOT CAUGHT ***'} by {designated} [{st}]")
        print(f"       inject : {desc}")
        print(f"       check  : {detail[:300]}")
        if others:
            print(f"       also fired (not required): {', '.join(others)}")
        if not keep:
            shutil.rmtree(mroot, ignore_errors=True)
    print("\n=== MUTATION HARNESS SUMMARY ===")
    for mid, desc, designated, st, others in rows:
        print(f"  {mid:<3} -> {designated:<28} {'CAUGHT' if st == 'FAIL' else 'NOT CAUGHT'}")
    unexercised = sorted(set(CHECK_DOC) - {r[2] for r in rows})
    print(f"  checks exercised by a mutation : {sorted({r[2] for r in rows})}")
    print(f"  checks NOT exercised by any mutation (declared, see --limitations): {unexercised}")
    if not keep:
        shutil.rmtree(base, ignore_errors=True)
    if allok:
        print("\nMUTATION HARNESS OK — every injected defect was caught by its own designated check.")
        return 0
    print("\nFAIL — at least one injected defect was not caught by its designated check.")
    return 1


# ==================================================================================================
# SELF-TEST — synthetic only, touches no real artifact
# ==================================================================================================
def cmd_self_test(work):
    fails = []

    def ck(name, cond, extra=""):
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{(' — ' + extra) if extra else ''}")
        if not cond:
            fails.append(name)

    print("[self-test] unit properties of the re-implemented rules")
    pat = concept_pattern("bomb")
    ck("word-boundary match is exact",
       bool(pat.search("a Bomb.")) and bool(pat.search("the bomb, yes"))
       and not pat.search("bombshell") and not pat.search("carbomb"),
       "'Bomb.' and 'the bomb,' match; 'bombshell'/'carbomb' do not")
    ck("§28.1 AND clause keeps cell B",
       is_excluded(dict(full_prompt="the bomb here", target_surface="button"), pat, "bomb")
       and not is_excluded(dict(full_prompt="the bomb here", target_surface="bomb"), pat, "bomb"),
       "concept word + surface != concept is excluded; surface == concept is retained")

    ck("verdict category parser",
       verdict_category("POSITIVE — x") == "POSITIVE"
       and verdict_category("VOID — the n_examples=0 null control FIRED") == "VOID"
       and verdict_category("NOT ATTRIBUTABLE — y") == "NOT ATTRIBUTABLE"
       and verdict_category(None) is None)

    base = dict(null_p=0.4, fit_capable=True, length_acc=0.34, probe_null_q95=0.40,
                primary_p=0.01, above_null=True, ctrl_p=0.01, primary_present=True)
    ck("§23.5 clause 1 (null fires) -> VOID",
       derive_verdict(**{**base, "null_p": 0.01})[0] == "VOID")
    ck("§23.5 train-fold gate -> VOID",
       derive_verdict(**{**base, "fit_capable": False})[0] == "VOID")
    ck("§23.5 clause 5 (length matches probe) -> VOID",
       derive_verdict(**{**base, "length_acc": 0.9})[0] == "VOID")
    ck("§23.5 missing control -> CANNOT ANSWER (not a failed control, §28.4)",
       derive_verdict(**{**base, "ctrl_p": None})[0] == "CANNOT ANSWER")
    ck("§23.5 clauses 3+4 -> POSITIVE", derive_verdict(**base)[0] == "POSITIVE")
    ck("§23.5 control does not clear -> NOT ATTRIBUTABLE",
       derive_verdict(**{**base, "ctrl_p": 0.4})[0] == "NOT ATTRIBUTABLE")
    ck("§23.5 primary does not clear -> NEGATIVE",
       derive_verdict(**{**base, "primary_p": 0.4})[0] == "NEGATIVE")

    t = mc_tolerance(0.5, 0.5, 200)
    ck("Monte-Carlo tolerance shrinks with n_perm",
       mc_tolerance(0.5, 0.5, 2000) < t and t < mc_tolerance(0.5, 0.5, 20)
       and mc_tolerance(0.0, 0.0, 200) >= 3.0 / 201,
       f"3-sigma band at p=0.5, n=200 is {t:.3f}; floored at 3/(n+1)")

    print("[self-test] planted-signal sanity of the re-implemented classifier")
    rng = np.random.default_rng(11)
    centres = {c: rng.normal(0, 1, 24) for c in PRIMARY_CLASSES}
    def synth(strength):
        rows = []
        for c in PRIMARY_CLASSES:
            for d in FIX_DOMAINS:
                for i in range(8):
                    rows.append(dict(domain=d, bank_block="core2x2", concept=c,
                                     vec=rng.normal(0, 1, (len(FIX_LAYERS), 24))
                                     + strength * centres[c][None, :]))
        return rows
    lab = lambda r: r["concept"]
    hot = loo_domain(synth(1.5), FIX_LAYERS, PRIMARY_CLASSES, lab,
                     selection_rows=synth(1.5))
    cold_rows = synth(0.0)
    cold = loo_domain(cold_rows, FIX_LAYERS, PRIMARY_CLASSES, lab, selection_rows=cold_rows)
    ck("planted class signal is detected", hot["mean_acc"] > 0.70, f"acc={hot['mean_acc']:.3f}")
    ck("pure noise lands near chance", abs(cold["mean_acc"] - 1.0 / 3) < 0.15,
       f"acc={cold['mean_acc']:.3f} vs chance 0.333")
    pv = permutation_p(cold_rows, FIX_LAYERS, PRIMARY_CLASSES, cold["picks"], 40, 5,
                       cold["mean_acc"])
    ck("group-permutation null is centred on the observed noise statistic",
       pv["p_one_sided"] is not None and pv["p_one_sided"] > 0.05,
       f"p={pv['p_one_sided']:.3f} null_mean={pv['null_mean']:.3f}")

    print("[self-test] end-to-end on the synthetic fixture (no real artifacts)")
    root = os.path.join(work, "selftest_fixture")
    info = build_fixture(root, verbose=True)
    rep = run_verify_on_fixture(root, n_perm=FIX_NPERM)
    rep.print("SELF-TEST FIXTURE")
    ck("the unmutated fixture VERIFIES", rep.ok(),
       "" if rep.ok() else f"failing: {rep.failed()}")
    ck("every declared check ran on the fixture",
       set(c for c, _, _ in rep.rows) == set(CHECK_DOC),
       f"missing: {sorted(set(CHECK_DOC) - {c for c, _, _ in rep.rows})}")
    shutil.rmtree(root, ignore_errors=True)

    print()
    if fails:
        print(f"SELF-TEST FAILED: {fails}")
        return 1
    print("SELF-TEST OK — all unit properties hold and the synthetic fixture verifies.")
    return 0


LIMITATIONS = """
WHAT THIS VERIFIER CANNOT CHECK (stated so it is not mistaken for more than it is)
---------------------------------------------------------------------------------
1. It cannot verify the HIDDEN STATES themselves.  It ties each rep cache to its own run through
   that run's `results.jsonl` hnorm columns, which catches a swapped or mis-pointed cache; it does
   NOT re-run the model, so a cache and a results table produced together from the wrong prompt,
   the wrong position, or the wrong layer would agree with each other and pass.  Re-extraction is
   the only check for that, and it is out of scope here.
2. It recomputes ONE statistic end-to-end: the blocking n_examples=0 null (§23.2).  The P2 primary,
   P1, the 2-way contrasts, the cell-F comparator, the LOBO secondary and the length-only control
   are checked structurally (population, folds, layer band, derived-field arithmetic, verdict
   logic) but their accuracies are NOT independently recomputed.  A producer that mis-fitted the
   primary while reporting internally consistent folds would pass.
3. The mutation harness runs on a SYNTHETIC fixture, not on the real caches: proving that every
   check FIRES on its own defect, not that the real run is free of those defects.  Its baseline
   producer JSON is generated by this file's own re-implementation, so the harness demonstrates
   check sensitivity, never producer correctness.
4. Two checks are not exercised by any mutation: C0 (class-set completeness) and C2c (the
   prompt_id collision demonstration).  Both are positive controls on the artifacts themselves
   rather than on the producer, and both would have to be broken by deleting a run or by a bank
   regeneration, which the harness does not simulate.  C9 is exercised only indirectly.
5. It cannot audit the PREREGISTRATION.  If §23.5's rule, the L6-14 band, the domain-as-unit
   choice or the exclusion rule are themselves wrong, this file reproduces the error faithfully.
   `C-053` §28.5's structural confound (cells C and F sit in disjoint template blocks) is an
   example: it is unfixable in these banks and this verifier does not detect it.
6. Monte-Carlo agreement on the permutation p is a statistical, not an exact, statement.  Two
   independent estimates can agree within the band while both being wrong in the same direction if
   the permutation SCHEME (not the RNG) is misconceived.
7. It reads §23.5's input numbers from the producer to re-derive the verdict.  Each of those
   inputs is separately checked (C6, C9, C5, C7), but the check is verdict-vs-inputs consistency,
   not an independent recomputation of every input.
8. It says nothing about EXTERNAL VALIDITY.  A run that passes every check here is internally
   sound; whether the probe measures Bombness rather than remapping strength is what §23.5's
   knife-vs-club clause is for, and that is a scientific question this file only bookkeeps.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Independent verifier for DCS-PR-035.")
    ap.add_argument("--self-test", action="store_true",
                    help="synthetic only; no real artifact is read")
    ap.add_argument("--mutate", action="store_true",
                    help="prove every check FAILS on its own injected defect")
    ap.add_argument("--limitations", action="store_true", help="print what this cannot check")
    ap.add_argument("--json", default="outputs/boombness/dcs_analysis/dcs_bombness_specificity.json")
    ap.add_argument("--bank-dir", default="data/boombness_prompts")
    ap.add_argument("--runs-root", default="outputs/boombness/extract_boombness")
    ap.add_argument("--run-prefix", default="bombspec")
    ap.add_argument("--channel", default=PRIMARY_CHANNEL)
    ap.add_argument("--n-perm", type=int, default=0,
                    help="permutations for the independent null recomputation (0 = use the "
                         "producer's own n_perm)")
    ap.add_argument("--perm-seed", type=int, default=815,
                    help="deliberately NOT the producer's seed: the null must reproduce as a "
                         "statistic, not as an RNG stream")
    ap.add_argument("--hnorm-rows", type=int, default=300)
    ap.add_argument("--hnorm-stride", type=int, default=7)
    ap.add_argument("--expect-rows", type=int, default=EXPECT_ROWS_PER_BANK)
    ap.add_argument("--work", default=None, help="scratch dir for fixtures (default: a temp dir)")
    ap.add_argument("--keep", action="store_true", help="keep mutated fixtures for inspection")
    a = ap.parse_args(argv)

    if a.limitations:
        print(LIMITATIONS)
        return 0
    if a.self_test or a.mutate:
        work = a.work or tempfile.mkdtemp(prefix="pr035_verify_")
        os.makedirs(work, exist_ok=True)
        try:
            rc = cmd_self_test(work) if a.self_test else cmd_mutate(work, keep=a.keep)
        finally:
            if not a.work and not a.keep:
                shutil.rmtree(work, ignore_errors=True)
        return rc

    cfg = Cfg(bank_dir=a.bank_dir, runs_root=a.runs_root, run_prefix=a.run_prefix,
              json_path=a.json, channel=a.channel, n_perm=a.n_perm, perm_seed=a.perm_seed,
              hnorm_rows=a.hnorm_rows, hnorm_stride=a.hnorm_stride, expect_rows=a.expect_rows)
    print(f"[verify] producer JSON : {cfg.json_path}")
    print(f"[verify] banks         : {cfg.bank_dir}")
    print(f"[verify] runs          : {cfg.runs_root}/{cfg.run_prefix}_*")
    rep = Report()
    ctx = verify(cfg, rep)
    if ctx is None:
        print("\nCANNOT VERIFY — the producer JSON does not exist yet.  This verifier was written "
              "blind to it (C-049 §22.5); run the producer first.")
        for n in rep.notes:
            print(f"  (note) {n}")
        return 2
    rep.print()
    print(f"\n  producer verdict: {ctx['res'].get('verdict')!r}")
    print("\nRun --limitations for what this verifier does NOT check.")
    return 0 if rep.ok() else 1


if __name__ == "__main__":
    raise SystemExit(main())
