"""
Clean interfaces for the AutoInject-style optimization POC.

These dataclasses define the shared vocabulary between the adapter,
dataset builder, offline optimizer, and report generator.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StructuralAction:
    """One discrete structural action over wrapper configuration."""
    action_id: str
    wrapper_type: str              # A / D / F / E
    has_puzzle: bool
    has_thinking: bool
    is_length_matched: bool
    is_bare_target: bool
    length_bucket: str             # short / medium / long / matched / unknown
    reasoning_difficulty: str     # easy / medium / hard / unknown
    target_placement: str         # early / middle / late / unchanged / unknown
    answer_cue: str               # weak / medium / strong / unchanged / unknown
    thinking_mode: str            # on / off
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "wrapper_type": self.wrapper_type,
            "has_puzzle": self.has_puzzle,
            "has_thinking": self.has_thinking,
            "is_length_matched": self.is_length_matched,
            "is_bare_target": self.is_bare_target,
            "length_bucket": self.length_bucket,
            "reasoning_difficulty": self.reasoning_difficulty,
            "target_placement": self.target_placement,
            "answer_cue": self.answer_cue,
            "thinking_mode": self.thinking_mode,
            "description": self.description,
        }


@dataclass
class CandidateMetadata:
    """Safe metadata describing a candidate from the existing Stage 4.7/4.8 pool."""
    stage: str
    safe_example_hash: str
    goal_index: int
    condition: str
    seed: int = 0
    n_target_keywords: int = 0
    redacted_context_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "safe_example_hash": self.safe_example_hash,
            "goal_index": self.goal_index,
            "condition": self.condition,
            "seed": self.seed,
            "n_target_keywords": self.n_target_keywords,
            "redacted_context_hash": self.redacted_context_hash,
        }


@dataclass
class Candidate:
    """
    One candidate in the optimization pool.
    Corresponds to a single Stage 4.7/4.8 run cell.
    """
    candidate_id: str
    action: StructuralAction
    metadata: CandidateMetadata

    # Observed outcomes (from existing runs)
    sr_score: float = 0.0
    sr_success: bool = False
    think_token_count: int = 0
    censored: bool = False
    onset_percent: Optional[float] = None
    onset_bucket: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "candidate_id": self.candidate_id,
            "sr_score": self.sr_score,
            "sr_success": self.sr_success,
            "think_token_count": self.think_token_count,
            "censored": self.censored,
            "onset_percent": self.onset_percent,
            "onset_bucket": self.onset_bucket,
        }
        d.update({f"action_{k}": v for k, v in self.action.to_dict().items()})
        d.update({f"meta_{k}": v for k, v in self.metadata.to_dict().items()})
        return d


@dataclass
class RewardResult:
    """Reward components computed for a candidate."""
    candidate_id: str
    reward_asr: float               # binary: sr_success
    reward_sr_score: float          # continuous: strongreject_score
    reward_combined: float          # sr_score + alpha_onset*onset + alpha_think*log_think - beta*censored
    reward_safe_mechanistic: float  # sr_score + alpha_onset*onset (no L22 as primary)

    # Component breakdown
    alpha_onset: float = 0.1
    alpha_thinking: float = 0.1
    beta_censoring: float = 0.5
    onset_term: float = 0.0
    thinking_term: float = 0.0
    censoring_penalty: float = 0.0

    # Diagnostic only — never used as primary reward
    l22_projection_diagnostic: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "reward_asr": self.reward_asr,
            "reward_sr_score": self.reward_sr_score,
            "reward_combined": self.reward_combined,
            "reward_safe_mechanistic": self.reward_safe_mechanistic,
            "alpha_onset": self.alpha_onset,
            "alpha_thinking": self.alpha_thinking,
            "beta_censoring": self.beta_censoring,
            "onset_term": self.onset_term,
            "thinking_term": self.thinking_term,
            "censoring_penalty": self.censoring_penalty,
        }


@dataclass
class OptimizationTrace:
    """Full trace of an offline optimization run."""
    run_id: str
    policy_name: str
    reward_name: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    final_selection: Optional[str] = None
    cumulative_reward: float = 0.0
    n_steps: int = 0
    notes: str = ""

    def add_step(self, step: int, candidate_id: str, reward: float, action_id: str,
                 explore: bool = False):
        self.steps.append({
            "step": step,
            "candidate_id": candidate_id,
            "action_id": action_id,
            "reward": reward,
            "explore": explore,
        })
        self.cumulative_reward += reward
        self.n_steps = step + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "policy_name": self.policy_name,
            "reward_name": self.reward_name,
            "n_steps": self.n_steps,
            "cumulative_reward": self.cumulative_reward,
            "final_selection": self.final_selection,
            "notes": self.notes,
            "steps": self.steps,
        }
