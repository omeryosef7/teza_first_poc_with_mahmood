#!/bin/bash

#SBATCH --job-name=gcg_ref_gemma4
#SBATCH --output=logs/gcg_ref_gemma4_%j.out
#SBATCH --error=logs/gcg_ref_gemma4_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Ablation 4C prep — Build Gemma4-E4B-it reference cache for AdvBench manifest.
#
# Builds repr_loss reference cache for all 20 train behaviors in the manifest,
# using Gemma4-E4B-it (42 layers; layers 0,5,...,40 sampled).
#
# Prerequisites: advbench_manifest_v1.jsonl must exist.
#
# Usage:
#   sbatch slurm_scripts/build_gcg_reference_cache_gemma4_full.slurm
#
# Resume: re-run; script skips tasks already cached.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MANIFEST_PATH="${PROJECT_DIR}/outputs/stage_gcg_full/advbench_manifest_v1.jsonl"
OUTPUT_DIR="${PROJECT_DIR}/outputs/stage_gcg_full/reference_cache_gemma4_v1"
MODEL_FAMILY="gemma4"
MODEL_NAME="google/gemma-4-E4B-it"
LAYERS="0,5,10,15,20,25,30,35,40"
REPR_POSITIONS="3"
SUFFIX_LENGTH="20"

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
echo "  Ablation 4C prep — Gemma4 Reference Cache Build (AdvBench)"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "MANIFEST:        ${MANIFEST_PATH}"
echo "OUTPUT_DIR:      ${OUTPUT_DIR}"
echo "MODEL:           ${MODEL_NAME}"
echo "LAYERS:          ${LAYERS}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ ! -f "${MANIFEST_PATH}" ]; then
    echo "ERROR: Manifest not found: ${MANIFEST_PATH}"
    exit 1
fi

echo "Manifest: $(wc -l < "${MANIFEST_PATH}") rows"

python -m poc_stage_gcg_early.build_reference_cache \
    --manifest "${MANIFEST_PATH}" \
    --cache-dir "${OUTPUT_DIR}" \
    --model-family "${MODEL_FAMILY}" \
    --model-name-or-path "${MODEL_NAME}" \
    --layers "${LAYERS}" \
    --repr-positions "${REPR_POSITIONS}" \
    --suffix-length "${SUFFIX_LENGTH}" \
    --split train

echo ""
echo "--- Cache manifest ---"
cat "${OUTPUT_DIR}/REFERENCE_CACHE_MANIFEST.json" 2>/dev/null | head -30 || echo "(no manifest yet)"

echo ""
echo "========================================================"
echo "  Gemma4 Reference Cache Build COMPLETE"
echo "  Output: ${OUTPUT_DIR}"
echo "  $(date -u)"
echo "========================================================"
