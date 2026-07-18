#!/bin/bash

#SBATCH --job-name=gcg_9c_lambda03_s45
#SBATCH --output=logs/gcg_9c_lambda03_s45_%j.out
#SBATCH --error=logs/gcg_9c_lambda03_s45_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Experiment 9C — GCG optimization: λ=0.3 refusal-dir + CoT-prefix + seed=45.
#
# This combination has never been tried. Prior results:
#   - Phase 8 (λ=0.3, seed=42): 24.0% seeded ASR on 25 behaviors
#   - Phase 8 (λ=0.3, seed=43): 12.0% seeded ASR on 25 behaviors
#   - Phase 7B (seed=45, λ=0.0): 16.0% seeded / 21.3% unseeded on 25 behaviors
#
# Hypothesis: the strong seed=45 optimization path combined with weak refusal-
# direction suppression may synergize to achieve the highest per-behavior ASR yet.
#
# After this run completes:
#   1. Submit run_gcg_full_free_generation.slurm (RUN_DIR=...9c...) for 25-behavior eval
#   2. Submit run_gcg_full_9c_full520.slurm for full-scale 520-behavior eval
#
# Prerequisites:
#   - outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl (25-behavior CoT manifest)
#   - outputs/stage_gcg_full/refusal_direction_qwen3_L25.pt (v_refusal vector)

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_qwen3_9c_lambda03_seed45}"
MANIFEST_PATH="${MANIFEST_PATH:-${PROJECT_DIR}/outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl}"
REFUSAL_DIR_PATH="${REFUSAL_DIR_PATH:-${PROJECT_DIR}/outputs/stage_gcg_full/refusal_direction_qwen3_L25.pt}"
N_STEPS="${N_STEPS:-500}"
BATCH_SIZE="${BATCH_SIZE:-64}"
SUFFIX_LEN="${SUFFIX_LEN:-20}"
SEED="${SEED:-45}"
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
echo "  Experiment 9C — CoT-Prefix + λ=0.3 Refusal-Dir + seed=45"
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
echo "Next steps:"
echo "  1. Free-gen (25 behaviors): sbatch --export=ALL,RUN_DIR=${RUN_DIR},MANIFEST=${MANIFEST_PATH} slurm_scripts/run_gcg_full_free_generation.slurm"
echo "  2. Full-520 eval: sbatch slurm_scripts/run_gcg_full_9c_full520.slurm"
echo ""
echo "========================================================"
echo "  Experiment 9C Optimization COMPLETE"
echo "  Run: ${RUN_ID}"
echo "  $(date -u)"
echo "========================================================"
