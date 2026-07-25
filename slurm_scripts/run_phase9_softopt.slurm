#!/bin/bash
#SBATCH --job-name=phase9_softopt
#SBATCH --output=logs/phase9_softopt_%j.out
#SBATCH --error=logs/phase9_softopt_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805

# §Phase 8+9 soft-optimization Gate-4 test: optimize a soft prefix to MAXIMIZE the success-direction
# projection, then free-generate for StrongREJECT. Reuses poc_stage4.phase9_soft_opt (which reuses
# load_qwen3_model + the fitted direction). Qwen3 already cached.
# Required env: OUT. Optional: DIRECTION_DIR, N_TASKS, K_SOFT, STEPS, LR, MAX_NEW_TOKENS.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
OUT="${OUT:?set OUT=outputs/phase9_softopt/.../generations.jsonl}"
DIRECTION_DIR="${DIRECTION_DIR:-outputs/phase7_causal/success_dir__prefill_last__L16}"
N_TASKS="${N_TASKS:-25}"; K_SOFT="${K_SOFT:-8}"; STEPS="${STEPS:-100}"; LR="${LR:-0.05}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-2048}"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$(dirname "$OUT")"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then echo "ERROR: expected L40S, got $GPU_NAME"; exit 1; fi
echo "[phase9] job=${SLURM_JOB_ID:-?} dir=$DIRECTION_DIR n=$N_TASKS K=$K_SOFT steps=$STEPS lr=$LR date=$(date -u)"
python -u -m poc_stage4.phase9_soft_opt \
    --direction-dir "$DIRECTION_DIR" --n-tasks "$N_TASKS" --k-soft "$K_SOFT" \
    --steps "$STEPS" --lr "$LR" --max-new-tokens "$MAX_NEW_TOKENS" --out "$OUT"
echo "[phase9] done $(date -u)"
