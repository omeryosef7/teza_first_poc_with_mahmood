from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poc_stage4.schemas import INTERVENTION_SELECTED, PROVISIONAL_SELECTION, read_json


@dataclass(frozen=True)
class LoadedDirection:
    direction: Any
    metadata: dict[str, Any]
    direction_path: Path
    metadata_path: Path


def load_direction(
    output_dir: str | Path,
    *,
    allow_provisional_direction: bool = False,
) -> LoadedDirection:
    """Load a selected direction, rejecting provisional Stage 4A1 directions by default."""

    base = Path(output_dir)
    direction_path = base / "direction.pt"
    metadata_path = base / "selected_direction.json"
    if not direction_path.exists():
        raise FileNotFoundError(f"Missing direction tensor: {direction_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing direction metadata: {metadata_path}")

    metadata = read_json(metadata_path)
    selection_status = metadata.get("selection_status")
    if selection_status != INTERVENTION_SELECTED and not allow_provisional_direction:
        extra = ""
        if selection_status == PROVISIONAL_SELECTION:
            extra = " This is a Stage 4A1 provisional projection-diagnostic direction."
        raise RuntimeError(
            "Refusing to load a non-final refusal direction by default."
            f"{extra} Run Stage 4A2 intervention-based selection first, or pass "
            "`allow_provisional_direction=True` / `--allow-provisional-direction` only for smoke tests."
        )

    import torch

    return LoadedDirection(
        direction=torch.load(direction_path, map_location="cpu"),
        metadata=metadata,
        direction_path=direction_path,
        metadata_path=metadata_path,
    )
