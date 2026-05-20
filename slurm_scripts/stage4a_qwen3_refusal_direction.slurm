#!/bin/bash

#SBATCH --job-name=poc_stage4a_qwen3_refusal
#SBATCH --output=logs/poc_stage4a_qwen3_refusal_%j.out
#SBATCH --error=logs/poc_stage4a_qwen3_refusal_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=studentkillable
#SBATCH --account=gpu-students
#SBATCH --exclude=s-002
#SBATCH --gres=gpu:1

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction}"
BATCH_SIZE="${BATCH_SIZE:-1}"
POSITIONS="${POSITIONS:--1,-2,-3}"
ENABLE_THINKING="${ENABLE_THINKING:-false}"
SEED="${SEED:-42}"

# Dry-run defaults to true because Stage 4A1 loads a 14B model and should be
# smoke-tested before larger prompt counts.
DRY_RUN="${DRY_RUN:-true}"
NUM_HARMFUL="${NUM_HARMFUL:-}"
NUM_HARMLESS="${NUM_HARMLESS:-}"
OVERWRITE="${OVERWRITE:-true}"
USE_BUILTIN_PROMPTS="${USE_BUILTIN_PROMPTS:-false}"

cd "$PROJECT_DIR"

# Initialize conda for the batch shell.
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh

# Activate the environment with torch, accelerate, and transformers>=4.51.0.
# Override at submit time with: sbatch --export=CONDA_ENV=your_env ...
conda activate "$CONDA_ENV"

# Load API keys, Hugging Face tokens, and other local environment variables when present.
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs outputs "$OUTPUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

# Keep runtime caches local to the project workspace.
export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"

ARGS=(
    --model-name "$MODEL_NAME"
    --output-dir "$OUTPUT_DIR"
    --batch-size "$BATCH_SIZE"
    --positions "$POSITIONS"
    --enable-thinking "$ENABLE_THINKING"
    --seed "$SEED"
)

if [ "$DRY_RUN" = "true" ]; then
    ARGS+=(--dry-run)
fi

if [ -n "$NUM_HARMFUL" ]; then
    ARGS+=(--num-harmful "$NUM_HARMFUL")
fi

if [ -n "$NUM_HARMLESS" ]; then
    ARGS+=(--num-harmless "$NUM_HARMLESS")
fi

if [ "$OVERWRITE" = "true" ]; then
    ARGS+=(--overwrite)
fi

if [ "$USE_BUILTIN_PROMPTS" = "true" ]; then
    ARGS+=(--use-builtin-prompts)
fi

python -m poc_stage4.extract_refusal_direction "${ARGS[@]}"
