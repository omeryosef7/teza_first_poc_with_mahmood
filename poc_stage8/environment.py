from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from poc_stage8.actions import ACTION_CATALOG, SAFE_PLACEHOLDER_TOKENS, SandboxAction, validate_action


@dataclass(frozen=True)
class SandboxState:
    episode: int
    step: int
    template_variant: str
    reasoning_block_length_bucket: str
    neutral_delimiter: str
    safe_placeholder_order: str
    include_harmless_puzzle_block: bool
    suffix_length_bucket: str
    applied_action_count: int

    def summary(self) -> dict[str, Any]:
        return {
            "episode": self.episode,
            "step": self.step,
            "template_variant": self.template_variant,
            "reasoning_block_length_bucket": self.reasoning_block_length_bucket,
            "neutral_delimiter": self.neutral_delimiter,
            "safe_placeholder_order": self.safe_placeholder_order,
            "include_harmless_puzzle_block": self.include_harmless_puzzle_block,
            "suffix_length_bucket": self.suffix_length_bucket,
            "applied_action_count": self.applied_action_count,
            "safe_placeholders": list(SAFE_PLACEHOLDER_TOKENS),
            "structural_action_types": list(ACTION_CATALOG),
        }


@dataclass(frozen=True)
class SandboxStepResult:
    state: SandboxState
    applied_action: SandboxAction
    done: bool

    @property
    def state_summary(self) -> dict[str, Any]:
        return self.state.summary()


class SandboxEnvironment:
    def __init__(self, *, seed: int = 0) -> None:
        self._seed = seed
        self._episode_index = -1
        self._step_index = 0
        self._applied_action_count = 0
        self._state = self._make_state(
            episode=0,
            step=0,
            template_variant="template_alpha",
            reasoning_block_length_bucket="omit",
            neutral_delimiter="[NEUTRAL_DELIMITER]",
            safe_placeholder_order="task_reasoning_suffix",
            include_harmless_puzzle_block=False,
            suffix_length_bucket="tiny",
        )

    def _make_state(
        self,
        *,
        episode: int,
        step: int,
        template_variant: str,
        reasoning_block_length_bucket: str,
        neutral_delimiter: str,
        safe_placeholder_order: str,
        include_harmless_puzzle_block: bool,
        suffix_length_bucket: str,
    ) -> SandboxState:
        return SandboxState(
            episode=episode,
            step=step,
            template_variant=template_variant,
            reasoning_block_length_bucket=reasoning_block_length_bucket,
            neutral_delimiter=neutral_delimiter,
            safe_placeholder_order=safe_placeholder_order,
            include_harmless_puzzle_block=include_harmless_puzzle_block,
            suffix_length_bucket=suffix_length_bucket,
            applied_action_count=self._applied_action_count,
        )

    def reset(self, *, episode_index: int) -> dict[str, Any]:
        self._episode_index = episode_index
        self._step_index = 0
        self._applied_action_count = 0
        self._state = self._make_state(
            episode=episode_index,
            step=0,
            template_variant="template_alpha",
            reasoning_block_length_bucket="omit",
            neutral_delimiter="[NEUTRAL_DELIMITER]",
            safe_placeholder_order="task_reasoning_suffix",
            include_harmless_puzzle_block=False,
            suffix_length_bucket="tiny",
        )
        return self._state.summary()

    def step(self, action: SandboxAction | Mapping[str, Any]) -> SandboxStepResult:
        validated = validate_action(action)
        if validated.action_type == "choose_template_variant":
            template_variant = validated.action_value
            reasoning_block_length_bucket = self._state.reasoning_block_length_bucket
            neutral_delimiter = self._state.neutral_delimiter
            safe_placeholder_order = self._state.safe_placeholder_order
            include_harmless_puzzle_block = self._state.include_harmless_puzzle_block
            suffix_length_bucket = self._state.suffix_length_bucket
        elif validated.action_type == "choose_reasoning_block_length_bucket":
            template_variant = self._state.template_variant
            reasoning_block_length_bucket = validated.action_value
            neutral_delimiter = self._state.neutral_delimiter
            safe_placeholder_order = self._state.safe_placeholder_order
            include_harmless_puzzle_block = self._state.include_harmless_puzzle_block
            suffix_length_bucket = self._state.suffix_length_bucket
        elif validated.action_type == "choose_neutral_delimiter":
            template_variant = self._state.template_variant
            reasoning_block_length_bucket = self._state.reasoning_block_length_bucket
            neutral_delimiter = validated.action_value
            safe_placeholder_order = self._state.safe_placeholder_order
            include_harmless_puzzle_block = self._state.include_harmless_puzzle_block
            suffix_length_bucket = self._state.suffix_length_bucket
        elif validated.action_type == "choose_safe_placeholder_order":
            template_variant = self._state.template_variant
            reasoning_block_length_bucket = self._state.reasoning_block_length_bucket
            neutral_delimiter = self._state.neutral_delimiter
            safe_placeholder_order = validated.action_value
            include_harmless_puzzle_block = self._state.include_harmless_puzzle_block
            suffix_length_bucket = self._state.suffix_length_bucket
        elif validated.action_type == "choose_include_harmless_puzzle_block":
            template_variant = self._state.template_variant
            reasoning_block_length_bucket = self._state.reasoning_block_length_bucket
            neutral_delimiter = self._state.neutral_delimiter
            safe_placeholder_order = self._state.safe_placeholder_order
            include_harmless_puzzle_block = validated.action_value == "included"
            suffix_length_bucket = self._state.suffix_length_bucket
        else:
            template_variant = self._state.template_variant
            reasoning_block_length_bucket = self._state.reasoning_block_length_bucket
            neutral_delimiter = self._state.neutral_delimiter
            safe_placeholder_order = self._state.safe_placeholder_order
            include_harmless_puzzle_block = self._state.include_harmless_puzzle_block
            suffix_length_bucket = validated.action_value

        self._step_index += 1
        self._applied_action_count += 1
        self._state = self._make_state(
            episode=self._episode_index,
            step=self._step_index,
            template_variant=template_variant,
            reasoning_block_length_bucket=reasoning_block_length_bucket,
            neutral_delimiter=neutral_delimiter,
            safe_placeholder_order=safe_placeholder_order,
            include_harmless_puzzle_block=include_harmless_puzzle_block,
            suffix_length_bucket=suffix_length_bucket,
        )
        return SandboxStepResult(state=self._state, applied_action=validated, done=False)