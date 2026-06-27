#!/bin/bash

#SBATCH --job-name=stage4_rd_exact
#SBATCH --output=logs/stage4_rd_exact_%j.out
#SBATCH --error=logs/stage4_rd_exact_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801

# Stage 4: Exact Qwen3 Refusal Direction Replication (Phase A smoke).
# Fixes 4 bugs from replicate_standard_refusal_direction.py:
#   Bug 1: single-layer → all-layer ablation (3×n_layers hooks)
#   Bug 2: KL with addition hooks → KL with ablation hooks
#   Bug 3: steer_alpha=20.0 → coeff=1.0
#   Bug 4: prune first 20% → prune last 20%
# Phase A targets: pos=-1, layer=26 (exact Arditi et al. reported config).

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

OUTPUT_DIR="outputs/stage4/qwen_rd_exact_replication"
mkdir -p "$OUTPUT_DIR"

echo "=== Stage 4: Exact Qwen3 Refusal Direction Replication ==="
echo "Phase A: single target (pos=-1, layer=26)"
echo "All 4 bugs fixed vs replicate_standard_refusal_direction.py"
date
hostname
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

python -m poc_stage4.replicate_qwen_rd_exact \
    --phase A \
    --output-dir "$OUTPUT_DIR" \
    --smoke

echo ""
echo "Phase A complete at: $(date)"
echo "Results in: $OUTPUT_DIR/phase_A/selection_result.json"
