#!/bin/bash
#SBATCH --job-name=phase4_cot
#SBATCH --output=logs/phase4_cot_%j.out
#SBATCH --error=logs/phase4_cot_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1

# Phase 4 (RESEARCH_PLAN_DISTILLING_JAILBREAKS.md sec 8): CoT-Hijacking baseline on
# our dev-25 AdvBench goals. API-only (no GPU) -> cpu-killable. Runs on a compute node
# where `import litellm` behaves (it hangs on the login node). Reuses
# poc_stage2/run_phase4_cot_baseline.py (which reuses the existing hijacking wrapper).
#
# Env overrides: TARGET_MODEL, LIMIT (0=full dev-25), N_STREAMS, N_ITERATIONS, MANIFEST, OUTPUT_DIR
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-poc_stage2}"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs outputs/phase4_cot_baseline

# Defensive: avoid litellm's network fetch of the model-cost map at import.
export LITELLM_LOCAL_MODEL_COST_MAP="True"

TARGET_MODEL="${TARGET_MODEL:-gpt-o4-mini}"
LIMIT="${LIMIT:-3}"
N_STREAMS="${N_STREAMS:-2}"
N_ITERATIONS="${N_ITERATIONS:-2}"
MANIFEST="${MANIFEST:-data/manifests/dev_25.csv}"
OUTPUT_DIR="${OUTPUT_DIR:-outputs/phase4_cot_baseline}"

echo "[phase4] target=$TARGET_MODEL limit=$LIMIT streams=$N_STREAMS iters=$N_ITERATIONS manifest=$MANIFEST"
python -u -m poc_stage2.run_phase4_cot_baseline \
    --target-model "$TARGET_MODEL" \
    --manifest "$MANIFEST" \
    --limit "$LIMIT" \
    --n-streams "$N_STREAMS" \
    --n-iterations "$N_ITERATIONS" \
    --output-dir "$OUTPUT_DIR"
echo "[phase4] done"
