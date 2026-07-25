#!/bin/bash
#SBATCH --job-name=phase6_signal
#SBATCH --output=logs/phase6_signal_%j.out
#SBATCH --error=logs/phase6_signal_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research

# Phase-6 (§10) predictive-signal search (grouped LOGO Fisher AUC) — CPU only (small tensors, but
# torch import is slow on the login node). Env: CONDITIONS (space-sep, e.g. "F G"), OUT, SCORES, RUN_DIR.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
CONDITIONS="${CONDITIONS:?set CONDITIONS, e.g. \"F G\"}"
OUT="${OUT:?set OUT csv path}"
SCORES="${SCORES:-outputs/phase5_mechanistic/phase6_scores.jsonl}"
RUN_DIR="${RUN_DIR:-outputs/phase5_mechanistic/extraction}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
mkdir -p logs
echo "[phase6] job=${SLURM_JOB_ID:-?} conditions=$CONDITIONS out=$OUT date=$(date -u)"
python -u scripts/phase6_signal_search.py \
    --run-dir "$RUN_DIR" --model "${MODEL:-qwen3}" \
    --conditions $CONDITIONS \
    --scores "$SCORES" --out "$OUT" ${EXTRA_ARGS:-}
echo "[phase6] done $(date -u)"
