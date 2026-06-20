"""
Stage 4A1-startofthink: extract refusal direction at the <think> token position.

DIFFERENCE FROM OTHER EXTRACTIONS:
  Stage 4A1 (EOI/original):  enable_thinking=False → prompt includes <think></think> template;
                              captures at offsets -1...-4 from end of prompt (~at </think> position).
  Stage 4A1-endofthink:      enable_thinking=True → generates full reasoning chain until </think>;
                              captures at </think> position (after all deliberation).
  Stage 4A1-startofthink:    enable_thinking=True → prompt ends at `<|im_start|>assistant\n`;
                              appends <think> token (151667) manually; no generation needed.
                              Captures at <think> position: the transition INTO the thinking phase.

WHY THIS POSITION:
  Prior Stage 4C analysis found the refusal signal appears at BIN 0 (first 5% of thinking,
  ~first 150 tokens). This suggests the representational difference is established very early
  in the thinking chain — possibly at or before the <think> token itself.
  Extracting here fills the timeline: EOI → <think> → early thinking (bin 0) → </think>.
  If startofthink and endofthink directions are well-aligned, the attack commits at <think>.
  If they diverge, the corruption happens during the reasoning chain.

CONTRAST SET: harmful vs. harmless vanilla prompts (same as EOI/endofthink).
EXTRACTION POSITION: <think> token (Qwen3 token ID 151667; Gemma4: <|channel>thought).
METHOD:
  1. Format each prompt with enable_thinking=True → prompt ends at `assistant\n`.
  2. Tokenize and append the <think> start token.
  3. Run one forward pass with forward pre-hooks.
  4. Capture residual stream at the <think> token position (last token in sequence).
  5. Compute DiM: mean(harmful) − mean(harmless) per layer.

NO GENERATION REQUIRED — much faster than endofthink.
At ~1–2s per prompt (just one forward pass), 220+220 prompts takes <15 min total.

OUTPUT SHAPE: candidate_directions.pt is [1, n_layers, d_model]
  (one position = "startofthink", compatible with Stage 4A2 subspace pipeline.)

Outputs (to --output-dir, default: outputs/stage4/<model-slug>/refusal_direction_startofthink/):
  candidate_directions.pt       [1, n_layers, d_model]
  candidate_metadata.json       position/token metadata
  projection_diagnostics.json   per-layer standardized separation scores
  direction.pt                  provisional best direction
  selected_direction.json       provisional selection metadata
  extraction_metrics.json       run summary
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from typing import Any

STAGE_NAME = "stage4a1_startofthink"
STARTOFTHINK_POSITION_LABEL = "startofthink"
STARTOFTHINK_POSITION_VALUE = 0


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    n = value.strip().lower()
    if n in {"true", "1", "yes", "y"}:
        return True
    if n in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected true or false.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 4A1-startofthink: extract refusal direction at the <think> token position. "
            "No generation needed — appends <think> to the formatted prompt and runs one forward pass."
        )
    )
    parser.add_argument(
        "--model-family", default="qwen3", choices=["qwen3", "gemma4"],
        help="Model family. Default: qwen3.",
    )
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--num-harmful", type=int)
    parser.add_argument("--num-harmless", type=int)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--direction-normalization", choices=("unit", "raw"), default="unit")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--use-builtin-prompts", action="store_true")
    return parser


def _default_prompt_count(args: argparse.Namespace, *, harmful: bool) -> int:
    explicit = args.num_harmful if harmful else args.num_harmless
    if explicit is not None:
        return explicit
    return 4 if args.dry_run else 220


def capture_startofthink_activations(
    model_base: Any,
    prompts: list[str],
    *,
    think_start_token_id: int,
    progress_enabled: bool,
    stage_name: str,
    group_label: str = "group",
    batch_size: int = 32,
) -> Any:
    """
    For each prompt:
      1. Format with enable_thinking=True → prompt ends at `<|im_start|>assistant\\n`.
      3. Run batched forward pass on RIGHT-padded (prompt + <think>) sequences.
         Right-padding is required: Flash Attention 2 (auto-selected by Qwen3) does not
         support left-padded inputs without explicit position_ids.  Left-padding caused
         harmful/harmless activations at L3+ to be identical (zero DiM) because the
         incorrect attention patterns are similar across both groups.
         With right-padding + causal masking, <think> only attends to preceding real tokens.
      4. Capture residual stream at each example's per-example <think> position.
      4. Capture residual stream at the <think> position for every layer.

    Batching dramatically reduces the number of CUDA kernel launches, improving
    robustness on shared-GPU nodes where cumulative launch failures were observed.

    Returns:
      activations: torch.Tensor [n_prompts, 1, n_layers, d_model]  (float32, on CPU)
    """
    import torch
    from poc_stage4.run_state import log_progress, progress_iter

    layers = model_base.layers
    n_layers = model_base.num_layers
    d_model = model_base.hidden_size
    tokenizer = model_base.tokenizer

    try:
        input_embedding = model_base.model.get_input_embeddings()
        input_device = input_embedding.weight.device
    except Exception:
        input_device = next(model_base.model.parameters()).device

    # Tokenize all prompts upfront, appending <think>
    t0_total = time.time()
    log_progress(stage_name, f"[{group_label}] tokenizing {len(prompts)} prompts...", enabled=progress_enabled)
    all_input_ids: list[Any] = []
    for prompt in prompts:
        formatted = model_base.format_prompts([prompt], enable_thinking=True)[0]
        tok_ids = tokenizer(formatted, return_tensors="pt", padding=False, truncation=False).input_ids[0]
        # Append <think> token
        think_id = torch.tensor([think_start_token_id], dtype=torch.long)
        full_ids = torch.cat([tok_ids, think_id], dim=0)  # [prompt_len + 1]
        all_input_ids.append(full_ids)

    all_activations: list[Any] = []

    # Process in batches; LEFT-pad with explicit position_ids.
    # Flash Attention 2 (auto-selected by Qwen3) ignores the 2D attention_mask for
    # left-padded inputs when position_ids is absent, producing wrong RoPE encodings
    # and causing activations to converge (zero DiM at L3+).
    # Fix: pass position_ids = cumsum(attention_mask) - 1 so each real token gets its
    # correct local position (0-indexed), and <think> lands at position real_len-1.
    # With left-padding, <think> is always at the same tensor column (max_len-1),
    # so the hook can extract it with a single vectorised slice.
    pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0

    n_batches = (len(prompts) + batch_size - 1) // batch_size
    for batch_idx in range(n_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, len(prompts))
        batch_ids = all_input_ids[start:end]
        bs = len(batch_ids)

        # Left-pad; <think> always lands at column max_len-1 for all examples.
        max_len = max(ids.shape[0] for ids in batch_ids)
        padded = torch.full((bs, max_len), pad_token_id, dtype=torch.long)
        for i, ids in enumerate(batch_ids):
            padded[i, max_len - ids.shape[0] :] = ids
        attention_mask = (padded != pad_token_id).long()
        think_pos = max_len - 1  # same column for every row

        # Explicit position_ids: real tokens get positions 0..real_len-1 (cumsum trick).
        # Padding positions get id=1 (arbitrary; they are masked out by attention_mask).
        position_ids = attention_mask.long().cumsum(dim=-1) - 1
        position_ids.masked_fill_(attention_mask == 0, 1)

        batch_cache = torch.zeros((bs, n_layers, d_model), dtype=torch.float32)
        hooks = []

        def _make_hook(layer_idx: int) -> Any:
            def _hook(module: Any, hook_input: Any) -> None:
                act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
                batch_cache[:, layer_idx, :] = act[:, think_pos, :].detach().float().cpu()
            return _hook
        for li, layer in enumerate(layers):
            hooks.append(layer.register_forward_pre_hook(_make_hook(li)))

        try:
            with torch.no_grad():
                model_base.model(
                    input_ids=padded.to(input_device),
                    attention_mask=attention_mask.to(input_device),
                    position_ids=position_ids.to(input_device),
                    use_cache=False,
                )
            if torch.cuda.is_available():
                torch.cuda.synchronize()
        finally:
            for h in hooks:
                h.remove()

        # batch_cache: [bs, n_layers, d_model] → [bs, 1, n_layers, d_model]
        all_activations.append(batch_cache.unsqueeze(1))

        elapsed = time.time() - t0_total
        log_progress(
            stage_name,
            f"[{group_label}] batch {batch_idx+1}/{n_batches} examples {start+1}-{end}/{len(prompts)} elapsed={elapsed:.1f}s",
            enabled=progress_enabled,
        )
        if progress_enabled:
            print(f"startofthink extraction [{group_label}]: {end}/{len(prompts)} ({100*end/len(prompts):.0f}%)")

    # Concatenate: [n_prompts, 1, n_layers, d_model]
    return torch.cat(all_activations, dim=0)


def run(args: argparse.Namespace) -> None:
    import torch
    from poc_stage4.candidate_directions import generate_candidate_directions, split_prompts
    from poc_stage4.default_prompts import load_prompt_sets
    from poc_stage4.model_family_utils import (
        DEFAULT_MODEL_BY_FAMILY,
        DEFAULT_MODEL_SLUG_BY_FAMILY,
        load_model_by_family,
        get_thinking_start_token_ids,
    )
    from poc_stage4.projection_diagnostics import (
        compute_projection_diagnostics,
        summarize_diagnostics,
    )
    from poc_stage4.schemas import (
        PROVISIONAL_SELECTION,
        PROVISIONAL_SELECTION_CRITERION,
        STAGE4A1_ARTIFACT_VERSION,
        utc_now,
        write_json,
    )

    model_family = args.model_family
    model_name = args.model_name or DEFAULT_MODEL_BY_FAMILY[model_family]
    model_slug = DEFAULT_MODEL_SLUG_BY_FAMILY[model_family]

    output_dir = pathlib.Path(
        args.output_dir or f"outputs/stage4/{model_slug}/refusal_direction_startofthink"
    )

    if output_dir.exists() and not args.overwrite:
        if (output_dir / "candidate_directions.pt").exists():
            print(
                f"[{STAGE_NAME}] Output already exists at {output_dir}. "
                "Use --overwrite to re-run.",
                file=sys.stderr,
            )
            sys.exit(0)

    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------
    num_harmful = _default_prompt_count(args, harmful=True)
    num_harmless = _default_prompt_count(args, harmful=False)

    harmful_prompts, harmless_prompts, prompt_source_meta = load_prompt_sets(
        num_harmful=num_harmful,
        num_harmless=num_harmless,
        seed=args.seed,
        use_builtin_prompts=args.use_builtin_prompts,
    )
    prompt_split = split_prompts(harmful_prompts, harmless_prompts, seed=args.seed)

    print(
        f"[{STAGE_NAME}] harmful: train={len(prompt_split.harmful_train)} "
        f"val={len(prompt_split.harmful_validation)} | "
        f"harmless: train={len(prompt_split.harmless_train)} "
        f"val={len(prompt_split.harmless_validation)}",
        flush=True,
    )

    # ------------------------------------------------------------------
    # Load model
    # ------------------------------------------------------------------
    print(f"[{STAGE_NAME}] Loading {model_name} ...", flush=True)
    model_base = load_model_by_family(model_name, model_family)

    think_start_ids = get_thinking_start_token_ids(model_base.tokenizer, model_family)
    if not think_start_ids:
        raise ValueError("Could not find thinking-start token ID for this model family.")
    think_start_token_id = think_start_ids[-1]
    print(f"[{STAGE_NAME}] <think> token id = {think_start_token_id}", flush=True)

    n_layers = model_base.num_layers
    d_model = model_base.hidden_size
    progress_enabled = not args.no_progress

    # ------------------------------------------------------------------
    # Extract activations for train + val groups
    # ------------------------------------------------------------------
    def _extract(prompts: list[str], label: str) -> torch.Tensor:
        t0 = time.time()
        acts = capture_startofthink_activations(
            model_base, prompts,
            think_start_token_id=think_start_token_id,
            progress_enabled=progress_enabled,
            stage_name=STAGE_NAME,
            group_label=label,
        )
        print(f"[{STAGE_NAME}] {label}: {len(prompts)} prompts in {time.time()-t0:.1f}s shape={acts.shape}", flush=True)
        return acts

    harmful_train_acts = _extract(prompt_split.harmful_train, "harmful_train")
    harmless_train_acts = _extract(prompt_split.harmless_train, "harmless_train")
    harmful_val_acts = _extract(prompt_split.harmful_validation, "harmful_val")
    harmless_val_acts = _extract(prompt_split.harmless_validation, "harmless_val")

    # ------------------------------------------------------------------
    # Compute candidate directions: DiM from train activations per layer
    # Use generate_candidate_directions: [n_harmful_train, 1, n_layers, d_model]
    # → needs [n, n_pos, n_layers, d_model] format
    # ------------------------------------------------------------------
    n_train = min(harmful_train_acts.shape[0], harmless_train_acts.shape[0])
    candidate_dirs = generate_candidate_directions(
        harmful_train_acts[:n_train],
        harmless_train_acts[:n_train],
        direction_normalization=args.direction_normalization,
    )  # [1, n_layers, d_model]

    # ------------------------------------------------------------------
    # Projection diagnostics on val activations
    # ------------------------------------------------------------------
    n_val = min(harmful_val_acts.shape[0], harmless_val_acts.shape[0])
    diagnostic_rows, selection = compute_projection_diagnostics(
        candidate_dirs,
        harmful_val_acts[:n_val],
        harmless_val_acts[:n_val],
        positions=[STARTOFTHINK_POSITION_VALUE],
    )

    best_pos_idx = selection.selected_position_index
    best_layer = selection.selected_layer
    best_score = selection.selected_score

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    torch.save(candidate_dirs, output_dir / "candidate_directions.pt")
    print(f"[{STAGE_NAME}] Saved candidate_directions.pt shape={candidate_dirs.shape}", flush=True)

    base_meta = {
        "artifact_version": STAGE4A1_ARTIFACT_VERSION,
        "stage": f"{STAGE_NAME}_candidate_refusal_direction_extraction",
        "source_variant": "extract_refusal_direction_startofthink",
        "timestamp_utc": utc_now(),
        "model_name": model_name,
        "model_family": model_family,
        "extraction_position": STARTOFTHINK_POSITION_LABEL,
        "think_start_token_id": think_start_token_id,
        "extraction_notes": (
            "Direction extracted at the <think> token position (first generated token). "
            "Format: enable_thinking=True so prompt ends at `assistant\\n`; "
            "<think> appended manually. No generation step — single forward pass only. "
            "Contrast: harmful vs harmless (same as EOI/endofthink). "
            "Fills the timeline: EOI → <think> → early thinking (bin 0) → </think>."
        ),
        "num_harmful_prompts": len(harmful_prompts),
        "num_harmless_prompts": len(harmless_prompts),
        "num_harmful_train": len(prompt_split.harmful_train),
        "num_harmless_train": len(prompt_split.harmless_train),
        "num_harmful_val": len(prompt_split.harmful_validation),
        "num_harmless_val": len(prompt_split.harmless_validation),
        "num_train_used_for_dim": n_train,
        "num_val_used_for_diagnostics": n_val,
        "positions": [STARTOFTHINK_POSITION_VALUE],
        "token_position_semantics": "startofthink_first_generated_token",
        "layers": list(range(n_layers)),
        "num_layers": n_layers,
        "hidden_size": d_model,
        "candidate_tensor_shape": list(candidate_dirs.shape),
        "direction_normalization": args.direction_normalization,
        "dry_run": args.dry_run,
        "seed": args.seed,
        **prompt_source_meta,
    }
    write_json(output_dir / "candidate_metadata.json", base_meta)

    diagnostics_payload = {
        **base_meta,
        "selection_status": PROVISIONAL_SELECTION,
        "selection_criterion": PROVISIONAL_SELECTION_CRITERION,
        "diagnostic_summary": summarize_diagnostics(diagnostic_rows),
        "diagnostics": diagnostic_rows,
    }
    write_json(output_dir / "projection_diagnostics.json", diagnostics_payload)

    best_dir = candidate_dirs[best_pos_idx, best_layer, :].detach().cpu()
    torch.save(best_dir, output_dir / "direction.pt")

    selected_meta = {
        **base_meta,
        "selection_status": PROVISIONAL_SELECTION,
        "selection_criterion": PROVISIONAL_SELECTION_CRITERION,
        "selected_position_index": best_pos_idx,
        "selected_position": STARTOFTHINK_POSITION_LABEL,
        "selected_layer": best_layer,
        "selected_score": best_score,
        "selected_harmful_projection_mean": selection.selected_harmful_projection_mean,
        "selected_harmless_projection_mean": selection.selected_harmless_projection_mean,
        "direction_norm": float(best_dir.norm()),
        "direction_path": str(output_dir / "direction.pt"),
        "scientific_use_warning": (
            "Provisional: selected by projection diagnostics only. "
            "Run Stage 4A2 intervention-based selection before scientific use."
        ),
    }
    write_json(output_dir / "selected_direction.json", selected_meta)

    write_json(output_dir / "extraction_metrics.json", {
        "n_harmful": len(harmful_prompts),
        "n_harmless": len(harmless_prompts),
        "n_layers": n_layers,
        "d_model": d_model,
        "best_layer": best_layer,
        "best_score": best_score,
    })

    print(
        f"[{STAGE_NAME}] Done. Best layer={best_layer} score={best_score:.4f}. "
        f"Outputs: {output_dir}",
        flush=True,
    )


def main() -> None:
    args = build_parser().parse_args()
    run(args)


if __name__ == "__main__":
    main()
