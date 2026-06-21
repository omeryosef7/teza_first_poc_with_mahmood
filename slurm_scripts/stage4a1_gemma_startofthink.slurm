#!/bin/bash

#SBATCH --job-name=poc_s4a1_gemma_sot
#SBATCH --output=logs/poc_stage4a1_gemma_startofthink_%j.out
#SBATCH --error=logs/poc_stage4a1_gemma_startofthink_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602,n-302,n-303,n-304,n-305

# Stage 4A1-startofthink (Gemma 4): extract refusal direction at the <|channel>thought token.
#
# POSITION: the <|channel>thought token (Gemma's start-of-thinking marker, analogous to <think>).
#           Single forward pass per prompt — NO GENERATION needed.
# CONTRAST: harmful vs harmless vanilla prompts.
# SPEED: ~1-2s per prompt (no generation); 440 prompts ~ 15-30 min.
#
# SCIENTIFIC PURPOSE: tests whether representational differences exist even before
# any thinking tokens are generated (at the moment the model "decides to think").
#
# Output: outputs/stage4/gemma4-e4b-it/refusal_direction_startofthink/

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
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
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONUNBUFFERED=1

echo "[stage4a1_gemma_startofthink] Starting at $(date) on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

ARGS=(
    --model-family "$MODEL_FAMILY"
    --model-name "$MODEL_NAME"
    --num-harmful "$NUM_HARMFUL"
    --num-harmless "$NUM_HARMLESS"
)

if [ "$OVERWRITE" = "true" ]; then
    ARGS+=(--overwrite)
fi

echo "[stage4a1_gemma_startofthink] Args: ${ARGS[*]}"

python -m poc_stage4.extract_refusal_direction_startofthink "${ARGS[@]}"

echo "[stage4a1_gemma_startofthink] Done at $(date)"
