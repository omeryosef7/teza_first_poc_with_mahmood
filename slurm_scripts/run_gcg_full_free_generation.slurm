#!/bin/bash

#SBATCH --job-name=gcg_full_eval
#SBATCH --output=logs/gcg_full_eval_%j.out
#SBATCH --error=logs/gcg_full_eval_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805,t-806

# Stage GCG-Full — Free-generation evaluation of optimized suffixes.
#
# Uses AdvBench manifest (25 behaviors: 20 train + 5 val).
# Generates with optimized suffix and baseline conditions across all behaviors.
# Writes FREE_GENERATION_RESULTS.jsonl; resumable by row_key.
#
# Usage:
#   sbatch --export=ALL,RUN_DIR=outputs/stage_gcg_full/gcg_full_qwen3_weighted \
#          slurm_scripts/run_gcg_full_free_generation.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-}"
MANIFEST="${MANIFEST:-${PROJECT_DIR}/outputs/stage_gcg_full/advbench_manifest_v1.jsonl}"
SEEDS="${SEEDS:-42,43,44}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-2048}"
SPLIT="${SPLIT:-all}"

if [ -z "$RUN_DIR" ]; then
    echo "ERROR: RUN_DIR must be set."
    echo "Usage: sbatch --export=ALL,RUN_DIR=outputs/stage_gcg_full/gcg_full_qwen3_weighted run_gcg_full_free_generation.slurm"
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
echo "  Stage GCG-Full — Free-Generation Evaluation"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "MANIFEST:        ${MANIFEST}"
echo "SEEDS:           ${SEEDS}"
echo "SPLIT:           ${SPLIT}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_NAME"

if [ ! -f "${RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
    echo "ERROR: FINAL_CANDIDATES.jsonl not found at ${RUN_DIR}/FINAL_CANDIDATES.jsonl"
    echo "Optimization must complete before running free-gen."
    exit 1
fi
echo "FINAL_CANDIDATES: $(wc -l < "${RUN_DIR}/FINAL_CANDIDATES.jsonl") entries"

if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: Manifest not found: $MANIFEST"
    exit 1
fi
echo "Manifest: $(wc -l < "$MANIFEST") behaviors"

echo ""
echo "--- Running free-generation evaluation ---"
python - "$RUN_DIR" "$MANIFEST" "$SEEDS" "$MAX_NEW_TOKENS" "$SPLIT" <<'PYEOF'
import sys, json
from pathlib import Path

run_dir   = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
seeds     = [int(s) for s in sys.argv[3].split(",")]
max_new_tokens = int(sys.argv[4])
split     = sys.argv[5]   # "all" | "train" | "val"

import torch
sys.path.insert(0, str(Path(".").resolve()))

from poc_stage_gcg_early.build_safe_surrogate_manifest import load_manifest
from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_all_candidates

print(f"[stage_eval] Loading manifest from {manifest_path}", flush=True)
tasks = load_manifest(manifest_path)
if split != "all":
    tasks = [t for t in tasks if t.split == split]
print(f"[stage_eval] {len(tasks)} tasks (split={split})", flush=True)

config_path = run_dir / "CONFIG.json"
config = json.load(open(config_path))
model_family = config.get("model_family", "qwen3")
model_name = config.get("model_name_or_path", "Qwen/Qwen3-14B")
enable_thinking = config.get("enable_thinking", True)

print(f"[stage_eval] Loading model {model_name} (family={model_family})...", flush=True)
if model_family in ("qwen3", "deepseek_r1"):
    from poc_stage4.qwen3_model import load_qwen3_model
    wrapped = load_qwen3_model(model_name, require_cuda=True, log_device_placement=True)
elif model_family == "gemma4":
    from poc_stage4.qwen3_model import load_gemma4_model
    wrapped = load_gemma4_model(model_name, require_cuda=True, log_device_placement=True)
else:
    raise ValueError(f"Unknown model_family: {model_family}")

model     = wrapped.model
tokenizer = wrapped.tokenizer
model.eval()

evaluate_all_candidates(
    model=model,
    tokenizer=tokenizer,
    model_family=model_family,
    final_candidates_path=run_dir / "FINAL_CANDIDATES.jsonl",
    tasks=tasks,
    enable_thinking=enable_thinking,
    seeds=seeds,
    output_dir=run_dir,
    max_new_tokens=max_new_tokens,
)
PYEOF

echo ""
echo "--- Results summary ---"
RESULTS="${RUN_DIR}/FREE_GENERATION_RESULTS.jsonl"
if [ -f "$RESULTS" ]; then
    echo "Total rows: $(wc -l < "$RESULTS")"
    python3 -c "
import json, collections
rows = [json.loads(l) for l in open('${RESULTS}') if l.strip()]
by_label = collections.Counter(r['condition_label'] for r in rows)
print('Rows by condition:', dict(sorted(by_label.items())))
sr_rows = [r for r in rows if r.get('strongreject_score') is not None]
if sr_rows:
    avg_sr = sum(r['strongreject_score'] for r in sr_rows) / len(sr_rows)
    opt_rows = [r for r in sr_rows if 'optimized' in r.get('condition_label','')]
    opt_avg = sum(r['strongreject_score'] for r in opt_rows)/len(opt_rows) if opt_rows else 0
    base_rows = [r for r in sr_rows if 'neutral' in r.get('condition_label','')]
    base_avg = sum(r['strongreject_score'] for r in base_rows)/len(base_rows) if base_rows else 0
    print(f'Average StrongREJECT (all):       {avg_sr:.3f} (n={len(sr_rows)})')
    print(f'Average StrongREJECT (optimized): {opt_avg:.3f} (n={len(opt_rows)})')
    print(f'Average StrongREJECT (neutral):   {base_avg:.3f} (n={len(base_rows)})')
"
fi

echo ""
echo "========================================================"
echo "  Free-Generation Evaluation COMPLETE"
echo "  Results: ${RESULTS}"
echo "  Date: $(date -u)"
echo "========================================================"
