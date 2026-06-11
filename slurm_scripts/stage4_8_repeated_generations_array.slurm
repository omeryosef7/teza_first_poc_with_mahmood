#!/bin/bash

#SBATCH --job-name=stage4_8_array
#SBATCH --output=logs/stage4_8_array_%A_%a.out
#SBATCH --error=logs/stage4_8_array_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805
#SBATCH --array=0-3

# Stage 4.8 full run — 60 stochastic generations.
# Array: 1 task per source goal (4 tasks total).
# Each task runs 1 source prompt × 3 conditions × 5 seeds = 15 generations.
#
# All tasks write to the SAME output dir (set by RUN_DIR env var or auto-stamped).
# Resume-safe: individual run_ids are skipped if already present in run_summary.jsonl.
#
# Submit ONLY after stage4_8_smoke passes audit with generation_hash diversity confirmed.
# Usage:
#   RUN_DIR=outputs/stage4_8/runs/run_<ts> sbatch slurm_scripts/stage4_8_repeated_generations_array.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MANIFEST="$PROJECT_DIR/outputs/stage4_8/repeated_generation_manifest.jsonl"

# All array tasks share one run dir. If RUN_DIR not set externally, create a shared
# timestamp dir before submitting (set via sbatch --export=RUN_DIR=...).
# Fallback: each task creates/uses the same timestamped dir — safe because SLURM starts
# all array tasks within seconds and the runner is resume-safe.
ARRAY_RUN_DIR="${RUN_DIR:-$PROJECT_DIR/outputs/stage4_8/runs/run_array_${SLURM_JOB_ID}}"

# Map array task index to goal index
GOAL_INDEX=$SLURM_ARRAY_TASK_ID   # 0,1,2,3

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

echo "=== Stage 4.8 Array Task ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID  SLURM_ARRAY_TASK_ID=$SLURM_ARRAY_TASK_ID"
echo "GOAL_INDEX=$GOAL_INDEX"
echo "ARRAY_RUN_DIR=$ARRAY_RUN_DIR"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

python -m poc_stage4_8.run_repeated_generations \
    --manifest "$MANIFEST" \
    --output-dir "$ARRAY_RUN_DIR" \
    --goals "$GOAL_INDEX" \
    --skip-judge

echo ""
echo "=== Task $SLURM_ARRAY_TASK_ID (goal=$GOAL_INDEX) complete ==="
date

# Final task (goal 3) runs audit and analysis after all tasks finish.
# Note: this fires when goal=3 finishes; the other tasks are usually done by then.
# If they are not, re-run audit manually after all tasks complete.
if [ "$GOAL_INDEX" -eq 3 ]; then
    echo ""
    echo "=== Final task: waiting briefly for sibling tasks, then running audit ==="
    sleep 30

    export ARRAY_RUN_DIR
    python -m poc_stage4_8.audit_repeated_generations \
        --run-dir "$ARRAY_RUN_DIR"

    ROW_COUNT=$(python - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ["ARRAY_RUN_DIR"]) / "run_summary.jsonl"
if not p.exists():
    print(0)
    exit()
rows = [l for l in p.read_text().splitlines() if l.strip()]
print(len(rows))
PY
)
    echo "Total rows in run_summary.jsonl: $ROW_COUNT"

    if [ "$ROW_COUNT" -ge 58 ]; then
        echo "Sufficient rows. Running behavioral analysis..."
        python -m poc_stage4_8.analyze_repeated_generations \
            --run-dir "$ARRAY_RUN_DIR"

        echo ""
        echo "=== matched_outcome_cells.csv ==="
        cat "$ARRAY_RUN_DIR/analysis/matched_outcome_cells.csv" 2>/dev/null || echo "(not generated)"

        # Auto-submit representations job if >=4 matched cells
        MATCHED=$(python3 -c "
import csv
from pathlib import Path
import os
p = Path(os.environ['ARRAY_RUN_DIR']) / 'analysis' / 'matched_outcome_cells.csv'
if not p.exists(): print(0)
else: print(len(list(csv.DictReader(open(p)))))
")
        echo "Matched outcome cells: $MATCHED"

        if [ "$MATCHED" -ge 4 ]; then
            echo ""
            echo "=== Auto-submitting representations job ==="
            # Make run dir relative to project dir for the SLURM script
            REL_RUN_DIR="${ARRAY_RUN_DIR#$PROJECT_DIR/}"
            sbatch --export=ALL,RUN_DIR="$REL_RUN_DIR" \
                slurm_scripts/stage4_8_compute_representations.slurm
            echo "Representations job submitted. Check logs/stage4_8_repr_*.out when done."
        else
            echo "WARNING: only $MATCHED matched cells (need >=4 for direction extraction)."
            echo "See decision gate in docs/STAGE4_8_REPEATED_GENERATIONS_RESULTS.md"
        fi
    else
        echo "WARNING: Only $ROW_COUNT rows — some tasks may not have completed."
        echo "Re-run audit manually when all tasks finish:"
        echo "  python -m poc_stage4_8.audit_repeated_generations --run-dir $ARRAY_RUN_DIR"
    fi
fi
