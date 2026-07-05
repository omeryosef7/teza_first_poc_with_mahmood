#!/bin/bash
# One-liner status wrapper: runs the completion audit for both models (if
# RUN_DIR is given) and prints squeue for the current user.
#
# Usage:
#   ./slurm_scripts/status_ae_experiment.sh [RUN_DIR]
#
# If RUN_DIR is omitted, only squeue is printed.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUN_DIR="${1:-}"

cd "$PROJECT_DIR"

if [ -n "$RUN_DIR" ]; then
    echo "=== Qwen3 audit ==="
    python -m poc_stage_ae.audit_ae_run \
        --manifest "$RUN_DIR/manifests/qwen3_ae_manifest.jsonl" \
        --generation-dir "$RUN_DIR/generation/qwen3" \
        --hidden-states-dir "$RUN_DIR/qwen" \
        --scoring-dir "$RUN_DIR/qwen" \
        --output "$RUN_DIR/qwen/status" || echo "(qwen audit failed — generation dir may not exist yet)"

    echo ""
    echo "=== Gemma4 audit ==="
    python -m poc_stage_ae.audit_ae_run \
        --manifest "$RUN_DIR/manifests/gemma4_ae_manifest.jsonl" \
        --generation-dir "$RUN_DIR/generation/gemma4" \
        --hidden-states-dir "$RUN_DIR/gemma" \
        --scoring-dir "$RUN_DIR/gemma" \
        --output "$RUN_DIR/gemma/status" || echo "(gemma audit failed — generation dir may not exist yet)"
    echo ""
else
    echo "No RUN_DIR given — skipping audit, showing squeue only."
    echo ""
fi

echo "=== squeue -u \$USER ==="
squeue -u "$USER"
