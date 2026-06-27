"""Build a manifest of which (model, goal_id, source_puzzle_id, seed) tuples have
which conditions (A/D/E/F/G) present or absent.

This is the source of truth for what G-condition jobs to submit.
The G-condition SLURM jobs MUST target exactly the (source_puzzle_id, seed) tuples
that exist for A/D/E/F, not simply "3 seeds × all goals."

Outputs:
  outputs/stage4/factorial_balanced/manifest.jsonl
      One row per (model, source_example_id, seed) tuple.
      Fields: model_family, source_example_id, goal_index, seed,
              has_A, has_D, has_E, has_F, has_G,
              missing_conditions, is_complete_adefs, is_complete_adefg

  outputs/stage4/factorial_balanced/coverage_summary.csv
      Per-(model, source_example_id): how many seeds per condition.

Usage:
    python -m poc_stage4.build_complete_factorial_manifest
        [--dataset outputs/stage4/factorial_attack_dataset.jsonl]
        [--output-dir outputs/stage4/factorial_balanced]
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_DATASET = _REPO_ROOT / "outputs" / "stage4" / "factorial_attack_dataset.jsonl"
_OUTPUT_DIR = _REPO_ROOT / "outputs" / "stage4" / "factorial_balanced"
_ALL_CONDITIONS = ["A", "D", "E", "F", "G"]


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_manifest(dataset_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    if not dataset_path.exists():
        print(f"ERROR: dataset not found at {dataset_path}")
        return

    rows = _load_jsonl(dataset_path)
    print(f"Loaded {len(rows)} rows from {dataset_path}")

    # Group by (model_family, source_example_id, seed) → set of conditions present
    # Key: (model, source_id, seed)
    present: dict[tuple, set[str]] = defaultdict(set)
    metadata: dict[tuple, dict] = {}

    for r in rows:
        model = r.get("model_family", "")
        sid = r.get("source_example_id", "")
        seed = r.get("seed")
        cond = r.get("condition", "")
        if not model or not sid or seed is None or not cond:
            continue
        key = (model, sid, seed)
        present[key].add(cond)
        if key not in metadata:
            metadata[key] = {
                "goal_index": r.get("goal_index"),
                "source_stage": r.get("source_stage", ""),
            }

    # Build manifest rows
    manifest_rows = []
    for key, conditions in sorted(present.items()):
        model, sid, seed = key
        meta = metadata[key]
        missing = [c for c in _ALL_CONDITIONS if c not in conditions]
        row = {
            "model_family": model,
            "source_example_id": sid,
            "goal_index": meta["goal_index"],
            "seed": seed,
            "has_A": "A" in conditions,
            "has_D": "D" in conditions,
            "has_E": "E" in conditions,
            "has_F": "F" in conditions,
            "has_G": "G" in conditions,
            "missing_conditions": missing,
            "is_complete_adef": all(c in conditions for c in ["A", "D", "E", "F"]),
            "is_complete_adefg": all(c in conditions for c in ["A", "D", "E", "F", "G"]),
            "source_stage": meta["source_stage"],
        }
        manifest_rows.append(row)

    # Write manifest
    manifest_path = output_dir / "manifest.jsonl"
    with manifest_path.open("w") as f:
        for row in manifest_rows:
            f.write(json.dumps(row) + "\n")
    print(f"Wrote {len(manifest_rows)} seed-level tuples to {manifest_path}")

    # Per-(model, source_id) coverage summary
    coverage: dict[tuple, dict] = defaultdict(lambda: {c: 0 for c in _ALL_CONDITIONS})
    for r in manifest_rows:
        key2 = (r["model_family"], r["source_example_id"])
        for c in _ALL_CONDITIONS:
            if r.get(f"has_{c}"):
                coverage[key2][c] += 1

    coverage_rows = []
    for (model, sid), cond_counts in sorted(coverage.items()):
        goal = next((r["goal_index"] for r in manifest_rows
                     if r["model_family"] == model and r["source_example_id"] == sid), None)
        counts_equal = len(set(v for v in cond_counts.values() if v > 0)) <= 1
        coverage_rows.append({
            "model_family": model,
            "source_example_id": sid[:60],
            "goal_index": goal,
            **{f"n_{c}": cond_counts[c] for c in _ALL_CONDITIONS},
            "g_missing": cond_counts["G"] == 0,
            "seed_counts_equal_adefs": counts_equal,
        })

    csv_path = output_dir / "coverage_summary.csv"
    if coverage_rows:
        fields = list(coverage_rows[0].keys())
        with csv_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(coverage_rows)
    print(f"Coverage summary → {csv_path}")

    # Print key statistics
    n_total = len(manifest_rows)
    n_g_missing = sum(1 for r in manifest_rows if not r["has_G"])
    n_complete_adefg = sum(1 for r in manifest_rows if r["is_complete_adefg"])
    n_complete_adef = sum(1 for r in manifest_rows if r["is_complete_adef"])

    print(f"\n=== MANIFEST SUMMARY ===")
    print(f"Total (model, source_id, seed) tuples: {n_total}")
    print(f"  Complete A/D/E/F (no G): {n_complete_adef}")
    print(f"  Complete A/D/E/F/G:      {n_complete_adefg}")
    print(f"  Missing G condition:     {n_g_missing}")

    # Per-model breakdown
    by_model: dict[str, dict] = defaultdict(lambda: {"total": 0, "missing_g": 0, "complete_adefg": 0})
    for r in manifest_rows:
        m = r["model_family"]
        by_model[m]["total"] += 1
        if not r["has_G"]:
            by_model[m]["missing_g"] += 1
        if r["is_complete_adefg"]:
            by_model[m]["complete_adefg"] += 1

    print("\nPer model:")
    for model in sorted(by_model.keys()):
        d = by_model[model]
        print(f"  {model}: {d['total']} tuples, {d['missing_g']} missing G, {d['complete_adefg']} complete")

    # List which (source_id, seed) tuples need G — these are the G job targets
    need_g = [r for r in manifest_rows if r["is_complete_adef"] and not r["has_G"]]
    if need_g:
        print(f"\nTuples that need G condition ({len(need_g)} total):")
        for r in need_g[:20]:
            print(f"  {r['model_family']} | goal={r['goal_index']} | seed={r['seed']} | {r['source_example_id'][:50]}")
        if len(need_g) > 20:
            print(f"  ... and {len(need_g) - 20} more")

        # Write a job input file for the G condition SLURM jobs
        g_job_path = output_dir / "g_condition_job_targets.jsonl"
        with g_job_path.open("w") as f:
            for r in need_g:
                f.write(json.dumps({
                    "model_family": r["model_family"],
                    "source_example_id": r["source_example_id"],
                    "goal_index": r["goal_index"],
                    "seed": r["seed"],
                }) + "\n")
        print(f"\nG condition job targets → {g_job_path}")
        print("Use this file as the job array input for stage4_8_cond_g_*.slurm")
    else:
        print("\nNo tuples missing G (either G is already present, or A/D/E/F are incomplete)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(_DATASET))
    parser.add_argument("--output-dir", default=str(_OUTPUT_DIR))
    args = parser.parse_args()
    build_manifest(Path(args.dataset), Path(args.output_dir))
