#!/bin/bash

#SBATCH --job-name=stage4_8_repr
#SBATCH --output=logs/stage4_8_repr_%j.out
#SBATCH --error=logs/stage4_8_repr_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4.8 — compute layer projections on repeated-generation outputs.
# Must run AFTER stage4_8_repeated_generations_array completes and
# audit_repeated_generations passes.
#
# Usage:
#   RUN_DIR=outputs/stage4_8/runs/run_array_<jobid> sbatch slurm_scripts/stage4_8_compute_representations.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

if [ -z "${RUN_DIR:-}" ]; then
    echo "ERROR: RUN_DIR must be set. Usage: RUN_DIR=outputs/stage4_8/runs/... sbatch ..."
    exit 1
fi

RUN_DIR="$PROJECT_DIR/$RUN_DIR"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$RUN_DIR/representations" \
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

echo "=== Stage 4.8 Representations ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
echo "RUN_DIR=$RUN_DIR"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

# Verify run_summary.jsonl exists and has ≥58 rows
ROW_COUNT=$(python3 -c "
from pathlib import Path
p = Path('${RUN_DIR}/run_summary.jsonl')
if not p.exists(): print(0); exit()
rows = [l for l in p.read_text().splitlines() if l.strip()]
print(len(rows))
")
echo "run_summary.jsonl rows: $ROW_COUNT"
if [ "$ROW_COUNT" -lt 58 ]; then
    echo "ERROR: fewer than 58 rows in run_summary.jsonl — array may not have finished"
    exit 1
fi

echo ""
echo "=== Running compute_repeated_generation_representations ==="
python -m poc_stage4_8.compute_repeated_generation_representations \
    --run-dir "$RUN_DIR"

echo ""
echo "=== Verifying projection output ==="
export RUN_DIR
python - <<'PY'
import json, os
from pathlib import Path
from collections import Counter
run_dir = Path(os.environ["RUN_DIR"])
summary = run_dir / "representations" / "projection_summary.jsonl"
if not summary.exists():
    print("ERROR: projection_summary.jsonl not found")
    exit(1)
rows = [json.loads(l) for l in summary.read_text().splitlines() if l.strip()]
print(f"Projection rows: {len(rows)}")
by_cond = Counter(r.get("condition") for r in rows)
print(f"By condition: {dict(by_cond)}")
l22_rows = [r for r in rows if r.get("layer22_first_500_mean_projection") is not None]
print(f"Rows with L22 first_500: {len(l22_rows)}")
for cond in ("A", "D", "F"):
    cond_rows = [r for r in l22_rows if r.get("condition") == cond]
    if cond_rows:
        mean_proj = sum(r["layer22_first_500_mean_projection"] for r in cond_rows) / len(cond_rows)
        print(f"  {cond}: mean_L22={mean_proj:.4f} n={len(cond_rows)}")
PY

echo ""
echo "=== Running behavioral analysis (CPU) ==="
python -m poc_stage4_8.analyze_repeated_generations \
    --run-dir "$RUN_DIR"

echo ""
echo "=== Checking matched outcome cells ==="
MATCHED=$(python3 -c "
import csv
from pathlib import Path
p = Path('${RUN_DIR}/analysis/matched_outcome_cells.csv')
if not p.exists(): print(0); exit()
rows = list(csv.DictReader(open(p)))
print(len(rows))
")
echo "Matched outcome cells: $MATCHED"

if [ "$MATCHED" -ge 4 ]; then
    echo ""
    echo "=== Sufficient matched cells — running direction extraction ==="
    python -m poc_stage4_8.extract_behavior_conditioned_direction \
        --run-dir "$RUN_DIR"
    echo "Direction extraction complete."
else
    echo "WARNING: fewer than 4 matched cells ($MATCHED). Skipping direction extraction."
    echo "See docs/STAGE4_8_REPEATED_GENERATIONS_RESULTS.md for decision gate."
fi

echo ""
echo "=== Running Stage 4.8 plots ==="
python -m poc_stage4_8.plot_repeated_generations \
    --run-dir "$RUN_DIR"

echo ""
echo "=== Stage 4.8 Representations + Plots COMPLETE ==="
echo "Figures at: $RUN_DIR/plots/"
echo "Direction results at: $RUN_DIR/direction_analysis/direction_results.json"
date
