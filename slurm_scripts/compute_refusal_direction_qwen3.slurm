#!/bin/bash

#SBATCH --job-name=refusal_dir_qwen3
#SBATCH --output=logs/refusal_dir_qwen3_%j.out
#SBATCH --error=logs/refusal_dir_qwen3_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,t-806

# Compute v_refusal for Qwen3-14B at layer 25.
# Based on CoT Hijacking paper (Zhao et al. 2026): ablating v_refusal at L25
# raises Qwen3-14B ASR from 11% to 91%.
# Output: outputs/stage_gcg_full/refusal_direction_qwen3_L25.pt

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
LAYER="${LAYER:-25}"
OUTPUT="${OUTPUT:-${PROJECT_DIR}/outputs/stage_gcg_full/refusal_direction_qwen3_L25.pt}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs outputs/stage_gcg_full

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"

echo "========================================================"
echo "  Compute Refusal Direction — Qwen3-14B, Layer ${LAYER}"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "LAYER:           ${LAYER}"
echo "OUTPUT:          ${OUTPUT}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

python -m poc_stage_gcg_early.compute_refusal_direction \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
    --manifest outputs/stage_gcg_full/advbench_manifest_v1.jsonl \
    --layer "${LAYER}" \
    --output "${OUTPUT}"

echo ""
echo "========================================================"
echo "  Refusal Direction (Qwen3) COMPLETE — ${OUTPUT}"
echo "  $(date -u)"
echo "========================================================"
