#!/bin/bash
#SBATCH --job-name=pp_mechval
#SBATCH --output=logs/pp_mechval_%j.out
#SBATCH --error=logs/pp_mechval_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=6:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1

# =====================================================================================
# ASYMMETRY SPRINT §7.5 add-on 1 — per-prompt MECHANISTIC readout (§19.1).
# Does each per-prompt suffix actually lower the refusal projection ON ITS OWN PROMPT,
# and more than its matched-random counterpart? This is Gate E's "the intended internal
# target must move more than random" clause, asked of the per-prompt arms.
#
# Why this is worth running even though the per-prompt ASR contrast is underpowered
# (n=37 -> 9% power at the observed base rates): the projection is a CONTINUOUS, paired
# per-prompt measurement with far better SNR than binary ASR, so n=37 is adequate here.
#
#   --export=ALL,JL_MECH=<joblist>,JL_RAND=<joblist>,TAG=<label>
# Optional: NRAND (unoptimized random-token controls, default 0), OUTDIR.
# =====================================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"

JL_MECH="${JL_MECH:?set JL_MECH}"; JL_RAND="${JL_RAND:?set JL_RAND}"
TAG="${TAG:?set TAG}"; NRAND="${NRAND:-0}"
OUTDIR="${OUTDIR:-${DC}/outputs/asym_p75_mechval_${TAG}}"
MANIFEST="${DC}/data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak.jsonl"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$OUTDIR"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "TAG=$TAG NRAND=$NRAND OUT=$OUTDIR"
echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | awk 'NR==1{print;exit}')
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then
    echo "ERROR: GPU unusable or <20GB"; exit 1; fi

# --manifest <path>:test  -> the frozen test split the per-prompt arms attacked.
python -u "${DC}/scripts/asym_p1c_mech_validity_ext.py" \
    --manifest "${MANIFEST}:test" \
    --arm-perprompt "pp_mech=${JL_MECH}" \
    --arm-perprompt "pp_rand=${JL_RAND}" \
    --n-random-suffix "$NRAND" \
    --out-dir "$OUTDIR"

echo "Done TAG=$TAG at $(date -u)"
