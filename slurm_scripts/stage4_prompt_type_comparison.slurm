#!/bin/bash

#SBATCH --job-name=poc_s4_ptcomp
#SBATCH --output=logs/poc_stage4_prompt_type_comparison_%j.out
#SBATCH --error=logs/poc_stage4_prompt_type_comparison_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602

# Stage 4 — Prompt-type comparison analysis.
#
# Compares how 3 prompt types project onto the refusal direction subspace
# at 3 time points, answering the core CoT-hijacking question:
#
#   "Does a puzzle-attack prompt look like harmless or direct-harmful in
#    the refusal subspace at startofthink / endofthink / endofresponse?"
#
# Prompt types:
#   harmless      benign requests from refusal_direction/dataset/splits/harmless_train.json
#   direct_harm   unmasked harmful requests from harmful_train.json
#   puzzle_attack CoT-hijacking traces from Stage 6 (pre-computed)
#
# Time points: startofthink (<think>), endofthink (</think>), endofresponse (EOS)
#
# One causal forward pass per prompt covers all 3 time points simultaneously.
# Harmless/direct_harm need model.generate() first (max 8192 new tokens, ~few min each).
# Puzzle: use pre-computed Stage 6 full_prompt_plus_generation_token_ids.
#
# Runtime estimate: 50 harmless + 50 direct_harm × ~3 min/prompt = ~5h; adjust NUM_* to taste.
#
# SUBSPACE_VARIANT controls which refusal direction subspace to use.
# Default: behavioral (direction from complied vs refused at </think>)
# Other options: endofthink, startofthink

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
SUBSPACE_VARIANT="${SUBSPACE_VARIANT:-behavioral}"
SUBSPACE_DIR="${SUBSPACE_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/direction_subspace_${SUBSPACE_VARIANT}}"
STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/all_traces_full_1_11}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/prompt_type_comparison_${SUBSPACE_VARIANT}}"
NUM_HARMLESS="${NUM_HARMLESS:-50}"
NUM_DIRECT_HARM="${NUM_DIRECT_HARM:-50}"
MAX_PUZZLE="${MAX_PUZZLE:-}"        # default: all available
MAX_GEN_TOKENS="${MAX_GEN_TOKENS:-8192}"
MAX_SEQ_LEN="${MAX_SEQ_LEN:-30000}"
FOCUS_LAYERS="${FOCUS_LAYERS:-}"   # default: auto from subspace metadata

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

echo "[stage4_prompt_type_comparison] Starting at $(date) on $(hostname)"
echo "[stage4_prompt_type_comparison] Subspace: ${SUBSPACE_VARIANT} (${SUBSPACE_DIR})"
echo "[stage4_prompt_type_comparison] num_harmless=${NUM_HARMLESS} num_direct_harm=${NUM_DIRECT_HARM}"

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

echo "[stage4_prompt_type_comparison] Done at $(date)"
