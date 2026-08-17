"""analyze_position.py — the predictor × position 2×2, with provenance. Committed.

WHY THIS SCRIPT EXISTS. `outputs/boombness/position_2x2.json` held the sprint's headline positive
finding — that the ASR-predictive state is localized at the codeword token — as four bare numbers
with no run paths, no n, no seed, no domain list, and NO PRODUCER. The final verifier could
reproduce every cell, but had to do it from raw rows. That is precisely the "nothing in the repo
could regenerate this" failure that caused RETRACTION #2, sitting under the headline finding. So the
table now comes from a committed command, and the JSON records what produced it.

WHAT IT COMPUTES, and the three ways it refuses to flatter itself:

  1. FREEDOM MATCHED WITHIN PROBE. `d_surface` was extracted with different layer sets at the two
     positions (64 candidate columns at codeword_last, 20 at last), so an unrestricted argmax makes
     the POSITION comparison a comparison of selection freedom. Only columns present at BOTH
     positions are considered.

  2. FREEDOM NOT MATCHED BETWEEN PROBES, and it says so. `d_surface` offers ~20 columns and
     refusalness ~10; both best-of-k statistics, so the between-probe ratio is biased toward
     Boombness. `--subsample-to-min` equalizes it by drawing the same number of columns for each,
     and the report is expected to quote both.

  3. INTERVALS, NOT POINT ESTIMATES. Ratios get a domain-clustered bootstrap. Two variants are
     reported because they answer different questions: `fixed_column` holds the winning column
     (excludes selection variance) and `reselect` re-argmaxes inside each resample (includes it).
     Selection variance is what two of this sprint's five retractions were about, so hiding it is
     not an option.

POSITION SAFETY. Refusalness rows carry `readout_position`; extract rows carry `token_pos`/`seq_len`.
This script VERIFIES that each named run actually read where it claims — a prior "last token" extract
moved only the direction-fitting position and left the readout at the codeword, producing a phantom
cell that briefly flipped the sprint's conclusion. It refuses rather than warns.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl, require_done  # noqa: E402


def _load(run: str, prefix: str, final_occurrence: bool, keep: set) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for r in read_jsonl(os.path.join(run, "results.jsonl")):
        if final_occurrence and not r.get("is_final_occurrence"):
            continue
        if r["prompt_id"] not in keep:
            continue
        out[r["prompt_id"]] = {k: v for k, v in r.items()
                               if k.startswith(prefix) and isinstance(v, (int, float))}
    return out


def _verify_position(run: str, expect: str, kind: str) -> str:
    """Refuse unless the run demonstrably read at `expect`."""
    rows = read_jsonl(os.path.join(run, "results.jsonl"))
    if kind == "refusalness":
        pos = {r.get("readout_position") for r in rows} - {None}
        if not pos:
            raise SystemExit(
                f"[pos] REFUSING: {run} carries no `readout_position` field (pre-2026-08-17 run), so "
                f"its readout position cannot be verified from the artifact. Re-run refusalness.py.")
        if pos != {expect}:
            raise SystemExit(f"[pos] REFUSING: {run} recorded position {pos}, expected {expect!r}")
        return f"readout_position == {expect} on all rows"
    fo = [r for r in rows if r.get("is_final_occurrence")]
    at_last = sum(1 for r in fo if r.get("token_pos") == (r.get("seq_len") or 0) - 1)
    if expect == "last" and at_last != len(fo):
        raise SystemExit(
            f"[pos] REFUSING: {run} claims --position last but only {at_last}/{len(fo)} rows sit at "
            f"seq_len-1. This is the PHANTOM CELL signature: the direction was re-fit at the last "
            f"token while the readout stayed at the codeword.")
    if expect == "codeword_last" and at_last != 0:
        raise SystemExit(f"[pos] REFUSING: {run} claims codeword_last but {at_last} rows sit at seq_len-1")
    return f"{at_last}/{len(fo)} final-occurrence rows at seq_len-1 (expected {'all' if expect=='last' else 'none'})"


def main() -> int:
    import numpy as np
    from sklearn.linear_model import LinearRegression

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--extract-codeword", required=True)
    ap.add_argument("--extract-last", required=True)
    ap.add_argument("--refusalness-codeword", required=True)
    ap.add_argument("--refusalness-last", required=True)
    ap.add_argument("--arm", default="natural_doublespeak")
    ap.add_argument("--min-examples", type=int, default=1)
    ap.add_argument("--cluster-by", default="domain")
    ap.add_argument("--n-boot", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20260817)
    ap.add_argument("--subsample-to-min", action="store_true",
                    help="equalize BETWEEN-probe selection freedom by using the same number of "
                         "candidate columns for each probe (audit item: 20 vs 10 biases the ratio)")
    ap.add_argument("--out", default="outputs/boombness/position_2x2.json")
    ap.add_argument("--allow-partial", action="store_true",
                    help="analyse a run with no DONE.json (output must not be reported)")

    args = ap.parse_args()
    if args.judge:
        require_done(args.judge, allow_partial=args.allow_partial)
    if args.extract_codeword:
        require_done(args.extract_codeword, allow_partial=args.allow_partial)
    if args.extract_last:
        require_done(args.extract_last, allow_partial=args.allow_partial)
    if args.refusalness_codeword:
        require_done(args.refusalness_codeword, allow_partial=args.allow_partial)
    if args.refusalness_last:
        require_done(args.refusalness_last, allow_partial=args.allow_partial)

    J = read_jsonl(os.path.join(args.judge, "results.jsonl"))
    asr = {r["prompt_id"]: r["strongreject_score"] for r in J
           if r.get("strongreject_score") is not None and r.get("condition") == args.arm}
    meta = {r["prompt_id"]: r for r in J if r["prompt_id"] in asr}

    runs = {("d_surface", "codeword_last"): (args.extract_codeword, "d_surface|", True, "extract"),
            ("d_surface", "last"): (args.extract_last, "d_surface|", True, "extract"),
            ("refusalness", "codeword_last"): (args.refusalness_codeword, "refusalness|", False, "refusalness"),
            ("refusalness", "last"): (args.refusalness_last, "refusalness|", False, "refusalness")}

    print("[pos] verifying every run read where it claims to (the phantom-cell check):")
    provenance = {}
    for (probe, pos), (run, _pref, _fo, kind) in runs.items():
        msg = _verify_position(run, pos, kind)
        provenance[f"{probe}@{pos}"] = {"run": os.path.abspath(run), "check": msg}
        print(f"  {probe:12s} @{pos:14s} OK — {msg}")

    keep = set(asr)
    data = {k: _load(v[0], v[1], v[2], keep) for k, v in runs.items()}
    keys = [p for p in asr
            if (meta[p].get("n_examples") or 0) >= args.min_examples
            and all(p in d for d in data.values())]
    y = np.array([asr[p] for p in keys])
    cl = [meta[p].get(args.cluster_by) for p in keys]
    groups = sorted(set(cl))
    gidx = {g: [i for i, c in enumerate(cl) if c == g] for g in groups}
    print(f"[pos] n={len(keys)} prompts, {len(groups)} {args.cluster_by} clusters")
    # A cluster bootstrap over ONE cluster resamples the same rows every draw, giving a ZERO-WIDTH
    # interval and P(ratio>1) of exactly 0 or 1 — manufactured significance that would flip the
    # report's central hedge ("both CIs straddle 1.0") into a false certainty. Refuse rather than
    # degrade.
    if len(groups) < 3:
        raise SystemExit(
            f"[pos] REFUSING: only {len(groups)} {args.cluster_by} cluster(s) "
            f"({groups}) — a cluster bootstrap needs >=3 or it returns a degenerate interval that "
            f"looks like precision. Widen the population or pass a different --cluster-by.")

    def cols_both(probe: str) -> List[str]:
        a = set().union(*[set(data[(probe, "codeword_last")][p]) for p in keys])
        b = set().union(*[set(data[(probe, "last")][p]) for p in keys])
        return sorted(a & b)

    cand = {p: cols_both(p) for p in ("d_surface", "refusalness")}
    if args.subsample_to_min:
        m = min(len(v) for v in cand.values())
        rng0 = np.random.default_rng(args.seed)
        cand = {p: sorted(np.array(v)[rng0.choice(len(v), m, replace=False)].tolist())
                for p, v in cand.items()}
        print(f"[pos] --subsample-to-min: {m} candidate columns per probe (between-probe freedom matched)")
    for p, v in cand.items():
        print(f"[pos] {p}: {len(v)} candidate columns present at BOTH positions")

    def r2_of(probe, pos, col, idx=None):
        ii = idx if idx is not None else range(len(keys))
        x = np.array([[data[(probe, pos)][keys[i]].get(col, np.nan)] for i in ii])
        yy = y[list(ii)]
        if np.isnan(x).any() or yy.std() < 1e-12:
            return float("nan")
        return LinearRegression().fit(x, yy).score(x, yy)

    table, best = {}, {}
    for probe in cand:
        for pos in ("last", "codeword_last"):
            scores = {c: r2_of(probe, pos, c) for c in cand[probe]}
            scores = {c: v for c, v in scores.items() if v == v}
            bc = max(scores, key=scores.get)
            best[(probe, pos)] = bc
            table[f"{probe}@{pos}"] = {"best_col": bc, "best_r2": scores[bc],
                                       "median_r2": float(np.median(list(scores.values()))),
                                       "n_cols": len(scores)}
            print(f"  {probe:12s} @{pos:14s} best {scores[bc]:.4f} ({bc})  median {np.median(list(scores.values())):.4f}")

    ratios = {}
    rng = np.random.default_rng(args.seed)
    for pos in ("last", "codeword_last"):
        obs = table[f"d_surface@{pos}"]["best_r2"] / table[f"refusalness@{pos}"]["best_r2"]
        variants = {}
        for mode in ("fixed_column", "reselect"):
            boots = []
            for _ in range(args.n_boot):
                sel = np.concatenate([gidx[groups[i]] for i in rng.integers(0, len(groups), len(groups))])
                if mode == "fixed_column":
                    a = r2_of("d_surface", pos, best[("d_surface", pos)], sel)
                    b = r2_of("refusalness", pos, best[("refusalness", pos)], sel)
                else:
                    a = max((r2_of("d_surface", pos, c, sel) for c in cand["d_surface"]), default=float("nan"))
                    b = max((r2_of("refusalness", pos, c, sel) for c in cand["refusalness"]), default=float("nan"))
                if a == a and b == b and b > 1e-9:
                    boots.append(a / b)
            boots = np.sort(np.array(boots))
            variants[mode] = {"ci95": [float(boots[int(.025 * len(boots))]),
                                       float(boots[int(.975 * len(boots))])],
                              "p_ratio_gt_1": float(np.mean(boots > 1)), "n_boot": len(boots)}
        ratios[pos] = {"ratio_boombness_over_refusalness": obs, **variants}
        fc, rs = variants["fixed_column"], variants["reselect"]
        print(f"[pos] @{pos:14s} ratio {obs:.2f}  fixed-col CI [{fc['ci95'][0]:.2f},{fc['ci95'][1]:.2f}] "
              f"P(>1)={fc['p_ratio_gt_1']:.2f} | reselect CI [{rs['ci95'][0]:.2f},{rs['ci95'][1]:.2f}]")

    for probe in cand:
        a, b = table[f"{probe}@codeword_last"]["best_r2"], table[f"{probe}@last"]["best_r2"]
        print(f"[pos] {probe:12s} POSITION EFFECT {a/b:.2f}x  ({b:.4f} @last -> {a:.4f} @codeword_last)")

    out = {"design": "predictor x position, single-predictor R2 on a common prompt set",
           "arm": args.arm, "n": len(keys), "clusters": {args.cluster_by: groups},
           "min_examples": args.min_examples, "seed": args.seed,
           "between_probe_freedom_matched": bool(args.subsample_to_min),
           "candidate_columns": {p: len(v) for p, v in cand.items()},
           "provenance": provenance, "judge": os.path.abspath(args.judge),
           "cells": table, "ratios": ratios,
           "position_effect": {p: table[f"{p}@codeword_last"]["best_r2"] / table[f"{p}@last"]["best_r2"]
                               for p in cand}}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n[pos] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
