#!/bin/bash

#SBATCH --job-name=ae_gen_gemma4
#SBATCH --output=logs/ae_gen_gemma4_%A_%a.out
#SBATCH --error=logs/ae_gen_gemma4_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=23:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805
#SBATCH --array=0-43%3

# Stage AE — Gemma4-E4B-it generation (conditions A/D/E/G x goal_index 0-10).
# Array indexing: task_id = goal_index*4 + cond_idx, cond_idx in {0:A, 1:D, 2:E, 3:G}.
# 44 tasks total, throttled to 3 concurrent (per proven precedent for Gemma4 L40S jobs).
#
# Based directly on slurm_scripts/stage4_8_cond_g_goals4_10_gemma4.slurm
# (account/partition/GPU-guard/env-setup identical).
#
# Requires RUN_DIR and MANIFEST_PATH passed via --export, e.g.:
#   RUN_DIR=outputs/stage_ae_early_token_expansion/full_<TS>
#   sbatch --export=ALL,RUN_DIR="$RUN_DIR",MANIFEST_PATH="$RUN_DIR/manifests/gemma4_ae_manifest.jsonl" \
#     slurm_scripts/submit_gemma_ae.sh

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

if [ -z "${RUN_DIR:-}" ] || [ -z "${MANIFEST_PATH:-}" ]; then
    echo "ERROR: RUN_DIR and MANIFEST_PATH must be set via --export=ALL,RUN_DIR=...,MANIFEST_PATH=..."
    exit 1
fi

_CONDITIONS=(A D E G)
TASK_ID=$SLURM_ARRAY_TASK_ID
GOAL_INDEX=$(( TASK_ID / 4 ))
COND_IDX=$(( TASK_ID % 4 ))
CONDITION=${_CONDITIONS[$COND_IDX]}

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$RUN_DIR/generation/gemma4" \
    "$RUNTIME_DIR"/{config,data,runtime,ipython} \
    "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

echo "=== Stage AE Generation — Gemma4 Array Task ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}  SLURM_ARRAY_TASK_ID=${TASK_ID}"
echo "GOAL_INDEX=$GOAL_INDEX  CONDITION=$CONDITION"
echo "RUN_DIR=$RUN_DIR"
echo "MANIFEST_PATH=$MANIFEST_PATH"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

GPU_TYPE=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
if echo "$GPU_TYPE" | grep -qi "A5000\|A4000\|A2000"; then
    echo "ERROR: GPU is $GPU_TYPE — not L40S. Aborting to prevent CPU offloading."
    exit 1
fi
echo "GPU check passed: $GPU_TYPE"

python -m poc_stage_ae.run_ae_generation \
    --model gemma4 \
    --manifest "$MANIFEST_PATH" \
    --goal-index "$GOAL_INDEX" \
    --condition "$CONDITION" \
    --output-dir "$RUN_DIR/generation/gemma4"

echo ""
echo "=== Task $TASK_ID (goal=$GOAL_INDEX cond=$CONDITION) complete ==="
date
