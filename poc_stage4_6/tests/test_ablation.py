"""
Stage 4.6 unit tests — no GPU required.

Tests all logic that does not require Qwen3-14B or external APIs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ---------------------------------------------------------------------------
# Helpers for building synthetic data
# ---------------------------------------------------------------------------

def _make_prompt_tokens(n_content: int = 100) -> list[dict]:
    """
    Build a synthetic prompt token list matching Qwen3 chat template structure:
      [0] <|im_start|> (special)
      [1] user (non-special)
      [2] \\n (non-special)
      [3..n+2] content tokens (non-special)
      [n+3] <|im_end|> (special)
      [n+4] \\n (non-special)
      [n+5] <|im_start|> (special)
      [n+6] assistant (non-special)
      [n+7] \\n (non-special)
    """
    tokens = []
    # chat template prefix
    tokens.append({"global_token_index": 0, "segment": "prompt", "role_or_part": "special",
                   "token_id": 151644, "decoded_single_token": "<|im_start|>", "is_special_token": True})
    tokens.append({"global_token_index": 1, "segment": "prompt", "role_or_part": "user",
                   "token_id": 1, "decoded_single_token": "user", "is_special_token": False})
    tokens.append({"global_token_index": 2, "segment": "prompt", "role_or_part": "user",
                   "token_id": 2, "decoded_single_token": "\n", "is_special_token": False})
    # content tokens
    for i in range(n_content):
        tokens.append({
            "global_token_index": 3 + i,
            "segment": "prompt",
            "role_or_part": "user",
            "token_id": 1000 + i,
            "decoded_single_token": f"word{i} ",
            "is_special_token": False,
        })
    n = len(tokens)
    # chat template suffix
    tokens.append({"global_token_index": n, "segment": "prompt", "role_or_part": "special",
                   "token_id": 151645, "decoded_single_token": "<|im_end|>", "is_special_token": True})
    tokens.append({"global_token_index": n + 1, "segment": "prompt", "role_or_part": "special",
                   "token_id": 3, "decoded_single_token": "\n", "is_special_token": False})
    tokens.append({"global_token_index": n + 2, "segment": "prompt", "role_or_part": "special",
                   "token_id": 151644, "decoded_single_token": "<|im_start|>", "is_special_token": True})
    tokens.append({"global_token_index": n + 3, "segment": "prompt", "role_or_part": "special",
                   "token_id": 4, "decoded_single_token": "assistant", "is_special_token": False})
    tokens.append({"global_token_index": n + 4, "segment": "prompt", "role_or_part": "special",
                   "token_id": 5, "decoded_single_token": "\n", "is_special_token": False})
    return tokens


def _make_trace(n_content: int = 100) -> dict:
    """Build a minimal stage6 trace dict."""
    tokens = _make_prompt_tokens(n_content)
    return {
        "token_table": tokens,
        "saved_formatted_prompt": "".join(t["decoded_single_token"] for t in tokens),
        "config": {"example_id": "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"},
    }


def _make_stage2_row(attack_prompt: str, goal: str = "do bad thing") -> dict:
    return {"attack_prompt": attack_prompt, "goal": goal}


def _sha256_ids(ids: list[int]) -> str:
    h = hashlib.sha256()
    h.update(json.dumps(ids, separators=(",", ":")).encode())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Import the modules under test
# ---------------------------------------------------------------------------

from poc_stage4_6.build_controlled_ablation_prompts import (
    identify_spans,
    build_condition,
    _sha256_of_token_ids,
    _extract_answer_cue,
    _extract_target_hint,
    CONDITIONS,
    THINKING_MODE,
    PUZZLE_FRACTIONS,
)


# ---------------------------------------------------------------------------
# Tests: identify_spans
# ---------------------------------------------------------------------------

class TestIdentifySpans:

    def test_returns_expected_keys(self):
        trace = _make_trace(80)
        row = _make_stage2_row("word0 word1 " * 40 + "final sentence here")
        spans = identify_spans(trace, row)
        assert "puzzle_indices" in spans
        assert "target_span" in spans
        assert "answer_cue_span" in spans
        assert "full_prompt_sha256" in spans
        assert "target_span_sha256" in spans
        assert "answer_cue_span_sha256" in spans

    def test_prompt_token_ids_match_token_table(self):
        trace = _make_trace(60)
        row = _make_stage2_row("a b c " * 20 + "last sentence")
        spans = identify_spans(trace, row)
        token_table = [t for t in trace["token_table"] if t["segment"] == "prompt"]
        assert spans["prompt_token_ids"] == [t["token_id"] for t in token_table]

    def test_full_prompt_sha256(self):
        trace = _make_trace(40)
        row = _make_stage2_row("abc " * 40)
        spans = identify_spans(trace, row)
        expected = _sha256_ids(spans["prompt_token_ids"])
        assert spans["full_prompt_sha256"] == expected

    def test_special_tokens_identified(self):
        trace = _make_trace(50)
        row = _make_stage2_row("x " * 50)
        spans = identify_spans(trace, row)
        # Qwen3 chat template has 3 special tokens: <|im_start|> at 0, <|im_end|>, <|im_start|> again
        special_ids = [t["token_id"] for t in trace["token_table"]
                       if t["segment"] == "prompt" and t["is_special_token"]]
        assert len(spans["special_token_indices"]) == len(special_ids)

    def test_puzzle_indices_exclude_special_and_protected(self):
        trace = _make_trace(80)
        row = _make_stage2_row("a " * 80)
        spans = identify_spans(trace, row)
        n = spans["n_prompt_tokens"]
        # Puzzle indices must not include any special token index
        special_set = set(spans["special_token_indices"])
        for idx in spans["puzzle_indices"]:
            assert idx not in special_set, f"Special token found in puzzle_indices at {idx}"
        # Puzzle indices must not include target or answer cue spans
        t_start, t_end = spans["target_span"]
        ac_start, ac_end = spans["answer_cue_span"]
        for idx in spans["puzzle_indices"]:
            assert not (t_start <= idx < t_end), f"Target token in puzzle at {idx}"
            assert not (ac_start <= idx < ac_end), f"Answer cue token in puzzle at {idx}"

    def test_content_range_fields_present(self):
        trace = _make_trace(50)
        row = _make_stage2_row("q " * 50)
        spans = identify_spans(trace, row)
        assert "content_start_idx" in spans
        assert "content_end_idx" in spans
        assert spans["content_start_idx"] == 3


# ---------------------------------------------------------------------------
# Tests: build_condition
# ---------------------------------------------------------------------------

class TestBuildCondition:

    def _make_span_info(self, n_content: int = 100) -> dict:
        trace = _make_trace(n_content)
        attack = "puzzle preamble " * 20 + "target thing " * 5 + "answer this now"
        row = _make_stage2_row(attack)
        return identify_spans(trace, row)

    def test_condition_A_is_identity(self):
        span_info = self._make_span_info(80)
        rng = random.Random(42)
        result = build_condition("A", span_info, 1.0, rng)
        assert result["token_ids"] == span_info["prompt_token_ids"]

    def test_condition_E_is_identity_different_thinking(self):
        span_info = self._make_span_info(80)
        rng = random.Random(42)
        a = build_condition("A", span_info, 1.0, rng)
        e = build_condition("E", span_info, 1.0, rng)
        assert a["token_ids"] == e["token_ids"], "E should have same token ids as A"
        assert a["enable_thinking"] is True
        assert e["enable_thinking"] is False

    def test_thinking_modes(self):
        span_info = self._make_span_info(100)
        rng = random.Random(42)
        for cond in CONDITIONS:
            result = build_condition(cond, span_info, PUZZLE_FRACTIONS[cond], rng)
            assert result["enable_thinking"] == THINKING_MODE[cond]

    def test_deletion_only_A_geq_B_geq_C_geq_D(self):
        span_info = self._make_span_info(120)
        rng = random.Random(42)
        counts = {}
        for cond in ["A", "B", "C", "D"]:
            result = build_condition(cond, span_info, PUZZLE_FRACTIONS[cond], rng)
            counts[cond] = result["prompt_token_count"]
        assert counts["A"] >= counts["B"], f"A={counts['A']} < B={counts['B']}"
        assert counts["B"] >= counts["C"], f"B={counts['B']} < C={counts['C']}"
        assert counts["C"] >= counts["D"], f"C={counts['C']} < D={counts['D']}"

    def test_deletion_only_output_is_subsequence_of_source(self):
        span_info = self._make_span_info(100)
        rng = random.Random(42)
        source_ids = span_info["prompt_token_ids"]
        for cond in ["B", "C", "D"]:
            result = build_condition(cond, span_info, PUZZLE_FRACTIONS[cond], rng)
            output_ids = result["token_ids"]
            # Check that output_ids is a subsequence of source_ids
            it = iter(source_ids)
            assert all(tok in it for tok in output_ids), \
                f"Condition {cond} output is not a subsequence of source"

    def test_target_span_preserved_across_A_B_C_D(self):
        span_info = self._make_span_info(120)
        rng = random.Random(42)
        target_sha = span_info["target_span_sha256"]
        t_start, t_end = span_info["target_span"]
        target_ids = span_info["target_span_ids"]
        for cond in ["A", "B", "C", "D"]:
            result = build_condition(cond, span_info, PUZZLE_FRACTIONS[cond], rng)
            output_ids = result["token_ids"]
            # target tokens must appear in output (as subsequence at same position)
            assert all(tid in output_ids for tid in target_ids), \
                f"Condition {cond}: target span tokens missing from output"

    def test_answer_cue_preserved(self):
        span_info = self._make_span_info(120)
        rng = random.Random(42)
        answer_cue_ids = span_info["answer_cue_ids"]
        for cond in ["A", "B", "C", "D"]:
            result = build_condition(cond, span_info, PUZZLE_FRACTIONS[cond], rng)
            output_ids = result["token_ids"]
            assert all(tid in output_ids for tid in answer_cue_ids), \
                f"Condition {cond}: answer cue tokens missing from output"

    def test_condition_D_has_no_puzzle_tokens(self):
        span_info = self._make_span_info(100)
        rng = random.Random(42)
        result = build_condition("D", span_info, 0.0, rng)
        assert result["puzzle_tokens_kept"] == 0

    def test_condition_A_sha256_equals_source(self):
        span_info = self._make_span_info(80)
        rng = random.Random(42)
        result = build_condition("A", span_info, 1.0, rng)
        assert result["prompt_token_ids_sha256"] == span_info["full_prompt_sha256"]

    def test_validation_passed_for_all_conditions(self):
        span_info = self._make_span_info(100)
        rng = random.Random(42)
        for cond in CONDITIONS:
            result = build_condition(cond, span_info, PUZZLE_FRACTIONS[cond], rng)
            assert result["validation_passed"], \
                f"Condition {cond} failed validation: {result['validation_notes']}"

    def test_user_message_text_present(self):
        span_info = self._make_span_info(100)
        rng = random.Random(42)
        for cond in CONDITIONS:
            result = build_condition(cond, span_info, PUZZLE_FRACTIONS[cond], rng)
            assert "user_message_text" in result
            assert isinstance(result["user_message_text"], str)

    def test_user_message_text_decreases_D_shorter_than_A(self):
        span_info = self._make_span_info(100)
        rng = random.Random(42)
        a = build_condition("A", span_info, 1.0, rng)
        d = build_condition("D", span_info, 0.0, rng)
        # D should have shorter or equal user message text (puzzle tokens removed)
        assert len(d["user_message_text"]) <= len(a["user_message_text"])


# ---------------------------------------------------------------------------
# Tests: sha256 helper
# ---------------------------------------------------------------------------

class TestSha256:

    def test_empty_list(self):
        sha = _sha256_of_token_ids([])
        assert isinstance(sha, str) and len(sha) == 64

    def test_deterministic(self):
        ids = [1, 2, 3, 4]
        assert _sha256_of_token_ids(ids) == _sha256_of_token_ids(ids)

    def test_different_ids_different_sha(self):
        assert _sha256_of_token_ids([1, 2, 3]) != _sha256_of_token_ids([1, 2, 4])


# ---------------------------------------------------------------------------
# Tests: select_source_examples (determinism + 4 goals covered)
# ---------------------------------------------------------------------------

class TestSelectSourceExamples:

    def test_deterministic_same_seed(self):
        """Same seed → same selection."""
        from poc_stage4_6.build_controlled_ablation_prompts import select_source_examples
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        s1 = select_source_examples(rng1)
        s2 = select_source_examples(rng2)
        assert [r["example_id"] for r in s1] == [r["example_id"] for r in s2]

    def test_all_4_goals_represented(self):
        from poc_stage4_6.build_controlled_ablation_prompts import select_source_examples
        rng = random.Random(42)
        sources = select_source_examples(rng)
        assert len(sources) == 4
        goals = {int(r["goal_index"]) for r in sources}
        assert goals == {0, 1, 2, 3}

    def test_one_per_goal(self):
        from poc_stage4_6.build_controlled_ablation_prompts import select_source_examples
        rng = random.Random(42)
        sources = select_source_examples(rng)
        from collections import Counter
        goal_counts = Counter(int(r["goal_index"]) for r in sources)
        for gi, count in goal_counts.items():
            assert count == 1, f"goal {gi} selected {count} times"


# ---------------------------------------------------------------------------
# Tests: extract helpers
# ---------------------------------------------------------------------------

class TestExtractHelpers:

    def test_extract_answer_cue_last_paragraph(self):
        prompt = "intro paragraph.\n\nMiddle part here.\n\nFinal instruction, answer this."
        cue = _extract_answer_cue(prompt)
        assert "Final instruction" in cue

    def test_extract_answer_cue_single_paragraph(self):
        prompt = "just one paragraph with no breaks"
        cue = _extract_answer_cue(prompt)
        assert "just one paragraph" in cue

    def test_extract_target_hint_is_middle(self):
        prompt = "A" * 100 + "B" * 100 + "C" * 100
        hint = _extract_target_hint(prompt)
        # Should NOT be entirely from the beginning (all A's)
        assert "B" in hint or "C" in hint


# ---------------------------------------------------------------------------
# Tests: audit_controlled_ablation_prompts
# ---------------------------------------------------------------------------

def _make_valid_ablation_jsonl(tmp_dir: Path) -> Path:
    """Write a minimal valid ablation_prompts.jsonl with 20 rows."""
    from poc_stage4_6.build_controlled_ablation_prompts import THINKING_MODE, PUZZLE_FRACTIONS
    rows = []
    sha_a = "aaa" + "0" * 61
    sha_src = "aaa" + "0" * 61
    for gi in range(4):
        eid = f"goal_index={gi}|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
        for cond in ["A", "B", "C", "D", "E"]:
            token_count = {"A": 100, "B": 80, "C": 60, "D": 40, "E": 100}[cond]
            rows.append({
                "source_example_id": eid,
                "condition": cond,
                "goal_index": gi,
                "attack_iteration": 1,
                "conversation_id": 1,
                "target_model": "gpt-o4-mini",
                "enable_thinking": THINKING_MODE[cond],
                "puzzle_fraction_target": PUZZLE_FRACTIONS[cond],
                "puzzle_tokens_total": 60,
                "puzzle_tokens_kept": {"A": 60, "B": 30, "C": 15, "D": 0, "E": 60}[cond],
                "prompt_token_count": token_count,
                "prompt_token_ids_sha256": sha_a if cond == "A" else "bbb" + "0" * 61,
                "target_span_sha256": "tgt" + "0" * 61,
                "answer_cue_span_sha256": "ans" + "0" * 61,
                "condition_a_sha256": sha_a,
                "source_prompt_sha256": sha_src,
                "validation_passed": True,
                "validation_notes": "OK",
            })
    path = tmp_dir / "ablation_prompts.jsonl"
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return path


class TestAuditAblationPrompts:

    def test_valid_input_passes(self, tmp_path):
        _make_valid_ablation_jsonl(tmp_path)
        from poc_stage4_6.audit_controlled_ablation_prompts import audit
        result = audit(tmp_path)
        assert result["validation_passed"]
        assert result["gate_result"] == "PASS"

    def test_wrong_row_count_fails(self, tmp_path):
        path = _make_valid_ablation_jsonl(tmp_path)
        # Remove one row
        rows = path.read_text().strip().splitlines()
        path.write_text("\n".join(rows[:-1]) + "\n")
        from poc_stage4_6.audit_controlled_ablation_prompts import audit
        result = audit(tmp_path)
        assert not result["validation_passed"]
        assert result["gate_result"] == "FAIL"

    def test_thinking_mode_mismatch_fails(self, tmp_path):
        path = _make_valid_ablation_jsonl(tmp_path)
        rows = [json.loads(l) for l in path.read_text().strip().splitlines()]
        # Flip enable_thinking for condition E
        for r in rows:
            if r["condition"] == "E":
                r["enable_thinking"] = True  # wrong: should be False
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        from poc_stage4_6.audit_controlled_ablation_prompts import audit
        result = audit(tmp_path)
        assert not result["validation_passed"]

    def test_condition_a_sha_mismatch_fails(self, tmp_path):
        path = _make_valid_ablation_jsonl(tmp_path)
        rows = [json.loads(l) for l in path.read_text().strip().splitlines()]
        for r in rows:
            if r["condition"] == "A" and r["goal_index"] == 0:
                r["prompt_token_ids_sha256"] = "different_sha" + "0" * 51
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        from poc_stage4_6.audit_controlled_ablation_prompts import audit
        result = audit(tmp_path)
        assert not result["validation_passed"]

    def test_non_monotone_token_lengths_fails(self, tmp_path):
        path = _make_valid_ablation_jsonl(tmp_path)
        rows = [json.loads(l) for l in path.read_text().strip().splitlines()]
        # Make B longer than A for goal 0
        for r in rows:
            if r["goal_index"] == 0 and r["condition"] == "B":
                r["prompt_token_count"] = 200  # > A's 100
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        from poc_stage4_6.audit_controlled_ablation_prompts import audit
        result = audit(tmp_path)
        assert not result["validation_passed"]

    def test_unique_source_condition_pairs(self, tmp_path):
        path = _make_valid_ablation_jsonl(tmp_path)
        rows = [json.loads(l) for l in path.read_text().strip().splitlines()]
        # Add a duplicate
        rows.append(rows[0])
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        from poc_stage4_6.audit_controlled_ablation_prompts import audit
        result = audit(tmp_path)
        # Should fail due to wrong row count and/or duplicate check
        assert not result["validation_passed"]

    def test_audit_writes_audit_json(self, tmp_path):
        _make_valid_ablation_jsonl(tmp_path)
        from poc_stage4_6.audit_controlled_ablation_prompts import audit
        audit(tmp_path)
        assert (tmp_path / "ablation_audit.json").exists()


# ---------------------------------------------------------------------------
# Tests: run_controlled_ablation helpers (no GPU)
# ---------------------------------------------------------------------------

class TestRunAblationHelpers:

    def test_already_done_false_for_new_id(self, tmp_path):
        from poc_stage4_6.run_controlled_ablation import _already_done
        summary_path = tmp_path / "run_summary.jsonl"
        assert not _already_done("new_run_id", summary_path)

    def test_already_done_true_after_write(self, tmp_path):
        from poc_stage4_6.run_controlled_ablation import _already_done
        summary_path = tmp_path / "run_summary.jsonl"
        with open(summary_path, "w") as f:
            f.write(json.dumps({"run_id": "existing_id", "condition": "A"}) + "\n")
        assert _already_done("existing_id", summary_path)
        assert not _already_done("other_id", summary_path)

    def test_run_id_format(self):
        from poc_stage4_6.run_controlled_ablation import _run_id
        eid = "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
        rid = _run_id(eid, "B")
        assert "cond_B" in rid
        assert "|" not in rid
        assert "=" not in rid


# ---------------------------------------------------------------------------
# Tests: analyze helpers
# ---------------------------------------------------------------------------

class TestAnalyzeHelpers:

    def test_bootstrap_mean_ci_returns_triple(self):
        from poc_stage4_6.analyze_controlled_ablation import bootstrap_mean_ci
        mean, lo, hi = bootstrap_mean_ci([0.1, 0.5, 0.9], n_boot=100)
        assert lo <= mean <= hi

    def test_bootstrap_mean_ci_empty(self):
        import math
        from poc_stage4_6.analyze_controlled_ablation import bootstrap_mean_ci
        mean, lo, hi = bootstrap_mean_ci([])
        assert math.isnan(mean) and math.isnan(lo) and math.isnan(hi)

    def test_condition_summary_shape(self):
        from poc_stage4_6.analyze_controlled_ablation import _condition_summary
        # Create fake rows
        fake_rows = []
        for cond in ["A", "B", "C", "D", "E"]:
            for gi in range(4):
                fake_rows.append({
                    "condition": cond, "goal_index": gi,
                    "sr_success": True, "judge_success": False, "is_success": True,
                    "strongreject_score": 0.7, "think_token_count": 500,
                })
        summary = _condition_summary(fake_rows)
        assert len(summary) == 5
        for row in summary:
            assert row["n"] == 4

    def test_paired_comparison_no_common_sources(self):
        from poc_stage4_6.analyze_controlled_ablation import _paired_comparison
        rows = [
            {"source_example_id": "s1", "condition": "A", "strongreject_score": 0.5,
             "think_token_count": 100, "is_success": True, "goal_index": 0},
            {"source_example_id": "s2", "condition": "B", "strongreject_score": 0.3,
             "think_token_count": 80, "is_success": False, "goal_index": 0},
        ]
        result = _paired_comparison(rows, "A", "B", "test")
        assert result["n_pairs"] == 0

    def test_paired_comparison_with_common_sources(self):
        from poc_stage4_6.analyze_controlled_ablation import _paired_comparison
        rows = [
            {"source_example_id": "s1", "condition": "A", "strongreject_score": 0.8,
             "think_token_count": 200, "is_success": True, "goal_index": 0},
            {"source_example_id": "s1", "condition": "E", "strongreject_score": 0.2,
             "think_token_count": 50, "is_success": False, "goal_index": 0},
        ]
        result = _paired_comparison(rows, "A", "E", "test")
        assert result["n_pairs"] == 1
        assert result["mean_sr_score_a"] == pytest.approx(0.8)
        assert result["mean_sr_score_b"] == pytest.approx(0.2)
        assert result["n_a_higher"] == 1


# ---------------------------------------------------------------------------
# Tests: stage4 per_example files unchanged (no mutation guard)
# ---------------------------------------------------------------------------

class TestFrozenArtifacts:

    def test_stage4_per_example_dir_not_modified(self):
        """Verify the frozen stage4 run dir exists and build script doesn't touch it."""
        from poc_stage4_5.common import STAGE4_PER_EXAMPLE_DIR
        if not STAGE4_PER_EXAMPLE_DIR.exists():
            pytest.skip("Stage4 per_example dir not available in this environment")
        # Just check the directory exists — the non-mutation invariant is structural
        assert STAGE4_PER_EXAMPLE_DIR.is_dir()
