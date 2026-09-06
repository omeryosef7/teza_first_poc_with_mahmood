#!/usr/bin/env python3
"""DCS-PR-045 — re-read gate `R6` and §13 ABOVE the structurally degenerate layer.

FROZEN BEFORE ITS NUMBERS, per §70. ⛔ NO p-VALUE on anything here: §67.3 spent `PR-040`'s single
significance test, and nothing since has changed that. Everything below is DESCRIPTIVE.

WHY THE GRID CHANGES (§69.2, `C-068`). All six of `PR-044`'s folds picked `L = 6`, which is the FIRST
LAYER OF THE KNOCKOUT BAND. At the band's first layer no lower layer has been perturbed, so the read
row's hidden state is a function of unperturbed inputs masked by ITS OWN query row -- and
`legacy_all_query` and `target_surface_row_only` block exactly the same keys on that row. The two
scopes are therefore PROVABLY IDENTICAL at the read site at layer 6, for any prompt, before any data
exists. Measured and confirmed: max abs elementwise difference 0.000e+00 over all 2520 shared rows.

⛔ Excluding layer 6 is therefore a STRUCTURAL exclusion derivable from the band definition, NOT a
post-hoc layer choice. It is applied as ONE uniform rule -- to both arms, to the third `ko_on` arm,
to SELECTION, and to every cell -- with no outcome consulted:

    LAYERS_PR045 = [L for L in layers if L > min(BAND)]        # -> 7..14

DECLARED BARS (§70.3), executable, fixed before the run:
  * VOID   if the restricted grid costs the baseline more than 0.10 absolute vs the L=6 baseline.
  * BUG    if `ko1`'s drop EXCEEDS `ko_on`'s on the same grid -- `KO-1` blocks a strict subset of
           `KO-legacy`'s cells at every layer, so a larger drop is incoherent, not a finding.
  * §13b is expected to stay at CEILING; if it does it is CANNOT ANSWER again, never a null.

REUSE: population builder, §28.1 exclusion, cache loader, select/fit from
`dcs_verify_pr035_primary`; run resolution, per-class bank binding and the ABORTED refusal from
`dcs_pr044_analysis`.
"""
from __future__ import annotations

import argparse, json, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dcs_verify_pr035_primary as vp          # noqa: E402
import dcs_pr044_analysis as p44               # noqa: E402

CLASSES = vp.CLASSES
CHANCE = 1.0 / len(CLASSES)
BAND_MIN = 6                                    # --band 6-14, the value the arms were run with
VOID_BASELINE_COST = 0.10                       # §70.3
# C-070 (M-3): §70.3 worded the BUG bar against R-093's L=6 drop (+0.0482). That is the WRONG
# comparator -- R-093 lives on the layer this grid excludes. The faithful reading of the stated
# REASON ("KO-1 blocks a strict subset of KO-legacy's cells at every layer") compares the two arms
# ON THIS GRID, which is what is implemented and what §71.1 reports. Kept for the record:
R093_DROP_AT_L6 = 0.04824561403508776          # NOT the bar; the L=6 whole-query drop, for context


def loo_on_grid(rows, sel_rows, layers, grid):
    """`vp.loo` with an explicit (layers, C) grid -- selection and fit both restricted."""
    return vp.loo(rows, sel_rows, layers, CLASSES, grid=grid)


def readout(name, off_pool, ko_pool, sel_pool, layers, grid, res, what):
    TR = [r for c in CLASSES for r in off_pool[c]]
    TE = [r for c in CLASSES for r in ko_pool[c]]
    SEL = [r for c in CLASSES for r in sel_pool[c]]
    for cc in CLASSES:
        if {r["prompt_id"] for r in off_pool[cc]} != {r["prompt_id"] for r in ko_pool[cc]}:
            res["void"].append(f"{name}: population differs between arms for {cc}")
            return None
    base, picks = loo_on_grid(TR, SEL, layers, grid)
    ko = {}
    for d in sorted({r["domain"] for r in TE}):
        tr = [r for r in TR if r["domain"] != d]
        te = [r for r in TE if r["domain"] == d]
        if d not in picks or not tr or not te:
            continue
        L, C = picks[d]
        acc = vp.fit(tr, te, L, layers, C, CLASSES)
        if acc is not None:
            ko[d] = acc
    if not base or not ko:
        res["void"].append(f"{name}: no fold produced an accuracy")
        return None
    doms = sorted(set(base) & set(ko))
    drop = {d: base[d] - ko[d] for d in doms}
    ab, ak = float(np.mean([base[d] for d in doms])), float(np.mean([ko[d] for d in doms]))
    avail = ab - CHANCE
    out = dict(what=what, n_rows_per_class={cc: len(off_pool[cc]) for cc in CLASSES},
               baseline_per_domain=base, knockout_per_domain=ko, drop_per_domain=drop,
               baseline=ab, knockout=ak, mean_drop=float(np.mean(list(drop.values()))),
               n_positive=int(sum(1 for v in drop.values() if v > 0)), n_domains=len(doms),
               frac_of_available=(ab - ak) / avail if avail > 0 else None,
               picks={d: dict(layer=int(L), C=float(C)) for d, (L, C) in picks.items()},
               NOTE="DESCRIPTIVE, NO p-VALUE (§67.3/§70.3).")
    res[name] = out
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_pr045.json")
    a = ap.parse_args()
    res = dict(preregistration="DCS-PR-045 (§70)", chance=CHANCE, independence_unit="domain",
               note="Layer 6 excluded STRUCTURALLY: it is the band's first layer, where the two "
                    "knockout scopes are provably identical at the read row (C-068 §69.2). One "
                    "uniform rule, both arms, selection included. No p-values anywhere.",
               void=[])

    offC, layers = p44.load("off", ("C",), res)
    offB, l2 = p44.load("off", ("B",), res)
    ko1C, l3 = p44.load("ko1", ("C",), res)
    ko1B, l4 = p44.load("ko1", ("B",), res)
    onC, l5 = p44.load("on", ("C",), res)
    if res["void"]:
        res["verdict"] = "VOID — " + "; ".join(res["void"])
        return _write(res, a.out)
    if not (layers == l2 == l3 == l4 == l5):
        res["verdict"] = "VOID — layer lists differ across arms"
        return _write(res, a.out)

    # C-070 (CR-1): the cell-B selection surface is 1.000000 at ALL 36 grid points, so `select()`
    # returns the FIRST grid element and no maximisation occurs. That makes "layers 7-14"
    # operationally "layer 7". Persist the evidence so this is never again invisible in an artifact.
    res["selection_is_inert_CR1"] = dict(
        measured="cell-B LOO accuracy = 1.000000 at 36/36 (layer, C) grid points",
        consequence="select() returns the first grid element; the pick is a TIE-BREAK, not a "
                    "maximisation. The layers-7-14 grid resolves to layer 7.",
        structural_justification_unaffected="C-068's layer-6 degeneracy is proven from the band "
                    "definition and holds however the layer came to be picked.")
    keep = [L for L in layers if L > BAND_MIN]
    res["layers_all"], res["layers_pr045"] = list(layers), keep
    if len(keep) != len(layers) - 1:
        res["verdict"] = f"VOID — the restricted grid is {keep}, not the band minus its first layer"
        return _write(res, a.out)
    grid = (tuple(keep), vp.C_GRID)

    readout("R6b_codeword_row", offC, ko1C, offB, layers, grid, res,
            "KO-1 (surface-row-only) vs ko_off, read at the CODEWORD, layers 7-14.")
    readout("R6b_wholequery_ref", offC, onC, offB, layers, grid, res,
            "KO-legacy (whole-query) vs ko_off, SAME grid -- the denominator of the ratio.")
    readout("S13b_concept_row", offB, ko1B, offC, layers, grid, res,
            "KO-2 (surface-row-only) vs ko_off, read at the EXPLICIT CONCEPT, layers 7-14.")

    r6, ref = res.get("R6b_codeword_row"), res.get("R6b_wholequery_ref")
    if r6 and ref:
        res["ratio_ko1_over_kolegacy"] = dict(
            value=(r6["mean_drop"] / ref["mean_drop"]) if ref["mean_drop"] else None,
            reference_drop_at_L6_NOT_THE_BAR=R093_DROP_AT_L6,
            note="§70.3: DESCRIPTIVE, no bar attached, no verdict turns on it. It says what share "
                 "of the whole-query effect the codeword's OWN row accounts for, at layers where "
                 "the two scopes actually differ.")
        # C-070 (M-1): `if ref["mean_drop"] and ...` skipped the bar entirely when the reference
        # drop was exactly 0.0 -- realistic on a 1/114 grid, and §13b's IS exactly 0.0. A KO-1 drop
        # of +0.10 against a KO-legacy drop of 0.0 is flagrantly incoherent and printed clean.
        if ref["mean_drop"] is not None and r6["mean_drop"] > ref["mean_drop"] + 1e-12:
            res["void"].append("BUG SIGNAL: KO-1's drop exceeds KO-legacy's on the same grid, but "
                               "KO-1 blocks a STRICT SUBSET of KO-legacy's cells at every layer. "
                               "Re-audit the arms; this is not a finding (§70.3).")

    # §70.3 VOID bar: does the restricted grid destroy the probe?
    L6_BASE = 0.7529239766081872                # PR-044's ko_off baseline at L=6, cell C
    if r6 and (L6_BASE - r6["baseline"]) > VOID_BASELINE_COST:
        res["void"].append(f"VOID — the restricted grid costs the baseline "
                           f"{L6_BASE - r6['baseline']:.4f} > {VOID_BASELINE_COST} (§70.3).")

    s13 = res.get("S13b_concept_row")
    if s13 and s13["baseline"] >= 1.0 - 1e-12:
        res["S13b_verdict"] = ("CANNOT ANSWER — the readout is at CEILING (baseline 1.0000), so the "
                               "available range is zero. NOT a null (§70.3).")
    elif s13:
        res["S13b_verdict"] = ("DESCRIPTIVE — the ceiling lifted on the restricted grid; the drop "
                               "below is reported with no p-value.")

    if res["void"]:
        res["verdict"] = "VOID — " + "; ".join(res["void"])
    else:
        res["verdict"] = ("REPORTED DESCRIPTIVELY (§70.3). No p-value is attached to any block. "
                          "⛔ Gate R6 remains CANNOT ANSWER: nothing here is a confirmatory test, "
                          "and the ratio is descriptive with no bar attached to it.")
    return _write(res, a.out)


def _write(res, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1, default=str)
    print(f"[write] {out}\n")
    print(f"grid: layers {res.get('layers_pr045')} (from {res.get('layers_all')}), "
          f"C {list(vp.C_GRID)}\n")
    for v in res.get("void", []):
        print(f"  VOID/BUG: {v}")
    for name in ("R6b_codeword_row", "R6b_wholequery_ref", "S13b_concept_row"):
        o = res.get(name)
        if not o:
            continue
        print(f"{name} — {o['what']}")
        print(f"  rows/class {o['n_rows_per_class']}")
        print(f"  baseline {o['baseline']:.4f}  ->  knockout {o['knockout']:.4f}   "
              f"chance {CHANCE:.4f}")
        fa = o['frac_of_available']
        print(f"  mean drop {o['mean_drop']:+.4f}  positive in {o['n_positive']}/{o['n_domains']}"
              + (f"   = {fa:.1%} of the available drop" if fa is not None else ""))
        print("  per-domain drop: " + ", ".join(f"{d}={v:+.3f}"
                                                for d, v in sorted(o['drop_per_domain'].items())))
        print("  picks: " + ", ".join(f"{d}=L{p['layer']}/C{p['C']:g}"
                                      for d, p in sorted(o['picks'].items())))
        print(f"  ⛔ {o['NOTE']}\n")
    r = res.get("ratio_ko1_over_kolegacy")
    if r and r.get("value") is not None:
        print(f"RATIO KO-1 / KO-legacy on layers 7-14: {r['value']:.3f}   ⛔ descriptive only\n")
    if res.get("S13b_verdict"):
        print(f"§13b: {res['S13b_verdict']}\n")
    print(f"VERDICT: {res['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
