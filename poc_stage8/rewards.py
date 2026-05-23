from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from poc_stage5.data_loading import iter_jsonl, validate_jsonl_path
from poc_stage7.objectives import ObjectiveParameters, build_behavioral_score_fields, compute_objectives


REWARD_MODES = (
    "strongreject_only",
    "judge_only",
    "refusal_suppression",
    "refusal_preservation",
    "hybrid",
)

DEFAULT_REWARD_MODE = "strongreject_only"
EXPERIMENTAL_REWARD_MODES = ("refusal_suppression", "refusal_preservation", "hybrid")


@dataclass(frozen=True)
class RewardObservation:
    judge_score_raw: float | None
    judge_score_normalized: float | None
    strongreject_score_raw: float | None
    strongreject_score_normalized: float | None
    behavioral_score_raw: float | None
    behavioral_score_normalized: float | None
    projection_value: float | None
    baseline_projection: float | None
    used_stage7_row: bool
    source: str


@dataclass(frozen=True)
class RewardComputation:
    reward_mode: str
    reward: float
    observation: RewardObservation
    objective_values: dict[str, float | None]


def _coerce_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _clamp_unit(value: float) -> float:
    return min(1.0, max(0.0, value))


def _hash_to_unit_float(seed_text: str, *, offset: int = 0) -> float:
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    start = offset % (len(digest) - 8)
    chunk = digest[start : start + 8]
    return int.from_bytes(chunk, byteorder="big", signed=False) / float(2**64 - 1)


def build_reward_observation_from_row(row: dict[str, Any]) -> RewardObservation | None:
    score_fields = build_behavioral_score_fields(row)
    projection_value = _coerce_float(row.get("projection_value"))
    baseline_projection = _coerce_float(row.get("baseline_projection"))
    if projection_value is None or baseline_projection is None:
        return None
    return RewardObservation(
        judge_score_raw=score_fields["judge_score_raw"],
        judge_score_normalized=score_fields["judge_score_normalized"],
        strongreject_score_raw=score_fields["strongreject_score_raw"],
        strongreject_score_normalized=score_fields["strongreject_score_normalized"],
        behavioral_score_raw=score_fields["behavioral_score_raw"],
        behavioral_score_normalized=score_fields["behavioral_score_normalized"],
        projection_value=projection_value,
        baseline_projection=baseline_projection,
        used_stage7_row=True,
        source="stage7",
    )


def load_stage7_reward_observations(path: str | Path | None) -> list[RewardObservation]:
    if path is None:
        return []
    input_path = validate_jsonl_path(path)
    observations: list[RewardObservation] = []
    for row in iter_jsonl(input_path):
        observation = build_reward_observation_from_row(row)
        if observation is not None:
            observations.append(observation)
    return observations


def build_mock_reward_observation(
    *,
    seed: int,
    episode: int,
    step: int,
    action_type: str,
    action_value: str,
) -> RewardObservation:
    seed_text = f"{seed}:{episode}:{step}:{action_type}:{action_value}"
    judge_raw = 1.0 + 9.0 * _hash_to_unit_float(seed_text, offset=0)
    strongreject_raw = _hash_to_unit_float(seed_text, offset=8)
    projection_value = _hash_to_unit_float(seed_text, offset=16)
    baseline_projection = _clamp_unit(0.6 * projection_value + 0.4 * _hash_to_unit_float(seed_text, offset=24))
    judge_normalized = min(1.0, max(0.0, (judge_raw - 1.0) / 9.0))
    strongreject_normalized = strongreject_raw
    return RewardObservation(
        judge_score_raw=judge_raw,
        judge_score_normalized=judge_normalized,
        strongreject_score_raw=strongreject_raw,
        strongreject_score_normalized=strongreject_normalized,
        behavioral_score_raw=judge_raw,
        behavioral_score_normalized=judge_normalized,
        projection_value=projection_value,
        baseline_projection=baseline_projection,
        used_stage7_row=False,
        source="mock",
    )


def select_reward_observation(
    observations: list[RewardObservation],
    *,
    seed: int,
    episode: int,
    step: int,
    action_type: str,
    action_value: str,
) -> RewardObservation:
    if observations and (episode * 997 + step) % 2 == 0:
        index = (episode * 997 + step) % len(observations)
        return observations[index]
    return build_mock_reward_observation(
        seed=seed,
        episode=episode,
        step=step,
        action_type=action_type,
        action_value=action_value,
    )


def compute_reward(
    observation: RewardObservation,
    *,
    reward_mode: str,
    parameters: ObjectiveParameters | None = None,
) -> RewardComputation:
    if reward_mode not in REWARD_MODES:
        raise ValueError(f"Unsupported reward_mode: {reward_mode}")
    params = parameters or ObjectiveParameters()
    objective_values = compute_objectives(
        behavioral_score=observation.behavioral_score_normalized,
        strongreject_score=observation.strongreject_score_normalized,
        projection_value=observation.projection_value,
        baseline_projection=observation.baseline_projection,
        params=params,
    )
    reward = objective_values.get(f"objective_{reward_mode}")
    if reward is None:
        raise ValueError(f"Reward could not be computed for mode {reward_mode}.")
    return RewardComputation(
        reward_mode=reward_mode,
        reward=reward,
        observation=observation,
        objective_values=objective_values,
    )


def stage7_row_count(observations: Iterable[RewardObservation]) -> int:
    return sum(1 for observation in observations if observation.used_stage7_row)