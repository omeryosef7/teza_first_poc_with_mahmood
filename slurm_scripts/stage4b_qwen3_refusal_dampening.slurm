#!/bin/bash

#SBATCH --job-name=poc_stage4b_qwen3_dampen
#SBATCH --output=logs/poc_stage4b_qwen3_dampen_%j.out
#SBATCH --error=logs/poc_stage4b_qwen3_dampen_%j.err
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
DIRECTION_DIR="${DIRECTION_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction}"
ALLOW_PROVISIONAL_DIRECTION="${ALLOW_PROVISIONAL_DIRECTION:-false}"
if [ "${ALLOW_PROVISIONAL_DIRECTION:-false}" = "true" ]; then
    OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_dampening_debug}"
else
    OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_dampening}"
fi
STAGE2_JSONL="${STAGE2_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small.jsonl}"
ENABLE_THINKING="${ENABLE_THINKING:-false}"
NUM_GOALS="${NUM_GOALS:-2}"
DRY_RUN="${DRY_RUN:-true}"
BATCH_SIZE="${BATCH_SIZE:-1}"
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
    --model-name "$MODEL_NAME"
    --direction-dir "$DIRECTION_DIR"
    --output-dir "$OUTPUT_DIR"
    --stage2-jsonl "$STAGE2_JSONL"
    --enable-thinking "$ENABLE_THINKING"
    --num-goals "$NUM_GOALS"
    --batch-size "$BATCH_SIZE"
)

if [ "$DRY_RUN" = "true" ]; then
    ARGS+=(--dry-run)
fi

if [ "$ALLOW_PROVISIONAL_DIRECTION" = "true" ]; then
    ARGS+=(--allow-provisional-direction)
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

python -m poc_stage4.measure_refusal_dampening "${ARGS[@]}"
