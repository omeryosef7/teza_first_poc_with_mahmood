#!/bin/bash

#SBATCH --job-name=gcg_9g_gemma4
#SBATCH --output=logs/gcg_9g_gemma4_%j.out
#SBATCH --error=logs/gcg_9g_gemma4_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Track 9G — CoT Early-Token Anchor Sweep (Gemma4 variants).
#
# Gemma4 has given 0% ASR across 9 attempts. Hypothesis: the refusal mechanism
# is embedded in the thinking block content, and targeting different positions
# within (or bypassing) the thinking block might unlock jailbreaks.
#
# All variants use λ=0.3 + L31 refusal direction (correct depth for Gemma4).
# Gemma4 thinking format: <|channel>thought\n{thinking}\n<channel|>{response}
#
# Anchor variants (set via MANIFEST + RUN_DIR exports):
#   nocot        : advbench_manifest_v1.jsonl → "Sure, here is ..." (no thinking)
#   empty_think  : ..._anchor_empty_think.jsonl → <|channel>thought\n<channel|>Sure,...
#   tok5         : ..._anchor_tok5.jsonl → <|channel>thought\nOkay, I can help with
#   tok1         : ..._anchor_tok1.jsonl → <|channel>thought\nO
#   full_cot     : advbench_gemma4_cot_manifest_v2.jsonl → full short CoT (baseline)
#
# Example submission (empty_think — most promising):
#   BASE="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage_gcg_full"
#   sbatch --export=ALL,\
#     MANIFEST=${BASE}/advbench_gemma4_cot_manifest_v2_anchor_empty_think.jsonl,\
#     RUN_DIR=${BASE}/gcg_full_gemma4_9g_emptythink_L31 \
#     slurm_scripts/run_gcg_full_9g_gemma4.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
BASE="${PROJECT_DIR}/outputs/stage_gcg_full"

RUN_DIR="${RUN_DIR:-${BASE}/gcg_full_gemma4_9g_emptythink_L31}"
MANIFEST="${MANIFEST:-${BASE}/advbench_gemma4_cot_manifest_v2_anchor_empty_think.jsonl}"
MANIFEST_PATH="${MANIFEST}"
REFUSAL_DIR_PATH="${REFUSAL_DIR_PATH:-${BASE}/refusal_direction_gemma4_L31.pt}"
REFUSAL_LAYER="${REFUSAL_LAYER:-31}"
LAMBDA_RD="${LAMBDA_RD:-0.3}"
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
echo "  Track 9G — Gemma4 CoT Anchor Position Sweep"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "MANIFEST:        ${MANIFEST}"
echo "REFUSAL_DIR:     ${REFUSAL_DIR_PATH}"
echo "LAMBDA_RD:       ${LAMBDA_RD} (L${REFUSAL_LAYER})"
echo "SEED:            ${SEED}"
echo "NOTE: Gemma4 thinking format: <|channel>thought / <channel|>"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

for f in "${MANIFEST}" "${REFUSAL_DIR_PATH}"; do
    if [ ! -f "$f" ]; then echo "ERROR: Required file not found: $f"; exit 1; fi
done

echo "Sample target: $(head -1 "${MANIFEST}" | python3 -c "import json,sys; r=json.load(sys.stdin); print(repr(r.get('safe_target_prefix','')[:120]))")"

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint"
else
    echo ">>> Starting fresh"
fi

python -m poc_stage_gcg_early.run_optimization \
    --run-id "${RUN_ID}" \
    --model-family gemma4 \
    --model-name-or-path google/gemma-4-E4B-it \
    --manifest "${MANIFEST}" \
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
echo "  sbatch --export=ALL,RUN_DIR=${RUN_DIR},MANIFEST=${MANIFEST} slurm_scripts/run_gcg_full_free_generation.slurm"
echo ""
echo "========================================================"
echo "  9G Gemma4 (${RUN_ID}) COMPLETE — $(date -u)"
echo "========================================================"
