#!/usr/bin/env python
"""dcs_cell_interaction.py -- `DCS-PR-001`'s cell x intervention DiD, as CODE.

WRITTEN AND COMMITTED BEFORE ANY KO-1/KO-2 OUTCOME EXISTS. That is the only reason it is worth
anything: an interaction chosen after seeing which way the two cells went is not a test.

THE ESTIMAND (`DCS-PR-001`). Per domain d and cell X in {C, B}:

    delta_d^X = attacks(d | control arm) - attacks(d | surfacerow_demo arm)     # rows REMOVED

    DiD = paired sign test on  delta_d^C - delta_d^B  over the 38 domains

`C` = natural_doublespeak, whose final CODEWORD row is cut off from the demonstrations (KO-1).
`B` = direct_harmful, whose final CONCEPT row is cut off from the SAME matched columns (KO-2).
Per plan Sec 1.10: DiD ~ 0 with both falling => outcome E, generic context dependence;
DiD >> 0 => outcome F, a remapping-specific information path.
⛔ Neither arm alone is the result.

WHY THIS IS NOT `tsc_model_interaction.py` WITH DIFFERENT FLAGS (`DCS-PR-001a`)
------------------------------------------------------------------------------
That module REFUSES when its two factor levels cover different `prompt_id` sets, and it is right to:
for `model x intervention`, Llama and Qwen ran the SAME 380 prompts, so "paired by domain" was also
"paired by row". Here the two levels are CELLS, and `C` and `B` are DIFFERENT PROMPTS BY
CONSTRUCTION -- a natural_doublespeak prompt and a direct_harmful prompt never share a `prompt_id`.

So this analysis pairs BY DOMAIN ONLY: 38 clusters of different rows. That is STRICTLY WEAKER
pairing than the parent's, and every consumer of this output must say so. What this module asserts
instead is DOMAIN-SET identity, plus row-set identity WITHIN each cell (where the baseline and
intervened arms really are the same prompts, so the within-cell contrast stays row-paired).

The sign test, the alpha, the judge pin and the `k_informative` / attainable-floor reporting are
IMPORTED from the parent rather than restated. Two copies of a sign test are two things that drift
apart, and this project has the scars (standing rule 8: parameterize, never fork).

⚠ HEADROOM. `C` and `B` differ in baseline rate as well as in content, so the ABSOLUTE contrast
confounds "the intervention does less in cell B" with "there was less to remove". Both forms are
reported and NEITHER MAY STAND ALONE; zero-baseline domains are dropped from the normalised form
and COUNTED, never imputed.

Stdlib only. Reads scalar judge columns; never opens `gens.jsonl`.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

# ONE definition of the sign test, the alpha and the judge pin -- imported, never restated.
from tsc_model_interaction import ALPHA, PIN, load, per_domain, two_sided_sign_p  # noqa: E402

SCHEMA = "DCS_CELL_INTERACTION/1"
CELLS = ("C", "B")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    for c in CELLS:
        ap.add_argument(f"--{c}-baseline", required=True, help=f"judge dir, cell {c}, no intervention")
        ap.add_argument(f"--{c}-surfacerow", required=True,
                        help=f"judge dir, cell {c}, target_surface_row_only + demo_all")
        ap.add_argument(f"--{c}-control", action="append", required=True,
                        help="repeatable; count-matched control at the SAME scope")
    ap.add_argument("--dose", type=int, default=4)
    ap.add_argument("--tag", default="dcs_cell_interaction")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/dcs_analysis"))
    a = ap.parse_args()

    arms = {}
    for c in CELLS:
        arms[c] = {"A": load(getattr(a, f"{c}_baseline"), a.dose),
                   "ko": load(getattr(a, f"{c}_surfacerow"), a.dose),
                   "controls": [load(d, a.dose) for d in getattr(a, f"{c}_control")]}

    # ---- WITHIN a cell the arms MUST be the same rows: that contrast is row-paired and a
    # ---- different row set there would be a different experiment, not a weaker one.
    for c in CELLS:
        ref = set(arms[c]["A"])
        if not ref:
            raise SystemExit(f"REFUSING: cell {c} baseline has no rows at dose {a.dose}.")
        for name, rows in ([("ko", arms[c]["ko"])]
                           + [(f"ctrl{i + 1}", r) for i, r in enumerate(arms[c]["controls"])]):
            if set(rows) != ref:
                raise SystemExit(
                    f"REFUSING: {c}/{name} covers a different prompt_id set than {c}/baseline "
                    f"({len(set(rows) ^ ref)} symmetric difference). WITHIN a cell the contrast is "
                    f"row-paired and that requires identical rows.")
            for pid in ref:
                if rows[pid][0] != arms[c]["A"][pid][0]:
                    raise SystemExit(f"REFUSING: {c}/{name} disagrees about the domain of {pid}.")

    # ---- ACROSS cells we assert DOMAIN-set identity, NOT row identity (DCS-PR-001a). Asserting
    # ---- row identity here would be wrong -- C and B are different prompts by construction -- and
    # ---- asserting nothing would let two different domain populations be "paired" by position.
    dom_sets = {c: {d for d, _ in arms[c]["A"].values()} for c in CELLS}
    if dom_sets[CELLS[0]] != dom_sets[CELLS[1]]:
        diff = dom_sets[CELLS[0]] ^ dom_sets[CELLS[1]]
        raise SystemExit(f"REFUSING: cells cover different domain sets ({len(diff)} differ: "
                         f"{sorted(diff)[:6]}). The DiD is paired BY DOMAIN and that requires the "
                         f"same domains in both cells.")
    doms = sorted(dom_sets[CELLS[0]])
    n_rows = {c: len(arms[c]["A"]) for c in CELLS}

    results = {}
    n_ctrl = min(len(arms[c]["controls"]) for c in CELLS)
    for ci in range(n_ctrl):
        d_abs, d_norm = {}, {}
        for c in CELLS:
            ko = per_domain(arms[c]["ko"])
            ct = per_domain(arms[c]["controls"][ci])
            base = per_domain(arms[c]["A"])
            d_abs[c] = {d: ct[d] - ko[d] for d in doms}
            d_norm[c] = {d: ((ct[d] - ko[d]) / base[d]) for d in doms if base[d] > 0}
        common_norm = sorted(set(d_norm[CELLS[0]]) & set(d_norm[CELLS[1]]))
        dropped = len(doms) - len(common_norm)

        block = {}
        for scale, table, keys in (("absolute", d_abs, doms),
                                   ("normalised", d_norm, common_norm)):
            hi = sum(1 for d in keys if table["C"][d] > table["B"][d])
            lo = sum(1 for d in keys if table["C"][d] < table["B"][d])
            k = hi + lo
            p = two_sided_sign_p(min(hi, lo), k)
            floor = Fraction(2, 1 << k) if k else Fraction(1)
            block[scale] = {
                "k_domains": len(keys), "C_larger": hi, "B_larger": lo,
                "k_informative": k, "p_value": float(p),
                "attainable_p_floor": float(floor),
                "CAPABLE": bool(floor <= ALPHA),
                "total_C": sum(table["C"][d] for d in keys),
                "total_B": sum(table["B"][d] for d in keys),
            }
        block["normalised"]["domains_dropped_zero_baseline"] = dropped
        results[f"vs_control_{ci + 1}"] = block

    # Per-cell within-arm totals, so the DiD can never be read without the two effects it is built
    # from. A DiD of zero because NEITHER arm moved is a different result from a DiD of zero
    # because BOTH moved equally, and only these numbers tell them apart.
    per_cell = {}
    for c in CELLS:
        base = per_domain(arms[c]["A"])
        ko = per_domain(arms[c]["ko"])
        per_cell[c] = {
            "n_rows": n_rows[c],
            "baseline_attacks": sum(base[d] for d in doms),
            "ko_attacks": sum(ko[d] for d in doms),
            "rows_removed_vs_baseline": sum(base[d] - ko[d] for d in doms),
            "controls_attacks": [sum(per_domain(cc)[d] for d in doms) for cc in arms[c]["controls"]],
        }

    doc = {
        "schema": SCHEMA, "alpha": ALPHA, "dose": a.dose, "judge_pin": PIN,
        "k_domains": len(doms), "cells": list(CELLS), "n_rows_per_cell": n_rows,
        "estimand": ("delta_d^X = attacks(d|control) - attacks(d|surfacerow_demo); "
                     "DiD = exact paired sign test on delta^C - delta^B over domains"),
        "preregistered": "DCS-PR-001 / DCS-PR-001a, before any KO-1/KO-2 outcome existed",
        "pairing_note": ("PAIRED BY DOMAIN ONLY. C and B are different prompts by construction, so "
                         "unlike tsc_model_interaction this is NOT also row-paired across the two "
                         "levels. Within each cell the baseline-vs-intervened contrast IS "
                         "row-paired and is asserted as such."),
        "headroom_note": ("C and B differ in baseline rate, so the ABSOLUTE contrast confounds "
                          "effect size with headroom. The NORMALISED contrast is scale-free but "
                          "undefined on zero-baseline domains, which are dropped and counted."),
        "judge_band_note": ("The judge flips 13.4% of malicious_at_0.5 labels on byte-identical "
                            "text; no arm difference below 17 rows is an informative negative."),
        "per_cell": per_cell, "results": results,
    }
    os.makedirs(a.out, exist_ok=True)
    outp = os.path.join(a.out, f"{a.tag}.json")
    with open(outp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)

    print(f"[dcs] cell x intervention DiD, k_domains={len(doms)}, dose={a.dose}")
    for c in CELLS:
        pc = per_cell[c]
        print(f"  cell {c}: n={pc['n_rows']} baseline={pc['baseline_attacks']} "
              f"ko={pc['ko_attacks']} removed={pc['rows_removed_vs_baseline']} "
              f"controls={pc['controls_attacks']}")
    for name, block in results.items():
        for scale in ("absolute", "normalised"):
            b = block[scale]
            verdict = ("CELL-SPECIFIC (outcome F)" if b["CAPABLE"] and b["p_value"] < ALPHA else
                       "no detectable interaction (outcome E)" if b["CAPABLE"] else
                       "UNINFORMATIVE BY CONSTRUCTION")
            print(f"  {name:16s} {scale:11s} C_total={b['total_C']:8.3f} B_total={b['total_B']:8.3f} "
                  f"C>B {b['C_larger']:2d} B>C {b['B_larger']:2d} k_inf={b['k_informative']:2d} "
                  f"p={b['p_value']:.4e} floor={b['attainable_p_floor']:.2e} -> {verdict}")
    print(f"[dcs] -> {outp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
