#!/bin/bash

#SBATCH --job-name=stage4_9_qwen3
#SBATCH --output=logs/stage4_9_qwen3_%A_%a.out
#SBATCH --error=logs/stage4_9_qwen3_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-501,n-601,n-801,n-802,n-803,n-805
#SBATCH --array=4-10%3

# Stage 4.9 Qwen3 extended factorial — goals 4–10 (D/E/F conditions only).
# Array: 1 task per goal. Each task: 2 sources × 3 conditions × 3 seeds = 18 rows.
# All tasks write to the SAME output dir.
#
# Condition A is REUSED from Stage 6 (already in factorial_attack_dataset.jsonl).
# Only D, E, F are generated here.
#
# Submit ONLY after smoke test passes.
# Usage:
#   RUN_DIR=outputs/stage4_8_extended/runs/qwen3_run_<ts> sbatch slurm_scripts/stage4_9_qwen3_goals4_10.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MANIFEST="$PROJECT_DIR/outputs/stage4_8_extended/qwen3_manifest_goals4_10.jsonl"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARRAY_RUN_DIR="${RUN_DIR:-$PROJECT_DIR/outputs/stage4_8_extended/runs/qwen3_run_${SLURM_JOB_ID:-$TIMESTAMP}}"
GOAL_INDEX=$SLURM_ARRAY_TASK_ID

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$ARRAY_RUN_DIR" \
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

echo "=== Stage 4.9 Qwen3 Goals 4-10 Task ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}  SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID:-$GOAL_INDEX}"
echo "GOAL_INDEX=$GOAL_INDEX"
echo "ARRAY_RUN_DIR=$ARRAY_RUN_DIR"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

python -m poc_stage4_8.run_repeated_generations \
    --manifest "$MANIFEST" \
    --output-dir "$ARRAY_RUN_DIR" \
    --model-family qwen3 \
    --goals "$GOAL_INDEX" \
    --skip-judge

echo ""
echo "=== Task ${SLURM_ARRAY_TASK_ID:-$GOAL_INDEX} (goal=$GOAL_INDEX) complete ==="
date

if [ "$GOAL_INDEX" -eq 10 ]; then
    echo ""
    echo "=== Final task: waiting for sibling tasks, then auditing ==="
    sleep 60

    ROW_COUNT=$(python3 - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ.get("ARRAY_RUN_DIR", "")) / "run_summary.jsonl"
if not p.exists():
    print(0)
else:
    rows = [l for l in p.read_text().splitlines() if l.strip()]
    print(len(rows))
PY
)
    echo "Total rows in run_summary.jsonl: $ROW_COUNT"
    EXPECTED=126
    if [ "$ROW_COUNT" -ge "$EXPECTED" ]; then
        echo "Qwen3 goals 4-10 complete ($ROW_COUNT/$EXPECTED rows)."
        echo "Next: rebuild factorial dataset:"
        echo "  python -m poc_stage4.build_factorial_attack_dataset"
    else
        echo "WARNING: only $ROW_COUNT rows — some tasks may not have completed."
    fi
fi
