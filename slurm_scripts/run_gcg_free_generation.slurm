#!/bin/bash

#SBATCH --job-name=gcg_eval
#SBATCH --output=logs/gcg_eval_%j.out
#SBATCH --error=logs/gcg_eval_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage 9: Free-generation evaluation of optimized suffixes.
#
# Generates freely with the optimized suffix and baseline conditions
# (neutral_control, random_spaces, task_only) for all train+val tasks.
# Writes FREE_GENERATION_RESULTS.jsonl; resumable.
#
# Usage:
#   sbatch --export=ALL,RUN_DIR=outputs/stage_gcg_early/gcg_qwen3_repr_8b \
#          slurm_scripts/run_gcg_free_generation.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-${PROJECT_DIR}/outputs/stage_gcg_early/gcg_qwen3_repr_8b}"
MANIFEST="${PROJECT_DIR}/outputs/stage_gcg_early/surrogate_manifest_v1.jsonl"
SEEDS="${SEEDS:-42,43,44}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-2048}"

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
echo "  Stage 9: Free-Generation Evaluation"
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
echo "GPU check passed: $GPU_NAME"

FINAL_CANDS="${RUN_DIR}/FINAL_CANDIDATES.jsonl"
if [ ! -f "$FINAL_CANDS" ]; then
    echo "ERROR: FINAL_CANDIDATES.jsonl not found at ${FINAL_CANDS}"
    exit 1
fi
echo "FINAL_CANDIDATES: $(wc -l < "$FINAL_CANDS") entries"

echo ""
echo "--- Running free-generation evaluation ---"
python - "$RUN_DIR" "$MANIFEST" "$SEEDS" "$MAX_NEW_TOKENS" <<'PYEOF'
import sys, json
from pathlib import Path

run_dir = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
seeds = [int(s) for s in sys.argv[3].split(",")]
max_new_tokens = int(sys.argv[4])

import torch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent) if False else str(Path(".").resolve()))

from poc_stage_gcg_early.build_safe_surrogate_manifest import load_manifest
from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_all_candidates

print(f"[stage9] Loading manifest from {manifest_path}", flush=True)
tasks = load_manifest(manifest_path)
print(f"[stage9] {len(tasks)} tasks", flush=True)

config = json.load(open(run_dir / "CONFIG.json"))
model_family = config.get("model_family", "qwen3")
model_name = config.get("model_name_or_path", "Qwen/Qwen3-14B")
enable_thinking = config.get("enable_thinking", True)

print(f"[stage9] Loading model {model_name}...", flush=True)
if model_family == "qwen3":
    from poc_stage4.qwen3_model import load_qwen3_model
    wrapped = load_qwen3_model(model_name, require_cuda=True, log_device_placement=True)
else:
    from poc_stage4.qwen3_model import load_gemma4_model
    wrapped = load_gemma4_model(require_cuda=True, log_device_placement=True)

model = wrapped.model
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
rows = [json.loads(l) for l in open('${RESULTS}')]
by_label = collections.Counter(r['suffix_label'] for r in rows)
print('Rows by label:', dict(by_label))
sr_rows = [r for r in rows if r.get('strongreject_score') is not None]
if sr_rows:
    avg_sr = sum(r['strongreject_score'] for r in sr_rows) / len(sr_rows)
    print(f'Average StrongREJECT score: {avg_sr:.3f} (n={len(sr_rows)})')
"
fi

echo ""
echo "========================================================"
echo "  Stage 9 COMPLETE"
echo "  Results: ${RESULTS}"
echo "  Date: $(date -u)"
echo "========================================================"
