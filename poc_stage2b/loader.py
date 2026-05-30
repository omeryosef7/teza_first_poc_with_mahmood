from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("goal", "goal_index", "attack_prompt", "target_model")


@dataclass(frozen=True)
class Stage2Row:
    goal_index: int
    goal: str
    attack_prompt: str
    target_model: str
    attack_iteration: int | None
    conversation_id: int | None
    is_success: bool | None
    judge_score: int | None
    strongreject_score: float | None
    example_id: str
    raw: dict[str, Any]


def _make_example_id(row: dict[str, Any]) -> str:
    parts = [
        f"goal_index={row.get('goal_index')}",
        f"attack_iteration={row.get('attack_iteration')}",
        f"conversation_id={row.get('conversation_id')}",
        f"target_model={row.get('target_model')}",
    ]
    return "|".join(parts)


def load_stage2_jsonl(path: str | Path) -> list[Stage2Row]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input JSONL not found: {path}")

    rows: list[Stage2Row] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {path}: {exc}") from exc

            missing = [f for f in REQUIRED_FIELDS if f not in raw or raw[f] is None]
            if missing:
                raise ValueError(f"Row {line_number} is missing required fields: {missing}")

            attack_prompt = raw.get("attack_prompt")
            if not attack_prompt or not str(attack_prompt).strip():
                raise ValueError(f"Row {line_number} has an empty attack_prompt — cannot run Qwen inference without it")

            rows.append(
                Stage2Row(
                    goal_index=int(raw["goal_index"]),
                    goal=str(raw["goal"]),
                    attack_prompt=str(raw["attack_prompt"]),
                    target_model=str(raw["target_model"]),
                    attack_iteration=int(raw["attack_iteration"]) if raw.get("attack_iteration") is not None else None,
                    conversation_id=int(raw["conversation_id"]) if raw.get("conversation_id") is not None else None,
                    is_success=bool(raw["is_success"]) if raw.get("is_success") is not None else None,
                    judge_score=int(raw["judge_score"]) if raw.get("judge_score") is not None else None,
                    strongreject_score=float(raw["strongreject_score"]) if raw.get("strongreject_score") is not None else None,
                    example_id=_make_example_id(raw),
                    raw=raw,
                )
            )

    return rows
