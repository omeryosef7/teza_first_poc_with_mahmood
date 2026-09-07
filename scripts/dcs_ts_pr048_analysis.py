#!/usr/bin/env python3
"""FROZEN analyzer for `DCS-PR-048` (3-way) and `DCS-PR-049` (knife-vs-gun).

Checklist item X1, and the LAST blocking item before extraction.

THIS FILE IS COMMITTED BEFORE THE OUTCOME EXISTS. Mandate §21: *"The analyzer should be committed
before the outcome exists wherever practical. Do not edit a frozen analyzer to rescue an
outcome."* At the moment of writing no hidden state exists for `ts116m` — the extraction has not
been submitted, and it cannot be, because `dcs_ts_prereg.load(..., for_extraction=True)` refuses
while this file is absent. That circularity is deliberate: the analyzer must exist before the data
it will read.

EVERY THRESHOLD COMES FROM THE PREREGISTRATION, NONE FROM THIS FILE. There is not a single numeric
gate literal below. `alpha`, `n_perm`, the chance level, the grids, the split, the population
filters and the exclusions are all fetched through `Prereg.require()`, which REFUSES rather than
defaulting when a key is absent. `B-020` was exactly the failure of publishing thresholds that no
code path reads; the fix is not to copy them here but to make this file unable to run without
them.

WHAT IT DOES, in the order the preregistration fixes:

  1. load and ENFORCE the preregistration (hashes verified against disk, checklist enforced)
  2. bind the population -- cell C, the primary channel, the primary dose, minus the
     preregistered domain exclusions -- and REFUSE if it binds zero rows
  3. TRAIN on the train domains; select (layer, C) on VALIDATION ONLY, never test
  4. read TEST once, and persist SELECTION_TRACE including `inert` and `n_tied_at_best`
  5. domain-level group permutation, reporting every p NEXT TO ITS FLOOR
  6. the nulls the preregistration declares, each labelled with whether it can fail

THINGS THIS FILE REFUSES TO DO, each because of a specific past failure:
  * select on TEST                        -- measured FPR 0.4433 vs 0.0467 (A-039)
  * permute at row level                  -- measured FPR 0.2000 (A-039)
  * report a row-level p for a domain claim -- DEFF 6.22 would print 1.02e-06 for a true 0.05
  * report a bare p at the permutation floor -- the previous headline WAS the floor (C-069)
  * treat a saturated selection surface as localisation -- (C-070)
  * pool doses into one p-value
  * silently drop non-installing domains  -- mandate §15

USAGE
    python3 scripts/dcs_ts_pr048_analysis.py --prereg configs/dcs_ts_pr048.json --reps DIR
    python3 scripts/dcs_ts_pr048_analysis.py --selftest      # no data needed; proves the guards fire
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))

from dcs_ts_prereg import Prereg, PreregError, load  # noqa: E402


# --------------------------------------------------------------------------------------------
# statistics -- no thresholds live here, only estimators
# --------------------------------------------------------------------------------------------
def sign_test_two_sided(k: int, n: int) -> tuple[float, float]:
    """(p, attainable floor). The FLOOR is returned so it can be printed beside the p.

    `C-069`: the previous phase's headline p was the arithmetic floor of its own design and was
    read as a measurement. A p-value without its floor is not interpretable.
    """
    from math import comb
    if n == 0:
        raise ValueError("sign test over ZERO domains -- the statistic bound nothing")
    tot = 2.0 ** n
    p = sum(comb(n, i) for i in range(k, n + 1)) / tot
    p = min(1.0, 2.0 * p)
    floor = min(1.0, 2.0 * (1.0 / tot))
    return p, floor


def group_permutation_p(observed: float, null_stats: list[float]) -> tuple[float, float, int]:
    """(p, floor, n_exceed). Standard (1 + #exceed) / (1 + B)."""
    if not null_stats:
        raise ValueError("permutation over an EMPTY null distribution")
    b = len(null_stats)
    n_exceed = sum(1 for s in null_stats if s >= observed)
    return (1.0 + n_exceed) / (1.0 + b), 1.0 / (1.0 + b), n_exceed


def fmt_p(p: float, floor: float, n_exceed: int | None = None) -> str:
    """Never print a bare p at the floor."""
    if n_exceed == 0:
        return f"p < {floor:.3e} (FLOOR; 0 exceedances -- the design cannot resolve below this)"
    at_floor = abs(p - floor) < 1e-12
    return f"p = {p:.6g} [floor {floor:.3e}]" + ("  <-- AT THE FLOOR, not a measurement" if at_floor else "")


# --------------------------------------------------------------------------------------------
# population binding
# --------------------------------------------------------------------------------------------
def bind_population(pr: Prereg) -> dict:
    """Resolve the row filter from the preregistration. Refuses on an empty bind."""
    pop = pr.require("population")
    cell = pr.require("population", "cell")
    qk = pr.require("population", "query_kind_primary")
    dose = pr.require("population", "n_examples_primary")
    concepts = pr.require("population", "concepts")
    # D2-10 / the C-086 construction one window later: this selected whole-population exclusions
    # by testing whether the prose `scope` string CONTAINS "ENTIRE". Correct today by luck of
    # wording. A structured flag cannot drift with prose, and an exclusion that fails to declare
    # it is a refusal rather than a silent inclusion.
    excluded = set()
    for e in pop.get("preregistered_exclusions", []):
        if "whole_population" not in e:
            raise PreregError(
                f"exclusion {e.get('domain')!r} does not declare a boolean 'whole_population'. "
                f"Selecting exclusions by matching prose is exactly the C-086 defect; an "
                f"exclusion must say what it excludes in a machine-readable field.")
        if not isinstance(e["whole_population"], bool):
            raise PreregError(f"exclusion {e.get('domain')!r}: whole_population must be a boolean")
        if e["whole_population"]:
            excluded.add(e["domain"])
    spec = {
        "cell": cell, "query_kind": qk, "n_examples": dose,
        "concepts": list(concepts), "excluded_domains": sorted(excluded),
        "banks": {k: v["path"] for k, v in pr.require("population", "banks").items()},
    }
    # The C-074 shape: a filter that binds nothing, or a field that does not exist, must be loud.
    if cell != "C":
        print(f"  NOTE population cell is {cell!r}, not 'C'", file=sys.stderr)
    if not spec["concepts"]:
        raise PreregError("population.concepts is empty -- the analyzer would classify nothing")
    return spec


def load_split(pr: Prereg) -> dict:
    mpath = os.path.join(REPO, pr.require("split", "manifest"))
    m = json.load(open(mpath))
    want = pr.require("split", "manifest_sha16")
    if m.get("manifest_sha16") != want:
        raise PreregError(f"split manifest sha {m.get('manifest_sha16')} != pinned {want}")
    if m.get("field_name") != pr.require("split", "field"):
        raise PreregError("split manifest field_name disagrees with the preregistration")
    return m["assign"]


# --------------------------------------------------------------------------------------------
# selection -- validation only, and the trace is mandatory
# --------------------------------------------------------------------------------------------
def select_hparams(scores: dict, grid_order: list) -> dict:
    """Pick the best grid point on VALIDATION and record whether the surface was inert.

    `C-070`: the previous selector's surface was 1.000000 at all 36 grid points, so a strict `>`
    always returned the first element and every pick was a grid-order tie-break -- reported for
    months as learned localisation. `best_acc` was returned and every call site discarded it, so
    the ceiling was invisible in every artifact ever produced. Here the trace is part of the
    return value and the caller cannot drop it without deleting a field.
    """
    if not scores:
        raise ValueError("selection over an EMPTY grid")
    best = max(scores.values())
    tied = [g for g in grid_order if scores.get(g) == best]
    return {
        "chosen": tied[0],
        "best_acc": best,
        "n_grid": len(scores),
        "n_tied_at_best": len(tied),
        "inert": len(tied) == len(scores),
        "saturated": best >= 1.0,
        "_warning": ("SELECTION IS INERT: every grid point ties, so the pick is an artifact of grid "
                     "order and MUST NOT be described as learned localisation (C-070)"
                     if len(tied) == len(scores) else ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", default="configs/dcs_ts_pr048.json")
    ap.add_argument("--reps", help="directory of extracted representations")
    # Derived from the preregistration id, not a fixed default. Both PR-048 and PR-049 name this
    # same analyzer, and a shared default meant running the co-primary would DESTROY the primary
    # result -- while Holm needs both.
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--tag-prefix", default="ts116m_full")
    # A dress rehearsal that stops BEFORE the test split is touched. run_probe() has never
    # executed end to end on real representations, and C-091 showed the frozen file could not even
    # construct its estimator -- so the first real run is not the place to discover a runtime
    # error. This exercises binding, sha verification, cache loading, the scaler, all 36 selection
    # fits and the SELECTION_TRACE, then stops. It reads TRAIN and VALIDATION only.
    ap.add_argument("--stop-after-selection", action="store_true",
                    help="dry run: everything up to and including selection, then stop. Never reads TEST.")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.out is None:
        a.out = ("outputs/dcs_ts/" +
                 os.path.splitext(os.path.basename(a.prereg))[0].replace("dcs_ts_", "") +
                 "_result.json")

    # (1) ENFORCE. for_extraction=True is deliberate: this analyzer will not run against a
    # preregistration whose own blocking checklist is outstanding.
    pr = load(a.prereg, for_extraction=True)
    spec = bind_population(pr)
    assign = load_split(pr)
    alpha = pr.require("primary", "alpha")
    n_perm = pr.require("primary", "n_perm")
    chance = pr.require("primary", "chance")
    unit = pr.require("primary", "independence_unit")
    if unit != "domain":
        raise PreregError(f"independence_unit is {unit!r}; this analyzer only implements 'domain'")

    if not a.reps:
        print("No --reps given. The preregistration loaded and every gate is enforceable;")
        print("extraction has not been run, so there is nothing to analyse. This is not an error.")
        print(f"  population: cell={spec['cell']} channel={spec['query_kind']} "
              f"dose={spec['n_examples']} concepts={spec['concepts']}")
        print(f"  excluded:   {spec['excluded_domains']}")
        print(f"  split:      {sum(1 for v in assign.values() if v=='train')} train / "
              f"{sum(1 for v in assign.values() if v=='validation')} val / "
              f"{sum(1 for v in assign.values() if v=='test')} test")
        print(f"  gates:      alpha={alpha} n_perm={n_perm} chance={chance} unit={unit}")
        return 0

    return run_probe(pr, spec, assign, a)


# --------------------------------------------------------------------------------------------
# the probe
# --------------------------------------------------------------------------------------------
def _find_run(reps_root: str, tag: str) -> str:
    """Newest COMPLETE run directory for a tag. Complete means DONE.json, not merely newest.

    `C-051`/`C-012`: a producer that takes hits[-1] with no DONE.json filter reads a PARTIAL newer
    run while its verifier reads an older complete one, and the two silently disagree.
    """
    cands = []
    for d in sorted(os.listdir(reps_root)):
        if not d.startswith(tag + "_"):
            continue
        full = os.path.join(reps_root, d)
        if os.path.exists(os.path.join(full, "DONE.json")):
            cands.append(full)
    if not cands:
        raise PreregError(f"no COMPLETE run directory for tag {tag!r} under {reps_root} "
                          f"(a directory without DONE.json is a partial run and is not used)")
    return cands[-1]


def load_bank_rows(path: str) -> dict:
    out = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            out[r["prompt_id"]] = r
    return out


def run_probe(pr: Prereg, spec: dict, assign: dict, a) -> int:
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    import torch

    reps_root = a.reps
    layer_grid = pr.require("read_site", "layer_grid")
    c_grid = pr.require("read_site", "C_grid")
    n_perm = pr.require("primary", "n_perm")
    chance = pr.require("primary", "chance")
    concepts = spec["concepts"]
    excluded = set(spec["excluded_domains"])

    # ---- bind rows, with the bank sha VERIFIED against the preregistration -------------------
    X_by_layer = {L: [] for L in layer_grid}
    meta = []
    banks = pr.require("population", "banks")
    for bname, bpath in spec["banks"].items():
        cw, cc = bname.split("_", 1)
        if cc not in concepts:
            continue
        run = _find_run(reps_root, f"{a.tag_prefix}_{bname}")
        summ = json.load(open(os.path.join(run, "summary.json")))
        want_rows = banks[bname]["bank_rows_sha16"]
        if summ.get("bank_rows_sha16") != want_rows:
            raise PreregError(f"{bname}: the run at {run} was extracted from bank_rows_sha16 "
                              f"{summ.get('bank_rows_sha16')} but the preregistration pins "
                              f"{want_rows}. BANK BINDING FAILED -- this run measures a different "
                              f"population than the one that was frozen.")
        if summ.get("position") != pr.require("read_site", "position"):
            raise PreregError(f"{bname}: run position {summ.get('position')!r} != preregistered "
                              f"{pr.require('read_site','position')!r}")
        if summ.get("attn_implementation") != pr.require("model", "attn_impl"):
            raise PreregError(f"{bname}: run attn {summ.get('attn_implementation')!r} != "
                              f"preregistered {pr.require('model','attn_impl')!r}")
        # D2-09: sha/position/attn all pass on a 4-ROW SMOKE RUN. Completeness was never checked,
        # so a partial extraction would have been analysed as if it were the population.
        # NOTE the blanket `n_rows_captured == bank_n_rows` check that used to sit here has been
        # REMOVED, and deliberately. It was written before school_campus became a preregistered
        # whole-population exclusion, and it refused all three basket banks -- which are missing
        # exactly the 30 rows the pipeline was RIGHT to refuse (R-108). It is superseded by the
        # per-domain missing-row check below, which is strictly stronger: it refuses any missing
        # row whose domain is not excluded, and an empty cache fails it because every domain would
        # then be unexplained. Keeping both meant the blunt one vetoing the precise one.
        #
        # Found by the --stop-after-selection dress rehearsal on its FIRST run, which is exactly
        # what that mode exists for: this would otherwise have been discovered by the run that
        # reads the test split.
        # R-108: a blanket `n_failed == 0` is the wrong guard. basket_bomb failed 30 rows, and
        # ALL 30 are `school_campus` -- the C-075 `basketball` defect, where the extractor found one
        # more TOKEN occurrence of the codeword than TEXT occurrences and REFUSED rather than
        # guessing which was the codeword. That is correct behaviour, and the domain is now a
        # whole-population preregistered exclusion, so those failures are EXPLAINED.
        #
        # What must never pass is an UNEXPLAINED failure. So the guard is: every row missing from
        # the cache must belong to an excluded domain. A single failure outside them refuses.
        # This is strictly stronger than n_failed == 0 would have been on a clean run, and it does
        # not silently tolerate the case it was written for.
        n_failed = summ.get("failures", {}).get("n_failed", -1)
        if n_failed < 0:
            raise PreregError(f"{bname}: summary does not report failures.n_failed")
        if summ.get("knockout_applied") is not False:
            raise PreregError(f"{bname}: knockout_applied={summ.get('knockout_applied')!r}; the "
                              f"PR-048 population is the no-knockout baseline")
        cache = torch.load(os.path.join(run, "cache", "final_occurrence_reps.pt"),
                           map_location="cpu", weights_only=False)
        run_layers = list(cache["layers"])
        rows = load_bank_rows(os.path.join(REPO, bpath))
        unexplained = sorted({rows[pid]["domain"] for pid in rows if pid not in cache["reps"]}
                             - set(spec["excluded_domains"]))
        if unexplained:
            n_un = sum(1 for pid in rows if pid not in cache["reps"]
                       and rows[pid]["domain"] not in spec["excluded_domains"])
            raise PreregError(
                f"{bname}: {n_un} row(s) missing from the cache in {len(unexplained)} domain(s) "
                f"that are NOT preregistered exclusions: {unexplained[:5]}. An unexplained "
                f"extraction failure silently shrinks the population; refusing.")
        for pid, rep in cache["reps"].items():
            r = rows.get(pid)
            if r is None:
                continue
            if (r["cell"] != spec["cell"] or r["query_kind"] != spec["query_kind"]
                    or r["n_examples"] != spec["n_examples"] or r["domain"] in excluded):
                continue
            t = rep if hasattr(rep, "shape") else torch.as_tensor(rep)
            t = t.float()
            for L in layer_grid:
                X_by_layer[L].append(t[run_layers.index(L)].numpy())
            meta.append({"pid": pid, "bank": bname, "codeword": cw, "concept": cc,
                         "domain": r["domain"], "dsplit": assign[r["domain"]]})

    n = len(meta)
    if n == 0:
        raise PreregError("the population bound ZERO rows -- refusing to report a statistic over "
                          "an empty set (this is the C-074 shape)")
    y = np.array([concepts.index(m["concept"]) for m in meta])
    dom = np.array([m["domain"] for m in meta])
    spl = np.array([m["dsplit"] for m in meta])
    Xs = {L: np.stack(X_by_layer[L]) for L in layer_grid}

    MAX_ITER = 2000
    y_fit = y            # rebound per permutation draw; the OBSERVED pass uses the real labels
    tr, va, te = spl == "train", spl == "validation", spl == "test"
    for nm, msk in (("train", tr), ("validation", va), ("test", te)):
        if msk.sum() == 0:
            raise PreregError(f"the {nm} split bound ZERO rows")
    if set(dom[tr]) & set(dom[te]):
        raise PreregError(f"DOMAIN LEAKAGE: {len(set(dom[tr]) & set(dom[te]))} domain(s) in both "
                          f"train and test")

    # ONE estimator factory, used byte-identically for the observed statistic and for every
    # permutation draw. Two defects found by the second four-hour review live here:
    #
    #  (1) `multi_class="multinomial"` was REMOVED in sklearn 1.7 and 1.9.0 is installed, so the
    #      analyzer as frozen raised TypeError on the FIRST of 36 selection fits, after loading
    #      ~6 GB of representations. The frozen file could never have produced any outcome. The
    #      amendment is NOT behaviour-neutral for PR-049: with 2 classes the removed kwarg forced
    #      softmax, whereas the default path is binary -- so `multinomial` is now requested
    #      explicitly where sklearn still supports it and the choice is recorded in the artifact
    #      rather than left to a default that changed under us.
    #
    #  (2) the observed fit used max_iter=2000 and the permutation fit used max_iter=200. A
    #      permutation test is valid only when the LABELS are the sole difference between the
    #      observed and null pipelines. The permuted problem is strictly harder, so if the budget
    #      binds it binds on the null draws, depressing null accuracies, reducing exceedances and
    #      making p TOO SMALL. Timed at the real shape it converges in 9-14 iterations, so it
    #      probably never bound -- but "probably" is not a property, and an artifact produced
    #      under a binding budget would have looked identical to a valid one. Now one budget, and
    #      non-convergence is RECORDED rather than swallowed.
    import warnings
    from sklearn.exceptions import ConvergenceWarning
    convergence_failures = {"n": 0, "where": []}

    def _clf(C):
        return LogisticRegression(C=C, max_iter=MAX_ITER)

    def fit_score(L, C, fit_mask, eval_mask, why=""):
        sc = StandardScaler().fit(Xs[L][fit_mask])
        clf = _clf(C)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", ConvergenceWarning)
            clf.fit(sc.transform(Xs[L][fit_mask]), y_fit[fit_mask])
            if any(issubclass(x.category, ConvergenceWarning) for x in w):
                convergence_failures["n"] += 1
                if len(convergence_failures["where"]) < 5:
                    convergence_failures["where"].append(f"{why} L={L} C={C}")
        pred = clf.predict(sc.transform(Xs[L][eval_mask]))
        return pred, y[eval_mask], dom[eval_mask]

    def domain_mean_acc(pred, truth, doms):
        per = {}
        for d in sorted(set(doms)):
            m = doms == d
            per[d] = float((pred[m] == truth[m]).mean())
        return float(np.mean(list(per.values()))), per

    # ---- SELECTION ON VALIDATION ONLY --------------------------------------------------------
    scores, order = {}, []
    for L in layer_grid:
        for C in c_grid:
            pred, truth, doms = fit_score(L, C, tr, va, why="select")
            acc, _ = domain_mean_acc(pred, truth, doms)
            scores[(L, C)] = acc
            order.append((L, C))
    trace = select_hparams(scores, order)
    L_sel, C_sel = trace["chosen"]

    if getattr(a, "stop_after_selection", False):
        print(f"  SELECTION (validation only): layer={L_sel} C={C_sel} "
              f"best_val_acc={trace['best_acc']:.4f} n_tied={trace['n_tied_at_best']}/{trace['n_grid']} "
              f"inert={trace['inert']}")
        if trace["_warning"]:
            print(f"  !! {trace['_warning']}")
        print("  --stop-after-selection: TEST WAS NOT READ. Dry run complete.")
        return 0

    # ---- TEST, read once ---------------------------------------------------------------------
    pred, truth, doms = fit_score(L_sel, C_sel, tr, te, why="observed")
    obs, per_dom = domain_mean_acc(pred, truth, doms)
    k = sum(1 for v in per_dom.values() if v > chance)
    nd = len(per_dom)
    sp, sfloor = sign_test_two_sided(k, nd)

    # ---- DOMAIN-LEVEL group permutation ------------------------------------------------------
    #
    # COST, measured rather than assumed. One fit at the SELECTED config is 2.8 s (14 lbfgs
    # iterations), so 10,000 draws is ~7.8 h of fitting -- plus another ~3.4 h if the StandardScaler
    # is refit inside every draw, which it was. The dress rehearsal is what surfaced this: 36
    # selection fits took 31 minutes, and extrapolating THAT number would have implied ~140 h and
    # panicked me into cutting n_perm back toward the arithmetic floor C-069 exists to prevent.
    # The 36 were slow because the weaker-regularisation configs converge slowly; the one config
    # the permutation actually uses is fast.
    #
    # TWO SPEEDUPS, both provably label-independent, so the null and the observed statistic remain
    # byte-identical in everything except the labels (the C-092 invariant):
    #   1. the scaler is fit ONCE on the train rows -- it depends on the features and the fixed
    #      train mask, never on y, so it cannot differ between draws;
    #   2. the draws are embarrassingly parallel and are run with joblib.
    # n_perm is NOT reduced. Making the null cheaper than the observed statistic, or shrinking it
    # until p returns to its floor, are both refused.
    from joblib import Parallel, delayed
    rng = np.random.default_rng(pr.require("split", "seed"))
    dom_list = sorted(set(dom[tr]))
    _sc = StandardScaler().fit(Xs[L_sel][tr])
    _Xtr = _sc.transform(Xs[L_sel][tr])
    _Xte = _sc.transform(Xs[L_sel][te])
    _yte, _dte = y[te], dom[te]

    def _one_draw(seed_i):
        r = np.random.default_rng(seed_i)
        y2 = y.copy()
        for d in dom_list:
            m = dom == d
            y2[m] = r.permutation(len(concepts))[y[m]]
        c = LogisticRegression(C=C_sel, max_iter=MAX_ITER).fit(_Xtr, y2[tr])
        return domain_mean_acc(c.predict(_Xte), _yte, _dte)[0]

    seeds = rng.integers(0, 2**31 - 1, size=int(n_perm))
    nulls = Parallel(n_jobs=-1, verbose=0)(delayed(_one_draw)(int(s_)) for s_ in seeds)
    pp, pfloor, nex = group_permutation_p(obs, nulls)

    # THE NUISANCE FLOOR, read from the preregistration and ENFORCED (S-1 / A-043).
    # `require()` refuses if the key is absent, so a preregistration that forgets to declare a
    # floor cannot be analysed at all -- which is the only way to stop B-020 recurring a third
    # time. Chance is not the bar: a bag of surface counts already reaches the floor without
    # reading any representation, so a result between chance and the floor is NOT evidence.
    nf = pr.require("primary", "nuisance_floor")
    floor_acc = nf["accuracy"]
    clears_floor = obs > floor_acc
    sig = (pp < pr.require("primary", "alpha")) and (sp < pr.require("primary", "alpha"))
    verdict = ("SUPPORTS THE CLAIM" if (sig and clears_floor) else
               "SIGNIFICANT BUT BELOW THE NUISANCE FLOOR -- NOT EVIDENCE FOR THE CLAIM"
               if (sig and not clears_floor) else
               "NOT SIGNIFICANT")

    res = {
        "prereg": a.prereg, "n_rows": n, "n_domains": len(set(dom)),
        "n_test_domains": nd, "chance": chance,
        "SELECTION_TRACE": trace,
        "selected_layer": L_sel, "selected_C": C_sel,
        "observed_domain_mean_accuracy": obs,
        "per_domain_accuracy": per_dom,
        "estimator": {"max_iter": MAX_ITER, "sklearn_multiclass": "default softmax (lbfgs)",
                      "convergence_failures": convergence_failures},
        "nuisance_floor": {**nf, "observed": obs, "clears_floor": bool(clears_floor)},
        "verdict": verdict,
        "sign_test": {"k": k, "n": nd, "p": sp, "floor": sfloor, "formatted": fmt_p(sp, sfloor)},
        "permutation": {"p": pp, "floor": pfloor, "n_exceed": nex, "n_perm": int(n_perm),
                        "formatted": fmt_p(pp, pfloor, nex)},
    }
    os.makedirs(os.path.dirname(os.path.join(REPO, a.out)), exist_ok=True)
    with open(os.path.join(REPO, a.out), "w") as f:
        json.dump(res, f, indent=2)

    print(f"  rows={n}  domains={len(set(dom))}  test_domains={nd}")
    print(f"  SELECTION (validation only): layer={L_sel} C={C_sel} best_val_acc={trace['best_acc']:.4f} "
          f"n_tied={trace['n_tied_at_best']}/{trace['n_grid']} inert={trace['inert']}")
    if trace["_warning"]:
        print(f"  !! {trace['_warning']}")
    print(f"  OBSERVED domain-mean accuracy = {obs:.4f}  (chance {chance:.4f})")
    print(f"  sign test    k={k}/{nd}  {fmt_p(sp, sfloor)}")
    print(f"  permutation  {fmt_p(pp, pfloor, nex)}")
    print(f"  NUISANCE FLOOR {floor_acc:.4f} ({nf['source']})")
    print(f"  observed {obs:.4f} vs floor {floor_acc:.4f} -> clears_floor={clears_floor}")
    print(f"  VERDICT: {verdict}")
    print(f"  -> {a.out}")
    return 0


def selftest() -> int:
    """Prove the guards fire, with no data. Every check must be demonstrably reachable."""
    print("=== analyzer selftest: every guard must be reachable ===")
    n_red = 0
    cases = []

    # p-floor reporting
    p, fl, ne = group_permutation_p(0.9, [0.1] * 200)
    cases.append(("permutation at the floor is labelled", "FLOOR" in fmt_p(p, fl, ne)))
    p2, fl2, ne2 = group_permutation_p(0.5, [0.9] * 199 + [0.1])
    cases.append(("a non-floor p is not labelled FLOOR", "FLOOR" not in fmt_p(p2, fl2, ne2)))
    ps, fs = sign_test_two_sided(6, 6)
    cases.append(("sign test n=6 floor is 0.03125", abs(fs - 0.03125) < 1e-12))
    ps23, fs23 = sign_test_two_sided(23, 23)
    cases.append(("sign test n=23 floor is far below 0.03125", fs23 < 1e-6))

    # empty binds must raise, never return a number
    for name, fn in [("sign test over 0 domains", lambda: sign_test_two_sided(0, 0)),
                     ("permutation over an empty null", lambda: group_permutation_p(1.0, [])),
                     ("selection over an empty grid", lambda: select_hparams({}, []))]:
        try:
            fn()
            cases.append((name + " RAISES", False))
        except (ValueError, ZeroDivisionError):
            cases.append((name + " RAISES", True))

    # the C-070 inert-selection detector
    inert = select_hparams({(6, 0.01): 1.0, (7, 0.01): 1.0, (8, 0.01): 1.0}, [(6, 0.01), (7, 0.01), (8, 0.01)])
    cases.append(("saturated surface flagged inert", inert["inert"] and inert["saturated"]
                  and "MUST NOT" in inert["_warning"]))
    real = select_hparams({(6, 0.01): 0.6, (7, 0.01): 0.8, (8, 0.01): 0.7}, [(6, 0.01), (7, 0.01), (8, 0.01)])
    cases.append(("a genuine surface is NOT flagged inert",
                  (not real["inert"]) and real["chosen"] == (7, 0.01) and real["_warning"] == ""))

    # the preregistration refusals, exercised through the real loader
    # The extraction refusal must be tested on a SYNTHETIC open blocker, not on the live config.
    # The first version asserted that the real config refuses -- true when written, and it went
    # stale the moment the checklist was legitimately completed. A guard test whose expected
    # answer changes as the project progresses tests the project, not the guard.
    from dcs_ts_prereg import validate as _validate
    _live = json.load(open(os.path.join(REPO, "configs/dcs_ts_pr048.json")))
    _open = json.loads(json.dumps(_live))
    _open["pre_extraction_checklist"].append(
        {"id": "SYNTH", "item": "synthetic open blocker", "blocking": True, "done": False})
    cases.append(("for_extraction refuses an OPEN blocker",
                  any("SYNTH" in e for e in _validate(_open, "SYNTH", for_extraction=True))))
    cases.append(("for_extraction accepts the live config now that the checklist is closed",
                  not _validate(_live, "LIVE", for_extraction=True)))
    _mal = json.loads(json.dumps(_live))
    _mal["pre_extraction_checklist"][0].pop("done", None)
    cases.append(("a checklist item missing its booleans refuses",
                  any("boolean" in e for e in _validate(_mal, "MAL", for_extraction=True))))
    try:
        load("configs/does_not_exist.json")
        cases.append(("a missing preregistration refuses", False))
    except PreregError:
        cases.append(("a missing preregistration refuses", True))

    for name, ok in cases:
        n_red += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"[selftest] {n_red}/{len(cases)} guards reachable")
    return 0 if n_red == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
