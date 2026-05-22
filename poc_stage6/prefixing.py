from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PrefixLength = int | str


@dataclass(frozen=True)
class TokenPrefix:
    prefix_length: PrefixLength
    prefix_kind: str
    full_prompt_num_tokens: int
    num_tokens: int
    model_inputs: dict[str, Any]


def parse_prefix_lengths(value: str | None) -> list[PrefixLength]:
    """Parse comma-separated token prefix lengths such as '16,32,64,full'."""

    if value is None or not value.strip():
        return [16, 32, 64, 128, "full"]

    parsed: list[PrefixLength] = []
    for item in value.split(","):
        stripped = item.strip().lower()
        if not stripped:
            continue
        if stripped == "full":
            parsed.append("full")
            continue
        try:
            length = int(stripped)
        except ValueError as exc:
            raise ValueError(
                "prefix lengths must be positive integers or 'full', "
                "for example '16,32,64,128,full'."
            ) from exc
        if length <= 0:
            raise ValueError("prefix lengths must be positive integers.")
        parsed.append(length)

    if not parsed:
        raise ValueError("At least one prefix length is required.")
    return parsed


def _validate_tokenized_prompt(tokenized: Any) -> tuple[Any, Any, int]:
    if "input_ids" not in tokenized:
        raise ValueError("Tokenizer output did not include input_ids.")
    input_ids = tokenized["input_ids"]
    if not hasattr(input_ids, "ndim") or not hasattr(input_ids, "shape"):
        raise TypeError("input_ids must be a tensor-like object.")
    if input_ids.ndim != 2 or int(input_ids.shape[0]) != 1:
        raise ValueError(f"input_ids must have shape [1, seq_len], got {tuple(input_ids.shape)}.")

    full_prompt_num_tokens = int(input_ids.shape[1])
    if full_prompt_num_tokens <= 0:
        raise ValueError("Prompt tokenized to zero tokens.")

    attention_mask = tokenized.get("attention_mask")
    if attention_mask is None:
        attention_mask = input_ids.new_ones(input_ids.shape)
    elif (
        not hasattr(attention_mask, "ndim")
        or not hasattr(attention_mask, "shape")
        or attention_mask.ndim != 2
        or int(attention_mask.shape[0]) != 1
        or int(attention_mask.shape[1]) != full_prompt_num_tokens
    ):
        raise ValueError(
            "attention_mask must have shape [1, seq_len] matching input_ids, "
            f"got {tuple(getattr(attention_mask, 'shape', ())) }."
        )

    return input_ids, attention_mask, full_prompt_num_tokens


def tokenize_prompt_once(tokenizer: Any, prompt_text: str) -> tuple[Any, Any, int]:
    """Tokenize a prompt once without truncation or decoding."""

    if not isinstance(prompt_text, str):
        raise TypeError(f"prompt_text must be a string, got {type(prompt_text).__name__}.")
    tokenized = tokenizer(
        prompt_text,
        return_tensors="pt",
        truncation=False,
        padding=False,
    )
    return _validate_tokenized_prompt(tokenized)


def _prefix_actual_length(
    prefix_length: PrefixLength,
    *,
    full_prompt_num_tokens: int,
    max_length: int,
) -> int:
    if prefix_length == "full":
        requested = full_prompt_num_tokens
    elif isinstance(prefix_length, int):
        requested = prefix_length
    else:
        raise TypeError(f"Unsupported prefix length type: {type(prefix_length).__name__}.")
    return max(1, min(int(requested), full_prompt_num_tokens, max_length))


def make_token_prefixes(
    tokenizer: Any,
    prompt_text: str,
    prefix_lengths: list[PrefixLength],
    *,
    max_length: int,
) -> list[TokenPrefix]:
    """Return model-ready token prefixes without decoding or exposing text."""

    if max_length <= 0:
        raise ValueError("max_length must be positive.")
    if not prefix_lengths:
        raise ValueError("prefix_lengths must contain at least one item.")

    input_ids, attention_mask, full_prompt_num_tokens = tokenize_prompt_once(tokenizer, prompt_text)
    prefixes: list[TokenPrefix] = []
    for prefix_length in prefix_lengths:
        num_tokens = _prefix_actual_length(
            prefix_length,
            full_prompt_num_tokens=full_prompt_num_tokens,
            max_length=max_length,
        )
        prefix_kind = "full" if prefix_length == "full" else "fixed"
        prefixes.append(
            TokenPrefix(
                prefix_length=prefix_length,
                prefix_kind=prefix_kind,
                full_prompt_num_tokens=full_prompt_num_tokens,
                num_tokens=num_tokens,
                model_inputs={
                    "input_ids": input_ids[:, :num_tokens],
                    "attention_mask": attention_mask[:, :num_tokens],
                },
            )
        )
    return prefixes

