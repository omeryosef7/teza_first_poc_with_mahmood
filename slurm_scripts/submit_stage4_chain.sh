#!/bin/bash
# Submit the full Stage 4 pipeline as a SLURM dependency chain.
#
# Two parallel tracks:
#
#   TRACK A (endofthink): uses new activation capture at </think> position
#     smoke → endofthink_full → subspace_endofthink → token_dynamics_endofthink
#
#   TRACK B (behavioral): uses Stage 6 trace outcomes (qwen_run_success)
#     behavioral → subspace_behavioral → token_dynamics_behavioral
#
# Each job only starts if ALL its dependencies succeeded (afterok).
# If any job fails, downstream jobs are cancelled automatically by SLURM.
#
# Usage: bash slurm_scripts/submit_stage4_chain.sh
# To check status: squeue -u $USER

set -euo pipefail

cd "$(dirname "$0")/.."
SLURM_DIR="slurm_scripts"

echo "=== Stage 4 Chain Submission ==="
echo "Working dir: $(pwd)"
echo ""

# ---------------------------------------------------------------------------
# TRACK A — endofthink
# ---------------------------------------------------------------------------

# A1: Smoke test (4 prompts, 30 min — gates the full run)
JOB_SMOKE=$(sbatch --parsable "$SLURM_DIR/stage4a1_qwen3_endofthink_smoke.slurm")
echo "A1 smoke          → job $JOB_SMOKE"

# A2: Full endofthink extraction (220+220 prompts, 36h) — only if smoke passed
JOB_ENDOFTHINK=$(sbatch --parsable \
    --dependency=afterok:"$JOB_SMOKE" \
    "$SLURM_DIR/stage4a1_qwen3_endofthink.slurm")
echo "A2 endofthink     → job $JOB_ENDOFTHINK  (after $JOB_SMOKE)"

# A3: Subspace selection from endofthink (24h) — only if endofthink done
JOB_SUBSPACE_EOT=$(sbatch --parsable \
    --dependency=afterok:"$JOB_ENDOFTHINK" \
    --export=ALL,INPUT_VARIANT=endofthink \
    "$SLURM_DIR/stage4a2_qwen3_subspace.slurm")
echo "A3 subspace_eot   → job $JOB_SUBSPACE_EOT  (after $JOB_ENDOFTHINK)"

# A4: Token dynamics using endofthink subspace (12h)
JOB_DYN_EOT=$(sbatch --parsable \
    --dependency=afterok:"$JOB_SUBSPACE_EOT" \
    --export=ALL,INPUT_VARIANT=endofthink \
    "$SLURM_DIR/stage4b_qwen3_token_dynamics_subspace.slurm")
echo "A4 dyn_eot        → job $JOB_DYN_EOT  (after $JOB_SUBSPACE_EOT)"

echo ""

# ---------------------------------------------------------------------------
# TRACK B — behavioral (reads existing Stage 6 traces, no generation)
# ---------------------------------------------------------------------------

# B1: Behavioral extraction (forward passes only, ~12h)
JOB_BEHAVIORAL=$(sbatch --parsable "$SLURM_DIR/stage4a1_qwen3_behavioral.slurm")
echo "B1 behavioral     → job $JOB_BEHAVIORAL"

# B2: Subspace selection from behavioral
JOB_SUBSPACE_BEH=$(sbatch --parsable \
    --dependency=afterok:"$JOB_BEHAVIORAL" \
    --export=ALL,INPUT_VARIANT=behavioral \
    "$SLURM_DIR/stage4a2_qwen3_subspace.slurm")
echo "B2 subspace_beh   → job $JOB_SUBSPACE_BEH  (after $JOB_BEHAVIORAL)"

# B3: Token dynamics using behavioral subspace
JOB_DYN_BEH=$(sbatch --parsable \
    --dependency=afterok:"$JOB_SUBSPACE_BEH" \
    --export=ALL,INPUT_VARIANT=behavioral \
    "$SLURM_DIR/stage4b_qwen3_token_dynamics_subspace.slurm")
echo "B3 dyn_beh        → job $JOB_DYN_BEH  (after $JOB_SUBSPACE_BEH)"

echo ""
echo "=== All jobs submitted ==="
echo ""
echo "Track A: $JOB_SMOKE → $JOB_ENDOFTHINK → $JOB_SUBSPACE_EOT → $JOB_DYN_EOT"
echo "Track B: $JOB_BEHAVIORAL → $JOB_SUBSPACE_BEH → $JOB_DYN_BEH"
echo ""
echo "Monitor: squeue -u $USER"
echo "Cancel all: scancel $JOB_SMOKE $JOB_ENDOFTHINK $JOB_SUBSPACE_EOT $JOB_DYN_EOT $JOB_BEHAVIORAL $JOB_SUBSPACE_BEH $JOB_DYN_BEH"
echo ""
echo "If endofthink is preempted, resubmit with:"
echo "  RESUME=true sbatch --dependency=afterok:<replacement_job> slurm_scripts/stage4a1_qwen3_endofthink.slurm"
