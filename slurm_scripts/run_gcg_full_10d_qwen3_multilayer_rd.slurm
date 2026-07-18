#!/bin/bash

#SBATCH --job-name=gcg_10d_multilayer
#SBATCH --output=logs/gcg_10d_multilayer_%j.out
#SBATCH --error=logs/gcg_10d_multilayer_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Track 10D — Multi-layer refusal direction suppression.
#
# Phase 8 found L25 is best single layer, but refusal encoding is distributed.
# This track suppresses it simultaneously at L20 + L25 + L28 with split weights:
#   total_rd_loss = 0.1*rd(L20) + 0.3*rd(L25) + 0.1*rd(L28)
#
# Compare to 10C (single-layer, seed=42): if 10D > 24% ASR, multi-layer is better.
#
# Prerequisites (run first if not already done):
#   sbatch slurm_scripts/compute_refusal_direction_qwen3_L20.slurm
#   sbatch slurm_scripts/compute_refusal_direction_qwen3_L28.slurm
#   (L25 already exists at outputs/stage_gcg_full/refusal_direction_qwen3_L25.pt)
#
# After opt completes (~8h), run free-gen:
#   sbatch --export=ALL,RUN_DIR=outputs/stage_gcg_full/gcg_full_qwen3_10d_multilayer_rd,\
#     MANIFEST=outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl \
#     slurm_scripts/run_gcg_full_free_generation.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
BASE="${PROJECT_DIR}/outputs/stage_gcg_full"

RUN_DIR="${RUN_DIR:-${BASE}/gcg_full_qwen3_10d_multilayer_rd}"
MANIFEST_PATH="${MANIFEST_PATH:-${BASE}/advbench_cot_target_manifest.jsonl}"
RD_L20="${BASE}/refusal_direction_qwen3_L20.pt"
RD_L25="${BASE}/refusal_direction_qwen3_L25.pt"
RD_L28="${BASE}/refusal_direction_qwen3_L28.pt"
SEED="${SEED:-42}"
N_STEPS="${N_STEPS:-500}"
BATCH_SIZE="${BATCH_SIZE:-64}"
SUFFIX_LEN="${SUFFIX_LEN:-20}"

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
echo "  Track 10D — Multi-Layer Refusal Direction Suppression"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "SEED:            ${SEED}"
echo "RD_L20:          ${RD_L20}"
echo "RD_L25:          ${RD_L25}"
echo "RD_L28:          ${RD_L28}"
echo "LOSS:            0.1*rd(L20) + 0.3*rd(L25) + 0.1*rd(L28)"
echo "NOTE: Phase 8 baseline=24.0% (single L25). 10D tests distributed suppression."
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

for f in "${MANIFEST_PATH}" "${RD_L20}" "${RD_L25}" "${RD_L28}"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: Required file not found: $f"
        echo "Run compute_refusal_direction scripts first."
        exit 1
    fi
done

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint"
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
    --lambda-refusal-dir 0.0 \
    --refusal-dir-layers "20,25,28" \
    --refusal-dir-paths "${RD_L20},${RD_L25},${RD_L28}" \
    --lambda-refusal-dir-per-layer "0.1,0.3,0.1" \
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
echo "========================================================"
echo "  10D Qwen3 multi-layer RD COMPLETE — $(date -u)"
echo "========================================================"
