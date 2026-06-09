#!/bin/bash

#SBATCH --job-name=stage4_6_ablation_full
#SBATCH --output=logs/stage4_6_ablation_full_%j.out
#SBATCH --error=logs/stage4_6_ablation_full_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4.6 full ablation: all 20 conditions (4 goals × 5 conditions).
# do_sample=False → deterministic; run once per condition.
# Max 20 generations. Submit only after smoke test passes.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

RUN_NAME="${RUN_NAME:-full_$(date +%Y%m%d_%H%M%S)}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4_6/runs_output_$RUN_NAME}"
ABLATION_PROMPTS="${ABLATION_PROMPTS:-$PROJECT_DIR/outputs/stage4_6/ablation_prompts.jsonl}"
SKIP_JUDGE="${SKIP_JUDGE:-false}"
SKIP_STRONGREJECT="${SKIP_STRONGREJECT:-false}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUTPUT_DIR" \
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

echo "=== Stage 4.6 Controlled Ablation FULL started ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
pwd
python -V
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

echo ""
echo "OUTPUT_DIR=$OUTPUT_DIR"
echo "RUN_NAME=$RUN_NAME"
echo "ABLATION_PROMPTS=$ABLATION_PROMPTS"

if [ ! -f "$ABLATION_PROMPTS" ]; then
    echo "=== Building ablation prompts ==="
    python -m poc_stage4_6.build_controlled_ablation_prompts
    echo "=== Auditing ablation prompts ==="
    python -m poc_stage4_6.audit_controlled_ablation_prompts
    if [ $? -ne 0 ]; then
        echo "ERROR: ablation prompt audit failed — aborting full run"
        exit 1
    fi
fi

echo ""
echo "=== Running full ablation (4 goals × 5 conditions = 20 generations) ==="

SCRIPT_ARGS=(
    --ablation-prompts "$ABLATION_PROMPTS"
    --output-dir "$OUTPUT_DIR"
)

if [ "${SKIP_JUDGE:-false}" = "true" ]; then
    SCRIPT_ARGS+=(--skip-judge)
fi
if [ "${SKIP_STRONGREJECT:-false}" = "true" ]; then
    SCRIPT_ARGS+=(--skip-strongreject)
fi

python -m poc_stage4_6.run_controlled_ablation "${SCRIPT_ARGS[@]}"

echo ""
echo "=== Running analysis ==="
python -m poc_stage4_6.analyze_controlled_ablation \
    --run-dir "$OUTPUT_DIR" \
    --output-dir "$OUTPUT_DIR/analysis"

echo ""
echo "=== Running plots ==="
python -m poc_stage4_6.plot_controlled_ablation \
    --run-dir "$OUTPUT_DIR" \
    --output-dir "$OUTPUT_DIR/plots"

echo ""
echo "=== Checking full outputs ==="
python - <<'PY'
import json, sys
from pathlib import Path
import os
output_dir = Path(os.environ["OUTPUT_DIR"])
summary = output_dir / "run_summary.jsonl"
if not summary.exists():
    print("ERROR: run_summary.jsonl not found")
    sys.exit(1)
rows = [json.loads(l) for l in summary.read_text().splitlines() if l.strip()]
print(f"run_summary.jsonl: {len(rows)} rows")
n_success = sum(1 for r in rows if r.get("is_success") is True)
print(f"is_success=True: {n_success}/{len(rows)}")
if len(rows) < 20:
    print(f"WARNING: expected 20 rows, got {len(rows)} (may have failures)")
per_run_csv = output_dir / "analysis" / "per_run_results.csv"
if per_run_csv.exists():
    print(f"per_run_results.csv: exists")
condition_csv = output_dir / "analysis" / "condition_summary.csv"
if condition_csv.exists():
    print(f"condition_summary.csv: exists")
plots_dir = output_dir / "plots"
if plots_dir.exists():
    plots = list(plots_dir.glob("*.png"))
    print(f"plots/: {len(plots)} PNG files")
print("Output check OK")
PY

echo ""
echo "=== Stage 4.6 full ablation finished ==="
date
