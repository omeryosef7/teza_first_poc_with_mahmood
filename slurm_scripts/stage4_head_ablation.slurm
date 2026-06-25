#!/bin/bash

#SBATCH --job-name=stage4_head
#SBATCH --output=logs/stage4_head_%j.out
#SBATCH --error=logs/stage4_head_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-601,n-801,n-802,n-803,n-805

# Stage 4 P5b: Attention Head Ablation.
#
# Informed by P5a attention pattern analysis, zeroes specific attention head
# outputs to test if any head is causally responsible for the CoT hijacking
# attack mechanism.
#
# Target heads (from P5a smoke, n=3): high user_prompt attention + low entropy
#   L10/H33: user_prompt=0.961 (highest), L10/H2: entropy=0.282 (lowest)
#   L10/H19: user_prompt=0.925, L10/H4: entropy=0.293
#   L26/H31: user_prompt=0.912, L26/H29: entropy=1.045
#   L35/H25: entropy=0.460, L35/H37: entropy=0.465
#
# Decision gate:
#   Any single-head ablation with ASR < 0.5 → that head is causally necessary
#   If only multi-head works → mechanism distributed across heads
#   All ASR ≈ 1.0 → heads not causally sufficient (mechanism may be non-linear)
#
# Usage (smoke: 2 examples, top-4 heads):
#   SMOKE=1 sbatch slurm_scripts/stage4_head_ablation.slurm
#
# Usage (full: all 11 pure_cot_hijack examples, 9 heads + combos):
#   sbatch slurm_scripts/stage4_head_ablation.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

OUT_DIR="$PROJECT_DIR/outputs/stage4/head_ablation"
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

echo "=== Stage 4 Attention Head Ablation (P5b) ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

if [ "$SMOKE_FLAG" = "1" ]; then
    echo "=== SMOKE MODE: 2 examples, top-4 target heads ==="
    SMOKE=1 python -m poc_stage4.run_head_ablation \
        --model qwen3 \
        --n-examples 2 \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL: all pure_cot_hijack examples, all 9 target heads + combos ==="
    python -m poc_stage4.run_head_ablation \
        --model qwen3 \
        --output-dir "$OUT_DIR"
fi

echo ""
echo "=== Head ablation complete ==="
date
