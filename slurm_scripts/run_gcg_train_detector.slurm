#!/bin/bash

#SBATCH --job-name=gcg_detector
#SBATCH --output=logs/gcg_detector_%j.out
#SBATCH --error=logs/gcg_detector_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Ablation 4D — Real-time adversarial detector training.
#
# Trains a logistic regression classifier on position-0 layer-averaged hidden
# states from hidden_states/*.pt files. CPU-only (GPU not used, but 1 GPU
# requested to satisfy killable/gpu-research account requirements).
#
# Prerequisites: run_gcg_replay.slurm must complete for the source run.
# Source: gcg_full_qwen3_weighted/hidden_states/ (300 .pt files)
#
# Usage:
#   sbatch slurm_scripts/run_gcg_train_detector.slurm
#
# Optional: set RUN_DIR and OUTPUT_DIR env vars to change source/destination.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_qwen3_weighted}"
OUTPUT_DIR="${OUTPUT_DIR:-${PROJECT_DIR}/outputs/stage_gcg_ablation/detector}"
POS="${POS:-0}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs "$OUTPUT_DIR"

echo "========================================================"
echo "  Ablation 4D — Real-Time Adversarial Detector Training"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "OUTPUT_DIR:      ${OUTPUT_DIR}"
echo "POS:             ${POS}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"

if [ ! -d "${RUN_DIR}/hidden_states" ]; then
    echo "ERROR: hidden_states/ not found at ${RUN_DIR}/hidden_states"
    echo "Run run_gcg_replay.slurm first."
    exit 1
fi

echo "Hidden state files: $(ls "${RUN_DIR}/hidden_states/"*.pt 2>/dev/null | wc -l)"

echo ""
echo "--- Training detector ---"
python -m poc_stage_gcg_early.train_realtime_detector \
    --run-dir "${RUN_DIR}" \
    --output-dir "${OUTPUT_DIR}" \
    --pos "${POS}" \
    --n-splits 5

echo ""
echo "--- Results ---"
if [ -f "${OUTPUT_DIR}/DETECTOR_REPORT.md" ]; then
    grep -A 6 "## Summary" "${OUTPUT_DIR}/DETECTOR_REPORT.md" || true
fi

echo ""
echo "========================================================"
echo "  Detector Training COMPLETE"
echo "  Report: ${OUTPUT_DIR}/DETECTOR_REPORT.md"
echo "  Model:  ${OUTPUT_DIR}/detector_model.pkl"
echo "  $(date -u)"
echo "========================================================"
