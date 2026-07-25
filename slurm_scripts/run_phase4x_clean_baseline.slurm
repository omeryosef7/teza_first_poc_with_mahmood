#!/bin/bash
#SBATCH --job-name=clean_base
#SBATCH --output=logs/clean_base_%j.out
#SBATCH --error=logs/clean_base_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301

# Phase-4X clean (no-attack) baseline (plan §31.5/§31.6). Bare dev-25 goals → open-source HF
# target, greedy, no attack/suffix. Reuses models.hf_local.HFLocalLLM (same as the attack).
# USER CONSTRAINT §31.3: weights → node-local $SLURM_TMPDIR, NEVER the project HF cache.
# Required env: HF_MODEL=<hf repo id>. Optional: LIMIT MAX_NEW_TOKENS OUT_JSONL
set -euo pipefail
echo "[clean-base] START job=${SLURM_JOB_ID:-?} node=$(hostname) date=$(date -u) — activating env…"
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-poc_stage2}"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs outputs/phase4x_clean_baseline

# Node-local ephemeral HF cache (do NOT write to project .cache/huggingface).
HF_LOCAL_CACHE="${SLURM_TMPDIR:-/tmp/${SLURM_JOB_ID:-hf_local}}/hf"
mkdir -p "$HF_LOCAL_CACHE"
export HF_HOME="$HF_LOCAL_CACHE"
export HF_HUB_CACHE="$HF_LOCAL_CACHE/hub"
export TRANSFORMERS_CACHE="$HF_LOCAL_CACHE"
export HF_HUB_ENABLE_HF_TRANSFER=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

HF_MODEL="${HF_MODEL:?set HF_MODEL=<hf repo id>}"
LIMIT="${LIMIT:-0}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-4096}"
SAFE="${HF_MODEL//\//_}"
OUT_JSONL="${OUT_JSONL:-outputs/phase4x_clean_baseline/clean_${SAFE}_dev25.jsonl}"

echo "[clean-base] target=hf:$HF_MODEL limit=$LIMIT out=$OUT_JSONL hf_cache=$HF_LOCAL_CACHE"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then echo "ERROR: expected L40S, got $GPU_NAME"; exit 1; fi

python -u scripts/phase4x_clean_baseline.py \
    --hf-id "$HF_MODEL" \
    --manifest data/manifests/dev_25.csv \
    --out-jsonl "$OUT_JSONL" \
    --limit "$LIMIT" \
    --max-new-tokens "$MAX_NEW_TOKENS"

echo "[clean-base] project HF cache (should be unchanged):"; du -sh "$PROJECT_DIR/.cache/huggingface" 2>/dev/null || true
echo "[clean-base] done → $OUT_JSONL date=$(date -u)"
