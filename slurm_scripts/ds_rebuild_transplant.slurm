#!/bin/bash

#SBATCH --job-name=ds_rebuild_transplant
#SBATCH --output=logs/ds_rebuild_transplant_%j.out
#SBATCH --error=logs/ds_rebuild_transplant_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# NEXT_CAUSAL_SPRINT Stage 2 — CONSISTENT rebuild + transplant.
#
# The smoke (job 694383) revealed a bench/reps MISMATCH: the reps on disk (Jul29 21:53)
# predate the bench file rewrite (pair_carrot_bomb.json, Jul30 01:25), so feeding the new
# bench prompts with old reps floored the readout (identity p_concept ~0.005 vs 0.22 in
# the prior consistent run). This job rebuilds a CONSISTENT reps+directions set from the
# CURRENT bench, GATES on the readout validator, then runs the transplant + mediation.
#
# Chain (each python reloads the model; 33/43 are CPU):
#   31 validate readout  --> GATE on gate_pass_any (abort if the bench has no signal)
#   32 extract reps      --> per_prompt.npz (readout=cloze)
#   33 build directions  --> directions.npz
#   34 --mode replace    --> interv_raw.jsonl (completed 2x3 specs)
#   43 mediation         --> IE/DE/INT/TE + faithfulness
#
# Usage:  sbatch slurm_scripts/ds_rebuild_transplant.slurm
#         SMOKE=1 sbatch ...   (limit rows, n-prompts 2 — fast validation of the FIX)
# Overrides: BENCH=, NPROMPTS=

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
DSC="$PROJECT_DIR/doublespeak_causality"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MODEL="meta-llama/Llama-3.1-8B-Instruct"

BENCH="${BENCH:-$DSC/data/pair_benchmark/pair_carrot_bomb.json}"
READOUT="${READOUT:-forced_choice}"   # forced_choice has full dynamic range (DIRECT reads 0.785);
                                      # cloze FLOORS the positive control (DIRECT 0.005). See B3.
RUN_KV="${RUN_KV:-1}"                 # also run 44_kv_mediation.py on the same reps
SMOKE_FLAG="${SMOKE:-0}"
if [ "$SMOKE_FLAG" = "1" ]; then NPROMPTS="${NPROMPTS:-2}"; LIMIT="--limit 40"; else NPROMPTS="${NPROMPTS:-15}"; LIMIT=""; fi

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface" HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch" TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" PYTHONUNBUFFERED=1

echo "=== DS Rebuild + Transplant (Stage 2) ==="; date; hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local} SMOKE=$SMOKE_FLAG NPROMPTS=$NPROMPTS BENCH=$BENCH"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true); echo "GPU: $GPU_NAME"
echo "$GPU_NAME" | grep -qi "L40S" || { echo "FATAL: GPU not L40S ($GPU_NAME)" >&2; exit 1; }
[ -e "$BENCH" ] || { echo "FATAL: missing bench $BENCH" >&2; exit 1; }

cd "$DSC"

echo "--- [1/5] 31_validate_readouts (GATE) ---"
python 31_validate_readouts.py --bench "$BENCH" --model "$MODEL" $LIMIT --seed 0
RDIR=$(ls -dt outputs/pair_readout_* | head -1); echo "readout dir=$RDIR"
GATE=$(python -c "import json;print(json.load(open('$RDIR/readout_summary.json')).get('gate_pass_any'))")
echo "gate_pass_any=$GATE"
[ "$GATE" = "True" ] || { echo "FATAL: readout gate FAILED on $BENCH — aborting before transplant." >&2; exit 2; }

echo "--- [2/5] 32_extract_pair_reps (readout=$READOUT) ---"
python 32_extract_pair_reps.py --bench "$BENCH" --model "$MODEL" --readout "$READOUT" $LIMIT --seed 0
REPS_DIR="$DSC/$(ls -dt outputs/pair_reps_* | head -1)"; echo "reps_dir=$REPS_DIR"
[ -f "$REPS_DIR/per_prompt.npz" ] || { echo "FATAL: no per_prompt.npz" >&2; exit 1; }

echo "--- [3/5] 33_build_directions ---"
python 33_build_directions.py --reps-dir "$REPS_DIR" --seed 0
DIR_DIR="$DSC/$(ls -dt outputs/pair_directions_* | head -1)"; echo "dir_dir=$DIR_DIR"
[ -f "$DIR_DIR/directions.npz" ] || { echo "FATAL: no directions.npz" >&2; exit 1; }

echo "--- [4/6] 34_intervention_sweep --mode replace (2x3 specs, readout=$READOUT) ---"
python 34_intervention_sweep.py --bench "$BENCH" --reps-dir "$REPS_DIR" --dir-dir "$DIR_DIR" \
    --mode replace --readout "$READOUT" --component resid_post \
    --dir-position codeword_last --site codeword_last \
    --layer-groups single --alpha-mode absolute \
    --n-prompts "$NPROMPTS" --splits dev,heldout --crossfit true --seed 0
RUNDIR=$(ls -dt outputs/pair_interv_replace_* | head -1); echo "RUNDIR=$DSC/$RUNDIR"
[ -f "$RUNDIR/interv_raw.jsonl" ] || { echo "FATAL: no interv_raw.jsonl" >&2; exit 1; }

echo "--- [5/6] 43_transplant_mediation ---"
python 43_transplant_mediation.py --interv-dir "$RUNDIR" --metric p_concept --equiv-margin 0.05 \
    --out "$RUNDIR/transplant_mediation_p_concept.json"
python 43_transplant_mediation.py --interv-dir "$RUNDIR" --metric logodds --equiv-margin 0.5 \
    --out "$RUNDIR/transplant_mediation_logodds.json" || true

if [ "$RUN_KV" = "1" ]; then
  echo "--- [6/6] 44_kv_mediation (demo-K/V mediation, readout=$READOUT) ---"
  python 44_kv_mediation.py --bench "$BENCH" --reps-dir "$REPS_DIR" --model "$MODEL" \
      --readout "$READOUT" --n-prompts "$NPROMPTS" --splits dev,heldout --seed 0
  KVDIR=$(ls -dt outputs/pair_kv_mediation_* | head -1); echo "KVDIR=$DSC/$KVDIR"
fi

echo "=== DONE ==="; date
echo "READOUT_DIR=$DSC/$RDIR"
echo "REPS_DIR=$REPS_DIR"
echo "RUNDIR=$DSC/$RUNDIR"
echo "PRIMARY=$RUNDIR/transplant_mediation_p_concept.json"