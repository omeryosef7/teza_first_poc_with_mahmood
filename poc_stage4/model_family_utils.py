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
    "phi4": "microsoft/Phi-4-mini-reasoning",
    "deepseek_llama": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
}

DEFAULT_MODEL_SLUG_BY_FAMILY: dict[str, str] = {
    "qwen3": "qwen3-14b",
    "gemma4": "gemma4-e4b-it",
    "deepseek_r1": "deepseek-r1-distill-qwen-7b",
    "phi4": "phi-4-mini-reasoning",
    "deepseek_llama": "deepseek-r1-distill-llama-8b",
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
    # phi4 (Phi-4-mini-reasoning): the model GENERATES <think> as its first output tokens (like qwen3);
    # template ends at <|assistant|> with NO reasoning delimiter. BPE CONTEXT-DEPENDENCE (verified live +
    # against 35/35 real generations): the model always emits "<think>\n", where the ">" MERGES with the
    # newline into a single BPE token → generation starts [33313,881,523,...]. But standalone "<think>"
    # encodes to [33313,881,29] (">"=29), which never appears as a subsequence in the generation → the
    # marker is "not found" and all think positions come out NaN. Fix: match the AS-GENERATED form
    # "<think>\n" = [33313,881,523], so locate_positions finds the start and think_content_1 = first real
    # think token. (end kept as "</think>"; Phi-4 attack CoTs rarely close, so endofthink is usually None.)
    "phi4": {
        "start": "<think>\n",
        "end": "</think>",
    },
    # deepseek_llama (DeepSeek-R1-Distill-Llama-8B): <think>/</think> are single ADDED SPECIAL tokens
    # (128013/128014) — no BPE context-dependence. Emits <think> in the PREFILL (like the Qwen-7B distill).
    "deepseek_llama": {
        "start": "<think>",
        "end": "</think>",
    },
}

# Whether the model's chat template emits the thinking-START marker in the PREFILL
# (so the model generates only the think *content* + end marker), rather than the
# model generating the start marker itself.
#   qwen3 / gemma4 : model GENERATES "<think>"/"<|channel>thought" -> start marker is
#                    found by scanning the GENERATED tokens (default behavior).
#   deepseek_r1    : DeepSeek-R1-Distill's template appends "<think>\n" to the prompt
#                    (formatted input ends "<｜Assistant｜><think>\n"), so "<think>" is
#                    NEVER in the generated text -> think content starts at the first
#                    generated token. See locate_positions() in thinking_position_utils.
# Confirmed live from each family's chat template.
THINK_START_IN_PREFILL_BY_FAMILY: dict[str, bool] = {
    "qwen3": False,
    "gemma4": False,
    "deepseek_r1": True,
    "phi4": False,   # model generates <think> (found by scanning generated tokens), like qwen3
    "deepseek_llama": True,   # template ends "<｜Assistant｜><think>\n" → <think> in prefill (like deepseek_r1)
}


def think_start_in_prefill(model_family: str) -> bool:
    """True if `model_family`'s chat template emits the think-start marker in the
    prefill (think content begins at the first generated token). Defaults to False
    for any family not explicitly listed."""
    return THINK_START_IN_PREFILL_BY_FAMILY.get(model_family, False)

# Segment label hints used when scanning Stage 6 token_table rows to find the
# thinking boundary. The token_table may label the thinking section differently
# per model family; include multiple hints to be robust.
THINKING_SEGMENT_HINTS_BY_FAMILY: dict[str, list[str]] = {
    "qwen3": ["think"],
    "gemma4": ["think", "channel", "thought"],
    "deepseek_r1": ["think"],
    "phi4": ["think"],
    "deepseek_llama": ["think"],
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
