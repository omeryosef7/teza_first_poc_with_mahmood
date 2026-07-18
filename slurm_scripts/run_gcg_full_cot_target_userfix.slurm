#!/bin/bash

#SBATCH --job-name=gcg_5a_userfix
#SBATCH --output=logs/gcg_5a_userfix_%j.out
#SBATCH --error=logs/gcg_5a_userfix_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --nodelist=n-801,n-802,n-803,n-805
#SBATCH --exclude=n-804,n-602,n-301

# ============================================================================
# TIER-0 GATE — Experiment 5A (CoT-Prefix Targeting) re-optimized with the
# FIXED optimizer (suffix_placement=user), writing to a NEW v2 output dir.
#
# This is the decision gate for the whole re-run campaign (see
# docs/GCG_BUGFIX_RERUN_PLAN.md): does placing the suffix in the user turn
# (matching eval) change 5A's ASR vs. the v1 (assistant-turn) value of 10.7%?
#
# NOTE: does NOT overwrite v1. v1 lives in outputs/stage_gcg_full/gcg_full_qwen3_cot_target.
# ============================================================================

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-${PROJECT_DIR}/outputs/stage_gcg_full_v2_userfix/gcg_full_qwen3_cot_target}"
MANIFEST_PATH="${MANIFEST_PATH:-${PROJECT_DIR}/outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl}"
N_STEPS="${N_STEPS:-500}"
BATCH_SIZE="${BATCH_SIZE:-64}"
SUFFIX_LEN="${SUFFIX_LEN:-20}"
SEED="${SEED:-42}"
SUFFIX_PLACEMENT="${SUFFIX_PLACEMENT:-user}"

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
echo "  TIER-0 GATE: Experiment 5A re-optimized (FIXED optimizer)"
echo "========================================================"
echo "SUFFIX_PLACEMENT: ${SUFFIX_PLACEMENT} (FIXED = user)"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "MANIFEST:        ${MANIFEST_PATH}"
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
    echo "ERROR: CoT-target manifest not found: ${MANIFEST_PATH}"
    exit 1
fi

echo "Manifest rows: $(wc -l < "${MANIFEST_PATH}")"

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
    --suffix-placement "${SUFFIX_PLACEMENT}" \
    --checkpoint-every 10 \
    --snapshot-every 50 \
    --split train \
    --no-filter-cand

echo ""
echo "--- Verifying the fixed code path was recorded in CONFIG.json ---"
python3 -c "import json; c=json.load(open('${RUN_DIR}/CONFIG.json')); v=c['gcg'].get('suffix_placement'); assert v=='${SUFFIX_PLACEMENT}', f'BUG-STILL-PRESENT: suffix_placement={v!r}'; print('OK: suffix_placement=', v)"

echo ""
echo "--- Running audit + validation ---"
python -m poc_stage_gcg_early.audit_run --run-dir "${RUN_DIR}" || true
python -m poc_stage_gcg_early.validate_run_outputs --run-dir "${RUN_DIR}"

echo ""
echo "========================================================"
echo "  TIER-0 5A (FIXED, user-turn) OPTIMIZATION COMPLETE — ${RUN_ID}"
echo "  Next: free-generation eval, then compare v2 ASR vs v1 10.7%"
echo "  $(date -u)"
echo "========================================================"
