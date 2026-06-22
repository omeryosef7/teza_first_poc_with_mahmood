from __future__ import annotations

"""
Stage 4A1 — prompt-type vs puzzle: extract refusal direction by contrasting a prompt
type (harmless or direct_harm) against puzzle attack traces.

TWO CONTRASTS (--group-a-type):
  hvp  (harmless vs puzzle)   : Group A = harmless prompts,   Group B = 220 puzzle traces
  dvp  (direct_harm vs puzzle): Group A = raw harmful goals,  Group B = 220 puzzle traces

  For dvp, harmful goals come from --baseline-jsonl (the `goal` field of each entry —
  the SAME 220 harmful goals used in the puzzle attack, expressed without wrapping).
  For hvp, harmless prompts come from the refusal_direction dataset splits.

THREE POSITIONS (--position):
  startofthink  : <think> token — single forward pass, no generation
  endofthink    : </think> token — generation for Group A; Group B from Stage 6 artifacts
  endofresponse : EOS token    — full generation for Group A; Group B from Stage 6 artifacts

DiM = mean(puzzle_activations) − mean(group_a_activations)
  (puzzle is the "intervention" group; direction points FROM group_a TOWARD puzzle)

OUTPUT NAMING:
  outputs/stage4/<model-slug>/refusal_direction_{hvp|dvp}_{position}/
  Compatible with Stage 4A2 subspace selection pipeline.

OUTPUT SCHEMA: identical to existing 4A1 scripts:
  candidate_directions.pt       [1, n_layers, d_model]
  candidate_metadata.json
  projection_diagnostics.json
  direction.pt                  provisional best layer
  selected_direction.json
  extraction_metrics.json
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

import torch

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STAGE_NAME = "stage4a1_ptype_vs_puzzle"
POSITION_LABEL = "ptype_vs_puzzle"
POSITION_VALUE = 0  # schema sentinel (1 position per variant)

_GROUP_A_CHOICES = ["harmless", "direct_harm"]
_POSITION_CHOICES = ["startofthink", "endofthink", "endofresponse"]
DEFAULT_MAX_SEQ_LEN = 30000
DEFAULT_MAX_GEN_TOKENS = 2048
DEFAULT_NUM_GROUP_A = 64   # prompts per group (Group A)
DEFAULT_NUM_PUZZLE = 220   # all puzzle traces used for Group B


# ---------------------------------------------------------------------------
# Baseline JSONL loading (Group A for dvp)
# ---------------------------------------------------------------------------

def load_goals_from_baseline(baseline_jsonl: Path, n: int | None = None, seed: int = 42) -> list[str]:
    """Load raw harmful goals from hijacking baseline JSONL (the `goal` field)."""
    goals: list[str] = []
    with baseline_jsonl.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            goal = entry.get("goal")
            if goal:
                goals.append(str(goal))
    if n is not None:
        rng = random.Random(seed)
        rng.shuffle(goals)
        goals = goals[:n]
    return goals


# ---------------------------------------------------------------------------
# Group B: puzzle trace loading (shared across all positions)
# ---------------------------------------------------------------------------

def load_puzzle_artifacts(stage6_input: Path) -> list[dict[str, Any]]:
    """Load ALL Stage 6 artifact JSON files (no filtering by outcome)."""
    if stage6_input.is_file():
        files = [stage6_input]
    else:
        files = sorted(f for f in stage6_input.glob("*.json")
                       if not f.name.startswith("batch_summary"))
    artifacts = []
    for path in files:
        try:
            with path.open("r", encoding="utf-8") as fh:
                art = json.load(fh)
            art["_source_path"] = str(path)
            artifacts.append(art)
        except Exception as exc:
            print(f"[{STAGE_NAME}] WARNING: failed to read {path}: {exc}", flush=True)
    return artifacts


# ---------------------------------------------------------------------------
# Group B captures at each position
# ---------------------------------------------------------------------------

def capture_puzzle_startofthink(
    model_base: Any,
    artifacts: list[dict[str, Any]],
    *,
    think_start_token_id: int,
    progress_enabled: bool,
    batch_size: int = 32,
) -> tuple[torch.Tensor, int]:
    """
    For each artifact, use prompt_token_ids + append <think> token, then run a batched
    forward pass with left-padding (same trick as extract_refusal_direction_startofthink).
    Returns: [n_valid, 1, n_layers, d_model], n_skipped
    """
    from poc_stage4.run_state import log_progress

    layers = model_base.layers
    n_layers = model_base.num_layers
    d_model = model_base.hidden_size
    try:
        input_device = model_base.model.get_input_embeddings().weight.device
    except Exception:
        input_device = next(model_base.model.parameters()).device

    pad_token_id = model_base.tokenizer.pad_token_id or 0
    think_id = torch.tensor([think_start_token_id], dtype=torch.long)

    all_input_ids: list[torch.Tensor] = []
    skipped = 0
    for art in artifacts:
        raw_ids = art.get("prompt_token_ids")
        if not raw_ids:
            skipped += 1
            continue
        ids = torch.tensor(raw_ids, dtype=torch.long)
        all_input_ids.append(torch.cat([ids, think_id], dim=0))

    if not all_input_ids:
        raise RuntimeError("No puzzle artifacts had prompt_token_ids for startofthink extraction.")

    log_progress(STAGE_NAME, f"puzzle_startofthink: {len(all_input_ids)} sequences (skipped={skipped})",
                 enabled=progress_enabled)

    all_activations: list[torch.Tensor] = []
    n_batches = (len(all_input_ids) + batch_size - 1) // batch_size
    t0 = time.time()

    for bi in range(n_batches):
        start = bi * batch_size
        end = min(start + batch_size, len(all_input_ids))
        batch_ids = all_input_ids[start:end]
        bs = len(batch_ids)

        max_len = max(ids.shape[0] for ids in batch_ids)
        padded = torch.full((bs, max_len), pad_token_id, dtype=torch.long)
        for i, ids in enumerate(batch_ids):
            padded[i, max_len - ids.shape[0]:] = ids
        attention_mask = (padded != pad_token_id).long()
        think_pos = max_len - 1

        # Explicit position_ids for Flash Attention 2 compatibility
        position_ids = attention_mask.long().cumsum(dim=-1) - 1
        position_ids.masked_fill_(attention_mask == 0, 1)

        batch_cache = torch.zeros((bs, n_layers, d_model), dtype=torch.float32)
        hooks = []

        def _make_hook(li: int):
            def _hook(module: Any, hook_input: Any) -> None:
                act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
                batch_cache[:, li, :] = act[:, think_pos, :].detach().float().cpu()
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

        all_activations.append(batch_cache.unsqueeze(1))  # [bs, 1, n_layers, d_model]
        log_progress(STAGE_NAME,
                     f"puzzle_startofthink batch {bi+1}/{n_batches} "
                     f"examples {start+1}-{end}/{len(all_input_ids)} elapsed={time.time()-t0:.1f}s",
                     enabled=progress_enabled)

    return torch.cat(all_activations, dim=0), skipped


# ---------------------------------------------------------------------------
# Group A captures at startofthink (reuse existing function)
# ---------------------------------------------------------------------------

def capture_group_a_startofthink(
    model_base: Any,
    prompts: list[str],
    *,
    think_start_token_id: int,
    progress_enabled: bool,
    group_label: str,
) -> torch.Tensor:
    """Capture Group A activations at startofthink (reuses existing batched forward pass)."""
    from poc_stage4.extract_refusal_direction_startofthink import capture_startofthink_activations
    return capture_startofthink_activations(
        model_base, prompts,
        think_start_token_id=think_start_token_id,
        progress_enabled=progress_enabled,
        stage_name=STAGE_NAME,
        group_label=group_label,
    )


# ---------------------------------------------------------------------------
# Group A captures at endofresponse (generate full response, extract EOS)
# ---------------------------------------------------------------------------

def generate_and_capture_endofresponse_activations(
    model_base: Any,
    prompts: list[str],
    *,
    eos_token_ids: list[int],
    max_generation_tokens: int,
    max_seq_len: int,
    progress_enabled: bool,
    group_label: str,
    checkpoint_dir: Path | None = None,
    resume: bool = False,
) -> tuple[torch.Tensor, list[int | None], list[str]]:
    """
    For each prompt: generate full response (thinking + answer), find EOS in output,
    run forward pass on full sequence, capture residual stream at EOS for every layer.

    Returns: activations [n_valid, 1, n_layers, d_model], eos_positions, skipped_prompts
    """
    from poc_stage4.run_state import log_progress, progress_iter

    layers = model_base.layers
    n_layers = model_base.num_layers
    d_model = model_base.hidden_size
    try:
        input_device = model_base.model.get_input_embeddings().weight.device
    except Exception:
        input_device = next(model_base.model.parameters()).device

    ckpt_sub: Path | None = None
    if checkpoint_dir is not None:
        ckpt_sub = checkpoint_dir / group_label
        ckpt_sub.mkdir(parents=True, exist_ok=True)

    all_valid: list[torch.Tensor] = []
    eos_positions: list[int | None] = []
    skipped_prompts: list[str] = []

    for idx, prompt in enumerate(progress_iter(
        prompts, total=len(prompts), desc=f"endofresponse [{group_label}]",
        enabled=progress_enabled,
    )):
        # Resume: load checkpoint if available
        if ckpt_sub is not None and resume:
            meta_path = ckpt_sub / f"{idx:05d}_meta.json"
            act_path = ckpt_sub / f"{idx:05d}_act.pt"
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                if meta.get("skipped"):
                    eos_positions.append(None)
                    skipped_prompts.append(prompt)
                    continue
                elif act_path.exists():
                    all_valid.append(torch.load(act_path, map_location="cpu", weights_only=True))
                    eos_positions.append(meta["eos_pos"])
                    continue

        # Format + tokenize
        formatted = model_base.format_prompts([prompt], enable_thinking=True)[0]
        prompt_ids = model_base.tokenizer(
            formatted, return_tensors="pt", padding=False, truncation=False,
        ).input_ids[0].tolist()

        # Generate full response
        log_progress(STAGE_NAME, f"[{group_label}] generating {idx+1}/{len(prompts)}",
                     enabled=progress_enabled)
        with torch.no_grad():
            out = model_base.model.generate(
                torch.tensor(prompt_ids, dtype=torch.long).unsqueeze(0).to(input_device),
                max_new_tokens=max_generation_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=model_base.tokenizer.eos_token_id,
            )
        full_ids: list[int] = out[0].tolist()

        if len(full_ids) > max_seq_len:
            log_progress(STAGE_NAME, f"[{group_label}] skipping: seq_len={len(full_ids)} > {max_seq_len}",
                         enabled=progress_enabled)
            eos_positions.append(None)
            skipped_prompts.append(prompt)
            if ckpt_sub:
                (ckpt_sub / f"{idx:05d}_meta.json").write_text(json.dumps({"skipped": True, "idx": idx}))
            continue

        # Find EOS in generated portion
        eos_pos: int | None = None
        for eos_id in eos_token_ids:
            for j in range(len(full_ids) - 1, len(prompt_ids) - 1, -1):
                if full_ids[j] == eos_id:
                    eos_pos = j
                    break
            if eos_pos is not None:
                break
        if eos_pos is None:
            # Fallback: use last token
            eos_pos = len(full_ids) - 1

        log_progress(STAGE_NAME, f"[{group_label}] eos_pos={eos_pos} seq_len={len(full_ids)}",
                     enabled=progress_enabled)

        # Forward pass on full sequence, capture at eos_pos
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

        act_tensor = layer_cache.unsqueeze(0)  # [1, n_layers, d_model]
        all_valid.append(act_tensor.clone())
        eos_positions.append(eos_pos)

        if ckpt_sub:
            torch.save(act_tensor, ckpt_sub / f"{idx:05d}_act.pt")
            (ckpt_sub / f"{idx:05d}_meta.json").write_text(
                json.dumps({"skipped": False, "idx": idx, "eos_pos": eos_pos})
            )
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not all_valid:
        raise RuntimeError(
            f"No prompts in group '{group_label}' yielded a valid EOS activation. "
            "Check model generation and EOS token IDs."
        )
    return torch.stack(all_valid, dim=0), eos_positions, skipped_prompts


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def run_extraction(
    *,
    model_name: str,
    model_family: str,
    stage6_input: Path,
    baseline_jsonl: Path,
    group_a_type: str,          # "harmless" or "direct_harm"
    position: str,              # "startofthink" | "endofthink" | "endofresponse"
    output_dir: Path,
    num_group_a: int,
    max_generation_tokens: int,
    max_seq_len: int,
    seed: int,
    overwrite: bool,
    resume: bool,
    direction_normalization: str,
    no_progress: bool,
    dry_run: bool,
    puzzle_batch_size: int = 32,
) -> dict[str, Any]:
    from poc_stage4.candidate_directions import generate_candidate_directions
    from poc_stage4.extract_refusal_direction_behavioral import (
        capture_endthink_activations_from_artifacts,
    )
    from poc_stage4.extract_refusal_direction_endofresponse import (
        capture_endofresponse_activations_from_artifacts,
    )
    from poc_stage4.extract_refusal_direction_endofthink import (
        ENDOFTHINK_POSITION_VALUE,
        OUTPUT_FILENAMES,
        _check_outputs,
        generate_and_capture_endthink_activations,
    )
    from poc_stage4.model_family_utils import (
        DEFAULT_MODEL_BY_FAMILY,
        DEFAULT_MODEL_SLUG_BY_FAMILY,
        get_thinking_end_token_ids,
        get_thinking_start_token_ids,
        load_model_by_family,
    )
    from poc_stage4.projection_diagnostics import (
        compute_projection_diagnostics,
        summarize_diagnostics,
    )
    from poc_stage4.run_state import log_progress
    from poc_stage4.schemas import (
        PROVISIONAL_SELECTION,
        PROVISIONAL_SELECTION_CRITERION,
        STAGE4A1_ARTIFACT_VERSION,
        utc_now,
        write_json,
    )

    progress_enabled = not no_progress
    variant_name = "hvp" if group_a_type == "harmless" else "dvp"
    full_variant = f"{variant_name}_{position}"

    if not resume:
        _check_outputs(output_dir, overwrite=overwrite)
    output_dir.mkdir(parents=True, exist_ok=True)

    ckpt_dir = output_dir / "checkpoints" / position
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    log_progress(STAGE_NAME, f"Starting {full_variant} extraction", enabled=progress_enabled,
                 group_a_type=group_a_type, position=position)

    # --- Load model ---
    log_progress(STAGE_NAME, f"Loading {model_name}", enabled=progress_enabled)
    model_base = load_model_by_family(model_name, model_family)
    n_layers = model_base.num_layers
    d_model = model_base.hidden_size

    # --- Load Group B: puzzle traces ---
    if not stage6_input.exists():
        raise FileNotFoundError(f"--stage6-input does not exist: {stage6_input}")
    puzzle_artifacts = load_puzzle_artifacts(stage6_input)
    if dry_run:
        puzzle_artifacts = puzzle_artifacts[:4]
    log_progress(STAGE_NAME, f"Loaded {len(puzzle_artifacts)} puzzle artifacts", enabled=progress_enabled)

    # --- Load Group A prompts ---
    if group_a_type == "harmless":
        from poc_stage4.default_prompts import load_prompt_sets
        effective_n = 4 if dry_run else num_group_a
        _, group_a_prompts, _ = load_prompt_sets(
            num_harmful=effective_n,
            num_harmless=effective_n,
            seed=seed,
        )
        group_a_prompts = group_a_prompts[:effective_n]
        group_a_source = "harmless_train.json (refusal_direction dataset)"
    else:  # direct_harm
        if not baseline_jsonl.exists():
            raise FileNotFoundError(f"--baseline-jsonl does not exist: {baseline_jsonl}")
        effective_n = 4 if dry_run else num_group_a
        group_a_prompts = load_goals_from_baseline(baseline_jsonl, n=effective_n, seed=seed)
        group_a_source = str(baseline_jsonl)

    log_progress(STAGE_NAME, f"Group A ({group_a_type}): {len(group_a_prompts)} prompts",
                 enabled=progress_enabled)

    # Train/val split for Group A (75/25)
    rng = random.Random(seed)
    group_a_shuf = list(group_a_prompts)
    rng.shuffle(group_a_shuf)
    n_val_a = max(1, len(group_a_shuf) // 4)
    group_a_train = group_a_shuf[n_val_a:]
    group_a_val = group_a_shuf[:n_val_a]

    # Train/val split for Group B: puzzle artifacts (75/25)
    puzzle_shuf = list(puzzle_artifacts)
    rng.shuffle(puzzle_shuf)
    n_val_b = max(1, len(puzzle_shuf) // 4)
    puzzle_train = puzzle_shuf[n_val_b:]
    puzzle_val = puzzle_shuf[:n_val_b]

    log_progress(STAGE_NAME,
                 f"Splits — puzzle: train={len(puzzle_train)} val={len(puzzle_val)} | "
                 f"group_a: train={len(group_a_train)} val={len(group_a_val)}",
                 enabled=progress_enabled)

    # ==========================================================================
    # Capture activations at the chosen position
    # ==========================================================================

    if position == "startofthink":
        think_start_ids = get_thinking_start_token_ids(model_base.tokenizer, model_family)
        if not think_start_ids:
            raise ValueError("Could not find thinking-start token IDs for this model family.")
        think_start_token_id = think_start_ids[-1]
        log_progress(STAGE_NAME, f"<think> token id={think_start_token_id}", enabled=progress_enabled)

        log_progress(STAGE_NAME, "Capturing puzzle_train startofthink activations", enabled=progress_enabled)
        puzzle_train_acts, _ = capture_puzzle_startofthink(
            model_base, puzzle_train,
            think_start_token_id=think_start_token_id,
            progress_enabled=progress_enabled,
            batch_size=puzzle_batch_size,
        )

        log_progress(STAGE_NAME, f"Capturing group_a_train ({group_a_type}) startofthink activations",
                     enabled=progress_enabled)
        group_a_train_acts = capture_group_a_startofthink(
            model_base, group_a_train,
            think_start_token_id=think_start_token_id,
            progress_enabled=progress_enabled,
            group_label=f"group_a_train_{group_a_type}",
        )

        log_progress(STAGE_NAME, "Capturing puzzle_val startofthink activations", enabled=progress_enabled)
        puzzle_val_acts, _ = capture_puzzle_startofthink(
            model_base, puzzle_val,
            think_start_token_id=think_start_token_id,
            progress_enabled=progress_enabled,
            batch_size=puzzle_batch_size,
        )

        log_progress(STAGE_NAME, f"Capturing group_a_val ({group_a_type}) startofthink activations",
                     enabled=progress_enabled)
        group_a_val_acts = capture_group_a_startofthink(
            model_base, group_a_val,
            think_start_token_id=think_start_token_id,
            progress_enabled=progress_enabled,
            group_label=f"group_a_val_{group_a_type}",
        )
        extra_meta: dict[str, Any] = {"think_start_token_id": think_start_token_id}

    elif position == "endofthink":
        endthink_ids = get_thinking_end_token_ids(model_base.tokenizer, model_family)
        log_progress(STAGE_NAME, f"</think> token ids={endthink_ids}", enabled=progress_enabled)

        log_progress(STAGE_NAME, "Capturing puzzle_train endofthink activations (from artifacts)",
                     enabled=progress_enabled)
        puzzle_train_acts, _, _ = capture_endthink_activations_from_artifacts(
            model_base, puzzle_train,
            endthink_token_ids=endthink_ids,
            group_label="puzzle_train",
            progress_enabled=progress_enabled,
            max_seq_len=max_seq_len,
        )

        log_progress(STAGE_NAME, f"Generating + capturing group_a_train ({group_a_type}) endofthink",
                     enabled=progress_enabled)
        group_a_train_acts, _, _ = generate_and_capture_endthink_activations(
            model_base, group_a_train,
            endthink_token_ids=endthink_ids,
            max_generation_tokens=max_generation_tokens,
            progress_enabled=progress_enabled,
            stage_name=STAGE_NAME,
            checkpoint_dir=ckpt_dir,
            group_label=f"group_a_train_{group_a_type}",
            resume=resume,
        )

        log_progress(STAGE_NAME, "Capturing puzzle_val endofthink activations", enabled=progress_enabled)
        puzzle_val_acts, _, _ = capture_endthink_activations_from_artifacts(
            model_base, puzzle_val,
            endthink_token_ids=endthink_ids,
            group_label="puzzle_val",
            progress_enabled=progress_enabled,
            max_seq_len=max_seq_len,
        )

        log_progress(STAGE_NAME, f"Generating + capturing group_a_val ({group_a_type}) endofthink",
                     enabled=progress_enabled)
        group_a_val_acts, _, _ = generate_and_capture_endthink_activations(
            model_base, group_a_val,
            endthink_token_ids=endthink_ids,
            max_generation_tokens=max_generation_tokens,
            progress_enabled=progress_enabled,
            stage_name=STAGE_NAME,
            checkpoint_dir=ckpt_dir,
            group_label=f"group_a_val_{group_a_type}",
            resume=resume,
        )
        extra_meta = {"endthink_token_ids": endthink_ids}

    elif position == "endofresponse":
        # Get EOS token IDs from generation_config
        try:
            gc_eos = model_base.model.generation_config.eos_token_id
            eos_ids = gc_eos if isinstance(gc_eos, list) else [gc_eos]
        except Exception:
            eos_ids = [model_base.tokenizer.eos_token_id]
        eos_ids = [e for e in eos_ids if e is not None]
        if not eos_ids:
            eos_ids = [model_base.tokenizer.eos_token_id]
        log_progress(STAGE_NAME, f"EOS token ids={eos_ids}", enabled=progress_enabled)

        log_progress(STAGE_NAME, "Capturing puzzle_train endofresponse activations (from artifacts)",
                     enabled=progress_enabled)
        puzzle_train_acts, _, _ = capture_endofresponse_activations_from_artifacts(
            model_base, puzzle_train,
            group_label="puzzle_train",
            progress_enabled=progress_enabled,
            max_seq_len=max_seq_len,
        )

        log_progress(STAGE_NAME,
                     f"Generating + capturing group_a_train ({group_a_type}) endofresponse",
                     enabled=progress_enabled)
        group_a_train_acts, _, _ = generate_and_capture_endofresponse_activations(
            model_base, group_a_train,
            eos_token_ids=eos_ids,
            max_generation_tokens=max_generation_tokens,
            max_seq_len=max_seq_len,
            progress_enabled=progress_enabled,
            group_label=f"group_a_train_{group_a_type}",
            checkpoint_dir=ckpt_dir,
            resume=resume,
        )

        log_progress(STAGE_NAME, "Capturing puzzle_val endofresponse activations", enabled=progress_enabled)
        puzzle_val_acts, _, _ = capture_endofresponse_activations_from_artifacts(
            model_base, puzzle_val,
            group_label="puzzle_val",
            progress_enabled=progress_enabled,
            max_seq_len=max_seq_len,
        )

        log_progress(STAGE_NAME,
                     f"Generating + capturing group_a_val ({group_a_type}) endofresponse",
                     enabled=progress_enabled)
        group_a_val_acts, _, _ = generate_and_capture_endofresponse_activations(
            model_base, group_a_val,
            eos_token_ids=eos_ids,
            max_generation_tokens=max_generation_tokens,
            max_seq_len=max_seq_len,
            progress_enabled=progress_enabled,
            group_label=f"group_a_val_{group_a_type}",
            checkpoint_dir=ckpt_dir,
            resume=resume,
        )
        extra_meta = {"eos_token_ids": eos_ids}

    else:
        raise ValueError(f"Unknown position: {position!r}")

    # ==========================================================================
    # Compute DiM = mean(puzzle) - mean(group_a)
    # ==========================================================================
    n_train = min(puzzle_train_acts.shape[0], group_a_train_acts.shape[0])
    if n_train == 0:
        raise RuntimeError("No valid training activations after filtering.")
    puzzle_train_acts = puzzle_train_acts[:n_train]
    group_a_train_acts = group_a_train_acts[:n_train]

    log_progress(STAGE_NAME, f"Computing DiM from {n_train} train pairs", enabled=progress_enabled)
    # DiM: puzzle is group A in generate_candidate_directions convention
    # (first arg − second arg = mean(puzzle) − mean(group_a))
    candidate_directions = generate_candidate_directions(
        puzzle_train_acts,
        group_a_train_acts,
        direction_normalization=direction_normalization,
    )  # [1, n_layers, d_model]

    torch.save(candidate_directions.cpu(), output_dir / "candidate_directions.pt")
    log_progress(STAGE_NAME, f"Saved candidate_directions.pt shape={list(candidate_directions.shape)}",
                 enabled=progress_enabled)

    # Diagnostics on val set
    n_val = min(puzzle_val_acts.shape[0], group_a_val_acts.shape[0])
    puzzle_val_acts = puzzle_val_acts[:n_val]
    group_a_val_acts = group_a_val_acts[:n_val]

    log_progress(STAGE_NAME, f"Computing projection diagnostics on {n_val} val pairs",
                 enabled=progress_enabled)
    diagnostic_rows, selection = compute_projection_diagnostics(
        candidate_directions,
        puzzle_val_acts,
        group_a_val_acts,
        positions=[POSITION_VALUE],
    )

    # ==========================================================================
    # Save outputs
    # ==========================================================================
    timestamp_utc = utc_now()
    base_meta: dict[str, Any] = {
        "artifact_version": STAGE4A1_ARTIFACT_VERSION,
        "stage": f"stage4a1_{full_variant}_candidate_refusal_direction_extraction",
        "source_variant": f"extract_refusal_direction_ptype_vs_puzzle",
        "full_variant": full_variant,
        "timestamp_utc": timestamp_utc,
        "model_name": model_name,
        "model_family": model_family,
        "contrast_set": f"{variant_name}_puzzle_vs_{group_a_type}",
        "group_a_type": group_a_type,
        "group_a_source": group_a_source,
        "group_b_type": "puzzle",
        "group_b_source": str(stage6_input),
        "extraction_position": position,
        "contrast_set_notes": (
            f"DiM = mean(puzzle_at_{position}) − mean({group_a_type}_at_{position}). "
            f"Puzzle group: all {len(puzzle_artifacts)} Stage 6 attack traces. "
            f"Group A ({group_a_type}): {len(group_a_prompts)} prompts. "
            "Direction points FROM group_a TOWARD puzzle."
        ),
        "num_puzzle_artifacts": len(puzzle_artifacts),
        "num_group_a_prompts": len(group_a_prompts),
        "num_group_a_train": len(group_a_train),
        "num_group_a_val": len(group_a_val),
        "num_puzzle_train": len(puzzle_train),
        "num_puzzle_val": len(puzzle_val),
        "num_train_pairs_used_for_dim": n_train,
        "num_val_pairs_used_for_diagnostics": n_val,
        "positions": [POSITION_VALUE],
        "token_position_semantics": position,
        "layers": list(range(n_layers)),
        "num_layers": n_layers,
        "hidden_size": d_model,
        "candidate_tensor_shape": list(candidate_directions.shape),
        "direction_normalization": direction_normalization,
        "max_generation_tokens": max_generation_tokens,
        "max_seq_len": max_seq_len,
        "seed": seed,
        "dry_run": dry_run,
        **extra_meta,
    }

    write_json(output_dir / "candidate_metadata.json", base_meta)
    write_json(output_dir / "projection_diagnostics.json", {
        **base_meta,
        "selection_status": PROVISIONAL_SELECTION,
        "selection_criterion": PROVISIONAL_SELECTION_CRITERION,
        "diagnostic_summary": summarize_diagnostics(diagnostic_rows),
        "diagnostics": diagnostic_rows,
    })

    best_pos_idx = selection.selected_position_index
    best_layer = selection.selected_layer
    best_score = selection.selected_score
    best_dir = candidate_directions[best_pos_idx, best_layer, :].detach().cpu()
    torch.save(best_dir, output_dir / "direction.pt")

    write_json(output_dir / "selected_direction.json", {
        **base_meta,
        "selection_status": PROVISIONAL_SELECTION,
        "selection_criterion": PROVISIONAL_SELECTION_CRITERION,
        "selected_position_index": best_pos_idx,
        "selected_position": position,
        "selected_layer": best_layer,
        "selected_score": best_score,
        "selected_puzzle_projection_mean": selection.selected_harmful_projection_mean,
        "selected_group_a_projection_mean": selection.selected_harmless_projection_mean,
        "direction_norm": float(best_dir.norm()),
        "direction_path": str(output_dir / "direction.pt"),
        "scientific_use_warning": (
            "Provisional: selected by projection diagnostics only. "
            "Run Stage 4A2 with --subspace-method pca before scientific use."
        ),
    })

    metrics: dict[str, Any] = {
        **base_meta,
        "best_layer": best_layer,
        "best_score": best_score,
        "max_standardized_projection_separation": best_score,
        "diagnostic_summary": summarize_diagnostics(diagnostic_rows),
    }
    write_json(output_dir / "extraction_metrics.json", metrics)

    log_progress(STAGE_NAME, f"Done. best_layer={best_layer} sep={best_score:.4f} → {output_dir}",
                 enabled=progress_enabled)
    return metrics


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Stage 4A1 ptype_vs_puzzle: extract refusal direction contrasting a prompt type "
            "(harmless or direct_harm) against puzzle attack traces at one of three positions."
        )
    )
    p.add_argument("--model-family", default="qwen3", choices=["qwen3", "gemma4"])
    p.add_argument("--model-name", default=None)
    p.add_argument(
        "--stage6-input", required=True,
        help="Directory of Stage 6 trace JSON artifacts (Group B: puzzle traces).",
    )
    p.add_argument(
        "--baseline-jsonl", default=None,
        help=(
            "Path to hijacking_baseline JSONL for dvp. "
            "The `goal` field of each entry is used as the direct_harm prompt. "
            "Required when --group-a-type=direct_harm."
        ),
    )
    p.add_argument(
        "--group-a-type", required=True, choices=_GROUP_A_CHOICES,
        help="Prompt type for Group A: 'harmless' or 'direct_harm'.",
    )
    p.add_argument(
        "--position", required=True, choices=_POSITION_CHOICES,
        help="Token position for extraction: startofthink | endofthink | endofresponse.",
    )
    p.add_argument("--output-dir", default=None)
    p.add_argument("--num-group-a", type=int, default=DEFAULT_NUM_GROUP_A,
                   help=f"Number of Group A prompts. Default: {DEFAULT_NUM_GROUP_A}.")
    p.add_argument("--max-generation-tokens", type=int, default=DEFAULT_MAX_GEN_TOKENS)
    p.add_argument("--max-seq-len", type=int, default=DEFAULT_MAX_SEQ_LEN)
    p.add_argument("--puzzle-batch-size", type=int, default=32,
                   help="Batch size for puzzle-trace startofthink forward pass. "
                        "Reduce (e.g. 4) for models that OOM on the default of 32.")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--direction-normalization", choices=("unit", "raw"), default="unit")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--no-progress", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()

    from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY, DEFAULT_MODEL_SLUG_BY_FAMILY

    model_family: str = args.model_family
    model_name = args.model_name or DEFAULT_MODEL_BY_FAMILY[model_family]
    model_slug = DEFAULT_MODEL_SLUG_BY_FAMILY[model_family]

    group_a_type: str = args.group_a_type
    position: str = args.position
    variant_name = "hvp" if group_a_type == "harmless" else "dvp"
    full_variant = f"{variant_name}_{position}"

    output_dir = Path(
        args.output_dir
        or f"outputs/stage4/{model_slug}/refusal_direction_{full_variant}"
    )

    baseline_jsonl = Path(args.baseline_jsonl) if args.baseline_jsonl else None
    if group_a_type == "direct_harm" and baseline_jsonl is None:
        print(
            "ERROR: --baseline-jsonl is required when --group-a-type=direct_harm",
            file=sys.stderr,
        )
        return 1

    try:
        run_extraction(
            model_name=model_name,
            model_family=model_family,
            stage6_input=Path(args.stage6_input),
            baseline_jsonl=baseline_jsonl or Path("/dev/null"),
            group_a_type=group_a_type,
            position=position,
            output_dir=output_dir,
            num_group_a=args.num_group_a,
            max_generation_tokens=args.max_generation_tokens,
            max_seq_len=args.max_seq_len,
            seed=args.seed,
            overwrite=args.overwrite,
            resume=args.resume,
            direction_normalization=args.direction_normalization,
            no_progress=args.no_progress,
            dry_run=args.dry_run,
            puzzle_batch_size=args.puzzle_batch_size,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

    print(f"[{STAGE_NAME}] Done — outputs in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
