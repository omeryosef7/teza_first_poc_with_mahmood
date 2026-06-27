#!/bin/bash

#SBATCH --job-name=stage4_p15
#SBATCH --output=logs/stage4_p15_%j.out
#SBATCH --error=logs/stage4_p15_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-601,n-801,n-802,n-803,n-805

# P15: Gemma4-E4B-IT Attention Pattern Extraction
#
# Runs a single forward pass (teacher-forcing, eager attention) on each
# Gemma4 pure_cot_hijack example to extract per-head attention statistics.
# Tests whether the 56x puzzle_wrapper attention ratio found in Qwen3 (P5a)
# is architecture-general.
#
# Gemma4 pure_cot_hijack examples: n=4 (goals 0, 4, 6, 9)
# Layers analyzed: [3, 10, 17, 24, 35, 45]
# Memory: Gemma4-E4B-IT eager + seq_len 10000 → ~24 GB. Fits on L40S 46GB.
#
# Usage (smoke: 2 examples):
#   SMOKE=1 sbatch slurm_scripts/stage4_p15_gemma4_attention.slurm
# Usage (full: all 4 Gemma4 pure_cot_hijack):
#   sbatch slurm_scripts/stage4_p15_gemma4_attention.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

SMOKE_FLAG="${SMOKE:-0}"
if [ "$SMOKE_FLAG" = "1" ]; then
    OUT_DIR="$PROJECT_DIR/outputs/stage4/gemma4_attention_smoke"
else
    OUT_DIR="$PROJECT_DIR/outputs/stage4/gemma4_attention"
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

echo "Node: $(hostname)"
echo "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo "Smoke: $SMOKE_FLAG"
echo "Output: $OUT_DIR"

if [ "$SMOKE_FLAG" = "1" ]; then
    echo "=== SMOKE MODE: 2 examples ==="
    SMOKE=1 python -m poc_stage4.run_attention_extraction \
        --model gemma4 \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL: all 4 Gemma4 pure_cot_hijack examples ==="
    python -m poc_stage4.run_attention_extraction \
        --model gemma4 \
        --output-dir "$OUT_DIR"
fi

echo "=== Done. Analyzing... ==="
python -c "
import json, sys
from pathlib import Path
out = Path('$OUT_DIR')
files = list((out / 'per_example').glob('*.json')) if (out / 'per_example').exists() else []
print(f'Examples completed: {len(files)}')
for f in sorted(files):
    d = json.loads(f.read_text())
    print(f'  {f.name}: layers={list(d.keys())[:3]}...')
"
