from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any

import torch


@dataclass(frozen=True)
class ProjectionSelection:
    selected_position_index: int
    selected_position: int
    selected_layer: int
    selected_score: float
    selected_harmful_projection_mean: float
    selected_harmless_projection_mean: float


def _safe_std(values: torch.Tensor) -> float:
    if values.numel() <= 1:
        return 0.0
    return float(values.std(unbiased=False).item())


def compute_projection_diagnostics(
    candidate_directions: torch.Tensor,
    harmful_validation_activations: torch.Tensor,
    harmless_validation_activations: torch.Tensor,
    *,
    positions: list[int],
) -> tuple[list[dict[str, Any]], ProjectionSelection]:
    if candidate_directions.ndim != 3:
        raise ValueError("candidate_directions must have shape [n_position, n_layer, d_model].")
    if harmful_validation_activations.shape[1:] != candidate_directions.shape:
        raise ValueError("Harmful validation activations do not match candidate direction shape.")
    if harmless_validation_activations.shape[1:] != candidate_directions.shape:
        raise ValueError("Harmless validation activations do not match candidate direction shape.")
    if len(positions) != candidate_directions.shape[0]:
        raise ValueError("Number of position labels does not match candidate direction tensor.")

    diagnostics: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None

    for position_index, position in enumerate(positions):
        for layer in range(candidate_directions.shape[1]):
            direction = candidate_directions[position_index, layer]
            harmful_projection = harmful_validation_activations[:, position_index, layer, :] @ direction
            harmless_projection = harmless_validation_activations[:, position_index, layer, :] @ direction
            harmful_mean = float(harmful_projection.mean().item())
            harmless_mean = float(harmless_projection.mean().item())
            separation = harmful_mean - harmless_mean
            pooled_std = (
                (_safe_std(harmful_projection) ** 2 + _safe_std(harmless_projection) ** 2) / 2.0
            ) ** 0.5
            standardized_separation = separation / pooled_std if pooled_std > 0 else separation
            row = {
                "position_index": position_index,
                "position": position,
                "layer": layer,
                "harmful_projection_mean": harmful_mean,
                "harmless_projection_mean": harmless_mean,
                "projection_separation": separation,
                "pooled_projection_std": pooled_std,
                "standardized_projection_separation": standardized_separation,
            }
            diagnostics.append(row)
            if best is None or float(row["standardized_projection_separation"]) > float(
                best["standardized_projection_separation"]
            ):
                best = row

    if best is None:
        raise ValueError("No projection diagnostics were computed.")

    selection = ProjectionSelection(
        selected_position_index=int(best["position_index"]),
        selected_position=int(best["position"]),
        selected_layer=int(best["layer"]),
        selected_score=float(best["standardized_projection_separation"]),
        selected_harmful_projection_mean=float(best["harmful_projection_mean"]),
        selected_harmless_projection_mean=float(best["harmless_projection_mean"]),
    )
    return diagnostics, selection


def summarize_diagnostics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [float(row["standardized_projection_separation"]) for row in rows]
    return {
        "num_candidate_directions": len(rows),
        "max_standardized_projection_separation": max(scores) if scores else None,
        "mean_standardized_projection_separation": mean(scores) if scores else None,
        "min_standardized_projection_separation": min(scores) if scores else None,
    }

