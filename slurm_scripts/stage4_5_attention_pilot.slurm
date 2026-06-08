#!/bin/bash
# Stage 4.5 — Attention pilot: capture attention weights for pilot examples.
#
# DO NOT SUBMIT until the following preconditions are met:
#   1. docs/STAGE4_5_ATTENTION_METHOD_AUDIT.md is complete (Q3, Q7, Q10 answered)
#   2. Memory estimate is written to outputs/stage4_5/.../manifests/run_manifest.json
#   3. A 2–3 example smoke run has completed without OOM
#   4. span_alignment.json exists for all pilot examples
#
# See poc_stage4_5/capture_attention_pilot.py for implementation notes.

#SBATCH --job-name=stage4_5_attn_pilot
#SBATCH --output=logs/stage4_5_attn_pilot_%j.out
#SBATCH --error=logs/stage4_5_attn_pilot_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MODEL_NAME_OR_PATH="${MODEL_NAME_OR_PATH:-Qwen/Qwen3-14B}"
STAGE4_5_RUN_DIR="${STAGE4_5_RUN_DIR:-}"  # Must be set: path to the analysis run dir
REVIEW_DIR="${REVIEW_DIR:-$PROJECT_DIR/review}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs

export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

echo "=== Stage 4.5 Attention Pilot started ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
python -V
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

if [ -z "$STAGE4_5_RUN_DIR" ]; then
    echo "ERROR: STAGE4_5_RUN_DIR must be set to the stage4_5 analysis run directory." >&2
    exit 1
fi

# Verify preconditions
AUDIT_DOC="$PROJECT_DIR/docs/STAGE4_5_ATTENTION_METHOD_AUDIT.md"
if [ ! -f "$AUDIT_DOC" ]; then
    echo "ERROR: Attention methodology audit not found: $AUDIT_DOC" >&2
    exit 1
fi

MANIFEST="$STAGE4_5_RUN_DIR/manifests/run_manifest.json"
if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: Run manifest not found: $MANIFEST (required for memory estimate)" >&2
    exit 1
fi

echo "Precondition check passed."
echo "MODEL=$MODEL_NAME_OR_PATH"
echo "STAGE4_5_RUN_DIR=$STAGE4_5_RUN_DIR"

# NOTE: capture_attention_pilot.py currently exits 2 (blocked).
# Replace the following line with the actual implementation command
# after capture_attention_pilot.py is implemented:
python -m poc_stage4_5.capture_attention_pilot \
    --model-name-or-path "$MODEL_NAME_OR_PATH" \
    --run-dir "$STAGE4_5_RUN_DIR" \
    --review-dir "$REVIEW_DIR" \
    --output-dir "$STAGE4_5_RUN_DIR/attention_pilot"

echo "=== Stage 4.5 Attention Pilot finished ==="
date
