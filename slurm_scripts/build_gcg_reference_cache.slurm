#!/bin/bash

#SBATCH --job-name=gcg_ref_cache
#SBATCH --output=logs/gcg_ref_cache_%j.out
#SBATCH --error=logs/gcg_ref_cache_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage 5: Reference hidden-state cache building.
# Runs one forward pass per surrogate task using the neutral control suffix (" ")
# and stores hidden states at the selected layers and positions.
# Output: outputs/stage_gcg_early/reference_cache_v1/
# Idempotent: skips tasks already in the cache manifest.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MANIFEST="${PROJECT_DIR}/outputs/stage_gcg_early/surrogate_manifest_v1.jsonl"
CACHE_DIR="${PROJECT_DIR}/outputs/stage_gcg_early/reference_cache_v1"
# Layers: ~every 6 layers + final for Qwen3-14B (48 layers total)
LAYERS="${LAYERS:-0,6,12,18,24,30,36,42,47}"
POSITIONS="${POSITIONS:-0,1,2}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

mkdir -p logs "$CACHE_DIR"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
export CUDA_LAUNCH_BLOCKING=1

echo "========================================================"
echo "  Stage 5: Reference Cache Building"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
echo "LAYERS:          ${LAYERS}"
echo "POSITIONS:       ${POSITIONS}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_NAME"

echo ""
echo "--- Building reference cache ---"
python -m poc_stage_gcg_early.build_reference_cache \
    --manifest "${MANIFEST}" \
    --cache-dir "${CACHE_DIR}" \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
    --layers "${LAYERS}" \
    --positions "${POSITIONS}" \
    --split all

echo ""
echo "--- Cache manifest ---"
cat "${CACHE_DIR}/REFERENCE_CACHE_MANIFEST.json" 2>/dev/null || echo "(manifest not written)"

echo ""
echo "========================================================"
echo "  Stage 5 COMPLETE"
echo "  Cache dir: ${CACHE_DIR}"
echo "  Date: $(date -u)"
echo "========================================================"
