#!/bin/bash

#SBATCH --job-name=ds_stage4_toctou
#SBATCH --output=logs/ds_stage4_toctou_%j.out
#SBATCH --error=logs/ds_stage4_toctou_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# STAGE4 — TOCTOU factorial, gated on a GENERATION-VALIDATED refusal direction.
# One job, in order:
#   1. build_refusal_direction_llama.py --validate  (build + sign-check by generation +
#      write refusal_direction_llama_SELECTED.json naming the best layer / .pt).
#   2. GATE: if NO layer has both gains>0 (any_valid=false), FATAL exit 2 — never run the
#      factorial on an unvalidated refusal direction.
#   3. SMOKE (n-items 1) then, unless SMOKE=1, the full factorial (n-items $N_ITEMS) with
#      --refusal-pt = the selected .pt. The refusal layer is read from that .pt's .json.
#
# Usage:  SMOKE=1 sbatch slurm_scripts/ds_stage4_toctou.slurm   # first run: build+validate+smoke
#         sbatch slurm_scripts/ds_stage4_toctou.slurm           # SMOKE=0: also the full run
# Overrides: BENCH=, DIR_DIR=, N_ITEMS=, VAL_N_ITEMS=, INDUCE_ALPHA=

set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
DSC="$PROJECT_DIR/doublespeak_causality"; CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MODEL="meta-llama/Llama-3.1-8B-Instruct"
BENCH="${BENCH:-$DSC/data/pair_benchmark/pair_carrot_bomb.json}"
# Llama-3.1-8B carrot(codeword)/bomb(concept) d_Direct directions (directions.npz).
DIR_DIR="${DIR_DIR:-$DSC/outputs/pair_directions_20260730_190505_694691}"
OUT_STAGE="$DSC/outputs/stage_gcg_full"
SELECTED="$OUT_STAGE/refusal_direction_llama_SELECTED.json"
SMOKE_FLAG="${SMOKE:-0}"
N_ITEMS="${N_ITEMS:-40}"                 # full-run item count (smoke always uses 1)
VAL_N_ITEMS="${VAL_N_ITEMS:-15}"
INDUCE_ALPHA="${INDUCE_ALPHA:-8.0}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface" HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch" TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" PYTHONUNBUFFERED=1

echo "=== DS Stage4 TOCTOU (refusal-validate -> gate -> factorial) ==="; date; hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local} SMOKE=$SMOKE_FLAG N_ITEMS=$N_ITEMS"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true); echo "GPU: $GPU_NAME"
echo "$GPU_NAME" | grep -qi "L40S" || { echo "FATAL: GPU not L40S ($GPU_NAME)" >&2; exit 1; }
[ -e "$BENCH" ] || { echo "FATAL: missing bench $BENCH" >&2; exit 1; }
[ -d "$DIR_DIR" ] || { echo "FATAL: missing dir-dir $DIR_DIR" >&2; exit 1; }
cd "$DSC"

echo "--- STEP 1: build_refusal_direction_llama.py --validate ---"
python build_refusal_direction_llama.py --bench "$BENCH" --model "$MODEL" \
    --layers 12,14,16,18,20 --out "$OUT_STAGE" --validate \
    --val-n-items "$VAL_N_ITEMS" --val-max-new-tokens 64 --induce-alpha "$INDUCE_ALPHA" --seed 0

echo "--- STEP 2: GATE on SELECTED.json ---"
[ -f "$SELECTED" ] || { echo "FATAL: no $SELECTED" >&2; exit 2; }
BEST_PT=$(python -c "import json; d=json.load(open('$SELECTED')); print(d.get('selected_pt') or '')")
ANY_VALID=$(python -c "import json; print(json.load(open('$SELECTED')).get('any_valid'))")
echo "any_valid=$ANY_VALID selected_pt=$BEST_PT"
if [ "$ANY_VALID" != "True" ] || [ -z "$BEST_PT" ] || [ ! -f "$BEST_PT" ]; then
    echo "FATAL: no refusal layer passed generation validation (both gains>0). Refusing to run the" >&2
    echo "       factorial on an unvalidated refusal direction." >&2
    exit 2
fi
echo "GATE PASSED: BEST_PT=$BEST_PT"

run_factorial () {   # $1 = n-items, $2 = label
    local NI="$1" LABEL="$2"
    echo "--- STEP 3 ($LABEL): 45_toctou_factorial.py --n-items $NI ---"
    python 45_toctou_factorial.py --bench "$BENCH" --refusal-pt "$BEST_PT" \
        --dir-dir "$DIR_DIR" --model "$MODEL" --n-items "$NI" --seed 0
    local RUNDIR; RUNDIR=$(ls -dt outputs/toctou_* 2>/dev/null | head -1)
    echo "RUNDIR=$DSC/$RUNDIR"
    [ -f "$RUNDIR/toctou_summary.json" ] || { echo "FATAL: no toctou_summary.json ($LABEL)" >&2; exit 3; }
    echo "=== $LABEL headline: INTERACTION + per-timing refusal_gain ==="
    python -c "
import json
d=json.load(open('$RUNDIR/toctou_summary.json'))
oc=d.get('analysis',{}).get('outcomes',{})
for name,res in oc.items():
    it=res.get('INTERACTION')
    if isinstance(it,dict) and 'effect' in it:
        print(f'  {name:10} INTERACTION eff={it[\"effect\"]:+.4f} [{it.get(\"lo\"):+.4f},{it.get(\"hi\"):+.4f}] n={it.get(\"n\")} sig={it.get(\"significant_corrected\")}')
    for t,blk in (res.get('refusal_gain') or {}).items():
        if isinstance(blk,dict) and 'effect' in blk:
            print(f'  {name:10} refusal_gain[{t:5}] eff={blk[\"effect\"]:+.4f} [{blk.get(\"lo\"):+.4f},{blk.get(\"hi\"):+.4f}] n={blk.get(\"n\")}')"
    echo "SUMMARY=$DSC/$RUNDIR/toctou_summary.json"
}

run_factorial 1 "SMOKE"
if [ "$SMOKE_FLAG" != "1" ]; then
    run_factorial "$N_ITEMS" "FULL"
else
    echo "SMOKE=1 -> skipping full run. Re-run with SMOKE=0 for the full factorial."
fi

echo "=== DONE ==="; date
