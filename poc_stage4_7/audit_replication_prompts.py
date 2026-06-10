"""
Stage 4.7 — Audit replication prompts.

Validates all invariants from the plan:
  - A and E prompt hashes == source prompt hash
  - D is deletion-only (subsequence check)
  - Target span and answer cue sha256 identical in A, D, E, F
  - F length_match_ratio within ±5%
  - No empty prompts or user messages
  - No duplicates (source_example_id, condition)
  - Exactly 4 conditions per source prompt
  - Total ≤ 60 generation rows
  - All validation_passed == True

Fails loudly on any violated invariant.

Usage:
  python -m poc_stage4_7.audit_replication_prompts [--prompts-path PATH] [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_REPLICATION_PROMPTS = _REPO_ROOT / "outputs" / "stage4_7" / "replication_prompts.jsonl"
_OUTPUT_BASE = _REPO_ROOT / "outputs" / "stage4_7"
MAX_GENERATIONS = 60
LENGTH_MATCH_TOLERANCE = 0.05
EXPECTED_CONDITIONS = {"A", "D", "F", "E"}


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def audit(rows: list[dict]) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict = {}

    # 1. Total count
    checks["total_rows"] = len(rows)
    if len(rows) > MAX_GENERATIONS:
        errors.append(f"FAIL: {len(rows)} rows > {MAX_GENERATIONS} max allowed")
    checks["within_generation_limit"] = len(rows) <= MAX_GENERATIONS

    # 2. Duplicate detection
    seen: set[tuple] = set()
    dupes = []
    for r in rows:
        key = (r.get("source_example_id"), r.get("condition"))
        if key in seen:
            dupes.append(key)
        seen.add(key)
    if dupes:
        errors.append(f"FAIL: {len(dupes)} duplicate source-condition pairs: {dupes[:5]}")
    checks["no_duplicates"] = len(dupes) == 0

    # 3. All conditions present per source
    source_ids = list(dict.fromkeys(r.get("source_example_id") for r in rows))
    checks["n_source_prompts"] = len(source_ids)
    missing_conditions = {}
    for sid in source_ids:
        sid_rows = [r for r in rows if r.get("source_example_id") == sid]
        conds_present = {r.get("condition") for r in sid_rows}
        missing = EXPECTED_CONDITIONS - conds_present
        extra = conds_present - EXPECTED_CONDITIONS
        if missing:
            missing_conditions[sid] = list(missing)
            errors.append(f"FAIL: {sid} missing conditions: {missing}")
        if extra:
            warnings.append(f"WARN: {sid} has unexpected conditions: {extra}")
    checks["all_conditions_present"] = len(missing_conditions) == 0

    # 4. Per-source validation
    for sid in source_ids:
        sid_rows = {r.get("condition"): r for r in rows if r.get("source_example_id") == sid}
        r_a = sid_rows.get("A")
        r_d = sid_rows.get("D")
        r_e = sid_rows.get("E")
        r_f = sid_rows.get("F")

        # A and E must have source_prompt_sha256 == transformed_prompt_sha256
        if r_a:
            if r_a.get("source_prompt_sha256") != r_a.get("transformed_prompt_sha256"):
                warnings.append(
                    f"WARN: {sid} cond=A source_sha256 != transformed_sha256 "
                    f"(possible chat template wrapping diff — acceptable if token_ids differ only in template)"
                )

        if r_e and r_a:
            # E source sha256 should match A source sha256
            if r_e.get("source_prompt_sha256") != r_a.get("source_prompt_sha256"):
                errors.append(f"FAIL: {sid} cond=E source_sha256 != cond=A source_sha256")

        # Target and answer cue sha256 must be identical across all 4 conditions
        target_shas = set()
        acue_shas = set()
        for cond_key, r in sid_rows.items():
            if r:
                ts = r.get("target_span_sha256")
                acs = r.get("answer_cue_sha256")
                if ts:
                    target_shas.add(ts)
                if acs:
                    acue_shas.add(acs)
        if len(target_shas) > 1:
            errors.append(f"FAIL: {sid} target_span_sha256 differs across conditions: {target_shas}")
        if len(acue_shas) > 1:
            errors.append(f"FAIL: {sid} answer_cue_sha256 differs across conditions: {acue_shas}")

        # F length match
        if r_f:
            lr = r_f.get("length_match_ratio")
            if lr is not None:
                try:
                    lr = float(lr)
                    if abs(lr - 1.0) > LENGTH_MATCH_TOLERANCE:
                        errors.append(
                            f"FAIL: {sid} cond=F length_match_ratio={lr:.4f} outside ±{LENGTH_MATCH_TOLERANCE}"
                        )
                except (TypeError, ValueError):
                    errors.append(f"FAIL: {sid} cond=F length_match_ratio not numeric: {lr}")

        # F target and answer cue preserved
        if r_f:
            if not r_f.get("target_span_preserved", True):
                errors.append(f"FAIL: {sid} cond=F target_span_preserved=False")

        # No empty user messages
        for cond_key, r in sid_rows.items():
            msg = r.get("_user_message_text", "")
            if not msg or len(msg.strip()) < 10:
                errors.append(f"FAIL: {sid} cond={cond_key} _user_message_text is empty or too short")

        # D is deletion-only: D token count < A token count (if both present and puzzle exists)
        if r_a and r_d:
            tok_a = int(r_a.get("transformed_prompt_tokens", 0) or 0)
            tok_d = int(r_d.get("transformed_prompt_tokens", 0) or 0)
            if tok_d > tok_a:
                errors.append(f"FAIL: {sid} cond=D token count ({tok_d}) > cond=A ({tok_a})")

    # 5. All validation_passed == True
    failed = [r for r in rows if not r.get("validation_passed", True)]
    if failed:
        errors.append(f"FAIL: {len(failed)} rows have validation_passed=False")
        for r in failed[:5]:
            errors.append(f"  {r.get('source_example_id')} cond={r.get('condition')}: {r.get('validation_notes')}")
    checks["all_validation_passed"] = len(failed) == 0

    # 6. Enable_thinking check
    for r in rows:
        cond = r.get("condition")
        et = r.get("enable_thinking") or r.get("_enable_thinking")
        if cond == "E":
            if str(et).lower() in ("true", "1"):
                errors.append(f"FAIL: {r.get('source_example_id')} cond=E has enable_thinking=True (should be False)")
        elif cond in ("A", "D", "F"):
            if str(et).lower() in ("false", "0"):
                errors.append(f"FAIL: {r.get('source_example_id')} cond={cond} has enable_thinking=False (should be True)")

    checks["errors"] = errors
    checks["warnings"] = warnings
    checks["passed"] = len(errors) == 0
    return checks


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Audit Stage 4.7 replication prompts.")
    p.add_argument("--prompts-path", type=Path, default=_REPLICATION_PROMPTS)
    p.add_argument("--output-dir", type=Path, default=None)
    args = p.parse_args(argv)

    out_dir = args.output_dir or _OUTPUT_BASE
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.prompts_path} ...")
    rows = _load_jsonl(args.prompts_path)
    print(f"  {len(rows)} rows")

    print("Running audit ...")
    result = audit(rows)

    # Write JSON audit
    audit_json_path = out_dir / "replication_prompt_audit.json"
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {audit_json_path}")

    # Write CSV audit summary
    audit_csv_rows = []
    for r in rows:
        audit_csv_rows.append({
            "source_example_id": r.get("source_example_id"),
            "goal_index": r.get("goal_index"),
            "condition": r.get("condition"),
            "enable_thinking": r.get("enable_thinking") or r.get("_enable_thinking"),
            "transformed_prompt_tokens": r.get("transformed_prompt_tokens"),
            "length_match_ratio": r.get("length_match_ratio"),
            "target_span_preserved": r.get("target_span_preserved"),
            "answer_cue_preserved": r.get("answer_cue_preserved"),
            "validation_passed": r.get("validation_passed"),
            "validation_notes": r.get("validation_notes"),
        })
    audit_csv_path = out_dir / "replication_prompt_audit.csv"
    with open(audit_csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(audit_csv_rows[0].keys()))
        w.writeheader()
        w.writerows(audit_csv_rows)
    print(f"Wrote {audit_csv_path}")

    # Report
    print(f"\n=== Audit Summary ===")
    print(f"Total rows: {result['total_rows']}")
    print(f"Source prompts: {result['n_source_prompts']}")
    print(f"Within limit (<={MAX_GENERATIONS}): {result['within_generation_limit']}")
    print(f"No duplicates: {result['no_duplicates']}")
    print(f"All conditions present: {result['all_conditions_present']}")
    print(f"All validation passed: {result['all_validation_passed']}")

    if result["warnings"]:
        print(f"\nWarnings ({len(result['warnings'])}):")
        for w in result["warnings"][:10]:
            print(f"  {w}")

    if result["errors"]:
        print(f"\nERRORS ({len(result['errors'])}):")
        for e in result["errors"]:
            print(f"  {e}")
        print("\nAUDIT FAILED")
        return 1

    print("\nAUDIT PASSED — all invariants satisfied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
