#!/bin/bash

#SBATCH --job-name=stage4_attn
#SBATCH --output=logs/stage4_attn_%j.out
#SBATCH --error=logs/stage4_attn_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-601,n-801,n-802,n-803,n-805

# Stage 4C Attention Pattern Extraction (P5a).
#
# Runs a single forward pass (teacher-forcing) on each pure_cot_hijack example
# to extract per-head attention statistics. Uses 'eager' attention implementation
# (not flash attention) so that attention weights are returned.
#
# For each layer (sampled at [3, 10, 20, 26, 35, 40, 47]):
#   - Per-head attention entropy at last 50 thinking tokens
#   - Per-head attention mass on [thinking, answer, user_prompt, system, other] tokens
#
# Memory: Qwen3-14B with eager attention + seq_len 12000 → ~35 GB.
# Fits on L40S 46GB. Sequences > 12000 tokens are skipped.
#
# Usage (smoke: 3 examples):
#   SMOKE=1 sbatch slurm_scripts/stage4_attention_extraction.slurm
#
# Usage (full: all 11 pure_cot_hijack):
#   sbatch slurm_scripts/stage4_attention_extraction.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

# Use fresh directories to avoid stale "skipped" results from prior smoke run
SMOKE_FLAG="${SMOKE:-0}"
if [ "$SMOKE_FLAG" = "1" ]; then
    OUT_DIR="$PROJECT_DIR/outputs/stage4/attention_analysis_smoke_v2"
else
    OUT_DIR="$PROJECT_DIR/outputs/stage4/attention_analysis_v2"
fi

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

echo "=== Stage 4 Attention Extraction (P5a) ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

if [ "$SMOKE_FLAG" = "1" ]; then
    echo "=== SMOKE MODE: 3 examples ==="
    SMOKE=1 python -m poc_stage4.run_attention_extraction \
        --model qwen3 \
        --n-examples 3 \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL: all pure_cot_hijack examples ==="
    python -m poc_stage4.run_attention_extraction \
        --model qwen3 \
        --output-dir "$OUT_DIR"
fi

echo ""
echo "=== Attention extraction complete ==="
date

if [ -f "$OUT_DIR/summary.json" ]; then
    echo ""
    echo "=== Summary ==="
    python3 -c "
import json
from pathlib import Path
s = json.loads(Path('$OUT_DIR/summary.json').read_text())
print(f'Model: {s[\"model\"]}')
print(f'Examples: {s[\"n_examples\"]} (skipped: {s[\"n_skipped\"]})')
print(f'Layers: {s[\"layers_analyzed\"]}')
"
fi
