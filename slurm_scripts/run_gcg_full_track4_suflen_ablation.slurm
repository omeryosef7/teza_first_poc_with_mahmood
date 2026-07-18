#!/bin/bash

#SBATCH --job-name=gcg_t4_suflen
#SBATCH --output=logs/gcg_t4_suflen_%j.out
#SBATCH --error=logs/gcg_t4_suflen_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Sprint 2 / Track 4 — Suffix-length ablation on top of the 5A CoT-prefix recipe.
#
# Every prior Phase 4-8 Qwen3 run used suffix_length=20 (checked across every
# existing CONFIG.json). A longer suffix gives the optimizer more capacity to
# simultaneously satisfy fluency/plausibility and task-compliance signals --
# this is the cheapest, fastest-signal lever in the Track 4 "improve Qwen3
# attack quality" list, so it goes first.
#
# Recipe otherwise identical to gcg_full_qwen3_cot_target (5A): same manifest,
# seed, steps, lambda_repr=0/lambda_kl=0, batch_size, topk -- only SUFFIX_LEN
# differs. RUN_DIR is derived from SUFFIX_LEN so multiple lengths can be run
# without colliding.
#
# Usage:
#   sbatch --export=ALL,SUFFIX_LEN=35 slurm_scripts/run_gcg_full_track4_suflen_ablation.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="poc_stage2"
SUFFIX_LEN="${SUFFIX_LEN:?ERROR: SUFFIX_LEN must be set, e.g. --export=ALL,SUFFIX_LEN=35}"
RUN_DIR="${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_qwen3_track4_suflen${SUFFIX_LEN}_cot_target"
MANIFEST_PATH="${PROJECT_DIR}/outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl"
N_STEPS=500
BATCH_SIZE=64
SEED=42

RUN_ID=$(basename "${RUN_DIR}")

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs "${RUN_DIR}"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "========================================================"
echo "  Sprint 2 Track 4 — Suffix-Length Ablation (len=${SUFFIX_LEN})"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "SUFFIX_LEN:      ${SUFFIX_LEN}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ ! -f "${MANIFEST_PATH}" ]; then
    echo "ERROR: Manifest not found: ${MANIFEST_PATH}"
    exit 1
fi

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint in ${RUN_DIR}"
else
    echo ">>> Starting fresh"
fi

python -m poc_stage_gcg_early.run_optimization \
    --run-id "${RUN_ID}" \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
    --manifest "${MANIFEST_PATH}" \
    --output-dir "${RUN_DIR}" \
    --suffix-length "${SUFFIX_LEN}" \
    --n-steps "${N_STEPS}" \
    --batch-size "${BATCH_SIZE}" \
    --topk 256 \
    --seed "${SEED}" \
    --lambda-repr 0.0 \
    --lambda-kl 0.0 \
    --selection-mode weighted \
    --checkpoint-every 10 \
    --snapshot-every 50 \
    --split train \
    --no-filter-cand

echo ""
echo "--- Running audit ---"
python -m poc_stage_gcg_early.audit_run --run-dir "${RUN_DIR}" || true

echo ""
echo "--- Running validation ---"
python -m poc_stage_gcg_early.validate_run_outputs --run-dir "${RUN_DIR}"

echo ""
echo "--- Running pareto/results-summary analysis (NOT auto-invoked elsewhere -- Phase 8 gap) ---"
python -m poc_stage_gcg_early.analyze_pareto_frontier --run-dir "${RUN_DIR}"

echo ""
echo "========================================================"
echo "  Sprint 2 Track 4 (suffix-length=${SUFFIX_LEN}) COMPLETE"
echo "  Run: ${RUN_ID}"
echo "  $(date -u)"
echo "========================================================"
