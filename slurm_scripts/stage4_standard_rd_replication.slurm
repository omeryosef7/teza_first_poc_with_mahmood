#!/bin/bash

#SBATCH --job-name=stage4_rd_replication
#SBATCH --output=logs/stage4_rd_replication_%j.out
#SBATCH --error=logs/stage4_rd_replication_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-501,n-601,n-801,n-802,n-803,n-805

# Phase 1: Standard Arditi refusal direction replication on Qwen3-14B.
# Diagnoses why Stage 4A2 yielded 0/160 causal candidates.
#
# Runs two configurations:
#   (a) Reuse existing Stage 4A1 directions + re-evaluate with Arditi thresholds (KL<1.0)
#   (b) Fresh extraction with enable_thinking=True (matches actual inference condition)
#
# Submit after Gemma4 smoke clears (to stay under 6-job limit).
# Expected runtime: ~2-3 hours for 160 candidates with n_val=32.
#
# Usage:
#   sbatch slurm_scripts/stage4_standard_rd_replication.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
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

echo "=== Stage 4 Standard Refusal Direction Replication ==="
date
hostname
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

# ── Part A: Reuse Stage 4A1 directions, apply Arditi thresholds ──────────────
echo "=== Part A: Reuse Stage 4A1 dirs + Arditi thresholds (KL<1.0) ==="
OUTPUT_A="$PROJECT_DIR/outputs/stage4/standard_rd_replication/reuse_stage4a1"
mkdir -p "$OUTPUT_A"

python -m poc_stage4.replicate_standard_refusal_direction \
    --model-name "Qwen/Qwen3-14B" \
    --output-dir "$OUTPUT_A" \
    --reuse-stage4a1 \
    --n-harmful 64 \
    --n-harmless 64 \
    --n-harmful-val 32 \
    --n-harmless-val 32 \
    --steer-alpha 20.0

echo ""
echo "=== Part A complete ==="
date
echo ""

# ── Part B: Fresh extraction with thinking=True ───────────────────────────────
echo "=== Part B: Fresh extraction with enable_thinking=True ==="
OUTPUT_B="$PROJECT_DIR/outputs/stage4/standard_rd_replication/thinking_enabled"
mkdir -p "$OUTPUT_B"

python -m poc_stage4.replicate_standard_refusal_direction \
    --model-name "Qwen/Qwen3-14B" \
    --output-dir "$OUTPUT_B" \
    --enable-thinking \
    --n-harmful 64 \
    --n-harmless 64 \
    --n-harmful-val 32 \
    --n-harmless-val 32 \
    --steer-alpha 20.0

echo ""
echo "=== Part B complete ==="
date
echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
echo "=== Replication summary ==="
python3 - <<'PY'
import json
from pathlib import Path

proj = Path("/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood")
for name, subdir in [("Part A (reuse)", "reuse_stage4a1"), ("Part B (thinking)", "thinking_enabled")]:
    p = proj / "outputs" / "stage4" / "standard_rd_replication" / subdir / "replication_summary.json"
    if not p.exists():
        print(f"{name}: not found")
        continue
    d = json.loads(p.read_text())
    print(f"{name}: decision={d.get('decision_gate')}, "
          f"survivors_arditi={d.get('n_survivors_arditi')}, "
          f"max_steer_delta={d.get('max_steering_delta'):.4f if d.get('max_steering_delta') else 'None'}")
PY

echo ""
echo "=== Job complete ==="
date
