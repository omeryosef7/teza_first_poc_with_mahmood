"""
Main GCG optimization loop for Stage GCG-Early.

Implements the coordinate gradient optimizer from Zou et al. (2023) with
additional representation-distance and early-logit-KL objectives.

The mathematical core (token_gradients, sample_control) is re-implemented
here to use our model-family-aware embedding access (model_adapter.py)
instead of the vendor's Llama-specific llm_attacks.get_embedding_matrix.

Full resume support:
  - checkpoint.pt stores: step, suffix_ids, all three RNG states, config_hash
  - Written atomically (temp file + os.replace) every checkpoint_every steps
  - On SIGTERM: checkpoint is written then exit(0)
  - On startup: if checkpoint.pt exists and config_hash matches, resume from step N

Logging:
  - ITERATION_LOG.jsonl: one line per step, all loss components separately
  - PARETO_CANDIDATES.jsonl: append-mode, all Pareto-dominant candidates
  - checkpoint_step_N.pt: permanent trajectory snapshots every snapshot_every steps
"""
from __future__ import annotations

import gc
import json
import os
import random
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.config import RunConfig, SurrogateTask
from poc_stage_gcg_early.model_adapter import (
    get_embedding_matrix,
    get_embeddings,
)
from poc_stage_gcg_early.objectives import composite_loss, task_loss
from poc_stage_gcg_early.reference_cache import ReferenceCache
from poc_stage_gcg_early.suffix_token_manager import (
    SuffixSpans,
    build_suffix_spans,
    get_filtered_cands,
    make_init_suffix,
    replace_suffix,
)


# ---------------------------------------------------------------------------
# Gradient computation (re-implementation of GCG token_gradients)
# ---------------------------------------------------------------------------

def _token_gradients(
    model: Any,
    model_family: str,
    input_ids: torch.Tensor,
    suffix_slice: slice,
    target_slice: slice,
    loss_slice: slice,
    lambda_repr: float = 0.0,
    reference_hs: Optional[Dict] = None,
    repr_layers: Optional[List[int]] = None,
    repr_positions: Optional[List[int]] = None,
    repr_metric: str = "cosine",
) -> torch.Tensor:
    """
    Compute gradients of the composite loss w.r.t. suffix token one-hot embeddings.

    When lambda_repr > 0 and reference_hs is provided, the gradient includes a
    representation-distance term from output_hidden_states=True (required because
    hook-based capture cannot propagate gradients through the computation graph).

    Returns Tensor[suffix_len, vocab_size]: gradient for each suffix position
    over the vocabulary (normalized by row norm, matching minimal_gcg convention).
    """
    from poc_stage_gcg_early.objectives import repr_loss as _repr_loss_fn

    embed_weights = get_embedding_matrix(model, model_family)  # [vocab, d_model]
    device = model.device if hasattr(model, "device") else next(model.parameters()).device

    suffix_ids = input_ids[suffix_slice]  # [suffix_len]
    one_hot = torch.zeros(
        len(suffix_ids),
        embed_weights.shape[0],
        device=device,
        dtype=embed_weights.dtype,
    )
    one_hot.scatter_(
        1,
        suffix_ids.unsqueeze(1).to(device),
        torch.ones(len(suffix_ids), 1, device=device, dtype=embed_weights.dtype),
    )
    one_hot.requires_grad_()
    input_embeds = (one_hot @ embed_weights).unsqueeze(0)  # [1, suffix_len, d_model]

    # Stitch together: prefix | suffix_embeds | rest
    full_embeds = get_embeddings(model, input_ids.unsqueeze(0).to(device), model_family).detach()
    combined = torch.cat(
        [
            full_embeds[:, : suffix_slice.start, :],
            input_embeds,
            full_embeds[:, suffix_slice.stop :, :],
        ],
        dim=1,
    )

    use_repr = (
        lambda_repr > 0.0
        and reference_hs is not None
        and repr_layers
        and repr_positions
    )

    if use_repr:
        # output_hidden_states=True so gradients flow through repr_loss → one_hot
        output = model(inputs_embeds=combined, output_hidden_states=True)
        logits = output.logits  # [1, seq_len, vocab]
        # Extract candidate hidden states (retain grad — they're on the comp graph via combined)
        cand_hs: Dict[int, Dict[int, torch.Tensor]] = {}
        for layer_idx in repr_layers:
            if layer_idx < len(output.hidden_states):
                lt = output.hidden_states[layer_idx]  # [1, seq_len, d_model]
                cand_hs[layer_idx] = {
                    pos: lt[0, pos, :]
                    for pos in repr_positions
                    if pos < lt.shape[1]
                }
        r_loss = _repr_loss_fn(
            cand_hs, reference_hs,
            layers=repr_layers,
            positions=repr_positions,
            metric=repr_metric,
        )
        targets = input_ids[target_slice].to(device)
        t_loss = nn.CrossEntropyLoss()(logits[0, loss_slice, :], targets)
        loss = t_loss + lambda_repr * r_loss
    else:
        logits = model(inputs_embeds=combined).logits  # [1, seq_len, vocab]
        targets = input_ids[target_slice].to(device)
        loss = nn.CrossEntropyLoss()(logits[0, loss_slice, :], targets)

    loss.backward()

    grad = one_hot.grad.clone()
    grad = grad / (grad.norm(dim=-1, keepdim=True) + 1e-8)
    return grad  # [suffix_len, vocab]


# ---------------------------------------------------------------------------
# Candidate sampling (reused from GCG minimal)
# ---------------------------------------------------------------------------

def _sample_control(
    control_toks: torch.Tensor,
    grad: torch.Tensor,
    batch_size: int,
    topk: int = 256,
    not_allowed_tokens: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """
    Sample batch_size candidate suffix replacements.

    Returns Tensor[batch_size, suffix_len] of candidate token IDs.
    Mathematically identical to llm_attacks.minimal_gcg.opt_utils.sample_control.
    """
    if not_allowed_tokens is not None:
        grad[:, not_allowed_tokens.to(grad.device)] = float("inf")

    top_indices = (-grad).topk(topk, dim=1).indices  # [suffix_len, topk]
    control_toks = control_toks.to(grad.device)

    original_control_toks = control_toks.repeat(batch_size, 1)  # [batch, suffix_len]
    new_token_pos = torch.arange(
        0,
        len(control_toks),
        len(control_toks) / batch_size,
        device=grad.device,
    ).long()
    new_token_val = torch.gather(
        top_indices[new_token_pos], 1,
        torch.randint(0, topk, (batch_size, 1), device=grad.device),
    )
    new_control_toks = original_control_toks.scatter_(
        1, new_token_pos.unsqueeze(-1), new_token_val
    )
    return new_control_toks  # [batch, suffix_len]


# ---------------------------------------------------------------------------
# Candidate evaluation (mini-batched forward passes)
# ---------------------------------------------------------------------------

def _evaluate_candidates(
    model: Any,
    model_family: str,
    base_spans: SuffixSpans,
    candidate_suffix_lists: List[List[int]],
    eval_batch_size: int,
    config: RunConfig,
    reference_hs_per_task: Optional[Dict] = None,
    reference_logits_per_task: Optional[Dict] = None,
) -> List[Dict]:
    """
    Evaluate all candidate suffixes and return per-candidate loss dicts.

    Each result dict has keys: task_loss, repr_loss, kl_loss, reg_loss, total_loss.
    Never logs only the sum — all components are returned.
    """
    device = next(model.parameters()).device
    results = []

    for i in range(0, len(candidate_suffix_lists), eval_batch_size):
        batch_cands = candidate_suffix_lists[i : i + eval_batch_size]
        batch_ids = []
        for cand_ids in batch_cands:
            new_spans = replace_suffix(base_spans, torch.tensor(cand_ids))
            batch_ids.append(new_spans.input_ids)

        # Pad to equal length (should be equal since suffix_len is fixed)
        batch_tensor = torch.stack(batch_ids).to(device)
        attn_mask = torch.ones_like(batch_tensor)

        with torch.no_grad():
            logits = model(
                input_ids=batch_tensor,
                attention_mask=attn_mask,
            ).logits  # [batch, seq_len, vocab]

        for j, cand_ids in enumerate(batch_cands):
            losses = composite_loss(
                logits=logits[j],
                ids=batch_tensor[j],
                loss_slice=base_spans.loss_slice,
                target_slice=base_spans.target_slice,
                lambda_repr=config.objective.lambda_repr,
                lambda_kl=config.objective.lambda_kl,
                suffix_ids=torch.tensor(cand_ids),
            )
            results.append({k: v.item() for k, v in losses.items()})

        del batch_tensor, logits
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return results


# ---------------------------------------------------------------------------
# Checkpoint I/O
# ---------------------------------------------------------------------------

def _load_checkpoint(output_dir: Path, config_hash: str) -> Optional[dict]:
    ckpt_path = output_dir / "checkpoint.pt"
    if not ckpt_path.exists():
        return None
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    if ckpt.get("config_hash") != config_hash:
        raise RuntimeError(
            f"Checkpoint config_hash {ckpt.get('config_hash')} does not match "
            f"current config hash {config_hash}. "
            "Delete the checkpoint or use a new output directory."
        )
    return ckpt


def _save_checkpoint(
    output_dir: Path,
    step: int,
    suffix_ids: List[int],
    config_hash: str,
    run_id: str,
) -> None:
    ckpt = {
        "step": step,
        "suffix_ids": suffix_ids,
        "torch_rng_state": torch.random.get_rng_state(),
        "numpy_rng_state": np.random.get_state(),
        "python_rng_state": random.getstate(),
        "config_hash": config_hash,
        "run_id": run_id,
    }
    tmp_path = output_dir / "checkpoint.pt.tmp"
    torch.save(ckpt, tmp_path)
    os.replace(tmp_path, output_dir / "checkpoint.pt")


def _save_snapshot(output_dir: Path, step: int, suffix_ids: List[int], config_hash: str, run_id: str) -> None:
    snap_path = output_dir / f"checkpoint_step_{step}.pt"
    torch.save({"step": step, "suffix_ids": suffix_ids, "config_hash": config_hash, "run_id": run_id}, snap_path)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _append_jsonl(path: Path, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _update_pareto(pareto: List[dict], candidate: dict) -> List[dict]:
    """Return updated Pareto set (minimizing task_loss and repr_loss simultaneously)."""
    dominated = False
    new_pareto = []
    for p in pareto:
        if (p["task_loss"] <= candidate["task_loss"] and
                p["repr_loss"] <= candidate["repr_loss"]):
            dominated = True
            new_pareto.append(p)
        elif (candidate["task_loss"] <= p["task_loss"] and
              candidate["repr_loss"] <= p["repr_loss"]):
            pass  # p is dominated by candidate; drop it
        else:
            new_pareto.append(p)
    if not dominated:
        new_pareto.append(candidate)
    return new_pareto


# ---------------------------------------------------------------------------
# Main optimization loop
# ---------------------------------------------------------------------------

def run_optimization(
    model: Any,
    tokenizer: Any,
    model_family: str,
    tasks: List[SurrogateTask],
    config: RunConfig,
    reference_cache: Optional[ReferenceCache],
    output_dir: Path,
    reference_hs_per_task: Optional[Dict[str, Dict]] = None,
    repr_layers: Optional[List[int]] = None,
) -> None:
    """
    Main GCG optimization loop with full resume support.

    Stages:
      - Stage 3 (task-only):   lambda_repr=0, lambda_kl=0
      - Stage 8  (repr obj):   lambda_repr > 0, reference_hs_per_task provided

    reference_hs_per_task: {task_id: {layer_idx: {pos: fp16 CPU tensor}}}
      Pre-loaded from the reference cache (neutral-suffix hidden states).
      When provided with lambda_repr > 0, repr_loss is added to the gradient and
      logged per step. Selection is still by task_loss (repr_loss logged separately).
    repr_layers: layer indices that are present in reference_hs_per_task.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config_hash = config.config_hash()
    iter_log_path = output_dir / "ITERATION_LOG.jsonl"
    pareto_path = output_dir / "PARETO_CANDIDATES.jsonl"

    # --- Startup: write config (once only) ---
    config_path = output_dir / "CONFIG.json"
    if not config_path.exists():
        config_path.write_text(config.to_json(), encoding="utf-8")

    # --- SIGTERM handler for graceful preemption ---
    _preempted = {"flag": False}
    _current_state = {"step": 0, "suffix_ids": []}

    def _sigterm_handler(signum, frame):
        _preempted["flag"] = True
        step = _current_state["step"]
        suffix_ids = _current_state["suffix_ids"]
        print(f"\n[GCG] SIGTERM received at step {step}. Writing checkpoint and exiting.", flush=True)
        _save_checkpoint(output_dir, step, suffix_ids, config_hash, config.run_id)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _sigterm_handler)

    # --- Load or initialize checkpoint ---
    ckpt = _load_checkpoint(output_dir, config_hash)
    if ckpt is not None:
        start_step = ckpt["step"] + 1
        suffix_ids = ckpt["suffix_ids"]
        torch.random.set_rng_state(ckpt["torch_rng_state"])
        np.random.set_state(ckpt["numpy_rng_state"])
        random.setstate(ckpt["python_rng_state"])
        print(f"[GCG] Resuming from step {ckpt['step']} (suffix length {len(suffix_ids)})", flush=True)
    else:
        start_step = 0
        torch.manual_seed(config.gcg.seed)
        torch.cuda.manual_seed_all(config.gcg.seed)
        np.random.seed(config.gcg.seed)
        random.seed(config.gcg.seed)
        _, suffix_ids = make_init_suffix(config.gcg.suffix_length, tokenizer)
        print(f"[GCG] Starting fresh. suffix_length={config.gcg.suffix_length}", flush=True)

    suffix_str = tokenizer.decode(suffix_ids, skip_special_tokens=True)

    # Use the first train task as the optimization target (multi-task: average gradients)
    train_tasks = [t for t in tasks if t.split == "train"]
    if not train_tasks:
        train_tasks = tasks  # fallback if no split specified

    # Build spans for each task — pass suffix_ids directly to avoid BPE decode→encode mismatch
    task_spans: List[SuffixSpans] = []
    for task in train_tasks:
        spans = build_suffix_spans(
            tokenizer, model_family, config.enable_thinking,
            task.instruction, suffix_str, task.safe_target_prefix,
            suffix_ids_override=suffix_ids,
        )
        task_spans.append(spans)

    pareto_front: List[dict] = []
    device = next(model.parameters()).device

    # Repr-loss config
    use_repr = (
        config.objective.lambda_repr > 0.0
        and reference_hs_per_task is not None
        and repr_layers
    )

    if use_repr:
        # Build per-task repr positions from the suffix span (last N suffix tokens).
        # These positions attend to the full prefix + all suffix tokens → non-zero gradient.
        # Computed from initial suffix (positions don't change since suffix_length is fixed).
        N = config.objective.repr_positions
        repr_pos_per_task: Dict[str, List[int]] = {}
        for task in train_tasks:
            init_spans = build_suffix_spans(
                tokenizer, model_family, config.enable_thinking,
                task.instruction, suffix_str, task.safe_target_prefix,
                suffix_ids_override=suffix_ids,
            )
            repr_pos_per_task[task.task_id] = [
                max(0, init_spans.suffix_slice.stop - N + i) for i in range(N)
            ]
        print(
            f"[GCG] repr_loss ENABLED: lambda_repr={config.objective.lambda_repr}, "
            f"layers={repr_layers}, "
            f"repr_pos_per_task={repr_pos_per_task}, "
            f"tasks_with_cache={sorted(reference_hs_per_task.keys())}",
            flush=True,
        )
    else:
        repr_pos_per_task = {}

    for step in range(start_step, config.gcg.n_steps):
        t_start = time.time()
        _current_state["step"] = step

        # --- Gradient computation (averaged over tasks) ---
        model.zero_grad()
        grad_accum = None
        for task, spans in zip(train_tasks, task_spans):
            # Rebuild spans with current suffix_ids (bypass BPE decode→encode round-trip)
            spans = build_suffix_spans(
                tokenizer, model_family, config.enable_thinking,
                task.instruction, suffix_str, task.safe_target_prefix,
                suffix_ids_override=suffix_ids,
            )
            ref_hs = (reference_hs_per_task or {}).get(task.task_id)
            g = _token_gradients(
                model, model_family,
                spans.input_ids, spans.suffix_slice,
                spans.target_slice, spans.loss_slice,
                lambda_repr=config.objective.lambda_repr,
                reference_hs=ref_hs,
                repr_layers=repr_layers,
                repr_positions=repr_pos_per_task.get(task.task_id, []),
                repr_metric=config.objective.repr_metric,
            )
            if grad_accum is None:
                grad_accum = g
            else:
                grad_accum = grad_accum + g

        if grad_accum is None:
            break
        if len(train_tasks) > 1:
            grad_accum = grad_accum / len(train_tasks)

        # --- Candidate sampling ---
        control_toks = torch.tensor(suffix_ids, device=device)
        candidate_ids = _sample_control(
            control_toks, grad_accum,
            batch_size=config.gcg.batch_size,
            topk=config.gcg.topk,
        )

        # --- Candidate filtering ---
        cand_lists = get_filtered_cands(
            tokenizer, candidate_ids, suffix_ids,
            config.gcg.suffix_length, config.gcg.filter_cand,
        )

        # --- Candidate evaluation (using first train task for selection) ---
        base_spans = build_suffix_spans(
            tokenizer, model_family, config.enable_thinking,
            train_tasks[0].instruction, suffix_str, train_tasks[0].safe_target_prefix,
            suffix_ids_override=suffix_ids,
        )
        eval_results = _evaluate_candidates(
            model, model_family, base_spans, cand_lists,
            eval_batch_size=config.gcg.batch_size,
            config=config,
        )

        # --- Candidate selection ---
        selection_mode = config.objective.selection_mode
        if selection_mode == "weighted":
            best_idx = min(range(len(eval_results)), key=lambda i: eval_results[i]["total_loss"])
        elif selection_mode == "constrained":
            thresh = config.objective.constrained_repr_threshold
            feasible = [i for i, r in enumerate(eval_results) if r["repr_loss"] <= thresh]
            if feasible:
                best_idx = min(feasible, key=lambda i: eval_results[i]["task_loss"])
            else:
                best_idx = min(range(len(eval_results)), key=lambda i: eval_results[i]["total_loss"])
        elif selection_mode == "lexicographic":
            best_task = min(r["task_loss"] for r in eval_results)
            eps = config.objective.lexicographic_task_eps
            eligible = [i for i, r in enumerate(eval_results) if r["task_loss"] <= best_task + eps]
            best_idx = min(eligible, key=lambda i: eval_results[i]["repr_loss"])
        else:
            best_idx = min(range(len(eval_results)), key=lambda i: eval_results[i]["task_loss"])

        best_cand = cand_lists[best_idx]
        best_losses = dict(eval_results[best_idx])  # mutable copy

        # Accept if better than current
        current_eval = _evaluate_candidates(
            model, model_family, base_spans, [suffix_ids],
            eval_batch_size=1, config=config,
        )
        if best_losses["total_loss"] < current_eval[0]["total_loss"]:
            suffix_ids = best_cand
            suffix_str = tokenizer.decode(suffix_ids, skip_special_tokens=True)

        _current_state["suffix_ids"] = suffix_ids

        # --- Post-selection repr_loss evaluation (one forward pass, no_grad) ---
        # Selection above used task_loss only; now compute true repr_loss for logging.
        if use_repr and reference_hs_per_task:
            from poc_stage_gcg_early.objectives import repr_loss as _repr_loss_fn
            ref_hs_0 = reference_hs_per_task.get(train_tasks[0].task_id)
            if ref_hs_0 is not None:
                sel_spans = build_suffix_spans(
                    tokenizer, model_family, config.enable_thinking,
                    train_tasks[0].instruction, suffix_str, train_tasks[0].safe_target_prefix,
                    suffix_ids_override=suffix_ids,
                )
                with torch.no_grad():
                    out = model(
                        input_ids=sel_spans.input_ids.unsqueeze(0).to(device),
                        output_hidden_states=True,
                    )
                t0_repr_pos = repr_pos_per_task.get(train_tasks[0].task_id, [])
                cand_hs: Dict[int, Dict[int, torch.Tensor]] = {}
                for layer_idx in repr_layers:
                    if layer_idx < len(out.hidden_states):
                        lt = out.hidden_states[layer_idx]  # [1, seq_len, d_model]
                        cand_hs[layer_idx] = {
                            pos: lt[0, pos, :].detach().cpu().to(torch.float16)
                            for pos in t0_repr_pos
                            if pos < lt.shape[1]
                        }
                r_val = _repr_loss_fn(
                    cand_hs, ref_hs_0,
                    layers=repr_layers, positions=t0_repr_pos,
                    metric=config.objective.repr_metric,
                ).item()
                best_losses["repr_loss"] = r_val
                best_losses["total_loss"] = (
                    best_losses["task_loss"] + config.objective.lambda_repr * r_val
                )

        # --- Memory stats ---
        if torch.cuda.is_available():
            peak_mem_gb = torch.cuda.max_memory_allocated() / 1024**3
            torch.cuda.reset_peak_memory_stats()
        else:
            peak_mem_gb = 0.0

        wall_time = time.time() - t_start

        # --- Iteration log (all components, never just total) ---
        log_record = {
            "step": step,
            "suffix_ids": suffix_ids,
            "suffix_str": suffix_str,
            "task_loss": best_losses["task_loss"],
            "repr_loss": best_losses["repr_loss"],
            "kl_loss": best_losses["kl_loss"],
            "reg_loss": best_losses["reg_loss"],
            "total_loss": best_losses["total_loss"],
            "selected_candidate_idx": best_idx,
            "wall_time_sec": wall_time,
            "peak_gpu_mem_gb": peak_mem_gb,
            "seed": config.gcg.seed,
        }
        _append_jsonl(iter_log_path, log_record)

        # --- Pareto update ---
        pareto_candidate = {
            "step": step,
            "suffix_ids": suffix_ids,
            "suffix_str": suffix_str,
            **best_losses,
            "feasible": best_losses["repr_loss"] <= config.objective.constrained_repr_threshold,
            "seed": config.gcg.seed,
            "runtime_so_far_sec": wall_time,
        }
        pareto_front = _update_pareto(pareto_front, pareto_candidate)
        _append_jsonl(pareto_path, pareto_candidate)

        if step % 10 == 0:
            print(
                f"[GCG] step={step:4d}  task_loss={best_losses['task_loss']:.4f}  "
                f"repr_loss={best_losses['repr_loss']:.4f}  "
                f"suffix={repr(suffix_str[:40])}",
                flush=True,
            )

        # --- Checkpoint ---
        if (step + 1) % config.gcg.checkpoint_every == 0:
            _save_checkpoint(output_dir, step, suffix_ids, config_hash, config.run_id)

        # --- Permanent snapshot ---
        if (step + 1) % config.gcg.snapshot_every == 0:
            _save_snapshot(output_dir, step, suffix_ids, config_hash, config.run_id)

        del grad_accum, candidate_ids
        gc.collect()

    # Final checkpoint
    _save_checkpoint(output_dir, config.gcg.n_steps - 1, suffix_ids, config_hash, config.run_id)
    print(f"[GCG] Optimization complete. Final suffix: {repr(suffix_str)}", flush=True)

    # Write FINAL_CANDIDATES.jsonl
    final_path = output_dir / "FINAL_CANDIDATES.jsonl"
    with open(final_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "suffix_ids": suffix_ids,
            "suffix_str": suffix_str,
            "n_steps": config.gcg.n_steps,
            "selection_mode": config.objective.selection_mode,
        }) + "\n")
        for p in pareto_front:
            f.write(json.dumps(p, default=str) + "\n")
