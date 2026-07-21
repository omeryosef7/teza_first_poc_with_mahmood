#!/bin/bash
#SBATCH --job-name=phase3_tropt
#SBATCH --output=logs/phase3_tropt_%j.out
#SBATCH --error=logs/phase3_tropt_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301

# Phase 3 (RESEARCH_PLAN_DISTILLING_JAILBREAKS.md sec 7): TROPT discrete-trigger
# optimization on Qwen3-14B (white-box, l40s). Runs under the TROPT venv, NOT conda.
# Reuses scripts/phase3_tropt_optimize.py (which reuses TROPT recipes).
#
# Env overrides: OPTIMIZER(gcg|mac|gcg_hij) TARGET_STYLE MODEL_NAME MANIFEST OUT_DIR LIMIT NUM_STEPS
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs

# Reuse the existing HF cache (Qwen3-14B already downloaded by prior GCG work).
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"

TROPT_PY="$PROJECT_DIR/TROPT/.venv/bin/python"
OPTIMIZER="${OPTIMIZER:-gcg}"
TARGET_STYLE="${TARGET_STYLE:-empty_think}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
MANIFEST="${MANIFEST:-data/manifests/dev_train_20.csv}"
OUT_DIR="${OUT_DIR:-outputs/phase3_tropt/${OPTIMIZER}_qwen3_${TARGET_STYLE}}"
LIMIT="${LIMIT:-0}"
NUM_STEPS="${NUM_STEPS:-0}"

echo "[phase3] opt=$OPTIMIZER style=$TARGET_STYLE model=$MODEL_NAME manifest=$MANIFEST out=$OUT_DIR"
"$TROPT_PY" -u scripts/phase3_tropt_optimize.py \
    --optimizer "$OPTIMIZER" \
    --target-style "$TARGET_STYLE" \
    --model-name "$MODEL_NAME" \
    --manifest "$MANIFEST" \
    --out-dir "$OUT_DIR" \
    --limit "$LIMIT" \
    --num-steps "$NUM_STEPS"
echo "[phase3] done"
