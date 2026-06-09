#!/bin/bash

#SBATCH --job-name=stage4_5b_llm_annotate
#SBATCH --output=logs/stage4_5b_llm_annotate_%j.out
#SBATCH --error=logs/stage4_5b_llm_annotate_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4.5B: LLM onset annotation using o4-mini (OpenAI API, no GPU needed).
#
# Steps:
#   1. Pilot annotation (10 examples from pilot_example_queue.csv)
#   2. Quality gate check
#   3. If gate passes, annotate all 42 examples
#   4. Final quality gate
#
# Requires: OPENAI_API_KEY in .env
# Output:   outputs/stage4_5/llm_harmful_interaction_annotations/run_<timestamp>/

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

PILOT_QUEUE="${PILOT_QUEUE:-$PROJECT_DIR/review/pilot_example_queue.csv}"
RUN_ALL="${RUN_ALL:-false}"
DRY_RUN="${DRY_RUN:-false}"

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

echo "=== Stage 4.5B LLM Annotation started ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
python -V

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "ERROR: OPENAI_API_KEY not set — check .env"
    exit 1
fi
echo "OPENAI_API_KEY: set (${#OPENAI_API_KEY} chars)"
echo "PILOT_QUEUE=$PILOT_QUEUE"
echo "RUN_ALL=$RUN_ALL"

# --- Step 1: Pilot annotation ---
echo ""
echo "=== Step 1: Pilot annotation (queue: $PILOT_QUEUE) ==="

PILOT_ARGS=(--queue "$PILOT_QUEUE")
if [ "${DRY_RUN:-false}" = "true" ]; then
    PILOT_ARGS+=(--dry-run)
fi

python -m poc_stage4_5.llm_annotate_harmful_interaction "${PILOT_ARGS[@]}"

# Find the latest run dir
LATEST_RUN=$(ls -td "$PROJECT_DIR/outputs/stage4_5/llm_harmful_interaction_annotations"/run_* 2>/dev/null | head -1)
if [ -z "$LATEST_RUN" ]; then
    echo "ERROR: no annotation run directory found after pilot"
    exit 1
fi
echo "Pilot run dir: $LATEST_RUN"

# --- Step 2: Quality gate after pilot ---
echo ""
echo "=== Step 2: Quality gate (pilot) ==="
python -m poc_stage4_5.audit_llm_annotations --run-dir "$LATEST_RUN"
GATE_EXIT=$?
if [ $GATE_EXIT -ne 0 ]; then
    echo "WARNING: quality gate failed on pilot — check spotcheck_queue.csv in $LATEST_RUN"
    echo "Set RUN_ALL=true to override and continue with full annotation anyway."
    if [ "${RUN_ALL:-false}" != "true" ]; then
        exit 1
    fi
fi

# --- Step 3: Full annotation (if requested or pilot passed) ---
if [ "${RUN_ALL:-false}" = "true" ] || [ $GATE_EXIT -eq 0 ]; then
    echo ""
    echo "=== Step 3: Full annotation (all 42 examples) ==="

    FULL_ARGS=(--all)
    if [ "${DRY_RUN:-false}" = "true" ]; then
        FULL_ARGS+=(--dry-run)
    fi

    python -m poc_stage4_5.llm_annotate_harmful_interaction "${FULL_ARGS[@]}"

    # Find updated run dir
    LATEST_RUN=$(ls -td "$PROJECT_DIR/outputs/stage4_5/llm_harmful_interaction_annotations"/run_* 2>/dev/null | head -1)

    # --- Step 4: Final quality gate ---
    echo ""
    echo "=== Step 4: Final quality gate ==="
    python -m poc_stage4_5.audit_llm_annotations --run-dir "$LATEST_RUN"
    echo "Final annotation run dir: $LATEST_RUN"
fi

echo ""
echo "=== Stage 4.5B LLM Annotation finished ==="
date
echo "Next step: sbatch slurm_scripts/stage4_5b_event_aligned_analysis.slurm"
