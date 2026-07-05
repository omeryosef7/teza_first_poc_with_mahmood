#!/bin/bash

#SBATCH --job-name=ae_replay_qwen3
#SBATCH --output=logs/ae_replay_qwen3_%A_%a.out
#SBATCH --error=logs/ae_replay_qwen3_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805
#SBATCH --array=0-43%4

# Stage AE — Qwen3-14B hidden-state replay. Arrays over completed generation
# shard files under $RUN_DIR/generation/qwen3/shards/*.jsonl (sorted, so the
# array index -> shard file mapping is stable across resubmissions as long as
# no shard files are deleted). 4h wall time is a conservative starting point
# to be tuned after the smoke test (32k-token full-sequence forward passes are
# the dominant cost per the plan's risk list).
#
# Based directly on slurm_scripts/stage4_8_cond_g_goals4_10_qwen3_l40s.slurm.
#
# Requires RUN_DIR passed via --export, e.g.:
#   sbatch --export=ALL,RUN_DIR="$RUN_DIR" slurm_scripts/submit_qwen_hidden_replay.sh

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

if [ -z "${RUN_DIR:-}" ]; then
    echo "ERROR: RUN_DIR must be set via --export=ALL,RUN_DIR=..."
    exit 1
fi

cd "$PROJECT_DIR"

SHARDS_DIR="$RUN_DIR/generation/qwen3/shards"
mapfile -t SHARD_FILES < <(find "$SHARDS_DIR" -maxdepth 1 -name '*.jsonl' | sort)
TASK_ID=$SLURM_ARRAY_TASK_ID
SHARD_PATH="${SHARD_FILES[$TASK_ID]:-}"

if [ -z "$SHARD_PATH" ]; then
    echo "No shard file at array index $TASK_ID (only ${#SHARD_FILES[@]} shards found in $SHARDS_DIR). Exiting cleanly."
    exit 0
fi

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$RUN_DIR/qwen/hidden_states" \
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

echo "=== Stage AE Hidden-State Replay — Qwen3 Array Task ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}  SLURM_ARRAY_TASK_ID=${TASK_ID}"
echo "SHARD_PATH=$SHARD_PATH"
echo "RUN_DIR=$RUN_DIR"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

GPU_TYPE=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
if echo "$GPU_TYPE" | grep -qi "A5000\|A4000\|A2000"; then
    echo "ERROR: GPU is $GPU_TYPE — not L40S. Aborting to prevent CPU offloading."
    exit 1
fi
echo "GPU check passed: $GPU_TYPE"

python -m poc_stage_ae.replay_hidden_states \
    --model qwen3 \
    --generation-shard "$SHARD_PATH" \
    --output-dir "$RUN_DIR/qwen"

echo ""
echo "=== Task $TASK_ID ($SHARD_PATH) complete ==="
date
