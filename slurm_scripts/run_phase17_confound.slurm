#!/bin/bash
#SBATCH --job-name=phase17_confound
#SBATCH --output=logs/phase17_confound_%j.out
#SBATCH --error=logs/phase17_confound_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-poc_stage2}"
mkdir -p logs
# Env overrides: CONDITIONS (default "C D"), CELLS, OUT, SCORES, RUN_DIR (for held-out re-runs).
CONDITIONS="${CONDITIONS:-C D}"
CELLS="${CELLS:-mlp:think_content_1:19 logistic:prefill_last:38 fisher:think_content_1:20 fisher:prefill_last:16}"
OUT="${OUT:-outputs/phase17_detect/detector_CvsD_confound.csv}"
SCORES="${SCORES:-outputs/phase5_mechanistic/phase6_scores.jsonl}"
RUN_DIR="${RUN_DIR:-outputs/phase5_mechanistic/extraction}"
python -u scripts/phase17_confound.py \
    --model "${MODEL:-qwen3}" \
    --conditions $CONDITIONS \
    --cells $CELLS \
    --scores "$SCORES" \
    --run-dir "$RUN_DIR" \
    --bootstrap 1000 \
    --out "$OUT"
