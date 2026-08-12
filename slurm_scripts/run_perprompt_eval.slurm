#!/bin/bash
#SBATCH --job-name=pp_eval
#SBATCH --output=logs/pp_eval_%j.out
#SBATCH --error=logs/pp_eval_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=8:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1

# =====================================================================================
# ASYMMETRY SPRINT §7.5 — batched evaluation of per-prompt / transfer arms.
# Loads the model ONCE and loops (scripts/eval_perprompt_batched.py), instead of paying
# ~18 min of weight loading per item via 26_eval.
#
#   MODE=perprompt : --export=ALL,MODE=perprompt,JOBLIST=<path>,ARM_LABEL=<label>
#   MODE=transfer  : --export=ALL,MODE=transfer,PLAN=<path>
# Optional: SHARD/NSHARD, EVAL_SEED (default 42), MAXNEW (default 2048).
#
# StrongREJECT needs OPENAI_API_KEY (sourced from .env). A null judge scores everything
# benign and would make a working arm look like total failure -- the aggregator warns on
# judge_fail_frac > 0, but check the .out before trusting any number.
# =====================================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"

MODE="${MODE:?must set MODE=perprompt|transfer}"
EVAL_SEED="${EVAL_SEED:-42}"; MAXNEW="${MAXNEW:-2048}"
SHARD="${SHARD:-0}"; NSHARD="${NSHARD:-1}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "MODE=$MODE EVAL_SEED=$EVAL_SEED SHARD=$SHARD/$NSHARD"
echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | awk 'NR==1{print;exit}')
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then
    echo "ERROR: GPU unusable or <20GB (vram='${VRAM_MB}MB')"; exit 1; fi

if [ "$MODE" = "perprompt" ]; then
    JOBLIST="${JOBLIST:?set JOBLIST}"; ARM_LABEL="${ARM_LABEL:?set ARM_LABEL}"
    python "${DC}/scripts/eval_perprompt_batched.py" --mode perprompt \
        --joblist "$JOBLIST" --arm-label "$ARM_LABEL" \
        --seed "$EVAL_SEED" --max-new-tokens "$MAXNEW" --shard "$SHARD" --nshard "$NSHARD"
else
    PLAN="${PLAN:?set PLAN}"
    python "${DC}/scripts/eval_perprompt_batched.py" --mode transfer \
        --plan "$PLAN" --seed "$EVAL_SEED" --max-new-tokens "$MAXNEW" \
        --shard "$SHARD" --nshard "$NSHARD"
fi
echo "Done MODE=$MODE at $(date -u)"
