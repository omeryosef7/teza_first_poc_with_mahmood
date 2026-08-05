"""
Model-family-aware utilities for Qwen3 and Gemma4.

Replaces llm_attacks.base.attack_manager.get_embedding_{layer,matrix} and
get_embeddings, which enumerate only GPTJForCausalLM / LlamaForCausalLM /
GPTNeoXForCausalLM and raise ValueError for Qwen3 or Gemma4.

All functions accept a model_family string ("qwen3" | "gemma4" | "llama") and
dispatch accordingly. The embedding paths were verified against Stage AE model loading:
  Qwen3:  model.model.embed_tokens  (standard decoder)
  Gemma4: model.language_model.embed_tokens  (Gemma4Model.language_model is the text decoder)
  Llama:  model.model.embed_tokens  (LlamaForCausalLM, same layout as Qwen3)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, List, Optional

import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ---------------------------------------------------------------------------
# Embedding access
# ---------------------------------------------------------------------------

_EMBED_PATHS_BY_FAMILY = {
    "qwen3": ["model.embed_tokens"],
    # Gemma4ForConditionalGeneration: .model → Gemma4Model, .language_model → text decoder
    "gemma4": ["model.language_model.embed_tokens", "model.embed_tokens",
               "language_model.model.embed_tokens"],
    # LlamaForCausalLM: standard decoder, same layout as Qwen3 (P9.0 item 3)
    "llama": ["model.embed_tokens"],
}
_EMBED_PATHS_FALLBACK = [
    "model.embed_tokens",
    "model.language_model.embed_tokens",
    "language_model.model.embed_tokens",
    "transformer.wte",
]


def _resolve_embed_layer(model: Any, model_family: str) -> Any:
    """Walk attribute paths to find the embedding layer."""
    candidates = _EMBED_PATHS_BY_FAMILY.get(model_family, []) + _EMBED_PATHS_FALLBACK
    for attr_path in candidates:
        obj = model
        try:
            for part in attr_path.split("."):
                obj = getattr(obj, part)
            return obj
        except AttributeError:
            continue
    raise ValueError(
        f"Cannot locate embedding layer for model family '{model_family}' "
        f"(type: {type(model).__name__}). "
        f"Tried paths: {candidates}"
    )


def get_embedding_layer(model: Any, model_family: str) -> Any:
    """Return the embedding layer module (e.g. nn.Embedding)."""
    return _resolve_embed_layer(model, model_family)


def get_embedding_matrix(model: Any, model_family: str) -> torch.Tensor:
    """Return the embedding weight matrix [vocab_size, d_model]."""
    return _resolve_embed_layer(model, model_family).weight


def get_embeddings(model: Any, input_ids: torch.Tensor, model_family: str) -> torch.Tensor:
    """Embed input_ids using the model's embedding layer. Returns [batch, seq, d_model]."""
    embed_layer = _resolve_embed_layer(model, model_family)
    return embed_layer(input_ids)


# ---------------------------------------------------------------------------
# EOS handling (Gemma4 has multiple valid EOS IDs)
# ---------------------------------------------------------------------------

def get_effective_eos_ids(model: Any, tokenizer: Any) -> List[int]:
    """
    Return the full list of valid EOS token IDs for this model.

    Reads model.generation_config.eos_token_id first (may be list or scalar),
    falls back to tokenizer.eos_token_id. Always returns list[int].

    Gemma4 has multiple valid EOS IDs (e.g. [1, 106, 50]). Using only the
    first entry causes mislabeled finish reasons — Stage AE hit this bug.
    """
    try:
        from poc_stage4.qwen3_model import _get_effective_eos_ids as _ae_impl
        return _ae_impl(model, tokenizer)
    except (ImportError, AttributeError):
        pass

    # Fallback implementation (mirrors Stage AE pattern exactly)
    raw = None
    try:
        raw = model.generation_config.eos_token_id
    except AttributeError:
        pass
    if raw is None:
        raw = tokenizer.eos_token_id
    if raw is None:
        raise RuntimeError("Cannot determine EOS token IDs for this model/tokenizer pair.")
    if isinstance(raw, int):
        return [raw]
    if isinstance(raw, list):
        return [int(x) for x in raw]
    return [int(raw)]


# ---------------------------------------------------------------------------
# Chat template
# ---------------------------------------------------------------------------

def apply_chat_template(
    tokenizer: Any,
    user_content: str,
    model_family: str,
    enable_thinking: bool,
    add_generation_prompt: bool = True,
) -> str:
    """
    Format a single-turn user message using the model's chat template.

    Uses tokenizer.apply_chat_template with enable_thinking kwarg, falling
    back (TypeError) for tokenizers that don't support it (Gemma4).

    Returns the formatted string (not token IDs).
    """
    messages = [{"role": "user", "content": user_content}]
    kwargs = dict(tokenize=False, add_generation_prompt=add_generation_prompt)
    try:
        return tokenizer.apply_chat_template(
            messages, **kwargs, enable_thinking=enable_thinking
        )
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs)


def tokenize_prompt(
    tokenizer: Any,
    formatted_prompt: str,
) -> List[int]:
    """
    Tokenize a pre-formatted prompt string.

    Uses add_special_tokens=False because apply_chat_template already includes
    the BOS token in the formatted string for most models.
    """
    return tokenizer(formatted_prompt, add_special_tokens=False).input_ids


def tokenize_continuation(
    tokenizer: Any,
    text: str,
) -> List[int]:
    """
    Tokenize a suffix or target string as a bare continuation (no special tokens).
    """
    return tokenizer(text, add_special_tokens=False).input_ids
