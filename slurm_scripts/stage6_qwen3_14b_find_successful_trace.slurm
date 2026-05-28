#!/bin/bash

# Submit with either:
#   sbatch slurm_scripts/stage6_qwen3_14b_find_successful_trace.slurm 5
# or:
#   MAX_ATTEMPTS=5 sbatch slurm_scripts/stage6_qwen3_14b_find_successful_trace.slurm
#
# The optional first positional argument is treated as MAX_ATTEMPTS for smoke tests.
# If MAX_ATTEMPTS is omitted or empty, the search scans all candidates.
# Default search settings now request 2 GPUs and a shorter generation cap.
# To escalate further on the cluster, you can override at submission time, e.g.:
#   sbatch --gpus=4 slurm_scripts/stage6_qwen3_14b_find_successful_trace.slurm

#SBATCH --job-name=poc_stage6_qwen3_find_success
#SBATCH --output=logs/poc_stage6_qwen3_find_success_%j.out
#SBATCH --error=logs/poc_stage6_qwen3_find_success_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,n-301,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage6/qwen_token_trace_search}"
OUTPUT_JSON="${OUTPUT_JSON:-$OUTPUT_DIR/search_summary.json}"
PROGRESS_JSONL="${PROGRESS_JSONL:-$OUTPUT_DIR/progress.jsonl}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
ENABLE_THINKING="${ENABLE_THINKING:-true}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-768}"
DO_SAMPLE="${DO_SAMPLE:-false}"
TEMPERATURE="${TEMPERATURE:-1.0}"
TOP_P="${TOP_P:-1.0}"
TOP_K="${TOP_K:-50}"
SEED="${SEED:-0}"
OVERWRITE="${OVERWRITE:-true}"
MAX_ATTEMPTS_FROM_ENV="${MAX_ATTEMPTS:-}"
MAX_ATTEMPTS_FROM_ARG="${1:-}"

if [ -n "$MAX_ATTEMPTS_FROM_ARG" ]; then
    MAX_ATTEMPTS="$MAX_ATTEMPTS_FROM_ARG"
else
    MAX_ATTEMPTS="$MAX_ATTEMPTS_FROM_ENV"
fi

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs outputs "$OUTPUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

if [ ! -f "$INPUT_JSONL" ]; then
    echo "ERROR: INPUT_JSONL does not exist: $INPUT_JSONL"
    exit 1
fi

echo "=== Stage 6 Qwen3-14B search-until-success started ==="
date
hostname
pwd
python -V
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-<unset>}"
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi -L
fi

echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUTPUT_JSON=$OUTPUT_JSON"
echo "PROGRESS_JSONL=$PROGRESS_JSONL"
echo "OUTPUT_DIR=$OUTPUT_DIR"
echo "MODEL_NAME=$MODEL_NAME"
echo "ENABLE_THINKING=$ENABLE_THINKING"
echo "MAX_NEW_TOKENS=$MAX_NEW_TOKENS"
echo "DO_SAMPLE=$DO_SAMPLE"
echo "TEMPERATURE=$TEMPERATURE"
echo "TOP_P=$TOP_P"
echo "TOP_K=$TOP_K"
echo "SEED=$SEED"
echo "MAX_ATTEMPTS=${MAX_ATTEMPTS:-<all>}"
echo "OVERWRITE=$OVERWRITE"
echo "HF_HOME=$HF_HOME"
echo "HF_HUB_CACHE=$HF_HUB_CACHE"
echo "TORCH_HOME=$TORCH_HOME"
echo "TRITON_CACHE_DIR=$TRITON_CACHE_DIR"

ARGS=(
    --input-jsonl "$INPUT_JSONL"
    --output-json "$OUTPUT_JSON"
    --progress-jsonl "$PROGRESS_JSONL"
    --model-name-or-path "$MODEL_NAME"
    --enable-thinking "$ENABLE_THINKING"
    --max-new-tokens "$MAX_NEW_TOKENS"
    --do-sample "$DO_SAMPLE"
    --temperature "$TEMPERATURE"
    --top-p "$TOP_P"
    --top-k "$TOP_K"
    --seed "$SEED"
    --search-until-success
)

if [ -n "${MAX_ATTEMPTS:-}" ]; then
    ARGS+=(--max-attempts "$MAX_ATTEMPTS")
fi

if [ "$OVERWRITE" = "true" ]; then
    ARGS+=(--overwrite)
fi

python -m poc_stage6.find_successful_qwen_trace "${ARGS[@]}"

echo "=== Stage 6 Qwen3-14B search-until-success finished ==="
date
