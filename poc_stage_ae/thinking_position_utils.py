"""
Stage 3 — Named token-position location for the A/D/E/G early-token expansion study.

Given a model_family ("qwen3" | "gemma4"), the full token-ID sequence
(prompt_token_ids + generation_token_ids), and the prompt/generation boundary
index (== len(prompt_token_ids)), locate a small set of *named* absolute token
positions used by downstream hidden-state replay (Stage 4) and analysis
(Stage 9).

Positions are located by TOKEN-ID SUBSEQUENCE search (sliding window over the
generation segment), never by string matching — this avoids subtle mismatches
between what the tokenizer decodes and what was actually generated.

Thinking-enabled conditions (A, D) — 7 named positions:
    prefill_last        last prompt token index (== boundary_index - 1)
    startofthink         first token of the thinking-start marker
    think_content_1/2/3  first 1st/2nd/3rd tokens strictly after the marker
    endofthink            first token of the thinking-end marker
    endofresponse         last valid generated token index

Thinking-disabled conditions (E, G) — 5 named positions:
    prefill_last          last prompt token index
    answer_content_1/2/3  first 1st/2nd/3rd generated tokens
    endofresponse         last valid generated token index

If a marker cannot be found, the corresponding position(s) are set to None
and an explicit error code is recorded in the parallel `errors` dict — this
function NEVER raises for a missing marker (only for malformed inputs).

Error codes:
    "start_marker_not_found"
    "end_marker_not_found"
    "end_marker_before_start_marker"
    "insufficient_think_content_tokens"
    "insufficient_answer_content_tokens"
    "empty_generation"
"""
from __future__ import annotations

from typing import Any

from poc_stage4.model_family_utils import (
    THINKING_MARKERS_BY_FAMILY,
    get_thinking_end_token_ids,
    get_thinking_start_token_ids,
    think_start_in_prefill,
)

_THINKING_ENABLED_POSITION_NAMES = (
    "prefill_last", "startofthink", "think_content_1", "think_content_2",
    "think_content_3", "endofthink", "endofresponse",
)
_THINKING_DISABLED_POSITION_NAMES = (
    "prefill_last", "answer_content_1", "answer_content_2", "answer_content_3",
    "endofresponse",
)


def _find_subsequence(haystack: list[int], needle: list[int], start: int = 0) -> int:
    """Return the index of the first occurrence of needle in haystack at or after
    `start`, or -1 if not found. Sliding-window exact match on token IDs."""
    if not needle:
        return -1
    n = len(needle)
    limit = len(haystack) - n
    for i in range(start, limit + 1):
        if haystack[i:i + n] == needle:
            return i
    return -1


def locate_positions(
    *,
    model_family: str,
    tokenizer: Any,
    full_token_ids: list[int],
    boundary_index: int,
    enable_thinking: bool,
) -> tuple[dict[str, int | None], dict[str, str]]:
    """Locate named token positions in `full_token_ids`.

    Args:
        model_family: "qwen3" | "gemma4"
        tokenizer: HF tokenizer for `model_family` (used to encode marker strings)
        full_token_ids: prompt_token_ids + generation_token_ids, concatenated
        boundary_index: len(prompt_token_ids) — index of the first generated token
        enable_thinking: whether this row used enable_thinking=True (selects the
            7-position A/D schema vs the 5-position E/G schema)

    Returns:
        (positions, errors) — positions maps position name -> absolute index into
        full_token_ids (or None if not locatable); errors maps position name ->
        explicit error code string for any position that could not be located
        (only present for positions with errors).
    """
    positions: dict[str, int | None] = {}
    errors: dict[str, str] = {}

    n_total = len(full_token_ids)
    generation_ids = full_token_ids[boundary_index:]

    # prefill_last — always available if there is at least one prompt token.
    if boundary_index >= 1:
        positions["prefill_last"] = boundary_index - 1
    else:
        positions["prefill_last"] = None
        errors["prefill_last"] = "empty_prompt"

    if not generation_ids:
        # No generated tokens at all — every remaining position is unlocatable.
        names = _THINKING_ENABLED_POSITION_NAMES if enable_thinking else _THINKING_DISABLED_POSITION_NAMES
        for name in names:
            if name == "prefill_last":
                continue
            positions[name] = None
            errors[name] = "empty_generation"
        return positions, errors

    if enable_thinking and think_start_in_prefill(model_family):
        # The chat template emitted the think-START marker in the PREFILL (e.g.
        # DeepSeek-R1-Distill: input ends "<think>\n"), so "<think>" is never in the
        # generated text. Think content therefore begins at the first GENERATED token
        # (boundary_index). We still locate the prefill "<think>" (for startofthink)
        # and search the generated tokens for the end marker "</think>".
        start_ids = get_thinking_start_token_ids(tokenizer, model_family)
        end_ids = get_thinking_end_token_ids(tokenizer, model_family)

        # startofthink: the "<think>" marker, located in the PREFILL region.
        start_rel = _find_subsequence(full_token_ids[:boundary_index], start_ids, start=0)
        positions["startofthink"] = start_rel if start_rel != -1 else None
        if start_rel == -1:
            errors["startofthink"] = "start_marker_not_found"

        # think_content_1/2/3: first 3 tokens of the generated thinking span.
        content_start = boundary_index
        for idx, name in enumerate(("think_content_1", "think_content_2", "think_content_3")):
            pos = content_start + idx
            positions[name] = pos if pos < n_total else None
            if positions[name] is None:
                errors[name] = "insufficient_think_content_tokens"

        end_rel = _find_subsequence(full_token_ids, end_ids, start=content_start)
        if end_rel == -1:
            positions["endofthink"] = None
            errors["endofthink"] = "end_marker_not_found"
        else:
            positions["endofthink"] = end_rel

        positions["endofresponse"] = n_total - 1
    elif enable_thinking:
        start_ids = get_thinking_start_token_ids(tokenizer, model_family)
        end_ids = get_thinking_end_token_ids(tokenizer, model_family)

        start_rel = _find_subsequence(full_token_ids, start_ids, start=boundary_index)
        if start_rel == -1:
            positions["startofthink"] = None
            errors["startofthink"] = "start_marker_not_found"
            for name in ("think_content_1", "think_content_2", "think_content_3", "endofthink"):
                positions[name] = None
                errors[name] = "start_marker_not_found"
        else:
            positions["startofthink"] = start_rel
            content_start = start_rel + len(start_ids)

            # think_content_1/2/3: first 3 tokens strictly after the start marker.
            available = n_total - content_start
            if available < 3:
                for idx, name in enumerate(("think_content_1", "think_content_2", "think_content_3")):
                    pos = content_start + idx
                    positions[name] = pos if pos < n_total else None
                    if positions[name] is None:
                        errors[name] = "insufficient_think_content_tokens"
            else:
                positions["think_content_1"] = content_start
                positions["think_content_2"] = content_start + 1
                positions["think_content_3"] = content_start + 2

            end_rel = _find_subsequence(full_token_ids, end_ids, start=content_start)
            if end_rel == -1:
                positions["endofthink"] = None
                errors["endofthink"] = "end_marker_not_found"
            elif end_rel < start_rel:
                positions["endofthink"] = None
                errors["endofthink"] = "end_marker_before_start_marker"
            else:
                positions["endofthink"] = end_rel

        positions["endofresponse"] = n_total - 1
    else:
        # answer_content_1/2/3: first 3 generated tokens (no thinking span to skip).
        available = len(generation_ids)
        if available < 3:
            for idx, name in enumerate(("answer_content_1", "answer_content_2", "answer_content_3")):
                pos = boundary_index + idx
                positions[name] = pos if pos < n_total else None
                if positions[name] is None:
                    errors[name] = "insufficient_answer_content_tokens"
        else:
            positions["answer_content_1"] = boundary_index
            positions["answer_content_2"] = boundary_index + 1
            positions["answer_content_3"] = boundary_index + 2

        positions["endofresponse"] = n_total - 1

    return positions, errors


def position_names_for_condition(enable_thinking: bool) -> tuple[str, ...]:
    return _THINKING_ENABLED_POSITION_NAMES if enable_thinking else _THINKING_DISABLED_POSITION_NAMES
