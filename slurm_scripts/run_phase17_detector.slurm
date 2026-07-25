#!/bin/bash
#SBATCH --job-name=phase17_detect
#SBATCH --output=logs/phase17_detect_%j.out
#SBATCH --error=logs/phase17_detect_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research

# Phase-17 (§21) success-vs-failure detector comparison (CPU; torch import slow on login node).
# Env: CONDITIONS (space-sep, default "C D"), OUT, LAYERS (optional).
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
CONDITIONS="${CONDITIONS:-C D}"
OUT="${OUT:?set OUT csv path}"
LAYERS="${LAYERS:-8 12 16 20 24 28 32}"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
mkdir -p logs
echo "[phase17] job=${SLURM_JOB_ID:-?} conditions=$CONDITIONS out=$OUT date=$(date -u)"
python -u scripts/phase17_detector.py --conditions $CONDITIONS --layers $LAYERS --out "$OUT"
echo "[phase17] done $(date -u)"
