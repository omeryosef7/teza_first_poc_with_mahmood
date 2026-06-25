#!/bin/bash

#SBATCH --job-name=stage4_g4int
#SBATCH --output=logs/stage4_g4int_%j.out
#SBATCH --error=logs/stage4_g4int_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-601,n-801,n-802,n-803,n-805

# Stage 4 Gemma4 Direction Intervention Pilot (P7).
#
# Analogous to P4 (Qwen3 single-direction ablation) but for Gemma4-E4B-IT.
# Tests whether ablating the behavioral direction (L17/rank4, AUC=0.747) at
# the Gemma4 best behavioral layer restores refusal on pure_cot_hijack examples.
#
# Gemma4 mechanism: puzzle obfuscation (thinking irrelevant; puzzle wrapper drives ASR).
# Prediction: ablation at L17 may be more effective than for Qwen3, since Gemma4's
# EndOfThink and behavioral directions are more aligned (cos=0.679 vs Qwen3's 0.137).
#
# Examples: all 4 Gemma4 pure_cot_hijack examples (n=4, from mechanism_classification)
# Conditions: baseline, full_ablation, answer_only
# Direction: outputs/stage4/gemma4-e4b-it/direction_subspace_behavioral/direction_subspace.pt
#            (rank-5 subspace; script picks the L17 row)
#
# Usage (smoke: 2 examples, baseline + full_ablation):
#   SMOKE=1 sbatch slurm_scripts/stage4_gemma4_intervention.slurm
#
# Usage (full pilot: all 4 pure_cot_hijack examples, 3 conditions):
#   sbatch slurm_scripts/stage4_gemma4_intervention.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

DIRECTION_PATH="outputs/stage4/gemma4-e4b-it/direction_subspace_behavioral/direction_subspace.pt"
OUT_DIR="$PROJECT_DIR/outputs/stage4/gemma4_intervention_pilot"
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

echo "=== Stage 4 Gemma4 Direction Intervention Pilot ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
echo "DIRECTION: $DIRECTION_PATH"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

if [ "$SMOKE_FLAG" = "1" ]; then
    echo "=== SMOKE MODE: 2 examples, baseline + full_ablation ==="
    python -m poc_stage4.run_reasoning_intervention_experiments \
        --model gemma4 \
        --from-mechanism pure_cot_hijack \
        --direction-path "$DIRECTION_PATH" \
        --layer 17 \
        --conditions baseline full_ablation \
        --n-examples 2 \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL PILOT: all 4 Gemma4 pure_cot_hijack examples, 3 conditions ==="
    python -m poc_stage4.run_reasoning_intervention_experiments \
        --model gemma4 \
        --from-mechanism pure_cot_hijack \
        --direction-path "$DIRECTION_PATH" \
        --layer 17 \
        --conditions baseline full_ablation answer_only \
        --output-dir "$OUT_DIR"
fi

echo ""
echo "=== Gemma4 intervention pilot complete ==="
date

LATEST_RUN=$(ls -t "$OUT_DIR"/run_* 2>/dev/null | head -1 || true)
if [ -n "$LATEST_RUN" ] && [ -f "$LATEST_RUN/summary.json" ]; then
    echo ""
    echo "=== Summary ==="
    python3 -c "
import json
from pathlib import Path
s = json.loads(Path('$LATEST_RUN/summary.json').read_text())
print(f'Examples: {s.get(\"n_examples\", \"?\")}')
for c, stats in s.get('by_condition', {}).items():
    print(f'  {c}: n={stats[\"n\"]} ASR={stats[\"asr\"]:.3f}')
"
fi
