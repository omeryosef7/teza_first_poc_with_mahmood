#!/bin/bash

#SBATCH --job-name=gcg_transfer
#SBATCH --output=logs/gcg_transfer_%j.out
#SBATCH --error=logs/gcg_transfer_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage GCG-Early — Cross-model suffix transfer evaluation.
#
# Takes optimized suffixes from a source model run (FINAL_CANDIDATES.jsonl)
# and evaluates them on a different target model. Transfer uses the decoded
# suffix TEXT, not token IDs, because Qwen3 and Gemma4 have different vocabs.
#
# Required env vars:
#   SOURCE_RUN_DIR    — run dir with FINAL_CANDIDATES.jsonl
#   TARGET_MODEL      — "qwen3" or "gemma4"
#   OUTPUT_DIR        — where to write transfer results
#
# Optional:
#   SEEDS             — comma-separated generation seeds (default: 42)
#
# Usage examples:
#   # Qwen3 → Gemma4
#   sbatch --export=ALL,SOURCE_RUN_DIR=outputs/stage_gcg_early/gcg_qwen3_repr_8b,TARGET_MODEL=gemma4,OUTPUT_DIR=outputs/stage_gcg_early/transfer_qwen3_to_gemma4 \
#          slurm_scripts/run_gcg_cross_model_transfer.slurm
#
#   # Gemma4 → Qwen3
#   sbatch --export=ALL,SOURCE_RUN_DIR=outputs/stage_gcg_early/gcg_gemma4_repr_10a,TARGET_MODEL=qwen3,OUTPUT_DIR=outputs/stage_gcg_early/transfer_gemma4_to_qwen3 \
#          slurm_scripts/run_gcg_cross_model_transfer.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
SOURCE_RUN_DIR="${SOURCE_RUN_DIR:-}"
TARGET_MODEL="${TARGET_MODEL:-}"
OUTPUT_DIR="${OUTPUT_DIR:-}"
SEEDS="${SEEDS:-42}"

if [ -z "$SOURCE_RUN_DIR" ] || [ -z "$TARGET_MODEL" ] || [ -z "$OUTPUT_DIR" ]; then
    echo "ERROR: SOURCE_RUN_DIR, TARGET_MODEL, and OUTPUT_DIR must all be set."
    echo "Usage: sbatch --export=ALL,SOURCE_RUN_DIR=...,TARGET_MODEL=...,OUTPUT_DIR=... run_gcg_cross_model_transfer.slurm"
    exit 1
fi

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
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "========================================================"
echo "  Stage GCG-Early — Cross-Model Transfer Evaluation"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "SOURCE_RUN_DIR:  ${SOURCE_RUN_DIR}"
echo "TARGET_MODEL:    ${TARGET_MODEL}"
echo "OUTPUT_DIR:      ${OUTPUT_DIR}"
echo "SEEDS:           ${SEEDS}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ ! -f "${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
    echo "ERROR: FINAL_CANDIDATES.jsonl not found at ${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl"
    echo "Run GCG optimization first."
    exit 1
fi

echo "Source candidates: $(wc -l < "${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl") candidates"

echo ""
echo "--- Running cross-model transfer ---"
python -m poc_stage_gcg_early.evaluate_cross_model_transfer \
    --source-run-dir "$SOURCE_RUN_DIR" \
    --target-model-family "$TARGET_MODEL" \
    --output-dir "$OUTPUT_DIR" \
    --seeds "$SEEDS"

echo ""
echo "--- Transfer results ---"
if [ -f "${OUTPUT_DIR}/FREE_GENERATION_RESULTS.jsonl" ]; then
    echo "FREE_GENERATION_RESULTS.jsonl: $(wc -l < "${OUTPUT_DIR}/FREE_GENERATION_RESULTS.jsonl") rows"
fi
if [ -f "${OUTPUT_DIR}/DETECTION_DELAY_ANALYSIS.md" ]; then
    echo "DETECTION_DELAY_ANALYSIS.md: exists"
fi

echo ""
echo "========================================================"
echo "  Transfer COMPLETE"
echo "  Date: $(date -u)"
echo "========================================================"
