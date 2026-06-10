#!/bin/bash

#SBATCH --job-name=stage4_7_rep
#SBATCH --output=logs/stage4_7_array_%A_%a.out
#SBATCH --error=logs/stage4_7_array_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805
#SBATCH --array=0-3

# Stage 4.7 full replication — 4-task array, one goal per task.
# Each task: up to 3 prompts × 4 conditions = up to 12 generations.
# Total across all tasks: up to 48 generations (within 60-generation limit).
#
# Submit ONLY after smoke test passes.
# Array task 0 → goal 0, task 1 → goal 1, etc.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

GOAL_INDEX="${SLURM_ARRAY_TASK_ID}"
export GOAL_INDEX
RUN_NAME="${RUN_NAME:-full_$(date +%Y%m%d_%H%M%S)_goal${GOAL_INDEX}}"
# All tasks write to the same run directory for easy merging
SHARED_RUN_DIR="${SHARED_RUN_DIR:-$PROJECT_DIR/outputs/stage4_7/runs/run_array_$(date +%Y%m%d_%H%M%S | cut -c1-13)}"
OUTPUT_DIR="${OUTPUT_DIR:-$SHARED_RUN_DIR}"
REPLICATION_PROMPTS="${REPLICATION_PROMPTS:-$PROJECT_DIR/outputs/stage4_7/replication_prompts.jsonl}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUTPUT_DIR/runs" "$OUTPUT_DIR/logs" \
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
export OUTPUT_DIR

echo "=== Stage 4.7 Replication Array Task ${SLURM_ARRAY_TASK_ID} ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID}  SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"
echo "GOAL_INDEX=$GOAL_INDEX"
echo "OUTPUT_DIR=$OUTPUT_DIR"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true

echo ""
echo "=== Running goal=$GOAL_INDEX (all conditions A,D,F,E) ==="
python -m poc_stage4_7.run_replication \
    --replication-prompts "$REPLICATION_PROMPTS" \
    --output-dir "$OUTPUT_DIR" \
    --goals "$GOAL_INDEX" \
    --skip-judge \
    --max-new-tokens 32768

echo ""
echo "=== Checking task outputs ==="
python - <<PY
import json, sys
from pathlib import Path
import os
output_dir = Path(os.environ["OUTPUT_DIR"])
goal_idx = int(os.environ["GOAL_INDEX"])
summary = output_dir / "run_summary.jsonl"
if not summary.exists():
    print(f"ERROR: run_summary.jsonl not found in {output_dir}")
    sys.exit(1)
rows = [json.loads(l) for l in summary.read_text().splitlines() if l.strip()]
goal_rows = [r for r in rows if int(r.get("goal_index", -1)) == goal_idx]
print(f"Goal {goal_idx}: {len(goal_rows)} rows in summary (expected up to 12)")
conditions_seen = {r.get("condition") for r in goal_rows}
print(f"Conditions present: {sorted(conditions_seen)}")
truncated = [r for r in goal_rows if r.get("finish_reason") == "max_new_tokens"]
if truncated:
    print(f"WARNING: {len(truncated)} rows hit max_new_tokens")
for r in goal_rows:
    print(f"  {r.get('source_example_id')} cond={r.get('condition')} "
          f"sr={r.get('sr_success')} score={r.get('strongreject_score')} "
          f"think={r.get('think_token_count')} finish={r.get('finish_reason')}")
PY

echo ""
echo "=== Stage 4.7 Array Task $SLURM_ARRAY_TASK_ID COMPLETE ==="
date

echo ""
echo "After all 4 tasks complete, merge and verify with:"
echo "  python -c \""
echo "import json; from pathlib import Path"
echo "rows=[json.loads(l) for l in open('outputs/stage4_7/runs/<rundir>/run_summary.jsonl').read().splitlines() if l.strip()]"
echo "print(f'Total rows: {len(rows)}')\""
