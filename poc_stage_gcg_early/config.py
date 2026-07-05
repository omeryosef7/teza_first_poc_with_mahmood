"""
Typed dataclass configuration for Stage GCG-Early.

All configuration is expressed as dataclasses so it can be serialized to/from
JSON deterministically. RunConfig.config_hash() is used to detect mismatched
checkpoint/config pairs on resume.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SurrogateTask:
    """One harmless instruction-following task for surrogate optimization."""
    task_id: str
    instruction: str
    safe_target_prefix: str
    early_prefix: Optional[str]        # optional shared early prefix (None if unused)
    neutral_control_suffix: str        # matched baseline (e.g. " " or ".")
    split: str                         # "train" | "val"
    seed: int
    model: str                         # "qwen3" | "gemma4"
    enable_thinking: bool

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SurrogateTask":
        return cls(**d)


@dataclass
class GCGHyperparams:
    """GCG optimizer hyperparameters."""
    suffix_length: int = 16
    batch_size: int = 64               # safe for L40S with Qwen3-14B; 512 will OOM
    topk: int = 256
    n_steps: int = 200
    seed: int = 42
    allow_non_ascii: bool = True
    filter_cand: bool = True           # reject candidates that change token count on re-tokenization
    checkpoint_every: int = 10        # write checkpoint.pt every N steps
    snapshot_every: int = 50          # write permanent checkpoint_step_N.pt every N steps


@dataclass
class ObjectiveWeights:
    """
    Weights and settings for the composite objective.

    Stage 3 (task-only baseline): lambda_repr=0.0, lambda_kl=0.0.
    Stage 6+ (representation objectives): set lambda_repr > 0.
    """
    lambda_repr: float = 0.0
    lambda_kl: float = 0.0
    repr_metric: str = "cosine"        # "cosine" | "l2" | "whitened_l2" (experimental)
    repr_positions: int = 3            # first X generated positions to compare
    repr_layers: List[int] = field(default_factory=list)  # empty = all layers
    per_layer_weights: List[float] = field(default_factory=list)  # empty = uniform
    per_token_weights: List[float] = field(default_factory=list)  # empty = uniform
    kl_topk_vocab: Optional[int] = None  # None = exact KL; set to e.g. 1000 for memory efficiency
    whitened_l2: bool = False          # experimental flag; must be True to activate whitened_l2 metric
    selection_mode: str = "weighted"   # "weighted" | "constrained" | "lexicographic"
    constrained_repr_threshold: float = 0.1   # for constrained mode: repr_loss <= this
    lexicographic_task_eps: float = 0.01      # for lexicographic mode: task_loss tolerance


@dataclass
class RunConfig:
    """
    Full configuration for one optimization run.

    Serialized to CONFIG.json at the very start of run_optimization.py,
    before any model load. On resume, config_hash() is compared against
    checkpoint.pt — mismatches abort with a clear error.
    """
    run_id: str
    model_family: str                  # "qwen3" | "gemma4"
    model_name_or_path: str
    manifest_path: str                 # path to surrogate_manifest_*.jsonl
    gcg: GCGHyperparams
    objective: ObjectiveWeights
    output_dir: str
    model_revision: Optional[str] = None
    enable_thinking: bool = True

    def config_hash(self) -> str:
        """SHA-256 of the full config as sorted JSON (first 16 hex chars)."""
        d = dataclasses.asdict(self)
        serialized = json.dumps(d, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, s: str) -> "RunConfig":
        d = json.loads(s)
        d["gcg"] = GCGHyperparams(**d["gcg"])
        d["objective"] = ObjectiveWeights(**d["objective"])
        return cls(**d)

    @classmethod
    def from_dict(cls, d: dict) -> "RunConfig":
        d = dict(d)
        d["gcg"] = GCGHyperparams(**d["gcg"])
        d["objective"] = ObjectiveWeights(**d["objective"])
        return cls(**d)


def make_smoke_config(
    run_id: str,
    manifest_path: str,
    output_dir: str,
    model_family: str = "qwen3",
    model_name_or_path: str = "Qwen/Qwen3-14B",
    suffix_length: int = 8,
    n_steps: int = 50,
    batch_size: int = 32,
    seed: int = 42,
) -> RunConfig:
    """Convenience constructor for the task-only Stage 3 smoke run."""
    return RunConfig(
        run_id=run_id,
        model_family=model_family,
        model_name_or_path=model_name_or_path,
        manifest_path=manifest_path,
        gcg=GCGHyperparams(
            suffix_length=suffix_length,
            batch_size=batch_size,
            topk=256,
            n_steps=n_steps,
            seed=seed,
            checkpoint_every=5,
            snapshot_every=25,
        ),
        objective=ObjectiveWeights(
            lambda_repr=0.0,
            lambda_kl=0.0,
        ),
        output_dir=output_dir,
        enable_thinking=True,
    )
