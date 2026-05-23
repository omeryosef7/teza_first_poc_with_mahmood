from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from poc_stage4.default_prompts import load_prompt_sets
from poc_stage4.schemas import (
    PROVISIONAL_SELECTION,
    PROVISIONAL_SELECTION_CRITERION,
    STAGE4A1_ARTIFACT_VERSION,
    ExtractionConfig,
    config_as_metadata,
    utc_now,
    write_json,
)
from poc_stage4.run_state import log_progress, validate_checkpoint_manifest, write_checkpoint_manifest

if TYPE_CHECKING:
    import torch


DEFAULT_QWEN3_MODEL = "Qwen/Qwen3-14B"
DEFAULT_OUTPUT_DIR = Path("outputs/stage4/qwen3-14b/refusal_direction")
OUTPUT_FILENAMES = (
    "candidate_directions.pt",
    "candidate_metadata.json",
    "projection_diagnostics.json",
    "direction.pt",
    "selected_direction.json",
    "extraction_metrics.json",
)


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected true or false.")


def parse_positions(value: str | None, *, num_positions: int | None) -> list[int]:
    if value:
        positions = [int(item.strip()) for item in value.split(",") if item.strip()]
    else:
        count = 3 if num_positions is None else num_positions
        if count <= 0:
            raise ValueError("--num-positions must be positive.")
        positions = list(range(-1, -count - 1, -1))
    if not positions:
        raise ValueError("At least one token position is required.")
    invalid = [position for position in positions if position >= 0]
    if invalid:
        raise ValueError(
            "Stage 4A1 positions must be prompt-end-relative negative offsets, "
            f"for example -1,-2,-3. Invalid values: {invalid}"
        )
    return positions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 4A1: extract Qwen3-14B position x layer candidate refusal directions "
            "and save projection diagnostics. The saved direction.pt is provisional."
        )
    )
    parser.add_argument("--model-name", default=DEFAULT_QWEN3_MODEL)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--num-harmful", type=int)
    parser.add_argument("--num-harmless", type=int)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--positions", help="Comma-separated negative prompt-end-relative positions, e.g. -1,-2,-3.")
    parser.add_argument("--num-positions", type=int, help="Use positions -1 through -N when --positions is omitted.")
    parser.add_argument("--enable-thinking", type=parse_bool, default=False)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--direction-normalization",
        choices=("unit", "raw"),
        default="unit",
        help="How to store Stage 4A1 candidate directions: unit-normalized or raw harmful_mean-harmless_mean.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Resume from Stage 4A1 checkpoint batches.")
    parser.add_argument("--checkpoint-dir", help="Directory for Stage 4A1 resumable checkpoints.")
    parser.add_argument("--no-progress", action="store_true", help="Disable tqdm/progress logging.")
    parser.add_argument(
        "--use-builtin-prompts",
        action="store_true",
        help="Use the small built-in prompt lists instead of the vendored refusal_direction train splits.",
    )
    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] == "--positions" and index + 1 < len(argv):
            normalized.append(f"--positions={argv[index + 1]}")
            index += 2
            continue
        normalized.append(argv[index])
        index += 1
    return normalized


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    raw_args = sys.argv[1:] if argv is None else argv
    return build_parser().parse_args(_normalize_argv(raw_args))


def _check_outputs(output_dir: Path, *, overwrite: bool) -> None:
    existing = [output_dir / filename for filename in OUTPUT_FILENAMES if (output_dir / filename).exists()]
    if existing and not overwrite:
        formatted = "\n".join(f"  {path}" for path in existing)
        raise RuntimeError(
            "Stage 4A1 output files already exist. Use --overwrite to replace them:\n" + formatted
        )


def _checkpoint_config(config: ExtractionConfig) -> dict[str, Any]:
    return {
        "model_name": config.model_name,
        "dry_run": config.dry_run,
        "num_harmful": config.num_harmful,
        "num_harmless": config.num_harmless,
        "batch_size": config.batch_size,
        "positions": config.positions,
        "enable_thinking": config.enable_thinking,
        "seed": config.seed,
        "direction_normalization": config.direction_normalization,
        "use_builtin_prompts": config.use_builtin_prompts,
    }


def _default_prompt_count(args: argparse.Namespace, *, harmful: bool) -> int:
    explicit = args.num_harmful if harmful else args.num_harmless
    if explicit is not None:
        return explicit
    return 4 if args.dry_run else 64


def save_provisional_direction(
    *,
    output_dir: Path,
    candidate_directions: "torch.Tensor",
    selection: Any,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Save a Stage 4A1 smoke-test direction with explicit provisional status."""

    import torch

    selected_direction = candidate_directions[
        selection.selected_position_index,
        selection.selected_layer,
    ].detach().cpu()
    direction_path = output_dir / "direction.pt"
    torch.save(selected_direction, direction_path)

    selected_metadata = {
        **metadata,
        "selection_status": PROVISIONAL_SELECTION,
        "selection_criterion": PROVISIONAL_SELECTION_CRITERION,
        "selected_position_index": selection.selected_position_index,
        "selected_position": selection.selected_position,
        "selected_layer": selection.selected_layer,
        "selected_score": selection.selected_score,
        "selected_harmful_projection_mean": selection.selected_harmful_projection_mean,
        "selected_harmless_projection_mean": selection.selected_harmless_projection_mean,
        "direction_norm": float(selected_direction.norm().item()),
        "direction_path": str(direction_path),
        "scientific_use_warning": (
            "This direction was selected only by Stage 4A1 projection diagnostics. "
            "It is provisional and must not be treated as intervention-selected. "
            "Run Stage 4A2 intervention-based selection before scientific use."
        ),
    }
    write_json(output_dir / "selected_direction.json", selected_metadata)
    return selected_metadata


def run_extraction(config: ExtractionConfig) -> dict[str, Any]:
    import torch

    from poc_stage4.activation_capture import capture_residual_input_activations
    from poc_stage4.candidate_directions import generate_candidate_directions, split_prompts
    from poc_stage4.projection_diagnostics import compute_projection_diagnostics, summarize_diagnostics
    from poc_stage4.qwen3_model import load_qwen3_model

    output_dir = config.output_dir
    progress_enabled = not config.no_progress
    checkpoint_dir = config.checkpoint_dir or (output_dir / "checkpoints" / "stage4a1")
    checkpoint_payload = _checkpoint_config(config)
    if config.resume:
        validate_checkpoint_manifest(checkpoint_dir, stage="stage4a1", fingerprint_payload=checkpoint_payload)
    _check_outputs(output_dir, overwrite=config.overwrite or config.resume)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_checkpoint_manifest(
        checkpoint_dir,
        stage="stage4a1",
        fingerprint_payload=checkpoint_payload,
        extra={"checkpoint_dir": str(checkpoint_dir), "output_dir": str(output_dir)},
    )

    log_progress(
        "stage4a1",
        "Starting refusal-direction candidate extraction",
        enabled=progress_enabled,
        output_dir=str(output_dir),
        checkpoint_dir=str(checkpoint_dir),
        resume=config.resume,
    )

    log_progress("stage4a1", "Loading prompt sets", enabled=progress_enabled)
    harmful_prompts, harmless_prompts, prompt_source_metadata = load_prompt_sets(
        num_harmful=config.num_harmful,
        num_harmless=config.num_harmless,
        seed=config.seed,
        use_builtin_prompts=config.use_builtin_prompts,
    )
    prompt_split = split_prompts(harmful_prompts, harmless_prompts, seed=config.seed)
    log_progress(
        "stage4a1",
        "Loaded prompt split",
        enabled=progress_enabled,
        harmful_train=len(prompt_split.harmful_train),
        harmless_train=len(prompt_split.harmless_train),
        harmful_validation=len(prompt_split.harmful_validation),
        harmless_validation=len(prompt_split.harmless_validation),
    )

    log_progress("stage4a1", "Loading Qwen3 model", enabled=progress_enabled, model=config.model_name)
    model_base = load_qwen3_model(config.model_name)
    log_progress(
        "stage4a1",
        "Loaded Qwen3 model",
        enabled=progress_enabled,
        num_layers=model_base.num_layers,
        hidden_size=model_base.hidden_size,
    )

    log_progress("stage4a1", "Capturing harmful train activations", enabled=progress_enabled)
    harmful_train_activations = capture_residual_input_activations(
        model_base,
        prompt_split.harmful_train,
        positions=config.positions,
        batch_size=config.batch_size,
        enable_thinking=config.enable_thinking,
        checkpoint_dir=str(checkpoint_dir),
        checkpoint_prefix="harmful_train",
        resume=config.resume,
        progress_enabled=progress_enabled,
    )
    log_progress("stage4a1", "Capturing harmless train activations", enabled=progress_enabled)
    harmless_train_activations = capture_residual_input_activations(
        model_base,
        prompt_split.harmless_train,
        positions=config.positions,
        batch_size=config.batch_size,
        enable_thinking=config.enable_thinking,
        checkpoint_dir=str(checkpoint_dir),
        checkpoint_prefix="harmless_train",
        resume=config.resume,
        progress_enabled=progress_enabled,
    )
    log_progress("stage4a1", "Generating candidate directions", enabled=progress_enabled)
    candidate_directions = generate_candidate_directions(
        harmful_train_activations,
        harmless_train_activations,
        direction_normalization=config.direction_normalization,
    )
    torch.save(candidate_directions.cpu(), output_dir / "candidate_directions.pt")
    log_progress(
        "stage4a1",
        "Saved candidate directions",
        enabled=progress_enabled,
        shape=list(candidate_directions.shape),
    )

    log_progress("stage4a1", "Capturing harmful validation activations", enabled=progress_enabled)
    harmful_validation_activations = capture_residual_input_activations(
        model_base,
        prompt_split.harmful_validation,
        positions=config.positions,
        batch_size=config.batch_size,
        enable_thinking=config.enable_thinking,
        checkpoint_dir=str(checkpoint_dir),
        checkpoint_prefix="harmful_validation",
        resume=config.resume,
        progress_enabled=progress_enabled,
    )
    log_progress("stage4a1", "Capturing harmless validation activations", enabled=progress_enabled)
    harmless_validation_activations = capture_residual_input_activations(
        model_base,
        prompt_split.harmless_validation,
        positions=config.positions,
        batch_size=config.batch_size,
        enable_thinking=config.enable_thinking,
        checkpoint_dir=str(checkpoint_dir),
        checkpoint_prefix="harmless_validation",
        resume=config.resume,
        progress_enabled=progress_enabled,
    )
    log_progress("stage4a1", "Computing projection diagnostics", enabled=progress_enabled)
    diagnostic_rows, selection = compute_projection_diagnostics(
        candidate_directions,
        harmful_validation_activations,
        harmless_validation_activations,
        positions=config.positions,
    )

    timestamp_utc = utc_now()
    base_metadata: dict[str, Any] = {
        "artifact_version": STAGE4A1_ARTIFACT_VERSION,
        "stage": "stage4a1_candidate_refusal_direction_extraction",
        "timestamp_utc": timestamp_utc,
        "model_name": config.model_name,
        "model_family": "qwen3",
        "num_harmful_prompts": config.num_harmful,
        "num_harmless_prompts": config.num_harmless,
        "num_harmful_train_prompts": len(prompt_split.harmful_train),
        "num_harmless_train_prompts": len(prompt_split.harmless_train),
        "num_harmful_validation_prompts": len(prompt_split.harmful_validation),
        "num_harmless_validation_prompts": len(prompt_split.harmless_validation),
        "positions": config.positions,
        "token_position_semantics": "prompt_end_relative_negative_offsets",
        "layers": list(range(model_base.num_layers)),
        "num_layers": model_base.num_layers,
        "hidden_size": model_base.hidden_size,
        "candidate_tensor_shape": list(candidate_directions.shape),
        "enable_thinking": config.enable_thinking,
        "batch_size": config.batch_size,
        "seed": config.seed,
        "direction_normalization": config.direction_normalization,
        "dry_run": config.dry_run,
        "device_summary": model_base.device_summary,
        **prompt_source_metadata,
    }

    write_json(output_dir / "candidate_metadata.json", base_metadata)
    diagnostics_payload = {
        **base_metadata,
        "selection_status": PROVISIONAL_SELECTION,
        "selection_criterion": PROVISIONAL_SELECTION_CRITERION,
        "diagnostic_summary": summarize_diagnostics(diagnostic_rows),
        "diagnostics": diagnostic_rows,
    }
    write_json(output_dir / "projection_diagnostics.json", diagnostics_payload)
    selected_metadata = save_provisional_direction(
        output_dir=output_dir,
        candidate_directions=candidate_directions,
        selection=selection,
        metadata=base_metadata,
    )

    metrics = {
        **base_metadata,
        "config": config_as_metadata(config),
        "outputs": {filename: str(output_dir / filename) for filename in OUTPUT_FILENAMES},
        "selection": selected_metadata,
        "diagnostic_summary": summarize_diagnostics(diagnostic_rows),
    }
    write_json(output_dir / "extraction_metrics.json", metrics)
    log_progress(
        "stage4a1",
        "Finished Stage 4A1 extraction",
        enabled=progress_enabled,
        selected_position=selected_metadata["selected_position"],
        selected_layer=selected_metadata["selected_layer"],
    )
    return metrics


def main() -> int:
    args = parse_args()
    try:
        positions = parse_positions(args.positions, num_positions=args.num_positions)
        config = ExtractionConfig(
            model_name=args.model_name,
            output_dir=Path(args.output_dir),
            dry_run=bool(args.dry_run),
            num_harmful=_default_prompt_count(args, harmful=True),
            num_harmless=_default_prompt_count(args, harmful=False),
            batch_size=args.batch_size,
            positions=positions,
            enable_thinking=bool(args.enable_thinking),
            seed=args.seed,
            overwrite=bool(args.overwrite),
            use_builtin_prompts=bool(args.use_builtin_prompts),
            direction_normalization=args.direction_normalization,
            resume=bool(args.resume),
            checkpoint_dir=Path(args.checkpoint_dir) if args.checkpoint_dir else None,
            no_progress=bool(args.no_progress),
        )
        metrics = run_extraction(config)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Wrote Stage 4A1 artifacts to: {config.output_dir}")
    print(
        "Saved direction.pt is provisional; downstream loaders reject it unless "
        "`allow_provisional_direction=True` / `--allow-provisional-direction` is used."
    )
    print(f"Selected provisional position: {metrics['selection']['selected_position']}")
    print(f"Selected provisional layer: {metrics['selection']['selected_layer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
