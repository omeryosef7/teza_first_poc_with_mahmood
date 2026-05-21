from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


DEFAULT_QWEN3_MODEL = "Qwen/Qwen3-14B"


@dataclass
class Qwen3Model:
    model_name: str
    tokenizer: Any
    model: Any

    @property
    def layers(self) -> Any:
        try:
            return self.model.model.layers
        except AttributeError as exc:
            raise RuntimeError(
                "Unable to find Qwen3 transformer layers at `model.model.layers`. "
                "This Stage 4A1 wrapper currently supports Hugging Face Qwen3 causal LM models only."
            ) from exc

    @property
    def num_layers(self) -> int:
        return len(self.layers)

    @property
    def attn_modules(self) -> list[Any]:
        return [layer.self_attn for layer in self.layers]

    @property
    def mlp_modules(self) -> list[Any]:
        return [layer.mlp for layer in self.layers]

    @property
    def hidden_size(self) -> int:
        return int(self.model.config.hidden_size)

    @property
    def device_summary(self) -> dict[str, str]:
        device_map = getattr(self.model, "hf_device_map", None)
        if device_map is not None:
            return {str(key): str(value) for key, value in device_map.items()}
        try:
            return {"first_parameter_device": str(next(self.model.parameters()).device)}
        except StopIteration:
            return {}

    def format_prompts(self, prompts: list[str], *, enable_thinking: bool) -> list[str]:
        formatted: list[str] = []
        for prompt in prompts:
            messages = [{"role": "user", "content": prompt}]
            try:
                text = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                    enable_thinking=enable_thinking,
                )
            except TypeError as exc:
                raise RuntimeError(
                    "Qwen3 chat-template formatting with `enable_thinking` requires a recent "
                    "transformers version. Install transformers>=4.51.0 for Qwen3 support."
                ) from exc
            formatted.append(str(text))
        return formatted

    def tokenize_prompts(self, prompts: list[str], *, enable_thinking: bool) -> Any:
        formatted = self.format_prompts(prompts, enable_thinking=enable_thinking)
        return self.tokenizer(
            formatted,
            padding=True,
            truncation=False,
            return_tensors="pt",
        )


def load_qwen3_model(model_name: str = DEFAULT_QWEN3_MODEL) -> Qwen3Model:
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    ).eval()
    model.requires_grad_(False)

    return Qwen3Model(model_name=model_name, tokenizer=tokenizer, model=model)
