from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from poc_stage5.data_loading import load_stage5_examples_with_metadata, validate_jsonl_path
from poc_stage5.direction_loading import load_refusal_direction, validate_direction_path
from poc_stage5.projection import ProjectionRequest, describe_projection_request


@dataclass(frozen=True)
class ComputeConfig:
    input_jsonl: Path
    direction_path: Path
    model_name_or_path: str
    output_jsonl: Path
    summary_json: Path
    max_examples: int | None
    max_length: int | None
    device: str | None
    dtype: str | None
    layers: str | None
    token_regions: str | None
    no_progress: bool


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Expected a positive integer.")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 5 skeleton: validate planned refusal-projection dynamics inputs "
            "without loading a model or writing artifacts."
        )
    )
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--direction-path", required=True)
    parser.add_argument("--model-name-or-path", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--max-examples", type=_positive_int)
    parser.add_argument("--max-length", type=_positive_int)
    parser.add_argument("--device")
    parser.add_argument("--dtype")
    parser.add_argument("--layers")
    parser.add_argument("--token-regions")
    parser.add_argument("--no-progress", action="store_true")
    return parser


def validate_config(args: argparse.Namespace) -> ComputeConfig:
    input_jsonl = validate_jsonl_path(args.input_jsonl)
    direction_path = validate_direction_path(args.direction_path)
    return ComputeConfig(
        input_jsonl=input_jsonl,
        direction_path=direction_path,
        model_name_or_path=str(args.model_name_or_path),
        output_jsonl=Path(args.output_jsonl),
        summary_json=Path(args.summary_json),
        max_examples=args.max_examples,
        max_length=args.max_length,
        device=args.device,
        dtype=args.dtype,
        layers=args.layers,
        token_regions=args.token_regions,
        no_progress=bool(args.no_progress),
    )


def _json_safe_config(config: ComputeConfig) -> dict[str, Any]:
    payload = asdict(config)
    for key in ("input_jsonl", "direction_path", "output_jsonl", "summary_json"):
        payload[key] = str(payload[key])
    return payload


def _vector_dimension(vector: Any) -> int:
    shape = getattr(vector, "shape", None)
    if shape is not None:
        return int(shape[0])
    return len(vector)


def _vector_norm(vector: Any) -> float:
    if hasattr(vector, "norm"):
        norm = vector.norm()
        if hasattr(norm, "detach"):
            return float(norm.detach().cpu().item())
        return float(norm)
    values = vector.tolist() if hasattr(vector, "tolist") else vector
    return float(sum(float(value) * float(value) for value in values) ** 0.5)


def print_planned_run(config: ComputeConfig) -> None:
    loaded = load_stage5_examples_with_metadata(config.input_jsonl, max_examples=config.max_examples)
    refusal_direction = load_refusal_direction(
        config.direction_path,
        device=config.device,
        dtype=config.dtype,
    )
    projection_request = ProjectionRequest(
        layers=config.layers,
        token_regions=config.token_regions,
        max_length=config.max_length,
    )
    payload = {
        "stage": "stage5_refusal_projection_dynamics_skeleton",
        "status": "validated_inputs_only_no_model_loaded_no_outputs_written",
        "config": _json_safe_config(config),
        "loaded_examples": loaded.num_examples,
        "examples_with_response_text": loaded.num_with_response_text,
        "skipped_contentless_rows": loaded.skipped_contentless_rows,
        "detected_condition_values": loaded.condition_values,
        "first_example_ids": loaded.first_example_ids,
        "direction_dimension": _vector_dimension(refusal_direction.vector),
        "direction_norm": _vector_norm(refusal_direction.vector),
        "direction_source_path": refusal_direction.source_path,
        "projection_request": describe_projection_request(projection_request),
        "todos": [
            "load model and tokenizer",
            "normalize Stage 2/3 JSONL rows",
            "capture activations across layers and token regions",
            "write projection JSONL and summary JSON",
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = validate_config(args)
        print_planned_run(config)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
