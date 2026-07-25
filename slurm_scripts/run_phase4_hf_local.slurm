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
#SBATCH --exclude=n-804,n-602,n-301,n-801

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

# --- HF cache policy ---
# Default (§31.3): NEW open-model weights go to node-local ephemeral storage, never the project cache.
# Exception: HF_CACHE_MODE=project reuses the project cache for models ALREADY cached there (e.g.
# Qwen/Qwen3-14B, the group's main model) — avoids a wasteful multi-GB re-download + NFS thrash.
if [ "${HF_CACHE_MODE:-node_local}" = "project" ]; then
    HF_LOCAL_CACHE="$PROJECT_DIR/.cache/huggingface"
    # §31.3 guard: project-cache mode is ONLY for models already cached (e.g. Qwen3-14B). Verify the
    # snapshot exists so a typo can't silently download a NEW open-model into the project cache.
    _HF_SNAP="$PROJECT_DIR/.cache/huggingface/hub/models--${HF_MODEL//\//--}"
    if [ ! -d "$_HF_SNAP" ]; then
        echo "[phase4-hf] FATAL: HF_CACHE_MODE=project but $HF_MODEL is NOT in the project cache ($_HF_SNAP). Use node_local (default) for new models (§31.3 no-cache)." >&2
        exit 1
    fi
    echo "[phase4-hf] HF_CACHE_MODE=project → reusing project cache (verified $HF_MODEL is present)"
else
    HF_LOCAL_CACHE="${SLURM_TMPDIR:-/tmp/${SLURM_JOB_ID:-hf_local}}/hf"
fi
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
MANIFEST="${MANIFEST:-data/manifests/dev_25.csv}"

echo "[phase4-hf] target=hf:$HF_MODEL manifest=$MANIFEST limit=$LIMIT streams=$N_STREAMS iters=$N_ITERATIONS hf_cache=$HF_LOCAL_CACHE"
python -u -m poc_stage2.run_phase4_cot_baseline \
    --target-model "hf:${HF_MODEL}" \
    --manifest "$MANIFEST" \
    --limit "$LIMIT" \
    --n-streams "$N_STREAMS" \
    --n-iterations "$N_ITERATIONS" \
    --output-dir "$OUTPUT_DIR"

echo "[phase4-hf] project HF cache size (should be unchanged):"; du -sh "$PROJECT_DIR/.cache/huggingface" 2>/dev/null || true
echo "[phase4-hf] done"
