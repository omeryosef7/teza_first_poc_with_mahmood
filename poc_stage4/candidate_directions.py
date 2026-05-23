from __future__ import annotations

import random

import torch

from poc_stage4.schemas import PromptSplit


def split_prompts(
    harmful_prompts: list[str],
    harmless_prompts: list[str],
    *,
    seed: int,
    validation_fraction: float = 0.25,
) -> PromptSplit:
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1.")
    if len(harmful_prompts) < 2 or len(harmless_prompts) < 2:
        raise ValueError("At least two harmful and two harmless prompts are required.")

    rng = random.Random(seed)

    def split(items: list[str]) -> tuple[list[str], list[str]]:
        shuffled = list(items)
        rng.shuffle(shuffled)
        n_validation = max(1, int(round(len(shuffled) * validation_fraction)))
        n_validation = min(n_validation, len(shuffled) - 1)
        validation = shuffled[:n_validation]
        train = shuffled[n_validation:]
        return train, validation

    harmful_train, harmful_validation = split(harmful_prompts)
    harmless_train, harmless_validation = split(harmless_prompts)
    return PromptSplit(
        harmful_train=harmful_train,
        harmless_train=harmless_train,
        harmful_validation=harmful_validation,
        harmless_validation=harmless_validation,
    )


def generate_candidate_directions(
    harmful_train_activations: torch.Tensor,
    harmless_train_activations: torch.Tensor,
    *,
    direction_normalization: str = "unit",
) -> torch.Tensor:
    """Generate candidate directions as [n_position, n_layer, d_model]."""

    if harmful_train_activations.ndim != 4 or harmless_train_activations.ndim != 4:
        raise ValueError("Activation tensors must have shape [n_prompt, n_position, n_layer, d_model].")
    if harmful_train_activations.shape[1:] != harmless_train_activations.shape[1:]:
        raise ValueError("Harmful and harmless activation tensors must match after the prompt dimension.")

    harmful_mean = harmful_train_activations.mean(dim=0)
    harmless_mean = harmless_train_activations.mean(dim=0)
    candidate_directions = harmful_mean - harmless_mean
    if direction_normalization == "raw":
        return candidate_directions
    if direction_normalization != "unit":
        raise ValueError(
            f"Unsupported direction_normalization={direction_normalization!r}. "
            "Expected 'unit' or 'raw'."
        )
    norms = candidate_directions.norm(dim=-1, keepdim=True).clamp_min(1e-12)
    return candidate_directions / norms

