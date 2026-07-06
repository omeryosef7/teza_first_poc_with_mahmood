#!/bin/bash

#SBATCH --job-name=gcg_full_mm
#SBATCH --output=logs/gcg_full_mm_%j.out
#SBATCH --error=logs/gcg_full_mm_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage GCG-Full — Multi-model optimization (Qwen3-14B + Gemma4-E4B, 500 steps, 20 behaviors).
#
# Gradient computed in Qwen3 token space only (tokenizer incompatibility prevents
# joint gradient). Gemma4 task_loss added to candidate selection criterion by
# decode-reencode: Qwen3 tokens → text → Gemma4 tokens → Gemma4 forward pass.
# Final selection = argmin(qwen3_summed_loss + gemma4_task_loss) over top-K candidates.
#
# GPU layout: Qwen3-14B on cuda:0, Gemma4-E4B on cuda:1.
# Memory: Qwen3 ~28GB + Gemma4 ~10GB = ~38GB; fits per-GPU on 46GB L40S.
#
# Usage:
#   sbatch --export=ALL,\
#     RUN_DIR=outputs/stage_gcg_full/gcg_full_multimodel_weighted,\
#     LAMBDA_REPR=1.0,N_STEPS=500 \
#     slurm_scripts/run_gcg_full_multimodel.slurm
#
# Resume: re-submit with same RUN_DIR.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_multimodel_weighted}"
MANIFEST_PATH="${MANIFEST_PATH:-${PROJECT_DIR}/outputs/stage_gcg_full/advbench_manifest_v1.jsonl}"
REFERENCE_CACHE_DIR="${REFERENCE_CACHE_DIR:-${PROJECT_DIR}/outputs/stage_gcg_full/reference_cache_v1}"
LAMBDA_REPR="${LAMBDA_REPR:-1.0}"
LAMBDA_KL="${LAMBDA_KL:-0.0}"
N_STEPS="${N_STEPS:-500}"
BATCH_SIZE="${BATCH_SIZE:-64}"
SUFFIX_LEN="${SUFFIX_LEN:-20}"
SEED="${SEED:-42}"
SELECTION_MODE="${SELECTION_MODE:-weighted}"
REPR_LAYERS="${REPR_LAYERS:-0,5,10,15,20,25,30,35}"
REPR_POSITIONS="${REPR_POSITIONS:-3}"
# Second model: Gemma4 E4B
GEMMA4_MODEL="${GEMMA4_MODEL:-google/gemma-4-E4B-it}"

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
echo "  Stage GCG-Full — Multi-Model Optimization (Qwen3 + Gemma4)"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "MANIFEST:        ${MANIFEST_PATH}"
echo "N_STEPS:         ${N_STEPS}"
echo "SUFFIX_LEN:      ${SUFFIX_LEN}"
echo "BATCH_SIZE:      ${BATCH_SIZE}"
echo "LAMBDA_REPR:     ${LAMBDA_REPR}"
echo "SELECTION_MODE:  ${SELECTION_MODE}"
echo "REPR_LAYERS:     ${REPR_LAYERS}"
echo "GEMMA4_MODEL:    ${GEMMA4_MODEL}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Verify both GPUs are L40S
GPU_COUNT=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
if [ "${GPU_COUNT}" -lt 2 ]; then
    echo "ERROR: Expected 2 GPUs for multi-model run, got ${GPU_COUNT}. Aborting."
    exit 1
fi
while IFS= read -r gpu_name; do
    if [[ "$gpu_name" != *"L40S"* ]]; then
        echo "ERROR: Expected L40S GPU, got: $gpu_name. Aborting."
        exit 1
    fi
done < <(nvidia-smi --query-gpu=name --format=csv,noheader)
echo "GPU check passed: ${GPU_COUNT}× L40S"

if [ ! -f "${MANIFEST_PATH}" ]; then
    echo "ERROR: Manifest not found: ${MANIFEST_PATH}"
    echo "Run build_gcg_advbench_manifest.slurm first."
    exit 1
fi

MANIFEST_ROWS=$(wc -l < "${MANIFEST_PATH}")
echo "Manifest: ${MANIFEST_ROWS} rows"

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint in ${RUN_DIR}"
else
    echo ">>> Starting fresh"
fi

# Qwen3 → cuda:0 (CUDA_VISIBLE_DEVICES order), Gemma4 → cuda:1
# load_qwen3_model / load_gemma4_model use device=0/device=1 automatically
# when launched under 2 GPUs. The run_optimization CLI loads them sequentially.
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
    --no-filter-cand \
    --multi-model-family gemma4 \
    --multi-model-name-or-path "${GEMMA4_MODEL}"

echo ""
echo "--- Running audit ---"
python -m poc_stage_gcg_early.audit_run --run-dir "${RUN_DIR}" || true

echo ""
echo "--- Running validation ---"
python -m poc_stage_gcg_early.validate_run_outputs --run-dir "${RUN_DIR}"

echo ""
echo "========================================================"
echo "  Stage GCG-Full Multi-Model Optimization COMPLETE"
echo "  Run: ${RUN_ID}"
echo "  $(date -u)"
echo "========================================================"
