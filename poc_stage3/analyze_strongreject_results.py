from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from poc_stage3.strongreject_scoring import (
    DEFAULT_STRONGREJECT_THRESHOLD,
    build_summary,
    load_json,
    load_jsonl,
    truncate_text,
    validate_scored_rows,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze Stage 3 StrongREJECT scored artifacts and print a concise report."
    )
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--summary-json")
    parser.add_argument("--threshold", type=float, default=DEFAULT_STRONGREJECT_THRESHOLD)
    parser.add_argument("--output-json")
    return parser


def _usable_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if isinstance(row.get("strongreject_score"), (int, float))]


def _goal_rows(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["goal_index"])].append(row)
    return grouped


def print_report(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    usable_rows = _usable_rows(rows)
    validate_scored_rows(rows, threshold=threshold)

    success_rows = [row for row in usable_rows if bool(row.get("is_success"))]
    failure_rows = [row for row in usable_rows if not bool(row.get("is_success"))]

    summary = build_summary(
        input_jsonl="<in-memory>",
        output_jsonl="<in-memory>",
        scored_rows=rows,
        evaluator=str(rows[0].get("strongreject_evaluator", "unknown")) if rows else "unknown",
        threshold=threshold,
    )

    print("Stage 3 StrongREJECT analysis")
    print(f"Rows loaded: {len(rows)}")
    print(f"Usable scored rows: {len(usable_rows)}")
    print(f"Mean score: {summary['global_score_summary']['strongreject_score_mean']}")
    print(f"Median score: {summary['global_score_summary']['strongreject_score_median']}")
    print(f"Mean score for Hijacking-success rows: {summary['by_hijacking_success']['true']['mean']}")
    print(f"Mean score for Hijacking-failure rows: {summary['by_hijacking_success']['false']['mean']}")

    confusion = summary["agreement_analysis"]["confusion"]
    print("Agreement counts:")
    for key, value in confusion.items():
        print(f"  {key}: {value}")

    print("Per-goal summary:")
    for goal in summary["goal_level_analysis"]:
        print(
            f"  goal_index={goal['goal_index']} rows={goal['num_rows']} "
            f"success_rows={goal['num_hijacking_success_rows']} "
            f"mean={goal['mean_strongreject_score']} max={goal['max_strongreject_score']} "
            f"best_conversation_id={goal['best_response_conversation_id']} "
            f"best_iteration={goal['best_response_iteration']}"
        )

    print("Top-scoring row per goal:")
    for goal_index, goal_rows in sorted(_goal_rows(usable_rows).items()):
        best_row = max(goal_rows, key=lambda row: float(row["strongreject_score"]))
        print(
            f"  goal_index={goal_index} conversation_id={best_row.get('conversation_id')} "
            f"iteration={best_row.get('attack_iteration')} score={best_row.get('strongreject_score')} "
            f"is_success={best_row.get('is_success')} preview={truncate_text(str(best_row.get('goal', '')), 80)}"
        )

    if success_rows:
        all_high = all(float(row["strongreject_score"]) >= threshold for row in success_rows)
        print(f"All Hijacking-success rows above threshold {threshold}: {all_high}")
    if failure_rows:
        any_high_failure = any(float(row["strongreject_score"]) >= threshold for row in failure_rows)
        print(f"Any Hijacking-failure rows above threshold {threshold}: {any_high_failure}")

    return summary


def main() -> int:
    args = build_parser().parse_args()
    rows = load_jsonl(args.input_jsonl)
    summary = print_report(rows, threshold=args.threshold)

    if args.summary_json:
        summary_path = Path(args.summary_json)
        if summary_path.exists():
            existing = load_json(summary_path)
            print("Summary JSON compared with provided file:")
            print(f"  existing keys: {sorted(existing.keys())}")
        else:
            print(f"Summary JSON file not found: {summary_path}")

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        print(f"Wrote analysis JSON: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())