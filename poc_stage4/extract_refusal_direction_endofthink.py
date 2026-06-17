from __future__ import annotations

"""
Stage 4A1-endofthink: extract refusal direction at the </think> token position.

DIFFERENCE FROM extract_refusal_direction.py (Stage 4A1 / EOI position):
  Stage 4A1:   extracts at prompt-end offsets (last 1–6 tokens before generation starts)
  This script: extracts at the </think> token (after full reasoning, before answer)

WHY THIS POSITION:
  Arditi et al. use the EOI position (where the model reads the instruction).
  For reasoning models like Qwen3-14B, the CoT hijacking attack works by diluting the
  refusal signal DURING generation. The </think> token is where the model commits to a
  response after deliberation — the most mechanistically relevant checkpoint for whether
  the model will refuse or comply.

CONTRAST SET: same as Stage 4A1 — harmful vs. harmless vanilla prompts.
EXTRACTION POSITION: the </think> token in the model's generated thinking chain.
METHOD:
  1. Generate each prompt with enable_thinking=True until </think> appears.
  2. Truncate the full sequence at (and including) </think>.
  3. Run one forward pass on the truncated sequence with forward pre-hooks.
  4. Capture residual stream activation at the </think> token position for every layer.
  5. Compute DiM: mean(harmful) − mean(harmless) per layer → candidate directions.

OUTPUT SHAPE: candidate_directions.pt is [1, n_layers, d_model]
  (one "position" = the endofthink position; position label stored as "endofthink").
  This is compatible with the existing projection_diagnostics.py and the Stage 4A2
  intervention selection pipeline.

OUTPUTS (to --output-dir, default: outputs/stage4/<model-slug>/refusal_direction_endofthink/
  where <model-slug> = qwen3-14b or gemma4-e4b-it depending on --model-family):
  candidate_directions.pt        [1, n_layers, d_model]
  candidate_metadata.json        includes endofthink token IDs and skip statistics
  projection_diagnostics.json    per-layer standardized separation scores
  direction.pt                   provisional direction (run Stage 4A2 to validate)
  selected_direction.json        provisional selection metadata
  extraction_metrics.json        full run summary
  skipped_prompts.json           prompts where </think> was not found in the generation
"""

import argparse
import sys
from pathlib import Path
from typing import Any

STAGE_NAME = "stage4a1_endofthink"

# Sentinel: the "position" label for the endofthink extraction (for metadata)
# We pass this to projection_diagnostics as a single-element list with a special value
# (positions[0] is stored in metadata but not used for arithmetic offset computation).
ENDOFTHINK_POSITION_LABEL = "endofthink"
ENDOFTHINK_POSITION_VALUE = 0  # placeholder integer for schema compatibility


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected true or false.")


def _default_prompt_count(args: argparse.Namespace, *, harmful: bool) -> int:
    explicit = args.num_harmful if harmful else args.num_harmless
    if explicit is not None:
        return explicit
    return 4 if args.dry_run else 64


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 4A1-endofthink: extract refusal direction at the </think> token position. "
            "Generates each prompt with thinking enabled, finds </think>, and computes DiM."
        )
    )
    parser.add_argument(
        "--model-family", default="qwen3", choices=["qwen3", "gemma4"],
        help="Model family. Controls the thinking-end marker and HF loader. Default: qwen3.",
    )
    parser.add_argument(
        "--model-name", default=None,
        help="HF model name or path. Default: inferred from --model-family.",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory. Default: outputs/stage4/<model-slug>/refusal_direction_endofthink/",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Use 4 prompts each (quick test without generating results).")
    parser.add_argument("--num-harmful", type=int)
    parser.add_argument("--num-harmless", type=int)
    parser.add_argument("--max-generation-tokens", type=int, default=2048,
                        help="Max new tokens to generate when looking for </think>. Default: 2048.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--direction-normalization", choices=("unit", "raw"), default="unit")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--use-builtin-prompts", action="store_true",
                        help="Use the small built-in prompt lists instead of vendored splits.")
    return parser


# ---------------------------------------------------------------------------
# Finding </think> in token sequences
# ---------------------------------------------------------------------------

def get_endthink_token_ids(tokenizer: Any) -> list[int]:
    """Encode '</think>' and return its token ID sequence (Qwen3 only).

    For other model families use get_thinking_end_token_ids(tokenizer, model_family)
    from poc_stage4.model_family_utils instead.
    """
    from poc_stage4.model_family_utils import get_thinking_end_token_ids
    return get_thinking_end_token_ids(tokenizer, "qwen3")


def find_endthink_position(token_ids: list[int], endthink_ids: list[int]) -> int | None:
    """
    Return the absolute index of the last token of the first </think> occurrence.
    Returns None if not found.
    """
    n = len(endthink_ids)
    for i in range(len(token_ids) - n + 1):
        if token_ids[i:i + n] == endthink_ids:
            return i + n - 1
    return None


# ---------------------------------------------------------------------------
# Generate-then-capture for each prompt
# ---------------------------------------------------------------------------

def generate_and_capture_endthink_activations(
    model_base: Any,
    prompts: list[str],
    *,
    endthink_token_ids: list[int],
    max_generation_tokens: int,
    progress_enabled: bool,
    stage_name: str,
) -> tuple[Any, list[int | None], list[str]]:
    """
    For each prompt:
      1. Generate with enable_thinking=True until </think> appears or max tokens.
      2. Find </think> position in the full generated sequence.
      3. Run a forward pass on the truncated sequence (up to and including </think>).
      4. Capture residual stream input at the </think> position for every layer.

    Returns:
      activations: torch.Tensor [n_valid, 1, n_layers, d_model]  (float32, on CPU)
      valid_positions: list[int | None] — absolute </think> position for each prompt
                       (None for prompts where </think> was not found)
      skipped_prompts: list of prompts where </think> was not found
    """
    import torch
    from poc_stage4.run_state import log_progress, progress_iter

    layers = model_base.layers
    n_layers = model_base.num_layers
    d_model = model_base.hidden_size

    try:
        input_embedding = model_base.model.get_input_embeddings()
        input_device = input_embedding.weight.device
    except Exception:
        input_device = next(model_base.model.parameters()).device

    all_valid_activations: list[Any] = []
    valid_positions: list[int | None] = []
    skipped_prompts: list[str] = []

    for prompt in progress_iter(
        prompts,
        total=len(prompts),
        desc="endofthink extraction",
        enabled=progress_enabled,
    ):
        # Step 1: Format prompt and tokenize
        formatted = model_base.format_prompts([prompt], enable_thinking=True)[0]
        tokenized = model_base.tokenizer(
            formatted,
            return_tensors="pt",
            padding=False,
            truncation=False,
        )
        prompt_input_ids = tokenized.input_ids
        prompt_len = prompt_input_ids.shape[1]

        # Step 2: Generate until </think> or max tokens
        log_progress(
            stage_name,
            "Generating",
            enabled=progress_enabled,
            prompt_len=prompt_len,
            max_generation_tokens=max_generation_tokens,
        )
        with torch.no_grad():
            output_ids = model_base.model.generate(
                input_ids=prompt_input_ids.to(input_device),
                max_new_tokens=max_generation_tokens,
                do_sample=False,
                pad_token_id=model_base.tokenizer.pad_token_id or model_base.tokenizer.eos_token_id,
            )
        full_token_ids: list[int] = output_ids[0].tolist()

        # Step 3: Find </think> in the full sequence (prompt + generated)
        endthink_pos = find_endthink_position(full_token_ids, endthink_token_ids)
        if endthink_pos is None:
            log_progress(
                stage_name,
                "Skipping prompt: thinking-end token not found in generated sequence",
                enabled=progress_enabled,
                generated_tokens=len(full_token_ids) - prompt_len,
            )
            valid_positions.append(None)
            skipped_prompts.append(prompt)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            continue

        log_progress(
            stage_name,
            "Found </think>",
            enabled=progress_enabled,
            endthink_pos=endthink_pos,
            thinking_tokens=endthink_pos - prompt_len + 1,
        )

        # Step 4: Truncate sequence to prompt + thinking (inclusive of </think>)
        truncated_ids = torch.tensor(
            full_token_ids[: endthink_pos + 1],
            dtype=torch.long,
        ).unsqueeze(0)

        # Step 5: Forward pass with pre-hooks to capture activation at endthink_pos
        # We store [n_layers, d_model] for this prompt
        layer_cache = torch.zeros((n_layers, d_model), dtype=torch.float32, device="cpu")
        hooks = []

        def _make_hook(layer_idx: int):
            def _hook(module: Any, hook_input: Any) -> None:
                act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
                # act: [1, seq_len, d_model]
                layer_cache[layer_idx] = act[0, endthink_pos].detach().float().cpu()
            return _hook

        for li, layer in enumerate(layers):
            hooks.append(layer.register_forward_pre_hook(_make_hook(li)))

        try:
            with torch.no_grad():
                model_base.model(input_ids=truncated_ids.to(input_device))
        finally:
            for h in hooks:
                h.remove()

        # Add position dimension to match schema: [1, n_layers, d_model]
        all_valid_activations.append(layer_cache.unsqueeze(0).clone())
        valid_positions.append(endthink_pos)

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not all_valid_activations:
        raise RuntimeError(
            "No prompts yielded a thinking-end token in their generated sequences. "
            "The model may not be generating thinking chains for these prompts, or "
            "the end-of-thinking marker for this model family was not found. "
            "Try increasing --max-generation-tokens."
        )

    activations = torch.stack(all_valid_activations, dim=0)  # [n_valid, 1, n_layers, d_model]
    return activations, valid_positions, skipped_prompts


# ---------------------------------------------------------------------------
# Check outputs
# ---------------------------------------------------------------------------

OUTPUT_FILENAMES = (
    "candidate_directions.pt",
    "candidate_metadata.json",
    "projection_diagnostics.json",
    "direction.pt",
    "selected_direction.json",
    "extraction_metrics.json",
)


def _check_outputs(output_dir: Path, *, overwrite: bool) -> None:
    existing = [output_dir / fn for fn in OUTPUT_FILENAMES if (output_dir / fn).exists()]
    if existing and not overwrite:
        formatted = "\n".join(f"  {p}" for p in existing)
        raise RuntimeError(
            "Stage 4A1-endofthink output files already exist. Use --overwrite to replace:\n"
            + formatted
        )


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def run_extraction_endofthink(
    *,
    model_name: str,
    model_family: str,
    output_dir: Path,
    dry_run: bool,
    num_harmful: int,
    num_harmless: int,
    max_generation_tokens: int,
    seed: int,
    overwrite: bool,
    direction_normalization: str,
    use_builtin_prompts: bool,
    no_progress: bool,
) -> dict[str, Any]:
    import torch

    from poc_stage4.candidate_directions import generate_candidate_directions, split_prompts
    from poc_stage4.default_prompts import load_prompt_sets
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

    log_progress(STAGE_NAME, "Starting end-of-thinking direction extraction", enabled=progress_enabled)

    log_progress(STAGE_NAME, "Loading prompt sets", enabled=progress_enabled)
    harmful_prompts, harmless_prompts, prompt_source_metadata = load_prompt_sets(
        num_harmful=num_harmful,
        num_harmless=num_harmless,
        seed=seed,
        use_builtin_prompts=use_builtin_prompts,
    )
    prompt_split = split_prompts(harmful_prompts, harmless_prompts, seed=seed)
    log_progress(
        STAGE_NAME,
        "Loaded prompt split",
        enabled=progress_enabled,
        harmful_train=len(prompt_split.harmful_train),
        harmless_train=len(prompt_split.harmless_train),
        harmful_val=len(prompt_split.harmful_validation),
        harmless_val=len(prompt_split.harmless_validation),
    )

    log_progress(STAGE_NAME, "Loading model", enabled=progress_enabled, model=model_name,
                 model_family=model_family)
    model_base = load_model_by_family(model_name, model_family)

    endthink_token_ids = get_thinking_end_token_ids(model_base.tokenizer, model_family)
    log_progress(
        STAGE_NAME,
        "Resolved thinking-end token IDs",
        enabled=progress_enabled,
        model_family=model_family,
        endthink_token_ids=endthink_token_ids,
    )

    # --- Harmful train ---
    log_progress(STAGE_NAME, "Generating + capturing harmful train activations", enabled=progress_enabled)
    harmful_train_acts, harmful_train_positions, harmful_skipped = generate_and_capture_endthink_activations(
        model_base,
        prompt_split.harmful_train,
        endthink_token_ids=endthink_token_ids,
        max_generation_tokens=max_generation_tokens,
        progress_enabled=progress_enabled,
        stage_name=STAGE_NAME,
    )
    log_progress(
        STAGE_NAME,
        "Harmful train captured",
        enabled=progress_enabled,
        valid=harmful_train_acts.shape[0],
        skipped=len(harmful_skipped),
    )

    # --- Harmless train ---
    log_progress(STAGE_NAME, "Generating + capturing harmless train activations", enabled=progress_enabled)
    harmless_train_acts, harmless_train_positions, harmless_skipped = generate_and_capture_endthink_activations(
        model_base,
        prompt_split.harmless_train,
        endthink_token_ids=endthink_token_ids,
        max_generation_tokens=max_generation_tokens,
        progress_enabled=progress_enabled,
        stage_name=STAGE_NAME,
    )
    log_progress(
        STAGE_NAME,
        "Harmless train captured",
        enabled=progress_enabled,
        valid=harmless_train_acts.shape[0],
        skipped=len(harmless_skipped),
    )

    # Ensure same number of valid train examples for DiM
    n_valid_train = min(harmful_train_acts.shape[0], harmless_train_acts.shape[0])
    if n_valid_train == 0:
        raise RuntimeError("No valid training examples after thinking-end token filtering.")
    harmful_train_acts = harmful_train_acts[:n_valid_train]
    harmless_train_acts = harmless_train_acts[:n_valid_train]

    log_progress(STAGE_NAME, "Computing candidate directions (DiM)", enabled=progress_enabled)
    candidate_directions = generate_candidate_directions(
        harmful_train_acts,
        harmless_train_acts,
        direction_normalization=direction_normalization,
    )
    # Shape: [1, n_layers, d_model]
    torch.save(candidate_directions.cpu(), output_dir / "candidate_directions.pt")
    log_progress(
        STAGE_NAME,
        "Saved candidate_directions.pt",
        enabled=progress_enabled,
        shape=list(candidate_directions.shape),
    )

    # --- Harmful validation ---
    log_progress(STAGE_NAME, "Generating + capturing harmful validation activations", enabled=progress_enabled)
    harmful_val_acts, _, _ = generate_and_capture_endthink_activations(
        model_base,
        prompt_split.harmful_validation,
        endthink_token_ids=endthink_token_ids,
        max_generation_tokens=max_generation_tokens,
        progress_enabled=progress_enabled,
        stage_name=STAGE_NAME,
    )

    # --- Harmless validation ---
    log_progress(STAGE_NAME, "Generating + capturing harmless validation activations", enabled=progress_enabled)
    harmless_val_acts, _, _ = generate_and_capture_endthink_activations(
        model_base,
        prompt_split.harmless_validation,
        endthink_token_ids=endthink_token_ids,
        max_generation_tokens=max_generation_tokens,
        progress_enabled=progress_enabled,
        stage_name=STAGE_NAME,
    )

    n_valid_val = min(harmful_val_acts.shape[0], harmless_val_acts.shape[0])
    harmful_val_acts = harmful_val_acts[:n_valid_val]
    harmless_val_acts = harmless_val_acts[:n_valid_val]
    log_progress(STAGE_NAME, "Validation activations captured", enabled=progress_enabled, n_valid_val=n_valid_val)

    log_progress(STAGE_NAME, "Computing projection diagnostics", enabled=progress_enabled)
    # Use a sentinel list [ENDOFTHINK_POSITION_VALUE] as the "positions" arg — one position only.
    diagnostic_rows, selection = compute_projection_diagnostics(
        candidate_directions,
        harmful_val_acts,
        harmless_val_acts,
        positions=[ENDOFTHINK_POSITION_VALUE],
    )

    timestamp_utc = utc_now()
    base_metadata: dict[str, Any] = {
        "artifact_version": STAGE4A1_ARTIFACT_VERSION,
        "stage": "stage4a1_endofthink_candidate_refusal_direction_extraction",
        "source_variant": "extract_refusal_direction_endofthink",
        "timestamp_utc": timestamp_utc,
        "model_name": model_name,
        "model_family": model_family,
        "endofthink_extraction_notes": (
            "Direction extracted at the </think> token position after model reasoning. "
            "This captures 'refusal commitment after deliberation' rather than "
            "'harmfulness of input' (which Stage 4A1 EOI captures)."
        ),
        "endthink_token_ids": endthink_token_ids,
        "max_generation_tokens": max_generation_tokens,
        "num_harmful_prompts": num_harmful,
        "num_harmless_prompts": num_harmless,
        "num_harmful_train_valid": int(harmful_train_acts.shape[0]),
        "num_harmless_train_valid": int(harmless_train_acts.shape[0]),
        "num_harmful_train_skipped": len(harmful_skipped),
        "num_harmless_train_skipped": len(harmless_skipped),
        "num_harmful_val_valid": int(harmful_val_acts.shape[0]),
        "num_harmless_val_valid": int(harmless_val_acts.shape[0]),
        "num_valid_train_used_for_dim": n_valid_train,
        "num_valid_val_used_for_diagnostics": n_valid_val,
        "positions": [ENDOFTHINK_POSITION_VALUE],
        "token_position_semantics": "endofthink_token_after_generation",
        "layers": list(range(model_base.num_layers)),
        "num_layers": model_base.num_layers,
        "hidden_size": model_base.hidden_size,
        "candidate_tensor_shape": list(candidate_directions.shape),
        "direction_normalization": direction_normalization,
        "dry_run": dry_run,
        "seed": seed,
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

    # Save provisional direction
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
        "selected_harmful_projection_mean": selection.selected_harmful_projection_mean,
        "selected_harmless_projection_mean": selection.selected_harmless_projection_mean,
        "direction_norm": float(selected_direction.norm().item()),
        "direction_path": str(direction_path),
        "scientific_use_warning": (
            "Provisional: selected by projection diagnostics only. "
            "Run Stage 4A2 intervention-based selection before scientific use."
        ),
    }
    write_json(output_dir / "selected_direction.json", selected_metadata)

    # Save skipped prompts for inspection
    skipped_payload = {
        "harmful_skipped": harmful_skipped,
        "harmless_skipped": harmless_skipped,
        "total_harmful_skipped": len(harmful_skipped),
        "total_harmless_skipped": len(harmless_skipped),
    }
    write_json(output_dir / "skipped_prompts.json", skipped_payload)

    metrics: dict[str, Any] = {
        **base_metadata,
        "outputs": {fn: str(output_dir / fn) for fn in OUTPUT_FILENAMES},
        "selection": selected_metadata,
        "diagnostic_summary": summarize_diagnostics(diagnostic_rows),
    }
    write_json(output_dir / "extraction_metrics.json", metrics)

    log_progress(
        STAGE_NAME,
        "Finished Stage 4A1-endofthink extraction",
        enabled=progress_enabled,
        selected_layer=selection.selected_layer,
        score=round(selection.selected_score, 4),
    )
    return metrics


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = build_parser().parse_args()

    from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY, DEFAULT_MODEL_SLUG_BY_FAMILY
    model_family: str = args.model_family
    if args.model_name is None:
        args.model_name = DEFAULT_MODEL_BY_FAMILY[model_family]
    if args.output_dir is None:
        slug = DEFAULT_MODEL_SLUG_BY_FAMILY[model_family]
        args.output_dir = f"outputs/stage4/{slug}/refusal_direction_endofthink"

    try:
        metrics = run_extraction_endofthink(
            model_name=args.model_name,
            model_family=model_family,
            output_dir=Path(args.output_dir),
            dry_run=bool(args.dry_run),
            num_harmful=_default_prompt_count(args, harmful=True),
            num_harmless=_default_prompt_count(args, harmful=False),
            max_generation_tokens=args.max_generation_tokens,
            seed=args.seed,
            overwrite=bool(args.overwrite),
            direction_normalization=args.direction_normalization,
            use_builtin_prompts=bool(args.use_builtin_prompts),
            no_progress=bool(args.no_progress),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out = Path(args.output_dir)
    print(f"Wrote Stage 4A1-endofthink artifacts to: {out}")
    print("direction.pt is provisional — run Stage 4A2 intervention selection to validate.")
    print(f"Selected provisional layer: {metrics['selection']['selected_layer']}")
    print(f"Selected score (standardized separation): {metrics['selection']['selected_score']:.4f}")
    skipped = metrics.get("num_harmful_train_skipped", 0) + metrics.get("num_harmless_train_skipped", 0)
    if skipped:
        print(f"WARNING: {skipped} prompts skipped (</think> not found). See skipped_prompts.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
