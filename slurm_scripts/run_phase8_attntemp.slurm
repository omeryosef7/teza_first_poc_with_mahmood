#!/bin/bash

#SBATCH --job-name=phase8_attntemp
#SBATCH --output=logs/phase8_attntemp_%j.out
#SBATCH --error=logs/phase8_attntemp_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805

# §C1 (Claude extension) CAUSAL attention-temperature intervention on Qwen3-14B. Rescales
# self_attn.scaling by 1/tau (pre-softmax attention temperature) during generation and writes free
# generations for downstream StrongREJECT scoring + the ASR-vs-tau curve. Reuses
# poc_stage4.phase8_attn_temp_generate (which imports the phase7 generation plumbing). Weights come from
# the project HF cache (Qwen3 already cached). Mirror of run_phase7_steer.slurm.
#
# Required env: OUT. Optional: TAUS, ATTN_LAYERS, N_TASKS, MAX_NEW_TOKENS, MANIFEST, PROMPTS_JSONL.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="poc_stage2"
OUT="${OUT:?set OUT=outputs/phase8_attn_causal/.../generations.jsonl}"
TAUS="${TAUS:-0.5 0.7 1.0 1.4 2.0}"
ATTN_LAYERS="${ATTN_LAYERS:-targeted}"
N_TASKS="${N_TASKS:-25}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-2048}"

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

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then echo "ERROR: expected L40S, got $GPU_NAME"; exit 1; fi

echo "[phase8] job=${SLURM_JOB_ID:-?} taus=$TAUS layers=$ATTN_LAYERS n_tasks=$N_TASKS out=$OUT date=$(date -u)"
# Optional pre-formatted attacked-context prompts (NECESSITY arm). Empty → clean prompts (SUFFICIENCY).
PROMPTS_ARG=""
if [ -n "${PROMPTS_JSONL:-}" ]; then PROMPTS_ARG="--prompts-jsonl ${PROMPTS_JSONL}"; fi
MANIFEST_ARG=""
if [ -n "${MANIFEST:-}" ]; then MANIFEST_ARG="--manifest ${MANIFEST}"; fi

python -u -m poc_stage4.phase8_attn_temp_generate \
    --taus $TAUS \
    --attn-layers "$ATTN_LAYERS" \
    --n-tasks "$N_TASKS" \
    --max-new-tokens "$MAX_NEW_TOKENS" \
    ${MANIFEST_ARG} \
    ${PROMPTS_ARG} \
    --out "$OUT"
echo "[phase8] done $(date -u)"
