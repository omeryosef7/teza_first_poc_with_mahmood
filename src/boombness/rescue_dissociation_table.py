"""C9's table, as a COMMAND — because the phase's strongest claim had none.

WHY THIS EXISTS. Section 19-E requires that every paper-level result have one command that
regenerates its artifact, and that *"no important result should require reconstructing a method from
prose."* C9 -- the causal dissociation, the strongest claim in the phase -- violated that: its
manifest row said "join the judge dirs by prompt_id and read the `refused` field", which is prose.
C-13 had just shown what an untested prose instruction costs, so this closes the same hole one row
over.

WHAT IT ENFORCES, beyond convenience:

* **Rows and x-margin, never a bare percentage.** DR-5 measured that "% of the refusal rise removed"
  is INVERTED relative to the evidence here: the 92.3% cell is 12 rows at 1.44x margin (the weakest)
  and the 69.2% cell is 18 rows at 2.16x (the joint strongest), because the ratio divides by
  (knockout - clean) and one clean baseline is 2 rows of 160. The percentage is still emitted -- it
  is a real quantity -- but it can never appear without its row count and margin multiple beside it.
* **The control must be reported for every cell.** A rescue number without its below-band control is
  not evidence of localisation, and in all four published cells the control moved refusal by exactly
  0 rows. A cell whose control is non-zero is flagged, not silently averaged in.
* **Refusal comes from the judge row's `refused` field** (`kw_refusal`, deterministic), never from
  the LLM judge -- the distinction that makes these numbers free of session drift.

Scalar fields only; no prompt or completion text is read.

Usage
-----
    python src/boombness/rescue_dissociation_table.py \
        --cell NAME:BASELINE_JUDGE:KNOCKOUT_JUDGE:RESCUE_JUDGE:CONTROL_JUDGE [--cell ...] \
        [--n-examples 8] --tag c9
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

#: PR-3, measured from same-arm re-judge spread rather than assumed.
MARGIN_VS_BASELINE = 0.0521


def load(d):
    with open(os.path.join(d, "results.jsonl")) as fh:
        return {r["prompt_id"]: r for r in map(json.loads, fh)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", action="append", default=[],
                    metavar="NAME:BASE:KNOCK:RESCUE:CONTROL")
    ap.add_argument("--n-examples", type=int, default=None,
                    help="restrict to one dose level (C12 uses 8)")
    ap.add_argument("--tag", default="c9")
    ap.add_argument("--experiment", default="rescue_dissociation_table")
    args = ap.parse_args()

    run = common.RunDir(args.experiment, args=args, tag=args.tag)
    ledger = common.FailureLedger()
    cells = {}

    for spec in args.cell:
        parts = spec.split(":")
        if len(parts) != 5:
            raise SystemExit(f"[c9] REFUSING: --cell needs 5 colon fields, got {len(parts)}: {spec!r}")
        name, bd, kd, rd, cd = parts
        if name in cells:
            raise SystemExit(f"[c9] REFUSING: duplicate cell name {name!r}; it is the dict key.")
        A, K, R, C = load(bd), load(kd), load(rd), load(cd)
        ids = sorted(set(A) & set(K) & set(R) & set(C))
        if args.n_examples is not None:
            ids = [p for p in ids if A[p].get("n_examples") == args.n_examples]
        if not ids:
            raise SystemExit(f"[c9] REFUSING: cell {name!r} has no rows common to all four arms.")
        for p in set(A) | set(K) | set(R) | set(C):
            ledger.ok() if p in ids else ledger.fail("unpaired_prompt_id", f"{name}:{p}")

        n = len(ids)
        ref = lambda X: sum(1 for p in ids if X[p].get("refused"))  # noqa: E731
        n_clean, n_knock, n_resc, n_ctrl = ref(A), ref(K), ref(R), ref(C)
        margin_rows = MARGIN_VS_BASELINE * n
        effect_rows = n_knock - n_resc
        ctrl_rows = n_knock - n_ctrl
        rise_rows = n_knock - n_clean
        cells[name] = {
            "n": n,
            "refusal_rows": {"clean": n_clean, "knockout": n_knock,
                             "rescue": n_resc, "control": n_ctrl},
            "effect_rows": effect_rows,
            "margin_rows": round(margin_rows, 2),
            "effect_x_margin": round(effect_rows / margin_rows, 3) if margin_rows else None,
            "clears_margin": effect_rows > margin_rows,
            "control_rows_moved": ctrl_rows,
            "control_inert": ctrl_rows == 0,
            "pct_of_rise_removed": (round(100.0 * effect_rows / rise_rows, 1)
                                    if rise_rows else None),
            "PCT_CAVEAT": ("DR-5: this percentage is INVERTED relative to the evidence when the "
                           "clean baseline is near zero -- it divides by (knockout - clean). Never "
                           "quote it without effect_rows and effect_x_margin."),
            "dirs": {"baseline": bd, "knockout": kd, "rescue": rd, "control": cd},
        }

    out = {"schema": "RESCUE_DISSOCIATION_TABLE/1",
           "margin_vs_baseline": MARGIN_VS_BASELINE,
           "n_examples_filter": args.n_examples,
           "per_cell": cells,
           "n_cells_clearing_margin": sum(1 for v in cells.values() if v["clears_margin"]),
           "n_cells_control_inert": sum(1 for v in cells.values() if v["control_inert"]),
           "VERDICT": ("C9 rests on replication across cells with an inert control in each, not on "
                       "any single cell's magnitude."),
           "REFUSAL_SOURCE": "judge row `refused` == judge_boombness.kw_refusal, NOT the LLM judge"}
    path = os.path.join(run.path, "rescue_dissociation_table.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    run.finish(summary={"n_cells": len(cells),
                        "n_clearing": out["n_cells_clearing_margin"],
                        "n_control_inert": out["n_cells_control_inert"]}, ledger=ledger)
    print(f"[c9] wrote {path}")
    for k, v in cells.items():
        print(f"  {k:12s} n={v['n']:3d} effect={v['effect_rows']:3d} rows  margin={v['margin_rows']:5.1f}"
              f"  {v['effect_x_margin']:.2f}x  control={v['control_rows_moved']:2d}"
              f"  ({v['pct_of_rise_removed']}% of rise)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
