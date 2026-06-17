from __future__ import annotations

"""
Stage 4A1-behavioral: extract refusal direction from behavioral outcomes at </think> position.

DIFFERENCE FROM extract_refusal_direction.py (Stage 4A1 / EOI / input-label contrast):
  Stage 4A1: contrast = harmful (input label) vs. harmless (input label)
             position = EOI (prompt end, before generation)
  This script: contrast = complied (attack succeeded, judge_score=10) vs.
                          refused (model refused, judge_score=1)
               position = </think> token (after full reasoning, before answer)

WHY THIS CONTRAST:
  The Arditi et al. direction distinguishes "this input is harmful" at the instruction end.
  The behavioral direction distinguishes "the model is about to comply" from "the model is
  about to refuse" AT THE MOMENT AFTER DELIBERATION (</think>). This is the direction that
  directly encodes the attack's effect: why did the model comply when it normally would refuse?

INPUT:
  --stage6-input: directory of Stage 6 CoT-hijacking trace artifacts. Each artifact has:
    - full_prompt_plus_generation_token_ids: full sequence token IDs
    - source_judge.judge_score: 10 (complied) or 1 (refused)
    - token_table: per-token metadata (used to find </think> position)

METHOD:
  1. Load Stage 6 artifacts and split into "complied" (judge_score=10) vs. "refused" (judge_score=1).
  2. For each trace, find the </think> token in full_prompt_plus_generation_token_ids.
  3. Run a forward pass on the sequence up to and including </think>.
  4. Capture residual stream activation at the </think> position for every layer.
  5. Compute DiM: mean(complied_at_endthink) − mean(refused_at_endthink) per layer.

OUTPUT SHAPE: candidate_directions.pt is [1, n_layers, d_model]
  (one "position" = endofthink; same schema as extract_refusal_direction_endofthink.py)

OUTPUTS (to --output-dir, default: outputs/stage4/qwen3-14b/refusal_direction_behavioral/):
  candidate_directions.pt        [1, n_layers, d_model]
  candidate_metadata.json        contrast set info, skip statistics
  projection_diagnostics.json    per-layer standardized separation scores
  direction.pt                   provisional direction (run Stage 4A2 to validate)
  selected_direction.json        provisional selection metadata
  extraction_metrics.json        full run summary
  group_summary.json             how many complied/refused examples were found and used
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch

from poc_stage4.extract_refusal_direction_endofthink import (
    ENDOFTHINK_POSITION_LABEL,
    ENDOFTHINK_POSITION_VALUE,
    OUTPUT_FILENAMES,
    _check_outputs,
    find_endthink_position,
)
STAGE_NAME = "stage4a1_behavioral"

# judge_score thresholds for grouping
COMPLIED_JUDGE_SCORE = 10
REFUSED_JUDGE_SCORE = 1


# ---------------------------------------------------------------------------
# Stage 6 artifact loading and grouping
# ---------------------------------------------------------------------------

def _read_artifact(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _collect_trace_files(stage6_input: Path) -> list[Path]:
    if stage6_input.is_file():
        return [stage6_input]
    files = sorted(stage6_input.glob("*.json"))
    return [f for f in files if not f.name.startswith("batch_summary")]


def _judge_score(artifact: dict[str, Any]) -> int | None:
    """Extract judge_score from a Stage 6 artifact."""
    sj = artifact.get("source_judge") or {}
    score = sj.get("judge_score")
    if score is None:
        # Fallback: check top-level
        score = artifact.get("judge_score")
    if score is None:
        return None
    try:
        return int(score)
    except (TypeError, ValueError):
        return None


def group_artifacts(
    trace_files: list[Path],
    *,
    max_per_group: int | None = None,
    progress_enabled: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """
    Load Stage 6 artifacts and group into 'complied' (score=10) and 'refused' (score=1).

    Returns:
        complied_artifacts: list of artifact dicts with judge_score == 10
        refused_artifacts: list of artifact dicts with judge_score == 1
        group_summary: counts and source info
    """
    from poc_stage4.run_state import log_progress

    complied: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    unknown_count = 0
    failed_count = 0

    for path in trace_files:
        try:
            artifact = _read_artifact(path)
        except Exception as exc:
            log_progress(STAGE_NAME, f"Failed to read {path}: {exc}", enabled=progress_enabled)
            failed_count += 1
            continue

        score = _judge_score(artifact)
        artifact["_source_path"] = str(path)

        if score == COMPLIED_JUDGE_SCORE:
            complied.append(artifact)
        elif score == REFUSED_JUDGE_SCORE:
            refused.append(artifact)
        else:
            unknown_count += 1

    log_progress(
        STAGE_NAME,
        "Grouped artifacts",
        enabled=progress_enabled,
        complied=len(complied),
        refused=len(refused),
        unknown=unknown_count,
        failed=failed_count,
    )

    if max_per_group is not None:
        complied = complied[:max_per_group]
        refused = refused[:max_per_group]

    summary = {
        "total_trace_files": len(trace_files),
        "complied_count_raw": len(complied) + (0 if max_per_group is None else 0),
        "refused_count_raw": len(refused) + (0 if max_per_group is None else 0),
        "complied_count_used": len(complied),
        "refused_count_used": len(refused),
        "unknown_count": unknown_count,
        "failed_to_read_count": failed_count,
        "max_per_group": max_per_group,
    }
    return complied, refused, summary


# ---------------------------------------------------------------------------
# Activation capture from Stage 6 artifacts
# ---------------------------------------------------------------------------

def capture_endthink_activations_from_artifacts(
    model_base: Any,
    artifacts: list[dict[str, Any]],
    *,
    endthink_token_ids: list[int],
    group_label: str,
    progress_enabled: bool,
) -> tuple[torch.Tensor, list[int | None], list[str]]:
    """
    For each artifact:
      1. Use full_prompt_plus_generation_token_ids (already generated in Stage 6).
      2. Find </think> position in that sequence.
      3. Run a forward pass on the truncated sequence up to </think>.
      4. Capture activations at </think> for each layer.

    Returns:
      activations: [n_valid, 1, n_layers, d_model] float32 on CPU
      endthink_positions: per-artifact </think> absolute position (None if not found)
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
    endthink_positions: list[int | None] = []
    skipped_sources: list[str] = []

    for artifact in progress_iter(
        artifacts,
        total=len(artifacts),
        desc=f"endofthink [{group_label}]",
        enabled=progress_enabled,
    ):
        source_path = artifact.get("_source_path", "unknown")
        full_ids = artifact.get("full_prompt_plus_generation_token_ids")
        if not full_ids:
            log_progress(STAGE_NAME, "Skipping: missing token IDs", enabled=progress_enabled, source=source_path)
            endthink_positions.append(None)
            skipped_sources.append(source_path)
            continue

        endthink_pos = find_endthink_position(full_ids, endthink_token_ids)
        if endthink_pos is None:
            # Try finding it via token_table (segment boundary)
            endthink_pos = _find_endthink_from_token_table(artifact, endthink_token_ids)

        if endthink_pos is None:
            log_progress(
                STAGE_NAME, "Skipping: </think> not found",
                enabled=progress_enabled, source=source_path,
            )
            endthink_positions.append(None)
            skipped_sources.append(source_path)
            continue

        log_progress(
            STAGE_NAME,
            "Capturing",
            enabled=progress_enabled,
            group=group_label,
            endthink_pos=endthink_pos,
        )

        truncated_ids = torch.tensor(
            full_ids[: endthink_pos + 1], dtype=torch.long
        ).unsqueeze(0)

        layer_cache = torch.zeros((n_layers, d_model), dtype=torch.float32, device="cpu")
        hooks = []

        def _make_hook(li: int):
            def _hook(module: Any, hook_input: Any) -> None:
                act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
                layer_cache[li] = act[0, endthink_pos].detach().float().cpu()
            return _hook

        for li, layer in enumerate(layers):
            hooks.append(layer.register_forward_pre_hook(_make_hook(li)))

        try:
            with torch.no_grad():
                model_base.model(input_ids=truncated_ids.to(input_device))
        finally:
            for h in hooks:
                h.remove()

        all_valid.append(layer_cache.unsqueeze(0).clone())  # [1, n_layers, d_model]
        endthink_positions.append(endthink_pos)

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not all_valid:
        raise RuntimeError(
            f"No {group_label} artifacts yielded a </think> token. "
            "Check that the Stage 6 traces include thinking chains."
        )

    return torch.stack(all_valid, dim=0), endthink_positions, skipped_sources


def _find_endthink_from_token_table(
    artifact: dict[str, Any],
    endthink_token_ids: list[int],
) -> int | None:
    """
    Secondary search: look for the last 'thinking' segment token in the token_table
    as a fallback for when the raw ID search fails.
    Only returns a position if we can confirm it from the token_ids.

    Segment label hints cover both Qwen3 ("think") and Gemma4 ("channel", "thought").
    """
    from poc_stage4.model_family_utils import THINKING_SEGMENT_HINTS_BY_FAMILY

    token_table = artifact.get("token_table") or []
    full_ids = artifact.get("full_prompt_plus_generation_token_ids") or []

    # Collect hints for all families so this function works regardless of which
    # model generated the artifact.
    all_hints: set[str] = set()
    for hints in THINKING_SEGMENT_HINTS_BY_FAMILY.values():
        all_hints.update(hints)

    # Find the absolute index of the last thinking-segment token
    last_thinking_abs: int | None = None
    for row in token_table:
        segment = str(row.get("segment") or row.get("role_or_part") or "").lower()
        if any(h in segment for h in all_hints):
            abs_idx = row.get("absolute_token_index")
            if abs_idx is not None:
                last_thinking_abs = int(abs_idx)

    if last_thinking_abs is None:
        return None

    # Verify the token at that absolute index matches our endthink_ids (if single-token)
    if len(endthink_token_ids) == 1:
        if last_thinking_abs < len(full_ids) and full_ids[last_thinking_abs] == endthink_token_ids[0]:
            return last_thinking_abs

    # Multi-token endthink: check if the window ending at last_thinking_abs matches
    n = len(endthink_token_ids)
    start = last_thinking_abs - n + 1
    if start >= 0 and full_ids[start : last_thinking_abs + 1] == endthink_token_ids:
        return last_thinking_abs

    return None


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def run_extraction_behavioral(
    *,
    model_name: str,
    model_family: str,
    stage6_input: Path,
    output_dir: Path,
    max_per_group: int | None,
    dry_run: bool,
    overwrite: bool,
    direction_normalization: str,
    no_progress: bool,
) -> dict[str, Any]:
    from poc_stage4.candidate_directions import generate_candidate_directions, split_prompts
    from poc_stage4.model_family_utils import get_thinking_end_token_ids, load_model_by_family
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

    log_progress(STAGE_NAME, "Starting behavioral contrast direction extraction", enabled=progress_enabled)

    # Collect Stage 6 trace files
    if not stage6_input.exists():
        raise FileNotFoundError(f"--stage6-input does not exist: {stage6_input}")
    trace_files = _collect_trace_files(stage6_input)
    if not trace_files:
        raise ValueError(f"No Stage 6 trace JSON files in: {stage6_input}")
    log_progress(STAGE_NAME, f"Found {len(trace_files)} trace files", enabled=progress_enabled)

    # Apply dry-run cap
    effective_max = 4 if dry_run else max_per_group
    complied_artifacts, refused_artifacts, group_summary = group_artifacts(
        trace_files,
        max_per_group=effective_max,
        progress_enabled=progress_enabled,
    )

    if not complied_artifacts:
        raise RuntimeError("No 'complied' examples (judge_score=10) found in Stage 6 artifacts.")
    if not refused_artifacts:
        raise RuntimeError("No 'refused' examples (judge_score=1) found in Stage 6 artifacts.")

    write_json(output_dir / "group_summary.json", group_summary)

    log_progress(STAGE_NAME, "Loading model", enabled=progress_enabled, model=model_name,
                 model_family=model_family)
    model_base = load_model_by_family(model_name, model_family)

    endthink_token_ids = get_thinking_end_token_ids(model_base.tokenizer, model_family)
    log_progress(STAGE_NAME, "Resolved thinking-end token IDs", enabled=progress_enabled,
                 model_family=model_family, endthink_token_ids=endthink_token_ids)

    # Split each group into train/val (75/25)
    n_complied = len(complied_artifacts)
    n_refused = len(refused_artifacts)
    val_frac = 0.25
    n_complied_val = max(1, int(round(n_complied * val_frac)))
    n_refused_val = max(1, int(round(n_refused * val_frac)))
    n_complied_train = n_complied - n_complied_val
    n_refused_train = n_refused - n_refused_val

    import random
    rng = random.Random(42)
    complied_shuf = list(complied_artifacts)
    refused_shuf = list(refused_artifacts)
    rng.shuffle(complied_shuf)
    rng.shuffle(refused_shuf)

    complied_train = complied_shuf[n_complied_val:]
    complied_val = complied_shuf[:n_complied_val]
    refused_train = refused_shuf[n_refused_val:]
    refused_val = refused_shuf[:n_refused_val]

    log_progress(
        STAGE_NAME, "Split into train/val",
        enabled=progress_enabled,
        complied_train=len(complied_train), complied_val=len(complied_val),
        refused_train=len(refused_train), refused_val=len(refused_val),
    )

    # Capture train activations
    log_progress(STAGE_NAME, "Capturing complied train activations", enabled=progress_enabled)
    complied_train_acts, _, complied_skipped = capture_endthink_activations_from_artifacts(
        model_base, complied_train,
        endthink_token_ids=endthink_token_ids,
        group_label="complied_train",
        progress_enabled=progress_enabled,
    )
    log_progress(STAGE_NAME, "Capturing refused train activations", enabled=progress_enabled)
    refused_train_acts, _, refused_skipped = capture_endthink_activations_from_artifacts(
        model_base, refused_train,
        endthink_token_ids=endthink_token_ids,
        group_label="refused_train",
        progress_enabled=progress_enabled,
    )

    n_train = min(complied_train_acts.shape[0], refused_train_acts.shape[0])
    complied_train_acts = complied_train_acts[:n_train]
    refused_train_acts = refused_train_acts[:n_train]

    log_progress(STAGE_NAME, "Computing behavioral DiM", enabled=progress_enabled, n_train=n_train)
    # DiM: complied − refused (direction that encodes "compliance after reasoning")
    candidate_directions = generate_candidate_directions(
        complied_train_acts,
        refused_train_acts,
        direction_normalization=direction_normalization,
    )
    torch.save(candidate_directions.cpu(), output_dir / "candidate_directions.pt")
    log_progress(STAGE_NAME, "Saved candidate_directions.pt", enabled=progress_enabled,
                 shape=list(candidate_directions.shape))

    # Capture val activations
    log_progress(STAGE_NAME, "Capturing complied val activations", enabled=progress_enabled)
    complied_val_acts, _, _ = capture_endthink_activations_from_artifacts(
        model_base, complied_val,
        endthink_token_ids=endthink_token_ids,
        group_label="complied_val",
        progress_enabled=progress_enabled,
    )
    log_progress(STAGE_NAME, "Capturing refused val activations", enabled=progress_enabled)
    refused_val_acts, _, _ = capture_endthink_activations_from_artifacts(
        model_base, refused_val,
        endthink_token_ids=endthink_token_ids,
        group_label="refused_val",
        progress_enabled=progress_enabled,
    )
    n_val = min(complied_val_acts.shape[0], refused_val_acts.shape[0])
    complied_val_acts = complied_val_acts[:n_val]
    refused_val_acts = refused_val_acts[:n_val]

    log_progress(STAGE_NAME, "Computing projection diagnostics", enabled=progress_enabled)
    diagnostic_rows, selection = compute_projection_diagnostics(
        candidate_directions,
        complied_val_acts,
        refused_val_acts,
        positions=[ENDOFTHINK_POSITION_VALUE],
    )

    timestamp_utc = utc_now()
    base_metadata: dict[str, Any] = {
        "artifact_version": STAGE4A1_ARTIFACT_VERSION,
        "stage": "stage4a1_behavioral_candidate_refusal_direction_extraction",
        "source_variant": "extract_refusal_direction_behavioral",
        "timestamp_utc": timestamp_utc,
        "model_name": model_name,
        "model_family": model_family,
        "contrast_set": "behavioral_complied_vs_refused",
        "contrast_set_notes": (
            "DiM = mean(complied_at_endthink) − mean(refused_at_endthink). "
            "This direction captures what changes in the residual stream at the </think> position "
            "between examples where the model was successfully hijacked vs. refused. "
            "It is distinct from Stage 4A1 which contrasts input labels (harmful vs. harmless)."
        ),
        "endthink_token_ids": endthink_token_ids,
        "stage6_input": str(stage6_input),
        "num_complied_train": n_train,
        "num_refused_train": n_train,
        "num_complied_val": n_val,
        "num_refused_val": n_val,
        "num_complied_train_skipped": len(complied_skipped),
        "num_refused_train_skipped": len(refused_skipped),
        "positions": [ENDOFTHINK_POSITION_VALUE],
        "token_position_semantics": "endofthink_token_behavioral_contrast",
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

    # Provisional direction
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
        "selected_position": ENDOFTHINK_POSITION_LABEL,
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
        STAGE_NAME, "Finished behavioral extraction",
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
            "Stage 4A1-behavioral: extract refusal direction at </think> "
            "using behavioral contrast (complied vs. refused Stage 6 examples)."
        )
    )
    parser.add_argument("--stage6-input", required=True,
                        help="Directory of Stage 6 trace JSON artifacts.")
    parser.add_argument(
        "--model-family", default="qwen3", choices=["qwen3", "gemma4"],
        help="Model family. Controls the thinking-end marker and HF loader. Default: qwen3.",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory. Default: outputs/stage4/<model-slug>/refusal_direction_behavioral/",
    )
    parser.add_argument(
        "--model-name", default=None,
        help="HF model name or path. Default: inferred from --model-family.",
    )
    parser.add_argument("--max-per-group", type=int, default=None,
                        help="Max examples to use per group (complied/refused). Default: all.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Use only 4 examples per group (quick test).")
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
        args.output_dir = f"outputs/stage4/{slug}/refusal_direction_behavioral"

    try:
        metrics = run_extraction_behavioral(
            model_name=args.model_name,
            model_family=model_family,
            stage6_input=Path(args.stage6_input),
            output_dir=Path(args.output_dir),
            max_per_group=args.max_per_group,
            dry_run=bool(args.dry_run),
            overwrite=bool(args.overwrite),
            direction_normalization=args.direction_normalization,
            no_progress=bool(args.no_progress),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out = Path(args.output_dir)
    print(f"Wrote Stage 4A1-behavioral artifacts to: {out}")
    print("direction.pt is provisional — run Stage 4A2 intervention selection to validate.")
    print(f"Selected provisional layer: {metrics['selection']['selected_layer']}")
    print(f"Selected score (standardized separation): {metrics['selection']['selected_score']:.4f}")
    print(f"Complied examples used: {metrics.get('num_complied_train', '?')}")
    print(f"Refused examples used: {metrics.get('num_refused_train', '?')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
