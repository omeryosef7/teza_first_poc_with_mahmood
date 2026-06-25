#!/bin/bash

#SBATCH --job-name=stage4_subsp
#SBATCH --output=logs/stage4_subsp_%j.out
#SBATCH --error=logs/stage4_subsp_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-601,n-801,n-802,n-803,n-805

# Stage 4 Full Behavioral Subspace Ablation (P4b).
#
# Ablates ALL 5 behavioral directions simultaneously at their 5 respective
# layers (L3, L21, L22, L23, L26). Tests whether the full rank-5 subspace
# is causally sufficient to prevent CoT hijacking — a stronger test than P4's
# single-direction ablation (which showed ASR=1.000, McNemar p=1.000).
#
# Conditions:
#   baseline       — no intervention (verification)
#   single_best    — ablate only L26/rank3 (replicate P4 result for comparison)
#   full_subspace  — ablate all 5 directions simultaneously
#
# Expected outcome:
#   If ASR drops significantly in full_subspace condition → mechanism is distributed
#   across the behavioral subspace but captured at rank-5
#   If ASR=1.000 again → mechanism is encoded elsewhere or uses non-linear pathways
#
# Usage (smoke: 3 examples, baseline + full_subspace):
#   SMOKE=1 sbatch slurm_scripts/stage4_subspace_ablation.slurm
#
# Usage (full pilot: all 11 pure_cot_hijack examples, all 3 conditions):
#   sbatch slurm_scripts/stage4_subspace_ablation.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

DIRECTION_PATH="outputs/stage4/qwen3-14b/direction_subspace_behavioral/direction_subspace.pt"
OUT_DIR="$PROJECT_DIR/outputs/stage4/subspace_ablation_pilot"
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

echo "=== Stage 4 Full Behavioral Subspace Ablation ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
echo "DIRECTION: $DIRECTION_PATH"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

if [ "$SMOKE_FLAG" = "1" ]; then
    echo "=== SMOKE MODE: 3 examples, baseline + full_subspace ==="
    python -m poc_stage4.run_subspace_ablation \
        --model qwen3 \
        --from-mechanism pure_cot_hijack \
        --direction-path "$DIRECTION_PATH" \
        --conditions baseline full_subspace \
        --n-examples 3 \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL PILOT: all pure_cot_hijack examples, all 3 conditions ==="
    python -m poc_stage4.run_subspace_ablation \
        --model qwen3 \
        --from-mechanism pure_cot_hijack \
        --direction-path "$DIRECTION_PATH" \
        --conditions baseline single_best full_subspace \
        --output-dir "$OUT_DIR"
fi

echo ""
echo "=== Subspace ablation pilot complete ==="
date

LATEST_RUN=$(ls -t "$OUT_DIR"/run_* 2>/dev/null | head -1 || true)
if [ -n "$LATEST_RUN" ] && [ -f "$LATEST_RUN/summary.json" ]; then
    echo ""
    echo "=== Summary ==="
    python3 -c "
import json
from pathlib import Path
s = json.loads(Path('$LATEST_RUN/summary.json').read_text())
for cond, stats in s['by_condition'].items():
    print(f'{cond:<20} n={stats[\"n\"]:>4} ASR={stats[\"asr\"]:.3f}')
mcn = s.get('mcnemar_baseline_vs_full_subspace', {})
print(f'McNemar (baseline vs full_subspace): b={mcn.get(\"b\",\"?\")}, c={mcn.get(\"c\",\"?\")}, p={mcn.get(\"p_midp\",\"?\")}')
"
fi
