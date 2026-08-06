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
from scipy import stats

RNG = np.random.default_rng(0)


def pval(vals):
    """Two-sided WILCOXON signed-rank p-value for H0: median(diff)=0.

    NOTE (audit fix): the original sign-flip permutation at nperm=2e4 had resolution floor
    1/nperm=5e-5, COARSER than the Holm threshold alpha/m=0.05/1024=4.88e-5 for the 32x32 head
    family — so only artifactual p=0 cells could pass Holm. A paired t-test resolves but is
    over-conservative because the necessity diffs are strongly right-skewed (a few strong
    examples dominate the mean, sign consistent). Wilcoxon is robust to that skew, deterministic,
    and resolves below the 1024-cell threshold for strong effects. (Effect size + CI via bootci.)"""
    a = np.array(vals, float)
    if a.size < 6 or np.allclose(a, 0):
        return 1.0
    try:
        return float(stats.wilcoxon(a).pvalue)
    except ValueError:
        return 1.0


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
    import argparse
    ap = argparse.ArgumentParser(description="pool run dirs and Holm-correct over the (layer,head) family")
    ap.add_argument("dirs", nargs="+")
    # F2 (VERIFY_P4B1_ANALYSIS): m = len(pv) is data-dependent, so pointing this at ONE shard silently
    # Holm-corrects over <1024 cells and UNDER-corrects with no error. --expect-cells makes the
    # pre-registered family size a HARD gate: pass 1024 for a full sharded P4b run. Default 0 = off
    # (back-compat for the historical single-dir answer-position runs).
    ap.add_argument("--expect-cells", type=int, default=0,
                    help="assert n_cells == this per split (P4b pooled run: 1024). 0 = no check.")
    ap.add_argument("--only-sids-file", default=None,
                    help="JSON with {'clean_sids':[...]}; restrict to those sids (clean-subset sensitivity)")
    args = ap.parse_args()
    dirs = args.dirs
    _fail = []
    _keep_sids = None
    if args.only_sids_file:
        _keep_sids = set(json.load(open(args.only_sids_file))["clean_sids"])
        print(f"### RESTRICTED to {len(_keep_sids)} clean sids from {args.only_sids_file}")
    _holm_by_split = {}
    rows = []
    cohorts = set()
    for d in dirs:
        for l in open(os.path.join(d, "raw.jsonl")):
            rows.append(json.loads(l))
        s = json.load(open(os.path.join(d, "summary.json")))
        cohorts.add(s.get("cohort", "?"))
    cohort = "+".join(sorted(cohorts))
    print(f"### merged {len(dirs)} dir(s), cohort={cohort}, {len(rows)} rows")
    if _keep_sids is not None:
        rows = [r for r in rows if r.get("sid") in _keep_sids]
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
        pv, mean, diffs_of = {}, {}, {}
        for (l, h), d in by_cell.items():
            diffs = [c1_of[s] - d[s] for s in d]
            if diffs:
                pv[(l, h)] = pval(diffs)
                mean[(l, h)] = float(np.mean(diffs))
                diffs_of[(l, h)] = diffs
        rej = holm(pv)
        # bootstrap CIs only for the (few) Holm-significant cells — avoids 1024x2000 resamples
        cis = {k: bootci(diffs_of[k]) for k in pv if rej.get(k)}
        holm_sig = sorted([(f"L{l}H{h}", round(mean[(l, h)], 4), round(pv[(l, h)], 6), cis.get((l, h)))
                           for (l, h) in pv if rej.get((l, h)) and mean[(l, h)] > 0], key=lambda x: -x[1])
        top = sorted(mean.items(), key=lambda x: -x[1])[:12]
        n_layers = len({l for (l, h) in mean})
        # audit finding: power floor. Wilcoxon min achievable p ~ 2/2^n_valid; if that exceeds
        # alpha/m (m = tested cells) NO cell can survive Holm regardless of true effect -> a 0 is a
        # power artifact, not a null. (For n_valid>=16 & m=1024 the family is resolvable.)
        m = max(len(pv), 1)
        pfloor = 2.0 / (2 ** len(valid)) if len(valid) < 60 else 0.0
        underpowered = pfloor > 0.05 / m
        print(f"  [{split}] n_valid={len(valid)} layers_covered={n_layers} n_cells={len(pv)} "
              f"selfswap_dev={selfdev:.2e} underpowered={underpowered} (pfloor={pfloor:.1e} vs a/m={0.05/m:.1e})")
        print(f"     Holm-sig positive-necessity heads ({len(holm_sig)}): {holm_sig[:15]}")
        print(f"     top12 by necessity: {[(k, round(v,4)) for k,v in top]}")
        _holm_by_split[split] = {name for (name, _m, _p, _ci) in holm_sig}
        if args.expect_cells and len(pv) != args.expect_cells:
            _fail.append(f"[{split}] n_cells={len(pv)} != expected {args.expect_cells} -- Holm family is "
                         f"the WRONG SIZE (missing shard? truncated raw?). Numbers above are UNDER/OVER-"
                         f"corrected and must not be quoted.")
    if {"dev", "heldout"} <= set(_holm_by_split):
        confirmed = sorted(_holm_by_split["dev"] & _holm_by_split["heldout"])
        print(f"\n### CONFIRMED (Holm-sig positive-necessity on BOTH dev AND heldout, pre-reg section 4): "
              f"{len(confirmed)} heads")
        print(f"    {confirmed}")
        print(f"    dev-only: {len(_holm_by_split['dev'] - _holm_by_split['heldout'])}  "
              f"heldout-only: {len(_holm_by_split['heldout'] - _holm_by_split['dev'])}")
    if _fail:
        print("\nERROR: pre-registered family-size check FAILED:", file=sys.stderr)
        for _f in _fail:
            print("  " + _f, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
