from __future__ import annotations

from typing import Any

import torch

from poc_stage4.qwen3_model import Qwen3Model


def validate_positions(positions: list[int]) -> None:
    if not positions:
        raise ValueError("At least one token position is required.")
    invalid = [position for position in positions if position >= 0]
    if invalid:
        raise ValueError(
            "Stage 4A1 positions must be prompt-end-relative negative offsets, "
            f"for example -1,-2,-3. Invalid values: {invalid}"
        )


def _input_device(model: Any) -> torch.device:
    try:
        embedding = model.get_input_embeddings()
        return embedding.weight.device
    except Exception:
        return next(model.parameters()).device


def _absolute_positions(attention_mask: torch.Tensor, positions: list[int]) -> torch.Tensor:
    token_indices = torch.arange(attention_mask.shape[1], device=attention_mask.device, dtype=torch.long)
    masked_indices = attention_mask.to(dtype=torch.long) * token_indices[None, :]
    last_indices = masked_indices.max(dim=1).values
    offsets = torch.tensor(positions, dtype=torch.long, device=attention_mask.device) + 1
    absolute = last_indices[:, None] + offsets[None, :]
    if torch.any(absolute < 0):
        raise ValueError(
            "At least one prompt is shorter than the requested negative token positions. "
            "Use fewer positions or longer prompts."
        )
    selected_mask = attention_mask.gather(1, absolute)
    if torch.any(selected_mask == 0):
        raise ValueError(
            "At least one requested prompt-end-relative position resolves to padding. "
            "Use fewer positions or longer prompts."
        )
    return absolute


def capture_residual_input_activations(
    model_base: Qwen3Model,
    prompts: list[str],
    *,
    positions: list[int],
    batch_size: int,
    enable_thinking: bool,
) -> torch.Tensor:
    """Capture residual stream inputs as [n_prompt, n_position, n_layer, d_model]."""

    validate_positions(positions)
    if batch_size <= 0:
        raise ValueError("batch_size must be positive.")

    layers = model_base.layers
    n_layers = model_base.num_layers
    d_model = model_base.hidden_size
    n_positions = len(positions)
    all_batches: list[torch.Tensor] = []
    input_device = _input_device(model_base.model)

    for start in range(0, len(prompts), batch_size):
        batch_prompts = prompts[start : start + batch_size]
        tokenized = model_base.tokenize_prompts(batch_prompts, enable_thinking=enable_thinking)
        attention_mask = tokenized.attention_mask.to(input_device)
        absolute_positions = _absolute_positions(attention_mask, positions)
        batch_cache = torch.zeros(
            (len(batch_prompts), n_positions, n_layers, d_model),
            dtype=torch.float32,
            device="cpu",
        )
        hooks = []

        def make_hook(layer_index: int):
            def hook(module: Any, inputs: tuple[Any, ...]) -> None:
                activation = inputs[0].detach()
                positions_on_device = absolute_positions.to(activation.device)
                for batch_index in range(activation.shape[0]):
                    selected = activation[batch_index, positions_on_device[batch_index], :]
                    batch_cache[batch_index, :, layer_index, :] = selected.to(
                        dtype=torch.float32,
                        device="cpu",
                    )

            return hook

        for layer_index, layer in enumerate(layers):
            hooks.append(layer.register_forward_pre_hook(make_hook(layer_index)))

        try:
            with torch.no_grad():
                model_base.model(
                    input_ids=tokenized.input_ids.to(input_device),
                    attention_mask=attention_mask,
                )
        finally:
            for hook in hooks:
                hook.remove()

        all_batches.append(batch_cache)
        del batch_cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not all_batches:
        raise ValueError("No prompts were provided.")
    return torch.cat(all_batches, dim=0)
