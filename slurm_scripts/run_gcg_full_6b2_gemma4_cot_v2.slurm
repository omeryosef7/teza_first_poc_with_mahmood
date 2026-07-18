#!/bin/bash

#SBATCH --job-name=gcg_6b2_gemma4_v2
#SBATCH --output=logs/gcg_6b2_gemma4_v2_%j.out
#SBATCH --error=logs/gcg_6b2_gemma4_v2_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Sprint 2 / Track 1 — Gemma4 CoT-prefix target "v2" diagnostic retry.
#
# 6B (outputs/stage_gcg_full/gcg_full_gemma4_6b_cot_target/) stalled at best
# task_loss ~26.96 and concluded the <|channel>thought / <channel|> marker
# tokens (ids 100/101) are "infeasible for teacher-forced GCG" -- but that
# conclusion was inferred purely from the aggregate loss curve; nothing in the
# codebase actually masks/restricts those token IDs, and they are ordinary
# vocab entries. This run repeats the 6B recipe with two changes to actually
# test that claim rather than re-assume it:
#   1. Uses a NEW manifest (advbench_gemma4_cot_manifest_v2.jsonl) that fixes a
#      cosmetic "model": "qwen3" leftover-field bug in the original 6B manifest
#      (never overridden by build_gemma4_cot_target_manifest.py; did not affect
#      which model actually ran, since model family is a separate --model-family
#      CLI arg, but corrupts provenance).
#   2. Passes --log-channel-token-positions so ITERATION_LOG.jsonl records
#      per-step task_loss AT the specific channel-token positions, not just the
#      aggregate. If that per-token loss tracks down with the rest of the
#      target, 6B was under-optimized, not infeasible. If it stays flat/near-
#      random while the rest of the target improves, the original claim is
#      actually verified (not just inferred).
#
# Deliberately hardcoded RUN_DIR / MANIFEST_PATH (unlike run_gcg_full_6c_qwen3_combined.slurm's
# parameterized-with-override pattern) so this script can never accidentally point at or
# collide with 6B's original run directory/manifest -- this is a fixed diagnostic run, not a
# general-purpose reusable template.
#
# First attempt: same seed as 6B (42), MORE STEPS (800 instead of 500), since 6B's own loss
# curve may not have been given enough budget. Per the sprint decision rule: if the
# channel-token-specific loss is still flat/stuck near-random after 800 steps regardless of
# improvement elsewhere in the target, try a different seed next (not automated here).

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="poc_stage2"
RUN_DIR="${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_gemma4_6b2_cot_target_v2"
MANIFEST_PATH="${PROJECT_DIR}/outputs/stage_gcg_full/advbench_gemma4_cot_manifest_v2.jsonl"
N_STEPS=800
BATCH_SIZE=64
SUFFIX_LEN=20
SEED=42

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
echo "  Sprint 2 Track 1 — Gemma4 CoT-Prefix v2 Diagnostic"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_ID:          ${RUN_ID}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "MANIFEST:        ${MANIFEST_PATH}"
echo "N_STEPS:         ${N_STEPS}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ ! -f "${MANIFEST_PATH}" ]; then
    echo "ERROR: Required manifest not found: ${MANIFEST_PATH}"
    echo "Run first: python3 -m poc_stage_gcg_early.build_gemma4_cot_target_manifest --input outputs/stage_gcg_full/advbench_manifest_v1.jsonl --output ${MANIFEST_PATH}"
    exit 1
fi

echo "Sample target: $(head -1 "${MANIFEST_PATH}" | python3 -c "import json,sys; r=json.load(sys.stdin); print(repr(r['safe_target_prefix'][:120]))")"
echo "Manifest model field (should be gemma4): $(head -1 "${MANIFEST_PATH}" | python3 -c "import json,sys; print(json.load(sys.stdin)['model'])")"

if [ -f "${RUN_DIR}/checkpoint.pt" ]; then
    echo ">>> Resuming from checkpoint in ${RUN_DIR}"
else
    echo ">>> Starting fresh"
fi

python -m poc_stage_gcg_early.run_optimization \
    --run-id "${RUN_ID}" \
    --model-family gemma4 \
    --model-name-or-path google/gemma-4-E4B-it \
    --manifest "${MANIFEST_PATH}" \
    --output-dir "${RUN_DIR}" \
    --suffix-length "${SUFFIX_LEN}" \
    --n-steps "${N_STEPS}" \
    --batch-size "${BATCH_SIZE}" \
    --topk 256 \
    --seed "${SEED}" \
    --lambda-repr 0.0 \
    --lambda-kl 0.0 \
    --selection-mode weighted \
    --checkpoint-every 10 \
    --snapshot-every 50 \
    --split train \
    --log-channel-token-positions \
    --no-filter-cand

echo ""
echo "--- Running audit ---"
python -m poc_stage_gcg_early.audit_run --run-dir "${RUN_DIR}" || true

echo ""
echo "--- Running validation ---"
python -m poc_stage_gcg_early.validate_run_outputs --run-dir "${RUN_DIR}"

echo ""
echo "--- Running pareto/results-summary analysis (NOT auto-invoked elsewhere in this pipeline -- a gap discovered in Phase 8) ---"
python -m poc_stage_gcg_early.analyze_pareto_frontier --run-dir "${RUN_DIR}"

echo ""
echo "========================================================"
echo "  Sprint 2 Track 1 (Gemma4 CoT-prefix v2) COMPLETE"
echo "  Run: ${RUN_ID}"
echo "  $(date -u)"
echo "========================================================"
