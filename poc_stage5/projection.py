from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectionRequest:
    layers: str | None
    token_regions: str | None
    max_length: int | None


def describe_projection_request(request: ProjectionRequest) -> dict[str, object]:
    """Describe planned projection settings without running model inference."""

    return {
        "layers": request.layers,
        "token_regions": request.token_regions,
        "max_length": request.max_length,
        "status": "skeleton_only_no_projection_computed",
    }


def compute_projection_dynamics(*args: object, **kwargs: object) -> None:
    """Placeholder for future refusal-direction projection computation."""

    raise NotImplementedError(
        "Stage 5 projection dynamics are not implemented yet. "
        "This skeleton must not load models or run inference."
    )


# TODO(stage5): Parse token regions, capture activations, and project activations onto refusal directions.

