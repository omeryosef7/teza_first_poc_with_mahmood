"""
Stage 4.8 — Select 4 source prompts for repeated-generation study.

Selection criteria:
  - One per goal (0–3)
  - Non-censored in Stage 4.7 condition A (finish_reason == eos_token)
  - Valid think/final segmentation (thinking_segmentation_status == parsed_from_think_tags)
  - Deterministic: tie-breaking by "interest score" (distance of sr_score from 0.5,
    ascending — prefer intermediate behavior), then middle stratum, then conversation_id

Records all rejected alternatives with reasons.

Output:
  outputs/stage4_8/source_prompt_selection.csv
  outputs/stage4_8/source_prompt_selection_manifest.json

Usage:
  python -m poc_stage4_8.select_source_prompts
      [--stage47-run-dir outputs/stage4_7/runs/run_array_20260610_1442]
      [--output-dir outputs/stage4_8]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_STAGE47_RUN_DIR = (
    _REPO_ROOT / "outputs" / "stage4_7" / "runs" / "run_array_20260610_1442"
)
_OUTPUT_DIR = _REPO_ROOT / "outputs" / "stage4_8"
_SEEDS = [101, 102, 103, 104, 105]
_CONDITIONS = ["A", "D", "F"]
_GOALS = [0, 1, 2, 3]


def _f(x, default=float("nan")) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _interest_score(sr_score: float) -> float:
    """Lower score = more interesting (closer to 0.5 → more uncertain)."""
    if math.isnan(sr_score):
        return 1.0  # prefer rows with known scores
    return abs(sr_score - 0.5)


def select_prompts(run_dir: Path) -> tuple[list[dict], list[dict]]:
    """
    Returns (selected_rows, all_eligible_rows_with_rejection_reason).
    selected_rows: one per goal, sorted by goal_index.
    """
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        # Try canonical CSV
        canon_path = run_dir / "analysis" / "canonical_per_run_results.csv"
        if canon_path.exists():
            with open(canon_path, encoding="utf-8") as f:
                all_rows = list(csv.DictReader(f))
        else:
            raise FileNotFoundError(f"Neither run_summary.jsonl nor canonical CSV found in {run_dir}")
    else:
        with open(summary_path, encoding="utf-8") as f:
            all_rows = [json.loads(l) for l in f if l.strip()]

    # Filter: condition A, eos_token, parsed_from_think_tags
    eligible = []
    for r in all_rows:
        if r.get("condition") != "A":
            continue
        if r.get("finish_reason") != "eos_token":
            continue
        if r.get("thinking_segmentation_status") != "parsed_from_think_tags":
            continue
        eligible.append(r)

    selected = []
    all_with_reason = []

    for goal in _GOALS:
        goal_eligible = [r for r in eligible if int(_f(r.get("goal_index", -1))) == goal]
        if not goal_eligible:
            raise ValueError(f"No eligible rows for goal {goal}")

        # Sort by interest (ascending interest_score = most intermediate first),
        # then by selection_stratum == "middle" (prefer middle),
        # then by conversation_id (for determinism)
        def _sort_key(r):
            sr = _f(r.get("strongreject_score", float("nan")))
            interest = _interest_score(sr)
            is_not_middle = 0 if r.get("selection_stratum") == "middle" else 1
            conv_id = str(r.get("conversation_id", r.get("source_example_id", "")))
            return (interest, is_not_middle, conv_id)

        goal_eligible_sorted = sorted(goal_eligible, key=_sort_key)

        winner = goal_eligible_sorted[0]
        selected.append(winner)

        # Record all candidates with rejection reason
        for i, r in enumerate(goal_eligible_sorted):
            reason = "selected" if i == 0 else f"rejected_rank_{i+1}_interest={_interest_score(_f(r.get('strongreject_score',float('nan')))):.3f}"
            all_with_reason.append({
                "goal_index": goal,
                "source_example_id": r.get("source_example_id"),
                "selection_stratum": r.get("selection_stratum"),
                "sr_success": r.get("sr_success"),
                "strongreject_score": r.get("strongreject_score"),
                "think_token_count": r.get("think_token_count"),
                "finish_reason": r.get("finish_reason"),
                "thinking_segmentation_status": r.get("thinking_segmentation_status"),
                "interest_score": _interest_score(_f(r.get("strongreject_score", float("nan")))),
                "disposition": reason,
            })

    return selected, all_with_reason


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Select Stage 4.8 source prompts.")
    p.add_argument("--stage47-run-dir", type=Path, default=_STAGE47_RUN_DIR)
    p.add_argument("--output-dir", type=Path, default=_OUTPUT_DIR)
    args = p.parse_args(argv)

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading Stage 4.7 results from {args.stage47_run_dir} ...")
    selected, all_candidates = select_prompts(args.stage47_run_dir)

    print(f"\nSelected {len(selected)} source prompts (1 per goal):")
    for r in selected:
        print(
            f"  goal={r.get('goal_index')} | {r.get('source_example_id')} | "
            f"stratum={r.get('selection_stratum')} | "
            f"sr_success={r.get('sr_success')} | sr_score={r.get('strongreject_score')} | "
            f"think_tok={r.get('think_token_count')}"
        )

    # Validate: exactly 4, one per goal
    assert len(selected) == 4, f"Expected 4 selected, got {len(selected)}"
    goals_selected = [int(_f(r.get("goal_index", -1))) for r in selected]
    assert sorted(goals_selected) == _GOALS, f"Goals mismatch: {goals_selected}"
    # Check distinct source IDs
    ids = [r.get("source_example_id") for r in selected]
    assert len(set(ids)) == 4, f"Duplicate source IDs in selection: {ids}"

    # Write source_prompt_selection.csv
    fields = [
        "goal_index", "source_example_id", "selection_stratum",
        "sr_success", "strongreject_score", "think_token_count",
        "finish_reason", "thinking_segmentation_status",
        "source_prompt_sha256",
    ]
    sel_path = out_dir / "source_prompt_selection.csv"
    with open(sel_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(selected)
    print(f"\nWrote {sel_path}")

    # Write manifest
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "stage47_run_dir": str(args.stage47_run_dir),
        "n_selected": len(selected),
        "selected_goals": sorted(goals_selected),
        "selection_algorithm": (
            "For each goal: filter condition-A, eos_token, parsed_from_think_tags. "
            "Sort by interest_score (|sr_score - 0.5|, ascending), then middle stratum first, "
            "then conversation_id. Select top-ranked."
        ),
        "seeds": _SEEDS,
        "conditions": _CONDITIONS,
        "total_planned_generations": len(selected) * len(_CONDITIONS) * len(_SEEDS),
        "selected_prompts": [
            {
                "goal_index": int(_f(r.get("goal_index", -1))),
                "source_example_id": r.get("source_example_id"),
                "selection_stratum": r.get("selection_stratum"),
                "sr_success": r.get("sr_success"),
                "strongreject_score": _f(r.get("strongreject_score", float("nan"))),
                "think_token_count": int(_f(r.get("think_token_count", 0))),
            }
            for r in selected
        ],
        "all_candidates": all_candidates,
    }
    manifest_path = out_dir / "source_prompt_selection_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    print(f"Wrote {manifest_path}")
    print(
        f"\nTotal planned generations: "
        f"{len(selected)} prompts × {len(_CONDITIONS)} conditions × {len(_SEEDS)} seeds = "
        f"{len(selected) * len(_CONDITIONS) * len(_SEEDS)}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
