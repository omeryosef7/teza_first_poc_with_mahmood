#!/usr/bin/env python3
"""Paired statistics for a phase_behav_carry run (reads raw.jsonl only — no generation/GPU).

Behavioral necessity of the carry heads is a PAIRED design: the same DS prompt is judged under
baseline and under carry-ablation. So the right test is McNemar's exact test on the discordant
pairs (was-MALICIOUS→not vs not→was-MALICIOUS), not an unpaired proportion test. We report:
  - ASR per arm, ASR delta (baseline - carry_abl) with a paired bootstrap CI
  - McNemar exact p (baseline vs carry_abl) and (baseline vs rand_abl)  [Holm across the 2 arms]
  - the same for the random-head control arm (specificity: carry should flip more than random)
Rows with EMPTY on either compared arm are dropped from that pair (can't score a flip).

Usage: python scripts/phase_behav_carry_analyze.py outputs/behav_carry_clearharm_...  [more dirs]
"""
from __future__ import annotations
import json, os, sys
from math import comb
import numpy as np


def mcnemar_exact(b, c):
    """Two-sided exact McNemar on discordant counts b (0->1) and c (1->0): binomial(min,b+c,0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * p)


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj = [0.0] * len(pvals)
    m = len(pvals)
    running = 0.0
    for rank, i in enumerate(order):
        v = (m - rank) * pvals[i]
        running = max(running, v)
        adj[i] = min(1.0, running)
    return adj


def analyze_dir(d):
    rows = [json.loads(x) for x in open(os.path.join(d, "raw.jsonl"))]
    splits = sorted({r["split"] for r in rows})
    out = {"dir": os.path.basename(d), "by_split": {}}
    rng = np.random.default_rng(0)
    for sp in splits:
        sr = [r for r in rows if r["split"] == sp]
        mal = lambda r, arm: r.get(f"{arm}_label") == "MALICIOUS"
        emp = lambda r, arm: r.get(f"{arm}_label") == "EMPTY"
        n = len(sr)
        asr = {arm: round(float(np.mean([mal(r, arm) for r in sr])), 4) for arm in ("baseline", "carry_abl", "rand_abl")}
        res = {"n": n, "ASR": asr}
        pvals, keys = [], []
        for arm in ("carry_abl", "rand_abl"):
            pair = [r for r in sr if not emp(r, "baseline") and not emp(r, arm)]
            b = sum(1 for r in pair if not mal(r, "baseline") and mal(r, arm))    # 0->1 (ablation ADDED harm)
            c = sum(1 for r in pair if mal(r, "baseline") and not mal(r, arm))    # 1->0 (ablation REMOVED harm)
            p = mcnemar_exact(b, c)
            # paired bootstrap CI on ASR delta (baseline - arm) over paired rows
            db = np.array([int(mal(r, "baseline")) - int(mal(r, arm)) for r in pair], float)
            boot = [rng.choice(db, len(db), replace=True).mean() for _ in range(5000)] if len(db) else [0.0]
            res[arm] = {"n_paired": len(pair), "flip_off_1to0": c, "flip_on_0to1": b,
                        "delta_ASR": round(float(db.mean()) if len(db) else 0.0, 4),
                        "delta_CI": [round(float(np.percentile(boot, 2.5)), 4), round(float(np.percentile(boot, 97.5)), 4)],
                        "mcnemar_p": round(p, 5)}
            pvals.append(p); keys.append(arm)
        for k, pa in zip(keys, holm(pvals)):
            res[k]["mcnemar_p_holm"] = round(pa, 5)
        res["empty_rate"] = {arm: round(float(np.mean([emp(r, arm) for r in sr])), 4) for arm in ("baseline", "carry_abl", "rand_abl")}
        out["by_split"][sp] = res
    return out


def main():
    dirs = sys.argv[1:]
    if not dirs:
        print("usage: phase_behav_carry_analyze.py <run_dir> [run_dir...]"); sys.exit(1)
    for d in dirs:
        r = analyze_dir(d)
        json.dump(r, open(os.path.join(d, "paired_stats.json"), "w"), indent=1)
        print(f"\n=== {r['dir']} ===")
        for sp, s in r["by_split"].items():
            c = s["carry_abl"]; ra = s["rand_abl"]
            print(f" [{sp}] n={s['n']} ASR base={s['ASR']['baseline']} carry={s['ASR']['carry_abl']} rand={s['ASR']['rand_abl']}")
            print(f"    carry: ΔASR={c['delta_ASR']} CI{c['delta_CI']} (off 1->0={c['flip_off_1to0']}, on 0->1={c['flip_on_0to1']}) McNemar p={c['mcnemar_p']} Holm={c['mcnemar_p_holm']}")
            print(f"    rand : ΔASR={ra['delta_ASR']} CI{ra['delta_CI']} McNemar p={ra['mcnemar_p']} Holm={ra['mcnemar_p_holm']} | empty carry={s['empty_rate']['carry_abl']}")


if __name__ == "__main__":
    main()
