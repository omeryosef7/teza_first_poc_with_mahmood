"""§C3 (Claude extension, user-authorized 2026-07-23) — length IDENTIFIABILITY diagnostic.

The adversarial review of the original C3 (a length-matched-pair AUC) showed that statistic is
UNACHIEVABLE here: successful vs failed CoT-Hijacking attack prompts have near-DISJOINT lengths, so
caliper matching yields ≤10 pairs → zero power. Reframed (per review) as an honest IDENTIFIABILITY
DIAGNOSTIC: quantify the non-overlap directly. If success and failure prompt lengths barely overlap, then
length and any length-correlated internal signal are structurally NON-SEPARABLE in this pool — which is
*why* the length confound cannot be resolved by matching, and strengthens the honest confound story
WITHOUT claiming an inferential verdict the N cannot support.

Outputs, per (model, condition-set): success vs failure input-length distributions (min/median/mean/max),
distribution overlap, greedy caliper-matched pair counts at ±10/±25/±50 tokens, and AUC(−input_len →
success) for context. REUSE: `_row_lengths` (input lengths from §9 generation shards) and `_auc` from
`scripts/phase6_confound_control.py`; success labels from the frozen `phase6_scores.jsonl`.

Usage:
  python scripts/phase6_length_identifiability.py \
    --run-dir outputs/phase5_mechanistic/extraction \
    --scores outputs/phase5_mechanistic/phase6_scores.jsonl \
    --conditions C D --out outputs/phase5_mechanistic/phase6_length_identifiability.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from phase6_confound_control import _row_lengths, _auc  # reuse (no duplication)


def _greedy_matched_pairs(succ_lens: list[int], fail_lens: list[int], caliper: int) -> int:
    """Greedy 1:1 caliper matching on input length: for each success row (ascending), take the closest
    still-unused failure row within `caliper` tokens. Returns the number of matched pairs (the count that
    a length-matched analysis could actually use)."""
    fails = sorted(fail_lens)
    used = [False] * len(fails)
    pairs = 0
    for sl in sorted(succ_lens):
        best_j, best_d = -1, None
        for j, fl in enumerate(fails):
            if used[j]:
                continue
            d = abs(fl - sl)
            if d <= caliper and (best_d is None or d < best_d):
                best_j, best_d = j, d
        if best_j >= 0:
            used[best_j] = True
            pairs += 1
    return pairs


def _overlap_fraction(succ: list[int], fail: list[int]) -> float:
    """Fraction of the combined length RANGE where BOTH classes have mass (interval overlap / union)."""
    lo = max(min(succ), min(fail))
    hi = min(max(succ), max(fail))
    inter = max(0, hi - lo)
    union = max(max(succ), max(fail)) - min(min(succ), min(fail))
    return round(inter / union, 4) if union > 0 else 0.0


def _dist(xs: list[int]) -> dict:
    a = np.array(xs)
    return {"n": len(xs), "min": int(a.min()), "median": float(np.median(a)),
            "mean": round(float(a.mean()), 1), "max": int(a.max())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--conditions", nargs="+", default=["C", "D"])
    ap.add_argument("--calipers", nargs="+", type=int, default=[10, 25, 50])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    lengths = _row_lengths(Path(args.run_dir))          # row_key -> {input_len, gen_len}
    conds = set(args.conditions)
    succ_lens, fail_lens = [], []
    with open(args.scores) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("condition") not in conds:
                continue
            rk = r["row_key"]
            if rk not in lengths:
                continue
            ilen = lengths[rk]["input_len"]
            if not ilen:
                continue
            (succ_lens if r.get("strongreject_is_success") else fail_lens).append(int(ilen))

    if not succ_lens or not fail_lens:
        raise SystemExit(f"need both classes; got {len(succ_lens)} succ / {len(fail_lens)} fail")

    all_lens = np.array(succ_lens + fail_lens)
    y = np.array([1] * len(succ_lens) + [0] * len(fail_lens))
    result = {
        "conditions": sorted(conds),
        "n_success": len(succ_lens), "n_failure": len(fail_lens),
        "success_input_len": _dist(succ_lens),
        "failure_input_len": _dist(fail_lens),
        "length_range_overlap_fraction": _overlap_fraction(succ_lens, fail_lens),
        "auc_length_to_success": (round(_auc(-all_lens.astype(float), y), 4)
                                  if _auc(-all_lens.astype(float), y) is not None else None),
        "matched_pairs_by_caliper": {str(c): _greedy_matched_pairs(succ_lens, fail_lens, c)
                                     for c in args.calipers},
        "max_possible_pairs": min(len(succ_lens), len(fail_lens)),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    mp = result["matched_pairs_by_caliper"]
    print(f"\n[C3] succ len mean={result['success_input_len']['mean']} vs fail "
          f"{result['failure_input_len']['mean']}; range-overlap={result['length_range_overlap_fraction']}; "
          f"matched pairs {mp} of max {result['max_possible_pairs']} → "
          f"{'NON-separable (matching underpowered)' if max(mp.values()) < 12 else 'matchable'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
