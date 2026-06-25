#!/bin/bash

#SBATCH --job-name=stage4_8_gemma_smoke
#SBATCH --output=logs/stage4_8_gemma_smoke_%j.out
#SBATCH --error=logs/stage4_8_gemma_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:30:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805

# Stage 4.8 Gemma4 smoke test — 6 generations (goal 0, conds A+D, seeds 101+102).
# Verifies Gemma4 model loading, EOS handling, and thinking segmentation.
#
# Run AFTER stage4_8_cond_e_array (job 611041) has started to keep under 6-job limit.
# Verify smoke passes before submitting the full array.
#
# Submit:
#   sbatch slurm_scripts/stage4_8_gemma_smoke.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MANIFEST="$PROJECT_DIR/outputs/stage4_8_gemma/repeated_generation_manifest.jsonl"
SMOKE_RUN_DIR="$PROJECT_DIR/outputs/stage4_8_gemma/runs/smoke_${SLURM_JOB_ID}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$SMOKE_RUN_DIR" \
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

echo "=== Stage 4.8 Gemma4 Smoke Test ==="
date
hostname
echo "SMOKE_RUN_DIR=$SMOKE_RUN_DIR"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

python -m poc_stage4_8.run_repeated_generations \
    --manifest "$MANIFEST" \
    --output-dir "$SMOKE_RUN_DIR" \
    --model-family gemma4 \
    --goals 0 \
    --conditions A,D \
    --seeds 101,102 \
    --skip-judge

echo ""
echo "=== Smoke complete ==="
date

ROW_COUNT=$(python3 - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ.get("SMOKE_RUN_DIR", "")) / "run_summary.jsonl"
if not p.exists():
    print(0)
else:
    rows = [l for l in p.read_text().splitlines() if l.strip()]
    print(len(rows))
PY
)
echo "Rows written: $ROW_COUNT"

if [ "$ROW_COUNT" -ge 4 ]; then
    echo "SMOKE PASSED: $ROW_COUNT rows. Ready to submit full array."
    echo "  RUN_DIR=outputs/stage4_8_gemma/runs/run_<ts> sbatch slurm_scripts/stage4_8_gemma_array.slurm"
else
    echo "SMOKE FAILED: only $ROW_COUNT rows. Check logs."
    exit 1
fi
