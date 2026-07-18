"""
Suffix span management for GCG optimization.

Bypasses llm_attacks SuffixManager / AttackPrompt char-offset logic entirely.
Instead uses subsequence search to verify suffix boundaries in the tokenized
sequence — safe for BPE tokenizers where char boundaries don't align with
token boundaries.

Token layout for one GCG step:
  [prefix_ids | suffix_ids | target_ids]
   <--------->  <--------->  <--------->
   prefix_slice suffix_slice target_slice
                              loss_slice = slice(target_start-1, target_stop-1)

The prefix is: chat_template(instruction + suffix)[:prefix_end] — i.e. everything
the model sees before the suffix tokens begin. The target is the teacher-forced
safe completion appended directly after the suffix.
"""
from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple

import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.model_adapter import (
    apply_chat_template,
    tokenize_continuation,
    tokenize_prompt,
)


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

@dataclass
class SuffixSpans:
    """
    Complete tokenized representation of one GCG input.

    input_ids: full [seq_len] token ID tensor (CPU, long)
    prefix_len: number of tokens before the suffix
    suffix_slice: slice object for the suffix token positions
    target_slice: slice object for the safe target token positions
    loss_slice:   slice(target_start-1, target_stop-1) — logit positions for CE loss
    suffix_ids_expected: the suffix token IDs we expect at suffix_slice
    target_ids: the target token IDs we expect at target_slice
    """
    input_ids: torch.Tensor
    prefix_len: int
    suffix_slice: slice
    target_slice: slice
    loss_slice: slice
    suffix_ids_expected: List[int]
    target_ids: List[int]

    @property
    def suffix_len(self) -> int:
        return self.suffix_slice.stop - self.suffix_slice.start

    @property
    def target_len(self) -> int:
        return self.target_slice.stop - self.target_slice.start

    def verify(self) -> None:
        """Assert internal consistency. Raises AssertionError on failure."""
        ids = self.input_ids.tolist()
        actual_suffix = ids[self.suffix_slice]
        assert actual_suffix == self.suffix_ids_expected, (
            f"Suffix mismatch at positions {self.suffix_slice}: "
            f"got {actual_suffix}, expected {self.suffix_ids_expected}"
        )
        actual_target = ids[self.target_slice]
        assert actual_target == self.target_ids, (
            f"Target mismatch at positions {self.target_slice}: "
            f"got {actual_target}, expected {self.target_ids}"
        )
        assert self.suffix_slice.stop <= self.target_slice.start, (
            f"Suffix overlaps/follows target: suffix ends at {self.suffix_slice.stop}, "
            f"target starts at {self.target_slice.start}. "
            "(For user-turn placement a template trailer sits between suffix and target; "
            "for assistant-turn placement they are adjacent — either way stop <= start.)"
        )
        assert self.loss_slice == slice(self.target_slice.start - 1, self.target_slice.stop - 1), (
            f"loss_slice {self.loss_slice} does not match expected "
            f"slice({self.target_slice.start - 1}, {self.target_slice.stop - 1})"
        )


# ---------------------------------------------------------------------------
# Subsequence search (reuses Stage AE utility if available)
# ---------------------------------------------------------------------------

def _find_subsequence(haystack: List[int], needle: List[int], start: int = 0) -> int:
    """
    Find the first occurrence of needle in haystack starting at index start.
    Returns -1 if not found. O(len(haystack) * len(needle)).
    """
    try:
        from poc_stage_ae.thinking_position_utils import _find_subsequence as _ae_impl
        return _ae_impl(haystack, needle, start)
    except (ImportError, AttributeError):
        pass
    # Fallback: identical algorithm
    n, m = len(haystack), len(needle)
    for i in range(start, n - m + 1):
        if haystack[i:i + m] == needle:
            return i
    return -1


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def build_suffix_spans(
    tokenizer: Any,
    model_family: str,
    enable_thinking: bool,
    instruction: str,
    suffix_str: str,
    safe_target: str,
    suffix_ids_override: Optional[List[int]] = None,
    suffix_placement: str = "user",
) -> SuffixSpans:
    """
    Build the full token layout for one GCG input.

    Algorithm:
    1. Format the prompt-only string using the chat template (instruction only,
       with add_generation_prompt=True so we get the assistant turn prefix).
    2. Tokenize the formatted prompt to get prefix_ids.
    3. Use suffix_ids_override if provided (avoids BPE non-invertibility), else
       tokenize suffix_str. Qwen3/tiktoken BPE tokenizers can decode-then-
       re-encode to different tokens (e.g. decode([0,220,0,220,...]) gives a
       string that re-tokenizes via merged " !" → 753, producing fewer tokens).
       Passing suffix_ids_override=<current suffix IDs> bypasses this.
    4. Tokenize safe_target as a bare continuation to get target_ids.
    5. Concatenate: full_ids = prefix_ids + suffix_ids + target_ids.
    6. Verify suffix_ids appear at prefix_len using subsequence search.
    7. Build and return SuffixSpans with verified slices.

    Raises ValueError if suffix_ids cannot be located in full_ids at the
    expected position (indicates tokenizer boundary issue).
    """
    # ------------------------------------------------------------------
    # Resolve suffix + target token ids (shared by both placements).
    # Use suffix_ids_override if provided to avoid BPE decode->encode mismatch.
    # ------------------------------------------------------------------
    if suffix_ids_override is not None:
        suffix_ids: List[int] = list(suffix_ids_override)
        if not suffix_ids:
            raise ValueError("suffix_ids_override is an empty list.")
    else:
        suffix_ids = tokenize_continuation(tokenizer, suffix_str)
        if not suffix_ids:
            raise ValueError(
                f"suffix_str {repr(suffix_str)} tokenized to empty sequence. "
                "Use at least one non-empty token (e.g. '!')."
            )

    target_ids: List[int] = tokenize_continuation(tokenizer, safe_target)
    if not target_ids:
        raise ValueError(
            f"safe_target {repr(safe_target)} tokenized to empty sequence."
        )

    if suffix_placement == "assistant":
        # ==============================================================
        # LEGACY placement (pre-2026-07-19): suffix lands in the ASSISTANT
        # turn (after add_generation_prompt appends the assistant header).
        # This is the BUG documented in docs/GCG_BUGFIX_RERUN_PLAN.md: the
        # optimizer placed the suffix after the assistant header while eval
        # places it in the user turn. Retained VERBATIM for exact v1 replay.
        # ==============================================================
        formatted_prefix = apply_chat_template(
            tokenizer, instruction, model_family, enable_thinking,
            add_generation_prompt=True,
        )
        prefix_ids: List[int] = tokenize_prompt(tokenizer, formatted_prefix)
        full_ids: List[int] = prefix_ids + suffix_ids + target_ids
        expected_start = len(prefix_ids)
        found_at = _find_subsequence(full_ids, suffix_ids, start=expected_start)
        if found_at != expected_start:
            raise ValueError(
                f"Suffix token IDs {suffix_ids} not found at expected position "
                f"{expected_start} in full_ids (found at {found_at}). "
                "This indicates a tokenizer boundary issue — the chat template "
                "may be merging tokens across the instruction/suffix boundary."
            )
        suffix_start = expected_start

    elif suffix_placement == "user":
        # ==============================================================
        # FIXED placement (2026-07-19): suffix lands in the USER turn,
        # exactly where evaluate_optimized_suffixes.py places it
        # (user_content = instruction + suffix_str). This makes the prompt
        # the optimizer scores IN-DISTRIBUTION with the free-generation eval.
        #
        # Construction: split the user turn at the CHARACTER level using an
        # instruction-only render (content-agnostic), hand-assemble
        #   header_ids + suffix_ids + trailer_ids + target_ids
        # keeping suffix_ids a fixed-length known-position block (required by
        # GCG token substitution), then assert byte-equality with eval's exact
        # tokenization of the whole prompt; warn (not fail) on BPE boundary merge.
        # ==============================================================
        suffix_text = (
            tokenizer.decode(suffix_ids)
            if suffix_ids_override is not None else suffix_str
        )
        # eval's EXACT prompt string (instruction + suffix in the user turn):
        prompt_with = apply_chat_template(
            tokenizer, instruction + suffix_text, model_family, enable_thinking,
            add_generation_prompt=True,
        )
        # instruction-only render, to split header (<user>..instr) from
        # trailer (<im_end>..<assistant>[..<think>]) at the character level:
        prompt_wo = apply_chat_template(
            tokenizer, instruction, model_family, enable_thinking,
            add_generation_prompt=True,
        )
        content_start = prompt_wo.find(instruction)
        if content_start < 0:
            raise ValueError(
                "Instruction text not found verbatim in its own chat-template "
                "render; cannot locate the user-turn suffix insertion point."
            )
        split = content_start + len(instruction)
        header_str = prompt_wo[:split]     # ...<im_start>user\n{instruction}
        trailer_str = prompt_wo[split:]    # <im_end>\n<im_start>assistant\n[<think>...]
        header_ids = tokenize_prompt(tokenizer, header_str)
        trailer_ids = tokenize_continuation(tokenizer, trailer_str)
        full_prompt_ids = header_ids + suffix_ids + trailer_ids

        # In-distribution guard: hand-assembly should match eval's exact
        # tokenization of the whole prompt. A mismatch = a BPE boundary merge
        # at the instruction/suffix or suffix/<im_end> junction; placement is
        # still correct (user turn) but not byte-identical to eval for this suffix.
        eval_ids = tokenize_prompt(tokenizer, prompt_with)
        if full_prompt_ids != eval_ids:
            warnings.warn(
                "[build_suffix_spans] user-turn hand-assembly differs from eval's "
                f"tokenization by a boundary token (suffix_ids={suffix_ids}); "
                "placement is correct but not byte-identical to eval for this suffix.",
                RuntimeWarning,
            )
        full_ids = full_prompt_ids + target_ids
        suffix_start = len(header_ids)

    else:
        raise ValueError(
            f"Unknown suffix_placement {suffix_placement!r}; expected 'user' or 'assistant'."
        )

    # ------------------------------------------------------------------
    # Build slices (target is always the tail of full_ids; a template trailer
    # may sit between suffix and target in user placement, none in assistant).
    # ------------------------------------------------------------------
    suffix_slice = slice(suffix_start, suffix_start + len(suffix_ids))
    target_start = len(full_ids) - len(target_ids)
    target_end = len(full_ids)
    target_slice = slice(target_start, target_end)
    loss_slice = slice(target_start - 1, target_end - 1)

    spans = SuffixSpans(
        input_ids=torch.tensor(full_ids, dtype=torch.long),
        prefix_len=suffix_start,
        suffix_slice=suffix_slice,
        target_slice=target_slice,
        loss_slice=loss_slice,
        suffix_ids_expected=suffix_ids,
        target_ids=target_ids,
    )
    spans.verify()
    return spans


def replace_suffix(
    spans: SuffixSpans,
    new_suffix_ids: torch.Tensor,
    tokenizer: Optional[Any] = None,
) -> SuffixSpans:
    """
    Return a new SuffixSpans with the suffix replaced by new_suffix_ids.

    GCG maintains fixed-length suffixes: asserts len(new_suffix_ids) == spans.suffix_len.
    The target and loss slices are unchanged (same fixed offset).

    If tokenizer is provided, optionally verify the new suffix decodes and
    re-tokenizes to the same length (get_filtered_cands guard).
    """
    new_ids = new_suffix_ids.tolist() if isinstance(new_suffix_ids, torch.Tensor) else list(new_suffix_ids)
    if len(new_ids) != spans.suffix_len:
        raise ValueError(
            f"replace_suffix: new_suffix_ids length {len(new_ids)} != "
            f"spans.suffix_len {spans.suffix_len}. GCG requires fixed-length suffixes."
        )

    old_full = spans.input_ids.tolist()
    new_full = (
        old_full[:spans.suffix_slice.start]
        + new_ids
        + old_full[spans.suffix_slice.stop:]
    )

    new_spans = SuffixSpans(
        input_ids=torch.tensor(new_full, dtype=torch.long),
        prefix_len=spans.prefix_len,
        suffix_slice=spans.suffix_slice,
        target_slice=spans.target_slice,
        loss_slice=spans.loss_slice,
        suffix_ids_expected=new_ids,
        target_ids=spans.target_ids,
    )
    new_spans.verify()
    return new_spans


# ---------------------------------------------------------------------------
# Candidate filtering (GCG tokenizer-consistency guard)
# ---------------------------------------------------------------------------

def get_filtered_cands(
    tokenizer: Any,
    candidate_ids: torch.Tensor,
    curr_suffix_ids: List[int],
    suffix_len: int,
    filter_cand: bool = True,
) -> List[List[int]]:
    """
    Filter candidate suffix token batches for tokenizer consistency.

    For each candidate row in candidate_ids [batch, suffix_len]:
      - Decode to string (skip_special_tokens=True)
      - Re-tokenize with add_special_tokens=False
      - Accept only if re-tokenized length == suffix_len AND decoded != current suffix
    Rejected candidates are replaced by padding with the last valid candidate.

    Returns list of accepted candidate token ID lists.
    """
    cands: List[List[int]] = []
    rejected = 0

    curr_decoded = tokenizer.decode(curr_suffix_ids, skip_special_tokens=True)

    for i in range(candidate_ids.shape[0]):
        row = candidate_ids[i].tolist()
        decoded = tokenizer.decode(row, skip_special_tokens=True)
        if filter_cand:
            retokenized = tokenizer(decoded, add_special_tokens=False).input_ids
            if decoded != curr_decoded and len(retokenized) == suffix_len:
                cands.append(row)
            else:
                rejected += 1
        else:
            cands.append(row)

    if filter_cand and cands:
        # Pad back to batch_size with the last valid candidate
        n_total = candidate_ids.shape[0]
        cands = cands + [cands[-1]] * (n_total - len(cands))
    elif filter_cand and not cands:
        # All rejected — return current suffix repeated
        cands = [curr_suffix_ids] * candidate_ids.shape[0]

    return cands


def make_init_suffix(suffix_length: int, tokenizer: Any) -> Tuple[str, List[int]]:
    """
    Build the standard GCG initialization suffix: ' !' (space-prefixed) repeated
    suffix_length times.

    The leading-space unit ' !' matches the original Zou et al. GCG reference,
    where the control string is joined to the goal as f"{goal} {control}" so the
    control's first in-context token is space-prefixed (' !'). Using ' !' here
    makes our in-context suffix tokens identical to the reference's control tokens
    ([' !'] * suffix_length) and guarantees a space separates the instruction from
    the suffix in `instruction + suffix_str` (used by both optimizer and eval),
    instead of merging ("...bomb! !" -> "...bomb ! !"). See docs/GCG_BUGFIX_RERUN_PLAN.md.

    Returns (suffix_str, token_ids). If ' !' tokenizes to more than 1 token per
    repetition, the length is padded to reach exactly suffix_length total tokens
    by truncating or repeating the base unit.
    """
    base_str = " !"
    base_ids = tokenizer(base_str, add_special_tokens=False).input_ids
    tokens_per_unit = len(base_ids)

    if tokens_per_unit == 0:
        raise ValueError("'! ' tokenized to empty sequence — unexpected for this tokenizer.")

    if tokens_per_unit == 1:
        suffix_str = base_str * suffix_length
        suffix_ids = base_ids * suffix_length
    else:
        # Take enough full repetitions; truncate or extend to exact length
        repeats = (suffix_length + tokens_per_unit - 1) // tokens_per_unit
        all_ids = (base_ids * repeats)[:suffix_length]
        suffix_ids = all_ids
        suffix_str = tokenizer.decode(all_ids, skip_special_tokens=True)

    return suffix_str, suffix_ids
