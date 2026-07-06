#!/bin/bash

#SBATCH --job-name=gcg_ref_gemma4
#SBATCH --output=logs/gcg_ref_gemma4_%j.out
#SBATCH --error=logs/gcg_ref_gemma4_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage 10: Reference hidden-state cache for Gemma4-E4B-it.
#
# Gemma4-E4B-it architecture: 42 layers, hidden_size=2560.
# Neutral suffix token: 236743 = '▁' (SentencePiece space marker).
# Positions: last 3 suffix tokens (suffix-relative, non-zero repr gradient).
#
# Output: outputs/stage_gcg_early/reference_cache_gemma4/
# Idempotent: skips tasks already in the cache manifest.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MANIFEST="${PROJECT_DIR}/outputs/stage_gcg_early/surrogate_manifest_v1.jsonl"
CACHE_DIR="${PROJECT_DIR}/outputs/stage_gcg_early/reference_cache_gemma4"
# Layers: every 5 for Gemma4-E4B (42 layers; omit layer 41 to avoid final-norm edge cases)
LAYERS="${LAYERS:-0,5,10,15,20,25,30,35,40}"
REPR_POSITIONS="${REPR_POSITIONS:-3}"
SUFFIX_LENGTH="${SUFFIX_LENGTH:-16}"
# Neutral suffix token: 236743 = '▁' (space marker in Gemma4 SentencePiece vocab)
NEUTRAL_TOKEN_ID="${NEUTRAL_TOKEN_ID:-236743}"

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
echo "  Stage 10: Gemma4 Reference Cache (suffix-relative positions)"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
echo "LAYERS:          ${LAYERS}"
echo "REPR_POSITIONS:  ${REPR_POSITIONS}  (last N suffix tokens)"
echo "SUFFIX_LENGTH:   ${SUFFIX_LENGTH}"
echo "NEUTRAL_TOKEN:   ${NEUTRAL_TOKEN_ID}  (Gemma4 space marker)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_NAME"

echo ""
echo "--- Building Gemma4 reference cache ---"
python -m poc_stage_gcg_early.build_reference_cache \
    --manifest "${MANIFEST}" \
    --cache-dir "${CACHE_DIR}" \
    --model-family gemma4 \
    --model-name-or-path google/gemma-4-E4B-it \
    --layers "${LAYERS}" \
    --repr-positions "${REPR_POSITIONS}" \
    --suffix-length "${SUFFIX_LENGTH}" \
    --neutral-suffix-token-id "${NEUTRAL_TOKEN_ID}" \
    --split all

echo ""
echo "--- Cache manifest ---"
cat "${CACHE_DIR}/REFERENCE_CACHE_MANIFEST.json" 2>/dev/null || echo "(manifest not written)"

echo ""
echo "========================================================"
echo "  Gemma4 Cache Build COMPLETE"
echo "  Cache dir: ${CACHE_DIR}"
echo "  Date: $(date -u)"
echo "========================================================"
