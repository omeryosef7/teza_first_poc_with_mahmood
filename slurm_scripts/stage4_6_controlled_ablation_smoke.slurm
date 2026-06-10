#!/bin/bash

#SBATCH --job-name=stage4_6_ablation_smoke
#SBATCH --output=logs/stage4_6_ablation_smoke_%j.out
#SBATCH --error=logs/stage4_6_ablation_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4.6 smoke test: first goal (goal_index=0), conditions A and D only.
# Verifies generation pipeline end-to-end before full run.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4_6/runs_output_smoke_$(date +%Y%m%d_%H%M%S)}"
ABLATION_PROMPTS="${ABLATION_PROMPTS:-$PROJECT_DIR/outputs/stage4_6/ablation_prompts.jsonl}"
export OUTPUT_DIR
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

echo "=== Stage 4.6 Controlled Ablation SMOKE started ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
pwd
python -V
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

echo ""
echo "OUTPUT_DIR=$OUTPUT_DIR"
echo "ABLATION_PROMPTS=$ABLATION_PROMPTS"

if [ ! -f "$ABLATION_PROMPTS" ]; then
    echo "=== Building ablation prompts ==="
    python -m poc_stage4_6.build_controlled_ablation_prompts
    echo "=== Auditing ablation prompts ==="
    python -m poc_stage4_6.audit_controlled_ablation_prompts
fi

echo ""
echo "=== Running smoke ablation (goal=0, conditions A+D) ==="

SCRIPT_ARGS=(
    --ablation-prompts "$ABLATION_PROMPTS"
    --output-dir "$OUTPUT_DIR"
    --conditions "A,D"
    --goals "0"
)

if [ "${SKIP_JUDGE:-false}" = "true" ]; then
    SCRIPT_ARGS+=(--skip-judge)
fi
if [ "${SKIP_STRONGREJECT:-false}" = "true" ]; then
    SCRIPT_ARGS+=(--skip-strongreject)
fi

python -m poc_stage4_6.run_controlled_ablation "${SCRIPT_ARGS[@]}"

echo ""
echo "=== Checking smoke outputs ==="
python - <<'PY'
import json, sys
from pathlib import Path
import os
output_dir = Path(os.environ.get("OUTPUT_DIR", "outputs/stage4_6/runs_output_smoke"))
summary = output_dir / "run_summary.jsonl"
if not summary.exists():
    print("ERROR: run_summary.jsonl not found")
    sys.exit(1)
rows = [json.loads(l) for l in summary.read_text().splitlines() if l.strip()]
print(f"run_summary.jsonl: {len(rows)} rows")
for r in rows:
    print(f"  {r['run_id']}: is_success={r.get('is_success')} sr={r.get('strongreject_score')} think_tokens={r.get('think_token_count')}")
if len(rows) < 1:
    print("ERROR: expected at least 1 row in summary")
    sys.exit(1)
print("Smoke check OK")
PY

echo ""
echo "=== Stage 4.6 smoke finished ==="
date
