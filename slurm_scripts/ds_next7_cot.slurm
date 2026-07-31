#!/bin/bash

#SBATCH --job-name=ds_n7_cot
#SBATCH --output=logs/ds_n7_cot_%j.out
#SBATCH --error=logs/ds_n7_cot_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# NEXT7 N7-B — within-CoT concept-reading trajectory on a THINKING model.
# The </think> answer-marker has shell metachars, so it is quoted INLINE here (never via $CMD).
# Usage: MODEL=Qwen/Qwen3-14B sbatch slurm_scripts/ds_next7_cot.slurm
# Overrides: MODEL=, BENCH=, MAXTOK=, NPER=

set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
DSC="$PROJECT_DIR/doublespeak_causality"; CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MODEL="${MODEL:-Qwen/Qwen3-14B}"
BENCH="${BENCH:-$DSC/data/pair_benchmark/pair_carrot_bomb.json}"
MAXTOK="${MAXTOK:-1024}"
NPER="${NPER:-6}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface" HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch" TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" PYTHONUNBUFFERED=1

echo "=== NEXT7 N7-B CoT trajectory ==="; date; hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local} MODEL=$MODEL MAXTOK=$MAXTOK NPER=$NPER"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true); echo "GPU: $GPU_NAME"
echo "$GPU_NAME" | grep -qi "L40S" || { echo "FATAL: GPU not L40S ($GPU_NAME)" >&2; exit 1; }
[ -e "$BENCH" ] || { echo "FATAL: missing bench $BENCH" >&2; exit 1; }
cd "$DSC"

python 52_cot_concept_trajectory.py --bench "$BENCH" --model "$MODEL" \
    --enable-thinking true --answer-marker '</think>' --max-new-tokens "$MAXTOK" \
    --n-per-cell "$NPER" --readout one_word --seed 0

echo "=== DONE ==="; date
