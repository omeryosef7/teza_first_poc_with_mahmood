#!/bin/bash
#
# Stage 4A1: extract Gemma refusal direction candidates.
# Mirrors stage4a_qwen3_refusal_direction.slurm for google/gemma-4-E4B-it.
# Gemma 4B fits on 1 GPU; thinking is disabled.
#
# After this completes, run stage4a2_gemma_intervention_selection.slurm.
#
# Submit with:
#   sbatch slurm_scripts/stage4a_gemma_refusal_direction.slurm

#SBATCH --job-name=poc_stage4a_gemma_refusal
#SBATCH --output=logs/poc_stage4a_gemma_refusal_%j.out
#SBATCH --error=logs/poc_stage4a_gemma_refusal_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/gemma/refusal_direction}"
BATCH_SIZE="${BATCH_SIZE:-1}"
POSITIONS="${POSITIONS:--1,-2,-3,-4}"
ENABLE_THINKING="${ENABLE_THINKING:-false}"
SEED="${SEED:-42}"

DRY_RUN="${DRY_RUN:-false}"
NUM_HARMFUL="${NUM_HARMFUL:-64}"
NUM_HARMLESS="${NUM_HARMLESS:-64}"
OVERWRITE="${OVERWRITE:-true}"
USE_BUILTIN_PROMPTS="${USE_BUILTIN_PROMPTS:-false}"
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

echo "=== Stage 4A1 Gemma refusal direction extraction started ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""
echo "MODEL_NAME=$MODEL_NAME"
echo "OUTPUT_DIR=$OUTPUT_DIR"

python -m poc_stage4.extract_refusal_direction "${ARGS[@]}"

echo ""
echo "=== Stage 4A1 Gemma refusal direction extraction finished ==="
date
