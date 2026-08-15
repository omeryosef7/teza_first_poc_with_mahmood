"""analyze_d3_scope.py — aggregate the D3 intervention-scope-matched comparison.

Reads the results.csv from one or more validate_refusal_directions runs (one per
ablation scope) and tabulates, per (scope, family), the refusal-reduction the
activation attack achieves (`ablate_gain` = base_refusal − ablated_refusal), its
norm-matched random control, and the held-out projection separation. The D3
question (gap-matrix §D3): does the activation refusal-reduction collapse as the
scope narrows from all-layer/all-position (Arditi) → single-layer → single-position
(decision), i.e. toward a token attack's one-layer/one-position budget?

Pure CSV parsing — no GPU, no model text.

    python scripts/analyze_d3_scope.py --runs <dir1> <dir2> <dir3> \
        --family clearharm --out reports/D3_SCOPE_COMPARISON.json
"""
from __future__ import annotations
import argparse, csv, json, os

SCOPE_ORDER = {"all_layers": 0, "single_layer": 1, "decision": 2}
SCOPE_DESC = {
    "all_layers": "every layer / every position / every step (Arditi)",
    "single_layer": "one layer (L18) / all positions",
    "decision": "one layer (L18) / decision position only (D3 scope-matched)",
}


def read_rows(run_dir):
    p = os.path.join(run_dir, "results.csv")
    with open(p) as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--family", default="clearharm")
    ap.add_argument("--layer", default="18")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    recs = []
    for rd in args.runs:
        for r in read_rows(rd):
            if r.get("family") != args.family or str(r.get("layer")) != str(args.layer):
                continue
            recs.append({
                "scope": r["ablate_scope"],
                "run": os.path.basename(rd.rstrip("/")),
                "refusal_base": float(r["refusal_base_harmful"]),
                "refusal_ablated": float(r["refusal_ablated"]),
                "ablate_gain": float(r["ablate_gain"]),
                "ablate_gain_rand": float(r["ablate_gain_rand"]),
                "ablate_vs_rand_p": float(r.get("ablate_vs_rand_p", "nan") or "nan"),
                "separation_heldout": float(r["separation_heldout"]),
                "n_harmful": int(r["n_harmful"]),
            })
    recs.sort(key=lambda x: SCOPE_ORDER.get(x["scope"], 9))

    print(f"D3 scope comparison — family={args.family} L{args.layer}")
    print(f"{'scope':<13} {'base':>5} {'ablated':>7} {'gain':>6} {'gain_rand':>9} {'sep_ho':>7} {'n':>3}")
    for r in recs:
        print(f"{r['scope']:<13} {r['refusal_base']:>5.2f} {r['refusal_ablated']:>7.2f} "
              f"{r['ablate_gain']:>+6.2f} {r['ablate_gain_rand']:>+9.2f} "
              f"{r['separation_heldout']:>+7.3f} {r['n_harmful']:>3}")

    # verdict: does gain collapse as scope narrows?
    by_scope = {r["scope"]: r for r in recs}
    verdict = None
    if {"all_layers", "decision"} <= set(by_scope):
        g_all = by_scope["all_layers"]["ablate_gain"]
        g_dec = by_scope["decision"]["ablate_gain"]
        if g_all > 0:
            retained = g_dec / g_all if g_all else 0.0
            verdict = (f"decision scope retains {retained:.0%} of the all-layer refusal-"
                       f"reduction ({g_dec:+.2f} vs {g_all:+.2f}) — "
                       + ("the activation advantage is LARGELY SCOPE (D3 confound confirmed)"
                          if retained < 0.34 else
                          "the activation advantage substantially survives scope-matching"))
        else:
            verdict = f"all-layer gain is {g_all:+.2f} (no headroom); comparison uninformative"
        print("\nVERDICT:", verdict)

    result = {"family": args.family, "layer": args.layer, "rows": recs,
              "scope_desc": SCOPE_DESC, "verdict": verdict}
    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        json.dump(result, open(args.out, "w"), indent=2)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
