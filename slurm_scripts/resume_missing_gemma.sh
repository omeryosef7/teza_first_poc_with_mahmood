#!/bin/bash
# Resubmit only the missing (goal_index, condition) generation array indices for
# Gemma4, based on outputs/.../status/resume_targets.jsonl written by
# poc_stage_ae.audit_ae_run. Thin wrapper — no SLURM-side logic beyond reading
# the target list and computing array indices (task_id = goal_index*4 + cond_idx).
#
# Usage:
#   ./slurm_scripts/resume_missing_gemma.sh <RUN_DIR>
#
# Expects <RUN_DIR>/gemma/status/resume_targets.jsonl to exist (produced by:
#   python -m poc_stage_ae.audit_ae_run --manifest <RUN_DIR>/manifests/gemma4_ae_manifest.jsonl \
#       --generation-dir <RUN_DIR>/generation/gemma4 --output <RUN_DIR>/gemma/status
# )

set -euo pipefail

RUN_DIR="${1:?Usage: resume_missing_gemma.sh <RUN_DIR>}"
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RESUME_TARGETS="$RUN_DIR/gemma/status/resume_targets.jsonl"
MANIFEST_PATH="$RUN_DIR/manifests/gemma4_ae_manifest.jsonl"

if [ ! -f "$RESUME_TARGETS" ]; then
    echo "ERROR: $RESUME_TARGETS not found. Run poc_stage_ae.audit_ae_run first:"
    echo "  python -m poc_stage_ae.audit_ae_run --manifest $MANIFEST_PATH --generation-dir $RUN_DIR/generation/gemma4 --output $RUN_DIR/gemma/status"
    exit 1
fi

INDICES=$(python3 - "$RESUME_TARGETS" <<'PY'
import json, sys
cond_idx_map = {"A": 0, "D": 1, "E": 2, "G": 3}
targets = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
targets = [t for t in targets if t.get("model") == "gemma4"]
indices = sorted({int(t["goal_index"]) * 4 + cond_idx_map[t["condition"]] for t in targets})
print(",".join(str(i) for i in indices))
PY
)

if [ -z "$INDICES" ]; then
    echo "No missing Gemma4 rows — nothing to resubmit."
    exit 0
fi

echo "Resubmitting Gemma4 array indices: $INDICES"
sbatch --array="$INDICES%3" \
    --export=ALL,RUN_DIR="$RUN_DIR",MANIFEST_PATH="$MANIFEST_PATH" \
    "$PROJECT_DIR/slurm_scripts/submit_gemma_ae.sh"
