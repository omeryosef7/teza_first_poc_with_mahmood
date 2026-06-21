#!/bin/bash

#SBATCH --job-name=poc_s4_ptcomp_gemma
#SBATCH --output=logs/poc_stage4_prompt_type_comparison_gemma_%j.out
#SBATCH --error=logs/poc_stage4_prompt_type_comparison_gemma_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602,n-302,n-303,n-304,n-305

# Stage 4 — Prompt-type comparison (Gemma 4).
#
# Projects 3 prompt types onto the behavioral refusal subspace at 3 time points:
#   Prompt types: harmless / direct_harm / puzzle_attack
#   Time points:  startofthink (<|channel>thought) / endofthink (<channel|>) / endofresponse (EOS)
#
# Scientific question: does a puzzle-attack prompt look like harmless or direct-harmful
# in Gemma's refusal subspace?
#
# Must run AFTER stage4a2_gemma_subspace.slurm (behavioral variant) completes.
# Uses puzzle traces from gemma_traces_full_1_11_eos_fixed.
#
# MAX_GEN_TOKENS=4096 (reduced from Qwen3's 8192; Gemma traces are much shorter).
# PYTHONUNBUFFERED=1 ensures per-phase log lines flush immediately (avoiding silent 6h waits).
#
# Output: outputs/stage4/gemma4-e4b-it/prompt_type_comparison_behavioral/

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
SUBSPACE_VARIANT="${SUBSPACE_VARIANT:-behavioral}"
SUBSPACE_DIR="${SUBSPACE_DIR:-$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_${SUBSPACE_VARIANT}}"
STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/gemma_traces_full_1_11_eos_fixed}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/prompt_type_comparison_${SUBSPACE_VARIANT}}"
NUM_HARMLESS="${NUM_HARMLESS:-50}"
NUM_DIRECT_HARM="${NUM_DIRECT_HARM:-50}"
MAX_PUZZLE="${MAX_PUZZLE:-}"
MAX_GEN_TOKENS="${MAX_GEN_TOKENS:-4096}"
MAX_SEQ_LEN="${MAX_SEQ_LEN:-16000}"
FOCUS_LAYERS="${FOCUS_LAYERS:-}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs outputs "$OUTPUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONUNBUFFERED=1

echo "[stage4_ptcomp_gemma] Starting at $(date) on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo "[stage4_ptcomp_gemma] Subspace: ${SUBSPACE_VARIANT} (${SUBSPACE_DIR})"
echo "[stage4_ptcomp_gemma] num_harmless=${NUM_HARMLESS} num_direct_harm=${NUM_DIRECT_HARM}"

ARGS=(
    --model-family "$MODEL_FAMILY"
    --model-name "$MODEL_NAME"
    --subspace-dir "$SUBSPACE_DIR"
    --stage6-input "$STAGE6_INPUT"
    --output-dir "$OUTPUT_DIR"
    --num-harmless "$NUM_HARMLESS"
    --num-direct-harm "$NUM_DIRECT_HARM"
    --max-generation-tokens "$MAX_GEN_TOKENS"
    --max-seq-len "$MAX_SEQ_LEN"
    --no-progress
)

if [ -n "$MAX_PUZZLE" ]; then
    ARGS+=(--max-puzzle "$MAX_PUZZLE")
fi

if [ -n "$FOCUS_LAYERS" ]; then
    ARGS+=(--focus-layers "$FOCUS_LAYERS")
fi

python -m poc_stage4.compare_prompt_projections "${ARGS[@]}"

echo "[stage4_ptcomp_gemma] Done at $(date)"
