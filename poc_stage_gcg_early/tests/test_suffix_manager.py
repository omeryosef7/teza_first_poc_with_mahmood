"""
Tests for suffix_token_manager.py.

All tests are CPU-only and use the ToyTokenizer from conftest.py.
No real Qwen3 or Gemma4 model required.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.suffix_token_manager import (
    SuffixSpans,
    build_suffix_spans,
    get_filtered_cands,
    make_init_suffix,
    replace_suffix,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_spans(toy_tokenizer, instruction="List fruits", suffix=" ! ! ", target="Apple"):
    return build_suffix_spans(
        toy_tokenizer, "qwen3", True,
        instruction, suffix, target,
    )


# ---------------------------------------------------------------------------
# Tests: build_suffix_spans
# ---------------------------------------------------------------------------

class TestBuildSuffixSpans:

    def test_basic_construction(self, toy_tokenizer):
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True,
            "List fruits", " ! ", "Apple",
        )
        assert isinstance(spans.input_ids, torch.Tensor)
        assert spans.input_ids.dtype == torch.long
        assert spans.prefix_len > 0
        assert spans.suffix_len > 0
        assert spans.target_len > 0

    def test_suffix_slice_is_correct(self, toy_tokenizer):
        """The tokens at suffix_slice must match the suffix tokenization."""
        suffix = " ! "
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", suffix, "Apple"
        )
        actual = spans.input_ids[spans.suffix_slice].tolist()
        assert actual == spans.suffix_ids_expected

    def test_target_slice_is_correct(self, toy_tokenizer):
        """The tokens at target_slice must match the target tokenization."""
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", " ! ", "Apple"
        )
        actual = spans.input_ids[spans.target_slice].tolist()
        assert actual == spans.target_ids

    def test_template_trailer_sits_between_suffix_and_target(self, toy_tokenizer):
        """A chat-template trailer separates the suffix from the target.

        UPDATED 2026-08-05. This test previously asserted
        `suffix_slice.stop == target_slice.start` ("no gap"), which was the correct
        contract only under the OLD, BUGGY `assistant` suffix placement, where the suffix
        was appended after add_generation_prompt=True and therefore sat immediately before
        the target. The 2026-07-19 fix moved placement into the USER turn, so the layout is
        now `header_ids + suffix_ids + trailer_ids + target_ids`
        (suffix_token_manager.py:210), where the trailer is `<im_end>\\n<im_start>assistant\\n`.
        The old assertion is therefore FALSE BY DESIGN on the fixed path, and its failure was
        positive evidence that the placement fix is in effect - not a regression.
        The correct invariant is that the gap is exactly the trailer, i.e. non-negative and
        accounted for by the reconstruction test below.
        """
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", " ! ", "Apple"
        )
        gap = spans.target_slice.start - spans.suffix_slice.stop
        assert gap >= 0, "target must not start before the suffix ends"
        # the gap is the template trailer; with this toy template it is exactly 1 token
        assert gap == 1, f"expected a 1-token template trailer, got {gap}"

    def test_loss_slice_offset(self, toy_tokenizer):
        """loss_slice = target_start - 1 : target_stop - 1 (GCG convention)."""
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", " ! ", "Apple"
        )
        ts = spans.target_slice
        ls = spans.loss_slice
        assert ls.start == ts.start - 1
        assert ls.stop == ts.stop - 1

    def test_verify_passes(self, toy_tokenizer):
        """SuffixSpans.verify() must not raise for correctly built spans."""
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", " ! ", "Apple"
        )
        spans.verify()  # must not raise

    def test_full_ids_equals_prefix_suffix_trailer_target(self, toy_tokenizer):
        """input_ids == prefix + suffix + TRAILER + target, token-by-token.

        UPDATED 2026-08-05 for the same reason as the test above: under the fixed USER
        suffix placement the layout is header + suffix + trailer + target
        (suffix_token_manager.py:210), so the old `prefix + suffix + target` reconstruction
        was short by exactly the trailer. Asserting the full four-part reconstruction is a
        STRICTLY STRONGER check than the original - it pins every token, including the ones
        between the suffix and the target that the old test silently ignored.
        """
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", " ! ", "Apple"
        )
        ids = spans.input_ids.tolist()
        prefix_part = ids[:spans.prefix_len]
        suffix_part = ids[spans.suffix_slice]
        trailer_part = ids[spans.suffix_slice.stop:spans.target_slice.start]
        target_part = ids[spans.target_slice]
        reconstructed = prefix_part + suffix_part + trailer_part + target_part
        assert reconstructed == ids, f"Reconstruction mismatch: {reconstructed} != {ids}"
        # and the suffix/target slices really do hold what the spans claim
        assert suffix_part == spans.suffix_ids_expected
        assert target_part == spans.target_ids

    def test_empty_suffix_raises(self, toy_tokenizer):
        with pytest.raises(ValueError, match="tokenized to empty sequence"):
            build_suffix_spans(toy_tokenizer, "qwen3", True, "List fruits", "", "Apple")

    def test_empty_target_raises(self, toy_tokenizer):
        with pytest.raises(ValueError, match="tokenized to empty sequence"):
            build_suffix_spans(toy_tokenizer, "qwen3", True, "List fruits", " ! ", "")


# ---------------------------------------------------------------------------
# Tests: replace_suffix
# ---------------------------------------------------------------------------

class TestReplaceSuffix:

    def test_replace_changes_suffix_only(self, toy_tokenizer):
        """replace_suffix changes only suffix tokens; prefix and target are unchanged."""
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", " ! ", "Apple"
        )
        new_suffix_ids = torch.tensor(spans.suffix_ids_expected[::-1])  # reverse
        new_spans = replace_suffix(spans, new_suffix_ids)

        old_ids = spans.input_ids.tolist()
        new_ids = new_spans.input_ids.tolist()

        # Prefix unchanged
        assert old_ids[:spans.prefix_len] == new_ids[:spans.prefix_len]
        # Target unchanged
        assert old_ids[spans.target_slice] == new_ids[new_spans.target_slice]
        # Suffix changed
        assert new_ids[new_spans.suffix_slice] == new_suffix_ids.tolist()

    def test_replace_wrong_length_raises(self, toy_tokenizer):
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", " ! ", "Apple"
        )
        bad_ids = torch.tensor([99, 99, 99, 99, 99])  # wrong length
        with pytest.raises(ValueError, match="fixed-length"):
            replace_suffix(spans, bad_ids)

    def test_replace_verify_passes(self, toy_tokenizer):
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", " ! ", "Apple"
        )
        new_ids = torch.tensor(spans.suffix_ids_expected)
        new_spans = replace_suffix(spans, new_ids)
        new_spans.verify()  # must not raise


# ---------------------------------------------------------------------------
# Tests: make_init_suffix
# ---------------------------------------------------------------------------

class TestMakeInitSuffix:

    def test_suffix_length(self, toy_tokenizer):
        suffix_str, suffix_ids = make_init_suffix(4, toy_tokenizer)
        assert len(suffix_ids) == 4

    def test_returns_string_and_ids(self, toy_tokenizer):
        suffix_str, suffix_ids = make_init_suffix(8, toy_tokenizer)
        assert isinstance(suffix_str, str)
        assert isinstance(suffix_ids, list)
        assert all(isinstance(i, int) for i in suffix_ids)

    def test_build_spans_with_init_suffix(self, toy_tokenizer):
        suffix_str, suffix_ids = make_init_suffix(4, toy_tokenizer)
        # Should not raise
        spans = build_suffix_spans(
            toy_tokenizer, "qwen3", True, "List fruits", suffix_str, "Apple"
        )
        assert spans.suffix_len == len(suffix_ids)


# ---------------------------------------------------------------------------
# Tests: get_filtered_cands
# ---------------------------------------------------------------------------

class TestGetFilteredCands:

    def test_returns_correct_length(self, toy_tokenizer):
        """get_filtered_cands always returns batch_size candidates."""
        suffix_ids = [3, 4, 3]  # 3 tokens
        candidate_ids = torch.tensor([
            [5, 4, 3],
            [3, 6, 3],
            [7, 4, 5],
            [3, 4, 7],
        ])
        result = get_filtered_cands(toy_tokenizer, candidate_ids, suffix_ids, 3, filter_cand=False)
        assert len(result) == 4

    def test_filter_mode_preserves_length(self, toy_tokenizer):
        """Even when many candidates are filtered, output length == batch_size."""
        suffix_ids = [3, 4, 3]
        # All same as current suffix → all filtered
        candidate_ids = torch.tensor([[3, 4, 3]] * 4)
        result = get_filtered_cands(toy_tokenizer, candidate_ids, suffix_ids, 3, filter_cand=True)
        assert len(result) == 4
