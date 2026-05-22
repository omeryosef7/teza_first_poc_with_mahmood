from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from poc_stage5.data_loading import Stage5Example, load_stage5_examples_with_metadata, validate_jsonl_path
from poc_stage5.direction_loading import load_refusal_direction, validate_direction_path
from poc_stage5.projection import (
    SUPPORTED_TOKEN_REGIONS,
    compute_layer_token_projections,
    load_hf_model_and_tokenizer,
    summarize_token_regions,
)
from poc_stage6.prefixing import PrefixLength, TokenPrefix, make_token_prefixes, parse_prefix_lengths


DEFAULT_MAX_LENGTH = 512
DEFAULT_LAYERS = "-1"
DEFAULT_PREFIX_LENGTHS = "16,32,64,128,full"
DEFAULT_TOKEN_REGION = "final_token"
PROGRESS_INTERVAL = 1


@dataclass(frozen=True)
class ComputeConfig:
    input_jsonl: Path
    direction_path: Path
    model_name_or_path: str
    output_jsonl: Path
    summary_json: Path
    max_examples: int | None
    max_length: int
    prefix_lengths: str
    layers: str | None
    token_region: str
    device: str | None
    dtype: str | None
    condition: str | None
    run_name: str
    overwrite: bool
    error_jsonl: Path | None
    store_text_hashes: bool


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Expected a positive integer.")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 6 token-level delayed detection. Writes compact prefix projection "
            "summaries only; never writes raw prompt text, response text, token strings, "
            "logits, or hidden states."
        )
    )
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--direction-path", required=True)
    parser.add_argument("--model-name-or-path", required=True)
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--max-examples", type=_positive_int)
    parser.add_argument("--max-length", type=_positive_int, default=DEFAULT_MAX_LENGTH)
    parser.add_argument("--prefix-lengths", default=DEFAULT_PREFIX_LENGTHS)
    parser.add_argument(
        "--layers",
        default=DEFAULT_LAYERS,
        help=(
            "HuggingFace hidden-state indices to project. 0 is embeddings, 1 is the first "
            "transformer block output, -1 is the final hidden state. Use comma lists like "
            "'0,-1' or '1,12,-1'. Use 'all' to project every hidden-state index."
        ),
    )
    parser.add_argument(
        "--token-region",
        default=DEFAULT_TOKEN_REGION,
        help=f"Comma-separated token regions. Supported: {','.join(sorted(SUPPORTED_TOKEN_REGIONS))}.",
    )
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", default="auto")
    parser.add_argument(
        "--condition",
        help="Default condition label for input rows that do not already contain a condition.",
    )
    parser.add_argument("--run-name", default="stage6_token_delay")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--error-jsonl")
    parser.add_argument(
        "--store-text-hashes",
        action="store_true",
        help="Store SHA256 hashes of prompt text only; never stores raw text.",
    )
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
        prefix_lengths=str(args.prefix_lengths),
        layers=args.layers,
        token_region=str(args.token_region),
        device=args.device,
        dtype=args.dtype,
        condition=args.condition,
        run_name=str(args.run_name),
        overwrite=bool(args.overwrite),
        error_jsonl=Path(args.error_jsonl) if args.error_jsonl else None,
        store_text_hashes=bool(args.store_text_hashes),
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


def _json_safe_config(config: ComputeConfig) -> dict[str, Any]:
    return _json_safe(asdict(config))


def _log(message: str, **fields: Any) -> None:
    suffix = ""
    if fields:
        safe_fields = " ".join(f"{key}={_json_safe(value)}" for key, value in fields.items())
        suffix = f" {safe_fields}"
    print(f"[{_utc_now()}] [stage6] {message}{suffix}", file=sys.stderr, flush=True)


def _parse_token_regions(value: str | None) -> list[str]:
    if value is None or not value.strip():
        return [DEFAULT_TOKEN_REGION]
    regions = [item.strip() for item in value.split(",") if item.strip()]
    if not regions:
        raise ValueError("At least one token region is required.")
    invalid = [region for region in regions if region not in SUPPORTED_TOKEN_REGIONS]
    if invalid:
        raise ValueError(
            f"Unsupported token region(s): {invalid}. Supported regions: {sorted(SUPPORTED_TOKEN_REGIONS)}."
        )
    return regions


def _parse_layers_spec(value: str | None) -> list[int] | str:
    if value is None or not value.strip() or value.strip().lower() == "auto":
        return [-1]
    normalized = value.strip().lower()
    if normalized == "all":
        return "all"
    layers: list[int] = []
    for item in value.split(","):
        stripped = item.strip()
        if not stripped:
            continue
        try:
            layers.append(int(stripped))
        except ValueError as exc:
            raise ValueError(
                "layers must be 'all', 'auto', or comma-separated hidden-state indices "
                "such as '-1', '0,-1', or '1,12,-1'."
            ) from exc
    if not layers:
        raise ValueError("At least one hidden-state index is required.")
    return layers


def _resolve_layers_for_hidden_states(layers_spec: list[int] | str, num_hidden_states: int) -> list[int] | None:
    if layers_spec == "all":
        return None
    resolved: list[int] = []
    for layer in layers_spec:
        index = layer if layer >= 0 else num_hidden_states + layer
        if index < 0 or index >= num_hidden_states:
            raise ValueError(
                f"Hidden-state index {layer} resolves outside the returned hidden_states tuple "
                f"of length {num_hidden_states}."
            )
        resolved.append(index)
    return resolved


def _direction_dimension(vector: Any) -> int:
    shape = getattr(vector, "shape", None)
    if shape is not None:
        if len(shape) != 1:
            raise ValueError(f"Refusal direction must be 1D after loading, got shape {tuple(shape)}.")
        return int(shape[0])
    return len(vector)


def _model_hidden_size(model: Any) -> int:
    hidden_size = getattr(getattr(model, "config", None), "hidden_size", None)
    if hidden_size is not None:
        return int(hidden_size)
    try:
        return int(model.get_input_embeddings().weight.shape[-1])
    except Exception as exc:
        raise RuntimeError("Unable to infer model hidden size from config or input embeddings.") from exc


def _validate_direction_matches_model(direction: Any, model: Any, *, model_name_or_path: str) -> None:
    direction_dim = _direction_dimension(direction)
    hidden_size = _model_hidden_size(model)
    if direction_dim != hidden_size:
        raise ValueError(
            "Refusal direction dimension does not match model hidden size: "
            f"direction dimension is {direction_dim}, model hidden size is {hidden_size} "
            f"for {model_name_or_path!r}."
        )


def _model_input_device(model: Any) -> Any:
    try:
        embedding = model.get_input_embeddings()
        return embedding.weight.device
    except Exception:
        try:
            return next(model.parameters()).device
        except StopIteration as exc:
            raise RuntimeError("Unable to infer model device from parameters or embeddings.") from exc


def _compute_hidden_states_from_inputs(model: Any, model_inputs: dict[str, Any]) -> tuple[Any, ...]:
    import torch

    input_device = _model_input_device(model)
    moved_inputs = {
        key: value.to(input_device) if hasattr(value, "to") else value
        for key, value in model_inputs.items()
    }
    with torch.no_grad():
        outputs = model(**moved_inputs, output_hidden_states=True)
    hidden_states = getattr(outputs, "hidden_states", None)
    if hidden_states is None:
        raise RuntimeError("Model output did not include hidden_states.")
    if not isinstance(hidden_states, tuple):
        hidden_states = tuple(hidden_states)
    if not hidden_states:
        raise RuntimeError("Model returned an empty hidden_states tuple.")
    return hidden_states


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _check_output_paths(config: ComputeConfig) -> None:
    paths = [config.output_jsonl, config.summary_json]
    if config.error_jsonl is not None:
        paths.append(config.error_jsonl)
    existing = [path for path in paths if path.exists()]
    if existing and not config.overwrite:
        formatted = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(f"Output file(s) already exist. Use --overwrite to replace them:\n{formatted}")


def _tmp_path(path: Path) -> Path:
    return path.with_name(path.name + ".tmp")


def _open_temp_jsonl(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(path)
    return tmp_path, tmp_path.open("w", encoding="utf-8")


def _replace_temp(tmp_path: Path, final_path: Path) -> None:
    final_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.replace(final_path)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _tmp_path(path)
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    _replace_temp(tmp_path, path)


def _write_jsonl_row(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(_json_safe(row), ensure_ascii=False) + "\n")


def _base_row(
    *,
    config: ComputeConfig,
    example: Stage5Example,
    prefix: TokenPrefix,
    hidden_state_index: int,
    token_region: str,
    stats: dict[str, float | int],
) -> dict[str, Any]:
    row = {
        "stage": 6,
        "run_name": config.run_name,
        "example_id": example.example_id,
        "goal_index": example.goal_index,
        "condition": example.condition,
        "model_name_or_path": config.model_name_or_path,
        "direction_path": str(config.direction_path),
        "hidden_state_index": hidden_state_index,
        "prefix_length": prefix.prefix_length,
        "prefix_kind": prefix.prefix_kind,
        "full_prompt_num_tokens": prefix.full_prompt_num_tokens,
        "token_region": token_region,
        "num_tokens": prefix.num_tokens,
        "token_region_num_tokens": stats["num_tokens"],
        "projection_mean": stats["mean"],
        "projection_max": stats["max"],
        "projection_min": stats["min"],
        "projection_final": stats["final"],
        "projection_abs_mean": stats["abs_mean"],
        "is_success": example.is_success,
        "judge_score": example.judge_score,
        "strongreject_score": example.strongreject_score,
    }
    if config.store_text_hashes:
        row["prompt_sha256"] = _sha256_text(example.prompt_text)
    return row


def _error_row(
    config: ComputeConfig,
    example: Stage5Example,
    exc: Exception,
    *,
    prefix_length: PrefixLength | None = None,
    prefix_kind: str | None = None,
) -> dict[str, Any]:
    row = {
        "stage": 6,
        "run_name": config.run_name,
        "example_id": example.example_id,
        "goal_index": example.goal_index,
        "condition": example.condition,
        "model_name_or_path": config.model_name_or_path,
        "direction_path": str(config.direction_path),
        "prefix_length": prefix_length,
        "prefix_kind": prefix_kind,
        "error_type": type(exc).__name__,
        "error_message": "token-prefix projection failed for this example; raw text omitted",
    }
    if config.store_text_hashes:
        row["prompt_sha256"] = _sha256_text(example.prompt_text)
    return row


def _process_prefix(
    *,
    model: Any,
    tokenizer: Any,
    direction: Any,
    config: ComputeConfig,
    example: Stage5Example,
    prefix: TokenPrefix,
    layers_spec: list[int] | str,
    token_regions: list[str],
    output_handle: Any,
) -> tuple[int, list[int]]:
    hidden_states = _compute_hidden_states_from_inputs(model, prefix.model_inputs)
    selected_layers = _resolve_layers_for_hidden_states(layers_spec, len(hidden_states))
    projections = compute_layer_token_projections(hidden_states, direction, layers=selected_layers)
    region_summary = summarize_token_regions(
        projections,
        prefix.model_inputs["input_ids"],
        tokenizer,
        token_regions,
    )

    rows_written = 0
    hidden_state_indices: list[int] = []
    for hidden_state_index, layer_summary in region_summary.items():
        hidden_state_indices.append(int(hidden_state_index))
        for token_region, stats in layer_summary.items():
            _write_jsonl_row(
                output_handle,
                _base_row(
                    config=config,
                    example=example,
                    prefix=prefix,
                    hidden_state_index=int(hidden_state_index),
                    token_region=token_region,
                    stats=stats,
                ),
            )
            rows_written += 1
    return rows_written, hidden_state_indices


def run_token_delay(config: ComputeConfig) -> dict[str, Any]:
    _check_output_paths(config)
    start_time = _utc_now()
    token_regions = _parse_token_regions(config.token_region)
    prefix_lengths = parse_prefix_lengths(config.prefix_lengths)
    layers_spec = _parse_layers_spec(config.layers)

    loaded = load_stage5_examples_with_metadata(
        config.input_jsonl,
        max_examples=config.max_examples,
        default_condition=config.condition,
    )
    if loaded.num_examples == 0:
        raise ValueError("No examples were loaded from the input JSONL.")

    _log("loading refusal direction", path=config.direction_path)
    refusal_direction = load_refusal_direction(config.direction_path, device=config.device, dtype=config.dtype)
    _log("loading model and tokenizer", model=config.model_name_or_path)
    model, tokenizer = load_hf_model_and_tokenizer(
        config.model_name_or_path,
        device=config.device,
        dtype=config.dtype,
    )
    _validate_direction_matches_model(
        refusal_direction.vector,
        model,
        model_name_or_path=config.model_name_or_path,
    )

    output_tmp, output_handle = _open_temp_jsonl(config.output_jsonl)
    error_tmp = None
    error_handle = None
    if config.error_jsonl is not None:
        error_tmp, error_handle = _open_temp_jsonl(config.error_jsonl)

    processed_examples = 0
    failed_examples = 0
    failed_prefixes = 0
    rows_written = 0
    observed_hidden_state_indices: set[int] = set()

    try:
        for example_index, example in enumerate(loaded.examples, start=1):
            example_failed = False
            example_succeeded = False
            try:
                prefixes = make_token_prefixes(
                    tokenizer,
                    example.prompt_text,
                    prefix_lengths,
                    max_length=config.max_length,
                )
            except Exception as exc:
                example_failed = True
                failed_prefixes += len(prefix_lengths)
                if error_handle is not None:
                    _write_jsonl_row(error_handle, _error_row(config, example, exc))
                _log(
                    "example prefixing failed",
                    example_index=example_index,
                    example_id=example.example_id,
                    error_type=type(exc).__name__,
                )
                prefixes = []

            for prefix in prefixes:
                try:
                    prefix_rows, prefix_indices = _process_prefix(
                        model=model,
                        tokenizer=tokenizer,
                        direction=refusal_direction.vector,
                        config=config,
                        example=example,
                        prefix=prefix,
                        layers_spec=layers_spec,
                        token_regions=token_regions,
                        output_handle=output_handle,
                    )
                    rows_written += prefix_rows
                    observed_hidden_state_indices.update(prefix_indices)
                    example_succeeded = True
                except Exception as exc:
                    example_failed = True
                    failed_prefixes += 1
                    if error_handle is not None:
                        _write_jsonl_row(
                            error_handle,
                            _error_row(
                                config,
                                example,
                                exc,
                                prefix_length=prefix.prefix_length,
                                prefix_kind=prefix.prefix_kind,
                            ),
                        )
                    _log(
                        "example prefix failed",
                        example_index=example_index,
                        example_id=example.example_id,
                        prefix_length=prefix.prefix_length,
                        error_type=type(exc).__name__,
                    )

            if example_succeeded:
                processed_examples += 1
            if example_failed:
                failed_examples += 1
            if example_index % PROGRESS_INTERVAL == 0:
                _log(
                    "processed examples",
                    processed=example_index,
                    total=loaded.num_examples,
                    rows_written=rows_written,
                    failed_examples=failed_examples,
                )
    finally:
        output_handle.close()
        if error_handle is not None:
            error_handle.close()

    _replace_temp(output_tmp, config.output_jsonl)
    if config.error_jsonl is not None and error_tmp is not None:
        _replace_temp(error_tmp, config.error_jsonl)

    summary = {
        "stage": 6,
        "run_name": config.run_name,
        "input_jsonl": str(config.input_jsonl),
        "direction_path": str(config.direction_path),
        "model_name_or_path": config.model_name_or_path,
        "output_jsonl": str(config.output_jsonl),
        "summary_json": str(config.summary_json),
        "error_jsonl": str(config.error_jsonl) if config.error_jsonl is not None else None,
        "loaded_examples": loaded.num_examples,
        "processed_examples": processed_examples,
        "failed_examples": failed_examples,
        "failed_prefixes": failed_prefixes,
        "rows_written": rows_written,
        "skipped_contentless_rows": loaded.skipped_contentless_rows,
        "detected_condition_values": loaded.condition_values,
        "layers_request": config.layers or DEFAULT_LAYERS,
        "selected_hidden_state_indices": sorted(observed_hidden_state_indices)
        if layers_spec != "all"
        else "all",
        "prefix_lengths": prefix_lengths,
        "token_regions": token_regions,
        "max_length": config.max_length,
        "store_text_hashes": config.store_text_hashes,
        "config": _json_safe_config(config),
        "start_time": start_time,
        "end_time": _utc_now(),
    }
    _atomic_write_json(config.summary_json, summary)
    _log(
        "completed Stage 6 token delay",
        processed_examples=processed_examples,
        failed_examples=failed_examples,
        rows_written=rows_written,
        output_jsonl=config.output_jsonl,
        summary_json=config.summary_json,
    )
    return summary


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = validate_config(args)
        summary = run_token_delay(config)
        print(json.dumps(_json_safe(summary), indent=2, ensure_ascii=False))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

