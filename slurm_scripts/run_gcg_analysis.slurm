#!/bin/bash

#SBATCH --job-name=gcg_analysis
#SBATCH --output=logs/gcg_analysis_%j.out
#SBATCH --error=logs/gcg_analysis_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1

# Stage GCG-Early — Pareto frontier + detection delay analysis (CPU only, no GPU).
#
# Runs analyze_pareto_frontier.py and analyze_detection_delay.py on a completed
# run directory. Writes RESULTS_SUMMARY.md and DETECTION_DELAY_ANALYSIS.md.
#
# Usage:
#   sbatch --export=ALL,RUN_DIR=outputs/stage_gcg_early/gcg_qwen3_repr_8b \
#          slurm_scripts/run_gcg_analysis.slurm
#
# Or analyze all completed runs:
#   sbatch slurm_scripts/run_gcg_analysis.slurm   (RUN_DIR defaults to all completed)

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
# Default: analyze all directories under outputs/stage_gcg_early/ that have DONE file
RUN_DIR="${RUN_DIR:-}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

mkdir -p logs

echo "========================================================"
echo "  Stage GCG-Early — Pareto + Detection Delay Analysis"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"

if [ -n "$RUN_DIR" ]; then
    RUN_DIRS=("$RUN_DIR")
else
    # Analyze all completed runs
    mapfile -t RUN_DIRS < <(find outputs/stage_gcg_early -maxdepth 2 -name "DONE" -exec dirname {} \; 2>/dev/null | sort)
fi

echo "Run directories to analyze: ${#RUN_DIRS[@]}"
for dir in "${RUN_DIRS[@]}"; do
    echo "  $dir"
done

for run_dir in "${RUN_DIRS[@]}"; do
    echo ""
    echo "--- Analyzing: $run_dir ---"

    echo "  [Pareto frontier analysis]"
    python -m poc_stage_gcg_early.analyze_pareto_frontier --run-dir "$run_dir" 2>&1 || echo "  WARNING: Pareto analysis failed"

    if [ -f "${run_dir}/FREE_GENERATION_RESULTS.jsonl" ]; then
        echo "  [Detection delay analysis]"
        python -m poc_stage_gcg_early.analyze_detection_delay --run-dir "$run_dir" 2>&1 || echo "  WARNING: Detection delay analysis failed"
    else
        echo "  [Detection delay] Skipped — no FREE_GENERATION_RESULTS.jsonl"
    fi
done

echo ""
echo "========================================================"
echo "  Analysis COMPLETE"
echo "  Date: $(date -u)"
echo "========================================================"
