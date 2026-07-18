#!/bin/bash
#SBATCH --job-name=gcg_userfix
#SBATCH --output=logs/gcg_userfix_%j.out
#SBATCH --error=logs/gcg_userfix_%j.err
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

# ============================================================================
# Generic FIXED-optimizer (suffix_placement=user + space-prefixed init) re-run.
# All experiment params via env; writes to a v2 dir. v1 never touched.
# See docs/GCG_BUGFIX_RERUN_PLAN.md.  Required env: RUN_DIR, MANIFEST_PATH.
# ============================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

RUN_DIR="${RUN_DIR:?set RUN_DIR}"
MANIFEST_PATH="${MANIFEST_PATH:?set MANIFEST_PATH}"
MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
SUFFIX_LEN="${SUFFIX_LEN:-20}"
N_STEPS="${N_STEPS:-500}"
BATCH_SIZE="${BATCH_SIZE:-64}"
SEED="${SEED:-42}"
LAMBDA_REPR="${LAMBDA_REPR:-0.0}"
LAMBDA_KL="${LAMBDA_KL:-0.0}"
LAMBDA_REFUSAL_DIR="${LAMBDA_REFUSAL_DIR:-0.0}"
REFUSAL_DIR_LAYER="${REFUSAL_DIR_LAYER:-25}"
REFUSAL_DIR_PATH="${REFUSAL_DIR_PATH:-}"
ENABLE_THINKING="${ENABLE_THINKING:-true}"
SELECTION_MODE="${SELECTION_MODE:-weighted}"
RUN_ID=$(basename "${RUN_DIR}")

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "${RUN_DIR}"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "==== FIXED re-run: ${RUN_ID} (suffix_placement=user) ===="
echo "SUFFIX_PLACEMENT: user (FIXED)"
echo "JOB=${SLURM_JOB_ID} NODE=${SLURM_NODELIST} RUN_DIR=${RUN_DIR}"
echo "model=${MODEL_FAMILY}/${MODEL_NAME} manifest=${MANIFEST_PATH} seed=${SEED} think=${ENABLE_THINKING}"
echo "lam_repr=${LAMBDA_REPR} lam_rd=${LAMBDA_REFUSAL_DIR} rd_layer=${REFUSAL_DIR_LAYER} rd_path=${REFUSAL_DIR_PATH}"
echo "git=$(git rev-parse HEAD) date=$(date -u)"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
[[ "$GPU_NAME" == *"L40S"* ]] || { echo "ERROR: not L40S ($GPU_NAME)"; exit 1; }
[ -f "${MANIFEST_PATH}" ] || { echo "ERROR: manifest missing ${MANIFEST_PATH}"; exit 1; }

CMD=(python -m poc_stage_gcg_early.run_optimization
  --run-id "${RUN_ID}" --model-family "${MODEL_FAMILY}" --model-name-or-path "${MODEL_NAME}"
  --manifest "${MANIFEST_PATH}" --output-dir "${RUN_DIR}"
  --suffix-length "${SUFFIX_LEN}" --n-steps "${N_STEPS}" --batch-size "${BATCH_SIZE}" --topk 256
  --seed "${SEED}" --lambda-repr "${LAMBDA_REPR}" --lambda-kl "${LAMBDA_KL}"
  --selection-mode "${SELECTION_MODE}" --suffix-placement user
  --checkpoint-every 10 --snapshot-every 50 --split train --no-filter-cand)
if [ "$(echo "${LAMBDA_REFUSAL_DIR} > 0" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
  CMD+=(--lambda-refusal-dir "${LAMBDA_REFUSAL_DIR}" --refusal-dir-layer "${REFUSAL_DIR_LAYER}" --refusal-dir-path "${REFUSAL_DIR_PATH}")
fi
[ "${ENABLE_THINKING}" = "false" ] && CMD+=(--no-thinking)

"${CMD[@]}"

echo "--- verify fixed path recorded ---"
python3 -c "import json;c=json.load(open('${RUN_DIR}/CONFIG.json'));v=c['gcg'].get('suffix_placement');assert v=='user',f'BUG {v}';print('OK suffix_placement=',v)"
python -m poc_stage_gcg_early.audit_run --run-dir "${RUN_DIR}" || true
echo "==== ${RUN_ID} FIXED OPT COMPLETE $(date -u) ===="
