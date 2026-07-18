#!/bin/bash

#SBATCH --job-name=gcg_10c_qwen3
#SBATCH --output=logs/gcg_10c_qwen3_%j.out
#SBATCH --error=logs/gcg_10c_qwen3_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Track 10C — Qwen3 new seed sweep with λ=0.3 + CoT-prefix target.
#
# Best known config: λ=0.3 at L25 + full CoT prefix, seed=42 → 24.0% ASR (25 beh).
# Seeds 42–45 have been tried; this sweeps seeds 0, 1, 2.
# If any seed yields >24%, it becomes the candidate for 520-behavior scaling.
#
# Reference:
#   seed=42 → 24.0% seeded ASR (Phase 8 baseline)
#   seed=45 → 16.0% seeded ASR (7B); λ interaction: -4pp with λ=0.3
#   seeds 0,1,2 → untested
#
# Usage:
#   sbatch --export=ALL,SEED=0 slurm_scripts/run_gcg_full_10c_qwen3_seed_sweep.slurm
#   sbatch --export=ALL,SEED=1 slurm_scripts/run_gcg_full_10c_qwen3_seed_sweep.slurm
#   sbatch --export=ALL,SEED=2 slurm_scripts/run_gcg_full_10c_qwen3_seed_sweep.slurm
#
# After opt completes (~8h), run free-gen:
#   sbatch --export=ALL,RUN_DIR=outputs/stage_gcg_full/gcg_full_qwen3_10c_lambda03_seed0,\
#     MANIFEST=outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl \
#     slurm_scripts/run_gcg_full_free_generation.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
BASE="${PROJECT_DIR}/outputs/stage_gcg_full"

SEED="${SEED:-0}"
RUN_DIR="${RUN_DIR:-${BASE}/gcg_full_qwen3_10c_lambda03_seed${SEED}}"
MANIFEST_PATH="${MANIFEST_PATH:-${BASE}/advbench_cot_target_manifest.jsonl}"
REFUSAL_DIR_PATH="${REFUSAL_DIR_PATH:-${BASE}/refusal_direction_qwen3_L25.pt}"
REFUSAL_LAYER="${REFUSAL_LAYER:-25}"
LAMBDA_RD="${LAMBDA_RD:-0.3}"
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
echo "  Track 10C — Qwen3 New Seed Sweep (λ=0.3, CoT-prefix)"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "SEED:            ${SEED}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "MANIFEST:        ${MANIFEST_PATH}"
echo "REFUSAL_DIR:     ${REFUSAL_DIR_PATH}"
echo "LAMBDA_RD:       ${LAMBDA_RD} (L${REFUSAL_LAYER})"
echo "NOTE: Phase 8 seed=42 baseline=24.0%. Seeds 0,1,2 are untested."
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

echo "Sample target: $(head -1 "${MANIFEST_PATH}" | python3 -c "import json,sys; r=json.load(sys.stdin); print(repr(r['safe_target_prefix'][:100]))")"

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint in ${RUN_DIR}"
else
    echo ">>> Starting fresh (seed=${SEED})"
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
echo "  If ASR > 24%, scale to 520 behaviors."
echo ""
echo "========================================================"
echo "  10C Qwen3 seed=${SEED} COMPLETE — $(date -u)"
echo "========================================================"
