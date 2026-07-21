#!/bin/bash
#SBATCH --job-name=phase4_hf
#SBATCH --output=logs/phase4_hf_%j.out
#SBATCH --error=logs/phase4_hf_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301

# Phase 4X (RESEARCH_PLAN_DISTILLING_JAILBREAKS.md sec 31): CoT-Hijacking with an
# OPEN-SOURCE LOCAL HF thinking model as the TARGET (on GPU). Attacker + judge stay
# Gemini API. Reuses poc_stage2/run_phase4_cot_baseline.py with --target-model hf:<id>.
#
# USER CONSTRAINT: local weights must NOT be saved to the project HF cache -> HF_HOME
# points at node-local $SLURM_TMPDIR (wiped when the job ends).
#
# Required env: HF_MODEL=<hf repo id>. Optional: LIMIT N_STREAMS N_ITERATIONS OUTPUT_DIR HF_TARGET_MAX_NEW_TOKENS
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-poc_stage2}"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs outputs/phase4_hf_local

# --- Node-local ephemeral HF cache (do NOT write to project .cache/huggingface) ---
HF_LOCAL_CACHE="${SLURM_TMPDIR:-/tmp/${SLURM_JOB_ID:-hf_local}}/hf"
mkdir -p "$HF_LOCAL_CACHE"
export HF_HOME="$HF_LOCAL_CACHE"
export HF_HUB_CACHE="$HF_LOCAL_CACHE/hub"
export TRANSFORMERS_CACHE="$HF_LOCAL_CACHE"
export HF_HUB_ENABLE_HF_TRANSFER=1
export LITELLM_LOCAL_MODEL_COST_MAP="True"   # attacker/judge litellm: avoid slow cost-map fetch
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

HF_MODEL="${HF_MODEL:?set HF_MODEL=<hf repo id, e.g. deepseek-ai/DeepSeek-R1-Distill-Llama-8B>}"
LIMIT="${LIMIT:-2}"
N_STREAMS="${N_STREAMS:-1}"
N_ITERATIONS="${N_ITERATIONS:-1}"
OUTPUT_DIR="${OUTPUT_DIR:-outputs/phase4_hf_local}"

echo "[phase4-hf] target=hf:$HF_MODEL limit=$LIMIT streams=$N_STREAMS iters=$N_ITERATIONS hf_cache=$HF_LOCAL_CACHE"
python -u -m poc_stage2.run_phase4_cot_baseline \
    --target-model "hf:${HF_MODEL}" \
    --manifest data/manifests/dev_25.csv \
    --limit "$LIMIT" \
    --n-streams "$N_STREAMS" \
    --n-iterations "$N_ITERATIONS" \
    --output-dir "$OUTPUT_DIR"

echo "[phase4-hf] project HF cache size (should be unchanged):"; du -sh "$PROJECT_DIR/.cache/huggingface" 2>/dev/null || true
echo "[phase4-hf] done"
