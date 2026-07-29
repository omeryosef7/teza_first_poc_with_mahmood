"""
41_aggregate_pairs.py — CAUSAL_CORE_PLAN §10 Phase F + §16.18 (S16). CPU-only.

Does the fixed-pair result GENERALIZE? Plan §15 forbids converting one pair into a general
mechanism, and §16.18 gates scale-up on the fixed-pair chain passing (it now does). This
aggregates the per-pair `controls` sweeps and asks the two questions that matter:

  1. Does `add_d_Direct` install the target reading for EVERY pair?  (the positive)
  2. Does `add_d_DS` stay inert for EVERY pair?                       (the load-bearing null)

A dissociation that holds on one pair and fails on four is a property of `carrot`↔`bomb`, not
of Doublespeak. Reporting per-pair effects side by side is the only way to tell, so this
prints the full per-pair table rather than a pooled average — pooling would let one strong
pair carry four null ones.

Also reports, per pair, whether the concept-specific arm exceeded its matched-control
distribution, since that is what makes each individual effect interpretable (§5).

Usage:
  python 41_aggregate_pairs.py --analysis outputs/pair_causal_controls_A.json \
      --analysis outputs/pair_causal_controls_B.json --out outputs/pair_generalization.json
"""
import os
import json
import argparse

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", action="append", required=True,
                    help="35_analyze_pair_causal.py output for a `controls` sweep")
    ap.add_argument("--interv-summary", action="append", default=[],
                    help="matching interv_summary.json, to recover the pair label")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pairs = []
    for i, path in enumerate(args.analysis):
        d = json.load(open(path))
        label = None
        if i < len(args.interv_summary):
            try:
                s = json.load(open(args.interv_summary[i]))
                label = f"{s['pair']['codeword']}->{s['pair']['concept']}"
            except Exception:
                pass
        label = label or os.path.basename(path)

        row = {"pair": label, "analysis": os.path.abspath(path), "windows": {}}
        for arm in ("add_d_Direct", "add_d_DS"):
            for win in ("early", "mid", "late"):
                cells = [v for v in d["per_cell"].values()
                         if v["arm"] == arm and v["group"] == win
                         and v["site"] == "codeword_all"]
                if not cells:
                    continue
                c = max(cells, key=lambda v: abs(v["effect"]))
                row["windows"][f"{arm}|{win}"] = {
                    "effect": c["effect"], "lo": c["lo"], "hi": c["hi"], "n": c["n"],
                    "significant_corrected": c.get("significant_corrected"),
                }
        # did the concept-specific arm beat its matched-control distribution?
        exceeded = {}
        for k, v in d.get("control_distribution", {}).items():
            for arm, c in v.get("concept_arms", {}).items():
                if c.get("exceeds_all_controls") and c.get("materially_nonzero"):
                    exceeded.setdefault(arm, []).append(k)
        row["arms_exceeding_all_controls"] = {a: sorted(v) for a, v in exceeded.items()}
        pairs.append(row)

    def get(p, key):
        return p["windows"].get(key, {}).get("effect")

    n = len(pairs)
    direct_ok = [p for p in pairs
                 if any((get(p, f"add_d_Direct|{w}") or 0) >= 0.05 for w in ("early", "mid", "late"))]
    ds_inert = [p for p in pairs
                if all(abs(get(p, f"add_d_DS|{w}") or 0) < 0.05 for w in ("early", "mid", "late"))]

    out = {
        "plan": "CAUSAL_CORE_PLAN §F + §16.18 (S16)",
        "n_pairs": n,
        "criterion_install": "max_window(add_d_Direct) >= 0.05",
        "criterion_inert": "all windows |add_d_DS| < 0.05",
        "n_pairs_where_d_Direct_installs": len(direct_ok),
        "n_pairs_where_d_DS_inert": len(ds_inert),
        "dissociation_holds_in_all_pairs": bool(len(direct_ok) == n and len(ds_inert) == n),
        "pairs": pairs,
        "reporting_note": ("Per-pair effects are reported side by side and NOT pooled: a "
                           "pooled mean would let one strong pair carry several null ones, "
                           "which is exactly the one-pair->general-mechanism conversion "
                           "plan §15 forbids."),
        "status": "COMPLETE",
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=1)

    print(f"{'pair':22} {'Direct.early':>13} {'Direct.mid':>11} {'Direct.late':>12} "
          f"{'DS.mid':>8} {'DS.late':>8}")
    for p in pairs:
        f = lambda k: ("  n/a" if get(p, k) is None else f"{get(p,k):+.4f}")
        print(f"{p['pair']:22} {f('add_d_Direct|early'):>13} {f('add_d_Direct|mid'):>11} "
              f"{f('add_d_Direct|late'):>12} {f('add_d_DS|mid'):>8} {f('add_d_DS|late'):>8}")
    print(f"\nd_Direct installs in {len(direct_ok)}/{n} pairs; "
          f"d_DS inert in {len(ds_inert)}/{n} pairs")
    print(f"dissociation holds in ALL pairs: {out['dissociation_holds_in_all_pairs']}")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
