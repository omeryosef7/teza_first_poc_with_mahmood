"""
CLI entry point for Stage GCG-Early optimization.

Usage (task-only baseline, Stage 3):
  python -m poc_stage_gcg_early.run_optimization \
      --run-id smoke_qwen3_v1 \
      --model-family qwen3 \
      --model-name-or-path Qwen/Qwen3-14B \
      --manifest outputs/stage_gcg_early/surrogate_manifest_v1.jsonl \
      --output-dir outputs/stage_gcg_early/smoke_qwen3_v1 \
      --suffix-length 8 \
      --n-steps 50 \
      --batch-size 32 \
      --seed 42

Resume: re-run the same command. The optimizer detects checkpoint.pt, verifies
the config hash, and continues from the last saved step.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.build_safe_surrogate_manifest import load_manifest
from poc_stage_gcg_early.config import (
    GCGHyperparams,
    ObjectiveWeights,
    RunConfig,
    make_smoke_config,
)
from poc_stage_gcg_early.gcg_optimizer import run_optimization
from poc_stage_gcg_early.reference_cache import ReferenceCache


def _collect_environment(model_name_or_path: str) -> dict:
    """Collect environment metadata for ENVIRONMENT.json."""
    env = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID", "local"),
        "slurm_nodelist": os.environ.get("SLURM_NODELIST", "local"),
        "model_name_or_path": model_name_or_path,
    }
    if torch.cuda.is_available():
        env["cuda_device_name"] = torch.cuda.get_device_name(0)
        env["cuda_memory_total_gb"] = torch.cuda.get_device_properties(0).total_memory / 1024**3
    try:
        git_rev = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
        env["git_revision"] = git_rev
    except Exception:
        env["git_revision"] = "unknown"
    try:
        import transformers
        env["transformers_version"] = transformers.__version__
    except ImportError:
        pass
    return env


def main(argv=None):
    parser = argparse.ArgumentParser(description="Stage GCG-Early optimization")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model-family", default="qwen3", choices=["qwen3", "gemma4"])
    parser.add_argument("--model-name-or-path", default="Qwen/Qwen3-14B")
    parser.add_argument("--model-revision", default=None)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--suffix-length", type=int, default=16)
    parser.add_argument("--n-steps", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--topk", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-filter-cand", action="store_true",
                        help="Disable BPE round-trip filter on candidates. Recommended when "
                             "suffix_ids_override is used (avoids all candidates being rejected "
                             "due to BPE tokenizer non-invertibility).")
    parser.add_argument("--lambda-repr", type=float, default=0.0)
    parser.add_argument("--lambda-kl", type=float, default=0.0)
    parser.add_argument("--repr-metric", default="cosine", choices=["cosine", "l2"])
    parser.add_argument("--repr-positions", type=int, default=3)
    parser.add_argument("--repr-layers", default="0,5,10,15,20,25,30,35",
                        help="Comma-separated layer indices for repr_loss (must be in pre-built cache). "
                             "Default excludes layer 40 to avoid final-norm mismatch.")
    parser.add_argument("--reference-cache-dir", default=None,
                        help="Path to pre-built reference hidden-state cache directory. "
                             "Required when lambda_repr > 0 to avoid rebuilding on every run.")
    parser.add_argument("--no-thinking", action="store_true")
    parser.add_argument("--checkpoint-every", type=int, default=10)
    parser.add_argument("--snapshot-every", type=int, default=50)
    parser.add_argument("--split", default="train", choices=["train", "all"])
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Config ---
    config = RunConfig(
        run_id=args.run_id,
        model_family=args.model_family,
        model_name_or_path=args.model_name_or_path,
        model_revision=args.model_revision,
        manifest_path=args.manifest,
        gcg=GCGHyperparams(
            suffix_length=args.suffix_length,
            batch_size=args.batch_size,
            topk=args.topk,
            n_steps=args.n_steps,
            seed=args.seed,
            checkpoint_every=args.checkpoint_every,
            snapshot_every=args.snapshot_every,
            filter_cand=not args.no_filter_cand,
        ),
        objective=ObjectiveWeights(
            lambda_repr=args.lambda_repr,
            lambda_kl=args.lambda_kl,
            repr_metric=args.repr_metric,
            repr_positions=args.repr_positions,
        ),
        output_dir=str(output_dir),
        enable_thinking=not args.no_thinking,
    )

    # Write CONFIG.json before any model load
    config_path = output_dir / "CONFIG.json"
    if not config_path.exists():
        config_path.write_text(config.to_json(), encoding="utf-8")

    # Write ENVIRONMENT.json (always overwrite — diagnostic)
    env_info = _collect_environment(args.model_name_or_path)
    (output_dir / "ENVIRONMENT.json").write_text(
        json.dumps(env_info, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    print(f"[run_optimization] run_id={args.run_id}", flush=True)
    print(f"[run_optimization] config_hash={config.config_hash()}", flush=True)
    print(f"[run_optimization] output_dir={output_dir}", flush=True)
    print(f"[run_optimization] GPU: {env_info.get('cuda_device_name', 'none')}", flush=True)
    print(f"[run_optimization] git_revision={env_info.get('git_revision', 'unknown')}", flush=True)

    # --- Load manifest ---
    tasks = load_manifest(Path(args.manifest))
    if args.split == "train":
        tasks = [t for t in tasks if t.split == "train"]
    print(f"[run_optimization] Loaded {len(tasks)} tasks (split={args.split})", flush=True)

    # Copy manifest to output_dir
    manifest_copy = output_dir / "MANIFEST.jsonl"
    if not manifest_copy.exists():
        import shutil
        shutil.copy(args.manifest, manifest_copy)

    # --- Load model ---
    print(f"[run_optimization] Loading model {args.model_name_or_path}...", flush=True)
    if args.model_family == "qwen3":
        from poc_stage4.qwen3_model import load_qwen3_model
        wrapped = load_qwen3_model(
            args.model_name_or_path, require_cuda=True, log_device_placement=True
        )
        model = wrapped.model
        tokenizer = wrapped.tokenizer
    elif args.model_family == "gemma4":
        from poc_stage4.qwen3_model import load_gemma4_model
        wrapped = load_gemma4_model(require_cuda=True, log_device_placement=True)
        model = wrapped.model
        tokenizer = wrapped.tokenizer
    else:
        raise ValueError(f"Unknown model_family: {args.model_family}")

    # --- Reference cache (optional for task-only baseline) ---
    ref_cache = None
    if args.lambda_repr > 0.0 or args.lambda_kl > 0.0:
        cache_dir = output_dir / "reference_cache"
        ref_cache = ReferenceCache(cache_dir)
        print("[run_optimization] Reference cache initialized.", flush=True)

    # --- Load pre-built reference hidden states for repr_loss ---
    reference_hs_per_task: Optional[dict] = None
    repr_layers_list: Optional[list] = None
    if args.lambda_repr > 0.0 and args.reference_cache_dir:
        import json as _json
        cache_dir_prebuilt = Path(args.reference_cache_dir)
        manifest_path = cache_dir_prebuilt / "REFERENCE_CACHE_MANIFEST.json"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Reference cache manifest not found: {manifest_path}. "
                "Run build_gcg_reference_cache.slurm first."
            )
        repr_layers_list = [int(x) for x in args.repr_layers.split(",")]
        manifest: dict = {}
        with open(manifest_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entry = _json.loads(line)
                    manifest[entry["task_id"]] = entry
        reference_hs_per_task = {}
        for task in tasks:
            if task.task_id not in manifest:
                print(f"[run_optimization] WARNING: no cache entry for task={task.task_id}", flush=True)
                continue
            meta = manifest[task.task_id]
            cache_key = meta["cache_key"]
            safe_task_id = task.task_id.replace("/", "_").replace(" ", "_")
            pt_filename = meta.get("pt_path", f"{safe_task_id}_{cache_key}.pt")
            pt_path = cache_dir_prebuilt / pt_filename
            if not pt_path.exists():
                print(f"[run_optimization] WARNING: cache file not found: {pt_path}", flush=True)
                continue
            data = torch.load(pt_path, map_location="cpu", weights_only=False)
            hs_raw = data["hidden_states"]
            hs = {
                int(l): {int(p): v for p, v in pos_dict.items()}
                for l, pos_dict in hs_raw.items()
            }
            # Keep only the layers that will be used for repr_loss
            hs_filtered = {l: hs[l] for l in repr_layers_list if l in hs}
            reference_hs_per_task[task.task_id] = hs_filtered
            print(
                f"[run_optimization] Loaded reference hs: task={task.task_id} "
                f"key={cache_key} layers={sorted(hs_filtered.keys())}",
                flush=True,
            )
        if not reference_hs_per_task:
            raise RuntimeError(
                "No reference hidden states loaded — cannot run with lambda_repr > 0. "
                "Check that reference_cache_dir contains entries for all train tasks."
            )
        print(
            f"[run_optimization] repr_layers={repr_layers_list} "
            f"repr_positions=0..{args.repr_positions - 1}",
            flush=True,
        )

    # --- Run optimization ---
    run_optimization(
        model=model,
        tokenizer=tokenizer,
        model_family=args.model_family,
        tasks=tasks,
        config=config,
        reference_cache=ref_cache,
        output_dir=output_dir,
        reference_hs_per_task=reference_hs_per_task,
        repr_layers=repr_layers_list,
    )


if __name__ == "__main__":
    main()
