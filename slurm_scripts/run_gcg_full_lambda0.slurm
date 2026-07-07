#!/bin/bash

#SBATCH --job-name=gcg_lambda0
#SBATCH --output=logs/gcg_lambda0_%j.out
#SBATCH --error=logs/gcg_lambda0_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Ablation 4B — Qwen3-14B GCG-Full with lambda_repr=0.0.
#
# Identical to gcg_full_qwen3_weighted except repr_loss is disabled (lambda=0).
# This gives the upper-bound ASR without representation penalty.
# Separates the "CoT-limited" and "repr-conflict-limited" hypotheses.
#
# Usage:
#   sbatch slurm_scripts/run_gcg_full_lambda0.slurm
#
# Resume: re-submit same command; checkpoint.pt detected automatically.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_qwen3_lambda0"
MANIFEST_PATH="${PROJECT_DIR}/outputs/stage_gcg_full/advbench_manifest_v1.jsonl"
REFERENCE_CACHE_DIR="${PROJECT_DIR}/outputs/stage_gcg_full/reference_cache_v1"
LAMBDA_REPR="0.0"
LAMBDA_KL="0.0"
N_STEPS="500"
BATCH_SIZE="64"
SUFFIX_LEN="20"
SEED="42"
SELECTION_MODE="weighted"
REPR_LAYERS="0,5,10,15,20,25,30,35"
REPR_POSITIONS="3"

RUN_ID="gcg_full_qwen3_lambda0"

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
echo "  Ablation 4B — Qwen3-14B GCG-Full (lambda_repr=0.0)"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "LAMBDA_REPR:     ${LAMBDA_REPR}  (repr_loss DISABLED)"
echo "N_STEPS:         ${N_STEPS}"
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

echo "Manifest: $(wc -l < "${MANIFEST_PATH}") rows"

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
    --lambda-repr "${LAMBDA_REPR}" \
    --lambda-kl "${LAMBDA_KL}" \
    --repr-positions "${REPR_POSITIONS}" \
    --repr-layers "${REPR_LAYERS}" \
    --reference-cache-dir "${REFERENCE_CACHE_DIR}" \
    --selection-mode "${SELECTION_MODE}" \
    --checkpoint-every 10 \
    --snapshot-every 50 \
    --split train \
    --no-filter-cand

echo ""
echo "--- Running audit ---"
python -m poc_stage_gcg_early.audit_run --run-dir "${RUN_DIR}" || true

echo ""
echo "--- Running validation ---"
python -m poc_stage_gcg_early.validate_run_outputs --run-dir "${RUN_DIR}" || true

echo ""
echo "========================================================"
echo "  Ablation 4B (lambda_repr=0.0) Optimization COMPLETE"
echo "  Run: ${RUN_ID}"
echo "  $(date -u)"
echo "========================================================"
