from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


DEFAULT_QWEN3_MODEL = "Qwen/Qwen3-14B"


def _hf_cache_dir() -> str | None:
    for env_name in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE", "HF_HOME"):
        value = os.environ.get(env_name)
        if value:
            return value
    return None


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

    @property
    def cpu_offload_entries(self) -> dict[str, str]:
        summary = self.device_summary
        return {
            str(key): str(value)
            for key, value in summary.items()
            if str(value).lower().startswith(("cpu", "disk", "meta"))
        }

    def format_prompts(self, prompts: list[str], *, enable_thinking: bool) -> list[str]:
        formatted: list[str] = []
        for prompt in prompts:
            messages = [{"role": "user", "content": prompt}]
            kwargs: dict = dict(tokenize=False, add_generation_prompt=True)
            if enable_thinking:
                kwargs["enable_thinking"] = True
            try:
                text = self.tokenizer.apply_chat_template(messages, **kwargs)
            except TypeError:
                # Tokenizer doesn't support enable_thinking kwarg — fall back to standard call
                text = self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
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


def load_qwen3_model(
    model_name: str = DEFAULT_QWEN3_MODEL,
    *,
    require_cuda: bool = False,
    log_device_placement: bool = False,
) -> Qwen3Model:
    if require_cuda and not torch.cuda.is_available():
        raise RuntimeError(
            f"CUDA is not available for {model_name}. "
            "Refusing to load Qwen3-14B without GPU because this run is expected to use CUDA."
        )

    cache_dir = _hf_cache_dir()
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        cache_dir=cache_dir,
    )
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
        cache_dir=cache_dir,
    ).eval()
    model.requires_grad_(False)

    wrapped = Qwen3Model(model_name=model_name, tokenizer=tokenizer, model=model)

    if log_device_placement:
        cuda_device_count = torch.cuda.device_count()
        print(f"[qwen3_model] model_name={model_name}")
        print(f"[qwen3_model] torch.cuda.is_available={torch.cuda.is_available()}")
        print(f"[qwen3_model] torch.cuda.device_count={cuda_device_count}")
        print(f"[qwen3_model] cache_dir={cache_dir}")
        print(f"[qwen3_model] hf_device_map={wrapped.device_summary}")
        if wrapped.cpu_offload_entries:
            print(f"[qwen3_model] cpu_offload_detected={wrapped.cpu_offload_entries}")
        else:
            print("[qwen3_model] cpu_offload_detected={}")

    return wrapped


def load_gemma4_model(
    model_name: str = "google/gemma-4-E4B-it",
    *,
    require_cuda: bool = False,
    log_device_placement: bool = False,
) -> Qwen3Model:
    """Load a Gemma 4 model using AutoTokenizer + AutoModelForCausalLM.

    Gemma4 E4B-it is text-only; AutoTokenizer is sufficient and avoids the
    torchvision dependency that AutoProcessor's image-processing module requires.
    Thinking is enabled via the chat template kwarg enable_thinking=True, which
    is handled by the Jinja2 chat_template.jinja loaded by the tokenizer.
    """
    if require_cuda and not torch.cuda.is_available():
        raise RuntimeError(
            f"CUDA is not available for {model_name}. "
            "Refusing to load Gemma4 without GPU because this run is expected to use CUDA."
        )

    cache_dir = _hf_cache_dir()
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        cache_dir=cache_dir,
    )
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
        cache_dir=cache_dir,
    ).eval()
    model.requires_grad_(False)

    wrapped = Qwen3Model(model_name=model_name, tokenizer=tokenizer, model=model)

    if log_device_placement:
        cuda_device_count = torch.cuda.device_count()
        print(f"[gemma4_model] model_name={model_name}")
        print(f"[gemma4_model] torch.cuda.is_available={torch.cuda.is_available()}")
        print(f"[gemma4_model] torch.cuda.device_count={cuda_device_count}")
        print(f"[gemma4_model] cache_dir={cache_dir}")
        print(f"[gemma4_model] hf_device_map={wrapped.device_summary}")
        if wrapped.cpu_offload_entries:
            print(f"[gemma4_model] cpu_offload_detected={wrapped.cpu_offload_entries}")
        else:
            print("[gemma4_model] cpu_offload_detected={}")

    return wrapped


# Generic alias — preferred name for non-Qwen3 callers
load_hf_model = load_qwen3_model
