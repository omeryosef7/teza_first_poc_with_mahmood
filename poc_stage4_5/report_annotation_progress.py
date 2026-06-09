"""
Stage 4.5 — Report annotation progress.

Non-interactive summary command.  Reads the persistent review files and
prints a structured progress report without modifying any file.

Usage:
  python -m poc_stage4_5.report_annotation_progress [--review-dir DIR]
  python -m poc_stage4_5.report_annotation_progress --queue review/pilot_example_queue.csv
  python -m poc_stage4_5.report_annotation_progress --queue review/pilot_example_queue.csv --json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common


def _count_by(rows: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        key = str(r.get(field, ""))
        counts[key] = counts.get(key, 0) + 1
    return counts


def report_progress(
    review_dir: Path,
    analysis_dataset_path: Path,
    queue_path: Path | None = None,
) -> dict:
    """
    Compute progress counts from persistent review files.

    When queue_path is provided, all counts are restricted to the example IDs
    listed in that CSV (pilot mode).  The total is set to the queue size.

    Returns a dict with keys:
      manual_review: {total, completed, pending, strict_successes,
                      lenient_successes, label_counts, reviewer_ids}
      event_annotation: {total, annotated, no_harmful_interaction_found,
                         uncertain, not_separable, right_censored,
                         pending, think_phase, final_phase, special_phase,
                         high_confidence, medium_confidence, low_confidence}
      is_pilot: bool
    """
    progress_path = review_dir / "manual_adjudication_progress.csv"
    annotations_path = review_dir / "harmful_interaction_annotations.csv"

    # Resolve pilot / queue IDs
    pilot_ids: set[str] | None = None
    is_pilot = queue_path is not None
    if queue_path is not None:
        pilot_ids = {
            r["example_id"]
            for r in common.read_csv_as_list(queue_path)
            if r.get("example_id")
        }

    # Total: queue size when restricted, else full dataset
    if pilot_ids is not None:
        n_total = len(pilot_ids)
    else:
        try:
            dataset = common.load_analysis_dataset(analysis_dataset_path)
            n_total = len(dataset)
        except Exception:
            n_total = 42  # fallback

    # --- Manual review ---
    reviews: list[dict] = []
    if progress_path.exists():
        all_reviews = common.read_csv_as_list(progress_path)
        reviews = (
            [r for r in all_reviews if r.get("example_id") in pilot_ids]
            if pilot_ids is not None
            else all_reviews
        )

    n_reviews = len(reviews)
    n_review_pending = max(0, n_total - n_reviews)
    n_strict = sum(
        1 for r in reviews
        if str(r.get("human_success_strict", "")).lower() == "true"
    )
    n_lenient = sum(
        1 for r in reviews
        if str(r.get("human_success_lenient", "")).lower() == "true"
    )
    label_counts = _count_by(reviews, "human_label")
    reviewer_ids = sorted({r.get("reviewer_id", "") for r in reviews} - {""})

    # --- Event annotation ---
    annotations: list[dict] = []
    if annotations_path.exists():
        all_anns = common.read_csv_as_list(annotations_path)
        annotations = (
            [r for r in all_anns if r.get("example_id") in pilot_ids]
            if pilot_ids is not None
            else all_anns
        )

    # Build status counts using the event queue (handles unannotated examples too)
    from poc_stage4_5.build_event_annotation_queue import build_annotation_queue
    queue = build_annotation_queue(analysis_dataset_path, progress_path, annotations_path)
    if pilot_ids is not None:
        queue = [r for r in queue if r.get("example_id") in pilot_ids]

    status_counts = _count_by(queue, "annotation_status")

    n_annotated = status_counts.get("annotated", 0)
    n_no_harmful = status_counts.get("no_harmful_interaction_found", 0)
    n_uncertain = status_counts.get("uncertain", 0)
    n_not_separable = status_counts.get("not_separable", 0)
    n_right_censored = status_counts.get("right_censored", 0)
    n_ann_pending = status_counts.get("pending", 0)

    # Phase breakdown (from annotation records only when status == annotated)
    annotated_rows = [r for r in annotations if r.get("annotation_status") == "annotated"]
    n_think_phase = sum(
        1 for r in annotated_rows if r.get("interaction_phase") == "think"
    )
    n_final_phase = sum(
        1 for r in annotated_rows if r.get("interaction_phase") == "final"
    )
    n_special_phase = sum(
        1 for r in annotated_rows if r.get("interaction_phase") == "special"
    )

    # Confidence breakdown
    n_high = sum(
        1 for r in annotations if r.get("annotation_confidence") == "high"
    )
    n_medium = sum(
        1 for r in annotations if r.get("annotation_confidence") == "medium"
    )
    n_low = sum(
        1 for r in annotations if r.get("annotation_confidence") == "low"
    )

    return {
        "is_pilot": is_pilot,
        "manual_review": {
            "total": n_total,
            "completed": n_reviews,
            "pending": n_review_pending,
            "strict_successes": n_strict,
            "lenient_successes": n_lenient,
            "label_counts": label_counts,
            "reviewer_ids": reviewer_ids,
        },
        "event_annotation": {
            "total": n_total,
            "annotated": n_annotated,
            "no_harmful_interaction_found": n_no_harmful,
            "uncertain": n_uncertain,
            "not_separable": n_not_separable,
            "right_censored": n_right_censored,
            "pending": n_ann_pending,
            "think_phase": n_think_phase,
            "final_phase": n_final_phase,
            "special_phase": n_special_phase,
            "high_confidence": n_high,
            "medium_confidence": n_medium,
            "low_confidence": n_low,
        },
    }


def print_report(data: dict) -> None:
    mr = data["manual_review"]
    ea = data["event_annotation"]
    is_pilot = data.get("is_pilot", False)

    sep = "-" * 60

    scope = "PILOT" if is_pilot else "FULL DATASET"
    print(sep)
    print(f"MANUAL ADJUDICATION PROGRESS  ({scope})")
    print(sep)
    pilot_prefix = "Pilot " if is_pilot else ""
    print(f"  {pilot_prefix}Manual reviews completed : {mr['completed']} / {mr['total']}")
    print(f"  Pending   : {mr['pending']}")
    print(f"  Strict successes  (human_success_strict=True)  : {mr['strict_successes']}")
    print(f"  Lenient successes (human_success_lenient=True) : {mr['lenient_successes']}")
    if mr["reviewer_ids"]:
        print(f"  Reviewer IDs : {', '.join(mr['reviewer_ids'])}")
    if mr["label_counts"]:
        print("  Label counts (harmful-interaction labels):")
        for lbl in ("yes", "no", "ambiguous"):
            cnt = mr["label_counts"].get(lbl, 0)
            print(f"    {lbl:<10s} {cnt:3d}")
        # Any unexpected labels
        for lbl, cnt in sorted(mr["label_counts"].items()):
            if lbl and lbl not in ("yes", "no", "ambiguous"):
                print(f"    {lbl:<42s} {cnt:3d}  [unexpected label]")

    print()
    print(sep)
    print(f"EVENT ANNOTATION PROGRESS  ({scope})")
    print(sep)
    print(f"  Total examples      : {ea['total']}")
    print(f"  Pending annotation  : {ea['pending']}")
    print(f"  Annotated           : {ea['annotated']}")
    if ea["annotated"] > 0:
        print(f"    think-phase onset        : {ea['think_phase']}")
        print(f"    final-phase onset        : {ea['final_phase']}")
        print(f"    special-token-region onset: {ea['special_phase']}")
    print(f"  No harmful interaction found : {ea['no_harmful_interaction_found']}")
    print(f"  Uncertain           : {ea['uncertain']}")
    print(f"  Not separable       : {ea['not_separable']}")
    print(f"  Right-censored      : {ea['right_censored']}")
    if ea["annotated"] > 0:
        print(f"  Confidence (annotated rows):")
        print(f"    high   : {ea['high_confidence']}")
        print(f"    medium : {ea['medium_confidence']}")
        print(f"    low    : {ea['low_confidence']}")
    print(sep)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Report Stage 4.5 annotation progress (read-only).",
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
        "--queue",
        type=Path,
        default=None,
        help="CSV with example_id column; restrict report to these examples "
             "(e.g. review/pilot_example_queue.csv).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output machine-readable JSON instead of formatted text.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data = report_progress(args.review_dir, args.analysis_dataset, args.queue)
    if args.json:
        import json
        print(json.dumps(data, indent=2))
    else:
        print_report(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
