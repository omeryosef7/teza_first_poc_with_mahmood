#!/bin/bash
#
# Single-task resubmit for stage6 on gpu-sharifm partition.
# Use when a specific slice needs to run on dedicated nodes (no preemption).
#
# Submit with:
#   INPUT_JSONL=outputs/... OUT_DIR=outputs/stage6/... MAX_NEW_TOKENS=32768 \
#   [START_INDEX=165] [END_INDEX=220] \
#   sbatch slurm_scripts/stage6_single_sharifm.slurm

#SBATCH --job-name=poc_stage6_qwen3_single_sharifm
#SBATCH --output=logs/poc_stage6_qwen3_single_sharifm_%j.out
#SBATCH --error=logs/poc_stage6_qwen3_single_sharifm_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-501,n-601

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_1_11_strongreject.jsonl}"
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/outputs/stage6/all_traces_full_1_11}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32768}"
START_INDEX="${START_INDEX:-165}"
END_INDEX="${END_INDEX:-220}"
RUN_JUDGE="${RUN_JUDGE:-true}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="$HF_HUB_CACHE"
export TRANSFORMERS_CACHE="$HF_HUB_CACHE"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

echo "=== Stage 6 single job started (gpu-sharifm) ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""
echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUT_DIR=$OUT_DIR"
echo "MODEL_NAME=$MODEL_NAME"
echo "MAX_NEW_TOKENS=$MAX_NEW_TOKENS"
echo "Slice: examples[$START_INDEX:$END_INDEX]"

if [ ! -f "$INPUT_JSONL" ]; then
    echo "ERROR: INPUT_JSONL not found: $INPUT_JSONL"
    exit 1
fi

ARGS=(
    --input-jsonl "$INPUT_JSONL"
    --out-dir "$OUT_DIR"
    --model "$MODEL_NAME"
    --max-new-tokens "$MAX_NEW_TOKENS"
    --no-redact
    --start-index "$START_INDEX"
    --end-index "$END_INDEX"
)

if [ "$RUN_JUDGE" = "true" ]; then
    ARGS+=(--run-judge)
fi

echo ""
echo "=== Running batch exporter (slice $START_INDEX-$END_INDEX) ==="
python -m poc_stage6.batch_redacted_export_all "${ARGS[@]}"

echo ""
echo "=== Stage 6 single job finished ==="
date
