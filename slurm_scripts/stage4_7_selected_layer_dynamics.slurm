#!/bin/bash

#SBATCH --job-name=stage4_7_proj
#SBATCH --output=logs/stage4_7_proj_%j.out
#SBATCH --error=logs/stage4_7_proj_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4.7 — Selected-layer projection analysis on 48 replication outputs.
#
# Runs compute_selected_layer_dynamics.py on the canonical run directory.
# Projects residual stream activations (layers 13, 16, 22, 38, 39) onto the
# provisional Stage 4 direction.  Layer 22 is pre-specified; others are
# exploratory.  Direction is diagnostic only — no causal claims.
#
# After completion, re-runs analyze_replication.py and plot_replication.py
# to populate mechanistic figures (5, 6, 8, 11).
#
# Output: outputs/stage4_7/runs/run_array_20260610_1442/projection_analysis/
#
# Resume-safe: already-processed run_ids get overwritten in place (idempotent).

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

RUN_DIR="${RUN_DIR:-$PROJECT_DIR/outputs/stage4_7/runs/run_array_20260610_1442}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs \
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

echo "=== Stage 4.7 Selected-Layer Projection Analysis ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
echo "RUN_DIR=$RUN_DIR"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

# Run projection analysis on all 48 rows (all conditions)
python -m poc_stage4_7.compute_selected_layer_dynamics \
    --run-dir "$RUN_DIR"

echo ""
echo "=== Projection complete — running analysis + plots ==="

# Re-run behavioral + mechanistic analysis (picks up new projection_summary.jsonl)
python -m poc_stage4_7.analyze_replication \
    --run-dir "$RUN_DIR"

# Re-run plots (now generates figs 5, 6, 8, 11 from projection data)
python -m poc_stage4_7.plot_replication \
    --run-dir "$RUN_DIR"

echo ""
echo "=== Verify projection output ==="
python - <<'PY'
import json, sys
from pathlib import Path
import os
run_dir = Path(os.environ.get("RUN_DIR", "outputs/stage4_7/runs/run_array_20260610_1442"))
proj_path = run_dir / "projection_analysis" / "projection_summary.jsonl"
if not proj_path.exists():
    print(f"ERROR: {proj_path} not found")
    sys.exit(1)
rows = [json.loads(l) for l in proj_path.read_text().splitlines() if l.strip()]
print(f"Projection rows: {len(rows)} (expected 48)")
from collections import Counter
print("By condition:", Counter(r.get("condition") for r in rows))
# Check primary feature present
l22_key = "layer22_first_500_mean_projection"
n_with_proj = sum(1 for r in rows if r.get(l22_key) is not None)
print(f"Rows with {l22_key}: {n_with_proj}")
# Show mean by condition (A, D, F only — E has no think phase)
for cond in ["A", "D", "F"]:
    vals = [r[l22_key] for r in rows if r.get("condition") == cond and r.get(l22_key) is not None]
    if vals:
        print(f"  {cond}: mean={sum(vals)/len(vals):.4f} n={len(vals)}")
print("Manifest direction_status:", json.loads((run_dir / "projection_analysis" / "projection_manifest.json").read_text()).get("direction_status", "?"))
PY

echo ""
echo "=== Stage 4.7 Projection Job COMPLETE ==="
date
