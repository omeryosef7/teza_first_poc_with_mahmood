#!/bin/bash

#SBATCH --job-name=poc_stage4a1_qwen3_endofthink
#SBATCH --output=logs/poc_stage4a1_qwen3_endofthink_%j.out
#SBATCH --error=logs/poc_stage4a1_qwen3_endofthink_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=23:59:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602

# Stage 4A1-endofthink: extract refusal direction at the </think> token position.
#
# DIFFERENCE FROM stage4a_qwen3_refusal_direction.slurm (EOI extraction):
#   EOI:        extracts at prompt-end offsets (-1,-2,-3,-4), no generation needed
#   Endofthink: generates each prompt with thinking enabled, finds </think>, then
#               captures residual stream activations at that token position.
#
# WHY 36h: each prompt requires a full generation pass (~300-700 thinking tokens)
# followed by a forward pass for activation capture. Sequential per-prompt processing.
# With 220 harmful + 220 harmless prompts (~36 hours estimated on 2 GPUs).
#
# Output: outputs/stage4/qwen3-14b/refusal_direction_endofthink/
#   candidate_directions.pt   [1, n_layers, d_model]
#   direction.pt              provisional best layer (run stage4a2 to validate)
#   skipped_prompts.json      prompts where </think> was not found in max_generation_tokens

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction_endofthink}"
NUM_HARMFUL="${NUM_HARMFUL:-220}"
NUM_HARMLESS="${NUM_HARMLESS:-220}"
MAX_GENERATION_TOKENS="${MAX_GENERATION_TOKENS:-2048}"
SEED="${SEED:-42}"
DIRECTION_NORMALIZATION="${DIRECTION_NORMALIZATION:-unit}"
DRY_RUN="${DRY_RUN:-false}"
OVERWRITE="${OVERWRITE:-true}"
RESUME="${RESUME:-false}"
CHECKPOINT_DIR="${CHECKPOINT_DIR:-}"
USE_BUILTIN_PROMPTS="${USE_BUILTIN_PROMPTS:-false}"

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
    --output-dir "$OUTPUT_DIR"
    --num-harmful "$NUM_HARMFUL"
    --num-harmless "$NUM_HARMLESS"
    --max-generation-tokens "$MAX_GENERATION_TOKENS"
    --seed "$SEED"
    --direction-normalization "$DIRECTION_NORMALIZATION"
    --no-progress
)

if [ "$DRY_RUN" = "true" ]; then
    ARGS+=(--dry-run)
fi

if [ "$RESUME" = "true" ]; then
    ARGS+=(--resume)
elif [ "$OVERWRITE" = "true" ]; then
    ARGS+=(--overwrite)
fi

if [ -n "$CHECKPOINT_DIR" ]; then
    ARGS+=(--checkpoint-dir "$CHECKPOINT_DIR")
fi

if [ "$USE_BUILTIN_PROMPTS" = "true" ]; then
    ARGS+=(--use-builtin-prompts)
fi

python -m poc_stage4.extract_refusal_direction_endofthink "${ARGS[@]}"
