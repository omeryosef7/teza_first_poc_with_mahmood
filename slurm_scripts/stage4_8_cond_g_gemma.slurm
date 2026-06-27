#!/bin/bash

#SBATCH --job-name=stage4_8_cond_g_gemma
#SBATCH --output=logs/stage4_8_cond_g_gemma_%A_%a.out
#SBATCH --error=logs/stage4_8_cond_g_gemma_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-501,n-601,n-801,n-802,n-803,n-805
#SBATCH --array=0-3

# Stage 4.8 condition-G: Gemma4-E4B-IT, bare harmful + thinking DISABLED.
# 12 generations total (4 goals × 3 seeds per goal).
# Each array task handles one goal index (0–3).
#
# Condition G = same user_message as condition D (bare harmful goal),
# but enable_thinking=False. Required to complete the full Puzzle×Thinking
# factorial interaction: (p_A - p_E) - (p_D - p_G).
#
# G condition is a plain generation run — NO intervention hooks.
# validate_intervention_hooks.py does NOT need to pass before submitting this job.
#
# Manifests built by: python -m poc_stage4_8.build_manifest_condition_g
# (requires outputs/stage4/factorial_balanced/g_condition_job_targets.jsonl)
#
# Smoke run (goal 0, seeds 101+102 only):
#   RUN_DIR=outputs/stage4_8_gemma/runs/run_cond_g_gemma_smoke sbatch --array=0 slurm_scripts/stage4_8_cond_g_gemma.slurm
#
# Full run (all goals):
#   RUN_DIR=outputs/stage4_8_gemma/runs/run_cond_g_gemma_$(date +%Y%m%d_%H%M%S) sbatch slurm_scripts/stage4_8_cond_g_gemma.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MANIFEST="$PROJECT_DIR/outputs/stage4_8_gemma/repeated_generation_manifest_cond_g_gemma.jsonl"
ARRAY_RUN_DIR="${RUN_DIR:-$PROJECT_DIR/outputs/stage4_8_gemma/runs/run_cond_g_gemma_${SLURM_JOB_ID}}"

GOAL_INDEX=$SLURM_ARRAY_TASK_ID   # 0, 1, 2, 3

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
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

echo "=== Stage 4.8 Condition-G (Gemma4) Array Task ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID  SLURM_ARRAY_TASK_ID=$SLURM_ARRAY_TASK_ID"
echo "GOAL_INDEX=$GOAL_INDEX"
echo "ARRAY_RUN_DIR=$ARRAY_RUN_DIR"
echo "MANIFEST=$MANIFEST"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

python -m poc_stage4_8.run_repeated_generations \
    --manifest "$MANIFEST" \
    --output-dir "$ARRAY_RUN_DIR" \
    --model-family gemma4 \
    --goals "$GOAL_INDEX" \
    --conditions G \
    --skip-judge

echo ""
echo "=== Task $SLURM_ARRAY_TASK_ID (goal=$GOAL_INDEX) complete ==="
date

# Final task: quick audit after all tasks finish
if [ "$GOAL_INDEX" -eq 3 ]; then
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
    EXPECTED=12
    if [ "$ROW_COUNT" -ge "$((EXPECTED - 1))" ]; then
        echo "Condition-G Gemma4 run looks complete ($ROW_COUNT/$EXPECTED rows)."
        echo "Next: add to factorial dataset with --cond-g-run-dir $ARRAY_RUN_DIR"
    else
        echo "WARNING: Only $ROW_COUNT rows — check for failures before proceeding."
    fi
fi
