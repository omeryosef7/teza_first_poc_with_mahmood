#!/usr/bin/env python3
"""Merge one or more phase5_head_zpatch.py output dirs (e.g. layer halves L0-15 + L16-31 of the
same cohort) and re-apply Holm across the FULL 32x32 (layer,head) family, per split.

Necessity(l,h) = C1 - patched_benign, paired over valid examples (DS C1 p_concept > benign).
Reports self-swap max dev, Holm-significant heads, and the top heads by necessity.

Usage:
  python scripts/phase5_analyze.py <dir1> <dir2> ...     # dirs of the SAME cohort
"""
from __future__ import annotations
import json, os, sys
from collections import defaultdict
import numpy as np

RNG = np.random.default_rng(0)


def perm_p(vals, nperm=20000):
    a = np.array(vals, float)
    if a.size == 0:
        return 1.0
    obs = abs(a.mean())
    signs = RNG.integers(0, 2, size=(nperm, a.size)) * 2 - 1
    return float((np.abs((signs * a).mean(1)) >= obs).mean())


def bootci(vals, nboot=2000):
    a = np.array(vals, float)
    if a.size == 0:
        return None
    boot = [RNG.choice(a, a.size, replace=True).mean() for _ in range(nboot)]
    return [round(float(a.mean()), 4), round(float(np.percentile(boot, 2.5)), 4),
            round(float(np.percentile(boot, 97.5)), 4)]


def holm(pv, alpha=0.05):
    order = sorted(pv, key=lambda k: pv[k])
    m = len(order)
    rej, ok = {}, True
    for i, k in enumerate(order):
        if ok and pv[k] <= alpha / (m - i):
            rej[k] = True
        else:
            ok = False
            rej[k] = False
    return rej


def main():
    dirs = sys.argv[1:]
    if not dirs:
        print("usage: phase5_analyze.py <dir1> [<dir2> ...]")
        sys.exit(1)
    rows = []
    cohorts = set()
    for d in dirs:
        for l in open(os.path.join(d, "raw.jsonl")):
            rows.append(json.loads(l))
        s = json.load(open(os.path.join(d, "summary.json")))
        cohorts.add(s.get("cohort", "?"))
    cohort = "+".join(sorted(cohorts))
    print(f"### merged {len(dirs)} dir(s), cohort={cohort}, {len(rows)} rows")
    for split in sorted({r["split"] for r in rows}):
        sr = [r for r in rows if r["split"] == split]
        valid = {r["sid"] for r in sr if r["cell"] == "benign"
                 and r.get("benign_p_concept") is not None and r["C1"] > r["benign_p_concept"]}
        selfdev = max([abs(r["C1"] - r["p_concept"]) for r in sr if r["cell"] == "selfswap"] or [0.0])
        # necessity per (l,h)
        by_cell = defaultdict(dict)   # (l,h) -> {sid: p_patched}
        c1_of = {}
        for r in sr:
            if r["cell"] == "benign" and r["sid"] in valid:
                by_cell[(r["layer"], r["head"])][r["sid"]] = r["p_concept"]
                c1_of[r["sid"]] = r["C1"]
        pv, mean, cis = {}, {}, {}
        for (l, h), d in by_cell.items():
            diffs = [c1_of[s] - d[s] for s in d]
            if diffs:
                pv[(l, h)] = perm_p(diffs)
                mean[(l, h)] = float(np.mean(diffs))
                cis[(l, h)] = bootci(diffs)
        rej = holm(pv)
        holm_sig = sorted([(f"L{l}H{h}", round(mean[(l, h)], 4), round(pv[(l, h)], 6), cis[(l, h)])
                           for (l, h) in pv if rej.get((l, h)) and mean[(l, h)] > 0], key=lambda x: -x[1])
        top = sorted(mean.items(), key=lambda x: -x[1])[:12]
        n_layers = len({l for (l, h) in mean})
        print(f"  [{split}] n_valid={len(valid)} layers_covered={n_layers} n_cells={len(pv)} "
              f"selfswap_dev={selfdev:.2e}")
        print(f"     Holm-sig positive-necessity heads ({len(holm_sig)}): {holm_sig[:15]}")
        print(f"     top12 by necessity: {[(k, round(v,4)) for k,v in top]}")


if __name__ == "__main__":
    main()
