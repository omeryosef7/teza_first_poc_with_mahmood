#!/bin/bash

#SBATCH --job-name=poc_stage4a1_startofthink
#SBATCH --output=logs/poc_stage4a1_startofthink_%j.out
#SBATCH --error=logs/poc_stage4a1_startofthink_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4A1-startofthink: extract refusal direction at the <think> token position.
#
# POSITION: the <think> token (Qwen3 token ID 151667), first generated token.
# METHOD:   enable_thinking=True format; append <think> token to prompt;
#           single forward pass per prompt — NO GENERATION NEEDED.
# CONTRAST: harmful vs harmless vanilla prompts (same as EOI/endofthink).
# SPEED:    ~1-2s per prompt (vs ~10 min/prompt for endofthink). 440 prompts ~ 15-30 min.
#
# SCIENTIFIC PURPOSE:
#   Prior Stage 4C analysis: signal appears at BIN 0 (first 5% of thinking).
#   Hypothesis: representational difference may be established AT the <think> token,
#   before any thinking tokens are generated.
#   Comparison: EOI (prompt end) → startofthink (<think>) → endofthink (</think>).
#
# Output: outputs/stage4/qwen3-14b/refusal_direction_startofthink/

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
NUM_HARMFUL="${NUM_HARMFUL:-220}"
NUM_HARMLESS="${NUM_HARMLESS:-220}"
OVERWRITE="${OVERWRITE:-false}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs outputs "$PROJECT_DIR/.cache"/{huggingface,torch,triton} "$RUNTIME_DIR"/{config,data,runtime,ipython}

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
    --num-harmful "$NUM_HARMFUL"
    --num-harmless "$NUM_HARMLESS"
)

if [ "$OVERWRITE" = "true" ]; then
    ARGS+=(--overwrite)
fi

echo "[stage4a1_startofthink] Starting at $(date) on $(hostname)"
echo "[stage4a1_startofthink] Args: ${ARGS[*]}"

python -m poc_stage4.extract_refusal_direction_startofthink "${ARGS[@]}"

echo "[stage4a1_startofthink] Done at $(date)"
