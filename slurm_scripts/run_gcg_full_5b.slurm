#!/bin/bash

#SBATCH --job-name=gcg_5b_cot_repr
#SBATCH --output=logs/gcg_5b_cot_repr_%j.out
#SBATCH --error=logs/gcg_5b_cot_repr_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# Experiment 5B — GCG with repr_loss at CoT position 0.
#
# Hypothesis: repr_loss applied at target_slice.start (= first target token =
# CoT position 0 in teacher-forcing) pushes the adversarial suffix to produce
# a CoT-start hidden state indistinguishable from the neutral-suffix model.
#
# If this works, the detector (which fires at CoT position 0) would have a
# harder time separating adversarial from neutral suffixes.
#
# Key parameters vs 5A:
#   --lambda-repr 1.0     (vs 0.0 in 5A)
#   --repr-at-cot-pos     (target_slice.start instead of last-3 suffix tokens)
#   --reference-cache-dir reference_cache_cot_pos  (must be pre-built)
#
# Prerequisite: run build_gcg_reference_cache_cot_pos.slurm first.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_qwen3_5b_cot_repr}"
MANIFEST_PATH="${MANIFEST_PATH:-${PROJECT_DIR}/outputs/stage_gcg_full/advbench_cot_target_manifest.jsonl}"
REFERENCE_CACHE_DIR="${REFERENCE_CACHE_DIR:-${PROJECT_DIR}/outputs/stage_gcg_full/reference_cache_cot_pos}"
N_STEPS="${N_STEPS:-500}"
BATCH_SIZE="${BATCH_SIZE:-64}"
SUFFIX_LEN="${SUFFIX_LEN:-20}"
SEED="${SEED:-42}"

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

echo "========================================================"
echo "  Experiment 5B — GCG CoT-Repr (repr_loss at CoT pos 0)"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "MANIFEST:        ${MANIFEST_PATH}"
echo "REF_CACHE:       ${REFERENCE_CACHE_DIR}"
echo "N_STEPS:         ${N_STEPS}"
echo "SUFFIX_LEN:      ${SUFFIX_LEN}"
echo "BATCH_SIZE:      ${BATCH_SIZE}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ ! -f "${MANIFEST_PATH}" ]; then
    echo "ERROR: CoT-target manifest not found: ${MANIFEST_PATH}"
    exit 1
fi

if [ ! -f "${REFERENCE_CACHE_DIR}/REFERENCE_CACHE_MANIFEST.json" ]; then
    echo "ERROR: CoT-pos reference cache not found: ${REFERENCE_CACHE_DIR}/REFERENCE_CACHE_MANIFEST.json"
    echo "Run first: sbatch slurm_scripts/build_gcg_reference_cache_cot_pos.slurm"
    exit 1
fi

echo "Manifest rows: $(wc -l < "${MANIFEST_PATH}")"
echo "Sample target: $(head -1 "${MANIFEST_PATH}" | python3 -c "import json,sys; r=json.load(sys.stdin); print(repr(r['safe_target_prefix'][:80]))")"

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint in ${RUN_DIR}"
else
    echo ">>> Starting fresh"
fi

python -m poc_stage_gcg_early.run_optimization \
    --run-id "${RUN_ID}" \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
    --manifest "${MANIFEST_PATH}" \
    --output-dir "${RUN_DIR}" \
    --suffix-length "${SUFFIX_LEN}" \
    --n-steps "${N_STEPS}" \
    --batch-size "${BATCH_SIZE}" \
    --topk 256 \
    --seed "${SEED}" \
    --lambda-repr 1.0 \
    --lambda-kl 0.0 \
    --repr-at-cot-pos \
    --repr-layers 0,5,10,15,20,25,30,35 \
    --reference-cache-dir "${REFERENCE_CACHE_DIR}" \
    --selection-mode weighted \
    --checkpoint-every 10 \
    --snapshot-every 50 \
    --split train \
    --no-filter-cand

echo ""
echo "--- Running audit ---"
python -m poc_stage_gcg_early.audit_run --run-dir "${RUN_DIR}" || true

echo ""
echo "--- Running validation ---"
python -m poc_stage_gcg_early.validate_run_outputs --run-dir "${RUN_DIR}"

echo ""
echo "========================================================"
echo "  Experiment 5B (CoT-Repr) COMPLETE"
echo "  Run: ${RUN_ID}"
echo "  $(date -u)"
echo "========================================================"
