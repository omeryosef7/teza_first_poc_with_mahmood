#!/bin/bash

#SBATCH --job-name=poc_stage4a2_qwen3_subspace
#SBATCH --output=logs/poc_stage4a2_qwen3_subspace_%j.out
#SBATCH --error=logs/poc_stage4a2_qwen3_subspace_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602

# Stage 4A2-subspace: select top-K intervention-validated refusal directions.
#
# SCRIPT: poc_stage4.select_direction_subspace  (NEW multi-direction version)
#         distinct from select_refusal_direction_interventions (single-direction).
#
# INPUT_VARIANT controls which Stage 4A1 output to use:
#   "endofthink" (default): outputs/stage4/qwen3-14b/refusal_direction_endofthink/
#   "behavioral":           outputs/stage4/qwen3-14b/refusal_direction_behavioral/
#
# METHOD: Same intervention filters as original Stage 4A2 (KL threshold, refusal
#   induction, layer pruning). After filtering, top-K survivors are kept as a
#   [K, d_model] subspace tensor for downstream use.
#
# RESUME: pass RESUME=true to continue from existing candidate checkpoints.
#
# Output: outputs/stage4/qwen3-14b/direction_subspace_{endofthink,behavioral}/
#   direction_subspace.pt              [K, d_model]
#   direction_subspace_metadata.json   per-direction origins and intervention scores
#   intervention_candidate_scores.json full per-candidate evaluation

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
INPUT_VARIANT="${INPUT_VARIANT:-endofthink}"   # "endofthink", "behavioral", "startofthink", or any hvp/dvp variant
SUBSPACE_METHOD="${SUBSPACE_METHOD:-intervention}"  # "intervention" or "pca"

# Resolve input/output dirs from variant
if [ "$INPUT_VARIANT" = "behavioral" ]; then
    DEFAULT_INPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction_behavioral"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/direction_subspace_behavioral"
elif [ "$INPUT_VARIANT" = "startofthink" ]; then
    DEFAULT_INPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction_startofthink"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/direction_subspace_startofthink"
elif [ "$INPUT_VARIANT" = "endofthink" ]; then
    DEFAULT_INPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction_endofthink"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/direction_subspace_endofthink"
else
    # Generic fallback for hvp_startofthink, dvp_endofthink, etc.
    DEFAULT_INPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction_${INPUT_VARIANT}"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/direction_subspace_${INPUT_VARIANT}"
fi

INPUT_DIR="${INPUT_DIR:-$DEFAULT_INPUT}"
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT}"

K="${K:-5}"
ENABLE_THINKING="${ENABLE_THINKING:-false}"
BATCH_SIZE="${BATCH_SIZE:-1}"
NUM_HARMFUL_VAL="${NUM_HARMFUL_VAL:-32}"
NUM_HARMLESS_VAL="${NUM_HARMLESS_VAL:-32}"
VALIDATION_SEED="${VALIDATION_SEED:-42}"
KL_THRESHOLD="${KL_THRESHOLD:-0.1}"
INDUCE_REFUSAL_THRESHOLD="${INDUCE_REFUSAL_THRESHOLD:-0.0}"
PRUNE_LAYER_PERCENTAGE="${PRUNE_LAYER_PERCENTAGE:-0.2}"
REFUSAL_TOKEN_STRINGS="${REFUSAL_TOKEN_STRINGS:-I,As}"
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
