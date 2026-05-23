from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from poc_stage4.extract_refusal_direction import DEFAULT_QWEN3_MODEL as DEFAULT_STAGE4_MODEL
from poc_stage4.extract_refusal_direction import run_extraction
from poc_stage4.intervention_selection import (
    CandidateIndex,
    FINAL_SELECTION_CRITERION,
    INTERVENTION_SELECTED,
    InterventionSelectionConfig,
    evaluate_candidates,
    load_stage4a2_validation_prompts,
    resolve_refusal_tokens,
    run_intervention_selection,
)
from poc_stage4.schemas import ExtractionConfig, make_json_safe, read_json, utc_now, write_json


DEFAULT_OUTPUT_DIR = Path("outputs/stage4/qwen3-14b/refusal_direction/upstream_direction_validation")
DEFAULT_REFUSAL_TOKEN_STRINGS = ["I", "As"]


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected true or false.")


def _parse_csv_ints(value: str | None) -> list[int] | None:
    if value is None or not value.strip():
        return None
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _parse_csv_strings(value: str | None) -> list[str] | None:
    if value is None or not value.strip():
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_positions(value: str | None) -> list[int]:
    if value:
        positions = [int(item.strip()) for item in value.split(",") if item.strip()]
    else:
        positions = [-1, -2, -3, -4]
    if not positions:
        raise ValueError("At least one prompt-end-relative position is required.")
    invalid = [position for position in positions if position >= 0]
    if invalid:
        raise ValueError(
            "Stage 4A1 positions must be prompt-end-relative negative offsets, "
            f"for example -1,-2,-3,-4. Invalid values: {invalid}"
        )
    return positions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a released upstream refusal direction for Qwen3-14B. "
            "If no compatible upstream direction exists, reproduce the upstream extraction pipeline "
            "into a separate output directory instead of using the local provisional candidate."
        )
    )
    parser.add_argument("--direction-dir", help="Path to an upstream release directory with direction.pt.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--model-name", default=DEFAULT_STAGE4_MODEL)
    parser.add_argument("--enable-thinking", type=parse_bool, default=False)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--num-harmful-val", type=int, default=32)
    parser.add_argument("--num-harmless-val", type=int, default=32)
    parser.add_argument("--validation-seed", type=int, default=42)
    parser.add_argument("--kl-threshold", type=float, default=0.1)
    parser.add_argument("--induce-refusal-threshold", type=float, default=0.0)
    parser.add_argument("--prune-layer-percentage", type=float, default=0.2)
    parser.add_argument("--no-layer-pruning", action="store_true")
    parser.add_argument("--refusal-token-strings", default=",".join(DEFAULT_REFUSAL_TOKEN_STRINGS))
    parser.add_argument("--refusal-token-ids")
    parser.add_argument("--no-progress", action="store_true", help="Disable timestamped progress logs and tqdm bars.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow the fallback reproduction run to replace existing stage 4 artifacts in the output directory.",
    )
    parser.add_argument(
        "--positions",
        help="Comma-separated negative prompt-end-relative positions for the fallback reproduction run.",
    )
    parser.add_argument(
        "--num-harmful",
        type=int,
        default=64,
        help="Number of harmful prompts to use when reproducing the upstream extraction method.",
    )
    parser.add_argument(
        "--num-harmless",
        type=int,
        default=64,
        help="Number of harmless prompts to use when reproducing the upstream extraction method.",
    )
    parser.add_argument(
        "--direction-normalization",
        choices=("unit", "raw"),
        default="unit",
        help="How to store fallback Stage 4A1 candidate directions: unit-normalized or raw harmful_mean-harmless_mean.",
    )
    parser.add_argument(
        "--top-k-projection",
        type=int,
        help="Only evaluate the top K promising candidates based on projection ranking.",
    )
    return parser


def _source_metadata_path(direction_dir: Path) -> Path:
    selected_path = direction_dir / "selected_direction.json"
    if selected_path.exists():
        return selected_path
    metadata_path = direction_dir / "direction_metadata.json"
    if metadata_path.exists():
        return metadata_path
    raise FileNotFoundError(
        f"Missing direction metadata. Expected {selected_path.name} or {metadata_path.name} in {direction_dir}."
    )


def _resolve_source_position_layer(metadata: dict[str, Any]) -> tuple[int, int]:
    position = metadata.get("selected_position", metadata.get("pos"))
    layer = metadata.get("selected_layer", metadata.get("layer"))
    if position is None or layer is None:
        raise ValueError("Direction metadata must include a position/layer pair.")
    return int(position), int(layer)


def _build_validation_config(args: argparse.Namespace, *, output_dir: Path) -> InterventionSelectionConfig:
    return InterventionSelectionConfig(
        input_dir=output_dir,
        output_dir=output_dir,
        model_name=args.model_name,
        enable_thinking=bool(args.enable_thinking),
        batch_size=args.batch_size,
        num_harmful_val=args.num_harmful_val,
        num_harmless_val=args.num_harmless_val,
        validation_seed=args.validation_seed,
        kl_threshold=args.kl_threshold,
        induce_refusal_threshold=args.induce_refusal_threshold,
        prune_layer_percentage=None if args.no_layer_pruning else args.prune_layer_percentage,
        top_k_projection=args.top_k_projection,
        dry_run=False,
        use_stage4a1_heldout_validation=False,
        refusal_token_strings=_parse_csv_strings(args.refusal_token_strings),
        refusal_token_ids=_parse_csv_ints(args.refusal_token_ids),
        resume=False,
        checkpoint_dir=None,
        no_progress=bool(args.no_progress),
        sign_scale_diagnostics=False,
        sign_scale_output=output_dir / "sign_scale_diagnostics.json",
    )


def _validation_payload_base(
    *,
    model_name: str,
    model_base: Any,
    output_dir: Path,
    validation_mode: str,
) -> dict[str, Any]:
    return {
        "artifact_version": "stage4a2_upstream_direction_validation_v1",
        "stage": "stage4a2_upstream_direction_validation",
        "timestamp_utc": utc_now(),
        "model_name": model_name,
        "model_hidden_size": int(model_base.hidden_size),
        "model_num_layers": int(model_base.num_layers),
        "output_dir": str(output_dir),
        "validation_mode": validation_mode,
        "selection_criterion": FINAL_SELECTION_CRITERION,
    }


def _validate_imported_direction(
    *,
    direction_dir: Path,
    output_dir: Path,
    args: argparse.Namespace,
    model_base: Any,
) -> dict[str, Any] | None:
    import torch

    direction_path = direction_dir / "direction.pt"
    if not direction_path.exists():
        return None

    metadata_path = _source_metadata_path(direction_dir)
    metadata = read_json(metadata_path)
    if metadata_path.name == "selected_direction.json" and metadata.get("selection_status") != INTERVENTION_SELECTED:
        return None

    source_position, source_layer = _resolve_source_position_layer(metadata)
    direction = torch.load(direction_path, map_location="cpu")
    if direction.ndim != 1:
        return None
    if int(direction.shape[-1]) != int(model_base.hidden_size):
        return None
    if source_layer < 0 or source_layer >= int(model_base.num_layers):
        return None

    validation_config = _build_validation_config(args, output_dir=output_dir)
    harmful_validation, harmless_validation, validation_metadata = load_stage4a2_validation_prompts(
        validation_config,
        {
            "num_harmful_prompts": 0,
            "num_harmless_prompts": 0,
            "seed": validation_config.validation_seed,
            "use_builtin_prompts": False,
        },
    )
    refusal_metadata = resolve_refusal_tokens(
        model_base,
        refusal_token_strings=validation_config.refusal_token_strings,
        refusal_token_ids=validation_config.refusal_token_ids,
    )
    candidate_directions = torch.zeros(
        (1, int(model_base.num_layers), int(model_base.hidden_size)),
        dtype=direction.dtype,
    )
    candidate_directions[0, source_layer] = direction.detach().cpu()
    candidate_indices = [CandidateIndex(position_index=0, position=source_position, layer=source_layer)]

    rows, baseline_summary = evaluate_candidates(
        model_base=model_base,
        candidate_directions=candidate_directions,
        candidate_indices=candidate_indices,
        harmful_validation_prompts=harmful_validation,
        harmless_validation_prompts=harmless_validation,
        refusal_token_ids=[int(token_id) for token_id in refusal_metadata["refusal_token_ids"]],
        config=validation_config,
        checkpoint_dir=None,
    )
    row = rows[0]
    validated = bool(row.get("passes_filters"))

    payload = {
        **_validation_payload_base(
            model_name=args.model_name,
            model_base=model_base,
            output_dir=output_dir,
            validation_mode="imported_upstream_direction",
        ),
        "validated": validated,
        "selection_status": INTERVENTION_SELECTED if validated else "intervention_selection_failed_no_survivors",
        "source_direction_dir": str(direction_dir),
        "source_direction_path": str(direction_path),
        "source_metadata_path": str(metadata_path),
        "source_metadata": make_json_safe(metadata),
        "source_position": source_position,
        "source_layer": source_layer,
        "direction_norm": float(direction.norm().item()),
        **validation_metadata,
        **refusal_metadata,
        **baseline_summary,
        "candidate": row,
    }
    if validated:
        payload["direction_path"] = str(direction_path)

    write_json(output_dir / "upstream_direction_validation.json", payload)
    return payload


def _reproduce_upstream_method(
    *,
    output_dir: Path,
    args: argparse.Namespace,
    model_base: Any | None,
) -> dict[str, Any]:
    from poc_stage4.qwen3_model import load_qwen3_model

    extraction_config = ExtractionConfig(
        model_name=args.model_name,
        output_dir=output_dir,
        dry_run=False,
        num_harmful=args.num_harmful,
        num_harmless=args.num_harmless,
        batch_size=1,
        positions=_parse_positions(args.positions),
        enable_thinking=bool(args.enable_thinking),
        seed=42,
        direction_normalization=args.direction_normalization,
        overwrite=bool(args.overwrite),
        use_builtin_prompts=False,
        resume=False,
        checkpoint_dir=None,
        no_progress=bool(args.no_progress),
    )
    run_extraction(extraction_config)

    if model_base is None:
        model_base = load_qwen3_model(args.model_name)

    selection_config = _build_validation_config(args, output_dir=output_dir)
    metrics = run_intervention_selection(config=selection_config, model_base=model_base)

    payload = {
        **_validation_payload_base(
            model_name=args.model_name,
            model_base=model_base,
            output_dir=output_dir,
            validation_mode="reproduced_upstream_method",
        ),
        "validated": metrics.get("selection_status") == INTERVENTION_SELECTED,
        "selection_status": metrics.get("selection_status"),
        "selection_criterion": metrics.get("selection_criterion", FINAL_SELECTION_CRITERION),
        "stage4a1_output_dir": str(output_dir),
        "stage4a1_candidate_metadata_path": str(output_dir / "candidate_metadata.json"),
        "stage4a2_metrics_path": str(output_dir / "intervention_selection_metrics.json"),
        "stage4a2_candidate_scores_path": str(output_dir / "intervention_candidate_scores.json"),
        "stage4a2_direction_path": str(output_dir / "direction.pt"),
        "stage4a2_selected_direction_path": str(output_dir / "selected_direction.json"),
        "direction_normalization": args.direction_normalization,
        "intervention_selection_metrics": make_json_safe(metrics),
    }
    if payload["validated"]:
        payload["direction_path"] = str(output_dir / "direction.pt")

    write_json(output_dir / "upstream_direction_validation.json", payload)
    return payload


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from poc_stage4.qwen3_model import load_qwen3_model

    model_base = None
    if args.direction_dir:
        model_base = load_qwen3_model(args.model_name)
        imported = _validate_imported_direction(
            direction_dir=Path(args.direction_dir),
            output_dir=output_dir,
            args=args,
            model_base=model_base,
        )
        if imported is not None:
            print(f"Wrote upstream direction validation to: {output_dir / 'upstream_direction_validation.json'}")
            print(f"Validated: {imported['validated']}")
            return 0

    result = _reproduce_upstream_method(output_dir=output_dir, args=args, model_base=model_base)
    print(f"Wrote upstream direction validation to: {output_dir / 'upstream_direction_validation.json'}")
    print(f"Validated: {result['validated']}")
    if result.get("selection_status") == INTERVENTION_SELECTED:
        print(f"Selected position: {result.get('selected_position')}")
        print(f"Selected layer: {result.get('selected_layer')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
