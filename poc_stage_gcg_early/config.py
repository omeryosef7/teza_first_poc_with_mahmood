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
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# Reference-cache provenance
# ---------------------------------------------------------------------------

def reference_cache_content_id(cache_dir: Union[str, "Path"]) -> str:
    """
    Content hash (first 16 hex of SHA-256) of a reference cache's manifest.

    The manifest (REFERENCE_CACHE_MANIFEST.json, one JSON object per line) records
    task_id / cache_key / layers / positions for every cached entry, so its bytes
    change whenever the cache content changes. Hashing it — rather than the cache
    *path* — means two runs that point at byte-identical caches share a config_hash
    and may resume each other, while two runs whose caches differ never can.

    Raises FileNotFoundError if the manifest does not exist.
    """
    manifest_path = Path(cache_dir) / "REFERENCE_CACHE_MANIFEST.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Reference cache manifest not found: {manifest_path}. "
            "Build the cache with build_reference_cache.py first."
        )
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()[:16]


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
        import dataclasses as _dc
        known = {f.name for f in _dc.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in known})


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
    # Where the adversarial suffix is placed in the optimized prompt:
    #   "user"      -> inside the user turn, matching evaluate_optimized_suffixes.py (FIXED, 2026-07-19)
    #   "assistant" -> after the assistant header (LEGACY/buggy pre-2026-07-19 behavior; v1 replay only)
    # Included in config_hash (via dataclasses.asdict) so v1 and v2 never cross-resume.
    suffix_placement: str = "user"


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
    repr_at_cot_pos: bool = False      # 5B: use target_slice.start instead of suffix positions
    quick_asr_every: int = 0           # 5C: run quick prefix-match ASR check every N steps (0=off)
    repr_layers: List[int] = field(default_factory=list)  # empty = all layers
    per_layer_weights: List[float] = field(default_factory=list)  # empty = uniform
    per_token_weights: List[float] = field(default_factory=list)  # empty = uniform
    kl_topk_vocab: Optional[int] = None  # None = exact KL; set to e.g. 1000 for memory efficiency
    whitened_l2: bool = False          # experimental flag; must be True to activate whitened_l2 metric
    fluency_penalty_weight: float = 0.0  # EXPERIMENTAL: penalize low-frequency suffix bigrams (default off)
    selection_mode: str = "weighted"   # "weighted" | "constrained" | "lexicographic"
    constrained_repr_threshold: float = 0.1   # for constrained mode: repr_loss <= this
    lexicographic_task_eps: float = 0.01      # for lexicographic mode: task_loss tolerance
    lambda_refusal_dir: float = 0.0          # weight for refusal-direction projection loss
    refusal_dir_layer: int = 25              # layer for refusal direction (CoT paper: layer 25)
    refusal_dir_path: Optional[str] = None  # path to v_refusal .pt file
    # WHERE the refusal/concept projection is read. See docs/ASYMMETRY_SPRINT_EXECUTION_LOG.md E0.3.
    #   "legacy_fixed"      ONE absolute index computed from train_tasks[0] and reused for EVERY
    #                       task. This is what every published run used. On the frozen v3 train
    #                       pool it lands on the intended token for 1 of 40 prompts (defect D1),
    #                       and an out-of-range index is silently dropped, making the term 0.
    #                       DEFAULT, so existing runs replay byte-identically.
    #   "per_task_suffix"   the last SUFFIX token, recomputed per task -> fixes D1.
    #   "per_task_decision" the last PROMPT token (after the assistant header), recomputed per
    #                       task -> fixes D1 AND D2, i.e. reads the residual at the position
    #                       where the refusal axis was actually fitted and causally validated.
    refusal_dir_position_mode: str = "legacy_fixed"
    # Multi-layer refusal direction suppression (10D): if non-empty, overrides the single-layer config.
    # Each entry (layer, path, lambda) defines an additive refusal direction loss term.
    refusal_dir_layers: List[int] = field(default_factory=list)
    refusal_dir_paths: List[str] = field(default_factory=list)
    lambda_refusal_dir_per_layer: List[float] = field(default_factory=list)
    # Lambda annealing schedule (10E): list of (step, lambda) breakpoints; piecewise-linear interpolation.
    # Empty = constant lambda_refusal_dir throughout. Format: [[0, 0.7], [100, 0.3], [300, 0.1]]
    lambda_refusal_dir_schedule: List[List[float]] = field(default_factory=list)
    # --- P9.0 (2026-08-05) ---------------------------------------------------
    # repr_in_selection: run the candidate batch with output_hidden_states=True so the
    #   representation / refusal-direction terms enter CANDIDATE SELECTION, not just the
    #   gradient. None = auto (ON iff a representation objective is actually configured:
    #   lambda_repr > 0 with a cache, or any refusal-direction term). False reproduces the
    #   pre-P9.0 behaviour exactly (selection by task_loss alone, repr_loss == 0.0).
    repr_in_selection: Optional[bool] = None
    # Sub-batch size for the hidden-state forward pass during selection. Hidden states are
    # [n_layers+1, batch, seq, d_model]; a batch of 64 does not fit next to a 14B model, so
    # the candidate batch is evaluated in sub-batches and the big tensors freed each time.
    repr_selection_sub_batch: int = 8
    # Provenance (P9.0 item 2): content hash of the reference cache manifest actually used,
    # and a human-readable objective label. Both land in CONFIG.json AND in config_hash(),
    # so two arms differing only in objective wiring can never cross-resume checkpoints.
    reference_cache_id: Optional[str] = None
    objective_name: Optional[str] = None


# ObjectiveWeights fields added by P9.0 that are folded into config_hash() ONLY when
# they differ from their default. Every CONFIG.json written before 2026-08-05 leaves them
# at the default, so those runs keep their original hash and stay resumable; any run that
# sets them (all new objective arms) gets a distinct hash. repr_layers is deliberately NOT
# in this list — it is an old field that was simply never populated, and populating it is
# exactly the provenance fix, so repr arms are *meant* to change hash.
_HASH_BACKCOMPAT_DEFAULTS: Dict[str, Any] = {
    "repr_in_selection": None,
    "repr_selection_sub_batch": 8,
    "reference_cache_id": None,
    "objective_name": None,
}


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
    multi_model_family: Optional[str] = None  # e.g. "gemma4" for cross-tokenizer multi-model selection
    log_channel_token_positions: bool = False  # diagnostic only (Sprint 2 Track 1); excluded from config_hash
                                                # like run_id/output_dir/manifest_path -- a logging toggle,
                                                # not a scientific hyperparameter, so it must never change
                                                # the hash of any existing or future config.

    def config_hash(self) -> str:
        """
        SHA-256 of the scientific config (first 16 hex chars).

        Excludes deployment metadata (run_id, output_dir, manifest_path) so that
        a checkpoint can be resumed even if those fields change — e.g. moving the
        output to a different directory, renaming the run, or pointing to a copy of
        the manifest. The hash only changes when the scientific hyperparameters change:
        model identity, suffix length, batch size, topk, seed, objectives, etc.

        Objective provenance (P9.0): repr_layers, reference_cache_id and objective_name
        are part of the objective dict and therefore part of the hash — two arms that
        differ only in which layers / which reference cache the representation objective
        reads can no longer share a hash and silently cross-resume each other's
        checkpoint.pt. The fields listed in _HASH_BACKCOMPAT_DEFAULTS are omitted while
        they hold their default value, so every pre-P9.0 CONFIG.json still hashes to
        exactly the value stored in its checkpoint.
        """
        objective = dataclasses.asdict(self.objective)
        for _key, _default in _HASH_BACKCOMPAT_DEFAULTS.items():
            if objective.get(_key, _default) == _default:
                objective.pop(_key, None)
        d = {
            "model_family": self.model_family,
            "model_name_or_path": self.model_name_or_path,
            "model_revision": self.model_revision,
            "enable_thinking": self.enable_thinking,
            "multi_model_family": self.multi_model_family,
            "gcg": dataclasses.asdict(self.gcg),
            "objective": objective,
        }
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


def make_full_config(
    run_id: str,
    manifest_path: str,
    output_dir: str,
    model_family: str = "qwen3",
    model_name_or_path: str = "Qwen/Qwen3-14B",
    n_steps: int = 500,
    batch_size: int = 64,
    suffix_length: int = 20,
    seed: int = 42,
    lambda_repr: float = 1.0,
    selection_mode: str = "weighted",
    multi_model_family: Optional[str] = None,
) -> RunConfig:
    """Full-scale config matching Zou et al. 2023 (500 steps, suffix_length=20)."""
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
            allow_non_ascii=False,
            checkpoint_every=10,
            snapshot_every=50,
        ),
        objective=ObjectiveWeights(
            lambda_repr=lambda_repr,
            lambda_kl=0.0,
            selection_mode=selection_mode,
        ),
        output_dir=output_dir,
        enable_thinking=True,
        multi_model_family=multi_model_family,
    )


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
