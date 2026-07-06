#!/bin/bash

#SBATCH --job-name=gcg_advbench_manifest
#SBATCH --output=logs/gcg_advbench_manifest_%j.out
#SBATCH --error=logs/gcg_advbench_manifest_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1

# Stage GCG-Full — Build AdvBench behavior manifest (CPU only, ~2 min).
#
# Reads llm-attacks/data/advbench/harmful_behaviors.csv (520 behaviors),
# selects 25 evenly-spaced rows (20 train + 5 val), and writes
# outputs/stage_gcg_full/advbench_manifest_v1.jsonl + SHA256.
#
# Usage:
#   sbatch slurm_scripts/build_gcg_advbench_manifest.slurm
#
# Optional overrides:
#   sbatch --export=ALL,N_TRAIN=20,N_VAL=5 slurm_scripts/build_gcg_advbench_manifest.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
N_TRAIN="${N_TRAIN:-20}"
N_VAL="${N_VAL:-5}"
OUTPUT_DIR="${PROJECT_DIR}/outputs/stage_gcg_full"
OUTPUT_FILE="advbench_manifest_v1.jsonl"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

mkdir -p logs "$OUTPUT_DIR"

echo "========================================================"
echo "  Stage GCG-Full — AdvBench Manifest Build"
echo "========================================================"
echo "SLURM_JOB_ID:  ${SLURM_JOB_ID}"
echo "N_TRAIN:       ${N_TRAIN}"
echo "N_VAL:         ${N_VAL}"
echo "OUTPUT_DIR:    ${OUTPUT_DIR}"
echo "GIT_REVISION:  $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:          $(date -u)"

python -m poc_stage_gcg_early.build_advbench_manifest \
    --n-train "${N_TRAIN}" \
    --n-val "${N_VAL}" \
    --output-dir "${OUTPUT_DIR}" \
    --output-file "${OUTPUT_FILE}"

echo ""
echo "Manifest rows:"
wc -l "${OUTPUT_DIR}/${OUTPUT_FILE}"
echo "SHA256:"
cat "${OUTPUT_DIR}/advbench_manifest_v1.sha256"

echo ""
echo "========================================================"
echo "  Manifest Build COMPLETE"
echo "  $(date -u)"
echo "========================================================"
