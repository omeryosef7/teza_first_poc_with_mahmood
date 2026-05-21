from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE4A1_ARTIFACT_VERSION = "stage4a1_v1"
INTERVENTION_SELECTED = "intervention_selected"
PROVISIONAL_SELECTION = "provisional_projection_diagnostic_only"
PROVISIONAL_SELECTION_CRITERION = "max_projection_separation_auxiliary_not_final"


@dataclass(frozen=True)
class PromptSplit:
    harmful_train: list[str]
    harmless_train: list[str]
    harmful_validation: list[str]
    harmless_validation: list[str]


@dataclass(frozen=True)
class ExtractionConfig:
    model_name: str
    output_dir: Path
    dry_run: bool
    num_harmful: int
    num_harmless: int
    batch_size: int
    positions: list[int]
    enable_thinking: bool
    seed: int
    overwrite: bool
    use_builtin_prompts: bool
    resume: bool = False
    checkpoint_dir: Path | None = None
    no_progress: bool = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return make_json_safe(value.item())
        except Exception:
            return str(value)
    return value


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(make_json_safe(payload), handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def config_as_metadata(config: ExtractionConfig) -> dict[str, Any]:
    payload = asdict(config)
    payload["output_dir"] = str(config.output_dir)
    if config.checkpoint_dir is not None:
        payload["checkpoint_dir"] = str(config.checkpoint_dir)
    return payload
