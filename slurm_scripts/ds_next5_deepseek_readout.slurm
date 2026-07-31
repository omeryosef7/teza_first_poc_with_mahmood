#!/bin/bash

#SBATCH --job-name=ds_n5_dsread
#SBATCH --output=logs/ds_n5_dsread_%j.out
#SBATCH --error=logs/ds_n5_dsread_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# NEXT5 W2 — DeepSeek-R1-Distill-Llama-8B readout GATE (3rd architecture).
# DeepSeek hardcodes <think>, so the concept/codeword next-token readout must be taken at the
# first ANSWER token AFTER </think> (31's generate_with_first_scores answer_marker path).
# This job ONLY runs the readout gate: does DS-Neutral read_as_concept exclude 0 on DeepSeek?
# If it passes, the transplant chain (32->34->43) is worth building the answer-position score for.
# The answer marker is quoted INLINE here (never via unquoted $CMD) so the shell can't treat
# </think> as a redirect.
#
# Usage:  sbatch slurm_scripts/ds_next5_deepseek_readout.slurm
# Overrides: BENCH=, MAX_NEW_TOKENS=, LIMIT=

set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
DSC="$PROJECT_DIR/doublespeak_causality"; CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MODEL="${MODEL:-deepseek-ai/DeepSeek-R1-Distill-Llama-8B}"
BENCH="${BENCH:-$DSC/data/pair_benchmark/pair_carrot_bomb.json}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-2048}"   # DeepSeek CoT is long; must reach </think>+1 answer tok
LIMIT="${LIMIT:-120}"                       # stratified cap over (condition, readout)

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface" HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch" TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" PYTHONUNBUFFERED=1

echo "=== NEXT5 W2 DeepSeek readout gate ==="; date; hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local} MODEL=$MODEL MAX_NEW_TOKENS=$MAX_NEW_TOKENS LIMIT=$LIMIT"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true); echo "GPU: $GPU_NAME"
echo "$GPU_NAME" | grep -qi "L40S" || { echo "FATAL: GPU not L40S ($GPU_NAME)" >&2; exit 1; }
[ -e "$BENCH" ] || { echo "FATAL: missing bench $BENCH" >&2; exit 1; }
cd "$DSC"

# answer marker quoted INLINE (safe). --enable-thinking default => think=None (DeepSeek ignores
# the kwarg and always emits <think>); the readout is scored at the first post-</think> token.
python 31_validate_readouts.py --bench "$BENCH" --model "$MODEL" \
    --answer-marker '</think>' --max-new-tokens "$MAX_NEW_TOKENS" --limit "$LIMIT" --seed 0

echo "=== DONE ==="; date
