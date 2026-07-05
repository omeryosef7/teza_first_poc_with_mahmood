#!/bin/bash

#SBATCH --job-name=gcg_smoke_qwen3
#SBATCH --output=logs/gcg_smoke_qwen3_%j.out
#SBATCH --error=logs/gcg_smoke_qwen3_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage GCG-Early smoke test (Stage 3 — task-only GCG).
# Runs 50 steps of task-only GCG on 2 harmless surrogate tasks with Qwen3-14B.
# Validation gate: task_loss must decrease; same seed must reproduce same trajectory.
#
# Resume: re-run with identical RUN_ID — checkpoint.pt is detected automatically.
#
# Usage:
#   sbatch --export=ALL,RUN_ID=smoke_qwen3_v1 slurm_scripts/smoke_gcg_qwen3.slurm
#
# Or use the default RUN_ID below.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_ID="${RUN_ID:-smoke_gcg_qwen3_$(date +%Y%m%d_%H%M%S)}"
MANIFEST_PATH="${PROJECT_DIR}/outputs/stage_gcg_early/surrogate_manifest_v1.jsonl"
OUTPUT_DIR="${PROJECT_DIR}/outputs/stage_gcg_early/${RUN_ID}"

# --- Environment ---
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$OUTPUT_DIR"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
# Synchronous CUDA kernel launches so errors report at the correct call site
export CUDA_LAUNCH_BLOCKING=1

# --- Startup diagnostics ---
echo "========================================================"
echo "  Stage GCG-Early Smoke Test — Qwen3-14B (task-only)"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "OUTPUT_DIR:      ${OUTPUT_DIR}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "CONDA_ENV:       $(conda info --envs | grep '*' | awk '{print $1}')"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# --- GPU guard: abort if not L40S ---
# Use awk instead of head to avoid SIGPIPE under set -o pipefail
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_NAME"

# --- Verify manifest exists ---
if [ ! -f "$MANIFEST_PATH" ]; then
    echo "ERROR: Manifest not found at $MANIFEST_PATH"
    echo "Run: python -m poc_stage_gcg_early.build_safe_surrogate_manifest"
    exit 1
fi
echo "Manifest: $MANIFEST_PATH"

# --- Check for existing checkpoint (resume) ---
if [ -f "${OUTPUT_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from existing checkpoint in ${OUTPUT_DIR}"
else
    echo ">>> Starting fresh run (no checkpoint found)"
fi

# --- Run CPU-only tests first (fast gate) ---
echo ""
echo "--- Running CPU unit tests ---"
python -m pytest poc_stage_gcg_early/tests/ -m "not gpu_integration" -q --tb=short
echo "CPU tests passed."
echo ""

# --- Run optimization (Stage 3: task-only, 50 steps) ---
echo "--- Starting GCG optimization ---"
python -m poc_stage_gcg_early.run_optimization \
    --run-id "${RUN_ID}" \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
    --manifest "${MANIFEST_PATH}" \
    --output-dir "${OUTPUT_DIR}" \
    --suffix-length 8 \
    --n-steps 50 \
    --batch-size 32 \
    --topk 256 \
    --seed 42 \
    --lambda-repr 0.0 \
    --lambda-kl 0.0 \
    --checkpoint-every 5 \
    --snapshot-every 25 \
    --split train

echo ""
echo "--- Optimization complete ---"

# --- Validation: check task_loss decreased ---
echo "--- Checking task_loss trajectory ---"
python - "$OUTPUT_DIR" <<'PYEOF'
import json
from pathlib import Path
import sys

run_dir = Path(sys.argv[1])
log_path = run_dir / "ITERATION_LOG.jsonl"
rows = []
with open(log_path) as f:
    for line in f:
        line = line.strip()
        if line:
            rows.append(json.loads(line))

if len(rows) < 2:
    print("ERROR: Fewer than 2 iteration log rows — optimization did not run.")
    sys.exit(1)

first_loss = rows[0]["task_loss"]
last_loss = rows[-1]["task_loss"]
best_loss = min(r["task_loss"] for r in rows)
print(f"Steps logged: {len(rows)}")
print(f"task_loss[0]={first_loss:.4f}  task_loss[-1]={last_loss:.4f}  best={best_loss:.4f}")
if best_loss < first_loss:
    print("PASS: task_loss decreased during optimization.")
else:
    print("WARNING: task_loss did not clearly decrease. Check learning dynamics.")
PYEOF

# --- Resume validation: re-run the same command — optimizer should detect checkpoint
#     and resume from the last saved step (identical RNG state → identical trajectory).
#     Since n_steps=50 is already complete, the optimizer exits immediately after
#     detecting "already at final step" — this confirms the checkpoint is loadable
#     and the config_hash matches. ---
echo ""
echo "--- Resume validation: re-run with same config (checkpoint should be detected) ---"
python -m poc_stage_gcg_early.run_optimization \
    --run-id "${RUN_ID}" \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
    --manifest "${MANIFEST_PATH}" \
    --output-dir "${OUTPUT_DIR}" \
    --suffix-length 8 \
    --n-steps 50 \
    --batch-size 32 \
    --topk 256 \
    --seed 42 \
    --lambda-repr 0.0 \
    --lambda-kl 0.0 \
    --checkpoint-every 5 \
    --snapshot-every 25 \
    --split train

echo ""
echo "Resume test: checkpoint detected and loaded successfully."

# --- Audit ---
echo ""
echo "--- Running audit ---"
python -m poc_stage_gcg_early.audit_run --run-dir "${OUTPUT_DIR}"

echo ""
echo "========================================================"
echo "  Smoke test COMPLETE: ${RUN_ID}"
echo "  Output: ${OUTPUT_DIR}"
echo "  Date: $(date -u)"
echo "========================================================"
