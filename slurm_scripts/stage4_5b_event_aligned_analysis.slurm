#!/bin/bash

#SBATCH --job-name=stage4_5b_event_analysis
#SBATCH --output=logs/stage4_5b_event_analysis_%j.out
#SBATCH --error=logs/stage4_5b_event_analysis_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4.5B: Event-aligned dynamics analysis using LLM-annotated onset indices.
#
# Runs analyze_harmful_interaction_aligned_dynamics.py with o4-mini annotations.
# Outputs get _llm_annotated suffix to distinguish from human ground truth.
#
# Requires: completed annotation run (consensus_annotations.csv)
# Set ANNOTATIONS_FILE to the path of your consensus CSV.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

# Auto-find latest annotation run if not specified
if [ -z "${ANNOTATIONS_FILE:-}" ]; then
    LATEST_RUN=$(ls -td "$PROJECT_DIR/outputs/stage4_5/llm_harmful_interaction_annotations"/run_* 2>/dev/null | head -1)
    if [ -z "$LATEST_RUN" ]; then
        echo "ERROR: No annotation run found. Run stage4_5b_llm_annotation.slurm first."
        exit 1
    fi
    ANNOTATIONS_FILE="$LATEST_RUN/consensus_annotations.csv"
fi

ANNOTATION_SOURCE="${ANNOTATION_SOURCE:-o4mini}"
OUTPUT_SUFFIX="${OUTPUT_SUFFIX:-_llm_annotated}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$RUNTIME_DIR"/{config,data,runtime,ipython}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"

echo "=== Stage 4.5B Event-Aligned Analysis started ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
python -V
echo "ANNOTATIONS_FILE=$ANNOTATIONS_FILE"
echo "ANNOTATION_SOURCE=$ANNOTATION_SOURCE"

if [ ! -f "$ANNOTATIONS_FILE" ]; then
    echo "ERROR: annotations file not found: $ANNOTATIONS_FILE"
    exit 1
fi

echo ""
echo "=== Running event-aligned dynamics analysis ==="
python -m poc_stage4_5.analyze_harmful_interaction_aligned_dynamics \
    --annotations-file "$ANNOTATIONS_FILE" \
    --annotation-source "$ANNOTATION_SOURCE" \
    --allow-llm-annotations

echo ""
echo "=== Stage 4.5B Event-Aligned Analysis finished ==="
date
