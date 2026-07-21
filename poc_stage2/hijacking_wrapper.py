from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from dotenv import load_dotenv

from poc_stage2.schemas import ARTIFACT_VERSION, HijackingResultRow, row_from_workflow_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HIJACKING_ROOT = PROJECT_ROOT / "Chain_of_Thought_Hijacking" / "Hijacking"

load_dotenv(PROJECT_ROOT / ".env")


DEFAULT_ATTACK_MODEL = "gemini-2.5-flash"
DEFAULT_JUDGE_MODEL = "gemini-judge"
DEFAULT_DATASET = "walledai/HarmBench"
DEFAULT_DATASET_SPLIT = "standard"
MODEL_TO_ENV_VAR = {
    "gemini-2.5-pro": "GEMINI_API_KEY",
    "gemini-2.5-flash": "GEMINI_API_KEY",
    "gpt-o4-mini": "OPENAI_API_KEY",
    "gpt-5-mini": "OPENAI_API_KEY",
    "grok-3-mini": "GROK_API_KEY",
    "claude-4-sonnet": "ANTHROPIC_API_KEY",
}
MODEL_PROVIDER_MAPPING = {
    "gpt-o4-mini": "o4-mini",
    "gpt-5-mini": "gpt-5-mini",
    "claude-4-sonnet": "anthropic/claude-sonnet-4-20250514",
    "grok-3-mini": "xai/grok-3-mini",
    "gemini-2.5-pro": "gemini/gemini-2.5-pro",
}


@dataclass(frozen=True)
class StructuredRunResult:
    rows: list[HijackingResultRow]
    summary: dict[str, Any]
    output_stem: str
    verified_model_mapping: dict[str, str]


def verify_target_model_mapping(target_model: str) -> dict[str, str]:
    base_model = normalize_target_model_name(target_model)
    return {
        "cli_model_name": target_model,
        "provider_model_name": MODEL_PROVIDER_MAPPING.get(base_model, base_model),
    }


def make_output_stem(target_model: str, start_example: int, end_example: int) -> str:
    slice_size = end_example - start_example
    slice_label = "small" if 3 <= slice_size <= 5 else f"{start_example}_{end_example}"
    return f"hijacking_baseline_{target_model}_{slice_label}"


def normalize_target_model_name(target_model: str) -> str:
    if target_model.startswith("gpt-5-mini-"):
        return "gpt-5-mini"
    return target_model


def require_api_keys(target_model: str) -> None:
    normalized_target_model = normalize_target_model_name(target_model)
    if normalized_target_model not in MODEL_TO_ENV_VAR:
        raise ValueError("Unsupported target model: {0}".format(target_model))
    required_env_vars = {
        MODEL_TO_ENV_VAR[DEFAULT_ATTACK_MODEL],
        MODEL_TO_ENV_VAR[normalized_target_model],
    }

    missing = sorted(env_var for env_var in required_env_vars if not os.getenv(env_var))
    if missing:
        raise RuntimeError(
            "Missing required API credentials for this run. Set: "
            + ", ".join(missing)
        )


def ensure_hijacking_import_path() -> None:
    if str(HIJACKING_ROOT) not in sys.path:
        sys.path.insert(0, str(HIJACKING_ROOT))


def build_args(
    *,
    target_model: str,
    start_example: int,
    end_example: int,
    n_iterations: int,
    n_streams: int,
    dataset: str,
    dataset_split: str,
    verbosity: int = 1,
) -> SimpleNamespace:
    return SimpleNamespace(
        target_model=target_model,
        attack_max_n_tokens=65535,
        max_n_attack_attempts=3,
        judge_max_n_tokens=65535,
        judge_temperature=0,
        n_streams=n_streams,
        keep_last_n=3,
        n_iterations=n_iterations,
        goal=None,
        dataset=dataset,
        dataset_split=dataset_split,
        start_examples=start_example,
        end_examples=end_example,
        verbosity=verbosity,
        logfile=None,
        attack_model=DEFAULT_ATTACK_MODEL,
        judge_model=DEFAULT_JUDGE_MODEL,
    )


def compute_summary(
    *,
    rows: list[HijackingResultRow],
    goal_successes: list[bool],
    target_model: str,
    dataset: str,
    dataset_split: str,
    dataset_slice: str,
    start_example: int,
    end_example: int,
    n_iterations: int,
    n_streams: int,
    timestamp_utc: str,
) -> dict[str, Any]:
    num_goals = len(goal_successes)
    num_successes = sum(1 for value in goal_successes if value)
    attack_success_rate = (num_successes / num_goals) if num_goals else 0.0

    return {
        "artifact_version": ARTIFACT_VERSION,
        "timestamp_utc": timestamp_utc,
        "num_goals": num_goals,
        "num_successes": num_successes,
        "attack_success_rate": attack_success_rate,
        "target_model": target_model,
        "dataset": dataset,
        "dataset_split": dataset_split,
        "dataset_slice": dataset_slice,
        "start_example": start_example,
        "end_example": end_example,
        "n_iterations": n_iterations,
        "n_streams": n_streams,
        "attack_model": DEFAULT_ATTACK_MODEL,
        "judge_model": DEFAULT_JUDGE_MODEL,
        "provider_model_name": verify_target_model_mapping(target_model)["provider_model_name"],
        "num_rows": len(rows),
    }


def run_hijacking_slice(
    *,
    target_model: str = "gpt-o4-mini",
    start_example: int = 1,
    end_example: int = 4,
    n_iterations: int = 2,
    n_streams: int = 6,
    dataset: str = DEFAULT_DATASET,
    dataset_split: str = DEFAULT_DATASET_SPLIT,
    verbosity: int = 1,
    wandb_mode: str = "disabled",
    goals: list[str] | None = None,
) -> StructuredRunResult:
    # `goals` (optional): run an explicit list of goal strings instead of a HF dataset
    # slice, reusing the identical attacker/target/judge machinery. Used by the Phase-4
    # driver to run our AdvBench dev-25 goals. When set, start/end are index bookkeeping only.
    if goals is not None:
        if not goals:
            raise ValueError("goals list is empty")
        # HF convention: N goals span train[start_index : start_index+N],
        # i.e. end_example = (start_example-1) + N. Keeps the slice label accurate.
        end_example = (start_example - 1) + len(goals)
    if end_example <= start_example:
        raise ValueError("--end-example must be greater than --start-example.")

    verify_target_model_mapping(target_model)
    require_api_keys(target_model)
    ensure_hijacking_import_path()

    from core import load_attack_and_target_models, load_judge, run_for_goal  # type: ignore
    from data.dataset import load_goals  # type: ignore
    from utils.logger import configure_logging  # type: ignore

    configure_logging(verbosity=verbosity, logfile=None)
    args = build_args(
        target_model=target_model,
        start_example=start_example,
        end_example=end_example,
        n_iterations=n_iterations,
        n_streams=n_streams,
        dataset=dataset,
        dataset_split=dataset_split,
        verbosity=verbosity,
    )

    attack_lm, target_lm = load_attack_and_target_models(args)
    judge_lm = load_judge(args)
    if goals is not None:
        goals_to_test, start_index = list(goals), start_example - 1
    else:
        goals_to_test, start_index = load_goals(args)

    timestamp_utc = datetime.now(timezone.utc).isoformat()
    dataset_slice = f"train[{start_example - 1}:{end_example}]"
    rows: list[HijackingResultRow] = []
    goal_successes: list[bool] = []

    for offset, goal in enumerate(goals_to_test):
        absolute_index = start_index + offset
        goal_result = run_for_goal(
            args,
            attack_lm,
            target_lm,
            judge_lm,
            goal,
            absolute_index,
            return_details=True,
            wandb_mode=wandb_mode,
        )
        goal_successes.append(bool(goal_result["is_success"]))
        for record in goal_result["rows"]:
            rows.append(
                row_from_workflow_record(
                    record,
                    timestamp_utc=timestamp_utc,
                    dataset=dataset,
                    dataset_split=dataset_split,
                    dataset_slice=dataset_slice,
                )
            )

    summary = compute_summary(
        rows=rows,
        goal_successes=goal_successes,
        target_model=target_model,
        dataset=dataset,
        dataset_split=dataset_split,
        dataset_slice=dataset_slice,
        start_example=start_example,
        end_example=end_example,
        n_iterations=n_iterations,
        n_streams=n_streams,
        timestamp_utc=timestamp_utc,
    )

    return StructuredRunResult(
        rows=rows,
        summary=summary,
        output_stem=make_output_stem(target_model, start_example, end_example),
        verified_model_mapping=verify_target_model_mapping(target_model),
    )


def summary_as_jsonable(result: StructuredRunResult) -> dict[str, Any]:
    payload = dict(result.summary)
    payload["verified_model_mapping"] = dict(result.verified_model_mapping)
    return payload


def rows_as_jsonable(result: StructuredRunResult) -> list[dict[str, Any]]:
    return [asdict(row) for row in result.rows]
