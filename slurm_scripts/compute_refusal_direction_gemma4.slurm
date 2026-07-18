#!/bin/bash

#SBATCH --job-name=refusal_dir_gemma4
#SBATCH --output=logs/refusal_dir_gemma4_%j.out
#SBATCH --error=logs/refusal_dir_gemma4_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Compute v_refusal for Gemma4-E4B at the specified layer (default: 25).
# L25/40=62.5% depth. For 78% depth equivalent (matching Qwen3's L25/32), use LAYER=31.
# Output: outputs/stage_gcg_full/refusal_direction_gemma4_L<LAYER>.pt

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
LAYER="${LAYER:-25}"
OUTPUT="${OUTPUT:-${PROJECT_DIR}/outputs/stage_gcg_full/refusal_direction_gemma4_L${LAYER}.pt}"

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
echo "  Compute Refusal Direction — Gemma4-E4B, Layer ${LAYER}"
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
    --model-family gemma4 \
    --model-name-or-path google/gemma-4-E4B-it \
    --manifest outputs/stage_gcg_full/advbench_manifest_v1.jsonl \
    --layer "${LAYER}" \
    --output "${OUTPUT}"

echo ""
echo "========================================================"
echo "  Refusal Direction (Gemma4) COMPLETE — ${OUTPUT}"
echo "  $(date -u)"
echo "========================================================"
