#!/bin/bash

#SBATCH --job-name=gcg_9d_gemma4_rd03
#SBATCH --output=logs/gcg_9d_gemma4_rd03_%j.out
#SBATCH --error=logs/gcg_9d_gemma4_rd03_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Experiment 9D — Gemma4 with λ=0.3 refusal-direction + CoT-prefix (first attempt).
#
# All 7 prior Gemma4 attacks achieved 0% ASR. λ=0.3 refusal-direction suppression
# doubles Qwen3 ASR (10.7% → 24.0%) — testing if the same effect exists on Gemma4.
#
# Gemma4 thinking tags: <|channel>thought ... <channel|> (token IDs 100/101, NOT <think>).
# The manifest and refusal direction file already handle this correctly.
#
# Note on refusal-direction layer: We use L25 (the only precomputed vector).
# L25/40 = 62.5% depth vs Qwen3's L25/32 = 78.1% depth. If 9D gives 0% ASR,
# consider recomputing refusal direction at L31 (78% depth for Gemma4) as follow-up.
#
# After this run completes:
#   Run free-gen eval using run_gcg_full_free_generation.slurm:
#   sbatch --export=ALL,RUN_DIR=<9D-dir>,MANIFEST=<gemma4-manifest> run_gcg_full_free_generation.slurm
#
# Prerequisites:
#   - outputs/stage_gcg_full/advbench_gemma4_cot_manifest_v2.jsonl
#   - outputs/stage_gcg_full/refusal_direction_gemma4_L25.pt

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_gemma4_9d_lambda03_cot}"
MANIFEST_PATH="${MANIFEST_PATH:-${PROJECT_DIR}/outputs/stage_gcg_full/advbench_gemma4_cot_manifest_v2.jsonl}"
REFUSAL_DIR_PATH="${REFUSAL_DIR_PATH:-${PROJECT_DIR}/outputs/stage_gcg_full/refusal_direction_gemma4_L25.pt}"
N_STEPS="${N_STEPS:-500}"
BATCH_SIZE="${BATCH_SIZE:-64}"
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
echo "  Experiment 9D — Gemma4 + λ=0.3 Refusal-Dir + CoT-Prefix"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "MANIFEST:        ${MANIFEST_PATH}"
echo "REFUSAL_DIR:     ${REFUSAL_DIR_PATH}"
echo "LAMBDA_RD:       ${LAMBDA_RD}"
echo "LAYER:           ${REFUSAL_LAYER}"
echo "SEED:            ${SEED}"
echo "NOTE: Gemma4 uses <|channel>thought / <channel|> (NOT <think>)"
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

echo "Sample target: $(head -1 "${MANIFEST_PATH}" | python3 -c "import json,sys; r=json.load(sys.stdin); print(repr(r['safe_target_prefix'][:120]))")"

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint in ${RUN_DIR}"
else
    echo ">>> Starting fresh"
fi

python -m poc_stage_gcg_early.run_optimization \
    --run-id "${RUN_ID}" \
    --model-family gemma4 \
    --model-name-or-path google/gemma-4-E4B-it \
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

GEMMA4_MANIFEST="${MANIFEST_PATH}"
echo ""
echo "Next step — free-gen eval:"
echo "  sbatch --export=ALL,RUN_DIR=${RUN_DIR},MANIFEST=${GEMMA4_MANIFEST} slurm_scripts/run_gcg_full_free_generation.slurm"
echo ""
echo "If ASR=0%: consider recomputing refusal direction at L31 for Gemma4 (78% depth)"
echo "  and rerunning with --refusal-dir-layer 31 --refusal-dir-path .../refusal_direction_gemma4_L31.pt"
echo ""
echo "========================================================"
echo "  Experiment 9D (Gemma4 λ=0.3) COMPLETE"
echo "  Run: ${RUN_ID}"
echo "  $(date -u)"
echo "========================================================"
