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
    reference_cache_content_id,
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


def _derive_objective_name(args) -> Optional[str]:
    """
    Auto-label the objective from the loss terms that are actually switched on.

    Returns None for a pure task-loss arm, so that every pre-P9.0 task-only config keeps
    its original config_hash (see config._HASH_BACKCOMPAT_DEFAULTS). An explicit
    --objective-name always wins over this.
    """
    parts = []
    if args.lambda_repr > 0.0:
        parts.append(
            f"repr_{args.repr_metric}" + ("_cotpos" if args.repr_at_cot_pos else "")
        )
    if args.lambda_kl > 0.0:
        parts.append("kl")
    if args.refusal_dir_layers:
        parts.append("refusal_dir_L" + args.refusal_dir_layers.replace(",", "-"))
    elif args.lambda_refusal_dir > 0.0:
        parts.append(f"refusal_dir_L{args.refusal_dir_layer}")
    return "+".join(parts) if parts else None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Stage GCG-Early optimization")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model-family", default="qwen3",
                        choices=["qwen3", "gemma4", "deepseek_r1", "llama"])
    parser.add_argument("--model-name-or-path", default="Qwen/Qwen3-14B")
    parser.add_argument("--model-revision", default=None)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--suffix-length", type=int, default=16)
    parser.add_argument("--n-steps", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--topk", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--suffix-placement", default="user", choices=["user", "assistant"],
                        help="Where the adversarial suffix is placed in the optimized prompt. "
                             "'user' (default, FIXED 2026-07-19) matches free-generation eval; "
                             "'assistant' reproduces the legacy pre-2026-07-19 placement bug.")
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
    parser.add_argument("--selection-mode", default="weighted",
                        choices=["weighted", "constrained", "lexicographic"],
                        help="Candidate selection strategy. 'weighted': argmin(total_loss). "
                             "'constrained': argmin(task_loss) s.t. repr_loss<=threshold. "
                             "'lexicographic': argmin(repr_loss) s.t. task_loss<=best+eps.")
    parser.add_argument("--constrained-repr-threshold", type=float, default=0.3,
                        help="repr_loss threshold for constrained selection mode.")
    parser.add_argument("--lexicographic-task-eps", type=float, default=0.01,
                        help="task_loss tolerance for lexicographic selection mode.")
    parser.add_argument("--repr-at-cot-pos", action="store_true",
                        help="5B: use target_slice.start as repr position (CoT position 0 in teacher-forcing). "
                             "Reference cache must be built with --repr-at-cot-pos flag.")
    parser.add_argument("--quick-asr-every", type=int, default=0,
                        help="5C: run quick prefix-match ASR check on top-5 candidates every N steps. "
                             "0 = disabled. Adds ~10pct runtime overhead.")
    parser.add_argument("--multi-model-family", default=None, choices=["gemma4"],
                        help="Add a second model for cross-tokenizer candidate re-scoring. "
                             "Gradients stay in primary model's token space; second model's "
                             "task_loss is added to candidate selection criterion. Requires 2 GPUs.")
    parser.add_argument("--multi-model-name-or-path", default="google/gemma-4-E4B-it",
                        help="HF model id or local path for the second model.")
    parser.add_argument("--lambda-refusal-dir", type=float, default=0.0,
                        help="Weight for refusal-direction projection loss (CoT Hijacking paper, layer 25).")
    parser.add_argument("--refusal-dir-layer", type=int, default=25,
                        help="Layer index for refusal direction projection (default: 25 per CoT Hijacking paper).")
    parser.add_argument("--refusal-dir-path", default=None,
                        help="Path to v_refusal .pt file (from compute_refusal_direction.py). Required when --lambda-refusal-dir > 0.")
    parser.add_argument("--refusal-dir-layers", default=None,
                        help="Multi-layer RD (10D): comma-separated layer indices e.g. '20,25,28'. Overrides --refusal-dir-layer.")
    parser.add_argument("--refusal-dir-paths", default=None,
                        help="Multi-layer RD (10D): comma-separated paths to v_refusal .pt files, one per layer in --refusal-dir-layers.")
    parser.add_argument("--lambda-refusal-dir-per-layer", default=None,
                        help="Multi-layer RD (10D): comma-separated lambda weights, one per layer. e.g. '0.1,0.3,0.1'.")
    parser.add_argument("--lambda-refusal-dir-schedule", default=None,
                        help="Lambda annealing (10E): JSON schedule e.g. '[[0,0.7],[100,0.3],[300,0.1]]'.")
    parser.add_argument("--repr-in-selection", dest="repr_in_selection",
                        action="store_true", default=None,
                        help="P9.0: evaluate candidates with output_hidden_states=True so the "
                             "repr / refusal-direction terms enter CANDIDATE SELECTION, not just "
                             "the gradient. Default (unset) = auto: ON iff a representation "
                             "objective is configured (lambda_repr > 0 with a cache, or any "
                             "refusal-direction term), OFF for task-only arms.")
    parser.add_argument("--no-repr-in-selection", dest="repr_in_selection",
                        action="store_false",
                        help="Force the pre-P9.0 behaviour: select on task_loss only "
                             "(repr_loss == 0.0 for every candidate). For ablations that "
                             "reproduce the old runs.")
    parser.add_argument("--repr-selection-sub-batch", type=int, default=8,
                        help="Sub-batch size for the hidden-state candidate forward pass. "
                             "Hidden states for 64 candidates do not fit next to a 14B model; "
                             "lower this if selection OOMs.")
    parser.add_argument("--objective-name", default=None,
                        help="Human-readable objective label; written to CONFIG.json and folded "
                             "into config_hash(). Auto-derived from the active loss terms when "
                             "any non-task objective is configured.")
    parser.add_argument("--log-channel-token-positions", action="store_true",
                        help="Sprint 2 Track 1 diagnostic: log per-position task_loss at the target's "
                             "opening/closing CoT-marker token positions into ITERATION_LOG.jsonl. "
                             "No-op (and no effect on config_hash) for targets without those markers.")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Objective provenance (P9.0 item 2) ---
    # repr_layers was a config field that nothing ever populated, and --reference-cache-dir
    # was not a config field at all: CONFIG.json showed "repr_layers": [] and config_hash()
    # ignored both, so two arms differing only in objective wiring shared a hash and could
    # silently cross-resume each other's checkpoint.pt. Record both (the cache as a content
    # hash of its manifest, so the hash tracks cache CONTENT rather than a path).
    repr_layers_cfg = (
        [int(x) for x in args.repr_layers.split(",") if x.strip()]
        if args.lambda_repr > 0.0 else []
    )
    reference_cache_id = None
    if args.reference_cache_dir and (args.lambda_repr > 0.0 or args.lambda_kl > 0.0):
        reference_cache_id = reference_cache_content_id(args.reference_cache_dir)
    objective_name = args.objective_name or _derive_objective_name(args)

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
            suffix_placement=args.suffix_placement,
        ),
        objective=ObjectiveWeights(
            lambda_repr=args.lambda_repr,
            lambda_kl=args.lambda_kl,
            repr_metric=args.repr_metric,
            repr_positions=args.repr_positions,
            repr_at_cot_pos=args.repr_at_cot_pos,
            quick_asr_every=args.quick_asr_every,
            selection_mode=args.selection_mode,
            constrained_repr_threshold=args.constrained_repr_threshold,
            lexicographic_task_eps=args.lexicographic_task_eps,
            lambda_refusal_dir=args.lambda_refusal_dir,
            refusal_dir_layer=args.refusal_dir_layer,
            refusal_dir_path=args.refusal_dir_path,
            refusal_dir_layers=[int(x) for x in args.refusal_dir_layers.split(",")] if args.refusal_dir_layers else [],
            refusal_dir_paths=[x.strip() for x in args.refusal_dir_paths.split(",")] if args.refusal_dir_paths else [],
            lambda_refusal_dir_per_layer=[float(x) for x in args.lambda_refusal_dir_per_layer.split(",")] if args.lambda_refusal_dir_per_layer else [],
            lambda_refusal_dir_schedule=json.loads(args.lambda_refusal_dir_schedule) if args.lambda_refusal_dir_schedule else [],
            repr_layers=repr_layers_cfg,
            repr_in_selection=args.repr_in_selection,
            repr_selection_sub_batch=args.repr_selection_sub_batch,
            reference_cache_id=reference_cache_id,
            objective_name=objective_name,
        ),
        output_dir=str(output_dir),
        enable_thinking=not args.no_thinking,
        multi_model_family=args.multi_model_family,
        log_channel_token_positions=args.log_channel_token_positions,
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
    print(
        f"[run_optimization] objective_name={objective_name} "
        f"repr_layers={repr_layers_cfg} reference_cache_id={reference_cache_id} "
        f"repr_in_selection={args.repr_in_selection if args.repr_in_selection is not None else 'auto'}",
        flush=True,
    )
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
        # In multimodel mode: pin Qwen3 to cuda:0 so its gradient computation stays on one
        # device. With device_map="auto" and 2 visible GPUs, HF splits Qwen3 across both,
        # which causes NaN in the one-hot gradient path (cross-device hidden states vs CPU cache).
        qwen3_device_map = "cuda:0" if args.multi_model_family else "auto"
        wrapped = load_qwen3_model(
            args.model_name_or_path, require_cuda=True, log_device_placement=True,
            device_map=qwen3_device_map,
        )
        model = wrapped.model
        tokenizer = wrapped.tokenizer
    elif args.model_family == "gemma4":
        from poc_stage4.qwen3_model import load_gemma4_model
        wrapped = load_gemma4_model(
            args.model_name_or_path, require_cuda=True, log_device_placement=True
        )
        model = wrapped.model
        tokenizer = wrapped.tokenizer
    elif args.model_family == "deepseek_r1":
        # Sprint 2 Track 3: DeepSeek-R1-Distill-Qwen-7B is a Qwen2.5-backbone distillation that
        # uses the IDENTICAL <think>/</think> marker strings as Qwen3 (verified directly from its
        # tokenizer_config.json chat_template before this was written) and has no enable_thinking
        # toggle -- it thinks unconditionally. load_qwen3_model() is already generic in
        # model_name_or_path (plain AutoModelForCausalLM/AutoTokenizer.from_pretrained calls, no
        # Qwen3-14B-specific hardcoding), so it loads this model correctly as-is.
        from poc_stage4.qwen3_model import load_qwen3_model
        wrapped = load_qwen3_model(
            args.model_name_or_path, require_cuda=True, log_device_placement=True,
        )
        model = wrapped.model
        tokenizer = wrapped.tokenizer
    elif args.model_family == "llama":
        # P9.0 item 3: Llama-family (LlamaForCausalLM) support. Same standard decoder
        # layout as Qwen3 -- model.model.embed_tokens (see model_adapter
        # _EMBED_PATHS_BY_FAMILY['llama']) -- and load_qwen3_model is generic in
        # model_name_or_path (plain AutoModelForCausalLM/AutoTokenizer.from_pretrained),
        # so it loads Llama correctly as-is. Llama has no thinking channel: pass
        # --no-thinking (apply_chat_template drops the unsupported enable_thinking kwarg
        # via its TypeError fallback either way).
        from poc_stage4.qwen3_model import load_qwen3_model
        wrapped = load_qwen3_model(
            args.model_name_or_path, require_cuda=True, log_device_placement=True,
        )
        model = wrapped.model
        tokenizer = wrapped.tokenizer
    else:
        raise ValueError(f"Unknown model_family: {args.model_family}")

    # --- Second model for multi-model candidate selection ---
    gemma4_model = None
    gemma4_tokenizer = None
    if args.multi_model_family == "gemma4":
        print(f"[run_optimization] Loading second model (Gemma4) for multi-model selection: {args.multi_model_name_or_path}", flush=True)
        from poc_stage4.qwen3_model import load_gemma4_model as _load_gemma4
        # Force Gemma4 entirely onto cuda:1 to isolate it from Qwen3 on cuda:0.
        # device_map="auto" would split Gemma4 across both GPUs, putting embed_tokens
        # on cuda:0 alongside Qwen3 — any CUDA assert in Gemma4 would corrupt Qwen3's context.
        # Gemma4-E4B (~10GB) fits comfortably on a single L40S (46GB).
        g4_device_map = "cuda:1" if torch.cuda.device_count() >= 2 else "auto"
        wrapped2 = _load_gemma4(
            args.multi_model_name_or_path, require_cuda=True, log_device_placement=True,
            device_map=g4_device_map,
        )
        gemma4_model = wrapped2.model
        gemma4_tokenizer = wrapped2.tokenizer
        print("[run_optimization] Second model loaded.", flush=True)

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
        repr_layers_list = repr_layers_cfg  # same parse, recorded in CONFIG.json above
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
            f"repr_positions=last {args.repr_positions} suffix tokens (computed per-task from spans)",
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
        gemma4_model=gemma4_model,
        gemma4_tokenizer=gemma4_tokenizer,
    )


if __name__ == "__main__":
    main()
