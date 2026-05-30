#!/bin/bash

#SBATCH --job-name=poc_stage4a2_qwen3_select
#SBATCH --output=logs/poc_stage4a2_qwen3_select_%j.out
#SBATCH --error=logs/poc_stage4a2_qwen3_select_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-302,n-303,n-304,n-305


set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
INPUT_DIR="${INPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction}"
BATCH_SIZE="${BATCH_SIZE:-1}"
ENABLE_THINKING="${ENABLE_THINKING:-false}"
NUM_HARMFUL_VAL="${NUM_HARMFUL_VAL:-32}"
NUM_HARMLESS_VAL="${NUM_HARMLESS_VAL:-32}"
VALIDATION_SEED="${VALIDATION_SEED:-42}"
KL_THRESHOLD="${KL_THRESHOLD:-0.1}"
INDUCE_REFUSAL_THRESHOLD="${INDUCE_REFUSAL_THRESHOLD:-0.0}"
PRUNE_LAYER_PERCENTAGE="${PRUNE_LAYER_PERCENTAGE:-0.2}"
TOP_K_PROJECTION="${TOP_K_PROJECTION:-}"
DRY_RUN="${DRY_RUN:-false}"
REFUSAL_TOKEN_STRINGS="${REFUSAL_TOKEN_STRINGS:-I,As}"
REFUSAL_TOKEN_IDS="${REFUSAL_TOKEN_IDS:-}"
RESUME="${RESUME:-false}"
CHECKPOINT_DIR="${CHECKPOINT_DIR:-}"
NO_PROGRESS="${NO_PROGRESS:-false}"

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

ARGS=(
    --input-dir "$INPUT_DIR"
    --output-dir "$OUTPUT_DIR"
    --model-name "$MODEL_NAME"
    --enable-thinking "$ENABLE_THINKING"
    --batch-size "$BATCH_SIZE"
    --num-harmful-val "$NUM_HARMFUL_VAL"
    --num-harmless-val "$NUM_HARMLESS_VAL"
    --validation-seed "$VALIDATION_SEED"
    --kl-threshold "$KL_THRESHOLD"
    --induce-refusal-threshold "$INDUCE_REFUSAL_THRESHOLD"
    --prune-layer-percentage "$PRUNE_LAYER_PERCENTAGE"
    --refusal-token-strings "$REFUSAL_TOKEN_STRINGS"
)

if [ -n "$TOP_K_PROJECTION" ]; then
    ARGS+=(--top-k-projection "$TOP_K_PROJECTION")
fi

if [ "$DRY_RUN" = "true" ]; then
    ARGS+=(--dry-run)
fi

if [ -n "$REFUSAL_TOKEN_IDS" ]; then
    ARGS+=(--refusal-token-ids "$REFUSAL_TOKEN_IDS")
fi

if [ "$RESUME" = "true" ]; then
    ARGS+=(--resume)
fi

if [ -n "$CHECKPOINT_DIR" ]; then
    ARGS+=(--checkpoint-dir "$CHECKPOINT_DIR")
fi

if [ "$NO_PROGRESS" = "true" ]; then
    ARGS+=(--no-progress)
fi

python -m poc_stage4.select_refusal_direction_interventions "${ARGS[@]}"
