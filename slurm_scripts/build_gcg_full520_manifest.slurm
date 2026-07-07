#!/bin/bash

#SBATCH --job-name=gcg_full520_manifest
#SBATCH --output=logs/gcg_full520_manifest_%j.out
#SBATCH --error=logs/gcg_full520_manifest_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:15:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Ablation 4F prep — Build full 520-behavior AdvBench manifest.
#
# Reads all 520 rows from llm-attacks/data/advbench/harmful_behaviors.csv
# and writes outputs/stage_gcg_full/advbench_full520_manifest.jsonl.
# CPU-only (1 GPU requested for account requirements only).
#
# Usage:
#   sbatch slurm_scripts/build_gcg_full520_manifest.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs

echo "========================================================"
echo "  Ablation 4F prep — Build Full 520-Behavior Manifest"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"

CSV="${PROJECT_DIR}/llm-attacks/data/advbench/harmful_behaviors.csv"
if [ ! -f "$CSV" ]; then
    echo "ERROR: AdvBench CSV not found: $CSV"
    exit 1
fi
echo "CSV: $(wc -l < "$CSV") lines"

python -m poc_stage_gcg_early.build_full520_manifest \
    --csv "${CSV}" \
    --output "${PROJECT_DIR}/outputs/stage_gcg_full/advbench_full520_manifest.jsonl"

echo ""
echo "Manifest rows: $(wc -l < "${PROJECT_DIR}/outputs/stage_gcg_full/advbench_full520_manifest.jsonl")"

echo ""
echo "========================================================"
echo "  Full 520-Behavior Manifest Build COMPLETE"
echo "  $(date -u)"
echo "========================================================"
