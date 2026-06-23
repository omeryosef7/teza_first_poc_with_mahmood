#!/bin/bash

#SBATCH --job-name=poc_s4a2_gemma_sub
#SBATCH --output=logs/poc_stage4a2_gemma_subspace_%j.out
#SBATCH --error=logs/poc_stage4a2_gemma_subspace_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --exclude=n-601,n-602,n-301

# Stage 4A2-subspace (Gemma 4): select top-K intervention-validated refusal directions.
#
# INPUT_VARIANT controls which Stage 4A1 output to use:
#   "behavioral" (default): outputs/stage4/gemma4-e4b-it/refusal_direction_behavioral/
#   "endofthink":           outputs/stage4/gemma4-e4b-it/refusal_direction_endofthink/
#   "startofthink":         outputs/stage4/gemma4-e4b-it/refusal_direction_startofthink/
#   "endofresponse":        outputs/stage4/gemma4-e4b-it/refusal_direction_endofresponse/
#
# Submit once per variant:
#   sbatch slurm_scripts/stage4a2_gemma_subspace.slurm
#   INPUT_VARIANT=endofthink sbatch slurm_scripts/stage4a2_gemma_subspace.slurm
#   INPUT_VARIANT=startofthink sbatch slurm_scripts/stage4a2_gemma_subspace.slurm
#   INPUT_VARIANT=endofresponse sbatch slurm_scripts/stage4a2_gemma_subspace.slurm
#
# REFUSAL_TOKEN_STRINGS: tune after inspecting actual Gemma 4 refusal outputs.
#   Gemma typically starts refusals with "I" or "I'm" — same as default "I,As".
#
# Output: outputs/stage4/gemma4-e4b-it/direction_subspace_{variant}/

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
INPUT_VARIANT="${INPUT_VARIANT:-behavioral}"
SUBSPACE_METHOD="${SUBSPACE_METHOD:-intervention}"  # "intervention" or "pca"

# Resolve input/output dirs from variant
if [ "$INPUT_VARIANT" = "behavioral" ]; then
    DEFAULT_INPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/refusal_direction_behavioral"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_behavioral"
elif [ "$INPUT_VARIANT" = "startofthink" ]; then
    DEFAULT_INPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/refusal_direction_startofthink"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_startofthink"
elif [ "$INPUT_VARIANT" = "endofresponse" ]; then
    DEFAULT_INPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/refusal_direction_endofresponse"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_endofresponse"
elif [ "$INPUT_VARIANT" = "endofthink" ]; then
    DEFAULT_INPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/refusal_direction_endofthink"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_endofthink"
else
    # Generic fallback for hvp_startofthink, dvp_endofthink, etc.
    DEFAULT_INPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/refusal_direction_${INPUT_VARIANT}"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_${INPUT_VARIANT}"
fi

INPUT_DIR="${INPUT_DIR:-$DEFAULT_INPUT}"
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT}"

K="${K:-5}"
ENABLE_THINKING="${ENABLE_THINKING:-true}"
BATCH_SIZE="${BATCH_SIZE:-1}"
NUM_HARMFUL_VAL="${NUM_HARMFUL_VAL:-32}"
NUM_HARMLESS_VAL="${NUM_HARMLESS_VAL:-32}"
VALIDATION_SEED="${VALIDATION_SEED:-42}"
KL_THRESHOLD="${KL_THRESHOLD:-1000.0}"
INDUCE_REFUSAL_THRESHOLD="${INDUCE_REFUSAL_THRESHOLD:--1000.0}"
PRUNE_LAYER_PERCENTAGE="${PRUNE_LAYER_PERCENTAGE:-0.2}"
REFUSAL_TOKEN_STRINGS="${REFUSAL_TOKEN_STRINGS:-I,As}"
# Gemma 4: harmless_ablation_kl_divergence is high for all layers (directions affect all behavior).
# Filter logic: KL must be BELOW threshold, steering must be ABOVE threshold.
# Setting KL_THRESHOLD=1000 and INDUCE_REFUSAL_THRESHOLD=-1000 accepts all 42 candidates;
# selection is then by lowest harmful_ablation_refusal_score (most refusal-reducing).
NO_LAYER_PRUNING="${NO_LAYER_PRUNING:-true}"
DRY_RUN="${DRY_RUN:-false}"
RESUME="${RESUME:-false}"
CHECKPOINT_DIR="${CHECKPOINT_DIR:-}"

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

echo "[stage4a2_gemma_subspace] Starting at $(date) on $(hostname)"
echo "[stage4a2_gemma_subspace] INPUT_VARIANT=${INPUT_VARIANT}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

ARGS=(
    --model-family "$MODEL_FAMILY"
    --model-name "$MODEL_NAME"
    --input-dir "$INPUT_DIR"
    --output-dir "$OUTPUT_DIR"
    --k "$K"
    --enable-thinking "$ENABLE_THINKING"
    --batch-size "$BATCH_SIZE"
    --num-harmful-val "$NUM_HARMFUL_VAL"
    --num-harmless-val "$NUM_HARMLESS_VAL"
    --validation-seed "$VALIDATION_SEED"
    --kl-threshold "$KL_THRESHOLD"
    --induce-refusal-threshold "$INDUCE_REFUSAL_THRESHOLD"
    --prune-layer-percentage "$PRUNE_LAYER_PERCENTAGE"
    --refusal-token-strings "$REFUSAL_TOKEN_STRINGS"
    --no-progress
)

if [ "$NO_LAYER_PRUNING" = "true" ]; then
    ARGS+=(--no-layer-pruning)
fi

if [ "$DRY_RUN" = "true" ]; then
    ARGS+=(--dry-run)
fi

if [ "$RESUME" = "true" ]; then
    ARGS+=(--resume)
fi

if [ -n "$CHECKPOINT_DIR" ]; then
    ARGS+=(--checkpoint-dir "$CHECKPOINT_DIR")
fi

ARGS+=(--subspace-method "$SUBSPACE_METHOD")

python -m poc_stage4.select_direction_subspace "${ARGS[@]}"

echo "[stage4a2_gemma_subspace] Done at $(date)"
