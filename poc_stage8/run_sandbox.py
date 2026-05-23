from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from poc_stage8.actions import build_action_space, sample_action
from poc_stage8.environment import SandboxEnvironment
from poc_stage8.rewards import (
    DEFAULT_REWARD_MODE,
    REWARD_MODES,
    ObjectiveParameters,
    compute_reward,
    load_stage7_reward_observations,
    select_reward_observation,
)
from poc_stage8.summarize_sandbox import summarize_rows


FORBIDDEN_RAW_FIELDS = (
    "prompt",
    "prompt_text",
    "response",
    "response_text",
    "tokens",
    "token_strings",
    "logits",
    "hidden_state",
    "hidden_states",
)


@dataclass(frozen=True)
class SandboxRunConfig:
    output_jsonl: Path
    summary_json: Path
    num_episodes: int
    max_steps: int
    reward_mode: str
    stage7_jsonl: Path | None
    seed: int
    overwrite: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the offline Stage 8 sandbox over a finite safe action space.")
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--num-episodes", type=int, required=True)
    parser.add_argument("--max-steps", type=int, required=True)
    parser.add_argument("--reward-mode", choices=REWARD_MODES, default=DEFAULT_REWARD_MODE)
    parser.add_argument("--stage7-jsonl")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def validate_config(args: argparse.Namespace) -> SandboxRunConfig:
    if args.num_episodes <= 0:
        raise ValueError("--num-episodes must be positive.")
    if args.max_steps <= 0:
        raise ValueError("--max-steps must be positive.")
    stage7_jsonl = Path(args.stage7_jsonl) if args.stage7_jsonl else None
    if stage7_jsonl is not None and not stage7_jsonl.exists():
        raise FileNotFoundError(f"Stage 7 JSONL does not exist: {stage7_jsonl}")
    return SandboxRunConfig(
        output_jsonl=Path(args.output_jsonl),
        summary_json=Path(args.summary_json),
        num_episodes=int(args.num_episodes),
        max_steps=int(args.max_steps),
        reward_mode=str(args.reward_mode),
        stage7_jsonl=stage7_jsonl,
        seed=int(args.seed),
        overwrite=bool(args.overwrite),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            return str(value)
    return value


def _tmp_path(path: Path) -> Path:
    return path.with_name(path.name + ".tmp")


def _check_outputs(config: SandboxRunConfig) -> None:
    paths = [config.output_jsonl, config.summary_json]
    existing = [path for path in paths if path.exists()]
    if existing and not config.overwrite:
        formatted = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(f"Output file(s) already exist. Use --overwrite to replace them:\n{formatted}")


def _write_jsonl_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(path)
    with tmp_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(_json_safe(row), ensure_ascii=False) + "\n")
    tmp_path.replace(path)


def _validate_no_forbidden_fields(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        for forbidden in FORBIDDEN_RAW_FIELDS:
            if forbidden in row:
                raise ValueError(f"Forbidden field found in sandbox output: {forbidden}")


def run_sandbox(config: SandboxRunConfig) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _check_outputs(config)
    rng = random.Random(config.seed)
    action_space = build_action_space()
    environment = SandboxEnvironment(seed=config.seed)
    stage7_observations = load_stage7_reward_observations(config.stage7_jsonl)

    rows: list[dict[str, Any]] = []
    for episode in range(config.num_episodes):
        environment.reset(episode_index=episode)
        for step in range(config.max_steps):
            action = sample_action(rng)
            step_result = environment.step(action)
            observation = select_reward_observation(
                stage7_observations,
                seed=config.seed,
                episode=episode,
                step=step,
                action_type=action.action_type,
                action_value=action.action_value,
            )
            reward = compute_reward(observation, reward_mode=config.reward_mode, parameters=ObjectiveParameters())
            rows.append(
                {
                    "stage": 8,
                    "episode": episode,
                    "step": step,
                    "action_type": action.action_type,
                    "action_value": action.action_value,
                    "reward_mode": config.reward_mode,
                    "reward": reward.reward,
                    "state_summary": step_result.state_summary,
                    "used_stage7_row": observation.used_stage7_row,
                }
            )

    _validate_no_forbidden_fields(rows)
    _write_jsonl_rows(config.output_jsonl, rows)

    summary_groups = summarize_rows(rows)
    summary = {
        "stage": 8,
        "summary_type": "sandbox_run",
        "output_jsonl": str(config.output_jsonl),
        "summary_json": str(config.summary_json),
        "num_episodes": config.num_episodes,
        "max_steps": config.max_steps,
        "reward_mode": config.reward_mode,
        "stage7_jsonl": str(config.stage7_jsonl) if config.stage7_jsonl is not None else None,
        "num_rows": len(rows),
        "rows_with_stage7_observation": sum(1 for row in rows if row["used_stage7_row"]),
        "action_space_size": len(action_space),
        "summary_groups": summary_groups,
        "config": _json_safe(asdict(config)),
        "generated_utc": _utc_now(),
    }
    config.summary_json.parent.mkdir(parents=True, exist_ok=True)
    with config.summary_json.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(summary), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return rows, summary


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = validate_config(args)
        _rows, summary = run_sandbox(config)
        print(json.dumps(_json_safe(summary), indent=2, ensure_ascii=False))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())