#!/bin/bash
#SBATCH --job-name=phase3_eval
#SBATCH --output=logs/phase3_eval_%j.out
#SBATCH --error=logs/phase3_eval_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301

# Phase-3 free-generation eval of TROPT triggers (plan §7.5) via the reused Stage-9 harness.
# Runs scripts/phase3_eval_triggers.py: Qwen3-14B greedy free-gen + inline StrongREJECT for
# each trigger + task_only/random_spaces controls. Resume-safe (row_key skip).
#
# Env: TRIGGERS="a.jsonl b.jsonl" (required, space-separated) OUT_DIR (required)
#      SEEDS="0" LIMIT=0 MAX_NEW_TOKENS=2048 DECODING=greedy|sampled
set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
TRIGGERS="${TRIGGERS:?set TRIGGERS to one or more triggers.jsonl paths (space-separated)}"
OUT_DIR="${OUT_DIR:?set OUT_DIR}"
SEEDS="${SEEDS:-0}"
LIMIT="${LIMIT:-0}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-2048}"
DECODING="${DECODING:-greedy}"

echo "[phase3-eval] START job=${SLURM_JOB_ID:-?} node=$(hostname) date=$(date -u) — activating env…"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
echo "[phase3-eval] env active ($CONDA_ENV); loading model next…"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$OUT_DIR"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "[phase3-eval] job=${SLURM_JOB_ID} node=${SLURM_NODELIST} decoding=${DECODING}"
echo "[phase3-eval] triggers=${TRIGGERS} out=${OUT_DIR} seeds=${SEEDS} limit=${LIMIT}"
echo "[phase3-eval] git=$(git rev-parse HEAD 2>/dev/null || echo unknown) date=$(date -u)"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then echo "ERROR: expected L40S, got $GPU_NAME"; exit 1; fi
echo "[phase3-eval] GPU ok: $GPU_NAME"

DECODE_FLAG=""
if [ "$DECODING" = "sampled" ]; then DECODE_FLAG="--sampled"; fi
SEEDS_ARGS="${SEEDS//,/ }"

python -u scripts/phase3_eval_triggers.py \
    --triggers $TRIGGERS \
    --out-dir "$OUT_DIR" \
    --seeds $SEEDS_ARGS \
    --limit "$LIMIT" \
    --max-new-tokens "$MAX_NEW_TOKENS" \
    $DECODE_FLAG

echo "[phase3-eval] COMPLETE → ${OUT_DIR}/FREE_GENERATION_RESULTS.jsonl date=$(date -u)"
