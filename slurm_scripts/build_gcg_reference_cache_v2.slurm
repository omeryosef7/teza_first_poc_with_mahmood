#!/bin/bash

#SBATCH --job-name=gcg_ref_v2
#SBATCH --output=logs/gcg_ref_v2_%j.out
#SBATCH --error=logs/gcg_ref_v2_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage 8b: Reference hidden-state cache v2 (correct repr_loss positions).
#
# Design: positions 0,1,2 (v1) are before the suffix in causal attention →
# repr gradient is 0. Correct positions: last N tokens of the suffix
# (suffix_slice.stop - N .. suffix_slice.stop - 1), which attend to the
# full prefix + all preceding suffix tokens → non-zero repr gradient.
#
# Uses a same-length neutral suffix ([space_token]*16) so that absolute
# positions for the reference and the candidate are identical.
#
# Output: outputs/stage_gcg_early/reference_cache_v2/
# Idempotent: skips tasks already in the cache manifest.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MANIFEST="${PROJECT_DIR}/outputs/stage_gcg_early/surrogate_manifest_v1.jsonl"
CACHE_DIR="${PROJECT_DIR}/outputs/stage_gcg_early/reference_cache_v2"
# Layers: every 5 for Qwen3-14B (layer 40 = pre-final-norm; omit to avoid norm mismatch)
LAYERS="${LAYERS:-0,5,10,15,20,25,30,35}"
# repr_positions: use last 3 suffix tokens (attend to full suffix context)
REPR_POSITIONS="${REPR_POSITIONS:-3}"
# suffix_length must match optimization run (Stage 8: 16 tokens)
SUFFIX_LENGTH="${SUFFIX_LENGTH:-16}"
# neutral suffix token: 220 = space token in Qwen3/tiktoken
NEUTRAL_TOKEN_ID="${NEUTRAL_TOKEN_ID:-220}"

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
echo "  Stage 8b: Reference Cache v2 (suffix-relative positions)"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
echo "LAYERS:          ${LAYERS}"
echo "REPR_POSITIONS:  ${REPR_POSITIONS}  (last N suffix tokens)"
echo "SUFFIX_LENGTH:   ${SUFFIX_LENGTH}"
echo "NEUTRAL_TOKEN:   ${NEUTRAL_TOKEN_ID}  (space token)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_NAME"

echo ""
echo "--- Building reference cache v2 ---"
python -m poc_stage_gcg_early.build_reference_cache \
    --manifest "${MANIFEST}" \
    --cache-dir "${CACHE_DIR}" \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
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
echo "  Stage 8b Cache Build COMPLETE"
echo "  Cache dir: ${CACHE_DIR}"
echo "  Date: $(date -u)"
echo "========================================================"
