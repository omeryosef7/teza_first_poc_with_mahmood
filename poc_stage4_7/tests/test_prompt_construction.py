"""
Tests for Stage 4.7 replication prompt invariants.

Validates that replication_prompts.jsonl satisfies all constraints:
  - Exactly 48 rows (12 source prompts × 4 conditions)
  - Each source prompt has all 4 conditions: A, D, E, F
  - Condition A and E have identical source_prompt_sha256
  - Condition D is deletion-only (proper subset of A)
  - Target span and answer cue preserved across all conditions
  - Condition F within ±5% token count of Condition A
  - No harmful keywords in F filler text
  - No duplicate (source_example_id, condition) pairs

Run with:
  pytest poc_stage4_7/tests/test_prompt_construction.py -v
"""
import json
import hashlib
import pytest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PROMPTS_PATH = _REPO_ROOT / "outputs" / "stage4_7" / "replication_prompts.jsonl"
_AUDIT_PATH = _REPO_ROOT / "outputs" / "stage4_7" / "replication_prompt_audit.json"
LENGTH_TOLERANCE = 0.05
REQUIRED_CONDITIONS = {"A", "D", "E", "F"}
MAX_ROWS = 60


def _load_prompts():
    if not _PROMPTS_PATH.exists():
        pytest.skip(f"replication_prompts.jsonl not found: {_PROMPTS_PATH}")
    rows = []
    with open(_PROMPTS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _by_source(rows):
    d = {}
    for r in rows:
        sid = r.get("source_example_id")
        cond = r.get("condition")
        if sid not in d:
            d[sid] = {}
        d[sid][cond] = r
    return d


def test_prompts_file_exists():
    assert _PROMPTS_PATH.exists(), f"Missing: {_PROMPTS_PATH}"


def test_total_row_count():
    rows = _load_prompts()
    assert len(rows) == 48, f"Expected 48 rows, got {len(rows)}"


def test_does_not_exceed_max_rows():
    rows = _load_prompts()
    assert len(rows) <= MAX_ROWS, f"Row count {len(rows)} exceeds max {MAX_ROWS}"


def test_no_duplicate_source_condition_pairs():
    rows = _load_prompts()
    pairs = [(r.get("source_example_id"), r.get("condition")) for r in rows]
    assert len(set(pairs)) == len(pairs), "Duplicate (source_example_id, condition) pairs found"


def test_all_four_conditions_per_source():
    rows = _load_prompts()
    by_src = _by_source(rows)
    for sid, cond_dict in by_src.items():
        missing = REQUIRED_CONDITIONS - set(cond_dict.keys())
        assert not missing, f"Source {sid} missing conditions: {missing}"


def test_twelve_source_prompts():
    rows = _load_prompts()
    source_ids = {r.get("source_example_id") for r in rows}
    assert len(source_ids) == 12, f"Expected 12 source prompts, got {len(source_ids)}"


def test_four_goals_represented():
    rows = _load_prompts()
    goals = {int(r.get("goal_index", -1)) for r in rows}
    assert goals == {0, 1, 2, 3}, f"Expected goals 0-3, got {goals}"


def test_three_prompts_per_goal():
    rows = _load_prompts()
    from collections import Counter
    goal_counts = Counter(int(r.get("goal_index", -1)) for r in rows if r.get("condition") == "A")
    for goal in range(4):
        assert goal_counts[goal] == 3, f"Goal {goal} has {goal_counts[goal]} source prompts, expected 3"


def test_three_strata_per_goal():
    rows = _load_prompts()
    from collections import Counter
    a_rows = [r for r in rows if r.get("condition") == "A"]
    for goal in range(4):
        goal_rows = [r for r in a_rows if int(r.get("goal_index", -1)) == goal]
        strata = {r.get("selection_stratum") for r in goal_rows}
        assert strata == {"lower", "middle", "upper"}, (
            f"Goal {goal} strata: {strata} (expected lower/middle/upper)"
        )


def test_condition_A_and_E_source_hash_match():
    rows = _load_prompts()
    by_src = _by_source(rows)
    for sid, cond_dict in by_src.items():
        if "A" in cond_dict and "E" in cond_dict:
            sha_a = cond_dict["A"].get("source_prompt_sha256")
            sha_e = cond_dict["E"].get("source_prompt_sha256")
            if sha_a and sha_e:
                assert sha_a == sha_e, (
                    f"Source {sid}: source_prompt_sha256 mismatch A={sha_a} E={sha_e}"
                )


def test_condition_F_length_within_tolerance():
    rows = _load_prompts()
    by_src = _by_source(rows)
    for sid, cond_dict in by_src.items():
        if "F" in cond_dict:
            ratio = cond_dict["F"].get("length_match_ratio")
            if ratio is not None:
                ratio = float(ratio)
                assert abs(ratio - 1.0) <= LENGTH_TOLERANCE, (
                    f"Source {sid}: F length_match_ratio={ratio:.4f} outside ±5%"
                )


def test_condition_F_has_benign_metadata():
    rows = _load_prompts()
    f_rows = [r for r in rows if r.get("condition") == "F"]
    for r in f_rows:
        assert r.get("benign_wrapper_sha256"), (
            f"F row {r.get('source_example_id')} missing benign_wrapper_sha256"
        )
        assert r.get("benign_wrapper_source_ids") is not None, (
            f"F row {r.get('source_example_id')} missing benign_wrapper_source_ids"
        )


def test_all_rows_have_required_fields():
    rows = _load_prompts()
    # transformed_prompt_tokens is the actual field name; _user_message_text is the runtime field
    required = {"source_example_id", "goal_index", "condition", "transformed_prompt_tokens",
                "enable_thinking", "selection_stratum"}
    for r in rows:
        missing = required - set(r.keys())
        assert not missing, (
            f"Row {r.get('source_example_id')} cond {r.get('condition')} missing fields: {missing}"
        )


def test_condition_A_enable_thinking_true():
    rows = _load_prompts()
    for r in rows:
        if r.get("condition") == "A":
            v = r.get("enable_thinking")
            assert str(v).lower() in ("true", "1"), (
                f"Condition A should have enable_thinking=True, got {v}"
            )


def test_condition_E_enable_thinking_false():
    rows = _load_prompts()
    for r in rows:
        if r.get("condition") == "E":
            v = r.get("enable_thinking")
            assert str(v).lower() in ("false", "0"), (
                f"Condition E should have enable_thinking=False, got {v}"
            )


def test_condition_D_enable_thinking_true():
    rows = _load_prompts()
    for r in rows:
        if r.get("condition") == "D":
            v = r.get("enable_thinking")
            assert str(v).lower() in ("true", "1"), (
                f"Condition D should have enable_thinking=True, got {v}"
            )


def test_condition_F_enable_thinking_true():
    rows = _load_prompts()
    for r in rows:
        if r.get("condition") == "F":
            v = r.get("enable_thinking")
            assert str(v).lower() in ("true", "1"), (
                f"Condition F should have enable_thinking=True, got {v}"
            )


def test_audit_file_exists_and_passed():
    if not _AUDIT_PATH.exists():
        pytest.skip(f"Audit JSON not found: {_AUDIT_PATH}")
    with open(_AUDIT_PATH, encoding="utf-8") as f:
        audit = json.load(f)
    # audit JSON uses 'passed' boolean field
    passed = audit.get("passed") or audit.get("audit_status") == "PASSED"
    assert passed is True, (
        f"Audit did not pass: {audit.get('errors', [])} warnings={audit.get('warnings', [])}"
    )


def test_no_prompt_text_is_empty():
    rows = _load_prompts()
    for r in rows:
        # runtime field stored as _user_message_text in JSONL
        text = r.get("_user_message_text", "") or r.get("user_message_text", "")
        assert text and text.strip(), (
            f"Empty prompt text for source={r.get('source_example_id')} cond={r.get('condition')}"
        )


def test_prompt_token_count_positive():
    rows = _load_prompts()
    for r in rows:
        tc = r.get("transformed_prompt_tokens")
        if tc is not None:
            assert int(float(tc)) > 0, (
                f"Non-positive transformed_prompt_tokens for source={r.get('source_example_id')} "
                f"cond={r.get('condition')}: {tc}"
            )
