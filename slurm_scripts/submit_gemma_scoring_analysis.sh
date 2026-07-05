#!/bin/bash

#SBATCH --job-name=ae_score_gemma4
#SBATCH --output=logs/ae_score_gemma4_%A_%a.out
#SBATCH --error=logs/ae_score_gemma4_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --array=0-43%3

# Stage AE — Gemma4 CPU-only scoring (StrongREJECT + heuristic failure taxonomy).
# No --gpus requested. Arrays over completed generation shard files under
# $RUN_DIR/generation/gemma4/shards/*.jsonl (sorted).
#
# Requires RUN_DIR passed via --export, e.g.:
#   sbatch --export=ALL,RUN_DIR="$RUN_DIR" slurm_scripts/submit_gemma_scoring_analysis.sh

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

if [ -z "${RUN_DIR:-}" ]; then
    echo "ERROR: RUN_DIR must be set via --export=ALL,RUN_DIR=..."
    exit 1
fi

cd "$PROJECT_DIR"

SHARDS_DIR="$RUN_DIR/generation/gemma4/shards"
mapfile -t SHARD_FILES < <(find "$SHARDS_DIR" -maxdepth 1 -name '*.jsonl' | sort)
TASK_ID=$SLURM_ARRAY_TASK_ID
SHARD_PATH="${SHARD_FILES[$TASK_ID]:-}"

if [ -z "$SHARD_PATH" ]; then
    echo "No shard file at array index $TASK_ID (only ${#SHARD_FILES[@]} shards found in $SHARDS_DIR). Exiting cleanly."
    exit 0
fi

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$RUN_DIR/gemma/scoring"

echo "=== Stage AE Scoring — Gemma4 Array Task ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}  SLURM_ARRAY_TASK_ID=${TASK_ID}"
echo "SHARD_PATH=$SHARD_PATH"
echo "RUN_DIR=$RUN_DIR"

python -m poc_stage_ae.score_ae_outputs \
    --model gemma4 \
    --generation-shard "$SHARD_PATH" \
    --output-dir "$RUN_DIR/gemma"

echo ""
echo "=== Task $TASK_ID ($SHARD_PATH) complete ==="
date
