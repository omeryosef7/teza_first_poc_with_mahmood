"""
Shared utilities for model-family-aware loading and thinking-boundary-marker resolution.

Two model families are supported across the poc_stage4 pipeline:
  qwen3  — Qwen/Qwen3-14B
             Thinking delimited by <think> ... </think>
  gemma4 — google/gemma-4-E4B-it
             Thinking delimited by <|channel>thought ... <channel|>
             (Gemma 4 wraps thinking in a "thought channel" block; the final answer starts
              immediately after <channel|>. The start marker has a mandatory newline after it
              in practice but we store the token string itself here.)

Both families reuse the same Qwen3Model wrapper (load_gemma4_model returns a Qwen3Model) and
access transformer layers via model.model.layers, so activation-capture code is identical.
Only the HF loader and the thinking-boundary token strings differ.

Exports:
  DEFAULT_MODEL_BY_FAMILY       — canonical HF model name per family
  DEFAULT_MODEL_SLUG_BY_FAMILY  — short slug used in default output dir names
  THINKING_MARKERS_BY_FAMILY    — {"start": ..., "end": ...} per family
  load_model_by_family()        — dispatch to the correct HF loader
  get_thinking_end_token_ids()  — token IDs for the end-of-thinking marker
  get_thinking_start_token_ids()— token IDs for the start-of-thinking marker
"""
from __future__ import annotations

from typing import Any

DEFAULT_MODEL_BY_FAMILY: dict[str, str] = {
    "qwen3": "Qwen/Qwen3-14B",
    "gemma4": "google/gemma-4-E4B-it",
    "deepseek_r1": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
}

DEFAULT_MODEL_SLUG_BY_FAMILY: dict[str, str] = {
    "qwen3": "qwen3-14b",
    "gemma4": "gemma4-e4b-it",
    "deepseek_r1": "deepseek-r1-distill-qwen-7b",
}

# Both start AND end markers are stored. The end marker alone is ambiguous for Gemma4
# (<channel|> closes the thought channel; having the start marker enables robust detection
# and avoids false positives when scanning token sequences).
# deepseek_r1 shares Qwen3's exact <think>/</think> marker strings (it's a Qwen2.5-backbone
# distillation of R1's reasoning traces) -- confirmed live from its tokenizer_config.json.
THINKING_MARKERS_BY_FAMILY: dict[str, dict[str, str]] = {
    "qwen3": {
        "start": "<think>",
        "end": "</think>",
    },
    "gemma4": {
        "start": "<|channel>thought",
        "end": "<channel|>",
    },
    "deepseek_r1": {
        "start": "<think>",
        "end": "</think>",
    },
}

# Segment label hints used when scanning Stage 6 token_table rows to find the
# thinking boundary. The token_table may label the thinking section differently
# per model family; include multiple hints to be robust.
THINKING_SEGMENT_HINTS_BY_FAMILY: dict[str, list[str]] = {
    "qwen3": ["think"],
    "gemma4": ["think", "channel", "thought"],
    "deepseek_r1": ["think"],
}


def load_model_by_family(model_name: str, model_family: str, **kwargs: Any) -> Any:
    """Load a Qwen3 or Gemma4 model using the correct HF loader for its family.

    Mirrors the pattern used in poc_stage6/batch_redacted_export_all.py.
    Both loaders return a Qwen3Model instance.
    """
    if model_family == "gemma4":
        from poc_stage4.qwen3_model import load_gemma4_model
        return load_gemma4_model(model_name, **kwargs)
    from poc_stage4.qwen3_model import load_hf_model
    return load_hf_model(model_name, **kwargs)


def get_thinking_end_token_ids(tokenizer: Any, model_family: str) -> list[int]:
    """Return token ID sequence for the end-of-thinking marker of the given family.

    Qwen3:  </think>    (one or more token IDs)
    Gemma4: <channel|>  (one or more token IDs)
    """
    marker = THINKING_MARKERS_BY_FAMILY[model_family]["end"]
    ids = tokenizer.encode(marker, add_special_tokens=False)
    if not ids:
        raise ValueError(
            f"Tokenizer returned empty encoding for end-of-thinking marker {marker!r} "
            f"(model_family={model_family!r}). "
            "Check that the correct tokenizer is loaded for this model family."
        )
    return ids


def get_thinking_start_token_ids(tokenizer: Any, model_family: str) -> list[int]:
    """Return token ID sequence for the start-of-thinking marker of the given family.

    Qwen3:  <think>          (one or more token IDs)
    Gemma4: <|channel>thought (one or more token IDs)
    """
    marker = THINKING_MARKERS_BY_FAMILY[model_family]["start"]
    ids = tokenizer.encode(marker, add_special_tokens=False)
    if not ids:
        raise ValueError(
            f"Tokenizer returned empty encoding for start-of-thinking marker {marker!r} "
            f"(model_family={model_family!r})."
        )
    return ids
