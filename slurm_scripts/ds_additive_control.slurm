#!/bin/bash

#SBATCH --job-name=ds_additive_ctrl
#SBATCH --output=logs/ds_additive_ctrl_%j.out
#SBATCH --error=logs/ds_additive_ctrl_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# NEXT_CAUSAL_SPRINT Stage 2 — ADDITIVE positive control on the CONSISTENT triple (job 694417).
# Reproduces the established d_Direct-installs / d_DS-inert dissociation via ADDITIVE intervention
# (34 --mode controls, alpha 1.0 relative), on the SAME bench/reps/dir as the transplant, so the
# transplant's weak PORT_Direct (a limitation of single-position full-state replacement) is
# contextualized: the concept IS installable additively; it is just not stored in a portable local
# state. Analyzed by 35_analyze_pair_causal.py.

set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
DSC="$PROJECT_DIR/doublespeak_causality"; CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MODEL="meta-llama/Llama-3.1-8B-Instruct"
BENCH="${BENCH:-$DSC/data/pair_benchmark/pair_carrot_bomb.json}"
REPS_DIR="${REPS_DIR:-$DSC/outputs/pair_reps_Llama-3.1-8B-Instruct_20260730_154913_694417}"
DIR_DIR="${DIR_DIR:-$DSC/outputs/pair_directions_20260730_154944_694417}"
NPROMPTS="${NPROMPTS:-12}"
MODE="${MODE:-controls}"          # 'controls' (single alpha) or 'dose' (alpha sweep)
ALPHAS="${ALPHAS:-1.0}"           # e.g. ALPHAS=1,2,4,8 with MODE=dose for the install curve
READOUT="${READOUT:-forced_choice}"   # forced_choice has dynamic range (B3); cloze floors DIRECT

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface" HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch" TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" PYTHONUNBUFFERED=1

echo "=== DS Additive Positive Control ==="; date; hostname
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true); echo "GPU: $GPU_NAME"
echo "$GPU_NAME" | grep -qi "L40S" || { echo "FATAL: GPU not L40S ($GPU_NAME)" >&2; exit 1; }
cd "$DSC"

echo "--- 34 --mode $MODE (add d_Direct / d_DS, alphas=$ALPHAS relative) ---"
python 34_intervention_sweep.py --bench "$BENCH" --reps-dir "$REPS_DIR" --dir-dir "$DIR_DIR" \
    --mode "$MODE" --readout "$READOUT" --component resid_post \
    --dir-position codeword_last --site codeword_last \
    --layer-groups single --alpha-mode relative --alphas "$ALPHAS" \
    --n-prompts "$NPROMPTS" --splits dev,heldout --crossfit true --seed 0
RUNDIR=$(ls -dt outputs/pair_interv_${MODE}_* | head -1); echo "RUNDIR=$DSC/$RUNDIR"
[ -f "$RUNDIR/interv_raw.jsonl" ] || { echo "FATAL: no interv_raw.jsonl" >&2; exit 1; }

echo "--- 35_analyze_pair_causal (d_Direct install / d_DS inert + control distribution) ---"
python 35_analyze_pair_causal.py --interv-dir "$RUNDIR" --out "$RUNDIR/pair_causal_analysis.json"
echo "=== DONE ==="; date; echo "ANALYSIS=$DSC/$RUNDIR/pair_causal_analysis.json"