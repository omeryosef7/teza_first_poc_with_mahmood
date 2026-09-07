#!/usr/bin/env python3
"""The two EXPLORATORY re-analyses of the ts116m extraction: `DCS-PR-049` and `DCS-PR-052`.

**NOTHING THIS SCRIPT PRODUCES CARRIES CONFIRMATORY WEIGHT.**  Both preregistrations place
themselves in the `EXPLORATORY` family of the phase multiplicity block, whose declared correction
is *"none -- exploratory results carry no confirmatory weight and are labelled as such"*.  The
label is not a courtesy added by this file: `check_exploratory_declared()` reads the family out of
the preregistration and REFUSES to run if the preregistration's own `multiplicity` block does not
list this `id` under `EXPLORATORY`.  It is therefore impossible to point this analyzer at
`PR-048` or `PR-053` and obtain a number, which is the only way to make the label load-bearing
rather than decorative.

  A. `DCS-PR-049` -- knife vs gun, unstratified.  **DEMOTED to exploratory by `C-101`:** its
     conjunctive power is 0.793 at its own Holm alpha, below the 0.80 bar.  The estimate is
     reported against its MEASURED nuisance floor of 0.7065 (`R-106` Y3), never against 0.5: a
     17-feature bag of surface counts already reaches 0.7065 on this contrast without reading a
     single hidden state.
  B. `DCS-PR-052` -- knife vs gun WITHIN arm-balanced joint-simplex cells, the one construction
     (`C-100`/Z1) in which the surface classifier is verifiably at chance: 0.5054,
     CI [0.4629, 0.5479], 552 rows, 23 domains.  Power there is 0.721.  Declared exploratory
     before it was run, not after it disappointed.

**A NULL FROM EITHER IS `CANNOT ANSWER`, NOT EVIDENCE OF ABSENCE.**  Both `primary.negative`
clauses are honoured: `PR-049`'s requires power >= 0.8, which `C-101` withdrew; `PR-052`'s says
`NOT AVAILABLE` in the file itself.  So this script prints an ESTIMATE, an INTERVAL and a FLOOR,
and it never prints a verdict.  `assert_no_verdict()` scans the artifact it just wrote for the
strings a confirmatory analyzer would emit and refuses to leave them there.

REUSE, NOT RE-IMPLEMENTATION.  The statistics, the run discovery, the bank-sha verification, the
explained/unexplained missing-row rule and the selection trace are IMPORTED from
`scripts/dcs_ts_pr048_analysis.py`; the 17 surface features, the checks ledger and the
zero-binding refusal from `scripts/dcs_ts_pr049_blockers.py`.  A difference between these numbers
and the primary's is therefore a difference of DESIGN, not of arithmetic.  EVERY THRESHOLD comes
out of the preregistration through `Prereg.require()`, which refuses rather than defaulting;
there is no numeric gate literal below.

WHAT IT REFUSES TO DO, each because of a specific recorded failure:
  * share an `--out` path between the two preregistrations   -- `C-093` (a shared default would
    have had the co-primary destroy the primary); `--out` is REQUIRED and a file already carrying
    a different `id` is not overwritten
  * select on TEST                                           -- measured FPR 0.4433 vs 0.0467
  * permute at row level                                     -- measured FPR 0.2000
  * print a p without its floor                              -- `C-069`
  * call a saturated selection surface localisation          -- `C-070`
  * report a statistic over a set it never counted           -- `C-074`; every check binds a
    counted set and a zero bind is a FAIL, never a PASS
  * quote the preregistered surface floor without re-deriving it on the rows actually analysed --
    `PR-052`'s own rule ("the floor is the measured surface accuracy in the SAME cells, verified
    per run")

USAGE
    python3 scripts/dcs_ts_exploratory.py --prereg configs/dcs_ts_pr049.json \
        --reps outputs/boombness/extract_boombness --out outputs/dcs_ts/pr049_exploratory.json
    python3 scripts/dcs_ts_exploratory.py --prereg configs/dcs_ts_pr052.json \
        --reps outputs/boombness/extract_boombness --out outputs/dcs_ts/pr052_exploratory.json
    python3 scripts/dcs_ts_exploratory.py --selftest          # no data needed
    python3 scripts/dcs_ts_exploratory.py --prereg ... --reps ... --out ... --mutate
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, OrderedDict, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))

# BLAS threads are pinned BEFORE numpy is imported, so the numerics cannot depend on how busy the
# node is, and so N joblib processes do not each spawn 16 BLAS threads on a 16-core login node.
# `C-107` is the caution here: pinning this to 1 is what made the primary's 36-point selection
# loop several times slower and nearly walled the run that reads TEST -- but that loop was
# SEQUENTIAL. Here both the selection grid and the permutation are parallel across PROCESSES, so
# one BLAS thread each is the right setting and the two are not in tension. Recorded because the
# same value was wrong for the other design.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np                                                        # noqa: E402

from dcs_ts_prereg import Prereg, PreregError, load as load_prereg        # noqa: E402
# THE FROZEN PRIMARY ANALYZER'S OWN HELPERS.  Imported, not copied: if the primary's sign test,
# permutation p, p-floor formatting or selection trace were ever to change, these two exploratory
# numbers would change with them rather than silently diverging.
from dcs_ts_pr048_analysis import (                                       # noqa: E402
    sign_test_two_sided, group_permutation_p, fmt_p, select_hparams,
    bind_population, load_split, _find_run, load_bank_rows,
)
import dcs_ts_pr049_blockers as B                                         # noqa: E402

Checks = B.Checks
ZeroBinding = B.ZeroBinding
register_features = B.register_features

#: Which mode each preregistration is analysed in.  Keyed by the preregistration's own `id`, so
#: pointing this script at anything else is a refusal rather than a guess.
MODES = {
    "DCS-PR-049": "unstratified",
    "DCS-PR-052": "arm_balanced_cells",
}

#: The stratification `Z1` measured the 0.5054 surface floor in, named here exactly as
#: `scripts/dcs_ts_pr050_pr051_blockers.py::STRAT_SPECS` names it.  It is NOT a threshold and NOT
#: a free choice made after seeing an outcome: it is the single construction `C-100` reports as
#: reaching chance, chosen on VALIDATION before the test split was read.
SIMPLEX_TIERS = 3
SIMPLEX_STRAT_NAME = "simplex_t3"
#: `_balanced_subsample`'s seed in that same file, reused so the subsample is the same draw.
BALANCE_SEED = 20260907
#: The surface classifier of `Z1`/`R-106` Y3, reused verbatim.
SURFACE_MAX_ITER = 4000
SURFACE_SEED = 0
#: The probe estimator's budget.  Identical for the observed statistic and for every permutation
#: draw (`C-092`): a permutation test is valid only when the LABELS are the sole difference.
PROBE_MAX_ITER = 2000

#: Strings a CONFIRMATORY analyzer emits.  `assert_no_verdict()` refuses to leave any of them in
#: an artifact written by this file.
FORBIDDEN_IN_ARTIFACT = ("SUPPORTS THE CLAIM", "NOT SIGNIFICANT", "significant at",
                         "CONFIRMS", "we conclude that")


# ==============================================================================================
# small statistics that the primary analyzer does not own
# ==============================================================================================
def t_interval(vals, conf=0.95):
    """Two-sided t interval on the DOMAIN means.  The unit is the domain, never the row."""
    from scipy import stats
    v = np.asarray(list(vals), dtype=float)
    n = len(v)
    if n < 2:
        raise ZeroBinding("t interval over %d domain(s) -- the interval bound nothing" % n)
    m = float(v.mean())
    sd = float(v.std(ddof=1))
    h = float(stats.t.ppf(0.5 + conf / 2.0, n - 1)) * sd / np.sqrt(n)
    return m, [m - h, m + h], sd, n


def domain_bootstrap_ci(vals, n_boot, seed, conf=0.95):
    """Percentile bootstrap RESAMPLING DOMAINS, not rows.  `A-039`: the row-level version of this
    interval is the same defect as the row-level permutation -- it reports an n it does not have.
    """
    v = np.asarray(list(vals), dtype=float)
    if len(v) < 2:
        raise ZeroBinding("bootstrap over %d domain(s)" % len(v))
    rng = np.random.default_rng(seed)
    draws = v[rng.integers(0, len(v), size=(int(n_boot), len(v)))].mean(axis=1)
    lo = float(np.quantile(draws, 0.5 - conf / 2.0))
    hi = float(np.quantile(draws, 0.5 + conf / 2.0))
    return [lo, hi], int(n_boot)


def fit_predict(Xtr, ytr, Xte, C_, max_iter=PROBE_MAX_ITER):
    """ONE estimator factory, used byte-identically for the observed statistic, for every
    selection point and for every permutation draw (`C-092`: the observed fit once used
    max_iter=2000 and the null 200, which makes the permuted -- strictly harder -- problem the
    only one whose budget can bind, depressing the null and making p too small).

    It is a MODULE-LEVEL function taking its matrices as ARGUMENTS rather than a closure, so
    joblib memory-maps the big arrays once and de-duplicates them across tasks instead of
    pickling a 666 MB copy into each of N worker processes.
    """
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(C=C_, max_iter=max_iter).fit(Xtr, ytr).predict(Xte)


def domain_mean(pred, truth, doms):
    per = {}
    for d in sorted(set(doms)):
        m = doms == d
        per[d] = float((pred[m] == truth[m]).mean())
    return float(np.mean(list(per.values()))), per


def clopper_pearson(k, n, alpha=0.05):
    from scipy import stats
    if n == 0:
        raise ZeroBinding("Clopper-Pearson over ZERO rows")
    lo = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2.0, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1 - alpha / 2.0, k + 1, n - k))
    return [lo, hi]


# ==============================================================================================
# preregistration-side guards
# ==============================================================================================
def check_exploratory_declared(pr: Prereg, C: Checks) -> str:
    """The EXPLORATORY label must come out of the PREREGISTRATION, not out of this file.

    Otherwise "labelled exploratory" is a sentence I wrote, and sentences drift; a config that
    later promoted itself to PRIMARY would still be analysed by this script and still print the
    word.  Reading the family back is what makes the label falsifiable.
    """
    pid = pr.require("id")
    fams = pr.require("multiplicity", "families")
    exp = [f for f in fams if f.get("name") == "EXPLORATORY"]
    if not exp:
        raise PreregError("%s declares no EXPLORATORY family; this analyzer only runs designs "
                          "the preregistration itself places outside the confirmatory families"
                          % pid)
    members = [str(m) for m in exp[0].get("members", [])]
    declared = any(pid in m for m in members)
    other = [f["name"] for f in fams if f.get("name") != "EXPLORATORY"
             and any(pid in str(m) for m in f.get("members", []))]
    C.add("EXPLORATORY-DECLARED",
          "the preregistration ITSELF places %s in the EXPLORATORY family (correction: none), "
          "and in no confirmatory family -- the exploratory label is read out of the frozen "
          "config, not asserted by the analyzer" % pid,
          declared and not other, len(members),
          "EXPLORATORY members %s; correction=%r; this id also appears in %s"
          % (members, exp[0].get("correction"), other or "no other family"))
    if not declared:
        raise PreregError("%s is not a declared EXPLORATORY member: %s. Refusing -- this script "
                          "must not be able to produce a confirmatory number." % (pid, members))
    if pid not in MODES:
        raise PreregError("no analysis mode is defined for %s" % pid)
    return MODES[pid]


def require_floor(pr: Prereg) -> dict:
    """The nuisance floor, through `require()` so a preregistration that forgets one cannot be
    analysed at all.  `B-020` was a published threshold no code path read; the fix is not to copy
    it here but to make this file unable to run without it."""
    nf = pr.require("primary", "nuisance_floor")
    for k in ("accuracy", "source", "rule"):
        if k not in nf:
            raise PreregError("primary.nuisance_floor is missing %r -- a floor without its "
                              "provenance is a number, not a bar" % k)
    return nf


# ==============================================================================================
# population binding -- metadata only, so the cheap guards do not need 10 GB of tensors
# ==============================================================================================
def bind_rows(pr: Prereg, spec: dict, mut=None) -> list:
    """Bind the analysed rows from the RAW bank JSONL.  Concept and codeword are re-derived from
    the FILE that was opened, never from the row's self-description."""
    cell = spec["cell"]
    if mut == "empty_population":
        cell = "Z"
    excluded = set(spec["excluded_domains"])
    if mut == "keep_excluded_domains":
        excluded = set()
    rows = []
    for bname, bpath in sorted(spec["banks"].items()):
        cw, cc = bname.split("_", 1)
        if cc not in spec["concepts"]:
            continue
        allr = bank_rows(bpath)
        if not allr:
            raise ZeroBinding("bank %s has no rows at all" % bname)
        for pid, r in allr.items():
            if (r["cell"] != cell or r["query_kind"] != spec["query_kind"]
                    or r["n_examples"] != spec["n_examples"] or r["domain"] in excluded):
                continue
            if r["demo_block"] not in r["full_prompt"]:
                raise ZeroBinding("demo_block is not a substring of full_prompt in %s" % pid)
            rows.append(dict(pid=pid, bank=bname, codeword=cw, concept=cc,
                             domain=r["domain"], demo_block=r["demo_block"]))
    return rows


def population_checks(C: Checks, pr: Prereg, spec: dict, rows: list, assign: dict) -> None:
    C.add("POP-BIND",
          "the population binds a NON-ZERO, counted set of rows -- cell %r x %s x n_examples=%s "
          "over concepts %s. A filter that binds nothing is the C-074 shape and must be loud"
          % (spec["cell"], spec["query_kind"], spec["n_examples"], spec["concepts"]),
          len(rows) > 0, len(rows),
          "%d rows, %d domains, arms %s, codewords %s"
          % (len(rows), len(set(r["domain"] for r in rows)),
             dict(Counter(r["concept"] for r in rows)),
             dict(Counter(r["codeword"] for r in rows))))

    bad = sorted(set(r["domain"] for r in rows) & set(spec["excluded_domains"]))
    C.add("EXCLUSIONS-APPLIED",
          "no preregistered whole-population exclusion (%s) survives into the analysed rows"
          % ", ".join(spec["excluded_domains"]),
          not bad, len(rows), "excluded domains present: %s" % (bad or "none"))

    doms = {s: set(r["domain"] for r in rows if assign.get(r["domain"]) == s)
            for s in ("train", "validation", "test")}
    unassigned = sorted(set(r["domain"] for r in rows) - set(assign))
    ok = (not unassigned and not (doms["train"] & doms["test"])
          and not (doms["train"] & doms["validation"])
          and not (doms["validation"] & doms["test"])
          and all(doms[s] for s in doms))
    C.add("SPLIT-DISJOINT",
          "every analysed domain carries a split assignment from the frozen manifest and the "
          "three splits are DOMAIN-DISJOINT -- the independence unit is the domain, so a shared "
          "domain is leakage no row-level check would see",
          ok, len(rows),
          "train %d / validation %d / test %d domains; unassigned %s; overlaps train&test %d, "
          "train&val %d, val&test %d"
          % (len(doms["train"]), len(doms["validation"]), len(doms["test"]),
             unassigned or "none", len(doms["train"] & doms["test"]),
             len(doms["train"] & doms["validation"]), len(doms["validation"] & doms["test"])))


# ==============================================================================================
# representations
# ==============================================================================================
#: Parsed bank rows, memoised by absolute path. Each `ts116m` bank JSONL is ~72 MB and the
#: pipeline reads four of them at least twice per invocation; the mutation harness runs the
#: pipeline a dozen times, which is ~3.5 GB of JSON parsing to demonstrate guards that do not
#: depend on re-parsing. The FROZEN primary analyzer's `load_bank_rows` is still the only parser
#: -- this wraps it, it does not replace it.
_BANK_CACHE: dict = {}


def bank_rows(path: str) -> dict:
    fp = path if os.path.isabs(path) else os.path.join(REPO, path)
    if fp not in _BANK_CACHE:
        _BANK_CACHE[fp] = load_bank_rows(fp)
    return _BANK_CACHE[fp]


#: run directory -> {"layers", "present" (pids the cache holds), "rows" (pid -> float32 (L,4096))}.
#: The four caches are 1.6 GB each and live on NFS; a cold read of all four takes minutes. The
#: mutation harness runs the whole pipeline a dozen times, so without this each mutation would
#: re-read 6.4 GB to demonstrate a guard. Keyed by RUN DIRECTORY, and the bound rows are the
#: preregistered cell filter WITHOUT the exclusions applied, so a mutation that changes which
#: domains are excluded still finds every vector it needs in the cache rather than silently
#: analysing fewer rows than it asked for.
_REPS_CACHE: dict = {}


def _bank_reps(run_dir: str, bpath: str, cell: str, qk: str, nex) -> dict:
    import torch
    ent = _REPS_CACHE.get(run_dir)
    if ent is not None:
        return ent
    allr = bank_rows(bpath)
    want = {pid for pid, r in allr.items()
            if r["cell"] == cell and r["query_kind"] == qk and r["n_examples"] == nex}
    if not want:
        raise ZeroBinding("bank %s binds ZERO rows at cell=%r %s n_examples=%s"
                          % (bpath, cell, qk, nex))
    cache = torch.load(os.path.join(run_dir, "cache", "final_occurrence_reps.pt"),
                       map_location="cpu", weights_only=False)
    reps = cache["reps"]
    ent = dict(layers=list(cache["layers"]), present=set(reps.keys()),
               rows={pid: reps[pid].float().numpy() for pid in want if pid in reps})
    del cache, reps
    _REPS_CACHE[run_dir] = ent
    return ent


def load_reps(pr: Prereg, spec: dict, rows: list, reps_root: str, tag_prefix: str,
              C: Checks, mut=None):
    """Load the cached hidden states for the bound rows, verifying every run against the pin.

    The bank-sha / position / attn / knockout verification and the explained-vs-unexplained
    missing-row rule are the frozen primary analyzer's, restated as CHECKS rather than bare
    raises so that `--mutate` can demonstrate each of them going RED.
    """
    layer_grid = pr.require("read_site", "layer_grid")
    banks = pr.require("population", "banks")
    want_pos = pr.require("read_site", "position")
    want_attn = pr.require("model", "attn_impl")
    excluded = set(spec["excluded_domains"])

    by_bank = defaultdict(list)
    for r in rows:
        by_bank[r["bank"]].append(r)

    bind_detail, bind_ok = [], True
    miss_detail, miss_ok = [], True
    X_by_layer = {L: [] for L in layer_grid}
    meta = []
    n_rows_checked = 0

    for bname in sorted(by_bank):
        run = _find_run(reps_root, "%s_%s" % (tag_prefix, bname))
        summ = json.load(open(os.path.join(run, "summary.json")))
        got_sha = summ.get("bank_rows_sha16")
        if mut == "wrong_bank_sha" and bname == sorted(by_bank)[0]:
            got_sha = "0" * 16
        want_sha = banks[bname]["bank_rows_sha16"]
        n_failed = summ.get("failures", {}).get("n_failed", -1)
        okb = (got_sha == want_sha and summ.get("position") == want_pos
               and summ.get("attn_implementation") == want_attn
               and summ.get("knockout_applied") is False and n_failed >= 0)
        bind_ok = bind_ok and okb
        bind_detail.append("%s: sha %s vs pinned %s, position=%r attn=%r knockout=%r n_failed=%s"
                           % (bname, got_sha, want_sha, summ.get("position"),
                              summ.get("attn_implementation"), summ.get("knockout_applied"),
                              n_failed))

        ent = _bank_reps(run, spec["banks"][bname], pr.require("population", "cell"),
                         pr.require("population", "query_kind_primary"),
                         pr.require("population", "n_examples_primary"))
        run_layers = ent["layers"]
        present, vecs = ent["present"], ent["rows"]
        if mut == "forge_missing":
            present, vecs = set(present), dict(vecs)
            for r in by_bank[bname][:3]:
                present.discard(r["pid"])
                vecs.pop(r["pid"], None)

        # THE EXPLAINED / UNEXPLAINED RULE.  A row missing from the cache is tolerated only if its
        # domain is a preregistered whole-population exclusion (R-108: 30 basket_bomb rows, all
        # school_campus, refused by the extractor for the right reason).  An UNEXPLAINED failure
        # silently shrinks the population and is a refusal.
        allr = bank_rows(spec["banks"][bname])
        missing = [pid for pid in allr if pid not in present]
        unexplained = sorted({allr[pid]["domain"] for pid in missing} - excluded)
        n_un = sum(1 for pid in missing if allr[pid]["domain"] not in excluded)
        miss_ok = miss_ok and not unexplained
        miss_detail.append("%s: %d missing of %d bank rows, %d unexplained in domains %s"
                           % (bname, len(missing), len(allr), n_un, unexplained[:3] or "none"))

        for r in by_bank[bname]:
            t = vecs.get(r["pid"])
            if t is None:
                continue          # already accounted for by the missing-row check above
            for L in layer_grid:
                X_by_layer[L].append(t[run_layers.index(L)])
            meta.append(r)
            n_rows_checked += 1

    C.add("RUN-BINDING",
          "every extraction run analysed was produced from the PINNED bank rows, at the "
          "preregistered read site %r, with attn %r and no knockout -- a run that measures a "
          "different population than the frozen one is VOID, not a result" % (want_pos, want_attn),
          bind_ok, len(rows), " | ".join(bind_detail))
    C.add("MISSING-ROWS",
          "every bank row absent from a cache belongs to a preregistered whole-population "
          "exclusion; an UNEXPLAINED extraction failure would shrink the analysed population "
          "without saying so",
          miss_ok, len(rows), " | ".join(miss_detail))
    C.add("REPS-BIND",
          "the representation matrix binds one vector per analysed row at every grid layer -- a "
          "silently short matrix is a statistic over a set that was never counted",
          n_rows_checked == len(meta) and len(meta) > 0
          and all(len(X_by_layer[L]) == len(meta) for L in layer_grid),
          len(meta), "%d rows x %d layers x %d dims"
          % (len(meta), len(layer_grid),
             len(X_by_layer[layer_grid[0]][0]) if meta else 0))
    if not meta:
        raise ZeroBinding("ZERO rows carry representations -- refusing to report a statistic "
                          "over an empty set")
    Xs = {L: np.stack(X_by_layer[L]) for L in layer_grid}
    return Xs, meta


# ==============================================================================================
# the arm-balanced joint-simplex cells (PR-052 only)
# ==============================================================================================
def fit_surface(rows_tr, rows_ev, classes, mut=None):
    """The 17-feature register/surface classifier of `R-106` Y3 and `C-100` Z1, fit on TRAIN
    demonstration blocks only and scored on the evaluated split."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    tr = [r for r in rows_tr if r["concept"] in classes]
    ev = [r for r in rows_ev if r["concept"] in classes]
    if not tr or not ev:
        raise ZeroBinding("surface classifier bound %d train / %d eval rows" % (len(tr), len(ev)))
    if set(r["domain"] for r in tr) & set(r["domain"] for r in ev):
        raise ZeroBinding("surface classifier TRAIN and EVAL share domains")
    Xtr = np.asarray([register_features(r["demo_block"]) for r in tr], dtype=float)
    Xev = np.asarray([register_features(r["demo_block"]) for r in ev], dtype=float)
    ytr = np.asarray([r["concept"] for r in tr])
    yev = np.asarray([r["concept"] for r in ev])
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=SURFACE_MAX_ITER, random_state=SURFACE_SEED)
    clf.fit(sc.transform(Xtr), ytr)
    proba = clf.predict_proba(sc.transform(Xev))
    pred = clf.classes_[np.argmax(proba, axis=1)]
    return dict(rows=ev, y=yev, pred=pred, proba=proba, classes=list(clf.classes_),
                n_train=len(tr), n_features=int(Xtr.shape[1]))


def simplex_cells(proba, tiers=SIMPLEX_TIERS, edges_from=None):
    """`simplex_t3`: coarsen EVERY coordinate of the predicted-probability vector into `tiers`
    equal-frequency tiers and take the cross-product cells.  Copied in behaviour from
    `dcs_ts_pr050_pr051_blockers.py::_strata_vector(kind='simplex')`.

    NO LABEL ENTERS THIS FUNCTION.  The cells are a function of the surface classifier's
    predicted probabilities alone, which is what makes them constructible on the test split
    without reading a test label (`PR-052` `void`: "cells constructed using TEST labels").
    """
    src = proba if edges_from is None else edges_from
    t = np.zeros_like(proba, dtype=int)
    for j in range(proba.shape[1]):
        edges = np.quantile(src[:, j], np.linspace(0, 1, tiers + 1)[1:-1])
        t[:, j] = np.digitize(proba[:, j], edges)
    keys = [tuple(r) for r in t]
    return [("cell%s" % (list(k),), np.asarray([kk == k for kk in keys]))
            for k in sorted(set(keys))]


def arm_balance(fit, cells, mut=None):
    """Subsample every (domain x cell) to its SMALLEST arm, so the concepts are equally frequent
    inside every cell BY CONSTRUCTION.  `C-100`: conditioning on a predicted score does not make
    the arms equally frequent, and binning alone cannot change pooled accuracy -- the balance has
    to be enforced, not assumed.  A cell that cannot be balanced is DROPPED and counted.
    """
    rng = np.random.RandomState(BALANCE_SEED)
    keep = np.zeros(len(fit["y"]), dtype=bool)
    idx = np.arange(len(fit["y"]))
    n_cells, n_dropped = 0, 0
    for _cname, m in cells:
        for dname, arms in _group_by_domain(fit, idx[m]).items():
            n_cells += 1
            if len(arms) < len(fit["classes"]) or min(len(v) for v in arms.values()) == 0:
                n_dropped += 1
                continue
            k = (max if mut == "unbalanced_subsample" else min)(len(v) for v in arms.values())
            for _c, v in arms.items():
                keep[rng.choice(v, size=min(k, len(v)), replace=False)] = True
    if not keep.any():
        raise ZeroBinding("the arm-balanced subsample bound ZERO rows")
    return keep, dict(n_domain_cells=n_cells, n_dropped=n_dropped,
                      n_kept=int(keep.sum()), n_total=int(len(keep)),
                      frac_retained=float(keep.sum()) / float(len(keep)),
                      arm_counts=dict(Counter(fit["y"][keep].tolist())))


def _group_by_domain(fit, indices):
    by = defaultdict(lambda: defaultdict(list))
    for i in indices:
        by[fit["rows"][i]["domain"]][fit["y"][i]].append(i)
    return by


def surface_accuracy(fit, keep):
    """The floor, RE-DERIVED on the rows actually analysed.  `PR-052`'s own rule: 'the floor is
    the measured surface accuracy in the SAME cells, verified per run, never the nominal chance
    level'.  A floor quoted from the preregistration and never re-measured on the split being
    read is the `B-020` failure wearing a different hat."""
    y, pred = fit["y"][keep], fit["pred"][keep]
    k, n = int((y == pred).sum()), int(len(y))
    per = defaultdict(list)
    for r, p, t in zip([r for r, m in zip(fit["rows"], keep) if m], pred, y):
        per[r["domain"]].append(1.0 if p == t else 0.0)
    return dict(acc=k / float(n), n_rows=n, n_domains=len(per), ci=clopper_pearson(k, n),
                domain_mean_acc=float(np.mean([np.mean(v) for v in per.values()])),
                arm_counts=dict(Counter(y.tolist())))


# ==============================================================================================
# the analysis
# ==============================================================================================
def run(pr: Prereg, mode: str, a, C: Checks, mut=None) -> dict:
    from joblib import Parallel, delayed
    from sklearn.preprocessing import StandardScaler

    t0 = time.time()
    concepts = list(pr.require("population", "concepts"))
    chance = pr.require("primary", "chance")
    alpha = pr.require("primary", "alpha")
    unit = pr.require("primary", "independence_unit")
    if unit != "domain":
        raise PreregError("independence_unit is %r; this analyzer only implements 'domain'" % unit)
    n_perm = int(a.n_perm_override or pr.require("primary", "n_perm"))
    layer_grid = list(pr.require("read_site", "layer_grid"))
    c_grid = list(pr.require("read_site", "C_grid"))
    if mut is not None:
        # A reduced but still >1-point grid. It has to stay larger than one point, or
        # select_hparams would report `inert` for EVERY mutation by arithmetic and the
        # `inert_grid` mutation would demonstrate nothing.
        # The two SMALLEST C values, not the extremes. Weak regularisation converges slowly at
        # 4096 features -- measured: the first attempt at this harness put C=10 in the reduced
        # grid and a single mutation ran for over twenty minutes, which turns a guard
        # demonstration into a scheduling problem. The mutations exercise the guards, not the
        # numerics, so the cheap end of the grid is the right end.
        mid = len(layer_grid) // 2
        layer_grid, c_grid = layer_grid[mid:mid + 2], sorted(c_grid)[:2]

    # ---- the floor, through require() --------------------------------------------------------
    floor_ok, nf = True, None
    try:
        nf = require_floor(pr) if mut != "drop_floor" else require_floor(_stripped_floor(pr))
    except PreregError as e:
        floor_ok, nf = False, {"accuracy": None, "source": str(e), "rule": ""}
    C.add("FLOOR-DECLARED",
          "the preregistration declares a MEASURED nuisance floor and this analyzer reads it "
          "through require(), so a design without a floor cannot be analysed at all -- the "
          "estimate is reported against that floor, never against the nominal chance level",
          floor_ok and isinstance(nf.get("accuracy"), float), 1,
          "floor=%s  source=%s" % (nf.get("accuracy"), str(nf.get("source"))[:120]))

    spec = bind_population(pr)
    assign = load_split(pr)
    if mut == "corrupt_split":
        # Five TEST domains lose their manifest assignment entirely. A domain the manifest does
        # not place is the silent version of leakage: it falls out of every mask without anyone
        # counting it, and the domain-mean is then over a population nobody declared.
        assign = dict(assign)
        for d in sorted(d for d, s in assign.items() if s == "test")[:5]:
            assign.pop(d)
    _log(mut, "binding population from the raw bank JSONL")
    rows = bind_rows(pr, spec, mut=mut)
    population_checks(C, pr, spec, rows, assign)
    if not rows:
        raise ZeroBinding("the population bound ZERO rows")

    _log(mut, "loading representations (%d rows)" % len(rows))
    Xs, meta = load_reps(pr, spec, rows, a.reps, a.tag_prefix, C, mut=mut)
    y = np.array([concepts.index(m["concept"]) for m in meta])
    dom = np.array([m["domain"] for m in meta])
    spl = np.array([assign.get(m["domain"], "UNASSIGNED") for m in meta])
    tr, va, te = spl == "train", spl == "validation", spl == "test"
    if mut == "empty_test":
        te = np.zeros_like(te)
    for nm, msk in (("train", tr), ("validation", va), ("test", te)):
        C.add("BIND-%s" % nm.upper(),
              "the %s split binds a NON-ZERO counted set of rows and domains" % nm,
              bool(msk.sum()), int(msk.sum()),
              "%d rows / %d domains" % (msk.sum(), len(set(dom[msk]))))
    if not te.sum() or not tr.sum() or not va.sum():
        raise ZeroBinding("a split bound ZERO rows")

    # ---- THE FLOOR, RE-DERIVED ON THE TEST ROWS ACTUALLY ANALYSED ----------------------------
    # Both preregistered floors (0.7065 for PR-049, 0.5054 for PR-052) were measured on
    # VALIDATION. A floor quoted from a config and never re-measured on the split being read is
    # `B-020` wearing a different hat, and PR-052's own rule already demands the per-run version.
    # It is also the only way to compare like with like: R-106 Y3's 0.7065 is a POOLED ROW
    # accuracy, while the probe statistic is a DOMAIN MEAN, so both are reported here.
    rows_tr_all = [m for m, k in zip(meta, tr) if k]
    surf_test_all = None
    if te.sum():
        _f = fit_surface(rows_tr_all, [m for m, k in zip(meta, te) if k], concepts, mut=mut)
        surf_test_all = surface_accuracy(_f, np.ones(len(_f["y"]), dtype=bool))
        C.add("FLOOR-RE-DERIVED",
              "the 17-feature surface classifier of R-106 Y3 is re-fit on TRAIN and re-scored on "
              "the TEST rows of THIS run, so the bar the estimate is read against is measured on "
              "the rows analysed rather than quoted from a validation-split measurement",
              surf_test_all["n_rows"] > 0, surf_test_all["n_rows"],
              "surface row acc %.4f CI [%.4f, %.4f], domain-mean %.4f on %d test rows / %d "
              "domains; preregistered floor %s (measured on VALIDATION)"
              % (surf_test_all["acc"], surf_test_all["ci"][0], surf_test_all["ci"][1],
                 surf_test_all["domain_mean_acc"], surf_test_all["n_rows"],
                 surf_test_all["n_domains"], nf.get("accuracy")))

    # ---- the evaluation set: everything, or the arm-balanced cells ---------------------------
    cells_info = None
    va_eval, te_eval = va.copy(), te.copy()
    if mode == "arm_balanced_cells":
        rows_tr = rows_tr_all
        out_cells = {}
        for nm, msk in (("validation", va), ("test", te)):
            fit = fit_surface(rows_tr, [m for m, k in zip(meta, msk) if k], concepts, mut=mut)
            cells = simplex_cells(fit["proba"])
            keep, binfo = arm_balance(fit, cells, mut=mut)
            surf = surface_accuracy(fit, keep)
            full = np.zeros(len(meta), dtype=bool)
            full[np.where(msk)[0][keep]] = True
            out_cells[nm] = dict(stratification=SIMPLEX_STRAT_NAME, n_cells=len(cells),
                                 balance=binfo, surface=surf, mask=full,
                                 n_surface_features=fit["n_features"],
                                 n_surface_train_rows=fit["n_train"])
        va_eval, te_eval = out_cells["validation"]["mask"], out_cells["test"]["mask"]
        cells_info = {k: {kk: vv for kk, vv in v.items() if kk != "mask"}
                      for k, v in out_cells.items()}

        cnts = sorted(out_cells["test"]["balance"]["arm_counts"].values())
        C.add("ARM-BALANCE",
              "inside the analysed cells every concept arm carries the SAME number of rows -- "
              "the condition PR-050 asserted held 'by construction' and C-100 showed does not, "
              "so it is ENFORCED here and then verified",
              len(set(cnts)) == 1 and len(cnts) == len(concepts),
              int(te_eval.sum()),
              "test arm counts %s over %d rows (%.1f%% retained, %d/%d domain-cells dropped)"
              % (out_cells["test"]["balance"]["arm_counts"], te_eval.sum(),
                 100.0 * out_cells["test"]["balance"]["frac_retained"],
                 out_cells["test"]["balance"]["n_dropped"],
                 out_cells["test"]["balance"]["n_domain_cells"]))

        s = out_cells["test"]["surface"]
        C.add("SURFACE-FLOOR-VERIFIED",
              "the surface classifier is AT CHANCE (its 95%% CI covers %.4f) inside the TEST "
              "cells actually analysed -- the preregistered 0.5054 was measured on VALIDATION, "
              "and PR-052's own rule requires the floor to be re-derived per run in the SAME "
              "cells" % chance,
              s["ci"][0] <= chance <= s["ci"][1], s["n_rows"],
              "surface acc %.4f CI [%.4f, %.4f] on %d rows / %d domains (preregistered floor "
              "%.4f, measured on validation)"
              % (s["acc"], s["ci"][0], s["ci"][1], s["n_rows"], s["n_domains"],
                 nf.get("accuracy") if isinstance(nf.get("accuracy"), float) else float("nan")))
        C.add("CELLS-COVER-DOMAINS",
              "the analysed cells retain EVERY test domain; a stratum that quietly drops domains "
              "changes the population the domain-mean is over",
              len(set(dom[te_eval])) == len(set(dom[te])), int(te_eval.sum()),
              "%d of %d test domains survive the cells"
              % (len(set(dom[te_eval])), len(set(dom[te]))))

    C.add("EVAL-BIND",
          "the SELECTION set and the TEST set both bind a non-zero counted set of rows",
          bool(va_eval.sum()) and bool(te_eval.sum()), int(va_eval.sum() + te_eval.sum()),
          "selection %d rows / %d domains; test %d rows / %d domains"
          % (va_eval.sum(), len(set(dom[va_eval])), te_eval.sum(), len(set(dom[te_eval]))))

    # ---- SELECTION, ON VALIDATION ONLY -------------------------------------------------------
    sel_mask = va_eval.copy()
    if mut == "select_on_test":
        sel_mask = sel_mask | te_eval
    C.add("SELECTION-NOTEST",
          "NOT ONE test domain enters the hyper-parameter selection set. Measured FPR is 0.0467 "
          "when selection reads validation and 0.4433 when it reads test -- a 9.5x inflation, "
          "which is why this is a guard and not a convention",
          not (set(dom[sel_mask]) & set(dom[te])), int(sel_mask.sum()),
          "selection domains %d, of which test domains %d"
          % (len(set(dom[sel_mask])), len(set(dom[sel_mask]) & set(dom[te]))))

    # The scaler is fit on the TRAIN rows ONCE per layer. It depends on the features and on the
    # fixed train mask, never on a label, so it cannot differ between grid points or between
    # permutation draws -- which is what keeps the null and the observed statistic identical in
    # everything except the labels.
    std = {}
    for L in layer_grid:
        sc = StandardScaler().fit(Xs[L][tr])
        std[L] = (sc.transform(Xs[L][tr]), sc.transform(Xs[L][sel_mask]))

    order = [(L, Cv) for L in layer_grid for Cv in c_grid]
    _log(mut, "selection: %d grid points over %d train rows" % (len(order), int(tr.sum())))
    preds = Parallel(n_jobs=a.n_jobs)(
        delayed(fit_predict)(std[L][0], y[tr], std[L][1], Cv) for L, Cv in order)
    scores = {g: domain_mean(p, y[sel_mask], dom[sel_mask])[0] for g, p in zip(order, preds)}
    del std
    if mut == "inert_grid":
        scores = {g: 1.0 for g in order}
    trace = select_hparams(scores, order)
    L_sel, C_sel = trace["chosen"]
    C.add("SELECTION-NOT-INERT",
          "the validation selection surface is NOT saturated: the grid points do not all tie, so "
          "the pick is a measurement rather than a grid-order tie-break (C-070, where a surface "
          "of 1.000000 at all 36 points was reported for months as learned localisation)",
          not trace["inert"], int(sel_mask.sum()),
          "best_val_acc=%.4f n_tied=%d/%d inert=%s saturated=%s"
          % (trace["best_acc"], trace["n_tied_at_best"], trace["n_grid"],
             trace["inert"], trace["saturated"]))

    # ---- TEST, read once ---------------------------------------------------------------------
    _sc = StandardScaler().fit(Xs[L_sel][tr])
    _Xtr, _Xte = _sc.transform(Xs[L_sel][tr]), _sc.transform(Xs[L_sel][te_eval])
    _yte, _dte = y[te_eval], dom[te_eval]
    obs, per_dom = domain_mean(fit_predict(_Xtr, y[tr], _Xte, C_sel), _yte, _dte)
    mean_, tci, sd_, nd = t_interval(per_dom.values())
    bci, n_boot = domain_bootstrap_ci(per_dom.values(), n_perm, pr.require("split", "seed"))
    k = sum(1 for v in per_dom.values() if v > chance)
    n_tie = sum(1 for v in per_dom.values() if abs(v - chance) < 1e-12)
    sp, sfloor = sign_test_two_sided(k, nd)

    # ---- DOMAIN-LEVEL group permutation, never row level -------------------------------------
    rng = np.random.default_rng(pr.require("split", "seed"))
    dom_list = sorted(set(dom))
    n_cls = len(concepts)

    def _relabel(seed_i, row_level=False):
        r = np.random.default_rng(seed_i)
        y2 = y.copy()
        if row_level:
            y2 = r.permutation(y2)          # THE DEFECT, only ever reached under --mutate
        else:
            for d in dom_list:
                m = dom == d
                y2[m] = r.permutation(n_cls)[y[m]]
        return y2

    row_level = (mut == "row_level_perm")
    true_labels = (mut == "null_true_labels")

    seeds = [int(s) for s in rng.integers(0, 2 ** 31 - 1, size=n_perm)]
    # COST, MEASURED RATHER THAN ASSUMED (C-104). One fit at the selected config is timed and the
    # full cost projected before the loop starts, so a run that cannot finish is visible in its
    # first minute rather than at its wall. n_perm is never reduced to make the projection nicer.
    _t1 = time.time()
    fit_predict(_Xtr, _relabel(seeds[0], row_level)[tr], _Xte, C_sel)
    _per = time.time() - _t1
    _log(mut, "permutation: %d domain-level draws at layer %s C=%s on %d test rows; one fit took "
              "%.2fs -> projected %.1f min on %s jobs"
              % (n_perm, L_sel, C_sel, int(te_eval.sum()), _per,
                 _per * n_perm / 60.0 / max(1, (os.cpu_count() if a.n_jobs < 0 else a.n_jobs)),
                 a.n_jobs))
    ylab = (y[tr] if true_labels else _relabel(s, row_level)[tr] for s in seeds)
    null_preds = Parallel(n_jobs=a.n_jobs)(
        delayed(fit_predict)(_Xtr, yy, _Xte, C_sel) for yy in ylab)
    nulls = [domain_mean(p, _yte, _dte)[0] for p in null_preds]
    pp, pfloor, nex = group_permutation_p(obs, nulls)
    null_mean = float(np.mean(nulls))

    C.add("PERM-DOMAIN-LEVEL",
          "the null relabels concepts WITHIN each domain, so every domain keeps its own class "
          "marginals exactly and the exchangeable unit is the domain. Row-level permutation "
          "measures FPR 0.2000 against a nominal 0.05 and would print a p the design cannot "
          "support",
          all((np.bincount(_relabel(s, row_level)[dom == d], minlength=n_cls)
               == np.bincount(y[dom == d], minlength=n_cls)).all()
              for s in seeds[:25] for d in dom_list[:8]),
          len(seeds), "checked %d domains x %d draws for exact marginal preservation"
                      % (min(8, len(dom_list)), min(25, len(seeds))))
    C.add("PERM-CENTRED",
          "the permutation null is CENTRED ON CHANCE %.4f -- a null that is not centred is not a "
          "null, and the p computed against it means nothing" % chance,
          abs(null_mean - chance) <= 0.05, len(nulls),
          "null mean %.4f over %d draws (sd %.4f), chance %.4f"
          % (null_mean, len(nulls), float(np.std(nulls)), chance))

    fa = nf.get("accuracy")
    res = OrderedDict()
    res["EXPLORATORY"] = True
    res["label"] = ("EXPLORATORY -- carries NO confirmatory weight. A null here is CANNOT "
                    "ANSWER, not evidence of absence.")
    res["prereg"] = a.prereg
    res["prereg_id"] = pr.require("id")
    res["mode"] = mode
    res["mutation"] = mut
    res["contrast"] = concepts
    res["chance"] = chance
    res["alpha_not_applied"] = alpha
    res["n_rows"] = len(meta)
    res["n_domains"] = len(set(dom))
    res["n_test_domains"] = nd
    res["n_test_rows"] = int(te_eval.sum())
    res["cells"] = cells_info
    res["SELECTION_TRACE"] = trace
    res["selected_layer"], res["selected_C"] = L_sel, C_sel
    res["estimate_domain_mean_accuracy"] = obs
    res["interval_t95"] = tci
    res["interval_bootstrap95"] = bci
    res["between_domain_sd"] = sd_
    res["n_bootstrap"] = n_boot
    res["per_domain_accuracy"] = per_dom
    res["nuisance_floor"] = {**nf, "estimate": obs,
                             "estimate_minus_floor": (obs - fa) if isinstance(fa, float) else None,
                             "surface_on_ALL_test_rows": surf_test_all,
                             "surface_in_the_analysed_cells":
                                 (cells_info["test"]["surface"] if cells_info else
                                  "not applicable: PR-049 is unstratified, so the analysed rows "
                                  "ARE all the test rows")}
    res["sign_test"] = {"k": k, "n": nd, "n_exact_ties_at_chance": n_tie,
                        "p": sp, "floor": sfloor, "formatted": fmt_p(sp, sfloor)}
    res["permutation"] = {"p": pp, "floor": pfloor, "n_exceed": nex, "n_perm": n_perm,
                          "null_mean": null_mean, "formatted": fmt_p(pp, pfloor, nex)}
    res["power_as_declared"] = _power_block(pr)
    res["no_verdict"] = ("This design reports an ESTIMATE, an INTERVAL and a FLOOR. It does not "
                         "report a verdict: primary.success/negative are unavailable to it and a "
                         "null is CANNOT ANSWER.")
    res["checks"] = {k2: v for k2, v in C.rows.items()}
    res["n_checks_failed"] = C.n_fail
    res["seconds"] = round(time.time() - t0, 1)
    return res


def _log(mut, msg: str) -> None:
    """Progress, flushed. Under --mutate it is suppressed: a dozen mutation runs each narrating
    themselves buries the RED/GREEN lines that are the point of the harness."""
    if mut is None:
        print("  ... %s  [%s]" % (msg, time.strftime("%H:%M:%S")), flush=True)


def _stripped_floor(pr: Prereg) -> Prereg:
    """A copy of the preregistration with its nuisance floor removed -- the `drop_floor` mutation.
    Mutating a COPY matters: the loader verifies hashes against disk, and a mutation that edited
    the file would be a different defect than the one being demonstrated."""
    obj = json.loads(json.dumps(pr.obj))
    obj["primary"].pop("nuisance_floor", None)
    return Prereg(obj, pr.path + "::MUTANT")


def _power_block(pr: Prereg) -> dict:
    """The power the preregistration DECLARES, quoted with its provenance. `C-101` corrected
    PR-049's conjunctive power to 0.905/0.793 AFTER this file was frozen and the file was not
    amended, so both numbers travel together rather than one silently replacing the other."""
    p = pr.require("power")
    out = {"as_frozen_in_the_config": p}
    if pr.require("id") == "DCS-PR-049":
        out["superseded_by"] = ("C-101: the published 0.963/0.900 is arithmetically wrong; the "
                                "corrected conjunctive power is 0.905 at alpha=0.05 and 0.793 at "
                                "the Holm alpha this config itself declares. 0.793 < 0.80 is what "
                                "demoted this contrast to EXPLORATORY, by the DEMOTION_CONTINGENCY "
                                "written into the config before any outcome existed.")
    return out


# ==============================================================================================
# artifact hygiene
# ==============================================================================================
def assert_no_verdict(res: dict) -> None:
    blob = json.dumps(res)
    hit = [s for s in FORBIDDEN_IN_ARTIFACT if s in blob]
    if hit:
        raise RuntimeError("the artifact contains confirmatory language %s -- an exploratory "
                           "analysis must not emit a verdict" % hit)


def write_out(res: dict, out: str) -> str:
    """`C-093`: the two preregistrations name the same analyzer, and a shared output path would
    have one run destroy the other. `--out` is REQUIRED, and a file already carrying a DIFFERENT
    preregistration id is not overwritten."""
    fp = out if os.path.isabs(out) else os.path.join(REPO, out)
    if os.path.exists(fp):
        try:
            prev = json.load(open(fp)).get("prereg_id")
        except Exception:
            prev = None
        if prev and prev != res["prereg_id"]:
            raise RuntimeError("REFUSING to overwrite %s: it holds %s and this run is %s. Two "
                               "preregistrations must not share an --out path (C-093)."
                               % (out, prev, res["prereg_id"]))
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w") as f:
        json.dump(res, f, indent=2, default=str)
    return fp


def print_result(res: dict) -> None:
    nf = res["nuisance_floor"]
    fa = nf.get("accuracy")
    print("  rows=%d  domains=%d  test_domains=%d  test_rows=%d"
          % (res["n_rows"], res["n_domains"], res["n_test_domains"], res["n_test_rows"]))
    t = res["SELECTION_TRACE"]
    print("  SELECTION (validation only): layer=%s C=%s best_val_acc=%.4f n_tied=%d/%d inert=%s"
          % (res["selected_layer"], res["selected_C"], t["best_acc"], t["n_tied_at_best"],
             t["n_grid"], t["inert"]))
    if t["_warning"]:
        print("  !! %s" % t["_warning"])
    if res["cells"]:
        s = res["cells"]["test"]["surface"]
        b = res["cells"]["test"]["balance"]
        print("  CELLS (%s): %d cells, %d/%d rows retained (%.1f%%), arms %s"
              % (res["cells"]["test"]["stratification"], res["cells"]["test"]["n_cells"],
                 b["n_kept"], b["n_total"], 100 * b["frac_retained"], b["arm_counts"]))
        print("  FLOOR RE-DERIVED in the SAME test cells: surface acc %.4f CI [%.4f, %.4f] "
              "on %d rows" % (s["acc"], s["ci"][0], s["ci"][1], s["n_rows"]))
    print("  ESTIMATE domain-mean accuracy = %.4f   t95 [%.4f, %.4f]   boot95 [%.4f, %.4f]  "
          "(between-domain sd %.4f)"
          % (res["estimate_domain_mean_accuracy"], res["interval_t95"][0], res["interval_t95"][1],
             res["interval_bootstrap95"][0], res["interval_bootstrap95"][1],
             res["between_domain_sd"]))
    st = res["sign_test"]
    print("  sign test  k=%d/%d (%d exact ties at chance)  %s"
          % (st["k"], st["n"], st["n_exact_ties_at_chance"], st["formatted"]))
    pm = res["permutation"]
    print("  permutation  %s   [null mean %.4f over %d draws, chance %.4f]"
          % (pm["formatted"], pm["null_mean"], pm["n_perm"], res["chance"]))
    s = nf.get("surface_on_ALL_test_rows")
    if s:
        print("  SURFACE on ALL test rows (re-derived this run): row acc %.4f CI [%.4f, %.4f], "
              "domain-mean %.4f" % (s["acc"], s["ci"][0], s["ci"][1], s["domain_mean_acc"]))
    print("  NUISANCE FLOOR %.4f (%s)" % (fa, str(nf["source"])[:90]))
    print("  estimate %.4f vs floor %.4f -> difference %+0.4f  (NO VERDICT IS DRAWN)"
          % (res["estimate_domain_mean_accuracy"], fa, res["estimate_domain_mean_accuracy"] - fa))


def report_failures(res: dict) -> None:
    """Name the checks that failed, rather than printing a count.

    A failed check here is not automatically a broken run: `SURFACE-FLOOR-VERIFIED` failing means
    the preregistered floor did not replicate on the split being read, which is a MEASUREMENT
    about the corpus and changes the bar rather than voiding the estimate. Saying only "1 check
    failed" would leave the reader unable to tell which of those two it is.
    """
    bad = [k for k, v in res["checks"].items() if not v["ok"]]
    if not bad:
        return
    print("  CHECK(S) FAILED: %s" % ", ".join(bad), file=sys.stderr)
    for k in bad:
        print("    %s: %s" % (k, res["checks"][k]["detail"]), file=sys.stderr)
    print("  Read the estimate against the RE-DERIVED floor above, not the frozen one, and do "
          "not quote either number without this line.", file=sys.stderr)


def one_line(res: dict) -> str:
    """The estimate, its interval, its FLOOR, and the word EXPLORATORY.

    Where the analysed rows are a stratum, the floor quoted is the one RE-DERIVED on those rows,
    with the preregistered figure beside it. PR-052 preregisters 0.5054 and also preregisters the
    rule that the floor is "the measured surface accuracy in the SAME cells, verified per run" --
    so when the two disagree the per-run number is the bar, and printing only the frozen one would
    be quoting a threshold the run itself contradicts.
    """
    nf = res["nuisance_floor"]
    floor = nf["accuracy"]
    cell = nf.get("surface_in_the_analysed_cells")
    extra = ""
    if isinstance(cell, dict):
        extra = (" (re-derived on the analysed test rows: %.4f, CI [%.4f, %.4f] -- THIS is the bar)"
                 % (cell["acc"], cell["ci"][0], cell["ci"][1]))
    return ("%s %s-vs-%s: estimate %.4f, 95%% t-interval [%.4f, %.4f], bootstrap [%.4f, %.4f], "
            "preregistered nuisance floor %.4f%s -- EXPLORATORY"
            % (res["prereg_id"], res["contrast"][0], res["contrast"][1],
               res["estimate_domain_mean_accuracy"], res["interval_t95"][0],
               res["interval_t95"][1], res["interval_bootstrap95"][0],
               res["interval_bootstrap95"][1], floor, extra))


# ==============================================================================================
# mutation harness -- a check that cannot go RED is not a guard
# ==============================================================================================
#: (mutation, the check it must turn RED).  `C-095`: a mutation harness whose mutations all come
#: back GREEN is itself unfalsifiable, so each entry names the SPECIFIC check it must break.
MUTATIONS = [
    ("empty_population", "POP-BIND"),
    ("keep_excluded_domains", "EXCLUSIONS-APPLIED"),
    ("corrupt_split", "SPLIT-DISJOINT"),
    ("wrong_bank_sha", "RUN-BINDING"),
    ("forge_missing", "MISSING-ROWS"),
    ("empty_test", "BIND-TEST"),
    ("select_on_test", "SELECTION-NOTEST"),
    ("inert_grid", "SELECTION-NOT-INERT"),
    ("row_level_perm", "PERM-DOMAIN-LEVEL"),
    ("null_true_labels", "PERM-CENTRED"),
    ("drop_floor", "FLOOR-DECLARED"),
]
MUTATIONS_CELLS = [("unbalanced_subsample", "ARM-BALANCE")]


def mutate(pr: Prereg, mode: str, a) -> int:
    muts = list(MUTATIONS) + (MUTATIONS_CELLS if mode == "arm_balanced_cells" else [])
    print("=== mutation harness (%s) -- reduced grid and n_perm=%d; a check that cannot go RED "
          "is not a guard ===" % (pr.require("id"), a.mut_n_perm))
    n_red = 0
    for m, target in muts:
        C = Checks()
        try:
            check_exploratory_declared(pr, C)
            b = argparse.Namespace(**vars(a))
            b.n_perm_override = a.mut_n_perm
            run(pr, mode, b, C, mut=m)
            row = C.rows.get(target)
            red = bool(row is not None and not row["ok"])
            detail = "" if row is None else row["detail"][:100]
            if row is None:
                detail = "the check never ran"
        except (ZeroBinding, PreregError, RuntimeError, KeyError, ValueError) as e:
            row = C.rows.get(target)
            red = bool((row is not None and not row["ok"]) or row is None)
            detail = "raised %s: %s" % (type(e).__name__, str(e)[:90])
        n_red += red
        print("  %s  %-24s -> %-22s %s" % ("RED  " if red else "GREEN", m, target, detail))
    print("[mutate] %d/%d mutations went RED" % (n_red, len(muts)))
    if n_red != len(muts):
        print("  A MUTATION THAT STAYS GREEN MEANS THE CHECK CANNOT FAIL.", file=sys.stderr)
    return dict(n_red=n_red, n_mutations=len(muts), all_red=n_red == len(muts),
                targets=[t for _m, t in muts], n_perm=a.mut_n_perm)


# ==============================================================================================
def selftest() -> int:
    print("=== dcs_ts_exploratory selftest: every guard must be reachable, no data needed ===")
    cases = []

    # the imported statistics still behave as the primary's do
    p, fl, ne = group_permutation_p(0.9, [0.1] * 200)
    cases.append(("a p at the permutation floor is labelled", "FLOOR" in fmt_p(p, fl, ne)))
    ps, fs = sign_test_two_sided(23, 23)
    cases.append(("the n=23 sign-test floor is printed, not the p", fs < 1e-6))

    # intervals refuse an empty or singleton bind
    for nm, fn in (("t interval over 1 domain", lambda: t_interval([0.5])),
                   ("bootstrap over 0 domains", lambda: domain_bootstrap_ci([], 10, 0)),
                   ("Clopper-Pearson over 0 rows", lambda: clopper_pearson(0, 0))):
        try:
            fn()
            cases.append((nm + " RAISES", False))
        except ZeroBinding:
            cases.append((nm + " RAISES", True))
    m, ci, sd, n = t_interval([0.6, 0.8, 0.7, 0.9])
    cases.append(("the t interval is over DOMAINS and brackets the mean",
                  n == 4 and ci[0] < m < ci[1]))
    bci, nb = domain_bootstrap_ci([0.6, 0.8, 0.7, 0.9], 2000, 1)
    cases.append(("the bootstrap resamples domains and brackets the mean", bci[0] < m < bci[1]))

    # the simplex cells are LABEL-BLIND and partition the rows
    rng = np.random.default_rng(0)
    pr_ = rng.random((300, 1))
    proba = np.hstack([pr_, 1 - pr_])
    cells = simplex_cells(proba)
    cov = np.zeros(300, dtype=int)
    for _n, m_ in cells:
        cov += m_.astype(int)
    cases.append(("simplex cells PARTITION the rows exactly once", bool((cov == 1).all())))
    cases.append(("simplex cells are more than one cell", len(cells) > 1))
    import inspect
    cases.append(("simplex_cells takes no label argument (cells cannot be built from TEST labels)",
                  "y" not in inspect.signature(simplex_cells).parameters))

    # arm balancing really balances, and the mutation really unbalances
    fake = dict(y=np.array(["knife"] * 30 + ["gun"] * 10), classes=["gun", "knife"],
                rows=[dict(domain="d%d" % (i % 2)) for i in range(40)])
    fake["pred"] = fake["y"].copy()
    keep, info = arm_balance(fake, [("all", np.ones(40, dtype=bool))])
    cases.append(("arm_balance equalises the arms",
                  len(set(info["arm_counts"].values())) == 1))
    keep2, info2 = arm_balance(fake, [("all", np.ones(40, dtype=bool))],
                               mut="unbalanced_subsample")
    cases.append(("the unbalanced_subsample mutation really unbalances them",
                  len(set(info2["arm_counts"].values())) > 1))

    # the artifact may not carry a verdict
    try:
        assert_no_verdict({"verdict": "SUPPORTS THE CLAIM"})
        cases.append(("a confirmatory verdict in the artifact RAISES", False))
    except RuntimeError:
        cases.append(("a confirmatory verdict in the artifact RAISES", True))
    assert_no_verdict({"EXPLORATORY": True, "estimate": 0.7})
    cases.append(("a clean exploratory artifact passes", True))

    # C-093: the two preregistrations may not share an --out path
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, "shared.json")
        write_out({"prereg_id": "DCS-PR-049", "x": 1}, fp)
        try:
            write_out({"prereg_id": "DCS-PR-052", "x": 2}, fp)
            cases.append(("a shared --out path across preregistrations RAISES (C-093)", False))
        except RuntimeError:
            cases.append(("a shared --out path across preregistrations RAISES (C-093)", True))
        write_out({"prereg_id": "DCS-PR-049", "x": 3}, fp)
        cases.append(("re-running the SAME preregistration to the same path is allowed",
                      json.load(open(fp))["x"] == 3))

    # the exploratory label is read out of the config, and a confirmatory config is refused
    live049 = load_prereg("configs/dcs_ts_pr049.json", for_extraction=True)
    C = Checks()
    mode = check_exploratory_declared(live049, C)
    cases.append(("PR-049 is EXPLORATORY per its own multiplicity block",
                  mode == "unstratified" and C.rows["EXPLORATORY-DECLARED"]["ok"]))
    live052 = load_prereg("configs/dcs_ts_pr052.json", for_extraction=True)
    C2 = Checks()
    cases.append(("PR-052 is EXPLORATORY per its own multiplicity block",
                  check_exploratory_declared(live052, C2) == "arm_balanced_cells"))
    fake_pr = Prereg(json.loads(json.dumps(live049.obj)), "MUTANT")
    for f in fake_pr.obj["multiplicity"]["families"]:
        if f["name"] == "EXPLORATORY":
            f["members"] = ["something else"]
        if f["name"] == "PRIMARY":
            f["members"] = list(f["members"]) + ["DCS-PR-049: promoted"]
    try:
        check_exploratory_declared(fake_pr, Checks())
        cases.append(("a config that promotes itself out of EXPLORATORY is REFUSED", False))
    except PreregError:
        cases.append(("a config that promotes itself out of EXPLORATORY is REFUSED", True))

    # the floor must be reachable through require(), and its absence must refuse
    cases.append(("PR-049 declares a measured floor of 0.7065",
                  abs(require_floor(live049)["accuracy"] - 0.7065) < 1e-9))
    cases.append(("PR-052 declares a measured floor of 0.5054",
                  abs(require_floor(live052)["accuracy"] - 0.5054) < 1e-9))
    try:
        require_floor(_stripped_floor(live049))
        cases.append(("a preregistration without a nuisance floor is REFUSED", False))
    except PreregError:
        cases.append(("a preregistration without a nuisance floor is REFUSED", True))

    # a check that binds zero rows is a FAIL, never a PASS
    C3 = Checks()
    C3.add("VACUOUS", "claim", True, 0, "")
    cases.append(("a check binding ZERO rows is recorded as a FAIL", not C3.rows["VACUOUS"]["ok"]))

    # every mutation names a check that this file actually declares
    declared = set()
    for src in (MUTATIONS, MUTATIONS_CELLS):
        declared |= set(t for _m, t in src)
    cases.append(("every mutation targets a named check", len(declared) == 12))

    n_ok = 0
    for name, ok in cases:
        n_ok += bool(ok)
        print("  %s  %s" % ("PASS" if ok else "FAIL", name))
    print("[selftest] %d/%d guards reachable" % (n_ok, len(cases)))
    return 0 if n_ok == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg")
    ap.add_argument("--reps", default="outputs/boombness/extract_boombness")
    ap.add_argument("--out", help="REQUIRED, and DISTINCT per preregistration (C-093)")
    ap.add_argument("--tag-prefix", default="ts116m_full")
    ap.add_argument("--n-jobs", type=int, default=-1)
    ap.add_argument("--n-perm-override", type=int, default=None,
                    help="recorded in the artifact; the preregistered n_perm is the default")
    ap.add_argument("--mut-n-perm", type=int, default=30,
                    help="draws per MUTATION run. The mutations exercise guards, not the null; "
                         "the preregistered n_perm is used for the real statistic")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--reprint", metavar="RESULT.json",
                    help="re-render an artifact this script already wrote. Reads the JSON and "
                         "nothing else -- it cannot change a number, only how one is displayed, "
                         "so the test split is not re-read to fix a printing decision.")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.reprint:
        fp = a.reprint if os.path.isabs(a.reprint) else os.path.join(REPO, a.reprint)
        res = json.load(open(fp))
        if not res.get("EXPLORATORY"):
            raise RuntimeError("%s was not written by this analyzer" % a.reprint)
        print("=== %s -- EXPLORATORY (no confirmatory weight) ===" % res["prereg_id"])
        print_result(res)
        print()
        print("ONE LINE: " + one_line(res))
        report_failures(res)
        return 0
    if not a.prereg:
        ap.error("--prereg is required")
    if not a.out and not a.mutate:
        ap.error("--out is required: the two preregistrations must not share an output path "
                 "(C-093), so there is no default")

    pr = load_prereg(a.prereg, for_extraction=True)
    C = Checks()
    mode = check_exploratory_declared(pr, C)
    print("=== %s -- %s -- EXPLORATORY (no confirmatory weight) ==="
          % (pr.require("id"), pr.require("title")))
    # --mutate and the real run in ONE process when both are asked for: the representation cache
    # is process-local and a cold read of the four 1.6 GB caches off NFS costs minutes, so a
    # separate mutation invocation would pay it twice for no scientific difference.
    mh = None
    if a.mutate:
        mh = mutate(pr, mode, a)
        if not a.out:
            return 0 if mh["all_red"] else 1
        print()

    res = run(pr, mode, a, C, mut=None)
    res["mutation_harness"] = mh or "not run in this invocation"
    assert_no_verdict(res)
    fp = write_out(res, a.out)
    print()
    C.report()
    print()
    print_result(res)
    print("  checks: %d/%d PASS" % (len(C.rows) - C.n_fail, len(C.rows)))
    print("  -> %s" % fp)
    print()
    print("ONE LINE: " + one_line(res))
    report_failures(res)
    return 1 if (C.n_fail or (mh and not mh["all_red"])) else 0


if __name__ == "__main__":
    raise SystemExit(main())
