#!/bin/bash

#SBATCH --job-name=poc_s4_dircmp_gemma
#SBATCH --output=logs/poc_stage4_direction_comparison_gemma_%j.out
#SBATCH --error=logs/poc_stage4_direction_comparison_gemma_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602,n-302,n-303,n-304,n-305

# Stage 4 direction cosine comparison (Gemma 4) — CPU-only.
#
# Computes pairwise cosine similarities among all available refusal directions:
#   startofthink / endofthink / behavioral (eoi/endofresponse if present)
#
# Run AFTER all 4A1 jobs complete. Missing subdirs are skipped gracefully.
#
# Output: outputs/stage4/gemma4-e4b-it/direction_comparison/
#   cosine_summary.json
#   plots/cosine_heatmap.png
#   plots/cosine_by_layer.png

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

BASE_DIR="${BASE_DIR:-$PROJECT_DIR/outputs/stage4/gemma4-e4b-it}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_comparison}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUTPUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export PYTHONUNBUFFERED=1

echo "[stage4_direction_comparison_gemma] Starting at $(date) on $(hostname)"

python -m poc_stage4.compare_directions \
    --base-dir "$BASE_DIR" \
    --output-dir "$OUTPUT_DIR"

echo "[stage4_direction_comparison_gemma] Done at $(date)"
