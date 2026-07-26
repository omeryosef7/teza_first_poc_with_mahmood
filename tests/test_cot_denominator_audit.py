"""Torch-free tests for the CoT-hijacking denominator audit.

Uses synthetic in-tmp JSONL only. Also verifies that decoy harmful-text
sentinels planted in the fixture are NEVER surfaced in any output.
"""
import json
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "scripts")
)

import cot_hijacking_denominator_audit as audit  # noqa: E402


# A sentinel that must never appear in any produced output (CSV or table).
DECOY = "DECOY_HARMFUL_TEXT_SHOULD_NEVER_APPEAR"


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")


def make_attacked(path):
    """5 expected behaviors (goal_index 0..4).

    - goal 0: two rows, one high (0.9) -> success (multi-row ANY logic)
    - goal 1: refusal-as-low-score row (0.05) -> delivered, NOT success
    - goal 2: high (0.8) -> success
    - goal 3: low (0.2) -> delivered, not success
    - goal 4: MISSING entirely (non-delivered attack) -> zero rows
    Each row carries decoy harmful text fields.
    """
    recs = [
        {"goal_index": 0, "strongreject_score": 0.1, "goal": DECOY,
         "target_response": DECOY, "attack_prompt": DECOY},
        {"goal_index": 0, "strongreject_score": 0.9, "goal": DECOY,
         "target_response": DECOY, "attack_prompt": DECOY},
        {"goal_index": 1, "strongreject_score": 0.05, "goal": DECOY,
         "target_response": DECOY, "attack_prompt": DECOY},
        {"goal_index": 2, "strongreject_score": 0.8, "goal": DECOY,
         "target_response": DECOY, "attack_prompt": DECOY},
        {"goal_index": 3, "strongreject_score": 0.2, "goal": DECOY,
         "target_response": DECOY, "attack_prompt": DECOY},
        # goal_index 4 deliberately absent.
    ]
    write_jsonl(path, recs)


def make_clean(path):
    """Clean baseline: goals 0..3 present (goal 4 also missing in clean).

    - goal 0: low (0.1) -> not success
    - goal 1: low (0.0) -> not success
    - goal 2: low (0.1) -> not success
    - goal 3: low (0.1) -> not success
    So clean matched ASR = 0.0; attacked matched ASR = 2/4 = 0.5.
    """
    recs = [
        {"goal_index": 0, "strongreject_score": 0.1, "goal": DECOY,
         "target_response": DECOY},
        {"goal_index": 1, "strongreject_score": 0.0, "goal": DECOY,
         "target_response": DECOY},
        {"goal_index": 2, "strongreject_score": 0.1, "goal": DECOY,
         "target_response": DECOY},
        {"goal_index": 3, "strongreject_score": 0.1, "goal": DECOY,
         "target_response": DECOY},
    ]
    write_jsonl(path, recs)


def test_delivered_success_and_missing(tmp_path):
    att = tmp_path / "attacked.jsonl"
    make_attacked(str(att))
    rows = audit.load_scored_rows(str(att))
    res = audit.audit_model(str(att), None, n_expected=5)

    # 4 delivered behaviors (0,1,2,3); goal 4 missing.
    assert res["n_delivered"] == 4
    # successes: goal 0 (0.9) and goal 2 (0.8) = 2.
    assert res["n_success"] == 2
    assert res["n_missing"] == 1
    assert res["missing_goal_indices"] == [4]


def test_refusal_row_is_delivered_not_success(tmp_path):
    att = tmp_path / "attacked.jsonl"
    make_attacked(str(att))
    res = audit.audit_model(str(att), None, n_expected=5)
    # goal 1 is a refusal-as-low-score row: counted as delivered but not success.
    att_map = audit.behavior_success_map(audit.load_scored_rows(str(att)))
    assert 1 in att_map  # delivered
    assert att_map[1] is False  # not a success


def test_asr_delivered_vs_of25_differ(tmp_path):
    att = tmp_path / "attacked.jsonl"
    make_attacked(str(att))
    res = audit.audit_model(str(att), None, n_expected=5)
    # asr_delivered = 2/4 = 0.5 ; asr_of25(expected=5) = 2/5 = 0.4
    assert res["asr_delivered"] == pytest.approx(0.5)
    assert res["asr_of25"] == pytest.approx(0.4)
    assert res["asr_delivered"] != res["asr_of25"]


def test_matched_set_math(tmp_path):
    att = tmp_path / "attacked.jsonl"
    clean = tmp_path / "clean.jsonl"
    make_attacked(str(att))
    make_clean(str(clean))
    res = audit.audit_model(str(att), str(clean), n_expected=5)
    # matched behaviors present in both: 0,1,2,3 -> 4.
    assert res["matched_n"] == 4
    assert res["matched_attacked_asr"] == pytest.approx(0.5)   # goals 0,2 succeed
    assert res["matched_clean_asr"] == pytest.approx(0.0)
    assert res["matched_uplift"] == pytest.approx(0.5)


def test_no_harmful_text_in_csv(tmp_path):
    att = tmp_path / "attacked.jsonl"
    clean = tmp_path / "clean.jsonl"
    out = tmp_path / "out.csv"
    make_attacked(str(att))
    make_clean(str(clean))
    # Run through the directory-based runner with a single fake slug so we
    # exercise the same path the real run uses. We fabricate the expected
    # filenames.
    att_dir = tmp_path / "attacked_dir"
    clean_dir = tmp_path / "clean_dir"
    att_dir.mkdir()
    clean_dir.mkdir()
    slug = "fake_model"
    make_attacked(str(att_dir / f"phase4_cot_hf_{slug}_dev25_strongreject.jsonl"))
    make_clean(str(clean_dir / f"clean_{slug}_dev25_strongreject.jsonl"))

    results = audit.run(
        str(att_dir), str(clean_dir), str(out), n_expected=5, slugs=[slug]
    )
    assert len(results) == 1

    text = out.read_text(encoding="utf-8")
    assert DECOY not in text
    # sanity: CSV really has our numbers.
    assert "fake_model" in text
    assert "0.5" in text


def test_print_table_has_no_harmful_text(tmp_path, capsys):
    att = tmp_path / "attacked.jsonl"
    clean = tmp_path / "clean.jsonl"
    make_attacked(str(att))
    make_clean(str(clean))
    res = audit.audit_model(str(att), str(clean), n_expected=5)
    res["model"] = "fake_model"
    audit.print_table([res])
    captured = capsys.readouterr()
    assert DECOY not in captured.out
    assert "fake_model" in captured.out
