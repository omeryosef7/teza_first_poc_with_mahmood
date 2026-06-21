#!/bin/bash

#SBATCH --job-name=poc_s4a1_gemma_eot
#SBATCH --output=logs/poc_stage4a1_gemma_endofthink_%j.out
#SBATCH --error=logs/poc_stage4a1_gemma_endofthink_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602,n-302,n-303,n-304,n-305

# Stage 4A1-endofthink (Gemma 4): extract refusal direction at the <channel|> token position.
#
# CONTRAST: harmful vs harmless vanilla prompts.
# POSITION: <channel|> token (Gemma's end-of-thinking marker, analogous to </think>).
# METHOD: generate each prompt with thinking enabled, find <channel|>, then capture
#         residual stream activations at that token position.
#
# Gemma 4 (4B) is ~3x faster than Qwen3 (14B), so 220+220 prompts fit in 8h.
# MAX_GENERATION_TOKENS=2048 — same as Qwen3 endofthink; thinking chains tend to be shorter.
#
# Output: outputs/stage4/gemma4-e4b-it/refusal_direction_endofthink/
#   candidate_directions.pt   [1, n_layers, d_model]
#   direction.pt              provisional best layer (run stage4a2 to validate)
#   skipped_prompts.json      prompts where <channel|> was not found

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/refusal_direction_endofthink}"
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
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONUNBUFFERED=1

echo "[stage4a1_gemma_endofthink] Starting at $(date) on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

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

echo "[stage4a1_gemma_endofthink] Done at $(date)"
