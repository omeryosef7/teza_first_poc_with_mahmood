#!/bin/bash

#SBATCH --job-name=gcg_seed_eval
#SBATCH --output=logs/gcg_seed_eval_%j.out
#SBATCH --error=logs/gcg_seed_eval_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage GCG-Early — Unseen-seed free-generation evaluation.
#
# Re-evaluates optimized suffixes from a completed run using new generation
# seeds (≠ training seed). Measures whether the optimized suffix generalizes
# to unseen random states or relies on seed-specific model behavior.
#
# Writes to FREE_GENERATION_RESULTS_UNSEEDED.jsonl (separate from original
# FREE_GENERATION_RESULTS.jsonl — does NOT overwrite training-seed results).
#
# Required env vars:
#   RUN_DIR    — completed optimization run directory
#   SEEDS      — comma-separated list of unseen seeds (e.g., "100,200,300")
#
# Usage:
#   sbatch --export=ALL,RUN_DIR=outputs/stage_gcg_early/gcg_qwen3_repr_8b,SEEDS=100,200,300 \
#          slurm_scripts/run_gcg_unseen_seed_eval.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-}"
SEEDS="${SEEDS:-100,200,300}"

if [ -z "$RUN_DIR" ]; then
    echo "ERROR: RUN_DIR must be set."
    echo "Usage: sbatch --export=ALL,RUN_DIR=...,SEEDS=100,200,300 run_gcg_unseen_seed_eval.slurm"
    exit 1
fi

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "========================================================"
echo "  Stage GCG-Early — Unseen-Seed Free-Gen Evaluation"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "SEEDS:           ${SEEDS}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ ! -f "${RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
    echo "ERROR: FINAL_CANDIDATES.jsonl not found at ${RUN_DIR}/FINAL_CANDIDATES.jsonl"
    echo "Run GCG optimization first."
    exit 1
fi

echo "Candidates: $(wc -l < "${RUN_DIR}/FINAL_CANDIDATES.jsonl")"
echo ""
echo "--- Running unseen-seed evaluation ---"

python - "$RUN_DIR" "$SEEDS" <<'PYEOF'
import sys, json
from pathlib import Path
import torch

run_dir = Path(sys.argv[1])
seeds = [int(s) for s in sys.argv[2].split(",")]

sys.path.insert(0, str(Path(".").resolve()))

config = json.load(open(run_dir / "CONFIG.json"))
model_family = config.get("model_family", "qwen3")
model_name = config.get("model_name_or_path", "Qwen/Qwen3-14B")
enable_thinking = config.get("enable_thinking", True)

print(f"[seed_eval] Loading model {model_name}...", flush=True)
if model_family == "qwen3":
    from poc_stage4.qwen3_model import load_qwen3_model
    wrapped = load_qwen3_model(model_name, require_cuda=True, log_device_placement=True)
else:
    from poc_stage4.qwen3_model import load_gemma4_model
    wrapped = load_gemma4_model(require_cuda=True, log_device_placement=True)

model = wrapped.model
tokenizer = wrapped.tokenizer
model.eval()

from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_suffix

manifest_rows = [json.loads(l) for l in open(run_dir / "MANIFEST.jsonl") if l.strip()]
candidates = [json.loads(l) for l in open(run_dir / "FINAL_CANDIDATES.jsonl") if l.strip()]

print(f"[seed_eval] {len(candidates)} candidates, {len(manifest_rows)} tasks, seeds={seeds}", flush=True)

# Write to separate file so we don't touch training-seed results
import os

class UnseedResults:
    """Redirect evaluate_suffix output to FREE_GENERATION_RESULTS_UNSEEDED.jsonl."""
    pass

# We pass output_dir=run_dir but evaluate_suffix appends to FREE_GENERATION_RESULTS.jsonl;
# to use a separate file, we temporarily use a subdirectory approach:
# create a symlink-like shadow dir that forwards the MANIFEST but has its own results file.
unseeded_dir = run_dir / "_unseeded_tmp"
unseeded_dir.mkdir(exist_ok=True)

# Hard-link manifest and config so evaluate_suffix can load them
import shutil
for fname in ["MANIFEST.jsonl", "CONFIG.json"]:
    src = run_dir / fname
    dst = unseeded_dir / fname
    if src.exists() and not dst.exists():
        shutil.copy2(src, dst)

done = 0
for task_data in manifest_rows:
    class Task: pass
    task = Task()
    for k, v in task_data.items():
        setattr(task, k, v)
    task.enable_thinking = (model_family == "qwen3") if not hasattr(task, "enable_thinking") else task.enable_thinking

    for seed in seeds:
        for cand in candidates:
            suffix_str = cand.get("suffix_str", "")
            if not suffix_str:
                continue
            label = f"optimized_{cand.get('selection_mode', 'weighted')}"
            res = evaluate_suffix(
                model, tokenizer, model_family,
                task_id=task.task_id,
                instruction=task.instruction,
                suffix_str=suffix_str,
                suffix_label=label,
                enable_thinking=task.enable_thinking,
                seed=seed,
                output_dir=unseeded_dir,
            )
            if res is not None:
                done += 1
                print(f"[seed_eval] {task.task_id} {label} seed={seed} sr={res.get('strongreject_score')}", flush=True)

        # Baselines
        for suffix_str, label in [
            (task.neutral_control_suffix, "neutral_control"),
            (" " * 16, "random_spaces"),
            (" ", "task_only"),
        ]:
            res = evaluate_suffix(
                model, tokenizer, model_family,
                task_id=task.task_id,
                instruction=task.instruction,
                suffix_str=suffix_str,
                suffix_label=label,
                enable_thinking=task.enable_thinking,
                seed=seed,
                output_dir=unseeded_dir,
            )
            if res is not None:
                done += 1

print(f"[seed_eval] {done} new rows written to {unseeded_dir}/FREE_GENERATION_RESULTS.jsonl", flush=True)

# Copy/move results to canonical unseeded path
results_src = unseeded_dir / "FREE_GENERATION_RESULTS.jsonl"
results_dst = run_dir / "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"

if results_src.exists():
    if results_dst.exists():
        # Append new rows (avoid duplicates by row_key)
        existing_keys = set()
        with open(results_dst) as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_keys.add(json.loads(line).get("row_key", ""))
        new_rows = []
        with open(results_src) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row.get("row_key", "") not in existing_keys:
                    new_rows.append(line)
        with open(results_dst, "a") as f:
            for row_line in new_rows:
                f.write(row_line + "\n")
        print(f"[seed_eval] Appended {len(new_rows)} new rows to {results_dst}", flush=True)
    else:
        shutil.copy2(results_src, results_dst)
        print(f"[seed_eval] Wrote {results_dst}", flush=True)

print(f"[seed_eval] Complete. Final: {results_dst}", flush=True)
PYEOF

echo ""
echo "--- Unseeded results ---"
if [ -f "${RUN_DIR}/FREE_GENERATION_RESULTS_UNSEEDED.jsonl" ]; then
    echo "FREE_GENERATION_RESULTS_UNSEEDED.jsonl: $(wc -l < "${RUN_DIR}/FREE_GENERATION_RESULTS_UNSEEDED.jsonl") rows"
fi

echo ""
echo "--- Running analysis on unseeded results ---"
python -m poc_stage_gcg_early.analyze_detection_delay \
    --run-dir "$RUN_DIR" \
    --results-file "FREE_GENERATION_RESULTS_UNSEEDED.jsonl" 2>&1 || echo "WARNING: analysis failed"

echo ""
echo "========================================================"
echo "  Unseen-Seed Eval COMPLETE"
echo "  Date: $(date -u)"
echo "========================================================"
