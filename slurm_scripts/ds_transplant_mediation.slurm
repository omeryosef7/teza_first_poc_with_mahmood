#!/bin/bash

#SBATCH --job-name=ds_transplant
#SBATCH --output=logs/ds_transplant_%j.out
#SBATCH --error=logs/ds_transplant_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# NEXT_CAUSAL_SPRINT Stage 2 (PRIMARY): State x Receiver-Context causal transplant.
#
# Runs 34_intervention_sweep.py --mode replace with the COMPLETED 2x3 specs
# (adds DS_from_Direct + the Neutral_from_Neutral / DS_from_DS self-transplant
# diagonals), then 43_transplant_mediation.py to compute IE_state / DE_context /
# INT / TE / PORT_Direct / RESID_ctx with paired bootstrap CIs and the
# self-transplant faithfulness check.
#
# Reuses the canonical CARROT<->BOMB bench, reps, and directions from the prior
# replace run (interv_summary 20260729_221157) so the 3 new arms are directly
# comparable to the 3 already-measured cells.
#
# Usage (smoke: 2 prompts/cell, windows fast):
#   SMOKE=1 sbatch slurm_scripts/ds_transplant_mediation.slurm
# Usage (full confirmatory, 12 prompts/cell, matches prior run):
#   sbatch slurm_scripts/ds_transplant_mediation.slurm
# Optional overrides: BENCH=, REPS_DIR=, DIR_DIR=, METRIC=, NPROMPTS=

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
DSC="$PROJECT_DIR/doublespeak_causality"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

# Default to the CONSISTENT triple built by job 694417 (bench/reps/dir all matched).
# Do NOT revert to the Jul29 reps — they mismatch the current bench (see BUG_AND_DEVIATION_LOG B1).
BENCH="${BENCH:-$DSC/data/pair_benchmark/pair_carrot_bomb.json}"
REPS_DIR="${REPS_DIR:-$DSC/outputs/pair_reps_Llama-3.1-8B-Instruct_20260730_154913_694417}"
DIR_DIR="${DIR_DIR:-$DSC/outputs/pair_directions_20260730_154944_694417}"
METRIC="${METRIC:-p_concept}"
SEED="${SEED:-0}"
SMOKE_FLAG="${SMOKE:-0}"
if [ "$SMOKE_FLAG" = "1" ]; then NPROMPTS="${NPROMPTS:-2}"; else NPROMPTS="${NPROMPTS:-12}"; fi

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONUNBUFFERED=1

echo "=== DS Transplant Mediation (Stage 2) ==="
date; hostname; echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}  SMOKE=$SMOKE_FLAG  NPROMPTS=$NPROMPTS  METRIC=$METRIC"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)
echo "GPU: $GPU_NAME"
# Project rule: L40S only. Nodelist pins L40S nodes; this guard is belt-and-suspenders.
if ! echo "$GPU_NAME" | grep -qi "L40S"; then
    echo "FATAL: GPU is not L40S ($GPU_NAME) — refusing to run (project rule)." >&2
    exit 1
fi

for f in "$BENCH" "$REPS_DIR/per_prompt.npz" "$DIR_DIR/directions.npz"; do
    [ -e "$f" ] || { echo "FATAL: missing input $f" >&2; exit 1; }
done

echo "--- 34_intervention_sweep.py --mode replace (completed 2x3 specs) ---"
python doublespeak_causality/34_intervention_sweep.py \
    --bench "$BENCH" --reps-dir "$REPS_DIR" --dir-dir "$DIR_DIR" \
    --mode replace --readout cloze --component resid_post \
    --dir-position codeword_last --site codeword_last \
    --layer-groups single --alpha-mode absolute \
    --n-prompts "$NPROMPTS" \
    --splits dev,heldout --crossfit true --seed "$SEED"

# Locate the run dir just produced (out_dir uniq == SLURM_JOB_ID, else PID; match newest).
RUNDIR=$(ls -dt "$DSC/outputs/pair_interv_replace_"* 2>/dev/null | head -1)
echo "RUNDIR=$RUNDIR"
[ -f "$RUNDIR/interv_raw.jsonl" ] || { echo "FATAL: no interv_raw.jsonl in $RUNDIR" >&2; exit 1; }

echo "--- 43_transplant_mediation.py (metric=$METRIC) ---"
python doublespeak_causality/43_transplant_mediation.py \
    --interv-dir "$RUNDIR" --metric "$METRIC" --equiv-margin 0.05 \
    --out "$RUNDIR/transplant_mediation_${METRIC}.json"

# Also emit the log-odds view as a secondary metric for the same run.
python doublespeak_causality/43_transplant_mediation.py \
    --interv-dir "$RUNDIR" --metric logodds --equiv-margin 0.5 \
    --out "$RUNDIR/transplant_mediation_logodds.json" || true

echo "=== DONE ==="; date
echo "ARTIFACTS: $RUNDIR/transplant_mediation_${METRIC}.json"