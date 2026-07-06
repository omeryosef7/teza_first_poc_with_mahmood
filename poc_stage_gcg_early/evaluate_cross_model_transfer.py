"""
Cross-model suffix transfer evaluation for Stage GCG-Early.

Takes optimized suffixes from a source run (one model family) and evaluates
them on a target model (different family). Cross-model transfer uses the
decoded suffix TEXT (not token IDs), because Qwen3 (tiktoken BPE) and Gemma4
(SentencePiece) have incompatible vocabularies.

Usage:
    python -m poc_stage_gcg_early.evaluate_cross_model_transfer \\
        --source-run-dir outputs/stage_gcg_early/gcg_qwen3_repr_8b \\
        --target-model-family gemma4 \\
        --output-dir outputs/stage_gcg_early/transfer_qwen3_to_gemma4

Writes FREE_GENERATION_RESULTS.jsonl + DETECTION_DELAY_ANALYSIS.md to output-dir.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def load_final_candidates(source_run_dir: Path) -> List[dict]:
    path = Path(source_run_dir) / "FINAL_CANDIDATES.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"FINAL_CANDIDATES.jsonl not found in {source_run_dir}")
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_manifest(run_dir: Path) -> List[dict]:
    path = Path(run_dir) / "MANIFEST.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"MANIFEST.jsonl not found in {run_dir}")
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_target_model(model_family: str):
    """Load target model and tokenizer. Returns (model, tokenizer, enable_thinking)."""
    if model_family == "qwen3":
        from poc_stage4.qwen3_model import load_qwen3_model
        model_name = "Qwen/Qwen3-14B"
        wrapped = load_qwen3_model(model_name, require_cuda=True, log_device_placement=True)
        enable_thinking = True
    elif model_family == "gemma4":
        from poc_stage4.qwen3_model import load_gemma4_model
        wrapped = load_gemma4_model(require_cuda=True, log_device_placement=True)
        enable_thinking = False
    else:
        raise ValueError(f"Unknown model_family: {model_family!r}. Use 'qwen3' or 'gemma4'.")

    wrapped.model.eval()
    return wrapped.model, wrapped.tokenizer, enable_thinking


def run_transfer_evaluation(
    source_run_dir: Path,
    target_model_family: str,
    output_dir: Path,
    seeds: Optional[List[int]] = None,
) -> None:
    """
    Transfer optimized suffixes from source_run_dir to target model.

    Uses suffix TEXT for cross-vocabulary transfer (not token IDs).
    Evaluates: optimized_weighted/optimized_lexicographic + baselines.
    """
    source_run_dir = Path(source_run_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if seeds is None:
        seeds = [42]

    print(f"[transfer] Source run: {source_run_dir.name}", flush=True)
    print(f"[transfer] Target model family: {target_model_family}", flush=True)
    print(f"[transfer] Output dir: {output_dir}", flush=True)

    # Load source candidates and manifest
    candidates = load_final_candidates(source_run_dir)
    manifest_rows = load_manifest(source_run_dir)

    print(f"[transfer] {len(candidates)} candidates, {len(manifest_rows)} tasks", flush=True)

    source_config_path = source_run_dir / "CONFIG.json"
    source_config = json.load(open(source_config_path)) if source_config_path.exists() else {}

    # Write transfer manifest (adapted for target model)
    target_manifest_path = output_dir / "MANIFEST.jsonl"
    if not target_manifest_path.exists():
        with open(target_manifest_path, "w", encoding="utf-8") as f:
            for task in manifest_rows:
                adapted = dict(task)
                adapted["model"] = target_model_family
                adapted["enable_thinking"] = (target_model_family == "qwen3")
                f.write(json.dumps(adapted) + "\n")
        print(f"[transfer] Wrote adapted manifest: {target_manifest_path}", flush=True)

    # Write transfer CONFIG
    transfer_config = {
        "source_run_dir": str(source_run_dir),
        "source_model_family": source_config.get("model_family", "unknown"),
        "target_model_family": target_model_family,
        "seeds": seeds,
        "transfer_type": "cross_model_text_transfer",
    }
    config_path = output_dir / "CONFIG.json"
    if not config_path.exists():
        with open(config_path, "w") as f:
            json.dump(transfer_config, f, indent=2)

    # Load target model
    print(f"[transfer] Loading {target_model_family} model...", flush=True)
    model, tokenizer, enable_thinking = load_target_model(target_model_family)

    # Import evaluation function
    from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_suffix

    tasks = [type("T", (), t)() for t in manifest_rows]
    for task_data in manifest_rows:
        task = argparse.Namespace(**task_data)
        # Adapt enable_thinking for target model
        task.enable_thinking = (target_model_family == "qwen3")

        for seed in seeds:
            # Optimized suffixes (text transfer)
            for cand in candidates:
                suffix_str = cand.get("suffix_str", "")
                if not suffix_str:
                    continue
                label = f"transfer_{cand.get('selection_mode', 'weighted')}"
                res = evaluate_suffix(
                    model, tokenizer, target_model_family,
                    task_id=task.task_id,
                    instruction=task.instruction,
                    suffix_str=suffix_str,
                    suffix_label=label,
                    enable_thinking=task.enable_thinking,
                    seed=seed,
                    output_dir=output_dir,
                )
                if res is not None:
                    print(f"[transfer] {task.task_id} {label} seed={seed} "
                          f"sr={res.get('strongreject_score')}", flush=True)

            # Baselines on target model
            for suffix_str, label in [
                (task.neutral_control_suffix, "neutral_control"),
                (" " * 16, "random_spaces"),
                (" ", "task_only"),
            ]:
                res = evaluate_suffix(
                    model, tokenizer, target_model_family,
                    task_id=task.task_id,
                    instruction=task.instruction,
                    suffix_str=suffix_str,
                    suffix_label=label,
                    enable_thinking=task.enable_thinking,
                    seed=seed,
                    output_dir=output_dir,
                )
                if res is not None:
                    print(f"[transfer] {task.task_id} {label} seed={seed} "
                          f"sr={res.get('strongreject_score')}", flush=True)

    # Run analysis
    from poc_stage_gcg_early.analyze_detection_delay import analyze_detection_delay
    analyze_detection_delay(output_dir, "FREE_GENERATION_RESULTS.jsonl")
    print(f"[transfer] Done. Results in {output_dir}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run-dir", required=True,
                        help="Run dir with FINAL_CANDIDATES.jsonl and MANIFEST.jsonl")
    parser.add_argument("--target-model-family", required=True, choices=["qwen3", "gemma4"],
                        help="Target model family for suffix transfer")
    parser.add_argument("--output-dir", required=True,
                        help="Where to write FREE_GENERATION_RESULTS.jsonl and analysis")
    parser.add_argument("--seeds", default="42",
                        help="Comma-separated list of generation seeds (default: 42)")
    args = parser.parse_args()

    seeds = [int(s) for s in args.seeds.split(",")]
    run_transfer_evaluation(
        source_run_dir=Path(args.source_run_dir),
        target_model_family=args.target_model_family,
        output_dir=Path(args.output_dir),
        seeds=seeds,
    )
