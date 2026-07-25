#!/bin/bash

#SBATCH --job-name=phase7_steer
#SBATCH --output=logs/phase7_steer_%j.out
#SBATCH --error=logs/phase7_steer_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805

# Phase-7 (§11) activation-addition causal test: steer the attack-success direction during Qwen3-14B
# generation on dev-25 CLEAN harmful prompts, sweep alpha, write free generations for downstream
# StrongREJECT scoring. Reuses poc_stage4.phase7_steer_generate (which reuses load_qwen3_model +
# build_steering_hooks). Weights come from the project HF cache (Qwen3 already cached).
#
# Required env: DIRECTION_DIR, OUT. Optional: ALPHAS, N_TASKS, MAX_NEW_TOKENS.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="poc_stage2"
DIRECTION_DIR="${DIRECTION_DIR:?set DIRECTION_DIR=outputs/phase7_causal/success_dir__...}"
OUT="${OUT:?set OUT=outputs/phase7_causal/steer__.../generations.jsonl}"
ALPHAS="${ALPHAS:--3 -2 -1 -0.5 0 0.5 1 2 3}"
N_TASKS="${N_TASKS:-5}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-2048}"
# §C2 cross-model steering knobs (default = Qwen3, so existing runs are unchanged).
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$(dirname "$OUT")"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
# §31.3-A: non-Qwen3 weights are READ offline from the project cache (never re-downloaded).
if [ "$MODEL_FAMILY" != "qwen3" ]; then
    export HF_HUB_OFFLINE=1
    export TRANSFORMERS_OFFLINE=1
fi

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then echo "ERROR: expected L40S, got $GPU_NAME"; exit 1; fi

echo "[phase7] job=${SLURM_JOB_ID:-?} model=$MODEL_NAME($MODEL_FAMILY) dir=$DIRECTION_DIR alphas=$ALPHAS n_tasks=$N_TASKS date=$(date -u)"
# Optional pre-formatted attacked-context prompts (§11.4). Empty → clean instructions from MANIFEST.
PROMPTS_ARG=""
if [ -n "${PROMPTS_JSONL:-}" ]; then PROMPTS_ARG="--prompts-jsonl ${PROMPTS_JSONL}"; fi
MANIFEST_ARG=""
if [ -n "${MANIFEST:-}" ]; then MANIFEST_ARG="--manifest ${MANIFEST}"; fi

python -u -m poc_stage4.phase7_steer_generate \
    --direction-dir "$DIRECTION_DIR" \
    --alphas $ALPHAS \
    --n-tasks "$N_TASKS" \
    --max-new-tokens "$MAX_NEW_TOKENS" \
    --model-name "$MODEL_NAME" \
    --model-family "$MODEL_FAMILY" \
    --timing "${TIMING:-all}" \
    ${MANIFEST_ARG} \
    ${PROMPTS_ARG} \
    --out "$OUT"
echo "[phase7] done $(date -u)"
