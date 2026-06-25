#!/bin/bash

#SBATCH --job-name=stage4_interv
#SBATCH --output=logs/stage4_interv_%j.out
#SBATCH --error=logs/stage4_interv_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-601,n-801,n-802,n-803,n-805

# Stage 4 Reasoning Intervention Pilot (P4).
#
# Tests whether ablating the behavioral refusal-bypass direction (L26)
# during generation restores model refusal on pure_cot_hijack examples.
#
# Conditions: baseline, full_ablation, answer_only
# Examples: all 4 Qwen3 pure_cot_hijack examples (from mechanism_classification.jsonl)
#           + 4 matched failures (target_easy or universally_resistant)
#
# Direction: outputs/stage4/qwen3-14b/direction_subspace_behavioral/direction_subspace.pt
#            (rank-5 subspace; script picks the L26 row, index 3)
#
# Usage (full pilot):
#   sbatch slurm_scripts/stage4_intervention_pilot.slurm
#
# Usage (smoke: 2 examples, baseline + full_ablation only):
#   SMOKE=1 sbatch slurm_scripts/stage4_intervention_pilot.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

DIRECTION_PATH="outputs/stage4/qwen3-14b/direction_subspace_behavioral/direction_subspace.pt"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR="$PROJECT_DIR/outputs/stage4/intervention_pilot"
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

echo "=== Stage 4 Reasoning Intervention Pilot ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
echo "DIRECTION: $DIRECTION_PATH"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

if [ "$SMOKE_FLAG" = "1" ]; then
    echo "=== SMOKE MODE: 2 examples, baseline + full_ablation ==="
    python -m poc_stage4.run_reasoning_intervention_experiments \
        --model qwen3 \
        --from-mechanism pure_cot_hijack \
        --direction-path "$DIRECTION_PATH" \
        --layer 26 \
        --conditions baseline full_ablation \
        --n-examples 2 \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL PILOT: all pure_cot_hijack examples, 3 conditions ==="
    python -m poc_stage4.run_reasoning_intervention_experiments \
        --model qwen3 \
        --from-mechanism pure_cot_hijack \
        --direction-path "$DIRECTION_PATH" \
        --layer 26 \
        --conditions baseline full_ablation answer_only \
        --output-dir "$OUT_DIR"
fi

echo ""
echo "=== Intervention pilot complete ==="
date

# Print summary if it exists
LATEST_RUN=$(ls -t "$OUT_DIR"/run_* 2>/dev/null | head -1 || true)
if [ -n "$LATEST_RUN" ] && [ -f "$LATEST_RUN/summary.json" ]; then
    echo ""
    echo "=== Summary ==="
    python3 -c "
import json
from pathlib import Path
s = json.loads(Path('$LATEST_RUN/summary.json').read_text())
print(f'Examples: {s[\"n_examples\"]}')
for c, stats in s['by_condition'].items():
    print(f'  {c}: n={stats[\"n\"]} success={stats[\"n_success\"]} ASR={stats[\"asr\"]:.3f}')
print()
print('Decision:', s.get('decision',''))
"
fi
