#!/bin/bash
# Submit all 24 jobs for hvp/dvp variants (12 4A1 + chained 4A2→4B→4C)
# Each 4A1 is submitted independently; 4A2/4B/4C chain with afterok dependency.
# PCA subspace selection (no model intervention tests) — SUBSPACE_METHOD=pca.
# 4B with LAYERS=all because PCA components span all layers (no single-layer assignments).

set -euo pipefail

cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood

submit_chain() {
    local MODEL="$1"        # qwen3 or gemma4
    local VARIANT="$2"      # hvp or dvp
    local POSITION="$3"     # startofthink/endofthink/endofresponse
    local SCRIPT_A1="$4"    # path to 4A1 SLURM script
    local A2_SCRIPT="$5"    # path to 4A2 SLURM script
    local B_SCRIPT="$6"     # path to 4B SLURM script
    local C_SCRIPT="$7"     # path to 4C SLURM script

    local FULL_VARIANT="${VARIANT}_${POSITION}"
    echo ""
    echo "=== Submitting ${MODEL} ${FULL_VARIANT} ==="

    J1=$(sbatch --parsable "$SCRIPT_A1")
    echo "  4A1 job: $J1"

    J2=$(INPUT_VARIANT="$FULL_VARIANT" SUBSPACE_METHOD=pca \
         sbatch --parsable --dependency=afterok:${J1} "$A2_SCRIPT")
    echo "  4A2 (PCA) job: $J2 (after $J1)"

    J3=$(INPUT_VARIANT="$FULL_VARIANT" LAYERS=all \
         sbatch --parsable --dependency=afterok:${J2} "$B_SCRIPT")
    echo "  4B job: $J3 (after $J2)"

    J4=$(INPUT_VARIANT="$FULL_VARIANT" \
         sbatch --parsable --dependency=afterok:${J3} "$C_SCRIPT")
    echo "  4C job: $J4 (after $J3)"
}

# --- Qwen3-14B chains ---
for VARIANT in hvp dvp; do
    for POSITION in startofthink endofthink endofresponse; do
        submit_chain \
            qwen3 \
            "$VARIANT" \
            "$POSITION" \
            "slurm_scripts/stage4a1_qwen3_${VARIANT}_${POSITION}.slurm" \
            "slurm_scripts/stage4a2_qwen3_subspace.slurm" \
            "slurm_scripts/stage4b_qwen3_token_dynamics_subspace.slurm" \
            "slurm_scripts/stage4_subspace_stats.slurm"
    done
done

# --- Gemma 4 E4B-it chains ---
for VARIANT in hvp dvp; do
    for POSITION in startofthink endofthink endofresponse; do
        submit_chain \
            gemma4 \
            "$VARIANT" \
            "$POSITION" \
            "slurm_scripts/stage4a1_gemma_${VARIANT}_${POSITION}.slurm" \
            "slurm_scripts/stage4a2_gemma_subspace.slurm" \
            "slurm_scripts/stage4b_gemma_token_dynamics_subspace.slurm" \
            "slurm_scripts/stage4_subspace_stats_gemma.slurm"
    done
done

echo ""
echo "=== All chains submitted ==="
echo "Monitor with: squeue -u \$(whoami) | grep poc"
