from __future__ import annotations

"""
Stage 4A1-endofresponse: extract refusal direction at EOS (end of response) position.

DIFFERENCE FROM extract_refusal_direction_behavioral.py (Stage 4A1-behavioral):
  behavioral:      position = </think> token (after reasoning, BEFORE answer generation)
  endofresponse:   position = EOS token (<|im_end|>) = AFTER the full answer is generated

WHY THIS MATTERS:
  This completes the temporal picture of refusal representation:
    startofthink (<think>)  → DiM only at L0/L1/L2 (AUC=0.731)
    endofthink   (</think>) → DiM at L26/L29        (AUC=0.750)
    endofresponse (EOS)     → ??? does signal strengthen or stay flat?

  If endofresponse AUC > endofthink AUC: the model further encodes its compliance state
  while generating the answer, even after the decision was made at </think>.
  If AUC ≈ same: the decision is fully encoded at </think> and generating the answer
  doesn't change the representation further.

  Also scientifically interesting: does the refusal direction at EOS (when the model has
  "seen" the entire answer it just wrote) differ geometrically from the endofthink direction?

INPUT:
  --stage6-input: directory of Stage 6 CoT-hijacking trace artifacts. Each artifact has:
    - full_prompt_plus_generation_token_ids: full sequence including the EOS token
    - generation_finish_reason: "eos_token" (only these are usable — "max_new_tokens" skipped)
    - source_judge.judge_score / qwen_run_success for group splitting

METHOD:
  1. Load Stage 6 artifacts; keep only those with generation_finish_reason=="eos_token".
  2. Split into "complied" vs "refused" using qwen_run_success (or judge_score).
  3. For each trace, EOS position = len(full_prompt_plus_generation_token_ids) - 1.
  4. Run a forward pass on the full sequence.
  5. Capture residual stream activation at EOS for every layer.
  6. Compute DiM: mean(complied_at_eos) − mean(refused_at_eos) per layer.

OUTPUT SHAPE: candidate_directions.pt is [1, n_layers, d_model]
  (one "position" = endofresponse; same schema as behavioral/endofthink)

OUTPUTS (to --output-dir, default: outputs/stage4/qwen3-14b/refusal_direction_endofresponse/):
  candidate_directions.pt        [1, n_layers, d_model]
  candidate_metadata.json        contrast set info, skip statistics
  projection_diagnostics.json    per-layer standardized separation scores
  direction.pt                   provisional direction (run Stage 4A2 to validate)
  selected_direction.json        provisional selection metadata
  extraction_metrics.json        full run summary
  group_summary.json             how many complied/refused examples were found and used
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch

# Reuse position schema constants from endofthink (position_index=0, position_value=0)
from poc_stage4.extract_refusal_direction_endofthink import (
    ENDOFTHINK_POSITION_VALUE,
    OUTPUT_FILENAMES,
    _check_outputs,
)

# Reuse grouping + artifact loading from behavioral
from poc_stage4.extract_refusal_direction_behavioral import (
    GROUP_BY_JUDGE_SCORE,
    GROUP_BY_QWEN_RUN_SUCCESS,
    DEFAULT_GROUP_BY,
    _collect_trace_files,
    _read_artifact,
    group_artifacts,
)

STAGE_NAME = "stage4a1_endofresponse"
ENDOFRESPONSE_POSITION_LABEL = "endofresponse"
ENDOFRESPONSE_POSITION_VALUE = ENDOFTHINK_POSITION_VALUE  # schema: position_index=0

# Default max sequence length for the forward pass — skip traces longer than this
# to avoid OOM. 32768 prompt+gen tokens fit on most A100 80GB nodes for 14B model.
DEFAULT_MAX_SEQ_LEN = 30000


# ---------------------------------------------------------------------------
# Core capture function
# ---------------------------------------------------------------------------

def capture_endofresponse_activations_from_artifacts(
    model_base: Any,
    artifacts: list[dict[str, Any]],
    *,
    group_label: str,
    progress_enabled: bool,
    max_seq_len: int = DEFAULT_MAX_SEQ_LEN,
) -> tuple[torch.Tensor, list[int | None], list[str]]:
    """
    For each artifact:
      1. Use full_prompt_plus_generation_token_ids (already generated in Stage 6).
      2. EOS position = len(full_ids) - 1 (always the last token).
      3. Run a forward pass on the full sequence.
      4. Capture activations at EOS for each layer.

    Only processes artifacts with generation_finish_reason == "eos_token".
    Skips artifacts whose sequence length exceeds max_seq_len.

    Returns:
      activations: [n_valid, 1, n_layers, d_model] float32 on CPU
      eos_positions: per-artifact EOS absolute position (None if skipped)
      skipped_sources: source paths of skipped artifacts
    """
    from poc_stage4.run_state import log_progress, progress_iter

    layers = model_base.layers
    n_layers = model_base.num_layers
    d_model = model_base.hidden_size

    try:
        input_device = model_base.model.get_input_embeddings().weight.device
    except Exception:
        input_device = next(model_base.model.parameters()).device

    all_valid: list[torch.Tensor] = []
    eos_positions: list[int | None] = []
    skipped_sources: list[str] = []

    for artifact in progress_iter(
        artifacts,
        total=len(artifacts),
        desc=f"endofresponse [{group_label}]",
        enabled=progress_enabled,
    ):
        source_path = artifact.get("_source_path", "unknown")

        # Only use complete (EOS-terminated) traces
        finish_reason = artifact.get("generation_finish_reason")
        if finish_reason != "eos_token":
            log_progress(
                STAGE_NAME, f"Skipping: finish_reason={finish_reason!r} (not eos_token)",
                enabled=progress_enabled, source=source_path,
            )
            eos_positions.append(None)
            skipped_sources.append(source_path)
            continue

        full_ids = artifact.get("full_prompt_plus_generation_token_ids")
        if not full_ids:
            log_progress(STAGE_NAME, "Skipping: missing token IDs", enabled=progress_enabled, source=source_path)
            eos_positions.append(None)
            skipped_sources.append(source_path)
            continue

        if len(full_ids) > max_seq_len:
            log_progress(
                STAGE_NAME, f"Skipping: seq_len={len(full_ids)} > max_seq_len={max_seq_len}",
                enabled=progress_enabled, source=source_path,
            )
            eos_positions.append(None)
            skipped_sources.append(source_path)
            continue

        eos_pos = len(full_ids) - 1

        log_progress(
            STAGE_NAME,
            "Capturing",
            enabled=progress_enabled,
            group=group_label,
            eos_pos=eos_pos,
            seq_len=len(full_ids),
        )

        full_tensor = torch.tensor(full_ids, dtype=torch.long).unsqueeze(0)

        layer_cache = torch.zeros((n_layers, d_model), dtype=torch.float32, device="cpu")
        hooks = []

        def _make_hook(li: int, pos: int = eos_pos) -> Any:
            def _hook(module: Any, hook_input: Any) -> None:
                act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
                layer_cache[li] = act[0, pos].detach().float().cpu()
            return _hook

        for li, layer in enumerate(layers):
            hooks.append(layer.register_forward_pre_hook(_make_hook(li)))

        try:
            with torch.no_grad():
                model_base.base_model(input_ids=full_tensor.to(input_device), use_cache=False)
        finally:
            for h in hooks:
                h.remove()

        all_valid.append(layer_cache.unsqueeze(0).clone())  # [1, n_layers, d_model]
        eos_positions.append(eos_pos)

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not all_valid:
        raise RuntimeError(
            f"No {group_label} artifacts yielded a valid EOS activation. "
            "Check that Stage 6 traces include eos_token finish reasons."
        )

    return torch.stack(all_valid, dim=0), eos_positions, skipped_sources


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def run_extraction_endofresponse(
    *,
    model_name: str,
    model_family: str,
    stage6_input: Path,
    output_dir: Path,
    group_by: str = DEFAULT_GROUP_BY,
    max_per_group: int | None,
    max_seq_len: int = DEFAULT_MAX_SEQ_LEN,
    dry_run: bool,
    overwrite: bool,
    direction_normalization: str,
    no_progress: bool,
) -> dict[str, Any]:
    from poc_stage4.candidate_directions import generate_candidate_directions
    from poc_stage4.model_family_utils import load_model_by_family
    from poc_stage4.projection_diagnostics import compute_projection_diagnostics, summarize_diagnostics
    from poc_stage4.run_state import log_progress
    from poc_stage4.schemas import (
        PROVISIONAL_SELECTION,
        PROVISIONAL_SELECTION_CRITERION,
        STAGE4A1_ARTIFACT_VERSION,
        utc_now,
        write_json,
    )

    progress_enabled = not no_progress
    _check_outputs(output_dir, overwrite=overwrite)
    output_dir.mkdir(parents=True, exist_ok=True)

    log_progress(STAGE_NAME, "Starting end-of-response contrast direction extraction", enabled=progress_enabled)

    if not stage6_input.exists():
        raise FileNotFoundError(f"--stage6-input does not exist: {stage6_input}")
    trace_files = _collect_trace_files(stage6_input)
    if not trace_files:
        raise ValueError(f"No Stage 6 trace JSON files in: {stage6_input}")
    log_progress(STAGE_NAME, f"Found {len(trace_files)} trace files", enabled=progress_enabled)

    effective_max = 4 if dry_run else max_per_group
    complied_artifacts, refused_artifacts, group_summary = group_artifacts(
        trace_files,
        group_by=group_by,
        max_per_group=effective_max,
        progress_enabled=progress_enabled,
    )

    if not complied_artifacts:
        raise RuntimeError(f"No 'complied' examples found (group_by={group_by!r}).")
    if not refused_artifacts:
        raise RuntimeError(f"No 'refused' examples found (group_by={group_by!r}).")

    write_json(output_dir / "group_summary.json", group_summary)

    log_progress(STAGE_NAME, "Loading model", enabled=progress_enabled,
                 model=model_name, model_family=model_family)
    model_base = load_model_by_family(model_name, model_family)

    # 75/25 train/val split
    import random
    rng = random.Random(42)
    n_complied = len(complied_artifacts)
    n_refused = len(refused_artifacts)
    val_frac = 0.25
    n_cv = max(1, int(round(n_complied * val_frac)))
    n_rv = max(1, int(round(n_refused * val_frac)))

    complied_shuf = list(complied_artifacts)
    refused_shuf = list(refused_artifacts)
    rng.shuffle(complied_shuf)
    rng.shuffle(refused_shuf)

    complied_train = complied_shuf[n_cv:]
    complied_val   = complied_shuf[:n_cv]
    refused_train  = refused_shuf[n_rv:]
    refused_val    = refused_shuf[:n_rv]

    log_progress(STAGE_NAME, "Split into train/val", enabled=progress_enabled,
                 complied_train=len(complied_train), complied_val=len(complied_val),
                 refused_train=len(refused_train), refused_val=len(refused_val))

    log_progress(STAGE_NAME, "Capturing complied train activations", enabled=progress_enabled)
    complied_train_acts, _, complied_skipped = capture_endofresponse_activations_from_artifacts(
        model_base, complied_train,
        group_label="complied_train",
        progress_enabled=progress_enabled,
        max_seq_len=max_seq_len,
    )

    log_progress(STAGE_NAME, "Capturing refused train activations", enabled=progress_enabled)
    refused_train_acts, _, refused_skipped = capture_endofresponse_activations_from_artifacts(
        model_base, refused_train,
        group_label="refused_train",
        progress_enabled=progress_enabled,
        max_seq_len=max_seq_len,
    )

    n_train = min(complied_train_acts.shape[0], refused_train_acts.shape[0])
    complied_train_acts = complied_train_acts[:n_train]
    refused_train_acts  = refused_train_acts[:n_train]

    log_progress(STAGE_NAME, "Computing end-of-response DiM", enabled=progress_enabled, n_train=n_train)
    candidate_directions = generate_candidate_directions(
        complied_train_acts,
        refused_train_acts,
        direction_normalization=direction_normalization,
    )
    torch.save(candidate_directions.cpu(), output_dir / "candidate_directions.pt")
    log_progress(STAGE_NAME, "Saved candidate_directions.pt", enabled=progress_enabled,
                 shape=list(candidate_directions.shape))

    log_progress(STAGE_NAME, "Capturing complied val activations", enabled=progress_enabled)
    complied_val_acts, _, _ = capture_endofresponse_activations_from_artifacts(
        model_base, complied_val,
        group_label="complied_val",
        progress_enabled=progress_enabled,
        max_seq_len=max_seq_len,
    )

    log_progress(STAGE_NAME, "Capturing refused val activations", enabled=progress_enabled)
    refused_val_acts, _, _ = capture_endofresponse_activations_from_artifacts(
        model_base, refused_val,
        group_label="refused_val",
        progress_enabled=progress_enabled,
        max_seq_len=max_seq_len,
    )

    n_val = min(complied_val_acts.shape[0], refused_val_acts.shape[0])
    complied_val_acts = complied_val_acts[:n_val]
    refused_val_acts  = refused_val_acts[:n_val]

    log_progress(STAGE_NAME, "Computing projection diagnostics", enabled=progress_enabled)
    diagnostic_rows, selection = compute_projection_diagnostics(
        candidate_directions,
        complied_val_acts,
        refused_val_acts,
        positions=[ENDOFRESPONSE_POSITION_VALUE],
    )

    timestamp_utc = utc_now()
    base_metadata: dict[str, Any] = {
        "artifact_version": STAGE4A1_ARTIFACT_VERSION,
        "stage": "stage4a1_endofresponse_candidate_refusal_direction_extraction",
        "source_variant": "extract_refusal_direction_endofresponse",
        "timestamp_utc": timestamp_utc,
        "model_name": model_name,
        "model_family": model_family,
        "contrast_set": "endofresponse_complied_vs_refused",
        "group_by_criterion": group_by,
        "contrast_set_notes": (
            "DiM = mean(complied_at_eos) − mean(refused_at_eos). "
            "EOS position = last token of full_prompt_plus_generation_token_ids. "
            "Only eos_token finish_reason traces are used (max_new_tokens traces skipped). "
            f"max_seq_len filter: {max_seq_len} tokens. "
            f"Grouping criterion: {group_by!r}."
        ),
        "stage6_input": str(stage6_input),
        "max_seq_len": max_seq_len,
        "num_complied_train": n_train,
        "num_refused_train": n_train,
        "num_complied_val": n_val,
        "num_refused_val": n_val,
        "num_complied_train_skipped": len(complied_skipped),
        "num_refused_train_skipped": len(refused_skipped),
        "positions": [ENDOFRESPONSE_POSITION_VALUE],
        "token_position_semantics": "eos_token_behavioral_contrast",
        "layers": list(range(model_base.num_layers)),
        "num_layers": model_base.num_layers,
        "hidden_size": model_base.hidden_size,
        "candidate_tensor_shape": list(candidate_directions.shape),
        "direction_normalization": direction_normalization,
        "dry_run": dry_run,
        "device_summary": model_base.device_summary,
        **group_summary,
    }

    write_json(output_dir / "candidate_metadata.json", base_metadata)
    write_json(output_dir / "projection_diagnostics.json", {
        **base_metadata,
        "selection_status": PROVISIONAL_SELECTION,
        "selection_criterion": PROVISIONAL_SELECTION_CRITERION,
        "diagnostic_summary": summarize_diagnostics(diagnostic_rows),
        "diagnostics": diagnostic_rows,
    })

    selected_direction = candidate_directions[
        selection.selected_position_index,
        selection.selected_layer,
    ].detach().cpu()
    direction_path = output_dir / "direction.pt"
    torch.save(selected_direction, direction_path)

    selected_metadata: dict[str, Any] = {
        **base_metadata,
        "selection_status": PROVISIONAL_SELECTION,
        "selection_criterion": PROVISIONAL_SELECTION_CRITERION,
        "selected_position_index": selection.selected_position_index,
        "selected_position": ENDOFRESPONSE_POSITION_LABEL,
        "selected_layer": selection.selected_layer,
        "selected_score": selection.selected_score,
        "selected_complied_projection_mean": selection.selected_harmful_projection_mean,
        "selected_refused_projection_mean": selection.selected_harmless_projection_mean,
        "direction_norm": float(selected_direction.norm().item()),
        "direction_path": str(direction_path),
        "scientific_use_warning": (
            "Provisional: selected by projection diagnostics only. "
            "Run Stage 4A2 intervention-based selection before scientific use."
        ),
    }
    write_json(output_dir / "selected_direction.json", selected_metadata)

    metrics: dict[str, Any] = {
        **base_metadata,
        "outputs": {fn: str(output_dir / fn) for fn in OUTPUT_FILENAMES},
        "selection": selected_metadata,
        "diagnostic_summary": summarize_diagnostics(diagnostic_rows),
    }
    write_json(output_dir / "extraction_metrics.json", metrics)

    log_progress(
        STAGE_NAME, "Finished end-of-response extraction",
        enabled=progress_enabled,
        selected_layer=selection.selected_layer,
        score=round(selection.selected_score, 4),
    )
    return metrics


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 4A1-endofresponse: extract refusal direction at EOS token "
            "using behavioral contrast (complied vs. refused Stage 6 examples). "
            "Captures activations after the FULL answer is generated."
        )
    )
    parser.add_argument("--stage6-input", required=True,
                        help="Directory of Stage 6 trace JSON artifacts.")
    parser.add_argument(
        "--model-family", default="qwen3", choices=["qwen3", "gemma4"],
        help="Model family. Default: qwen3.",
    )
    parser.add_argument("--output-dir", default=None,
                        help="Output directory. Default: outputs/stage4/<slug>/refusal_direction_endofresponse/")
    parser.add_argument("--model-name", default=None,
                        help="HF model name or path. Default: inferred from --model-family.")
    parser.add_argument(
        "--group-by", default=DEFAULT_GROUP_BY,
        choices=[GROUP_BY_QWEN_RUN_SUCCESS, GROUP_BY_JUDGE_SCORE],
    )
    parser.add_argument("--max-per-group", type=int, default=None)
    parser.add_argument(
        "--max-seq-len", type=int, default=DEFAULT_MAX_SEQ_LEN,
        help=f"Skip traces longer than this many tokens. Default: {DEFAULT_MAX_SEQ_LEN}.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--direction-normalization", choices=("unit", "raw"), default="unit")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-progress", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY, DEFAULT_MODEL_SLUG_BY_FAMILY
    model_family: str = args.model_family
    if args.model_name is None:
        args.model_name = DEFAULT_MODEL_BY_FAMILY[model_family]
    if args.output_dir is None:
        slug = DEFAULT_MODEL_SLUG_BY_FAMILY[model_family]
        args.output_dir = f"outputs/stage4/{slug}/refusal_direction_endofresponse"

    try:
        metrics = run_extraction_endofresponse(
            model_name=args.model_name,
            model_family=model_family,
            stage6_input=Path(args.stage6_input),
            output_dir=Path(args.output_dir),
            group_by=args.group_by,
            max_per_group=args.max_per_group,
            max_seq_len=args.max_seq_len,
            dry_run=bool(args.dry_run),
            overwrite=bool(args.overwrite),
            direction_normalization=args.direction_normalization,
            no_progress=bool(args.no_progress),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out = Path(args.output_dir)
    print(f"Wrote Stage 4A1-endofresponse artifacts to: {out}")
    print("direction.pt is provisional — run Stage 4A2 to validate.")
    print(f"Selected provisional layer: {metrics['selection']['selected_layer']}")
    print(f"Score (standardized separation): {metrics['selection']['selected_score']:.4f}")
    print(f"Complied examples used (train): {metrics.get('num_complied_train', '?')}")
    print(f"Refused examples used (train):  {metrics.get('num_refused_train', '?')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
