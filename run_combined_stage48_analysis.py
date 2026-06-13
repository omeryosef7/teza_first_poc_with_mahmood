#!/usr/bin/env python3
"""
Combined Stage 4.8 analysis: merge base + extension v2 + extension v3,
then run behavior-conditioned direction extraction on the full dataset.

Run AFTER all three extensions have had representation extraction completed.

Usage:
    python3 run_combined_stage48_analysis.py [--skip-if-exists]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent

# Source run directories
_BASE_RUN = _REPO / "outputs/stage4_8/runs/run_array_20260611_0109"
_EXT2_RUN = _REPO / "outputs/stage4_8/runs/run_array_extension2_20260612_012052"
_EXT3_RUN = _REPO / "outputs/stage4_8/runs/run_array_extension3_20260613_021039"

# Combined output directory
_COMBINED_RUN = _REPO / "outputs/stage4_8/runs/run_combined_all_goals"


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def merge_run_summaries(out_dir: Path) -> int:
    all_rows = []
    seen_run_ids = set()
    for src_dir, label in [(_BASE_RUN, "base"), (_EXT2_RUN, "ext2"), (_EXT3_RUN, "ext3")]:
        p = src_dir / "run_summary.jsonl"
        rows = _load_jsonl(p)
        new = 0
        for r in rows:
            rid = r.get("run_id", "")
            if rid not in seen_run_ids:
                seen_run_ids.add(rid)
                all_rows.append(r)
                new += 1
        print(f"  {label}: {new} unique rows from {p}")
    _write_jsonl(out_dir / "run_summary.jsonl", all_rows)
    print(f"  Combined run_summary.jsonl: {len(all_rows)} rows")
    return len(all_rows)


def merge_projections(out_dir: Path) -> int:
    repr_dir = out_dir / "representations"
    repr_dir.mkdir(exist_ok=True)

    # 1. Merge projection_summary.jsonl
    all_proj = []
    seen_run_ids = set()
    for src_dir, label in [(_BASE_RUN, "base"), (_EXT2_RUN, "ext2"), (_EXT3_RUN, "ext3")]:
        p = src_dir / "representations" / "projection_summary.jsonl"
        rows = _load_jsonl(p)
        new = 0
        for r in rows:
            rid = r.get("run_id", "")
            if rid not in seen_run_ids:
                seen_run_ids.add(rid)
                all_proj.append(r)
                new += 1
        print(f"  {label}: {new} unique projection rows from {p}")
    _write_jsonl(repr_dir / "projection_summary.jsonl", all_proj)

    # 2. Copy per-example JSON files
    n_copied = 0
    for src_dir, label in [(_BASE_RUN, "base"), (_EXT2_RUN, "ext2"), (_EXT3_RUN, "ext3")]:
        src_repr = src_dir / "representations"
        if not src_repr.exists():
            print(f"  WARNING: {label} has no representations/ dir — skipping per-example files")
            continue
        for json_file in src_repr.glob("*_projection.json"):
            dst = repr_dir / json_file.name
            if not dst.exists():
                shutil.copy2(json_file, dst)
                n_copied += 1
    print(f"  Copied {n_copied} per-example JSON files to {repr_dir}")
    return len(all_proj)


def run_analysis(out_dir: Path) -> None:
    print("\n=== Running analyze_repeated_generations ===")
    subprocess.run(
        [sys.executable, "-m", "poc_stage4_8.analyze_repeated_generations",
         "--run-dir", str(out_dir)],
        check=True, cwd=_REPO
    )

    # Check matched cells
    matched_csv = out_dir / "analysis" / "matched_outcome_cells.csv"
    if matched_csv.exists():
        import csv
        matched = list(csv.DictReader(open(matched_csv)))
        print(f"  Matched outcome cells: {len(matched)}")
        if len(matched) >= 4:
            print("\n=== Running extract_behavior_conditioned_direction ===")
            subprocess.run(
                [sys.executable, "-m", "poc_stage4_8.extract_behavior_conditioned_direction",
                 "--run-dir", str(out_dir)],
                check=True, cwd=_REPO
            )
        else:
            print(f"  WARNING: only {len(matched)} matched cells (need ≥4)")
    else:
        print("  WARNING: matched_outcome_cells.csv not found")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-if-exists", action="store_true",
                        help="Skip if combined run already has direction results")
    args = parser.parse_args()

    if args.skip_if_exists:
        dir_results = _COMBINED_RUN / "direction_analysis" / "direction_results.json"
        if dir_results.exists():
            print(f"Combined direction results already exist at {dir_results}. Skipping.")
            return

    # Check extension v3 representations exist
    ext3_repr = _EXT3_RUN / "representations" / "projection_summary.jsonl"
    if not ext3_repr.exists():
        print("ERROR: Extension v3 representations not found.")
        print(f"  Expected: {ext3_repr}")
        print("  Run representation extraction first:")
        print(f"  RUN_DIR=outputs/stage4_8/runs/run_array_extension3_20260613_021039 sbatch slurm_scripts/stage4_8_compute_representations.slurm")
        sys.exit(1)

    print(f"Creating combined run dir: {_COMBINED_RUN}")
    _COMBINED_RUN.mkdir(parents=True, exist_ok=True)

    print("\n=== Merging run summaries ===")
    n_summary = merge_run_summaries(_COMBINED_RUN)

    print("\n=== Merging representations ===")
    n_proj = merge_projections(_COMBINED_RUN)

    # Write metadata
    meta = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n_run_summary_rows": n_summary,
        "n_projection_rows": n_proj,
        "source_dirs": {
            "base": str(_BASE_RUN),
            "extension_v2": str(_EXT2_RUN),
            "extension_v3": str(_EXT3_RUN),
        },
        "goals_expected": [0, 1, 2, 3],
        "seeds_expected": list(range(101, 126)),
        "purpose": "Combined 4-goal direction extraction (base + ext_v2 + ext_v3)",
    }
    (_COMBINED_RUN / "combined_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"\nCombined dir: {_COMBINED_RUN}")
    print(f"  run_summary rows: {n_summary}")
    print(f"  projection rows:  {n_proj}")

    run_analysis(_COMBINED_RUN)
    print("\n=== Combined Stage 4.8 analysis complete ===")
    dir_results = _COMBINED_RUN / "direction_analysis" / "direction_results.json"
    if dir_results.exists():
        r = json.loads(dir_results.read_text())
        print(f"Direction result: AUC={r.get('mean_auc', 'N/A')} p={r.get('permutation_p', 'N/A')}")


if __name__ == "__main__":
    main()
