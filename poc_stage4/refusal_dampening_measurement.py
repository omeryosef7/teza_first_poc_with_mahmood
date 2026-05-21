from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable

from poc_stage4.direction_loader import LoadedDirection
from poc_stage4.schemas import make_json_safe, read_json, utc_now, write_json


DEFAULT_STAGE2_JSONL = Path("outputs/hijacking_baseline_gpt-o4-mini_small.jsonl")
STAGE4B_ARTIFACT_VERSION = "stage4b_v1"
CONDITIONS = ("direct_harmful", "hijacked_medium", "hijacked_long")


@dataclass(frozen=True)
class PromptCondition:
    goal_index: int
    condition: str
    prompt: str
    goal: str
    stage2_jsonl: str
    stage2_row_identity: dict[str, Any]
    prompt_source_field: str
    prompt_length_tokens: int
    attack_prompt_token_length: int | None
    hijacked_medium_equals_long: bool
    medium_long_comparison_status: str


@dataclass(frozen=True)
class DampeningConfig:
    model_name: str
    direction_dir: Path
    output_dir: Path
    stage2_jsonl: Path
    enable_thinking: bool
    num_goals: int
    dry_run: bool
    allow_provisional_direction: bool
    batch_size: int


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {path}: {exc}") from exc
            row["_stage2_line_number"] = line_number
            rows.append(row)
    return rows


def stage2_row_identity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "line_number": row.get("_stage2_line_number"),
        "goal_index": row.get("goal_index"),
        "attack_iteration": row.get("attack_iteration"),
        "conversation_id": row.get("conversation_id"),
        "target_model": row.get("target_model"),
    }


def _fallback_token_length(text: str) -> int:
    return max(1, len(text.split()))


def make_token_length_fn(tokenizer: Any | None = None) -> Callable[[str], int]:
    if tokenizer is None:
        return _fallback_token_length

    def token_length(text: str) -> int:
        return len(tokenizer.encode(text, add_special_tokens=False))

    return token_length


def build_prompt_conditions(
    *,
    stage2_jsonl: str | Path,
    num_goals: int,
    token_length_fn: Callable[[str], int] | None = None,
) -> tuple[list[PromptCondition], dict[str, Any]]:
    if num_goals <= 0:
        raise ValueError("num_goals must be positive.")

    token_length_fn = token_length_fn or _fallback_token_length
    rows = load_jsonl(stage2_jsonl)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if "goal_index" not in row or "goal" not in row:
            continue
        grouped[int(row["goal_index"])].append(row)

    available_goal_indices = sorted(grouped)
    if len(available_goal_indices) < num_goals:
        raise ValueError(
            f"Requested {num_goals} goals, but only {len(available_goal_indices)} goals are available "
            f"in {stage2_jsonl}. Use a larger Stage 2 artifact or a smaller --num-goals."
        )

    conditions: list[PromptCondition] = []
    medium_equals_long_count = 0
    selected_goal_indices = available_goal_indices[:num_goals]
    for goal_index in selected_goal_indices:
        goal_rows = grouped[goal_index]
        first_row = goal_rows[0]
        goal = str(first_row["goal"])
        attack_rows = [
            row for row in goal_rows if row.get("attack_prompt") is not None and str(row["attack_prompt"]).strip()
        ]
        if not attack_rows:
            raise ValueError(f"Goal {goal_index} has no non-empty Stage 2 attack_prompt rows.")

        attack_candidates = sorted(
            (
                {
                    "row": row,
                    "prompt": str(row["attack_prompt"]),
                    "token_length": token_length_fn(str(row["attack_prompt"])),
                }
                for row in attack_rows
            ),
            key=lambda item: (int(item["token_length"]), int(item["row"].get("_stage2_line_number", 0))),
        )
        medium_candidate = attack_candidates[len(attack_candidates) // 2]
        long_candidate = attack_candidates[-1]
        hijacked_medium_equals_long = (
            len(attack_candidates) == 1
            or medium_candidate["prompt"] == long_candidate["prompt"]
            or stage2_row_identity(medium_candidate["row"]) == stage2_row_identity(long_candidate["row"])
        )
        if hijacked_medium_equals_long:
            medium_equals_long_count += 1
        comparison_status = (
            "not_true_medium_long_comparison"
            if hijacked_medium_equals_long
            else "distinct_medium_and_long_attack_prompts"
        )

        conditions.append(
            PromptCondition(
                goal_index=goal_index,
                condition="direct_harmful",
                prompt=goal,
                goal=goal,
                stage2_jsonl=str(stage2_jsonl),
                stage2_row_identity=stage2_row_identity(first_row),
                prompt_source_field="goal",
                prompt_length_tokens=token_length_fn(goal),
                attack_prompt_token_length=None,
                hijacked_medium_equals_long=hijacked_medium_equals_long,
                medium_long_comparison_status=comparison_status,
            )
        )
        for condition_name, candidate in (
            ("hijacked_medium", medium_candidate),
            ("hijacked_long", long_candidate),
        ):
            conditions.append(
                PromptCondition(
                    goal_index=goal_index,
                    condition=condition_name,
                    prompt=str(candidate["prompt"]),
                    goal=goal,
                    stage2_jsonl=str(stage2_jsonl),
                    stage2_row_identity=stage2_row_identity(candidate["row"]),
                    prompt_source_field="attack_prompt",
                    prompt_length_tokens=int(candidate["token_length"]),
                    attack_prompt_token_length=int(candidate["token_length"]),
                    hijacked_medium_equals_long=hijacked_medium_equals_long,
                    medium_long_comparison_status=comparison_status,
                )
            )

    metadata = {
        "stage2_jsonl": str(stage2_jsonl),
        "num_stage2_rows": len(rows),
        "num_available_goals": len(available_goal_indices),
        "selected_goal_indices": selected_goal_indices,
        "num_goals": num_goals,
        "num_goals_hijacked_medium_equals_long": medium_equals_long_count,
        "prompt_conditions": list(CONDITIONS),
    }
    return conditions, metadata


def _input_device(model: Any) -> Any:
    try:
        return model.get_input_embeddings().weight.device
    except Exception:
        return next(model.parameters()).device


def _absolute_position(attention_mask: Any, position: int) -> Any:
    import torch

    if position >= 0:
        raise ValueError("selected_position must be a negative prompt-end-relative offset.")
    token_indices = torch.arange(attention_mask.shape[1], device=attention_mask.device, dtype=torch.long)
    masked_indices = attention_mask.to(dtype=torch.long) * token_indices[None, :]
    last_indices = masked_indices.max(dim=1).values
    absolute = last_indices + (position + 1)
    if torch.any(absolute < 0):
        raise ValueError("A prompt is shorter than the selected negative token position.")
    selected_mask = attention_mask.gather(1, absolute[:, None]).squeeze(1)
    if torch.any(selected_mask == 0):
        raise ValueError("Selected prompt-end-relative position resolves to padding.")
    return absolute


def measure_refusal_components(
    *,
    model_base: Any,
    loaded_direction: LoadedDirection,
    prompt_conditions: list[PromptCondition],
    enable_thinking: bool,
    batch_size: int,
) -> list[dict[str, Any]]:
    import torch

    metadata = loaded_direction.metadata
    selected_layer = int(metadata["selected_layer"])
    selected_position = int(metadata["selected_position"])
    direction = loaded_direction.direction.detach().to(dtype=torch.float32, device="cpu")
    direction = direction / (direction.norm() + 1e-8)
    direction_selection_status = metadata.get("selection_status")
    debug_only_run = bool(
        loaded_direction.metadata.get("selection_status") != "intervention_selected"
    )

    rows: list[dict[str, Any]] = []
    input_device = _input_device(model_base.model)
    for start in range(0, len(prompt_conditions), batch_size):
        batch = prompt_conditions[start : start + batch_size]
        tokenized = model_base.tokenize_prompts(
            [item.prompt for item in batch],
            enable_thinking=enable_thinking,
        )
        attention_mask = tokenized.attention_mask.to(input_device)
        absolute_positions = _absolute_position(attention_mask, selected_position)
        batch_cache: dict[int, torch.Tensor] = {}

        def hook(module: Any, inputs: tuple[Any, ...]) -> None:
            activation = inputs[0].detach()
            positions_on_device = absolute_positions.to(activation.device)
            selected = []
            for batch_index in range(activation.shape[0]):
                selected.append(activation[batch_index, positions_on_device[batch_index], :].to("cpu", torch.float32))
            batch_cache["activation"] = torch.stack(selected, dim=0)

        handle = model_base.layers[selected_layer].register_forward_pre_hook(hook)
        try:
            with torch.no_grad():
                model_base.model(
                    input_ids=tokenized.input_ids.to(input_device),
                    attention_mask=attention_mask,
                )
        finally:
            handle.remove()

        activation = batch_cache["activation"]
        components = activation @ direction
        prompt_lengths = tokenized.attention_mask.sum(dim=1).tolist()
        for item, component, prompt_length in zip(batch, components.tolist(), prompt_lengths):
            rows.append(
                {
                    "artifact_version": STAGE4B_ARTIFACT_VERSION,
                    "goal_index": item.goal_index,
                    "condition": item.condition,
                    "model_name": model_base.model_name,
                    "selected_position": selected_position,
                    "selected_layer": selected_layer,
                    "refusal_component": float(component),
                    "direction_selection_status": direction_selection_status,
                    "allow_provisional_direction": None,
                    "debug_only_run": debug_only_run,
                    "prompt_length_tokens": int(prompt_length),
                    "enable_thinking": enable_thinking,
                    "stage2_jsonl": item.stage2_jsonl,
                    "stage2_row_identity": item.stage2_row_identity,
                    "prompt_source_field": item.prompt_source_field,
                    "attack_prompt_token_length": item.attack_prompt_token_length,
                    "hijacked_medium_equals_long": item.hijacked_medium_equals_long,
                    "medium_long_comparison_status": item.medium_long_comparison_status,
                }
            )
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return rows


def _safe_stat(values: list[float], fn: Callable[[list[float]], float]) -> float | None:
    if not values:
        return None
    return float(fn(values))


def summarize_refusal_dampening(
    *,
    rows: list[dict[str, Any]],
    direction_metadata: dict[str, Any],
    prompt_metadata: dict[str, Any],
    config: DampeningConfig,
) -> dict[str, Any]:
    direction_selection_status = direction_metadata.get("selection_status")
    debug_only_run = bool(
        config.allow_provisional_direction or direction_selection_status != "intervention_selected"
    )
    debug_warning = None
    if debug_only_run:
        debug_warning = (
            "DEBUG ONLY: this run used --allow-provisional-direction or a non-final direction. "
            "It validates the Stage 4B code path only and must not be presented as final evidence."
        )

    by_condition: dict[str, list[float]] = {condition: [] for condition in CONDITIONS}
    by_goal: dict[int, dict[str, float]] = defaultdict(dict)
    for row in rows:
        condition = str(row["condition"])
        value = float(row["refusal_component"])
        by_condition.setdefault(condition, []).append(value)
        by_goal[int(row["goal_index"])][condition] = value

    delta_medium: list[float] = []
    delta_long: list[float] = []
    for condition_values in by_goal.values():
        direct = condition_values.get("direct_harmful")
        medium = condition_values.get("hijacked_medium")
        long = condition_values.get("hijacked_long")
        if direct is not None and medium is not None:
            delta_medium.append(float(medium - direct))
        if direct is not None and long is not None:
            delta_long.append(float(long - direct))

    condition_summary = {
        condition: {
            "mean": _safe_stat(values, mean),
            "median": _safe_stat(values, median),
            "count": len(values),
        }
        for condition, values in by_condition.items()
    }

    return {
        "artifact_version": STAGE4B_ARTIFACT_VERSION,
        "stage": "stage4b_refusal_component_dampening_measurement",
        "timestamp_utc": utc_now(),
        "model_name": config.model_name,
        "enable_thinking": config.enable_thinking,
        "dry_run": config.dry_run,
        "allow_provisional_direction": config.allow_provisional_direction,
        "debug_only_run": debug_only_run,
        "scientific_status": "debug_only_not_final_evidence" if debug_only_run else "scientific_direction_required",
        "debug_warning": debug_warning,
        "number_of_goals": prompt_metadata["num_goals"],
        "mean_refusal_component_by_condition": {
            condition: values["mean"] for condition, values in condition_summary.items()
        },
        "median_refusal_component_by_condition": {
            condition: values["median"] for condition, values in condition_summary.items()
        },
        "condition_summary": condition_summary,
        "mean_delta_medium": _safe_stat(delta_medium, mean),
        "mean_delta_long": _safe_stat(delta_long, mean),
        "fraction_negative_delta_medium": (
            sum(1 for value in delta_medium if value < 0) / len(delta_medium) if delta_medium else None
        ),
        "fraction_negative_delta_long": (
            sum(1 for value in delta_long if value < 0) / len(delta_long) if delta_long else None
        ),
        "num_goals_hijacked_medium_equals_long": prompt_metadata[
            "num_goals_hijacked_medium_equals_long"
        ],
        "negative_delta_interpretation": "negative delta means refusal-direction dampening",
        "prompt_metadata": prompt_metadata,
        "direction_metadata": direction_metadata,
        "outputs": {
            "per_example_refusal_components_jsonl": str(config.output_dir / "per_example_refusal_components.jsonl"),
            "refusal_dampening_summary_json": str(config.output_dir / "refusal_dampening_summary.json"),
        },
    }


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(make_json_safe(row), ensure_ascii=False) + "\n")


def run_refusal_dampening_measurement(
    *,
    config: DampeningConfig,
    model_base: Any,
    loaded_direction: LoadedDirection,
) -> dict[str, Any]:
    token_length_fn = make_token_length_fn(model_base.tokenizer)
    prompt_conditions, prompt_metadata = build_prompt_conditions(
        stage2_jsonl=config.stage2_jsonl,
        num_goals=config.num_goals,
        token_length_fn=token_length_fn,
    )
    rows = measure_refusal_components(
        model_base=model_base,
        loaded_direction=loaded_direction,
        prompt_conditions=prompt_conditions,
        enable_thinking=config.enable_thinking,
        batch_size=config.batch_size,
    )
    debug_only_run = bool(
        config.allow_provisional_direction
        or loaded_direction.metadata.get("selection_status") != "intervention_selected"
    )
    for row in rows:
        row["allow_provisional_direction"] = config.allow_provisional_direction
        row["debug_only_run"] = debug_only_run

    summary = summarize_refusal_dampening(
        rows=rows,
        direction_metadata=loaded_direction.metadata,
        prompt_metadata=prompt_metadata,
        config=config,
    )
    config.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(config.output_dir / "per_example_refusal_components.jsonl", rows)
    write_json(config.output_dir / "refusal_dampening_summary.json", summary)
    return summary
