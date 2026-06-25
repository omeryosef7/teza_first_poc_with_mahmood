#!/bin/bash

#SBATCH --job-name=stage4_p16
#SBATCH --output=logs/stage4_p16_%j.out
#SBATCH --error=logs/stage4_p16_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-601,n-801,n-802,n-803,n-805

# Stage 4 P16: MLP vs Attention Block Ablation.
#
# Tests whether zeroing the ENTIRE attention sublayer output OR MLP sublayer
# output at layers [10, 26] breaks the CoT hijacking attack.
#
# Coarser than P5b (individual heads) but more powerful: if the attack mechanism
# lives in any part of the attention or MLP computation at these layers,
# this will detect it.
#
# Decision gate:
#   zero_attn_L{l} breaks attack → attention mechanism at layer l is causal
#   zero_mlp_L{l} breaks attack → MLP computation at layer l is causal
#   Both non-causal → mechanism is fundamentally distributed/non-local
#
# Usage (smoke: 2 examples, layers [10, 26]):
#   SMOKE=1 sbatch slurm_scripts/stage4_p16_block_ablation.slurm
#
# Usage (full: all 11 examples):
#   sbatch slurm_scripts/stage4_p16_block_ablation.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

OUT_DIR="$PROJECT_DIR/outputs/stage4/p16_block_ablation"
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

echo "=== Stage 4 P16: MLP vs Attention Block Ablation ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

if [ "$SMOKE_FLAG" = "1" ]; then
    echo "=== SMOKE MODE: 2 examples, layers [10, 26] ==="
    SMOKE=1 python -m poc_stage4.run_block_ablation \
        --model qwen3 \
        --n-examples 2 \
        --layers 10 26 \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL: all 11 pure_cot_hijack, layers [3, 10, 17, 26, 32, 39] ==="
    python -m poc_stage4.run_block_ablation \
        --model qwen3 \
        --layers 3 10 17 26 32 39 \
        --output-dir "$OUT_DIR"
fi

echo ""
echo "=== P16 block ablation complete ==="
date
