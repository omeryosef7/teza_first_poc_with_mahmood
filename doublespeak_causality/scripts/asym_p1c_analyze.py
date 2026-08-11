#!/usr/bin/env python3
"""ASYMMETRY SPRINT — PHASE 1c analysis (CPU): plan §19.1(a-d) + §19.2 + defect-D2 check.

Consumes `asym_p1c_mech_validity_ext.py`'s per-prompt `projections.jsonl` and answers:

  §19.1(a) SEED REPLICATION   Is "the final refusal suffix lowers the held-out refusal
        signal LESS than a norm-matched random suffix" (the seed-42 Q5 result) stable at
        seeds 43 and 44, or does it flip with the ASR sign flips?
  §19.1(b) ABSOLUTE + SHAPE   Drop from the NO-SUFFIX baseline (not only vs neutral), and
        the per-prompt distribution, four ways: refusal / random / vanilla-DS / none.
  §19.1(c) TRAIN->HELD-OUT    The same quantity on the frozen train pool vs held-out test.
        A large gap = the universal suffix overfits its refusal suppression to the train
        prompts (supports H3/H5 and §5.5).
  §19.2    LAYER SWEEP        Held-out Dprojection across fit layers L10-L24. Broad,
        near-identical suppression by both suffixes => generic (H4). A refusal-suffix
        deepening specifically at/near its own target layer => partial specificity.
  D2       POSITION           The same contrasts at the `decision` position (where the axis
        was fitted/validated) vs `last_suffix` (where the GCG objective read it).

Paired statistics throughout: the same held-out prompt appears in every condition, so
refusal-vs-random is a paired contrast (bootstrap CI + Wilcoxon-style permutation).
Scalars only.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import stats as st  # noqa: E402


def load(run_dir):
    rows = [json.loads(l) for l in open(os.path.join(run_dir, "projections.jsonl"))]
    # (pool, pos, kind, fit_layer, cond) -> {task_id: proj}
    d = defaultdict(dict)
    for r in rows:
        d[(r["pool"], r["pos"], r["kind"], r["fit_layer"], r["cond"])][r["task_id"]] = r["proj"]
    return d


def paired(d, key_a, key_b, boot):
    a, b = d.get(key_a), d.get(key_b)
    if not a or not b:
        return None
    ids = sorted(set(a) & set(b))
    if len(ids) < 5:
        return None
    x = np.array([a[i] for i in ids])
    y = np.array([b[i] for i in ids])
    ci = st.paired_bootstrap_ci(x, y, n_boot=boot, seed=0)
    perm = st.permutation_test_paired(x, y, n_perm=10000, seed=0)
    return {"n": len(ids), "mean_a": round(float(x.mean()), 4),
            "mean_b": round(float(y.mean()), 4),
            "mean_diff": round(float((x - y).mean()), 4),
            "boot95": [round(ci["lo"], 4), round(ci["hi"], 4)],
            "ci_reliable": ci["ci_reliable"],
            "p_perm": float(perm.get("p_value", perm.get("p", float("nan")))),
            "frac_prompts_a_lower": round(float((x < y).mean()), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--target-fit-layer", type=int, default=18)
    ap.add_argument("--seeds", default="42,43,44")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    d = load(args.run_dir)
    seeds = [int(s) for s in args.seeds.split(",")]
    L = args.target_fit_layer
    pools = sorted({k[0] for k in d})
    positions = sorted({k[1] for k in d})
    layers = sorted({k[3] for k in d if k[2] == "refusal"})
    res = {"run_dir": args.run_dir, "target_fit_layer": L,
           "pools": pools, "positions": positions, "refusal_fit_layers": layers,
           "seed_replication": {}, "absolute_drop": {}, "train_test_gap": {},
           "layer_sweep": {}, "position_D2": {}}

    def K(pool, pos, layer, cond, kind="refusal"):
        return (pool, pos, kind, layer, cond)

    # ---------- §19.1(a) seed replication, held-out, decision position ----------
    for s in seeds:
        cell = {}
        for pool in pools:
            r = paired(d, K(pool, "decision", L, f"refusal_s{s}"),
                       K(pool, "decision", L, f"refusal_rand_s{s}"), args.boot)
            if r:
                # negative mean_diff => the refusal suffix suppresses MORE than random
                r["reading"] = ("refusal suppresses MORE than random"
                                if r["mean_diff"] < 0 else
                                "refusal suppresses LESS than random (non-specific)")
                cell[pool] = r
        res["seed_replication"][f"seed{s}"] = cell

    # ---------- §19.1(b) absolute drop from the NO-SUFFIX baseline ----------
    for pool in pools:
        cell = {}
        base = d.get(K(pool, "decision", L, "none"))
        if not base:
            continue
        for cond in ["neutral"] + [f"{a}_s{s}" for s in seeds
                                   for a in ("vanilla_ds", "refusal", "refusal_rand",
                                             "concept", "concept_rand")]:
            cur = d.get(K(pool, "decision", L, cond))
            if not cur:
                continue
            ids = sorted(set(base) & set(cur))
            x = np.array([cur[i] for i in ids])
            y = np.array([base[i] for i in ids])
            ci = st.paired_bootstrap_ci(x, y, n_boot=args.boot, seed=0)
            cell[cond] = {"n": len(ids),
                          "mean_proj": round(float(x.mean()), 4),
                          "drop_vs_none": round(float((x - y).mean()), 4),
                          "boot95": [round(ci["lo"], 4), round(ci["hi"], 4)],
                          "per_prompt_sd": round(float((x - y).std()), 4),
                          "frac_prompts_dropped": round(float((x < y).mean()), 4)}
        cell["baseline_none_mean"] = round(float(np.mean(list(base.values()))), 4)
        res["absolute_drop"][pool] = cell

    # ---------- §19.1(c) train -> held-out transfer of the suppression ----------
    if "train" in pools and "test" in pools:
        for s in seeds:
            for arm in ("refusal", "refusal_rand", "vanilla_ds"):
                cond = f"{arm}_s{s}"
                cell = {}
                for pool in ("train", "test"):
                    base = d.get(K(pool, "decision", L, "none"))
                    cur = d.get(K(pool, "decision", L, cond))
                    if not base or not cur:
                        continue
                    ids = sorted(set(base) & set(cur))
                    cell[pool] = round(float(np.mean([cur[i] - base[i] for i in ids])), 4)
                if len(cell) == 2:
                    cell["transfer_ratio"] = (round(cell["test"] / cell["train"], 4)
                                              if cell["train"] else None)
                    cell["gap_train_minus_test"] = round(cell["train"] - cell["test"], 4)
                    res["train_test_gap"][cond] = cell

    # ---------- §19.2 layer sweep, held-out ----------
    for s in seeds:
        cell = {}
        for lay in layers:
            base = d.get(K("test", "decision", lay, "none"))
            if not base:
                continue
            row = {}
            for arm in ("refusal", "refusal_rand", "vanilla_ds"):
                cur = d.get(K("test", "decision", lay, f"{arm}_s{s}"))
                if not cur:
                    continue
                ids = sorted(set(base) & set(cur))
                row[arm] = round(float(np.mean([cur[i] - base[i] for i in ids])), 4)
            if "refusal" in row and "refusal_rand" in row:
                row["refusal_minus_random"] = round(row["refusal"] - row["refusal_rand"], 4)
                row["baseline"] = round(float(np.mean(list(base.values()))), 4)
                cell[str(lay)] = row
        res["layer_sweep"][f"seed{s}"] = cell

    # ---------- D2: decision vs last_suffix position ----------
    for s in seeds:
        cell = {}
        for pos in positions:
            r = paired(d, K("test", pos, L, f"refusal_s{s}"),
                       K("test", pos, L, f"refusal_rand_s{s}"), args.boot)
            base = d.get(K("test", pos, L, f"vanilla_ds_s{s}"))
            if r:
                if base:
                    r["vanilla_ds_mean"] = round(float(np.mean(list(base.values()))), 4)
                cell[pos] = r
        res["position_D2"][f"seed{s}"] = cell

    out = args.out or os.path.join(args.run_dir, "ANALYSIS_P1C.json")
    json.dump(res, open(out, "w"), indent=2)

    # ---------------- printout ----------------
    print(f"\n=== P1c EXTENDED MECH-VALIDITY  (target fit layer L{L} -> hs[{L+1}], "
          f"decision position) ===")
    print("\n[19.1a] SEED REPLICATION — held-out test: refusal suffix vs its matched random")
    print(f"  {'seed':6s} {'mean(ref)':>10s} {'mean(rand)':>11s} {'diff':>8s} "
          f"{'boot95':>18s} {'p_perm':>8s} {'frac<':>7s}  reading")
    for s in seeds:
        r = res["seed_replication"].get(f"seed{s}", {}).get("test")
        if not r:
            continue
        print(f"  {s:<6d} {r['mean_a']:10.4f} {r['mean_b']:11.4f} {r['mean_diff']:+8.4f} "
              f"[{r['boot95'][0]:+.3f},{r['boot95'][1]:+.3f}]".ljust(0) +
              f" {r['p_perm']:8.4g} {r['frac_prompts_a_lower']:7.2f}  {r['reading']}")

    print("\n[19.1b] ABSOLUTE DROP from the NO-SUFFIX baseline (held-out test)")
    t = res["absolute_drop"].get("test", {})
    print(f"  baseline (no suffix) mean projection = {t.get('baseline_none_mean')}")
    for cond in sorted(k for k in t if k != "baseline_none_mean"):
        v = t[cond]
        print(f"    {cond:20s} proj={v['mean_proj']:+7.4f} drop={v['drop_vs_none']:+7.4f} "
              f"[{v['boot95'][0]:+.3f},{v['boot95'][1]:+.3f}] sd={v['per_prompt_sd']:.3f} "
              f"frac_dropped={v['frac_prompts_dropped']:.2f}")

    print("\n[19.1c] TRAIN -> HELD-OUT transfer of the suffix's refusal suppression")
    for cond, v in res["train_test_gap"].items():
        print(f"    {cond:20s} train={v['train']:+7.4f} test={v['test']:+7.4f} "
              f"transfer={v.get('transfer_ratio')} gap={v['gap_train_minus_test']:+.4f}")

    print("\n[19.2] LAYER SWEEP (held-out, drop vs no-suffix) — seed 42")
    sw = res["layer_sweep"].get("seed42", {})
    print(f"  {'L':>3s} {'refusal':>9s} {'random':>9s} {'vanillaDS':>10s} {'ref-rand':>9s}")
    for lay in sorted(sw, key=int):
        r = sw[lay]
        print(f"  {lay:>3s} {r.get('refusal', float('nan')):9.4f} "
              f"{r.get('refusal_rand', float('nan')):9.4f} "
              f"{r.get('vanilla_ds', float('nan')):10.4f} "
              f"{r.get('refusal_minus_random', float('nan')):+9.4f}")

    print("\n[D2] POSITION: decision (fit/validated) vs last_suffix (what GCG read)")
    for s in seeds:
        for pos, r in res["position_D2"].get(f"seed{s}", {}).items():
            print(f"    seed{s} {pos:12s} ref={r['mean_a']:+7.4f} rand={r['mean_b']:+7.4f} "
                  f"diff={r['mean_diff']:+7.4f} p={r['p_perm']:.4g}")
    print(f"\n[out] {out}")


if __name__ == "__main__":
    main()
