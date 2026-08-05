"""
CLI for building the reference hidden-state cache (Stage 5 / Stage 8b).

Loads Qwen3-14B, runs one forward pass per surrogate task using the neutral
control suffix, and stores the hidden states in a cache directory.

Two position modes:
  absolute: --positions 0,1,2  (original v1; positions 0-2 are before the suffix
            in a causal LM and cannot attend to the suffix — repr gradient is 0)

  last_suffix: --repr-positions 3  (correct for repr_loss; uses the last N tokens
               of the suffix, which attend to the full prefix + all preceding
               suffix tokens → meaningful repr gradient w.r.t. the suffix)

For Stage 8b (correct repr_loss), use --repr-positions 3 --suffix-length 16
with a same-length neutral suffix so candidate and reference share the same
absolute positions at the suffix end.

Usage (Stage 8b, correct repr_loss):
  python -m poc_stage_gcg_early.build_reference_cache \
      --manifest outputs/stage_gcg_early/surrogate_manifest_v1.jsonl \
      --cache-dir outputs/stage_gcg_early/reference_cache_v2 \
      --model-family qwen3 \
      --model-name-or-path Qwen/Qwen3-14B \
      --layers 0,5,10,15,20,25,30,35 \
      --repr-positions 3 \
      --suffix-length 16 \
      --neutral-suffix-token-id 220
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.build_safe_surrogate_manifest import load_manifest
from poc_stage_gcg_early.reference_cache import ReferenceCache
from poc_stage_gcg_early.suffix_token_manager import build_suffix_spans


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build Stage GCG-Early reference cache")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--model-family", default="qwen3", choices=["qwen3", "gemma4", "llama"])
    parser.add_argument("--model-name-or-path", default="Qwen/Qwen3-14B")
    parser.add_argument("--layers", default="0,5,10,15,20,25,30,35,40",
                        help="Comma-separated layer indices to cache (Qwen3-14B: 0..40)")
    # Position mode: absolute (original v1) or last_suffix (correct for repr_loss)
    parser.add_argument("--positions", default=None,
                        help="Absolute positions (comma-separated). Mutually exclusive with --repr-positions.")
    parser.add_argument("--repr-positions", type=int, default=None,
                        help="Number of LAST SUFFIX positions to use (suffix_slice.stop - N .. stop-1). "
                             "Correct for repr_loss since these attend to the full suffix. "
                             "Requires --suffix-length.")
    parser.add_argument("--suffix-length", type=int, default=None,
                        help="Optimization suffix length (tokens). Required with --repr-positions.")
    parser.add_argument("--neutral-suffix-token-id", type=int, default=220,
                        help="Token ID repeated suffix_length times for the neutral reference suffix. "
                             "Default 220 = space token in Qwen3/tiktoken. Used with --suffix-length.")
    parser.add_argument("--repr-at-cot-pos", action="store_true",
                        help="5B mode: cache at target_slice.start (first target token = CoT pos 0). "
                             "Requires --suffix-length. Mutually exclusive with --positions/--repr-positions.")
    parser.add_argument("--split", default="all", choices=["train", "all"])
    parser.add_argument("--no-thinking", action="store_true")
    args = parser.parse_args(argv)

    if args.repr_at_cot_pos:
        if args.positions is not None or args.repr_positions is not None:
            parser.error("--repr-at-cot-pos is mutually exclusive with --positions/--repr-positions")
        if args.suffix_length is None:
            parser.error("--repr-at-cot-pos requires --suffix-length")
    elif args.positions is not None and args.repr_positions is not None:
        parser.error("--positions and --repr-positions are mutually exclusive")
    elif args.repr_positions is not None and args.suffix_length is None:
        parser.error("--repr-positions requires --suffix-length")
    elif args.positions is None and args.repr_positions is None:
        args.positions = "0,1,2"  # backward-compatible default

    layers = [int(x) for x in args.layers.split(",")]
    enable_thinking = not args.no_thinking
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"[build_reference_cache] manifest={args.manifest}", flush=True)
    print(f"[build_reference_cache] cache_dir={cache_dir}", flush=True)
    print(f"[build_reference_cache] layers={layers}", flush=True)
    print(f"[build_reference_cache] enable_thinking={enable_thinking}", flush=True)

    tasks = load_manifest(Path(args.manifest))
    if args.split == "train":
        tasks = [t for t in tasks if t.split == "train"]
    print(f"[build_reference_cache] {len(tasks)} tasks to cache", flush=True)

    print(f"[build_reference_cache] Loading model {args.model_name_or_path}...", flush=True)
    if args.model_family in ("qwen3", "llama"):
        # P9.0 item 3: load_qwen3_model is generic in model_name_or_path (plain
        # AutoModelForCausalLM/AutoTokenizer.from_pretrained), and Llama uses the same
        # model.model.embed_tokens layout as Qwen3, so it loads Llama correctly as-is.
        from poc_stage4.qwen3_model import load_qwen3_model
        wrapped = load_qwen3_model(
            args.model_name_or_path, require_cuda=True, log_device_placement=True
        )
    else:
        from poc_stage4.qwen3_model import load_gemma4_model
        wrapped = load_gemma4_model(require_cuda=True, log_device_placement=True)

    model = wrapped.model
    tokenizer = wrapped.tokenizer
    model.eval()

    cache = ReferenceCache(cache_dir)

    for task in tasks:
        print(f"[build_reference_cache] Building cache for task={task.task_id} ...", flush=True)

        if args.repr_at_cot_pos:
            # 5B mode: position = target_slice.start (first target token = CoT position 0)
            neutral_suffix_ids = [args.neutral_suffix_token_id] * args.suffix_length
            neutral_suffix_str = tokenizer.decode(neutral_suffix_ids, skip_special_tokens=True)
            spans = build_suffix_spans(
                tokenizer, args.model_family, enable_thinking,
                task.instruction, neutral_suffix_str, safe_target=task.safe_target_prefix,
                suffix_ids_override=neutral_suffix_ids,
            )
            positions = [spans.target_slice.start]
            print(f"[build_reference_cache]   cot_pos mode: target_slice.start={positions[0]}", flush=True)
            entry = cache.build_and_store(
                task_id=task.task_id,
                instruction=task.instruction,
                model=model,
                tokenizer=tokenizer,
                model_family=args.model_family,
                neutral_suffix=neutral_suffix_str,
                enable_thinking=enable_thinking,
                layers=layers,
                positions=positions,
                suffix_ids_override=neutral_suffix_ids,
            )
        elif args.repr_positions is not None:
            # Stage 8b: same-length neutral suffix; positions = last N suffix tokens
            neutral_suffix_ids = [args.neutral_suffix_token_id] * args.suffix_length
            neutral_suffix_str = tokenizer.decode(neutral_suffix_ids, skip_special_tokens=True)
            spans = build_suffix_spans(
                tokenizer, args.model_family, enable_thinking,
                task.instruction, neutral_suffix_str, safe_target=" ",
                suffix_ids_override=neutral_suffix_ids,
            )
            N = args.repr_positions
            positions = [
                max(0, spans.suffix_slice.stop - N + i)
                for i in range(N)
            ]
            print(f"[build_reference_cache]   suffix_length={args.suffix_length} "
                  f"suffix_slice={spans.suffix_slice}  positions={positions}", flush=True)
            entry = cache.build_and_store(
                task_id=task.task_id,
                instruction=task.instruction,
                model=model,
                tokenizer=tokenizer,
                model_family=args.model_family,
                neutral_suffix=neutral_suffix_str,
                enable_thinking=enable_thinking,
                layers=layers,
                positions=positions,
                suffix_ids_override=neutral_suffix_ids,
            )
        else:
            # Original absolute position mode (v1 backward compat)
            positions = [int(x) for x in args.positions.split(",")]
            print(f"[build_reference_cache]   positions={positions} (absolute mode)", flush=True)
            entry = cache.build_and_store(
                task_id=task.task_id,
                instruction=task.instruction,
                model=model,
                tokenizer=tokenizer,
                model_family=args.model_family,
                neutral_suffix=task.neutral_control_suffix,
                enable_thinking=enable_thinking,
                layers=layers,
                positions=positions,
            )

        print(f"[build_reference_cache]   cache_key={entry.cache_key}  "
              f"layers={entry.layers}  positions={entry.positions}", flush=True)

    print(f"[build_reference_cache] Done. Cache manifest at {cache_dir}/REFERENCE_CACHE_MANIFEST.json", flush=True)


if __name__ == "__main__":
    main()
