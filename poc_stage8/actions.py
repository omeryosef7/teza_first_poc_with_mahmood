from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Mapping


ACTION_TYPES = (
    "choose_template_variant",
    "choose_reasoning_block_length_bucket",
    "choose_neutral_delimiter",
    "choose_safe_placeholder_order",
    "choose_include_harmless_puzzle_block",
    "choose_suffix_length_bucket",
)

SAFE_PLACEHOLDER_TOKENS = (
    "[BENIGN_TASK_PLACEHOLDER]",
    "[SAFE_REASONING_BLOCK]",
    "[NEUTRAL_DELIMITER]",
    "[HARMLESS_PUZZLE_BLOCK]",
)

ACTION_CATALOG: dict[str, tuple[str, ...]] = {
    "choose_template_variant": ("template_alpha", "template_beta", "template_gamma"),
    "choose_reasoning_block_length_bucket": ("omit", "short", "medium", "long"),
    "choose_neutral_delimiter": ("[NEUTRAL_DELIMITER]", "[NEUTRAL_DELIMITER]::", "[NEUTRAL_DELIMITER]|"),
    "choose_safe_placeholder_order": (
        "task_reasoning_suffix",
        "task_suffix_reasoning",
        "reasoning_task_suffix",
    ),
    "choose_include_harmless_puzzle_block": ("excluded", "included"),
    "choose_suffix_length_bucket": ("tiny", "small", "medium", "large"),
}


@dataclass(frozen=True)
class SandboxAction:
    action_type: str
    action_value: str

    def as_dict(self) -> dict[str, str]:
        return {"action_type": self.action_type, "action_value": self.action_value}


def validate_action(action: SandboxAction | Mapping[str, Any]) -> SandboxAction:
    if isinstance(action, SandboxAction):
        candidate = action
    else:
        action_type = action.get("action_type")
        action_value = action.get("action_value")
        if action_type is None or action_value is None:
            raise ValueError("Action must include action_type and action_value.")
        candidate = SandboxAction(action_type=str(action_type), action_value=str(action_value))

    if candidate.action_type not in ACTION_CATALOG:
        raise ValueError(f"Unsupported action_type: {candidate.action_type}")
    if candidate.action_value not in ACTION_CATALOG[candidate.action_type]:
        raise ValueError(
            f"Unsupported action_value for {candidate.action_type}: {candidate.action_value}. "
            f"Allowed values: {ACTION_CATALOG[candidate.action_type]}"
        )
    return candidate


def build_action_space() -> tuple[SandboxAction, ...]:
    actions: list[SandboxAction] = []
    for action_type in ACTION_TYPES:
        for action_value in ACTION_CATALOG[action_type]:
            actions.append(SandboxAction(action_type=action_type, action_value=action_value))
    return tuple(actions)


def sample_action(rng: random.Random) -> SandboxAction:
    return rng.choice(build_action_space())


def safe_placeholder_tokens() -> tuple[str, ...]:
    return SAFE_PLACEHOLDER_TOKENS