#!/bin/bash

#SBATCH --job-name=gcg_t3_dsr1
#SBATCH --output=logs/gcg_t3_dsr1_%j.out
#SBATCH --error=logs/gcg_t3_dsr1_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Sprint 2 / Track 3 -- DeepSeek-R1-Distill-Qwen-7B, core minimal comparison
# (standard target vs. CoT-prefix target, lambda_repr=0 both, matching the
# original 4B-vs-5A pairing that established the Qwen3 CoT-prefix finding).
#
# Verified before writing any of this: DeepSeek-R1-Distill-Qwen-7B's chat
# template always appends <think>\n unconditionally (no enable_thinking
# toggle -- confirmed live from tokenizer_config.json), and it shares Qwen3's
# exact <think>/</think> marker strings (it's a Qwen2.5-backbone distillation).
# model_family="deepseek_r1" was added to run_optimization.py's --model-family
# choices, dispatching to the same generic load_qwen3_model() loader (no
# Qwen3-14B-specific hardcoding in that function).
#
# Usage:
#   sbatch --export=ALL,RUN_DIR=...,MANIFEST_PATH=...,RUN_LABEL=... run_gcg_full_deepseek_r1.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="poc_stage2"
RUN_DIR="${RUN_DIR:?ERROR: RUN_DIR must be set}"
MANIFEST_PATH="${MANIFEST_PATH:?ERROR: MANIFEST_PATH must be set}"
RUN_LABEL="${RUN_LABEL:-deepseek_r1}"
N_STEPS=500
BATCH_SIZE=64
SUFFIX_LEN=20
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
echo "  Sprint 2 Track 3 -- DeepSeek-R1-Distill-Qwen-7B (${RUN_LABEL})"
echo "========================================================"
echo "SLURM_JOB_ID:  ${SLURM_JOB_ID}"
echo "RUN_DIR:       ${RUN_DIR}"
echo "MANIFEST:      ${MANIFEST_PATH}"
echo "DATE:          $(date -u)"
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
echo "Sample target: $(head -1 "${MANIFEST_PATH}" | python3 -c "import json,sys; r=json.load(sys.stdin); print(repr(r['safe_target_prefix'][:100]))")"
echo "Manifest model field: $(head -1 "${MANIFEST_PATH}" | python3 -c "import json,sys; print(json.load(sys.stdin)['model'])")"

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint in ${RUN_DIR}"
else
    echo ">>> Starting fresh"
fi

python -m poc_stage_gcg_early.run_optimization \
    --run-id "${RUN_ID}" \
    --model-family deepseek_r1 \
    --model-name-or-path deepseek-ai/DeepSeek-R1-Distill-Qwen-7B \
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
echo "  Sprint 2 Track 3 (${RUN_LABEL}) COMPLETE"
echo "  Run: ${RUN_ID}"
echo "  $(date -u)"
echo "========================================================"
