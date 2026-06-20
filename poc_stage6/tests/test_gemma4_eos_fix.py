"""Unit tests for Gemma 4 EOS fix — no GPU or real model required."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from poc_stage6.export_qwen_token_trace import (
    normalize_eos_token_ids,
    get_effective_eos_token_ids,
    validate_gemma_generation,
    _evaluate_strongreject,
)


# ---------------------------------------------------------------------------
# normalize_eos_token_ids
# ---------------------------------------------------------------------------

def test_normalize_none_returns_empty():
    assert normalize_eos_token_ids(None) == []


def test_normalize_scalar_wraps_to_list():
    assert normalize_eos_token_ids(1) == [1]


def test_normalize_list_unchanged():
    assert normalize_eos_token_ids([1, 106]) == [1, 106]


# ---------------------------------------------------------------------------
# get_effective_eos_token_ids
# ---------------------------------------------------------------------------

def _mock_model(gen_config_eos):
    model = MagicMock()
    model.generation_config.eos_token_id = gen_config_eos
    return model


def _mock_tokenizer(eos_token_id, unk_token_id=0, turn_end_id=106):
    tok = MagicMock()
    tok.eos_token_id = eos_token_id
    tok.unk_token_id = unk_token_id
    tok.convert_tokens_to_ids.return_value = turn_end_id
    return tok


def test_gemma4_scalar_eos_gets_turn_end_appended():
    model = _mock_model(gen_config_eos=1)
    tok = _mock_tokenizer(eos_token_id=1, turn_end_id=106)
    result = get_effective_eos_token_ids(model, tok, "gemma4")
    assert result == [1, 106]


def test_gemma4_already_has_turn_end_no_duplicate():
    model = _mock_model(gen_config_eos=[1, 106])
    tok = _mock_tokenizer(eos_token_id=1, turn_end_id=106)
    result = get_effective_eos_token_ids(model, tok, "gemma4")
    assert result == [1, 106]


def test_qwen3_eos_list_unchanged():
    model = _mock_model(gen_config_eos=[1, 151645])
    tok = _mock_tokenizer(eos_token_id=151645)
    result = get_effective_eos_token_ids(model, tok, "qwen3")
    assert result == [1, 151645]


def test_gemma4_turn_end_resolves_to_unk_raises():
    model = _mock_model(gen_config_eos=1)
    tok = _mock_tokenizer(eos_token_id=1, unk_token_id=999, turn_end_id=999)
    with pytest.raises(ValueError, match="unknown-token"):
        get_effective_eos_token_ids(model, tok, "gemma4")


# ---------------------------------------------------------------------------
# validate_gemma_generation
# ---------------------------------------------------------------------------

EFFECTIVE_EOS = [1, 106]
TURN_END = 106

def test_generation_ending_with_turn_end_is_valid():
    result = validate_gemma_generation(
        generation_token_ids=[10, 20, 30, TURN_END],
        turn_end_id=TURN_END,
        effective_eos_ids=EFFECTIVE_EOS,
        finish_reason="eos_token",
    )
    assert result["generation_valid"] is True
    assert result["turn_end_count"] == 1
    assert result["turn_end_repetition_detected"] is False
    assert result["ended_with_turn_end"] is True
    assert result["ended_with_valid_eos"] is True


def test_generation_ending_with_regular_eos_is_valid():
    result = validate_gemma_generation(
        generation_token_ids=[10, 20, 30, 1],
        turn_end_id=TURN_END,
        effective_eos_ids=EFFECTIVE_EOS,
        finish_reason="eos_token",
    )
    assert result["generation_valid"] is True
    assert result["turn_end_count"] == 0
    assert result["ended_with_turn_end"] is False
    assert result["ended_with_valid_eos"] is True


def test_repeated_turn_end_is_invalid():
    result = validate_gemma_generation(
        generation_token_ids=[10, TURN_END, TURN_END, TURN_END],
        turn_end_id=TURN_END,
        effective_eos_ids=EFFECTIVE_EOS,
        finish_reason="eos_token",
    )
    assert result["generation_valid"] is False
    assert result["turn_end_repetition_detected"] is True
    assert result["turn_end_count"] == 3


def test_turn_end_not_at_end_is_invalid():
    result = validate_gemma_generation(
        generation_token_ids=[TURN_END, 10, 20],
        turn_end_id=TURN_END,
        effective_eos_ids=EFFECTIVE_EOS,
        finish_reason="eos_token",
    )
    assert result["generation_valid"] is False


def test_max_new_tokens_finish_is_invalid():
    result = validate_gemma_generation(
        generation_token_ids=[10, 20, 30],
        turn_end_id=TURN_END,
        effective_eos_ids=EFFECTIVE_EOS,
        finish_reason="max_new_tokens",
    )
    assert result["generation_valid"] is False


def test_empty_generation_is_invalid():
    result = validate_gemma_generation(
        generation_token_ids=[],
        turn_end_id=TURN_END,
        effective_eos_ids=EFFECTIVE_EOS,
        finish_reason="empty",
    )
    assert result["generation_valid"] is False


# ---------------------------------------------------------------------------
# StrongREJECT gating via run_allowed
# ---------------------------------------------------------------------------

def test_strongreject_not_run_when_generation_invalid():
    source_row = {"goal": "test", "target_response": "original"}
    result = _evaluate_strongreject(
        source_row=source_row,
        evaluated_text="some text",
        run_allowed=False,
    )
    assert result["strongreject_status"] == "not_run"


# ---------------------------------------------------------------------------
# Semantic answer validity checks
# ---------------------------------------------------------------------------

def test_final_assistant_text_with_turn_end_fails_semantic_check():
    final_assistant_text = "Here is the answer.<turn|>"
    semantic_answer_valid = (
        final_assistant_text is not None
        and bool(final_assistant_text.strip())
        and "<turn|>" not in final_assistant_text
    )
    assert semantic_answer_valid is False


def test_clean_final_assistant_text_passes_semantic_check():
    final_assistant_text = "Here is the answer."
    semantic_answer_valid = (
        final_assistant_text is not None
        and bool(final_assistant_text.strip())
        and "<turn|>" not in final_assistant_text
    )
    assert semantic_answer_valid is True
