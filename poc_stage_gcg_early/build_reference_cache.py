"""
CLI for building the reference hidden-state cache (Stage 5).

Loads Qwen3-14B, runs one forward pass per surrogate task using the neutral
control suffix (" "), and stores the hidden states in a cache directory.

Usage:
  python -m poc_stage_gcg_early.build_reference_cache \
      --manifest outputs/stage_gcg_early/surrogate_manifest_v1.jsonl \
      --cache-dir outputs/stage_gcg_early/reference_cache_v1 \
      --model-family qwen3 \
      --model-name-or-path Qwen/Qwen3-14B \
      --layers 0,8,16,24,32,40,47 \
      --positions 0,1,2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.build_safe_surrogate_manifest import load_manifest
from poc_stage_gcg_early.reference_cache import ReferenceCache


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build Stage GCG-Early reference cache")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--model-family", default="qwen3", choices=["qwen3", "gemma4"])
    parser.add_argument("--model-name-or-path", default="Qwen/Qwen3-14B")
    parser.add_argument("--layers", default="0,8,16,24,32,40,47",
                        help="Comma-separated layer indices to cache")
    parser.add_argument("--positions", default="0,1,2",
                        help="Comma-separated token positions to cache")
    parser.add_argument("--split", default="all", choices=["train", "all"])
    parser.add_argument("--no-thinking", action="store_true")
    args = parser.parse_args(argv)

    layers = [int(x) for x in args.layers.split(",")]
    positions = [int(x) for x in args.positions.split(",")]
    enable_thinking = not args.no_thinking
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"[build_reference_cache] manifest={args.manifest}", flush=True)
    print(f"[build_reference_cache] cache_dir={cache_dir}", flush=True)
    print(f"[build_reference_cache] layers={layers}", flush=True)
    print(f"[build_reference_cache] positions={positions}", flush=True)
    print(f"[build_reference_cache] enable_thinking={enable_thinking}", flush=True)

    tasks = load_manifest(Path(args.manifest))
    if args.split == "train":
        tasks = [t for t in tasks if t.split == "train"]
    print(f"[build_reference_cache] {len(tasks)} tasks to cache", flush=True)

    print(f"[build_reference_cache] Loading model {args.model_name_or_path}...", flush=True)
    if args.model_family == "qwen3":
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
