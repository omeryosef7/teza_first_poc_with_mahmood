"""
Stage 4.5 — Phase 1: Build manual adjudication queue.

Reads analysis_dataset.csv (42 rows) and creates:
  review/manual_adjudication_queue.csv   — 42-row queue, one per example
  review/queue_manifest.json             — summary counts and timestamp

Usage:
  python -m poc_stage4_5.build_manual_adjudication_queue [options]

The queue CSV is idempotent: re-running refreshes review_status from the
current state of manual_adjudication_progress.csv but never overwrites the
progress file or any frozen Stage 4 artifact.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repo root is importable when run directly
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

QUEUE_FIELDNAMES: list[str] = [
    "example_id",
    "goal_index",
    "attack_iteration",
    "conversation_id",
    "target_model",
    "strongreject_score",
    "sr_success",
    "judge_score",
    "judge_success",
    "think_token_count",
    "generation_token_count",
    "right_censored",
    "usable_for_think_analysis",
    "thinking_segmentation_status",
    "stage6_trace_path",
    "stage4_per_example_path",
    "review_status",
    "review_timestamp_utc",
    "reviewer_notes",
]


# ---------------------------------------------------------------------------
# Core logic (importable by tests)
# ---------------------------------------------------------------------------

def load_completed_reviews(progress_path: Path) -> dict[str, dict]:
    """Return dict keyed by example_id from manual_adjudication_progress.csv."""
    if not progress_path.exists():
        return {}
    rows = common.read_csv_as_list(progress_path)
    return {r["example_id"]: r for r in rows if r.get("example_id")}


def build_queue(
    analysis_dataset_path: Path,
    progress_path: Path,
) -> list[dict]:
    """Build the 42-row queue, merging review status from progress file."""
    dataset = common.load_analysis_dataset(analysis_dataset_path)
    completed = load_completed_reviews(progress_path)

    queue: list[dict] = []
    for row in dataset:
        eid = row["example_id"]
        is_done = eid in completed
        progress_row = completed.get(eid, {})
        queue.append({
            "example_id": eid,
            "goal_index": row["goal_index"],
            "attack_iteration": row["attack_iteration"],
            "conversation_id": row["conversation_id"],
            "target_model": row.get("target_model", ""),
            "strongreject_score": row["strongreject_score"],
            "sr_success": row["sr_success"],
            "judge_score": row.get("judge_score", ""),
            "judge_success": row["judge_success"],
            "think_token_count": row["think_token_count"],
            "generation_token_count": row.get("generation_token_count", ""),
            "right_censored": row["right_censored"],
            "usable_for_think_analysis": row["usable_for_think_analysis"],
            "thinking_segmentation_status": row.get("thinking_segmentation_status", ""),
            "stage6_trace_path": row.get("stage6_trace_path", ""),
            "stage4_per_example_path": row.get("stage4_per_example_path", ""),
            "review_status": "completed" if is_done else "pending",
            "review_timestamp_utc": progress_row.get("review_timestamp_utc", ""),
            "reviewer_notes": progress_row.get("reviewer_notes", ""),
        })
    return queue


def write_queue(queue: list[dict], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    common.write_csv(output_csv, queue, QUEUE_FIELDNAMES)


def write_manifest(
    queue: list[dict],
    output_json: Path,
    analysis_dataset_path: Path,
) -> None:
    n_total = len(queue)
    n_completed = sum(1 for r in queue if r["review_status"] == "completed")
    manifest = {
        "artifact_version": "adjudication_queue_v1",
        "created_utc": common.utc_now(),
        "analysis_dataset_path": str(analysis_dataset_path),
        "n_total": n_total,
        "n_completed": n_completed,
        "n_pending": n_total - n_completed,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    common.atomic_write_json(output_json, manifest)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build Stage 4.5 manual adjudication review queue.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--analysis-dataset",
        type=Path,
        default=common.ANALYSIS_DATASET_PATH,
        help="Path to analysis_dataset.csv from Stage 4.",
    )
    p.add_argument(
        "--review-dir",
        type=Path,
        default=common.DEFAULT_REVIEW_DIR,
        help="Directory for persistent review files.",
    )
    p.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Path for output queue CSV (default: <review-dir>/manual_adjudication_queue.csv).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.analysis_dataset.exists():
        print(f"ERROR: analysis_dataset not found: {args.analysis_dataset}", file=sys.stderr)
        return 1

    progress_path = args.review_dir / "manual_adjudication_progress.csv"
    output_csv = args.output_csv or (args.review_dir / "manual_adjudication_queue.csv")
    output_manifest = args.review_dir / "queue_manifest.json"

    queue = build_queue(args.analysis_dataset, progress_path)
    write_queue(queue, output_csv)
    write_manifest(queue, output_manifest, args.analysis_dataset)

    n_completed = sum(1 for r in queue if r["review_status"] == "completed")
    print(
        f"Queue written: {output_csv}\n"
        f"  Total examples : {len(queue)}\n"
        f"  Completed      : {n_completed}\n"
        f"  Pending        : {len(queue) - n_completed}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
