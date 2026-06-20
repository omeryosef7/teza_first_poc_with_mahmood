#!/bin/bash

#SBATCH --job-name=poc_stage4a1_qwen3_endofthink_smoke
#SBATCH --output=logs/poc_stage4a1_qwen3_endofthink_smoke_%j.out
#SBATCH --error=logs/poc_stage4a1_qwen3_endofthink_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602

# Stage 4A1-endofthink SMOKE TEST — 4 prompts each, 1 GPU, 30 min.
# Run this before submitting stage4a1_qwen3_endofthink.slurm (the 36h full run).
#
# Checks:
#   - Model loads correctly on a single GPU
#   - </think> token is found in generated sequences
#   - Activation capture runs without OOM
#   - Output files are written correctly
#
# On success you will see: "Wrote Stage 4A1-endofthink artifacts to: ..."
# Check skipped_prompts.json — if all 4 prompts are skipped, increase
# --max-generation-tokens in the full run.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction_endofthink_smoke}"

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

python -m poc_stage4.extract_refusal_direction_endofthink \
    --model-family "$MODEL_FAMILY" \
    --model-name "$MODEL_NAME" \
    --output-dir "$OUTPUT_DIR" \
    --dry-run \
    --overwrite \
    --no-progress
