#!/bin/bash

#SBATCH --job-name=ae_combined_analysis
#SBATCH --output=logs/ae_combined_analysis_%j.out
#SBATCH --error=logs/ae_combined_analysis_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research

# Stage AE — combined cross-model completion audit (CPU-only, no --gpus).
# Runs audit_ae_run.py across both models' manifests + generation/hidden-state/
# scoring outputs and writes the top-level completion summary. Analysis
# scripts proper (analyze_paired_ae.py etc., per plan Stage 9) are a later
# session's deliverable — this script currently wires up the audit gate that
# must pass before Stage 9 analysis is meaningful to run.
#
# Requires RUN_DIR passed via --export, e.g.:
#   sbatch --export=ALL,RUN_DIR="$RUN_DIR" slurm_scripts/submit_combined_analysis.sh

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

if [ -z "${RUN_DIR:-}" ]; then
    echo "ERROR: RUN_DIR must be set via --export=ALL,RUN_DIR=..."
    exit 1
fi

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$RUN_DIR/combined_analysis"

echo "=== Stage AE Combined Analysis / Audit ==="
date
hostname
echo "RUN_DIR=$RUN_DIR"

echo ""
echo "--- Qwen3 audit ---"
python -m poc_stage_ae.audit_ae_run \
    --manifest "$RUN_DIR/manifests/qwen3_ae_manifest.jsonl" \
    --generation-dir "$RUN_DIR/generation/qwen3" \
    --hidden-states-dir "$RUN_DIR/qwen" \
    --scoring-dir "$RUN_DIR/qwen" \
    --output "$RUN_DIR/qwen/status" || true

echo ""
echo "--- Gemma4 audit ---"
python -m poc_stage_ae.audit_ae_run \
    --manifest "$RUN_DIR/manifests/gemma4_ae_manifest.jsonl" \
    --generation-dir "$RUN_DIR/generation/gemma4" \
    --hidden-states-dir "$RUN_DIR/gemma" \
    --scoring-dir "$RUN_DIR/gemma" \
    --output "$RUN_DIR/gemma/status" || true

echo ""
echo "--- Combined (both models) audit ---"
python -m poc_stage_ae.audit_ae_run \
    --manifest "$RUN_DIR/manifests" \
    --generation-dir "$RUN_DIR/generation/qwen3" \
    --output "$RUN_DIR/combined_analysis/status_qwen3_only" || true

QWEN_MISSING=$(python3 -c "
import json
d = json.load(open('$RUN_DIR/qwen/status/completion_audit.json'))
print(d['total_missing_rows'])
" 2>/dev/null || echo "unknown")
GEMMA_MISSING=$(python3 -c "
import json
d = json.load(open('$RUN_DIR/gemma/status/completion_audit.json'))
print(d['total_missing_rows'])
" 2>/dev/null || echo "unknown")

echo ""
echo "Qwen3 missing rows: $QWEN_MISSING"
echo "Gemma4 missing rows: $GEMMA_MISSING"

if [ "$QWEN_MISSING" = "0" ] && [ "$GEMMA_MISSING" = "0" ]; then
    echo "Both models complete — writing top-level DONE marker."
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "$RUN_DIR/DONE"
else
    echo "Not all rows complete yet — DONE marker NOT written."
fi

date
