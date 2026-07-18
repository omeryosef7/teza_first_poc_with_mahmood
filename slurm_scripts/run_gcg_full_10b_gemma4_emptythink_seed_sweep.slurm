#!/bin/bash

#SBATCH --job-name=gcg_10b_gemma4
#SBATCH --output=logs/gcg_10b_gemma4_%j.out
#SBATCH --error=logs/gcg_10b_gemma4_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Track 10B — Gemma4 empty_think seed sweep (seeds 43, 44, 45).
#
# Sprint 3 Track 9G found the first non-zero Gemma4 ASR (2.7%) using empty-think
# targeting with seed=42. Qwen3 showed large seed variance (seed=44→1.3%, seed=45→16%,
# seed=42→24%). This sweep tests whether other seeds find better Gemma4 suffixes.
#
# Config: empty_think target + λ_refusal_dir=0.3 at L31 (Gemma4 refusal depth).
# Each seed runs 500 steps on 25-behavior manifest; then submit free-gen separately.
#
# Usage:
#   sbatch --export=ALL,SEED=43 slurm_scripts/run_gcg_full_10b_gemma4_emptythink_seed_sweep.slurm
#   sbatch --export=ALL,SEED=44 slurm_scripts/run_gcg_full_10b_gemma4_emptythink_seed_sweep.slurm
#   sbatch --export=ALL,SEED=45 slurm_scripts/run_gcg_full_10b_gemma4_emptythink_seed_sweep.slurm
#
# After opt completes (~8h), run free-gen:
#   sbatch --export=ALL,RUN_DIR=outputs/stage_gcg_full/gcg_full_gemma4_10b_emptythink_seed43,\
#     MANIFEST=outputs/stage_gcg_full/advbench_gemma4_cot_manifest_v2_anchor_empty_think.jsonl \
#     slurm_scripts/run_gcg_full_free_generation.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
BASE="${PROJECT_DIR}/outputs/stage_gcg_full"

SEED="${SEED:-43}"
RUN_DIR="${RUN_DIR:-${BASE}/gcg_full_gemma4_10b_emptythink_seed${SEED}}"
MANIFEST="${MANIFEST:-${BASE}/advbench_gemma4_cot_manifest_v2_anchor_empty_think.jsonl}"
REFUSAL_DIR_PATH="${REFUSAL_DIR_PATH:-${BASE}/refusal_direction_gemma4_L31.pt}"
REFUSAL_LAYER="${REFUSAL_LAYER:-31}"
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
echo "  Track 10B — Gemma4 empty_think Seed Sweep"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "SEED:            ${SEED}"
echo "MANIFEST:        ${MANIFEST}"
echo "REFUSAL_DIR:     ${REFUSAL_DIR_PATH}"
echo "LAMBDA_RD:       ${LAMBDA_RD} (L${REFUSAL_LAYER})"
echo "NOTE: 9G seed=42 achieved 2.7% ASR; this sweeps other seeds"
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
    echo ">>> Starting fresh (seed=${SEED})"
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
echo "  10B Gemma4 (seed=${SEED}) COMPLETE — $(date -u)"
echo "========================================================"
