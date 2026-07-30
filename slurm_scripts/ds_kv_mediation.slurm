#!/bin/bash

#SBATCH --job-name=ds_kv_mediation
#SBATCH --output=logs/ds_kv_mediation_%j.out
#SBATCH --error=logs/ds_kv_mediation_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# NEXT_CAUSAL_SPRINT Stage 3 — demonstration K/V mediation (44_kv_mediation.py).
# 2x2 {query-state} x {demo-K/V} on the DOUBLESPEAK receiver, isolating whether the
# Stage-2 context effect is carried by the demonstration K/V and whether the cloze
# readout is merely re-reading the demos (ReRead_test = C1-C3) vs genuine consolidation.
# Also records the confound-free PatchscopeDecoder readout per cell.
#
# CRITICAL SMOKE CHECK: the C1_selfswap faithfulness arm must reproduce C1 (~0) on the
# REAL model before the full run is trusted (the ToyStack test cannot cover the real
# tokenizer/positions).
#
# Usage:  SMOKE=1 sbatch slurm_scripts/ds_kv_mediation.slurm   # n-prompts 4, fast
#         sbatch slurm_scripts/ds_kv_mediation.slurm           # full n-prompts 12
# Overrides: BENCH=, REPS_DIR=, NPROMPTS=

set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
DSC="$PROJECT_DIR/doublespeak_causality"; CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MODEL="meta-llama/Llama-3.1-8B-Instruct"
BENCH="${BENCH:-$DSC/data/pair_benchmark/pair_carrot_bomb.json}"
REPS_DIR="${REPS_DIR:-$DSC/outputs/pair_reps_Llama-3.1-8B-Instruct_20260730_154913_694417}"
SMOKE_FLAG="${SMOKE:-0}"
if [ "$SMOKE_FLAG" = "1" ]; then NPROMPTS="${NPROMPTS:-4}"; else NPROMPTS="${NPROMPTS:-12}"; fi

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface" HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch" TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" PYTHONUNBUFFERED=1

echo "=== DS KV Mediation (Stage 3) ==="; date; hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local} SMOKE=$SMOKE_FLAG NPROMPTS=$NPROMPTS"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true); echo "GPU: $GPU_NAME"
echo "$GPU_NAME" | grep -qi "L40S" || { echo "FATAL: GPU not L40S ($GPU_NAME)" >&2; exit 1; }
[ -e "$BENCH" ] || { echo "FATAL: missing bench $BENCH" >&2; exit 1; }
cd "$DSC"

echo "--- 44_kv_mediation.py (2x2 demo-K/V mediation) ---"
python 44_kv_mediation.py --bench "$BENCH" --reps-dir "$REPS_DIR" --model "$MODEL" \
    --readout cloze --n-prompts "$NPROMPTS" --splits dev,heldout --seed 0
RUNDIR=$(ls -dt outputs/pair_kv_mediation_* 2>/dev/null | head -1); echo "RUNDIR=$DSC/$RUNDIR"
[ -f "$RUNDIR/kv_mediation_summary.json" ] || { echo "FATAL: no summary" >&2; exit 1; }

echo "=== FAITHFULNESS CHECK (self-swap must ~0) + headline ==="
python -c "
import json
d=json.load(open('$RUNDIR/kv_mediation_summary.json'))
est=d.get('estimands',d)
for k in sorted(est):
    if any(t in k for t in ('faithful','ReRead','DE_via','INT_2x2','random')):
        e=est[k]
        if isinstance(e,dict) and 'effect' in e:
            print(f'  {k:28} {e[\"effect\"]:+.4f} [{e.get(\"lo\",0):+.4f},{e.get(\"hi\",0):+.4f}] n={e.get(\"n\")}')"
echo "=== DONE ==="; date; echo "SUMMARY=$DSC/$RUNDIR/kv_mediation_summary.json"