#!/bin/bash

#SBATCH --job-name=stage4_8_g_q3_l40s
#SBATCH --output=logs/stage4_8_cond_g_goals4_10_qwen3_l40s_%A_%a.out
#SBATCH --error=logs/stage4_8_cond_g_goals4_10_qwen3_l40s_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805
#SBATCH --array=4-10%3

# Stage 4.8 condition-G goals 4-10 Qwen3 — L40S ONLY retry.
# n-801,n-802,n-803,n-805 only (all L40S 46GB). Excludes n-501/n-601 (A5000 24GB).
# Previous job 618309 landed on n-501 (A5000 24GB) which is insufficient for
# Qwen3-14B (28GB bfloat16) — resulted in CPU offloading and >3h per generation.
#
# Skip already-done rows using --force=False (default). Resubmit after 618309 fails.
#
# Submit:
#   RUN_DIR=outputs/stage4_8_extended/runs/run_cond_g_qwen3_goals4_10_1782547135 \
#     sbatch slurm_scripts/stage4_8_cond_g_goals4_10_qwen3_l40s.slurm
# (same RUN_DIR so already-done rows are skipped automatically)

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MANIFEST="$PROJECT_DIR/outputs/stage4_8_extended/repeated_generation_manifest_cond_g_qwen3_goals4_10.jsonl"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARRAY_RUN_DIR="${RUN_DIR:-$PROJECT_DIR/outputs/stage4_8_extended/runs/run_cond_g_qwen3_goals4_10_${SLURM_JOB_ID:-$TIMESTAMP}}"
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

echo "=== Stage 4.8 Condition-G Goals 4-10 (Qwen3, L40S retry) Array Task ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}  SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID:-$GOAL_INDEX}"
echo "GOAL_INDEX=$GOAL_INDEX"
echo "ARRAY_RUN_DIR=$ARRAY_RUN_DIR"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

# Verify we are on L40S (abort if not — prevents repeat of n-501 CPU-offload issue)
GPU_TYPE=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
if echo "$GPU_TYPE" | grep -qi "A5000\|A4000\|A2000"; then
    echo "ERROR: GPU is $GPU_TYPE — not L40S. Aborting to prevent CPU offloading."
    exit 1
fi
echo "GPU check passed: $GPU_TYPE"

python -m poc_stage4_8.run_repeated_generations \
    --manifest "$MANIFEST" \
    --output-dir "$ARRAY_RUN_DIR" \
    --model-family qwen3 \
    --goals "$GOAL_INDEX" \
    --conditions G \
    --skip-judge

echo ""
echo "=== Task ${SLURM_ARRAY_TASK_ID:-$GOAL_INDEX} (goal=$GOAL_INDEX) complete ==="
date

if [ "$GOAL_INDEX" -eq 10 ]; then
    echo ""
    echo "=== Final task: auditing row count ==="
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
    EXPECTED=42
    if [ "$ROW_COUNT" -ge "$EXPECTED" ]; then
        echo "Qwen3 G goals 4-10 complete ($ROW_COUNT/$EXPECTED rows)."
    else
        echo "WARNING: only $ROW_COUNT rows."
    fi
fi
