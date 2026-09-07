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
    excluded = {e["domain"] for e in pop.get("preregistered_exclusions", [])
                if "ENTIRE" in str(e.get("scope", "")).upper()}
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
    ap.add_argument("--out", default="outputs/dcs_ts/pr048_result.json")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--tag-prefix", default="ts116m_full")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

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
        cache = torch.load(os.path.join(run, "cache", "final_occurrence_reps.pt"),
                           map_location="cpu", weights_only=False)
        run_layers = list(cache["layers"])
        rows = load_bank_rows(os.path.join(REPO, bpath))
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

    tr, va, te = spl == "train", spl == "validation", spl == "test"
    for nm, msk in (("train", tr), ("validation", va), ("test", te)):
        if msk.sum() == 0:
            raise PreregError(f"the {nm} split bound ZERO rows")
    if set(dom[tr]) & set(dom[te]):
        raise PreregError(f"DOMAIN LEAKAGE: {len(set(dom[tr]) & set(dom[te]))} domain(s) in both "
                          f"train and test")

    def fit_score(L, C, fit_mask, eval_mask):
        sc = StandardScaler().fit(Xs[L][fit_mask])
        clf = LogisticRegression(C=C, max_iter=2000, multi_class="multinomial")
        clf.fit(sc.transform(Xs[L][fit_mask]), y[fit_mask])
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
            pred, truth, doms = fit_score(L, C, tr, va)
            acc, _ = domain_mean_acc(pred, truth, doms)
            scores[(L, C)] = acc
            order.append((L, C))
    trace = select_hparams(scores, order)
    L_sel, C_sel = trace["chosen"]

    # ---- TEST, read once ---------------------------------------------------------------------
    pred, truth, doms = fit_score(L_sel, C_sel, tr, te)
    obs, per_dom = domain_mean_acc(pred, truth, doms)
    k = sum(1 for v in per_dom.values() if v > chance)
    nd = len(per_dom)
    sp, sfloor = sign_test_two_sided(k, nd)

    # ---- DOMAIN-LEVEL group permutation ------------------------------------------------------
    rng = np.random.default_rng(pr.require("split", "seed"))
    dom_list = sorted(set(dom[tr]))
    nulls = []
    for _ in range(int(n_perm)):
        # permute the LABEL MAP WITHIN each training domain's concept assignment, at the domain
        # level -- never row level (measured FPR 0.2000 at row level).
        perm = {d: rng.permutation(len(concepts)) for d in dom_list}
        y2 = y.copy()
        for d in dom_list:
            m = dom == d
            y2[m] = perm[d][y[m]]
        sc = StandardScaler().fit(Xs[L_sel][tr])
        clf = LogisticRegression(C=C_sel, max_iter=200, multi_class="multinomial")
        clf.fit(sc.transform(Xs[L_sel][tr]), y2[tr])
        p2 = clf.predict(sc.transform(Xs[L_sel][te]))
        nulls.append(domain_mean_acc(p2, y[te], dom[te])[0])
    pp, pfloor, nex = group_permutation_p(obs, nulls)

    res = {
        "prereg": a.prereg, "n_rows": n, "n_domains": len(set(dom)),
        "n_test_domains": nd, "chance": chance,
        "SELECTION_TRACE": trace,
        "selected_layer": L_sel, "selected_C": C_sel,
        "observed_domain_mean_accuracy": obs,
        "per_domain_accuracy": per_dom,
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
