"""
Stage 4.5 — Pilot selection: deterministically selects 10 representative examples
for the pilot human annotation and analysis workflow.

Selection rules (applied in order):
  1. Exclude not-separable examples (thinking_segmentation_status != 'parsed_from_think_tags').
  2. Exclude right-censored examples from the primary candidate pool; use as reserve only if the
     primary pool cannot fill 5 successes + 5 failures.
  3. Select 5 StrongREJECT successes and 5 StrongREJECT failures.
  4. Prioritise SR/Gemini disagreements (sr_success != judge_success).
  5. Prefer goal diversity (goal_index 0–3) across the selected set.
  6. Match failure think_token_count to median of selected success think_token_count.
  7. Random tiebreaking with RANDOM_SEED = 42 for full reproducibility.

Outputs:
  review/pilot_example_queue.csv
  review/pilot_selection_manifest.json

Usage:
  python -m poc_stage4_5.select_pilot_examples [--analysis-dataset PATH]
                                                [--review-dir PATH]
                                                [--seed INT] [--force]
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RANDOM_SEED: int = 42
PILOT_N_SUCCESS: int = 5
PILOT_N_FAILURE: int = 5

PILOT_QUEUE_FIELDNAMES: list[str] = [
    "example_id",
    "goal_index",
    "attack_iteration",
    "conversation_id",
    "sr_success",
    "judge_success",
    "is_disagreement",
    "think_token_count",
    "right_censored",
    "pilot_role",
    "review_status",
    "annotation_status",
]

SELECTION_RULES: list[str] = [
    "Exclude not-separable examples (thinking_segmentation_status != 'parsed_from_think_tags').",
    "Exclude right-censored examples from primary candidate pool; use only if primary pool is insufficient.",
    "Select exactly 5 StrongREJECT successes (sr_success=True) and 5 StrongREJECT failures (sr_success=False).",
    "Prioritise SR/Gemini disagreements (sr_success != judge_success) by scoring +1000.",
    "Prefer goal diversity: score +100 if goal_index appears in the other outcome group.",
    "Match thinking length: penalise abs(think_token_count - reference_median) / 100 "
    "(reference_median = median think_token_count of already-selected success examples, "
    "applied only when selecting failures).",
    "Random tiebreaking with seed=42; random values pre-computed before sorting.",
]


# ---------------------------------------------------------------------------
# Core selection logic
# ---------------------------------------------------------------------------

def _score_candidates(
    candidates: list[dict],
    reference_goals: set[int] | None,
    reference_think_median: float | None,
    rng: random.Random,
) -> list[tuple[float, dict]]:
    """Return (score, row) pairs, higher score = higher priority."""
    scored: list[tuple[float, dict]] = []
    for r in candidates:
        s = 0.0
        if r["sr_success"] != r["judge_success"]:
            s += 1000.0
        if reference_goals and r["goal_index"] in reference_goals:
            s += 100.0
        if reference_think_median is not None:
            s -= abs(r["think_token_count"] - reference_think_median) / 100.0
        rand_val = rng.random()
        scored.append((s, rand_val, r))
    # Sort descending by score, then by rand_val as tiebreak
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [(s, r) for s, _, r in scored]


def _pick(
    primary: list[dict],
    reserve: list[dict],
    n: int,
    reference_goals: set[int] | None,
    reference_think_median: float | None,
    rng: random.Random,
) -> list[dict]:
    """Select n rows; prefer primary pool, fall back to reserve if needed."""
    scored_primary = _score_candidates(primary, reference_goals, reference_think_median, rng)
    selected = [r for _, r in scored_primary[:n]]
    if len(selected) < n:
        deficit = n - len(selected)
        scored_reserve = _score_candidates(reserve, reference_goals, reference_think_median, rng)
        selected += [r for _, r in scored_reserve[:deficit]]
    return selected


def select_pilot(
    dataset: list[dict],
    n_success: int = PILOT_N_SUCCESS,
    n_failure: int = PILOT_N_FAILURE,
    seed: int = RANDOM_SEED,
) -> list[dict]:
    """
    Select pilot examples from the analysis dataset.

    Returns the selected rows (typed dicts from load_analysis_dataset) with two
    extra keys added: 'pilot_role' ('sr_success' | 'sr_failure') and
    'is_disagreement' (bool).
    """
    rng = random.Random(seed)

    separable = [
        r for r in dataset
        if r.get("thinking_segmentation_status") == "parsed_from_think_tags"
    ]
    primary = [r for r in separable if not r["right_censored"]]
    reserve = [r for r in separable if r["right_censored"]]

    primary_success = [r for r in primary if r["sr_success"]]
    primary_failure = [r for r in primary if not r["sr_success"]]
    reserve_success = [r for r in reserve if r["sr_success"]]
    reserve_failure = [r for r in reserve if not r["sr_success"]]

    # Select successes first (no reference yet)
    selected_success = _pick(
        primary_success, reserve_success, n_success,
        reference_goals=None,
        reference_think_median=None,
        rng=rng,
    )

    # Use selected-success metadata as reference for failure selection
    success_goals = {r["goal_index"] for r in selected_success}
    success_think_median = statistics.median(
        r["think_token_count"] for r in selected_success
    ) if selected_success else None

    selected_failure = _pick(
        primary_failure, reserve_failure, n_failure,
        reference_goals=success_goals,
        reference_think_median=success_think_median,
        rng=rng,
    )

    result: list[dict] = []
    for r in selected_success:
        row = dict(r)
        row["pilot_role"] = "sr_success"
        row["is_disagreement"] = r["sr_success"] != r["judge_success"]
        result.append(row)
    for r in selected_failure:
        row = dict(r)
        row["pilot_role"] = "sr_failure"
        row["is_disagreement"] = r["sr_success"] != r["judge_success"]
        result.append(row)
    return result


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_pilot_queue(selected: list[dict], path: Path) -> None:
    rows = []
    for r in selected:
        rows.append({
            "example_id": r["example_id"],
            "goal_index": r["goal_index"],
            "attack_iteration": r["attack_iteration"],
            "conversation_id": r["conversation_id"],
            "sr_success": str(r["sr_success"]),
            "judge_success": str(r["judge_success"]),
            "is_disagreement": str(r["is_disagreement"]),
            "think_token_count": r["think_token_count"],
            "right_censored": str(r["right_censored"]),
            "pilot_role": r["pilot_role"],
            "review_status": "pending",
            "annotation_status": "pending",
        })
    common.write_csv(path, rows, PILOT_QUEUE_FIELDNAMES)


def write_pilot_manifest(
    selected: list[dict],
    dataset: list[dict],
    path: Path,
    seed: int = RANDOM_SEED,
) -> None:
    separable = [
        r for r in dataset
        if r.get("thinking_segmentation_status") == "parsed_from_think_tags"
    ]
    n_not_separable = len(dataset) - len(separable)
    primary = [r for r in separable if not r["right_censored"]]
    n_right_censored = len(separable) - len(primary)
    n_primary_success = sum(1 for r in primary if r["sr_success"])
    n_primary_failure = sum(1 for r in primary if not r["sr_success"])

    n_disagree = sum(1 for r in selected if r["is_disagreement"])

    manifest = {
        "created_utc": common.utc_now(),
        "random_seed": seed,
        "pilot_size": len(selected),
        "n_success": sum(1 for r in selected if r["pilot_role"] == "sr_success"),
        "n_failure": sum(1 for r in selected if r["pilot_role"] == "sr_failure"),
        "selection_rules": SELECTION_RULES,
        "eligibility": {
            "total": len(dataset),
            "n_not_separable": n_not_separable,
            "n_right_censored": n_right_censored,
            "n_primary_eligible": len(primary),
            "n_primary_success": n_primary_success,
            "n_primary_failure": n_primary_failure,
        },
        "n_disagreements_included": n_disagree,
        "selected_example_ids": [r["example_id"] for r in selected],
        "per_example": [
            {
                "example_id": r["example_id"],
                "goal_index": r["goal_index"],
                "sr_success": r["sr_success"],
                "judge_success": r["judge_success"],
                "is_disagreement": r["is_disagreement"],
                "think_token_count": r["think_token_count"],
                "right_censored": r["right_censored"],
                "pilot_role": r["pilot_role"],
            }
            for r in selected
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stage 4.5 pilot example selection.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--analysis-dataset",
        type=Path,
        default=common.ANALYSIS_DATASET_PATH,
    )
    p.add_argument(
        "--review-dir",
        type=Path,
        default=common.DEFAULT_REVIEW_DIR,
    )
    p.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
    )
    p.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing pilot queue without prompting.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    queue_path = args.review_dir / "pilot_example_queue.csv"
    manifest_path = args.review_dir / "pilot_selection_manifest.json"

    if queue_path.exists() and not args.force:
        print(f"WARNING: {queue_path} already exists. Use --force to overwrite.",
              file=sys.stderr)
        return 1

    dataset = common.load_analysis_dataset(args.analysis_dataset)
    selected = select_pilot(dataset, seed=args.seed)

    write_pilot_queue(selected, queue_path)
    write_pilot_manifest(selected, dataset, manifest_path, seed=args.seed)

    n_disagree = sum(1 for r in selected if r["is_disagreement"])
    goals = sorted({r["goal_index"] for r in selected})
    print(f"Pilot selection complete: {len(selected)} examples "
          f"({sum(1 for r in selected if r['pilot_role']=='sr_success')} success, "
          f"{sum(1 for r in selected if r['pilot_role']=='sr_failure')} failure)")
    print(f"  Disagreements included: {n_disagree}")
    print(f"  Goals covered: {goals}")
    print(f"Written: {queue_path}")
    print(f"Written: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
