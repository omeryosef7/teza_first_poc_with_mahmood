#!/bin/bash

#SBATCH --job-name=gcg_9e_bs128
#SBATCH --output=logs/gcg_9e_bs128_%j.out
#SBATCH --error=logs/gcg_9e_bs128_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Experiment 9E — GCG with batch_size=128 (doubled candidate diversity).
#
# The Zou et al. 2023 reference implementation (llm-attacks/) uses batch_size=512.
# We have been using batch_size=64. More candidates per step = more diverse search
# space = potentially better suffixes found per step.
#
# This experiment tests batch_size=128 as a modest step up.
# Config is otherwise identical to Phase 8 (λ=0.3, seed=42, CoT-prefix manifest).
# Comparison baseline: gcg_full_qwen3_8_rd_lambda03 (batch=64, same other params)
# which achieved 24.0% ASR.
#
# OOM note: If batch_size=128 causes OOM on L40S, reduce BATCH_SIZE to 96.
# L40S has 46GB; Qwen3-14B uses ~28GB; batch_size=128 adds ~7GB for candidate eval.
#
# After optimization completes:
#   sbatch --export=ALL,RUN_DIR=<9e-dir>,MANIFEST=<cot-manifest> slurm_scripts/run_gcg_full_free_generation.slurm
#
# Prerequisites:
#   - outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl
#   - outputs/stage_gcg_full/refusal_direction_qwen3_L25.pt

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_qwen3_9e_bs128_lambda03}"
MANIFEST_PATH="${MANIFEST_PATH:-${PROJECT_DIR}/outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl}"
REFUSAL_DIR_PATH="${REFUSAL_DIR_PATH:-${PROJECT_DIR}/outputs/stage_gcg_full/refusal_direction_qwen3_L25.pt}"
N_STEPS="${N_STEPS:-500}"
BATCH_SIZE="${BATCH_SIZE:-128}"   # Key difference: 128 vs 64
SUFFIX_LEN="${SUFFIX_LEN:-20}"
SEED="${SEED:-42}"
LAMBDA_RD="${LAMBDA_RD:-0.3}"
REFUSAL_LAYER="${REFUSAL_LAYER:-25}"

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
echo "  Experiment 9E — batch_size=128 + λ=0.3 + CoT-Prefix"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "BATCH_SIZE:      ${BATCH_SIZE} (reference uses 512; baseline used 64)"
echo "LAMBDA_RD:       ${LAMBDA_RD}"
echo "SEED:            ${SEED}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

for f in "${MANIFEST_PATH}" "${REFUSAL_DIR_PATH}"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: Required file not found: $f"
        exit 1
    fi
done

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint in ${RUN_DIR}"
else
    echo ">>> Starting fresh (batch_size=${BATCH_SIZE})"
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
    --lambda-refusal-dir "${LAMBDA_RD}" \
    --refusal-dir-layer "${REFUSAL_LAYER}" \
    --refusal-dir-path "${REFUSAL_DIR_PATH}" \
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
echo "Next step — free-gen eval:"
echo "  sbatch --export=ALL,RUN_DIR=${RUN_DIR},MANIFEST=${MANIFEST_PATH} slurm_scripts/run_gcg_full_free_generation.slurm"
echo ""
echo "Compare ASR against gcg_full_qwen3_8_rd_lambda03 (same params, batch_size=64, ASR=24%)"
echo ""
echo "========================================================"
echo "  Experiment 9E (batch_size=128) COMPLETE"
echo "  Run: ${RUN_ID}"
echo "  $(date -u)"
echo "========================================================"
