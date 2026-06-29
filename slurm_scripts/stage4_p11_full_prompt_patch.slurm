#!/bin/bash

#SBATCH --job-name=stage4_p11
#SBATCH --output=logs/stage4_p11_%j.out
#SBATCH --error=logs/stage4_p11_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=23:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s

# Stage 4 P11: Full-Prompt Activation Patching.
#
# Extends P6 (end-aligned patching, last 26 positions) to patch ALL positions
# of the attack prompt with D-condition activations (tiled to fill full length).
#
# Scientific question: P6 showed NON-CAUSAL for end-aligned patching.
# P5a showed the harmful encoding is distributed across ALL 1000+ puzzle tokens.
# Does patching ALL positions with D-activations break the attack?
#
# Decision gate:
#   CAUSAL (ASR < 0.5) → attack mechanism distributed across all prompt tokens;
#     patching them all with clean-goal context restores refusal
#   NON-CAUSAL (ASR ≈ 1.0) → mechanism is non-linear or in model weights/attention
#     patterns, not reducible to residual stream activations at any position
#
# Usage (smoke: 2 examples, layers [3, 10, 26]):
#   SMOKE=1 sbatch slurm_scripts/stage4_p11_full_prompt_patch.slurm
#
# Usage (full: all 11 pure_cot_hijack examples, all layers):
#   sbatch slurm_scripts/stage4_p11_full_prompt_patch.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

OUT_DIR="$PROJECT_DIR/outputs/stage4/p11_full_prompt_patch"
SMOKE_FLAG="${SMOKE:-0}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$OUT_DIR" \
    "$RUNTIME_DIR"/{config,data,runtime,ipython} \
    "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONUNBUFFERED=1

echo "=== Stage 4 P11: Full-Prompt Activation Patching ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

if [ "$SMOKE_FLAG" = "1" ]; then
    echo "=== SMOKE MODE: 2 examples, layers [3, 10, 26] ==="
    SMOKE=1 python -m poc_stage4.run_causal_tracing \
        --model qwen3 \
        --n-examples 2 \
        --layers 3 10 26 \
        --patch-mode full_range \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL: all 11 pure_cot_hijack, layers [3,10,17,21,22,23,26,32,39] ==="
    python -m poc_stage4.run_causal_tracing \
        --model qwen3 \
        --layers 3 10 17 21 22 23 26 32 39 \
        --patch-mode full_range \
        --output-dir "$OUT_DIR"
fi

echo ""
echo "=== P11 full-prompt patching complete ==="
date
