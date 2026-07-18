"""
Track 10F — Union ensemble ASR across 9A and 9B (or any two completed runs).

9A (λ=0.3/seed=42) and 9B (seed=45) hit DIFFERENT behaviors.
Union ASR = fraction of (task_id, seed) combos where EITHER run succeeded.
Expected: significantly higher than either individual run (15–18% vs ~11%).

Usage:
    python scripts/build_union_ensemble_asr.py \
        --run-a outputs/stage_gcg_full/gcg_full_qwen3_9a_lambda03_full520 \
        --run-b outputs/stage_gcg_full/gcg_full_qwen3_9b_seed45_full520 \
        [--run-c outputs/stage_gcg_full/gcg_full_qwen3_9c_lambda03_seed45_full520]

Output:
    - Individual ASR for each run
    - Pairwise and N-way union ASR
    - Behavior-level overlap analysis (which behaviors each run hits uniquely)
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path


def load_results(run_dir: Path, condition_filter: str = "optimized") -> dict:
    """
    Load FREE_GENERATION_RESULTS.jsonl and return:
    {
        "by_combo": {(task_id, seed): bool — any success},
        "winning_behaviors": set of task_ids with any success,
        "total_combos": int,
        "n_rows": int,
    }
    """
    results_path = run_dir / "FREE_GENERATION_RESULTS.jsonl"
    if not results_path.exists():
        raise FileNotFoundError(f"Results not found: {results_path}")

    rows = [json.loads(l) for l in results_path.read_text().splitlines() if l.strip()]
    # Filter to optimized condition only (skip neutral/random baselines)
    if condition_filter:
        rows = [r for r in rows if condition_filter in r.get("condition_label", "")]

    by_combo: dict = collections.defaultdict(list)
    for r in rows:
        k = (r.get("task_id", ""), str(r.get("seed", "")))
        by_combo[k].append(str(r.get("strongreject_is_success", "False")) == "True")

    winning_combos = {k for k, v in by_combo.items() if any(v)}
    winning_behaviors = {k[0] for k in winning_combos}

    return {
        "by_combo": {k: any(v) for k, v in by_combo.items()},
        "winning_combos": winning_combos,
        "winning_behaviors": winning_behaviors,
        "total_combos": len(by_combo),
        "n_rows": len(rows),
    }


def union_asr(runs: list[dict]) -> dict:
    """Compute union: a combo succeeds if ANY run succeeds on it."""
    all_combos = set()
    for r in runs:
        all_combos.update(r["by_combo"].keys())

    union_wins = {
        k for k in all_combos
        if any(r["by_combo"].get(k, False) for r in runs)
    }
    union_behaviors = {k[0] for k in union_wins}

    return {
        "total_combos": len(all_combos),
        "union_wins": len(union_wins),
        "union_asr": len(union_wins) / len(all_combos) if all_combos else 0.0,
        "union_behaviors": len(union_behaviors),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Union ensemble ASR analysis (Track 10F)")
    parser.add_argument("--run-a", type=Path, required=True, help="First run directory (e.g. 9A)")
    parser.add_argument("--run-b", type=Path, required=True, help="Second run directory (e.g. 9B)")
    parser.add_argument("--run-c", type=Path, default=None, help="Optional third run (e.g. 9C)")
    parser.add_argument("--condition-filter", default="optimized",
                        help="Filter rows by condition_label containing this string (default: optimized)")
    args = parser.parse_args()

    run_dirs = [args.run_a, args.run_b]
    run_labels = [args.run_a.name, args.run_b.name]
    if args.run_c:
        run_dirs.append(args.run_c)
        run_labels.append(args.run_c.name)

    print("=" * 70)
    print("  Track 10F — Union Ensemble ASR Analysis")
    print("=" * 70)

    runs = []
    for label, run_dir in zip(run_labels, run_dirs):
        try:
            r = load_results(run_dir, condition_filter=args.condition_filter)
            runs.append(r)
            asr = len(r["winning_combos"]) / r["total_combos"] if r["total_combos"] else 0
            print(f"\n[{label}]")
            print(f"  Rows (opt only): {r['n_rows']}")
            print(f"  Combos:          {r['total_combos']}")
            print(f"  Winning combos:  {len(r['winning_combos'])} ({asr*100:.1f}% ASR)")
            print(f"  Unique behaviors: {len(r['winning_behaviors'])}")
        except FileNotFoundError as e:
            print(f"\nWARNING: {e} — skipping.")

    if len(runs) < 2:
        print("\nNeed at least 2 runs for union analysis.")
        return

    # Pairwise A+B
    ab_union = union_asr(runs[:2])
    print(f"\n[Union {run_labels[0]} + {run_labels[1]}]")
    print(f"  Total combos:    {ab_union['total_combos']}")
    print(f"  Union wins:      {ab_union['union_wins']} ({ab_union['union_asr']*100:.1f}% ASR)")
    print(f"  Union behaviors: {ab_union['union_behaviors']}")

    # Behavior-level overlap
    a_beh = runs[0]["winning_behaviors"]
    b_beh = runs[1]["winning_behaviors"]
    only_a = a_beh - b_beh
    only_b = b_beh - a_beh
    both = a_beh & b_beh
    print(f"\n  Behavior overlap:")
    print(f"    Only in {run_labels[0]}: {len(only_a)} behaviors")
    print(f"    Only in {run_labels[1]}: {len(only_b)} behaviors")
    print(f"    In both:             {len(both)} behaviors")
    print(f"    In either:           {len(a_beh | b_beh)} behaviors")

    # Three-way if present
    if len(runs) == 3:
        abc_union = union_asr(runs)
        c_beh = runs[2]["winning_behaviors"]
        print(f"\n[Union {run_labels[0]} + {run_labels[1]} + {run_labels[2]}]")
        print(f"  Total combos:    {abc_union['total_combos']}")
        print(f"  Union wins:      {abc_union['union_wins']} ({abc_union['union_asr']*100:.1f}% ASR)")
        print(f"  Union behaviors: {abc_union['union_behaviors']}")
        all_beh = a_beh | b_beh | c_beh
        print(f"  All 3 union:     {len(all_beh)} behaviors")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
