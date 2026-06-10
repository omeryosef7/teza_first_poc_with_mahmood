"""
Stage 4.7 — Deterministic source prompt selection.

Selects up to 3 source prompts per goal from the Stage 4 analysis dataset (42 examples)
using length-tertile stratification. One prompt per tertile (lower, middle, upper),
with preference for diverse conversation IDs.

Eligibility:
  - thinking_segmentation_status == "parsed_from_think_tags"
  - right_censored == False
  - Stage 6 trace must exist and be non-empty

Selection strategy:
  1. Sort eligible prompts by prompt_token_count (ascending).
  2. Divide into three tertiles of equal size (round down; remainder to final tertile).
  3. Select the prompt at the center index of each tertile.
  4. If tie on center (even tertile size), prefer the lower index.
  5. Verify all three selected prompts have different conversation_ids; if not,
     use seed-47 RNG to break ties among tertile candidates.
  6. If fewer than 3 eligible, select the maximum available.

Usage:
  python -m poc_stage4_7.select_source_prompts [--output-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_ANALYSIS_DATASET = (
    _REPO_ROOT
    / "outputs"
    / "stage4"
    / "token_dynamics"
    / "full_20260604_101929"
    / "analysis"
    / "analysis_dataset.csv"
)
_STAGE2B_JSONL = (
    _REPO_ROOT / "outputs" / "hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl"
)
_STAGE6_TRACES = _REPO_ROOT / "outputs" / "stage6" / "all_traces_full"
_OUTPUT_BASE = _REPO_ROOT / "outputs" / "stage4_7"

GOALS = [0, 1, 2, 3]
MAX_PER_GOAL = 3
SEED = 47

OUTPUT_FIELDNAMES = [
    "example_id",
    "goal_index",
    "conversation_id",
    "attack_iteration",
    "target_model",
    "source_prompt_token_count",
    "original_think_token_count",
    "original_strongreject_score",
    "original_sr_success",
    "selection_stratum",
    "source_prompt_sha256",
    "eligible_segmentation",
    "eligible_not_censored",
    "eligible_trace_exists",
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_analysis_dataset() -> list[dict]:
    rows = []
    with open(_ANALYSIS_DATASET, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def _load_stage2b_map() -> dict[str, dict]:
    result: dict[str, dict] = {}
    with open(_STAGE2B_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            eid = r.get("example_id") or _make_example_id(r)
            result[eid] = r
    return result


def _make_example_id(r: dict) -> str:
    gi = r.get("goal_index", "?")
    ai = r.get("attack_iteration", "?")
    ci = r.get("conversation_id", "?")
    tm = r.get("target_model", "gpt-o4-mini")
    return f"goal_index={gi}|attack_iteration={ai}|conversation_id={ci}|target_model={tm}"


def _trace_path(example_id: str) -> Path:
    parts = {}
    for seg in example_id.split("|"):
        k, _, v = seg.partition("=")
        parts[k] = v
    gi = parts.get("goal_index", "")
    ai = parts.get("attack_iteration", "")
    ci = parts.get("conversation_id", "")
    tm = parts.get("target_model", "gpt-o4-mini")
    fname = f"qwen3_14b_trace_goal_index_{gi}_attack_iteration_{ai}_conversation_id_{ci}_target_model_{tm}.json"
    return _STAGE6_TRACES / fname


def _trace_exists(example_id: str) -> bool:
    return _trace_path(example_id).exists()


def _sha256_prompt(example_id: str, s2b_map: dict) -> str | None:
    r = s2b_map.get(example_id)
    if r is None:
        return None
    prompt_text = r.get("attack_prompt", "")
    return hashlib.sha256(prompt_text.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Tertile selection
# ---------------------------------------------------------------------------

def _tertile_center_index(n: int, tertile: int) -> int:
    """Return center index of the given tertile (0, 1, or 2) in a list of n items."""
    size = n // 3
    remainder = n % 3
    # Distribute remainder to last tertiles
    sizes = [size, size, size + remainder]
    starts = [0, sizes[0], sizes[0] + sizes[1]]
    t_size = sizes[tertile]
    t_start = starts[tertile]
    if t_size == 0:
        return t_start
    center = t_start + (t_size - 1) // 2
    return center


def _select_for_goal(
    eligible: list[dict],
    goal: int,
    rng: random.Random,
) -> list[dict]:
    """
    Select up to MAX_PER_GOAL prompts from eligible list using tertile strategy.
    Returns list of selected rows, each augmented with 'selection_stratum'.
    """
    if not eligible:
        return []

    # Sort by prompt_token_count (int) ascending; break ties by example_id (deterministic)
    eligible_sorted = sorted(
        eligible,
        key=lambda r: (int(r["prompt_token_count"]), r["example_id"]),
    )

    n = len(eligible_sorted)
    n_tertiles = min(MAX_PER_GOAL, n)  # can't select more than available
    stratum_names = ["lower", "middle", "upper"]

    if n_tertiles == 1:
        # Only one eligible — select it
        sel = eligible_sorted[0].copy()
        sel["selection_stratum"] = "lower"
        return [sel]

    if n_tertiles == 2:
        # Take first and last
        sel0 = eligible_sorted[0].copy()
        sel0["selection_stratum"] = "lower"
        sel1 = eligible_sorted[-1].copy()
        sel1["selection_stratum"] = "upper"
        return [sel0, sel1]

    # Compute tertile centers
    candidates: list[dict] = []
    used_conv_ids: set[int] = set()

    for t in range(3):
        center_idx = _tertile_center_index(n, t)
        t_size = n // 3 + (1 if t == 2 else 0) if n % 3 else n // 3
        # Compute tertile start and end
        base_size = n // 3
        remainder = n % 3
        sizes = [base_size, base_size, base_size + remainder]
        starts = [0, sizes[0], sizes[0] + sizes[1]]
        t_start = starts[t]
        t_end = t_start + sizes[t]

        # Prefer candidate at center, then diversify by conversation_id
        tertile_candidates = eligible_sorted[t_start:t_end]

        # Sort by: prefer different conv_id from already used, then center distance
        def sort_key(r: dict, center: int = center_idx - t_start) -> tuple:
            conv_id = int(r["conversation_id"])
            conv_penalty = 0 if conv_id not in used_conv_ids else 1
            idx = tertile_candidates.index(r)
            return (conv_penalty, abs(idx - center))

        tertile_candidates_sorted = sorted(tertile_candidates, key=sort_key)
        selected = tertile_candidates_sorted[0].copy()
        selected["selection_stratum"] = stratum_names[t]
        candidates.append(selected)
        used_conv_ids.add(int(selected["conversation_id"]))

    return candidates


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def select_source_prompts(
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> list[dict]:
    rng = random.Random(SEED)
    out_dir = output_dir or _OUTPUT_BASE
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading analysis dataset from {_ANALYSIS_DATASET} ...")
    dataset = _load_analysis_dataset()
    print(f"  {len(dataset)} rows")

    print(f"Loading Stage 2B map from {_STAGE2B_JSONL} ...")
    s2b_map = _load_stage2b_map()
    print(f"  {len(s2b_map)} Stage 2B entries")

    all_selected: list[dict] = []

    for goal in GOALS:
        goal_rows = [r for r in dataset if r["goal_index"] == str(goal)]

        # Apply eligibility filters
        eligible: list[dict] = []
        for r in goal_rows:
            seg_ok = r["thinking_segmentation_status"] == "parsed_from_think_tags"
            cens_ok = r["right_censored"] == "False"
            trace_ok = _trace_exists(r["example_id"])
            if seg_ok and cens_ok and trace_ok:
                eligible.append(r)

        print(f"\nGoal {goal}: {len(goal_rows)} total, {len(eligible)} eligible")
        for r in sorted(eligible, key=lambda x: int(x["prompt_token_count"])):
            print(f"  {r['example_id']}  prompt_tokens={r['prompt_token_count']}  sr={r['strongreject_score']}")

        selected = _select_for_goal(eligible, goal, rng)
        print(f"  Selected {len(selected)} prompts:")
        for s in selected:
            print(f"    stratum={s['selection_stratum']}  {s['example_id']}  prompt_tokens={s['prompt_token_count']}")

        for sel in selected:
            eid = sel["example_id"]
            sha256 = _sha256_prompt(eid, s2b_map)
            output_row: dict[str, Any] = {
                "example_id": eid,
                "goal_index": int(sel["goal_index"]),
                "conversation_id": int(sel["conversation_id"]),
                "attack_iteration": int(sel["attack_iteration"]),
                "target_model": sel.get("target_model", "gpt-o4-mini"),
                "source_prompt_token_count": int(sel["prompt_token_count"]),
                "original_think_token_count": int(sel.get("think_token_count", 0) or 0),
                "original_strongreject_score": float(sel.get("strongreject_score", 0) or 0),
                "original_sr_success": sel.get("sr_success") == "True",
                "selection_stratum": sel["selection_stratum"],
                "source_prompt_sha256": sha256 or "",
                "eligible_segmentation": sel["thinking_segmentation_status"] == "parsed_from_think_tags",
                "eligible_not_censored": sel["right_censored"] == "False",
                "eligible_trace_exists": _trace_exists(eid),
            }
            all_selected.append(output_row)

    print(f"\nTotal selected: {len(all_selected)} prompts")

    if dry_run:
        print("[DRY RUN] — no files written.")
        return all_selected

    # Write CSV
    csv_path = out_dir / "source_prompt_selection.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_FIELDNAMES)
        w.writeheader()
        w.writerows(all_selected)
    print(f"Wrote {csv_path}")

    # Write manifest
    manifest = {
        "created_utc": __import__("datetime").datetime.utcnow().isoformat() + "+00:00",
        "n_goals": len(GOALS),
        "max_per_goal": MAX_PER_GOAL,
        "seed": SEED,
        "eligibility_criteria": [
            "thinking_segmentation_status == parsed_from_think_tags",
            "right_censored == False",
            "Stage 6 trace file exists",
        ],
        "selection_method": "length_tertile_center_with_conv_id_diversity",
        "per_goal_counts": {
            str(g): sum(1 for r in all_selected if r["goal_index"] == g)
            for g in GOALS
        },
        "total_selected": len(all_selected),
        "analysis_dataset": str(_ANALYSIS_DATASET),
    }
    manifest_path = out_dir / "source_prompt_selection_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {manifest_path}")

    return all_selected


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage 4.7 source prompt selection.")
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--dry-run", action="store_true", default=False)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    select_source_prompts(output_dir=args.output_dir, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
