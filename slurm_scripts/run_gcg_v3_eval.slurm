#!/bin/bash
#SBATCH --job-name=gcg_v3_eval
#SBATCH --output=logs/gcg_v3_eval_%j.out
#SBATCH --error=logs/gcg_v3_eval_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# Evaluate one or more optimized-arm suffixes on a v3 split (StrongREJECT held-out ASR).
# Pass a space-separated list of run-dir basenames via RUN_IDS and the SPLIT via env:
#   sbatch --export=ALL,SPLIT=test,SEED=42,RUN_IDS="phase9b_v3_arm07_refusal_down_L18_seed42 ..." run_gcg_v3_eval.slurm
# (RUN_IDS has spaces, not commas -> --export-safe.)  MANIFEST defaults to the v3 doublespeak file.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"
SPLIT="${SPLIT:-test}"; SEED="${SEED:-42}"
MANIFEST="${MANIFEST:-${DC}/data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak.jsonl}"
RUN_IDS="${RUN_IDS:?set RUN_IDS space-separated run-dir basenames}"
OUT_BASE="${PROJECT_DIR}/outputs/stage_gcg_full"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
nvidia-smi --query-gpu=name --format=csv,noheader
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then echo "ERROR: expected L40S, got '$GPU_NAME'"; exit 1; fi
if [ -z "${OPENAI_API_KEY:-}" ]; then echo "WARN: OPENAI_API_KEY unset -> StrongREJECT null"; fi

for rid in $RUN_IDS; do
    d="${OUT_BASE}/${rid}"
    if [ ! -f "${d}/FINAL_CANDIDATES.jsonl" ]; then echo "SKIP $rid (no FINAL_CANDIDATES)"; continue; fi
    echo ">>> EVAL $rid split=$SPLIT"
    python doublespeak_causality/26_eval_p9_gcg_heldout_asr.py \
        --run-dir "$d" --manifest "$MANIFEST" --split "$SPLIT" \
        --model-family llama --model-name-or-path meta-llama/Llama-3.1-8B-Instruct \
        --seed "$SEED" --max-new-tokens 2048 || echo "[eval] failed for $rid"
done
echo "Done eval at $(date -u)"
