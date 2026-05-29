from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

import torch


DEFAULT_MAX_NEW_TOKENS = 32768
DEFAULT_DO_SAMPLE = False
DEFAULT_SEED = 0


@dataclass(frozen=True)
class QwenGenerationResult:
    input_text: str
    generation_text: str
    think_text: str | None
    final_text: str | None
    thinking_segmentation_status: str
    input_token_ids: list[int]
    generation_token_ids: list[int]
    input_num_tokens: int
    generation_num_tokens: int
    think_num_tokens: int
    final_num_tokens: int
    finish_reason: str


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _parse_think_tags(text: str) -> tuple[str | None, str | None, str]:
    start_tag = "<think>"
    end_tag = "</think>"
    start = text.find(start_tag)
    end = text.find(end_tag)
    if start >= 0 and end >= 0 and end > start:
        think_text = text[start + len(start_tag):end]
        final_text = text[end + len(end_tag):]
        return think_text, final_text if final_text.strip() else None, "parsed_from_think_tags"
    if start >= 0 or end >= 0:
        return None, text.strip() or None, "not_separable"
    return None, text.strip() or None, "not_present"


def _finish_reason(
    generation_token_ids: list[int],
    *,
    max_new_tokens: int,
    eos_token_id: int | None,
) -> str:
    if not generation_token_ids:
        return "empty"
    if eos_token_id is not None and generation_token_ids[-1] == eos_token_id:
        return "eos_token"
    if len(generation_token_ids) >= max_new_tokens:
        return "max_new_tokens"
    return "unknown"


def run_qwen_inference(
    *,
    tokenizer: Any,
    model: Any,
    prompt_text: str,
    enable_thinking: bool = True,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    do_sample: bool = DEFAULT_DO_SAMPLE,
    seed: int = DEFAULT_SEED,
) -> QwenGenerationResult:
    seed_everything(seed)

    try:
        formatted_prompt: str = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt_text}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=enable_thinking,
        )
    except TypeError as exc:
        raise RuntimeError(
            "Qwen3 chat-template formatting with enable_thinking requires transformers>=4.51.0."
        ) from exc

    inputs = tokenizer(formatted_prompt, return_tensors="pt", add_special_tokens=False)
    device = next(model.parameters()).device
    inputs = {key: value.to(device) for key, value in inputs.items()}

    generation_kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": do_sample,
        "return_dict_in_generate": True,
        "eos_token_id": tokenizer.eos_token_id,
        "pad_token_id": tokenizer.pad_token_id,
    }

    with torch.inference_mode():
        generated = model.generate(**inputs, **generation_kwargs)

    full_ids: list[int] = [int(t) for t in generated.sequences[0].tolist()]
    prompt_len = inputs["input_ids"].shape[1]
    input_token_ids = full_ids[:prompt_len]
    generation_token_ids = full_ids[prompt_len:]

    generation_text: str = tokenizer.decode(generation_token_ids, skip_special_tokens=False)
    think_text, final_text, seg_status = _parse_think_tags(generation_text)

    think_num_tokens = 0
    final_num_tokens = 0
    if think_text is not None:
        try:
            think_num_tokens = len(tokenizer(think_text, add_special_tokens=False)["input_ids"])
        except Exception:
            think_num_tokens = 0
    if final_text is not None:
        try:
            final_num_tokens = len(tokenizer(final_text, add_special_tokens=False)["input_ids"])
        except Exception:
            final_num_tokens = 0

    return QwenGenerationResult(
        input_text=formatted_prompt,
        generation_text=generation_text,
        think_text=think_text,
        final_text=final_text,
        thinking_segmentation_status=seg_status,
        input_token_ids=input_token_ids,
        generation_token_ids=generation_token_ids,
        input_num_tokens=len(input_token_ids),
        generation_num_tokens=len(generation_token_ids),
        think_num_tokens=think_num_tokens,
        final_num_tokens=final_num_tokens,
        finish_reason=_finish_reason(
            generation_token_ids,
            max_new_tokens=max_new_tokens,
            eos_token_id=tokenizer.eos_token_id,
        ),
    )
