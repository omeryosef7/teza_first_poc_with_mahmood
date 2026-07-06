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
        # Paths are relative to self.model (the HF model object).
        # Qwen3ForCausalLM:                 self.model .model        .layers  → "model.layers"
        # Gemma4ForConditionalGeneration:   self.model .model        .language_model .layers → "model.language_model.layers"
        for attr_path in (
            "model.layers",
            "model.language_model.layers",
            "language_model.model.layers",
            "layers",
        ):
            obj = self.model
            try:
                for part in attr_path.split("."):
                    obj = getattr(obj, part)
                return obj
            except AttributeError:
                continue
        raise RuntimeError(
            f"Unable to find transformer layers in {type(self.model).__name__}. "
            "Tried: model.layers, model.language_model.layers, "
            "language_model.model.layers, layers"
        )

    @property
    def num_layers(self) -> int:
        return len(self.layers)

    @property
    def base_model(self) -> Any:
        """Text decoder without LM head — avoids materializing the logit matrix (seq × vocab).
        Use this for forward passes that only need intermediate hidden states via hooks."""
        for attr_path in ("model.language_model", "model"):
            obj = self.model
            try:
                for part in attr_path.split("."):
                    obj = getattr(obj, part)
                return obj
            except AttributeError:
                continue
        raise RuntimeError(f"Cannot find base text model in {type(self.model).__name__}")

    @property
    def attn_modules(self) -> list[Any]:
        return [layer.self_attn for layer in self.layers]

    @property
    def mlp_modules(self) -> list[Any]:
        return [layer.mlp for layer in self.layers]

    @property
    def hidden_size(self) -> int:
        cfg = self.model.config
        if hasattr(cfg, "hidden_size"):
            return int(cfg.hidden_size)
        # Multimodal models (Gemma4) expose text dims under text_config
        if hasattr(cfg, "text_config") and hasattr(cfg.text_config, "hidden_size"):
            return int(cfg.text_config.hidden_size)
        raise RuntimeError(f"Cannot determine hidden_size from {type(cfg).__name__}")

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
    device_map: str = "auto",
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

    # Use bfloat16 (model native dtype) with default SDPA dispatch.
    # On L40S (sm89), SDPA auto-selects FlashAttention2 for bfloat16, handling
    # 34K-token puzzle traces in O(n) memory. All SLURM scripts pin to L40S nodes
    # (n-801..n-805) so V100 (sm70, no flash for bf16) is never hit.
    # Checkpoints are always saved as float32 (.detach().float().cpu()) so dtype
    # changes across runs do not affect checkpoint compatibility.
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map=device_map,
        trust_remote_code=True,
        cache_dir=cache_dir,
        attn_implementation="sdpa",
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
    device_map: str = "auto",
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

    # Same bfloat16 + default SDPA as load_qwen3_model(). Gemma4 E4B-it also
    # loads in bfloat16 natively; FlashAttention2 on L40S handles its head_dim=256
    # and GQA structure for sequences up to 34K tokens.
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map=device_map,
        trust_remote_code=True,
        cache_dir=cache_dir,
        attn_implementation="sdpa",
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
