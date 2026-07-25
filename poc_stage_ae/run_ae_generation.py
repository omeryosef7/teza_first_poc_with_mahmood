"""
Stage 2 — Generation runner for the paired A/D/E/G early-token expansion study.

One process per SLURM array task: (model, goal_index, condition). Runs all
manifest rows matching that (model, goal_index, condition) tuple, in seed
order, loading the model exactly once.

Adapted from poc_stage4_8/run_repeated_generations.py — reuses:
  - load_qwen3_model / load_gemma4_model (poc_stage4.qwen3_model) for identical
    loader kwargs (torch_dtype="auto", device_map="auto", attn_implementation="sdpa").
  - _get_effective_eos_ids pattern (generation_config.eos_token_id first, list-safe,
    tokenizer fallback) — fixes the historical Gemma scalar-EOS bug.
  - apply_chat_template(..., enable_thinking=...) with try/except TypeError fallback.
  - _parse_think_tags / _parse_gemma4_thinking / _finish_reason from poc_stage2b.runner
    and poc_stage4_8.run_repeated_generations respectively.

New in this runner (per Stage AE spec):
  - Explicit per-row RNG seeding (python random, numpy, torch CPU+CUDA) before
    each generation call (not just torch.manual_seed).
  - Thinking/answer span positions located via thinking_position_utils at
    generation time and cached in the output row (so replay never re-derives
    from text).
  - do_sample=True, temperature=0.7, top_p=0.95, max_new_tokens=32768 for all
    conditions (A/D/E/G) — matches the max_new_tokens value used uniformly
    across poc_stage4_8 for all conditions including E/G (verified: no
    smaller default exists for thinking-disabled conditions anywhere in the
    reused code).
  - One shard file per (model, condition, goal_index): resumable/idempotent —
    on startup, reads existing shard rows and skips any row_key already
    present with status="ok".
  - Catches exceptions per-row (does not crash the whole shard).

Usage:
  python -m poc_stage_ae.run_ae_generation \
      --model qwen3 --manifest <path to {model}_ae_manifest.jsonl> \
      --goal-index 0 --condition A --output-dir <RUN_DIR>
"""
from __future__ import annotations

import argparse
import json
import random
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv
load_dotenv(_REPO_ROOT / ".env")

from poc_stage_ae.thinking_position_utils import locate_positions

_DO_SAMPLE = True
_TEMPERATURE = 0.7
_TOP_P = 0.95
_MAX_NEW_TOKENS = 32768


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _shard_path(output_dir: Path, model: str, condition: str, goal_index: int) -> Path:
    return output_dir / "shards" / f"{model}_{condition}_goal{goal_index}.jsonl"


def _load_completed_row_keys(shard_path: Path) -> set[str]:
    completed: set[str] = set()
    if not shard_path.exists():
        return completed
    with open(shard_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("status") == "ok" and row.get("row_key"):
                completed.add(row["row_key"])
    return completed


def _append_jsonl_flush(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        f.flush()


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=str(_REPO_ROOT),
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    import torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    try:
        import transformers
        transformers.set_seed(seed)
    except Exception:
        pass


def _load_model(model_family: str):
    from poc_stage4.qwen3_model import load_qwen3_model, load_gemma4_model
    if model_family == "gemma4":
        wrapped = load_gemma4_model(require_cuda=True, log_device_placement=True)
    elif model_family == "deepseek_r1":
        # DeepSeek-R1-Distill-Qwen-7B is a Qwen2 backbone → the generic Qwen3Model wrapper (.layers via
        # model.model.layers) + its tokenizer (which carries the shared <think></think> markers) work
        # unchanged. §31.3: weights must be node-local (HF_HOME set by the launcher), never project cache.
        from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY
        wrapped = load_qwen3_model(model_name=DEFAULT_MODEL_BY_FAMILY["deepseek_r1"],
                                   require_cuda=True, log_device_placement=True)
    elif model_family == "phi4":
        # Phi-4-mini-reasoning is Phi3ForCausalLM (hidden 3072, 32 layers); generic Qwen3Model wrapper
        # (.layers via model.model.layers) + its tokenizer (plain-BPE <think></think>) work unchanged.
        # §31.3-B: weights read offline from the project cache (user-authorized download).
        from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY
        wrapped = load_qwen3_model(model_name=DEFAULT_MODEL_BY_FAMILY["phi4"],
                                   require_cuda=True, log_device_placement=True)
    elif model_family == "deepseek_llama":
        # DeepSeek-R1-Distill-Llama-8B is LlamaForCausalLM (hidden 4096, 32 layers); generic Qwen3Model
        # wrapper (.layers via model.model.layers) + tokenizer (single-token <think>=128013/</think>=128014,
        # <think> in prefill) work unchanged. §31.3-B: offline project cache.
        from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY
        wrapped = load_qwen3_model(model_name=DEFAULT_MODEL_BY_FAMILY["deepseek_llama"],
                                   require_cuda=True, log_device_placement=True)
    else:
        wrapped = load_qwen3_model(require_cuda=True, log_device_placement=True)
    return wrapped.tokenizer, wrapped.model


def _get_effective_eos_ids(model: Any, tokenizer: Any) -> list[int]:
    """Reads model.generation_config.eos_token_id first (list-safe), falls back
    to tokenizer.eos_token_id. Copied verbatim from run_repeated_generations.py —
    fixes a historical Gemma scalar-EOS bug."""
    eos = getattr(getattr(model, "generation_config", None), "eos_token_id", None)
    if eos is None:
        eos = tokenizer.eos_token_id
    if isinstance(eos, int):
        return [eos]
    return list(eos)


def _parse_gemma4_thinking(generation_text: str) -> tuple[str | None, str | None, str]:
    from poc_stage4.model_family_utils import THINKING_MARKERS_BY_FAMILY
    start_marker = THINKING_MARKERS_BY_FAMILY["gemma4"]["start"]
    end_marker = THINKING_MARKERS_BY_FAMILY["gemma4"]["end"]
    start_idx = generation_text.find(start_marker)
    end_idx = generation_text.find(end_marker)
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        think_text = generation_text[start_idx + len(start_marker):end_idx]
        final_text = generation_text[end_idx + len(end_marker):].strip()
        return think_text, final_text, "parsed_from_thought_channel"
    elif start_marker in generation_text:
        return generation_text[generation_text.find(start_marker):], None, "thought_channel_unclosed"
    else:
        return None, generation_text, "no_thought_channel"


def _parse_think_tags(text: str) -> tuple[str | None, str | None, str]:
    start_tag, end_tag = "<think>", "</think>"
    start = text.find(start_tag)
    end = text.find(end_tag)
    if start >= 0 and end >= 0 and end > start:
        think_text = text[start + len(start_tag):end]
        final_text = text[end + len(end_tag):]
        return think_text, final_text if final_text.strip() else None, "parsed_from_think_tags"
    if start >= 0 or end >= 0:
        return None, text.strip() or None, "not_separable"
    return None, text.strip() or None, "not_present"


def _finish_reason(generation_token_ids: list[int], *, max_new_tokens: int, eos_token_ids: list[int]) -> str:
    if not generation_token_ids:
        return "empty"
    if generation_token_ids[-1] in eos_token_ids:
        return "eos_token"
    if len(generation_token_ids) >= max_new_tokens:
        return "max_new_tokens"
    return "unknown"


def _run_one_generation(
    *,
    tokenizer: Any,
    model: Any,
    model_family: str,
    prompt_text: str,
    enable_thinking: bool,
    seed: int,
    max_new_tokens: int,
) -> dict[str, Any]:
    import torch

    _seed_everything(seed)

    try:
        formatted_prompt: str = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt_text}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=enable_thinking,
        )
    except TypeError:
        formatted_prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt_text}],
            tokenize=False,
            add_generation_prompt=True,
        )

    inputs = tokenizer(formatted_prompt, return_tensors="pt", add_special_tokens=False)
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    eos_ids = _get_effective_eos_ids(model, tokenizer)

    generation_kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": _DO_SAMPLE,
        "temperature": _TEMPERATURE,
        "top_p": _TOP_P,
        "return_dict_in_generate": True,
        "eos_token_id": eos_ids,
        "pad_token_id": tokenizer.pad_token_id or eos_ids[0],
    }

    t0 = time.time()
    with torch.inference_mode():
        generated = model.generate(**inputs, **generation_kwargs)
    elapsed = time.time() - t0

    full_ids: list[int] = [int(t) for t in generated.sequences[0].tolist()]
    prompt_len = inputs["input_ids"].shape[1]
    input_token_ids = full_ids[:prompt_len]
    generation_token_ids = full_ids[prompt_len:]
    generation_text: str = tokenizer.decode(generation_token_ids, skip_special_tokens=False)

    if model_family == "gemma4":
        think_text, final_text, seg_status = _parse_gemma4_thinking(generation_text)
    else:
        think_text, final_text, seg_status = _parse_think_tags(generation_text)

    finish_reason = _finish_reason(generation_token_ids, eos_token_ids=eos_ids, max_new_tokens=max_new_tokens)

    # Locate cached span positions (never raises — errors recorded in parallel dict).
    positions, position_errors = locate_positions(
        model_family=model_family,
        tokenizer=tokenizer,
        full_token_ids=full_ids,
        boundary_index=prompt_len,
        enable_thinking=enable_thinking,
    )

    think_num_tokens = 0
    final_num_tokens = 0
    if think_text is not None:
        try:
            think_num_tokens = len(tokenizer(think_text, add_special_tokens=False)["input_ids"])
        except Exception:
            pass
    if final_text is not None:
        try:
            final_num_tokens = len(tokenizer(final_text, add_special_tokens=False)["input_ids"])
        except Exception:
            pass

    return {
        "formatted_input_text": formatted_prompt,
        "input_token_ids": input_token_ids,
        "input_token_count": prompt_len,
        "generation_token_ids": generation_token_ids,
        "generation_token_count": len(generation_token_ids),
        "generation_text": generation_text,
        "think_text": think_text,
        "final_text": final_text,
        "think_token_count": think_num_tokens,
        "final_token_count": final_num_tokens,
        "thinking_segmentation_status": seg_status,
        "finish_reason": finish_reason,
        "eos_ids": eos_ids,
        "positions": positions,
        "position_errors": position_errors,
        "generation_duration_seconds": round(elapsed, 3),
    }


def run_shard(
    *,
    model_family: str,
    manifest_path: Path,
    goal_index: int,
    condition: str,
    output_dir: Path,
) -> None:
    rows = _load_jsonl(manifest_path)
    target_rows = [
        r for r in rows
        if r.get("model") == model_family
        and int(r.get("goal_index", -1)) == goal_index
        and r.get("condition") == condition
    ]
    target_rows.sort(key=lambda r: int(r.get("seed", 0)))

    if not target_rows:
        print(f"WARNING: no manifest rows for model={model_family} goal_index={goal_index} condition={condition}")
        return

    shard_path = _shard_path(output_dir, model_family, condition, goal_index)
    completed = _load_completed_row_keys(shard_path)
    print(f"Shard {shard_path}: {len(completed)} rows already completed, {len(target_rows)} total rows in manifest slice")

    remaining = [r for r in target_rows if r["row_key"] not in completed]
    if not remaining:
        print("All rows already completed for this shard. Nothing to do.")
        return

    print(f"Loading model {model_family} ...")
    tokenizer, model = _load_model(model_family)
    print("Model loaded.")

    git_commit = _git_commit()
    hostname = socket.gethostname()
    try:
        import torch
        gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:
        gpu_name = None

    import os
    slurm_env = {
        "SLURM_JOB_ID": os.environ.get("SLURM_JOB_ID"),
        "SLURM_ARRAY_TASK_ID": os.environ.get("SLURM_ARRAY_TASK_ID"),
        "SLURM_ARRAY_JOB_ID": os.environ.get("SLURM_ARRAY_JOB_ID"),
    }

    n_done = n_failed = 0
    for row in remaining:
        row_key = row["row_key"]
        seed = int(row["seed"])
        enable_thinking = bool(row["enable_thinking"])
        prompt_text = row["user_message_text"]

        print(f"Running {row_key} (seed={seed} enable_thinking={enable_thinking}) ...")
        t0 = time.time()
        try:
            result = _run_one_generation(
                tokenizer=tokenizer,
                model=model,
                model_family=model_family,
                prompt_text=prompt_text,
                enable_thinking=enable_thinking,
                seed=seed,
                max_new_tokens=_MAX_NEW_TOKENS,
            )
            out_row = {
                "row_key": row_key,
                "status": "ok",
                "model": model_family,
                "model_name_or_path": row.get("model_name_or_path"),
                "model_revision": row.get("model_revision"),
                "git_commit": git_commit,
                "goal_index": row.get("goal_index"),
                "goal": row.get("goal"),
                "source_example_id": row.get("source_example_id"),
                "condition": condition,
                "seed": seed,
                "enable_thinking": enable_thinking,
                "do_sample": _DO_SAMPLE,
                "temperature": _TEMPERATURE,
                "top_p": _TOP_P,
                "max_new_tokens": _MAX_NEW_TOKENS,
                "user_message_text": prompt_text,
                **result,
                "eos_diagnostics": {
                    "eos_ids": result["eos_ids"],
                    "last_generated_token_id": result["generation_token_ids"][-1] if result["generation_token_ids"] else None,
                    "ended_on_eos": result["finish_reason"] == "eos_token",
                },
                "exception": None,
                "hostname": hostname,
                "gpu_name": gpu_name,
                "slurm": slurm_env,
                "created_utc": datetime.now(timezone.utc).isoformat(),
            }
            del out_row["eos_ids"]
            n_done += 1
            print(
                f"  OK gen_tokens={result['generation_token_count']} "
                f"finish={result['finish_reason']} "
                f"seg={result['thinking_segmentation_status']} "
                f"elapsed={result['generation_duration_seconds']:.1f}s"
            )
        except Exception as exc:
            import traceback
            elapsed = round(time.time() - t0, 3)
            out_row = {
                "row_key": row_key,
                "status": "error",
                "model": model_family,
                "goal_index": row.get("goal_index"),
                "source_example_id": row.get("source_example_id"),
                "condition": condition,
                "seed": seed,
                "enable_thinking": enable_thinking,
                "exception": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                },
                "generation_duration_seconds": elapsed,
                "hostname": hostname,
                "gpu_name": gpu_name,
                "slurm": slurm_env,
                "created_utc": datetime.now(timezone.utc).isoformat(),
            }
            n_failed += 1
            print(f"  FAILED {row_key}: {exc}")

        _append_jsonl_flush(shard_path, out_row)

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    print(f"Done. {n_done} ok, {n_failed} failed, {len(completed)} previously skipped. Shard: {shard_path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage 2 — AE generation runner (one process per model x goal_index x condition).")
    p.add_argument("--model", required=True, choices=["qwen3", "gemma4", "deepseek_r1", "phi4", "deepseek_llama"])
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--goal-index", required=True, type=int)
    # A/D/E/G = legacy stage-AE scheme; B/C/F added for the plan §9 mechanistic groups
    # (build_phase5_mechanistic_manifest.py). `condition` is only used for row-filtering + shard
    # naming here; positions/thinking come from enable_thinking, so new labels are safe.
    p.add_argument("--condition", required=True, choices=["A", "B", "C", "D", "E", "F", "G"])
    p.add_argument("--output-dir", required=True, type=Path)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_shard(
        model_family=args.model,
        manifest_path=args.manifest,
        goal_index=args.goal_index,
        condition=args.condition,
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
