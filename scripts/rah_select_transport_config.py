#!/usr/bin/env python
"""rah_select_transport_config.py -- `RAH-PR-011`'s selection rule, applied deterministically.

`RAH-R-014` established that the mapped concept IS transportable from the codeword position, but not
by the configuration Stage A froze -- `fc_probe_last` was selected on a POSITIVE CONTROL (a donor
captured at the CONCEPT token, where the concept is literally present) and is the worst of the four
forms on a CODEWORD-token donor. So the configuration for the actual question must be re-selected.

THE RULE, fixed here before it is applied, and applied to the COMMITTED level-A base-only grid
(`outputs/boombness/rah_preflight/basesweep_*.json`):

  ELIGIBLE cells are those that
    (a) pass the three-conjunct gate (level > t, uplift over the unpatched prior > t, concept beats
        codeword) at their best donor layer, AND
    (b) have at least MIN_ABOVE_BAND donor layers STRICTLY ABOVE the model's band `lo` clearing the
        gate threshold. `L > lo` is not negotiable: at or below it a query-position residual is
        BIT-IDENTICAL between the base and dpo arms (`RAH-DR-001` F2), so a cell whose signal lives
        only below the band is VACUOUS for the intervened comparison no matter how strong it looks.

  Among eligible cells, MAXIMISE the number of above-band donor layers clearing the threshold --
  ROBUSTNESS, not peak. Tie-break, in order:
    1. higher p(concept) at the best ABOVE-BAND donor layer  (never the global best, which may be
       below the band -- that is exactly Llama's `fc46` optimum at L = 4)
    2. lower receiver layer R
    3. form order as listed in `receiver_forms`

  If NO cell is eligible for a model, that model is DECLINED for this experiment. The rule decides
  it, not the result.

WHY MAXIMISE ABOVE-BAND BREADTH RATHER THAN PEAK. A single lucky layer is what `RAH-DR-001` F9
warned about when a gate argmaxes over ~1300 cells. Breadth above the band is also the property the
intervened comparison actually needs: the donor layer must be one where the arms can differ at all.

DECLARED SELECTION BIAS (`RAH-DR-001` F10). This rule selects on BASE transport. Since
Delta = base - dpo and only `base` was optimised, Delta is inflated by selection even though `dpo`
was never computed by the producing program (`grep -c intervene` on the sweep returns 0). The
mitigation is mandatory and is enforced downstream: Delta must be reported at the selected cell AND
across EVERY gate-passing cell, and the claim is scoped "on configurations where baseline transport
is established", never "the effect".

Usage:
  python scripts/rah_select_transport_config.py --out outputs/boombness/rah_stagea/rah_pr011_selection.json
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PF_DIR = os.path.join(ROOT, "outputs/boombness/rah_preflight")
SCHEMA = "RAH_PR011_SELECTION/1"

FORM_ORDER = ["id07_raw", "id07_tmpl", "fc_probe_last", "fc46"]
BAND_LO = {"meta-llama/Llama-3.1-8B-Instruct": 6, "Qwen/Qwen3-14B": 7}
GATE_T = 0.1
#: A cell must clear the threshold at this many donor layers ABOVE the band to be eligible. Three is
#: the smallest number that cannot be one lucky layer plus its two neighbours' noise.
MIN_ABOVE_BAND = 3


def above_band(cell, lo):
    return [p for p in cell["per_layer"] if p["L"] > lo]


def gate_at(cell, layer_rec, unpatched_concept):
    """The THREE CONJUNCTS evaluated at a SPECIFIC donor layer.

    `RAH-C-012`. The first version of this rule read `positive_control_ok`, which the producing
    sweep computes at the GLOBAL best donor layer -- and that layer may sit BELOW the band, where
    the arms are bit-identical. A cell could therefore qualify on the strength of a layer the
    intervened comparison can never use. The gate is now recomputed at the layer that will actually
    be used, which is the best ABOVE-BAND layer.
    """
    lvl = layer_rec["p_concept_mean"]
    cw = layer_rec["p_codeword_mean"]
    uplift = lvl - unpatched_concept
    return {"level": lvl, "uplift": uplift, "p_codeword": cw,
            "c_level": lvl > GATE_T, "c_uplift": uplift > GATE_T, "c_dominance": lvl > cw,
            "gate_ok_at_layer": bool(lvl > GATE_T and uplift > GATE_T and lvl > cw)}


def summarise(cell, lo, unpatched_concept):
    ab = above_band(cell, lo)
    clearing = [p for p in ab if p["p_concept_mean"] > GATE_T]
    best_ab = max(ab, key=lambda p: p["p_concept_mean"]) if ab else None
    g = gate_at(cell, best_ab, unpatched_concept) if best_ab else None
    return {"form": cell["form"], "R": cell["R"],
            "gate_ok_global": bool(cell["positive_control_ok"]),
            "gate_at_selected_layer": g,
            "gate_ok": bool(g and g["gate_ok_at_layer"]),
            "unpatched_p_concept": unpatched_concept,
            "global_best_L": cell["best_donor_L"],
            "global_best_p": cell["pos_ctrl_max"],
            "global_best_is_below_band": cell["best_donor_L"] <= lo,
            "n_above_band": len(ab),
            "n_above_band_clearing": len(clearing),
            "above_band_layers_clearing": [p["L"] for p in clearing],
            "best_above_band_L": best_ab["L"] if best_ab else None,
            "best_above_band_p_concept": best_ab["p_concept_mean"] if best_ab else None,
            "best_above_band_p_codeword": best_ab["p_codeword_mean"] if best_ab else None}


def select_for_model(cells, lo, concept):
    rows = [summarise(c, lo, c["unpatched_dist"][concept]) for c in cells]
    eligible = [r for r in rows
                if r["gate_ok"] and r["n_above_band_clearing"] >= MIN_ABOVE_BAND]
    if not eligible:
        return None, rows
    eligible.sort(key=lambda r: (-r["n_above_band_clearing"],
                                 -round(r["best_above_band_p_concept"] or 0.0, 6),
                                 r["R"],
                                 FORM_ORDER.index(r["form"])))
    return eligible[0], rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="outputs/boombness/rah_stagea/rah_pr011_selection.json")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(PF_DIR, "basesweep_*.json")))
    if not files:
        raise SystemExit("no basesweep_* artifacts; RAH-PR-010 must run first")
    out = {"schema": SCHEMA, "rule": __doc__.split("THE RULE")[1].split("Usage")[0].strip(),
           "gate_threshold": GATE_T, "min_above_band_clearing": MIN_ABOVE_BAND,
           "band_lo": BAND_LO, "models": {}}

    for f in files:
        d = json.load(open(f))
        model, lo = d["model"], BAND_LO[d["model"]]
        if d["donor_condition"] != "natural_doublespeak":
            raise SystemExit("REFUSING: %s has donor_condition=%r; PR-011 must be selected on the "
                             "CODEWORD-donor sweep, not on the positive control"
                             % (os.path.basename(f), d["donor_condition"]))
        win, rows = select_for_model(d["grid"], lo, d["concept"])
        out["models"][model] = {"artifact": os.path.basename(f), "band_lo": lo,
                                "n_cells": len(rows), "selected": win, "all_cells": rows,
                                "DECLINED": win is None}
        print("\n### %s   (band lo=%d, donor=%s @ codeword)" % (model, lo, d["donor_condition"]))
        print("  %-16s %3s %8s %9s %10s %9s %9s %9s" %
              ("form", "R", "gate@ab", "n_above>t", "best_ab_L", "p_conc", "uplift", "prior"))
        for r in sorted(rows, key=lambda r: (-r["n_above_band_clearing"], r["form"], r["R"])):
            flag = "" if not r["global_best_is_below_band"] else "  <-- global optimum BELOW band"
            g = r["gate_at_selected_layer"] or {}
            print("  %-16s %3d %8s %9d %10s %9s %9s %9s%s" %
                  (r["form"], r["R"], "PASS" if r["gate_ok"] else "-",
                   r["n_above_band_clearing"], r["best_above_band_L"],
                   "%.4f" % (r["best_above_band_p_concept"] or 0),
                   "%.4f" % g.get("uplift", 0), "%.4f" % r["unpatched_p_concept"], flag))
        if win is None:
            print("  => DECLINED BY THE RULE: no cell passes the three conjuncts AT ITS BEST "
                  "ABOVE-BAND LAYER with >= %d such layers clearing the threshold" % MIN_ABOVE_BAND)
        else:
            print("  => SELECTED %s R=%d, donor layer L=%d (best ABOVE band), "
                  "p_concept=%.4f p_codeword=%.4f, breadth %d layers"
                  % (win["form"], win["R"], win["best_above_band_L"],
                     win["best_above_band_p_concept"], win["best_above_band_p_codeword"],
                     win["n_above_band_clearing"]))

    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)), exist_ok=True)
    with open(os.path.join(ROOT, a.out), "w") as fh:
        json.dump(out, fh, indent=1)
    print("\n-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
