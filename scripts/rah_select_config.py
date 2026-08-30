#!/usr/bin/env python
"""rah_select_config.py -- apply `RAH-PR-009`'s selection rule to the Stage-A grid, deterministically.

`RAH-DR-001` F10 required that the Stage-A selection be *auditable after the fact*: a pure,
deterministic function with a written tie-break, run over a committed grid, so a reviewer can re-run
it and assert equality with the frozen configuration. This is that function.

THE RULE, as registered in `RAH-PR-009` before the level-A runs existed:

    Choose the (form, R) that maximises the MINIMUM uplift across all level-A banks and both models,
    subject to the three-conjunct gate passing on every one of them.
    Tie-break, in order: lower R -> broader donor-layer support above the intervention band ->
    form order as listed.

ONE FORCED CLARIFICATION, recorded rather than silently applied. The rule says "(form, R)", but R is
NOT commensurable across models: Llama has 32 blocks and Qwen3 has 40, and the grid was built as
`int(n_layers * f)` for f in (0.125, 0.25, 0.5, 0.75) plus `n_layers - 4`. The shared axis is
therefore the DEPTH FRACTION, and the rule is applied on it. This is not a change of rule -- the
design already parameterised R by fraction -- but it is an interpretation, so it is written down.

LEVEL-A ONLY. `RAH-R-008` recorded that the GO/NO-GO pre-flight chose R while looking at a level-B
population, and bound the freeze to re-derive it on level-A. This script therefore reads ONLY the
`sA_*` (level-A) artifacts. The level-B pre-flight files are excluded by the glob and by an explicit
assertion, so a stray file cannot leak into the selection.

DONOR-SET NOTE (`RAH-R-009`). `direct_harmful` carries the CONCEPT surface and never the codeword, so
`carrot_bomb` and `basket_bomb` share byte-identical donors. Level-A supplies TWO distinct donor sets
(bomb, knife), not three. The minimum is therefore reported BOTH over banks and over distinct
concepts, and they must agree on the winner or the disagreement is surfaced.

Usage:
  python scripts/rah_select_config.py --out outputs/boombness/rah_stagea/rah_stagea_selection.json
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PF_DIR = os.path.join(ROOT, "outputs/boombness/rah_preflight")
SCHEMA = "RAH_STAGEA_SELECTION/1"

#: Form order as listed in `receiver_forms` -- the final tie-break.
FORM_ORDER = ["id07_raw", "id07_tmpl", "fc_probe_last", "fc46"]

#: Model -> first knockout band layer `lo`. Donor layers must satisfy L > lo or the arms are
#: bit-identical (`RAH-DR-001` F2), so "broad support" is counted only above it.
BAND_LO = {"meta-llama/Llama-3.1-8B-Instruct": 6, "Qwen/Qwen3-14B": 7}

GATE_T = 0.1


def depth_fraction(R, n_layers):
    """Round to the grid's own construction so 4/32 and 5/40 collide on 0.125."""
    return round(R / n_layers, 3)


def load_level_a():
    files = sorted(glob.glob(os.path.join(PF_DIR, "sA_*.json")))
    if not files:
        raise SystemExit("no level-A (sA_*) artifacts found")
    runs = []
    for f in files:
        d = json.load(open(f))
        bank = os.path.basename(d["bank"])
        # Hard refusal: a level-B bank must never enter the selection.
        if "rbd" in bank:
            raise SystemExit("REFUSING: level-B bank %r found in a level-A selection file %r"
                             % (bank, os.path.basename(f)))
        runs.append({"file": os.path.basename(f), "model": d["model"], "bank": bank,
                     "concept": d["concept"], "codeword": d["codeword"],
                     "n_layers": d["n_layers"], "grid": d["grid"]})
    return runs


def support_above_band(rec, lo):
    """How many donor layers ABOVE the band clear the gate. The second tie-break."""
    return sum(1 for p in rec["per_layer"] if p["L"] > lo and p["p_concept_mean"] > GATE_T)


def select(runs):
    """Return (winner, table). Pure: same input -> same output, no randomness, no clock."""
    cells = {}
    for r in runs:
        lo = BAND_LO[r["model"]]
        for g in r["grid"]:
            key = (g["form"], depth_fraction(g["R"], r["n_layers"]))
            cells.setdefault(key, []).append({
                "file": r["file"], "model": r["model"], "bank": r["bank"],
                "concept": r["concept"], "R": g["R"],
                "uplift": g["uplift_over_unpatched"], "ok": g["positive_control_ok"],
                "p_concept": g["pos_ctrl_max"], "p_codeword": g["p_codeword_at_best"],
                "support_above_band": support_above_band(g, lo)})

    table = []
    n_runs = len(runs)
    for (form, frac), obs in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        if len(obs) != n_runs:
            continue                       # not measured on every run -> not eligible
        all_ok = all(o["ok"] for o in obs)
        min_up = min(o["uplift"] for o in obs)
        # minimum over DISTINCT CONCEPTS as well (RAH-R-009: bomb banks share donors)
        by_concept = {}
        for o in obs:
            by_concept.setdefault(o["concept"], []).append(o["uplift"])
        min_up_concept = min(min(v) for v in by_concept.values())
        table.append({"form": form, "depth_fraction": frac,
                      "R_by_model": {o["model"]: o["R"] for o in obs},
                      "gate_passes_everywhere": all_ok,
                      "min_uplift_over_runs": min_up,
                      "min_uplift_over_concepts": min_up_concept,
                      "n_distinct_concepts": len(by_concept),
                      "min_support_above_band": min(o["support_above_band"] for o in obs),
                      "per_run": obs})

    eligible = [t for t in table if t["gate_passes_everywhere"]]
    if not eligible:
        return None, table
    # THE RULE: max min-uplift; tie-break lower depth fraction, then broader support, then form order.
    eligible.sort(key=lambda t: (-round(t["min_uplift_over_runs"], 6),
                                 t["depth_fraction"],
                                 -t["min_support_above_band"],
                                 FORM_ORDER.index(t["form"])))
    return eligible[0], table


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="outputs/boombness/rah_stagea/rah_stagea_selection.json")
    a = ap.parse_args()
    runs = load_level_a()
    print("LEVEL-A runs entering the selection (%d):" % len(runs))
    for r in runs:
        print("   %-42s %-32s %s<->%s  nL=%d"
              % (r["file"], r["model"], r["codeword"], r["concept"], r["n_layers"]))
    winner, table = select(runs)

    print("\nEligible cells (gate passes on EVERY run), ranked by the registered rule:")
    print("%-16s %6s %-22s %11s %11s %8s" %
          ("form", "depth", "R by model", "min_uplift", "min/concept", "support"))
    for t in sorted([t for t in table if t["gate_passes_everywhere"]],
                    key=lambda t: -t["min_uplift_over_runs"]):
        rs = "/".join(str(v) for v in t["R_by_model"].values())
        print("%-16s %6.3f %-22s %11.4f %11.4f %8d" %
              (t["form"], t["depth_fraction"], rs, t["min_uplift_over_runs"],
               t["min_uplift_over_concepts"], t["min_support_above_band"]))

    print("\nRejected cells (gate fails on at least one run): %d"
          % sum(1 for t in table if not t["gate_passes_everywhere"]))

    if winner is None:
        print("\nNO CELL PASSES THE GATE ON EVERY LEVEL-A RUN -- selection refuses.")
        return 1
    print("\nSELECTED  form=%s  depth_fraction=%.3f  R_by_model=%s"
          % (winner["form"], winner["depth_fraction"], winner["R_by_model"]))
    print("          min uplift over runs     = %.4f" % winner["min_uplift_over_runs"])
    print("          min uplift over concepts = %.4f (%d distinct concepts)"
          % (winner["min_uplift_over_concepts"], winner["n_distinct_concepts"]))
    print("          min donor layers above band clearing the gate = %d"
          % winner["min_support_above_band"])

    out = {"schema": SCHEMA, "rule": "RAH-PR-009: max over cells of the MIN uplift across all "
                                     "level-A banks and both models, subject to the three-conjunct "
                                     "gate passing on every one; tie-break lower depth fraction, "
                                     "then broader donor support above the band, then form order",
           "clarification": "R is not commensurable across models (32 vs 40 blocks); the shared "
                            "axis is the DEPTH FRACTION and the rule is applied on it",
           "level_a_only": True, "band_lo": BAND_LO, "gate_threshold": GATE_T,
           "runs": [{k: r[k] for k in ("file", "model", "bank", "concept", "codeword", "n_layers")}
                    for r in runs],
           "selected": winner, "full_table": table}
    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)), exist_ok=True)
    with open(os.path.join(ROOT, a.out), "w") as f:
        json.dump(out, f, indent=1)
    print("\n-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
