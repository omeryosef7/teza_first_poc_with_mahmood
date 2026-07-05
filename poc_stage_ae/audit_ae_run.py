"""
Stage 7 — Completion audit / resume-target computation for the AE run.

Loads the manifest(s) as the expected row_key set, scans generation shard
files (and optionally hidden-state / scoring outputs) for completed row_keys,
and reports missing/incomplete counts per (model, condition, goal_index) as a
table. Writes `resume_targets.jsonl` (rows: model, condition, goal_index — the
SLURM array indices that still need (re)submission) and a human-readable
summary to stdout plus `completion_audit.json`.

Usage:
  python -m poc_stage_ae.audit_ae_run \
      --manifest <path to model_ae_manifest.jsonl (repeatable, or a directory)> \
      --generation-dir <RUN_DIR> \
      [--hidden-states-dir <RUN_DIR>] [--scoring-dir <RUN_DIR>] \
      --output <RUN_DIR>/status
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_CONDITIONS = ["A", "D", "E", "G"]


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _resolve_manifest_paths(manifest_args: list[Path]) -> list[Path]:
    resolved = []
    for p in manifest_args:
        if p.is_dir():
            resolved.extend(sorted(p.glob("*_ae_manifest.jsonl")))
        else:
            resolved.append(p)
    return resolved


def _scan_generation_shards(generation_dir: Path) -> set[str]:
    """Return the set of row_keys with status == 'ok' across all shard files."""
    completed: set[str] = set()
    shards_dir = generation_dir / "shards"
    if not shards_dir.exists():
        return completed
    for shard_path in shards_dir.glob("*.jsonl"):
        for row in _load_jsonl(shard_path):
            if row.get("status") == "ok" and row.get("row_key"):
                completed.add(row["row_key"])
    return completed


def _scan_hidden_states(hidden_states_dir: Path) -> set[str]:
    completed: set[str] = set()
    shards_dir = hidden_states_dir / "hidden_states" / "shards"
    if not shards_dir.exists():
        return completed
    for csv_path in shards_dir.glob("*_metadata.csv"):
        import csv as csv_mod
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv_mod.DictReader(f):
                if row.get("row_key"):
                    completed.add(row["row_key"])
    try:
        import pandas as pd
        for pq_path in shards_dir.glob("*_metadata.parquet"):
            df = pd.read_parquet(pq_path)
            completed.update(df["row_key"].unique().tolist())
    except ImportError:
        pass
    return completed


def _scan_scoring(scoring_dir: Path) -> set[str]:
    completed: set[str] = set()
    sdir = scoring_dir / "scoring"
    if not sdir.exists():
        return completed
    for path in sdir.glob("*_scores.jsonl"):
        for row in _load_jsonl(path):
            if row.get("row_key") and row.get("strongreject_status") not in (None,):
                completed.add(row["row_key"])
    return completed


def run_audit(
    *,
    manifest_paths: list[Path],
    generation_dir: Path,
    hidden_states_dir: Path | None,
    scoring_dir: Path | None,
    output_dir: Path,
) -> dict[str, Any]:
    expected_rows: list[dict] = []
    for mp in manifest_paths:
        expected_rows.extend(_load_jsonl(mp))

    expected_by_cell: dict[tuple[str, str, int], list[str]] = defaultdict(list)
    for row in expected_rows:
        cell = (row["model"], row["condition"], int(row["goal_index"]))
        expected_by_cell[cell].append(row["row_key"])

    completed_gen = _scan_generation_shards(generation_dir)
    completed_hidden = _scan_hidden_states(hidden_states_dir) if hidden_states_dir else set()
    completed_scoring = _scan_scoring(scoring_dir) if scoring_dir else set()

    table_rows = []
    resume_targets = []
    total_expected = total_completed_gen = 0

    for (model, condition, goal_index), row_keys in sorted(expected_by_cell.items()):
        n_expected = len(row_keys)
        n_done_gen = sum(1 for rk in row_keys if rk in completed_gen)
        n_done_hidden = sum(1 for rk in row_keys if rk in completed_hidden) if hidden_states_dir else None
        n_done_scoring = sum(1 for rk in row_keys if rk in completed_scoring) if scoring_dir else None

        total_expected += n_expected
        total_completed_gen += n_done_gen

        table_rows.append({
            "model": model,
            "condition": condition,
            "goal_index": goal_index,
            "n_expected": n_expected,
            "n_generation_done": n_done_gen,
            "n_hidden_states_done": n_done_hidden,
            "n_scoring_done": n_done_scoring,
            "generation_complete": n_done_gen == n_expected,
        })

        if n_done_gen < n_expected:
            resume_targets.append({"model": model, "condition": condition, "goal_index": goal_index,
                                    "n_missing": n_expected - n_done_gen})

    output_dir.mkdir(parents=True, exist_ok=True)
    resume_path = output_dir / "resume_targets.jsonl"
    with open(resume_path, "w", encoding="utf-8") as f:
        for row in resume_targets:
            f.write(json.dumps(row) + "\n")

    audit_summary = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_paths": [str(p) for p in manifest_paths],
        "generation_dir": str(generation_dir),
        "hidden_states_dir": str(hidden_states_dir) if hidden_states_dir else None,
        "scoring_dir": str(scoring_dir) if scoring_dir else None,
        "total_expected_rows": total_expected,
        "total_generation_completed_rows": total_completed_gen,
        "total_missing_rows": total_expected - total_completed_gen,
        "n_cells_incomplete": len(resume_targets),
        "n_cells_total": len(table_rows),
        "cells": table_rows,
    }
    audit_json_path = output_dir / "completion_audit.json"
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
        f.write("\n")

    # Human-readable stdout table
    print(f"{'model':<8} {'cond':<5} {'goal':<5} {'expected':<9} {'gen_done':<9} {'hidden':<8} {'scoring':<8} {'complete'}")
    for row in table_rows:
        print(
            f"{row['model']:<8} {row['condition']:<5} {row['goal_index']:<5} "
            f"{row['n_expected']:<9} {row['n_generation_done']:<9} "
            f"{str(row['n_hidden_states_done']):<8} {str(row['n_scoring_done']):<8} "
            f"{row['generation_complete']}"
        )
    print()
    print(f"TOTAL expected={total_expected} generation_completed={total_completed_gen} "
          f"missing={total_expected - total_completed_gen} incomplete_cells={len(resume_targets)}/{len(table_rows)}")
    print(f"Resume targets -> {resume_path}")
    print(f"Full audit -> {audit_json_path}")

    return audit_summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage 7 — completion audit / resume-target computation.")
    p.add_argument("--manifest", required=True, type=Path, action="append",
                    help="Manifest JSONL path or directory (repeatable).")
    p.add_argument("--generation-dir", required=True, type=Path)
    p.add_argument("--hidden-states-dir", type=Path, default=None)
    p.add_argument("--scoring-dir", type=Path, default=None)
    p.add_argument("--output", type=Path, default=None,
                    help="Output directory for resume_targets.jsonl / completion_audit.json. "
                         "Default: <generation-dir>/status")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_paths = _resolve_manifest_paths(args.manifest)
    if not manifest_paths:
        print("ERROR: no manifest files resolved from --manifest", file=sys.stderr)
        return 1
    output_dir = args.output or (args.generation_dir / "status")
    run_audit(
        manifest_paths=manifest_paths,
        generation_dir=args.generation_dir,
        hidden_states_dir=args.hidden_states_dir,
        scoring_dir=args.scoring_dir,
        output_dir=output_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
