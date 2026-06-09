"""
Stage 4.6 — Audit controlled ablation prompts.

Reads ablation_prompts.jsonl and verifies all 20 rows (4 sources × 5 conditions)
pass the validation checks. Writes ablation_audit.json. Exits 1 on failure.

Usage:
  python -m poc_stage4_6.audit_controlled_ablation_prompts [--run-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

_OUTPUT_BASE = _REPO_ROOT / "outputs" / "stage4_6"
CONDITIONS = ["A", "B", "C", "D", "E"]
EXPECTED_N_GOALS = 4
EXPECTED_N_CONDITIONS = 5
EXPECTED_N_ROWS = EXPECTED_N_GOALS * EXPECTED_N_CONDITIONS


def audit(run_dir: Path) -> dict[str, Any]:
    jsonl_path = run_dir / "ablation_prompts.jsonl"
    if not jsonl_path.exists():
        raise FileNotFoundError(f"ablation_prompts.jsonl not found in {run_dir}")

    rows: list[dict] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    failures: list[str] = []
    warnings: list[str] = []

    # 1. Row count
    if len(rows) != EXPECTED_N_ROWS:
        failures.append(f"Expected {EXPECTED_N_ROWS} rows, got {len(rows)}")

    # 2. All 4 goals represented
    goals_seen = set(r.get("goal_index") for r in rows)
    expected_goals = set(range(EXPECTED_N_GOALS))
    if goals_seen != expected_goals:
        failures.append(f"Goals present: {sorted(goals_seen)}, expected {sorted(expected_goals)}")

    # 3. All 5 conditions represented per goal
    from collections import defaultdict
    by_goal: dict[Any, list[dict]] = defaultdict(list)
    for r in rows:
        by_goal[r.get("goal_index")].append(r)

    for gi, group in by_goal.items():
        conds_seen = {r.get("condition") for r in group}
        if conds_seen != set(CONDITIONS):
            failures.append(f"goal={gi}: conditions {sorted(conds_seen)} != {CONDITIONS}")

    # 4. All rows passed validation
    failed_validation = [r for r in rows if not r.get("validation_passed", False)]
    if failed_validation:
        for r in failed_validation:
            failures.append(
                f"goal={r['goal_index']} cond={r['condition']}: validation_notes={r.get('validation_notes')}"
            )

    # 5. Condition A sha256 == source sha256
    for r in rows:
        if r.get("condition") == "A":
            if r.get("prompt_token_ids_sha256") != r.get("source_prompt_sha256"):
                failures.append(
                    f"goal={r['goal_index']} cond=A: sha256 mismatch "
                    f"(condition_a={r.get('prompt_token_ids_sha256')[:8]}... "
                    f"source={r.get('source_prompt_sha256', '')[:8]}...)"
                )

    # 6. Token lengths monotonically decrease A ≥ B ≥ C ≥ D per source
    for gi in range(EXPECTED_N_GOALS):
        group = {r["condition"]: r for r in by_goal.get(gi, [])}
        lengths = {}
        for cond in ["A", "B", "C", "D"]:
            if cond in group:
                lengths[cond] = group[cond].get("prompt_token_count", 0)
        seq = [lengths.get(c, 0) for c in ["A", "B", "C", "D"]]
        for i in range(len(seq) - 1):
            if seq[i] < seq[i + 1]:
                failures.append(
                    f"goal={gi}: token lengths not monotone: {dict(zip(['A','B','C','D'], seq))}"
                )
                break

    # 7. Target span sha256 same across A–D per source
    for gi in range(EXPECTED_N_GOALS):
        group = {r["condition"]: r for r in by_goal.get(gi, [])}
        shas = {c: group[c].get("target_span_sha256") for c in ["A","B","C","D"] if c in group}
        unique_shas = set(shas.values())
        if len(unique_shas) > 1:
            failures.append(f"goal={gi}: target_span_sha256 differs across conditions: {shas}")

    # 8. Answer cue sha256 same across A–D per source
    for gi in range(EXPECTED_N_GOALS):
        group = {r["condition"]: r for r in by_goal.get(gi, [])}
        shas = {c: group[c].get("answer_cue_span_sha256") for c in ["A","B","C","D"] if c in group}
        unique_shas = set(shas.values())
        if len(unique_shas) > 1:
            failures.append(f"goal={gi}: answer_cue_span_sha256 differs across conditions: {shas}")

    # 9. Thinking mode: E has enable_thinking=False; A–D have enable_thinking=True
    for r in rows:
        cond = r.get("condition")
        thinking = r.get("enable_thinking")
        if cond == "E" and thinking is not False:
            failures.append(f"goal={r['goal_index']} cond=E: enable_thinking should be False, got {thinking}")
        elif cond in ("A","B","C","D") and thinking is not True:
            failures.append(f"goal={r['goal_index']} cond={cond}: enable_thinking should be True, got {thinking}")

    # 10. Unique (source_example_id, condition) identifiers
    pairs = [(r.get("source_example_id"), r.get("condition")) for r in rows]
    if len(pairs) != len(set(pairs)):
        failures.append("Duplicate (source_example_id, condition) pairs found")

    # Condition D has no puzzle tokens remaining
    for gi in range(EXPECTED_N_GOALS):
        group = {r["condition"]: r for r in by_goal.get(gi, [])}
        if "D" in group:
            kept = group["D"].get("puzzle_tokens_kept", -1)
            if kept != 0:
                warnings.append(f"goal={gi} cond=D: puzzle_tokens_kept={kept} (expected 0)")

    passed = len(failures) == 0
    audit_result = {
        "created_utc": common.utc_now(),
        "n_rows": len(rows),
        "n_goals": len(goals_seen),
        "n_conditions": len(CONDITIONS),
        "validation_passed": passed,
        "failures": failures,
        "warnings": warnings,
        "gate_result": "PASS" if passed else "FAIL",
    }

    audit_path = run_dir / "ablation_audit.json"
    common.atomic_write_json(audit_path, audit_result)

    if passed:
        print(f"PASS — all {len(rows)} rows validated ({EXPECTED_N_GOALS} goals × {EXPECTED_N_CONDITIONS} conditions)")
    else:
        print(f"FAIL — {len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")

    print(f"Wrote {audit_path}")
    return audit_result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Audit Stage 4.6 ablation prompts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--run-dir", type=Path, default=_OUTPUT_BASE)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = audit(args.run_dir)
    return 0 if result["validation_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
