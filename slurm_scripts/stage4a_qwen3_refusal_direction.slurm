#!/bin/bash

#SBATCH --job-name=poc_stage4a_qwen3_refusal
#SBATCH --output=logs/poc_stage4a_qwen3_refusal_%j.out
#SBATCH --error=logs/poc_stage4a_qwen3_refusal_%j.err
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
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction}"
BATCH_SIZE="${BATCH_SIZE:-1}"
POSITIONS="${POSITIONS:--1,-2,-3,-4}"
ENABLE_THINKING="${ENABLE_THINKING:-false}"
SEED="${SEED:-42}"

# The dry run has already succeeded; default to the fuller Stage 4A1 candidate run.
DRY_RUN="${DRY_RUN:-false}"
NUM_HARMFUL="${NUM_HARMFUL:-64}"
NUM_HARMLESS="${NUM_HARMLESS:-64}"
OVERWRITE="${OVERWRITE:-true}"
USE_BUILTIN_PROMPTS="${USE_BUILTIN_PROMPTS:-false}"
RESUME="${RESUME:-false}"
CHECKPOINT_DIR="${CHECKPOINT_DIR:-}"
NO_PROGRESS="${NO_PROGRESS:-false}"

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
    "--positions=$POSITIONS"
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

if [ "$RESUME" = "true" ]; then
    ARGS+=(--resume)
fi

if [ -n "$CHECKPOINT_DIR" ]; then
    ARGS+=(--checkpoint-dir "$CHECKPOINT_DIR")
fi

if [ "$NO_PROGRESS" = "true" ]; then
    ARGS+=(--no-progress)
fi

python -m poc_stage4.extract_refusal_direction "${ARGS[@]}"
