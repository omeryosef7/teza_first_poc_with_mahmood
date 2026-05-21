from __future__ import annotations

import contextlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any, Iterable

from poc_stage4.default_prompts import REFUSAL_DATASET_DIR, load_prompt_sets
from poc_stage4.schemas import (
    INTERVENTION_SELECTED,
    PROVISIONAL_SELECTION,
    STAGE4A1_ARTIFACT_VERSION,
    make_json_safe,
    read_json,
    utc_now,
    write_json,
)
from poc_stage4.run_state import (
    append_jsonl,
    completed_rows_by_key,
    log_progress,
    progress_iter,
    validate_checkpoint_manifest,
    write_checkpoint_manifest,
)

if TYPE_CHECKING:
    import torch
    from poc_stage4.qwen3_model import Qwen3Model


STAGE4A2_ARTIFACT_VERSION = "stage4a2_v1"
SMOKE_SELECTION_STATUS = "intervention_smoke_test_only"
FINAL_SELECTION_CRITERION = (
    "lowest_harmful_refusal_score_after_ablation_with_kl_and_steering_filters"
)
DEFAULT_REFUSAL_TOKEN_STRINGS = ["I", "As"]
QWEN_UPSTREAM_REFUSAL_REFERENCE = "QWEN_REFUSAL_TOKS = [40, 2121] # ['I', 'As']"


@dataclass(frozen=True)
class InterventionSelectionConfig:
    input_dir: Path
    output_dir: Path
    model_name: str
    enable_thinking: bool
    batch_size: int
    num_harmful_val: int
    num_harmless_val: int
    validation_seed: int
    kl_threshold: float
    induce_refusal_threshold: float
    prune_layer_percentage: float | None
    top_k_projection: int | None
    dry_run: bool
    use_stage4a1_heldout_validation: bool
    refusal_token_strings: list[str] | None
    refusal_token_ids: list[int] | None
    resume: bool = False
    checkpoint_dir: Path | None = None
    no_progress: bool = False


@dataclass(frozen=True)
class CandidateIndex:
    position_index: int
    position: int
    layer: int


def load_json_list(path: str | Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Expected a JSON list at {path}.")


def _load_split_prompts(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    prompts: list[str] = []
    for item in payload:
        if isinstance(item, str):
            prompts.append(item)
        elif isinstance(item, dict) and item.get("instruction") is not None:
            prompts.append(str(item["instruction"]))
    return prompts


def _sample(items: list[str], count: int, *, seed: int) -> list[str]:
    if count <= 0:
        raise ValueError("Validation prompt count must be positive.")
    if len(items) < count:
        raise ValueError(f"Requested {count} prompts, but only {len(items)} are available.")
    rng = random.Random(seed)
    selected = list(items)
    rng.shuffle(selected)
    return selected[:count]


def load_stage4a2_validation_prompts(
    config: InterventionSelectionConfig,
    candidate_metadata: dict[str, Any],
) -> tuple[list[str], list[str], dict[str, Any]]:
    if config.use_stage4a1_heldout_validation:
        from poc_stage4.candidate_directions import split_prompts

        if not (config.dry_run or config.top_k_projection is not None):
            raise ValueError(
                "--use-stage4a1-heldout-validation is debug-only and requires --dry-run "
                "or --top-k-projection."
            )
        harmful_prompts, harmless_prompts, source_metadata = load_prompt_sets(
            num_harmful=int(candidate_metadata["num_harmful_prompts"]),
            num_harmless=int(candidate_metadata["num_harmless_prompts"]),
            seed=int(candidate_metadata["seed"]),
            use_builtin_prompts=bool(candidate_metadata.get("use_builtin_prompts", False)),
        )
        prompt_split = split_prompts(harmful_prompts, harmless_prompts, seed=int(candidate_metadata["seed"]))
        return (
            prompt_split.harmful_validation,
            prompt_split.harmless_validation,
            {
                "validation_mode": "stage4a1_heldout_debug_only",
                "validation_scientific_status": "debug_not_default_scientific_selection",
                **source_metadata,
            },
        )

    harmful_path = REFUSAL_DATASET_DIR / "harmful_val.json"
    harmless_path = REFUSAL_DATASET_DIR / "harmless_val.json"
    harmful_available = _load_split_prompts(harmful_path)
    harmless_available = _load_split_prompts(harmless_path)
    harmful = _sample(harmful_available, config.num_harmful_val, seed=config.validation_seed)
    harmless = _sample(harmless_available, config.num_harmless_val, seed=config.validation_seed + 1)
    return (
        harmful,
        harmless,
        {
            "validation_mode": "upstream_dedicated_validation_splits",
            "harmful_validation_source": str(harmful_path),
            "harmless_validation_source": str(harmless_path),
            "num_available_harmful_validation_prompts": len(harmful_available),
            "num_available_harmless_validation_prompts": len(harmless_available),
            "validation_seed": config.validation_seed,
        },
    )


def resolve_refusal_tokens(
    model_base: Qwen3Model,
    *,
    refusal_token_strings: list[str] | None,
    refusal_token_ids: list[int] | None,
) -> dict[str, Any]:
    tokenizer = model_base.tokenizer
    if refusal_token_ids:
        token_ids = [int(token_id) for token_id in refusal_token_ids]
        return {
            "refusal_token_source": "cli_token_id_override",
            "refusal_token_ids": token_ids,
            "refusal_token_decoded_strings": [
                tokenizer.decode([token_id], skip_special_tokens=False) for token_id in token_ids
            ],
            "refusal_token_strings_requested": None,
            "upstream_reference": QWEN_UPSTREAM_REFUSAL_REFERENCE,
        }

    requested = refusal_token_strings or DEFAULT_REFUSAL_TOKEN_STRINGS
    token_ids: list[int] = []
    decoded: list[str] = []
    for token_string in requested:
        encoded = tokenizer.encode(token_string, add_special_tokens=False)
        if len(encoded) != 1:
            raise ValueError(
                f"Refusal token string {token_string!r} resolved to {encoded}, not one token. "
                "Pass --refusal-token-ids to override explicitly."
            )
        token_id = int(encoded[0])
        token_ids.append(token_id)
        decoded.append(tokenizer.decode([token_id], skip_special_tokens=False))

    return {
        "refusal_token_source": "qwen_upstream_surface_forms_resolved_with_qwen3_tokenizer",
        "refusal_token_ids": token_ids,
        "refusal_token_decoded_strings": decoded,
        "refusal_token_strings_requested": requested,
        "upstream_reference": QWEN_UPSTREAM_REFUSAL_REFERENCE,
    }


@contextlib.contextmanager
def add_hooks(pre_hooks: list[tuple[Any, Any]], hooks: list[tuple[Any, Any]]):
    handles = []
    try:
        for module, hook in pre_hooks:
            handles.append(module.register_forward_pre_hook(hook))
        for module, hook in hooks:
            handles.append(module.register_forward_hook(hook))
        yield
    finally:
        for handle in handles:
            handle.remove()


def _normalized_direction(direction: torch.Tensor, activation: torch.Tensor) -> torch.Tensor:
    vector = direction.to(device=activation.device, dtype=activation.dtype)
    return vector / (vector.norm(dim=-1, keepdim=True) + 1e-8)


def get_direction_ablation_input_pre_hook(direction: torch.Tensor):
    def hook(module: Any, inputs: tuple[Any, ...]):
        activation = inputs[0] if isinstance(inputs, tuple) else inputs
        vector = _normalized_direction(direction, activation)
        patched = activation - (activation @ vector).unsqueeze(-1) * vector
        if isinstance(inputs, tuple):
            return (patched, *inputs[1:])
        return patched

    return hook


def get_direction_ablation_output_hook(direction: torch.Tensor):
    def hook(module: Any, inputs: tuple[Any, ...], output: Any):
        activation = output[0] if isinstance(output, tuple) else output
        vector = _normalized_direction(direction, activation)
        patched = activation - (activation @ vector).unsqueeze(-1) * vector
        if isinstance(output, tuple):
            return (patched, *output[1:])
        return patched

    return hook


def get_activation_addition_input_pre_hook(direction: torch.Tensor, coeff: float):
    def hook(module: Any, inputs: tuple[Any, ...]):
        activation = inputs[0] if isinstance(inputs, tuple) else inputs
        vector = direction.to(device=activation.device, dtype=activation.dtype)
        patched = activation + coeff * vector
        if isinstance(inputs, tuple):
            return (patched, *inputs[1:])
        return patched

    return hook


def build_ablation_hooks(model_base: Qwen3Model, direction: torch.Tensor) -> tuple[list[tuple[Any, Any]], list[tuple[Any, Any]]]:
    pre_hooks = [(layer, get_direction_ablation_input_pre_hook(direction)) for layer in model_base.layers]
    hooks = [(module, get_direction_ablation_output_hook(direction)) for module in model_base.attn_modules]
    hooks += [(module, get_direction_ablation_output_hook(direction)) for module in model_base.mlp_modules]
    return pre_hooks, hooks


def build_steering_hooks(model_base: Qwen3Model, direction: torch.Tensor, *, source_layer: int) -> tuple[list[tuple[Any, Any]], list[tuple[Any, Any]]]:
    return [(model_base.layers[source_layer], get_activation_addition_input_pre_hook(direction, coeff=1.0))], []


def _input_device(model: Any) -> torch.device:
    try:
        return model.get_input_embeddings().weight.device
    except Exception:
        return next(model.parameters()).device


def get_last_position_logits(
    model_base: Qwen3Model,
    prompts: list[str],
    *,
    enable_thinking: bool,
    batch_size: int,
    pre_hooks: list[tuple[Any, Any]] | None = None,
    hooks: list[tuple[Any, Any]] | None = None,
) -> torch.Tensor:
    import torch

    pre_hooks = pre_hooks or []
    hooks = hooks or []
    chunks: list[torch.Tensor] = []
    input_device = _input_device(model_base.model)

    for start in range(0, len(prompts), batch_size):
        batch_prompts = prompts[start : start + batch_size]
        tokenized = model_base.tokenize_prompts(batch_prompts, enable_thinking=enable_thinking)
        with torch.no_grad():
            with add_hooks(pre_hooks, hooks):
                logits = model_base.model(
                    input_ids=tokenized.input_ids.to(input_device),
                    attention_mask=tokenized.attention_mask.to(input_device),
                ).logits
        chunks.append(logits[:, -1, :].detach().cpu())
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return torch.cat(chunks, dim=0)


def refusal_scores_from_logits(logits: torch.Tensor, refusal_token_ids: list[int], epsilon: float = 1e-8) -> torch.Tensor:
    import torch

    logits = logits.to(torch.float64)
    probs = torch.nn.functional.softmax(logits, dim=-1)
    token_ids = torch.tensor(refusal_token_ids, dtype=torch.long, device=probs.device)
    refusal_probs = probs[:, token_ids].sum(dim=-1)
    nonrefusal_probs = torch.ones_like(refusal_probs) - refusal_probs
    return torch.log(refusal_probs + epsilon) - torch.log(nonrefusal_probs + epsilon)


def kl_divergence_from_logits(logits_a: torch.Tensor, logits_b: torch.Tensor, epsilon: float = 1e-6) -> torch.Tensor:
    import torch

    logits_a = logits_a.to(torch.float64)
    logits_b = logits_b.to(torch.float64)
    probs_a = logits_a.softmax(dim=-1)
    probs_b = logits_b.softmax(dim=-1)
    return torch.sum(probs_a * (torch.log(probs_a + epsilon) - torch.log(probs_b + epsilon)), dim=-1)


def load_candidate_directions(input_dir: str | Path, metadata: dict[str, Any]) -> torch.Tensor:
    import torch

    candidate_path = Path(input_dir) / "candidate_directions.pt"
    if not candidate_path.exists():
        raise FileNotFoundError(f"Missing candidate directions: {candidate_path}")
    candidates = torch.load(candidate_path, map_location="cpu")
    expected_shape = list(metadata.get("candidate_tensor_shape", []))
    if list(candidates.shape) != expected_shape:
        raise ValueError(
            f"Candidate tensor shape {list(candidates.shape)} does not match metadata {expected_shape}."
        )
    if candidates.ndim != 3:
        raise ValueError("candidate_directions.pt must have shape [n_position, n_layer, d_model].")
    return candidates


def all_candidate_indices(positions: list[int], num_layers: int) -> list[CandidateIndex]:
    return [
        CandidateIndex(position_index=position_index, position=int(position), layer=layer)
        for position_index, position in enumerate(positions)
        for layer in range(num_layers)
    ]


def top_k_candidate_indices(input_dir: str | Path, *, k: int) -> list[CandidateIndex]:
    diagnostics_path = Path(input_dir) / "projection_diagnostics.json"
    payload = read_json(diagnostics_path)
    rows = payload.get("diagnostics", [])
    if not isinstance(rows, list):
        raise ValueError(f"Invalid projection diagnostics at {diagnostics_path}.")
    rows = sorted(
        rows,
        key=lambda row: float(row.get("standardized_projection_separation", float("-inf"))),
        reverse=True,
    )
    selected = rows[:k]
    return [
        CandidateIndex(
            position_index=int(row["position_index"]),
            position=int(row["position"]),
            layer=int(row["layer"]),
        )
        for row in selected
    ]


def _candidate_passes_filters(
    row: dict[str, Any],
    *,
    num_layers: int,
    kl_threshold: float,
    induce_refusal_threshold: float,
    prune_layer_percentage: float | None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    score_fields = (
        "harmful_ablation_refusal_score",
        "harmless_steering_refusal_score",
        "harmless_ablation_kl_divergence",
    )
    for field in score_fields:
        value = row.get(field)
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            reasons.append(f"non_finite_{field}")

    if not reasons:
        if float(row["harmless_ablation_kl_divergence"]) > kl_threshold:
            reasons.append("kl_above_threshold")
        if float(row["harmless_steering_refusal_score"]) < induce_refusal_threshold:
            reasons.append("steering_below_threshold")
        if prune_layer_percentage is not None:
            first_pruned_layer = int(num_layers * (1.0 - prune_layer_percentage))
            if int(row["layer"]) >= first_pruned_layer:
                reasons.append("layer_pruned")

    return not reasons, reasons


def evaluate_candidates(
    *,
    model_base: Qwen3Model,
    candidate_directions: torch.Tensor,
    candidate_indices: list[CandidateIndex],
    harmful_validation_prompts: list[str],
    harmless_validation_prompts: list[str],
    refusal_token_ids: list[int],
    config: InterventionSelectionConfig,
    checkpoint_dir: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import torch

    progress_enabled = not config.no_progress
    baseline_harmful_path = checkpoint_dir / "baseline_harmful_logits.pt" if checkpoint_dir else None
    baseline_harmless_path = checkpoint_dir / "baseline_harmless_logits.pt" if checkpoint_dir else None
    if config.resume and baseline_harmful_path and baseline_harmless_path and baseline_harmful_path.exists() and baseline_harmless_path.exists():
        log_progress("stage4a2", "Loaded baseline logits from checkpoint", enabled=progress_enabled)
        baseline_harmful_logits = torch.load(baseline_harmful_path, map_location="cpu")
        baseline_harmless_logits = torch.load(baseline_harmless_path, map_location="cpu")
    else:
        log_progress("stage4a2", "Computing baseline harmful logits", enabled=progress_enabled)
        baseline_harmful_logits = get_last_position_logits(
            model_base,
            harmful_validation_prompts,
            enable_thinking=config.enable_thinking,
            batch_size=config.batch_size,
        )
        log_progress("stage4a2", "Computing baseline harmless logits", enabled=progress_enabled)
        baseline_harmless_logits = get_last_position_logits(
            model_base,
            harmless_validation_prompts,
            enable_thinking=config.enable_thinking,
            batch_size=config.batch_size,
        )
        if baseline_harmful_path and baseline_harmless_path:
            torch.save(baseline_harmful_logits, baseline_harmful_path)
            torch.save(baseline_harmless_logits, baseline_harmless_path)
            log_progress("stage4a2", "Saved baseline logits checkpoint", enabled=progress_enabled)
    baseline_harmful_scores = refusal_scores_from_logits(baseline_harmful_logits, refusal_token_ids)
    baseline_harmless_scores = refusal_scores_from_logits(baseline_harmless_logits, refusal_token_ids)

    checkpoint_jsonl = checkpoint_dir / "intervention_candidate_scores.checkpoint.jsonl" if checkpoint_dir else None
    completed: dict[tuple[Any, ...], dict[str, Any]] = {}
    if checkpoint_jsonl:
        if config.resume:
            completed = completed_rows_by_key(checkpoint_jsonl, ("position_index", "position", "layer"))
            log_progress(
                "stage4a2",
                "Loaded candidate checkpoint rows",
                enabled=progress_enabled,
                completed=len(completed),
                path=str(checkpoint_jsonl),
            )
        else:
            checkpoint_jsonl.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_jsonl.write_text("", encoding="utf-8")

    rows_by_key: dict[tuple[int, int, int], dict[str, Any]] = {}
    for candidate in progress_iter(
        candidate_indices,
        total=len(candidate_indices),
        desc="Stage 4A2 candidates",
        enabled=progress_enabled,
    ):
        key = (candidate.position_index, candidate.position, candidate.layer)
        if key in completed:
            rows_by_key[key] = completed[key]
            log_progress(
                "stage4a2",
                "Skipping completed candidate",
                enabled=progress_enabled,
                position=candidate.position,
                layer=candidate.layer,
            )
            continue

        log_progress(
            "stage4a2",
            "Evaluating candidate",
            enabled=progress_enabled,
            position_index=candidate.position_index,
            position=candidate.position,
            layer=candidate.layer,
        )
        direction = candidate_directions[candidate.position_index, candidate.layer].detach().cpu()
        ablation_pre_hooks, ablation_hooks = build_ablation_hooks(model_base, direction)
        steering_pre_hooks, steering_hooks = build_steering_hooks(
            model_base,
            direction,
            source_layer=candidate.layer,
        )

        harmless_ablation_logits = get_last_position_logits(
            model_base,
            harmless_validation_prompts,
            enable_thinking=config.enable_thinking,
            batch_size=config.batch_size,
            pre_hooks=ablation_pre_hooks,
            hooks=ablation_hooks,
        )
        harmful_ablation_logits = get_last_position_logits(
            model_base,
            harmful_validation_prompts,
            enable_thinking=config.enable_thinking,
            batch_size=config.batch_size,
            pre_hooks=ablation_pre_hooks,
            hooks=ablation_hooks,
        )
        harmless_steering_logits = get_last_position_logits(
            model_base,
            harmless_validation_prompts,
            enable_thinking=config.enable_thinking,
            batch_size=config.batch_size,
            pre_hooks=steering_pre_hooks,
            hooks=steering_hooks,
        )

        harmful_ablation_scores = refusal_scores_from_logits(harmful_ablation_logits, refusal_token_ids)
        harmless_steering_scores = refusal_scores_from_logits(harmless_steering_logits, refusal_token_ids)
        harmless_kl = kl_divergence_from_logits(baseline_harmless_logits, harmless_ablation_logits)

        row = {
            "position_index": candidate.position_index,
            "position": candidate.position,
            "layer": candidate.layer,
            "harmful_ablation_refusal_score": float(harmful_ablation_scores.mean().item()),
            "harmless_steering_refusal_score": float(harmless_steering_scores.mean().item()),
            "harmless_ablation_kl_divergence": float(harmless_kl.mean().item()),
            "baseline_harmful_refusal_score": float(baseline_harmful_scores.mean().item()),
            "baseline_harmless_refusal_score": float(baseline_harmless_scores.mean().item()),
        }
        passes, failure_reasons = _candidate_passes_filters(
            row,
            num_layers=model_base.num_layers,
            kl_threshold=config.kl_threshold,
            induce_refusal_threshold=config.induce_refusal_threshold,
            prune_layer_percentage=config.prune_layer_percentage,
        )
        row["passes_filters"] = passes
        row["filter_failure_reasons"] = failure_reasons
        rows_by_key[key] = row
        if checkpoint_jsonl:
            append_jsonl(checkpoint_jsonl, row)
        log_progress(
            "stage4a2",
            "Finished candidate",
            enabled=progress_enabled,
            position=candidate.position,
            layer=candidate.layer,
            passes_filters=passes,
            failures=",".join(failure_reasons) if failure_reasons else "none",
        )

    baseline_summary = {
        "baseline_harmful_refusal_score_mean": float(baseline_harmful_scores.mean().item()),
        "baseline_harmless_refusal_score_mean": float(baseline_harmless_scores.mean().item()),
    }
    rows = [
        rows_by_key[(candidate.position_index, candidate.position, candidate.layer)]
        for candidate in candidate_indices
        if (candidate.position_index, candidate.position, candidate.layer) in rows_by_key
    ]
    if len(rows) != len(candidate_indices):
        raise RuntimeError(
            f"Only {len(rows)} of {len(candidate_indices)} candidates are complete after resume/evaluation."
        )
    return rows, baseline_summary


def select_final_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    survivors = [row for row in rows if bool(row.get("passes_filters"))]
    if not survivors:
        raise RuntimeError("No intervention-evaluated candidates survived the configured filters.")
    return min(survivors, key=lambda row: float(row["harmful_ablation_refusal_score"]))


def run_intervention_selection(
    *,
    config: InterventionSelectionConfig,
    model_base: Qwen3Model,
) -> dict[str, Any]:
    import torch

    input_dir = config.input_dir
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_enabled = not config.no_progress
    checkpoint_dir = config.checkpoint_dir or (output_dir / "checkpoints" / "stage4a2")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    log_progress(
        "stage4a2",
        "Starting intervention-based selection",
        enabled=progress_enabled,
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        checkpoint_dir=str(checkpoint_dir),
        resume=config.resume,
    )

    candidate_metadata_path = input_dir / "candidate_metadata.json"
    candidate_metadata = read_json(candidate_metadata_path)
    if candidate_metadata.get("artifact_version") != STAGE4A1_ARTIFACT_VERSION:
        raise ValueError(f"Unexpected Stage 4A1 artifact version in {candidate_metadata_path}.")

    candidate_directions = load_candidate_directions(input_dir, candidate_metadata)
    positions = [int(position) for position in candidate_metadata["positions"]]
    num_layers = int(candidate_metadata["num_layers"])

    smoke_mode = bool(config.dry_run or config.top_k_projection is not None)
    if config.top_k_projection is not None:
        candidate_indices = top_k_candidate_indices(input_dir, k=config.top_k_projection)
    elif config.dry_run:
        candidate_indices = top_k_candidate_indices(input_dir, k=5)
    else:
        candidate_indices = all_candidate_indices(positions, num_layers)

    checkpoint_payload = {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "model_name": config.model_name,
        "enable_thinking": config.enable_thinking,
        "batch_size": config.batch_size,
        "num_harmful_val": config.num_harmful_val,
        "num_harmless_val": config.num_harmless_val,
        "validation_seed": config.validation_seed,
        "kl_threshold": config.kl_threshold,
        "induce_refusal_threshold": config.induce_refusal_threshold,
        "prune_layer_percentage": config.prune_layer_percentage,
        "top_k_projection": config.top_k_projection,
        "dry_run": config.dry_run,
        "use_stage4a1_heldout_validation": config.use_stage4a1_heldout_validation,
        "refusal_token_strings": config.refusal_token_strings,
        "refusal_token_ids": config.refusal_token_ids,
        "candidate_tensor_shape": list(candidate_directions.shape),
        "candidate_indices": [asdict(candidate) for candidate in candidate_indices],
    }
    if config.resume:
        validate_checkpoint_manifest(checkpoint_dir, stage="stage4a2", fingerprint_payload=checkpoint_payload)
    write_checkpoint_manifest(
        checkpoint_dir,
        stage="stage4a2",
        fingerprint_payload=checkpoint_payload,
        extra={"checkpoint_dir": str(checkpoint_dir)},
    )
    log_progress(
        "stage4a2",
        "Prepared candidate list",
        enabled=progress_enabled,
        candidates=len(candidate_indices),
        smoke_mode=bool(config.dry_run or config.top_k_projection is not None),
    )

    harmful_validation, harmless_validation, validation_metadata = load_stage4a2_validation_prompts(
        config,
        candidate_metadata,
    )
    refusal_metadata = resolve_refusal_tokens(
        model_base,
        refusal_token_strings=config.refusal_token_strings,
        refusal_token_ids=config.refusal_token_ids,
    )
    log_progress(
        "stage4a2",
        "Resolved refusal tokens",
        enabled=progress_enabled,
        token_ids=refusal_metadata["refusal_token_ids"],
    )

    rows, baseline_summary = evaluate_candidates(
        model_base=model_base,
        candidate_directions=candidate_directions,
        candidate_indices=candidate_indices,
        harmful_validation_prompts=harmful_validation,
        harmless_validation_prompts=harmless_validation,
        refusal_token_ids=[int(token_id) for token_id in refusal_metadata["refusal_token_ids"]],
        config=config,
        checkpoint_dir=checkpoint_dir,
    )

    survivors = [row for row in rows if bool(row.get("passes_filters"))]
    selected_row: dict[str, Any] | None = None
    selection_status = SMOKE_SELECTION_STATUS if smoke_mode else INTERVENTION_SELECTED
    if survivors:
        selected_row = select_final_candidate(rows)
        log_progress(
            "stage4a2",
            "Selected intervention candidate",
            enabled=progress_enabled,
            position=selected_row["position"],
            layer=selected_row["layer"],
            survivors=len(survivors),
        )
    elif not smoke_mode:
        write_json(output_dir / "intervention_candidate_scores.json", {"candidates": rows})
        raise RuntimeError("No candidates survived filters; leaving direction.pt and selected_direction.json unchanged.")

    timestamp = utc_now()
    base_payload: dict[str, Any] = {
        "artifact_version": STAGE4A2_ARTIFACT_VERSION,
        "stage": "stage4a2_intervention_based_refusal_direction_selection",
        "timestamp_utc": timestamp,
        "selection_status": selection_status,
        "selection_criterion": FINAL_SELECTION_CRITERION,
        "model_name": config.model_name,
        "enable_thinking": config.enable_thinking,
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "stage4a1_candidate_directions_path": str(input_dir / "candidate_directions.pt"),
        "stage4a1_candidate_metadata_path": str(candidate_metadata_path),
        "candidate_tensor_shape": list(candidate_directions.shape),
        "num_candidates_available": int(candidate_directions.shape[0] * candidate_directions.shape[1]),
        "num_candidates_evaluated": len(rows),
        "num_candidates_surviving_filters": len(survivors),
        "smoke_mode": smoke_mode,
        "top_k_projection": config.top_k_projection,
        "dry_run": config.dry_run,
        "kl_threshold": config.kl_threshold,
        "induce_refusal_threshold": config.induce_refusal_threshold,
        "prune_layer_percentage": config.prune_layer_percentage,
        "batch_size": config.batch_size,
        "num_harmful_validation_prompts": len(harmful_validation),
        "num_harmless_validation_prompts": len(harmless_validation),
        **validation_metadata,
        **refusal_metadata,
        **baseline_summary,
    }

    candidate_scores_payload = {
        **base_payload,
        "candidates": rows,
    }
    write_json(output_dir / "intervention_candidate_scores.json", candidate_scores_payload)

    if selected_row is not None:
        base_payload.update(
            {
                "selected_position_index": int(selected_row["position_index"]),
                "selected_position": int(selected_row["position"]),
                "selected_layer": int(selected_row["layer"]),
                "harmful_ablation_refusal_score": selected_row["harmful_ablation_refusal_score"],
                "harmless_steering_refusal_score": selected_row["harmless_steering_refusal_score"],
                "harmless_ablation_kl_divergence": selected_row["harmless_ablation_kl_divergence"],
            }
        )

    write_json(output_dir / "intervention_selection_metrics.json", base_payload)

    if not smoke_mode and selected_row is not None:
        selected_direction = candidate_directions[
            int(selected_row["position_index"]),
            int(selected_row["layer"]),
        ].detach().cpu()
        torch.save(selected_direction, output_dir / "direction.pt")
        selected_payload = {
            **base_payload,
            "direction_path": str(output_dir / "direction.pt"),
            "direction_norm": float(selected_direction.norm().item()),
        }
        write_json(output_dir / "selected_direction.json", selected_payload)
        log_progress("stage4a2", "Updated final selected direction", enabled=progress_enabled)

    log_progress(
        "stage4a2",
        "Finished intervention selection",
        enabled=progress_enabled,
        selection_status=base_payload["selection_status"],
        evaluated=len(rows),
        survivors=len(survivors),
    )
    return base_payload
