#!/bin/bash

#SBATCH --job-name=gcg_qwen3_opt
#SBATCH --output=logs/gcg_qwen3_opt_%j.out
#SBATCH --error=logs/gcg_qwen3_opt_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=23:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage GCG-Early — Qwen3-14B main optimization (Stage 8 smoke study).
#
# DO NOT SUBMIT until smoke_gcg_qwen3.slurm validation gate passes.
#
# Usage:
#   sbatch --export=ALL,RUN_ID=gcg_qwen3_repr_v1,LAMBDA_REPR=1.0,SUFFIX_LEN=16 \
#          slurm_scripts/run_gcg_qwen3_optimization.slurm
#
# Resume: re-submit with the same RUN_ID — checkpoint.pt detected automatically.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_ID="${RUN_ID:-gcg_qwen3_opt_$(date +%Y%m%d_%H%M%S)}"
MANIFEST_PATH="${PROJECT_DIR}/outputs/stage_gcg_early/surrogate_manifest_v1.jsonl"
OUTPUT_DIR="${PROJECT_DIR}/outputs/stage_gcg_early/${RUN_ID}"
LAMBDA_REPR="${LAMBDA_REPR:-0.0}"
LAMBDA_KL="${LAMBDA_KL:-0.0}"
SUFFIX_LEN="${SUFFIX_LEN:-16}"
N_STEPS="${N_STEPS:-200}"
BATCH_SIZE="${BATCH_SIZE:-64}"
SEED="${SEED:-42}"
REPR_POSITIONS="${REPR_POSITIONS:-3}"
REPR_LAYERS="${REPR_LAYERS:-0,5,10,15,20,25,30,35}"
REFERENCE_CACHE_DIR="${REFERENCE_CACHE_DIR:-${PROJECT_DIR}/outputs/stage_gcg_early/reference_cache_v1}"
SELECTION_MODE="${SELECTION_MODE:-weighted}"
CONSTRAINED_REPR_THRESHOLD="${CONSTRAINED_REPR_THRESHOLD:-0.3}"
LEXICOGRAPHIC_TASK_EPS="${LEXICOGRAPHIC_TASK_EPS:-0.01}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs "$OUTPUT_DIR"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "========================================================"
echo "  Stage GCG-Early — Qwen3-14B Optimization"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "lambda_repr:     ${LAMBDA_REPR}"
echo "lambda_kl:       ${LAMBDA_KL}"
echo "repr_layers:     ${REPR_LAYERS}"
echo "ref_cache_dir:   ${REFERENCE_CACHE_DIR}"
echo "suffix_length:   ${SUFFIX_LEN}"
echo "n_steps:         ${N_STEPS}"
echo "seed:            ${SEED}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ -f "${OUTPUT_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint in ${OUTPUT_DIR}"
else
    echo ">>> Starting fresh"
fi

python -m poc_stage_gcg_early.run_optimization \
    --run-id "${RUN_ID}" \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
    --manifest "${MANIFEST_PATH}" \
    --output-dir "${OUTPUT_DIR}" \
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
    --constrained-repr-threshold "${CONSTRAINED_REPR_THRESHOLD}" \
    --lexicographic-task-eps "${LEXICOGRAPHIC_TASK_EPS}" \
    --no-filter-cand \
    --checkpoint-every 10 \
    --snapshot-every 50 \
    --split train

python -m poc_stage_gcg_early.audit_run --run-dir "${OUTPUT_DIR}"

echo "Done: ${RUN_ID} at $(date -u)"
