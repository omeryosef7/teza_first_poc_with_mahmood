#!/bin/bash

#SBATCH --job-name=stage4_rd_L18
#SBATCH --output=logs/stage4_rd_L18_%j.out
#SBATCH --error=logs/stage4_rd_L18_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801

# Stage 4: Qwen3 Refusal Direction — full-scale (n=128) at pos=-4, layer=18.
# Phase C smoke identified pos=-4 L18 (delta=+5.65, KL=0.93) as closest to
# Arditi kl_threshold=1.0 (KL=0.93 < 1.0). Matches Arditi's reported position
# (pos=-4) though at an earlier layer (18 vs ~25). Full-scale run needed to
# confirm whether direction survives kl_threshold=0.1 at n=128.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs \
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

OUTPUT_DIR="outputs/stage4/qwen_rd_fullscale_L18"
mkdir -p "$OUTPUT_DIR"

echo "=== Stage 4: Qwen3 Refusal Direction Full-Scale — Layer 18 ==="
echo "Target: all positions at layer=18 (Phase C smoke: pos=-4 delta=+5.65, KL=0.93)"
echo "Scale: n_train=128 harmful+128 harmless, n_val=32 (Arditi full scale)"
date
hostname
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

python -m poc_stage4.replicate_qwen_rd_exact \
    --phase A \
    --target-layer 18 \
    --output-dir "$OUTPUT_DIR" \
    --also-test-kl-1p0

echo ""
echo "Layer 18 full-scale complete at: $(date)"
echo "Results in: $OUTPUT_DIR/phase_A/selection_result.json"
