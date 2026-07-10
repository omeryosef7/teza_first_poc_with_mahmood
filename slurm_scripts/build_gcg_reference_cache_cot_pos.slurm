#!/bin/bash

#SBATCH --job-name=gcg_ref_cot_pos
#SBATCH --output=logs/gcg_ref_cot_pos_%j.out
#SBATCH --error=logs/gcg_ref_cot_pos_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# Experiment 5B — Reference hidden-state cache at CoT position 0.
#
# For 5B repr_loss: instead of last-N suffix tokens, we cache the hidden state
# at target_slice.start (= first target token position in teacher-forcing).
# With the CoT target manifest, this is the position of the <think> token,
# i.e. CoT position 0. The reference state = neutral-suffix model at this position.
#
# Requires: --repr-at-cot-pos flag in build_reference_cache.py.
# Suffix length must match the 5B optimization (20 tokens, same as 5A).

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MANIFEST="${PROJECT_DIR}/outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl"
CACHE_DIR="${PROJECT_DIR}/outputs/stage_gcg_full/reference_cache_cot_pos"
LAYERS="${LAYERS:-0,5,10,15,20,25,30,35}"
SUFFIX_LENGTH="${SUFFIX_LENGTH:-20}"
NEUTRAL_TOKEN_ID="${NEUTRAL_TOKEN_ID:-220}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs "$CACHE_DIR"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
export CUDA_LAUNCH_BLOCKING=1

echo "========================================================"
echo "  5B: Reference Cache at CoT Position 0"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
echo "LAYERS:          ${LAYERS}"
echo "SUFFIX_LENGTH:   ${SUFFIX_LENGTH}"
echo "NEUTRAL_TOKEN:   ${NEUTRAL_TOKEN_ID}  (space token)"
echo "CACHE_DIR:       ${CACHE_DIR}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_NAME"

echo ""
echo "--- Building reference cache at CoT position 0 ---"
python -m poc_stage_gcg_early.build_reference_cache \
    --manifest "${MANIFEST}" \
    --cache-dir "${CACHE_DIR}" \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
    --layers "${LAYERS}" \
    --repr-at-cot-pos \
    --suffix-length "${SUFFIX_LENGTH}" \
    --neutral-suffix-token-id "${NEUTRAL_TOKEN_ID}" \
    --split all

echo ""
echo "--- Cache manifest ---"
cat "${CACHE_DIR}/REFERENCE_CACHE_MANIFEST.json" 2>/dev/null || echo "(manifest not written)"

echo ""
echo "========================================================"
echo "  5B Cache Build COMPLETE"
echo "  Cache dir: ${CACHE_DIR}"
echo "  Date: $(date -u)"
echo "========================================================"
