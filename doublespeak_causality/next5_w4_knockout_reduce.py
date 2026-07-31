"""
next5_w4_knockout_reduce.py — NEXT5 W4 tier-A: reduce a 36_pair_attention knockout run into a
per-group necessity map with paired bootstrap CIs + Holm, keyed on (source_set, group).

For each knocked-out group g (a layer, a head, or a head-group) and source set s, the effect is
the paired drop in the DOUBLESPEAK concept reading when attention from the query codeword to s is
blocked:  effect(sid) = p_concept_baseline(sid) - p_concept_knockout(sid, s, g).
A group/source is NECESSARY if effect CI excludes 0 (blocking it lowers the reading) AND the effect
exceeds the count-matched random_matched control (concept-specific, not generic attention loss).

Scalars only (reads p_concept floats; no prompt text). Reuse-only (stats.py). CPU.

Run: python next5_w4_knockout_reduce.py --run outputs/pair_attn_knockout_..._<jobid>
"""
import os
import sys
import json
import argparse
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stats as st

CTRL = "random_matched"


def load(run):
    p = run if run.endswith(".jsonl") else os.path.join(run, "attn_raw.jsonl")
    return [json.loads(l) for l in open(p)]


def ci_block(x, y):
    d = st.paired_bootstrap_ci(x, y, n_boot=10000, seed=0)
    out = {"n": d["n"], "effect": round(d["mean_diff"], 5), "lo": round(d["lo"], 5),
           "hi": round(d["hi"], 5), "ci_reliable": d["ci_reliable"]}
    if d["n"] >= 2:
        out["p_raw"] = round(st.permutation_test_paired(x, y, n_perm=2000, seed=0)["p"], 6)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--condition", default="DOUBLESPEAK")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rows = [r for r in load(args.run) if r.get("condition") == args.condition]
    # baseline p_concept per sid
    base = {r["sid"]: r.get("p_concept") for r in rows if r.get("granularity") == "baseline"}
    # knockout rows: (source_set, group) -> {sid: p_concept}
    ko = defaultdict(dict)
    for r in rows:
        if r.get("granularity") in (None, "baseline"):
            continue
        s, g = r.get("source_set"), r.get("group")
        if s is None or g is None:
            continue
        ko[(s, g)][r["sid"]] = r.get("p_concept")

    # per (source_set, group): paired effect = baseline - knockout over shared sids
    groups = {}
    pgrid = []
    for (s, g), sidmap in ko.items():
        sids = [sid for sid in sidmap if sid in base
                and sidmap[sid] is not None and base[sid] is not None]
        if len(sids) < 2:
            continue
        xb = [base[sid] for sid in sids]
        xk = [sidmap[sid] for sid in sids]
        blk = ci_block(xb, xk)                       # baseline - knockout (drop in reading)
        groups[f"{s}|{g}"] = {"source_set": s, "group": g, **blk}
        if "p_raw" in blk:
            pgrid.append(f"{s}|{g}")

    # concept-specificity: group effect vs the random_matched control effect at the SAME group
    ctrl_eff = {}
    for key, blk in groups.items():
        if blk["source_set"] == CTRL:
            ctrl_eff[blk["group"]] = blk["effect"]
    for key, blk in groups.items():
        c = ctrl_eff.get(blk["group"])
        blk["effect_above_random"] = (round(blk["effect"] - c, 5) if c is not None else None)

    # Holm across the group family
    if pgrid:
        keys = sorted(pgrid)
        adj = st.holm_bonferroni([groups[k]["p_raw"] for k in keys])
        for k, pa in zip(keys, adj):
            groups[k]["p_holm"] = round(float(pa), 6)
            groups[k]["significant_corrected"] = bool(pa < args.alpha and groups[k].get("ci_reliable"))

    # rank necessary (non-control) groups by effect_above_random
    ranked = sorted(
        [b for b in groups.values() if b["source_set"] != CTRL and b.get("effect_above_random") is not None],
        key=lambda b: b["effect_above_random"], reverse=True)

    res = {"run": os.path.abspath(args.run), "condition": args.condition,
           "n_groups": len(groups), "groups": groups,
           "top_necessary": [{"source_set": b["source_set"], "group": b["group"],
                              "effect": b["effect"], "effect_above_random": b["effect_above_random"],
                              "ci": [b["lo"], b["hi"]], "p_holm": b.get("p_holm"),
                              "sig": b.get("significant_corrected")} for b in ranked[:20]]}
    out = args.out or os.path.join(
        args.run if os.path.isdir(args.run) else os.path.dirname(args.run), "knockout_reduce.json")
    json.dump(res, open(out, "w"), indent=2)

    print(f"[w4-knockout] condition={args.condition} groups={len(groups)}")
    print("  top necessary (effect_above_random, non-control):")
    for b in ranked[:12]:
        print(f"    {b['source_set']:14s} {b['group']:10s} eff={b['effect']:+.4f} "
              f"above_rand={b['effect_above_random']:+.4f} [{b['lo']:+.4f},{b['hi']:+.4f}] "
              f"p_holm={b.get('p_holm')} sig={b.get('significant_corrected')}")
    print(f"[w4-knockout] -> {out}")


if __name__ == "__main__":
    main()
