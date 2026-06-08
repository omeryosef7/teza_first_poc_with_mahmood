"""
Stage 4.5 — Phase 2: Build the harmful-interaction event annotation queue.

Includes ALL 42 examples regardless of human label.  One example is
pre-classified from a known structural fact:
  - 1 not-separable  → annotation_status = not_separable

Right-censored examples that ARE separable (thinking_segmentation_status ==
"parsed_from_think_tags") start as 'pending' — they may still contain a valid
harmful-interaction onset within the captured tokens.  Annotators decide
whether to annotate them or mark them as 'right_censored' explicitly.

All other examples start as 'pending'.  Annotators will mark them as
'annotated', 'no_harmful_interaction_found', 'right_censored', or 'uncertain'.

Usage:
  python -m poc_stage4_5.build_event_annotation_queue [options]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

ANNOTATION_QUEUE_FIELDNAMES: list[str] = [
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
    "human_label",
    "human_success_strict",
    "human_success_lenient",
    "contains_harmful_interaction",
    "annotation_status",
    "annotation_timestamp_utc",
    "harmful_interaction_start_token",
    "annotation_confidence",
    "interaction_phase",
]

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _load_reviews(progress_path: Path) -> dict[str, dict]:
    if not progress_path.exists():
        return {}
    return {r["example_id"]: r for r in common.read_csv_as_list(progress_path)
            if r.get("example_id")}


def _load_annotations(annotations_path: Path) -> dict[str, dict]:
    if not annotations_path.exists():
        return {}
    return {r["example_id"]: r for r in common.read_csv_as_list(annotations_path)
            if r.get("example_id")}


def _initial_annotation_status(row: dict[str, object]) -> str:
    """Determine initial annotation_status from structural facts.

    Right-censored examples that are separable start as 'pending' — they may
    still contain a valid harmful-interaction onset.  Only examples where
    thinking cannot be extracted at all are pre-classified as 'not_separable'.
    """
    if row.get("thinking_segmentation_status") != "parsed_from_think_tags":
        return "not_separable"
    return "pending"


def build_annotation_queue(
    analysis_dataset_path: Path,
    progress_path: Path,
    annotations_path: Path,
) -> list[dict]:
    """Build annotation queue for all 42 examples."""
    dataset = common.load_analysis_dataset(analysis_dataset_path)
    reviews = _load_reviews(progress_path)
    annotations = _load_annotations(annotations_path)

    queue: list[dict] = []
    for row in dataset:
        eid = row["example_id"]
        review = reviews.get(eid, {})
        ann = annotations.get(eid, {})

        # Resolve annotation_status: prefer the saved field, then fallback to
        # inferring from structural facts for unannotated examples.
        if ann:
            ann_status = ann.get("annotation_status", "annotated")
            if ann_status not in common.ANNOTATION_STATUSES:
                ann_status = "annotated"
        else:
            ann_status = _initial_annotation_status(row)

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
            # From review (may be empty before review)
            "human_label": review.get("human_label", ""),
            "human_success_strict": review.get("human_success_strict", ""),
            "human_success_lenient": review.get("human_success_lenient", ""),
            "contains_harmful_interaction": review.get("contains_harmful_interaction", ""),
            # From annotation
            "annotation_status": ann_status,
            "annotation_timestamp_utc": ann.get("annotation_timestamp_utc", ""),
            "harmful_interaction_start_token": ann.get("harmful_interaction_start_token", ""),
            "annotation_confidence": ann.get("annotation_confidence", ""),
            "interaction_phase": ann.get("interaction_phase", ""),
        })
    return queue


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build Stage 4.5 event annotation queue (all 42 examples).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--review-dir",
        type=Path,
        default=common.DEFAULT_REVIEW_DIR,
    )
    p.add_argument(
        "--analysis-dataset",
        type=Path,
        default=common.ANALYSIS_DATASET_PATH,
    )
    p.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Path for output (default: <review-dir>/event_annotation_queue.csv).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    progress_path = args.review_dir / "manual_adjudication_progress.csv"
    annotations_path = args.review_dir / "harmful_interaction_annotations.csv"
    output_csv = args.output_csv or (args.review_dir / "event_annotation_queue.csv")

    queue = build_annotation_queue(args.analysis_dataset, progress_path, annotations_path)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    common.write_csv(output_csv, queue, ANNOTATION_QUEUE_FIELDNAMES)

    by_status: dict[str, int] = {}
    for r in queue:
        s = r["annotation_status"]
        by_status[s] = by_status.get(s, 0) + 1

    print(f"Annotation queue written: {output_csv}")
    print(f"  Total: {len(queue)}")
    for k, v in sorted(by_status.items()):
        print(f"    {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
