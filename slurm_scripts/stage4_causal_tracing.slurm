#!/bin/bash

#SBATCH --job-name=stage4_causal
#SBATCH --output=logs/stage4_causal_%j.out
#SBATCH --error=logs/stage4_causal_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-601,n-801,n-802,n-803,n-805

# Stage 4 P6: Causal Tracing / Activation Patching.
#
# For each pure_cot_hijack example, patches the residual stream at specific
# layers with the "clean" (D-condition) activations to find which layer
# mediates the puzzle-wrapper's causal effect on compliance.
#
# Rationale: P4 and P4b showed that linear direction ablation is non-causal.
# Activation patching is a different intervention: instead of REMOVING a
# direction, we REPLACE the full residual stream with the clean baseline.
# If patching layer L restores refusal: L is on the causal path.
#
# This directly tests whether the P4/P4b non-causality is due to:
# (a) Wrong direction choice → patching (which is direction-agnostic) would work
# (b) Mechanism not in residual stream → patching would also fail
#
# Usage (smoke: 2 examples, 3 layers):
#   SMOKE=1 sbatch slurm_scripts/stage4_causal_tracing.slurm
#
# Usage (full: 11 examples, all 9 layers):
#   sbatch slurm_scripts/stage4_causal_tracing.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

OUT_DIR="$PROJECT_DIR/outputs/stage4/causal_tracing"
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

echo "=== Stage 4 Causal Tracing (P6) ==="
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
        --patch-mode all_pos \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL: all 11 pure_cot_hijack examples, 9 layers ==="
    python -m poc_stage4.run_causal_tracing \
        --model qwen3 \
        --patch-mode all_pos \
        --output-dir "$OUT_DIR"
fi

echo ""
echo "=== Causal tracing complete ==="
date
