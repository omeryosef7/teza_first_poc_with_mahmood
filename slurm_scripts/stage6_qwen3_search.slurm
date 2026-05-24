#!/bin/bash

# Submit with:
#   sbatch slurm_scripts/stage6_qwen3_search.slurm

#SBATCH --job-name=poc_stage6_qwen3_search
#SBATCH --output=logs/poc_stage6_qwen3_search_%j.out
#SBATCH --error=logs/poc_stage6_qwen3_search_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,n-301,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl}"
OUTPUT_JSON="${OUTPUT_JSON:-$PROJECT_DIR/outputs/stage6/qwen_token_trace/qwen3_14b_first_success_trace.json}"
PROGRESS_JSONL="${PROGRESS_JSONL:-$PROJECT_DIR/outputs/stage6/qwen_token_trace/search_progress.jsonl}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-5}"
OVERWRITE="${OVERWRITE:-true}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs outputs "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
mkdir -p "$(dirname "$OUTPUT_JSON")" "$(dirname "$PROGRESS_JSONL")"

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

echo "=== Stage 6 Qwen3 search-until-success started ==="
date
hostname
pwd
python -V

echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUTPUT_JSON=$OUTPUT_JSON"
echo "PROGRESS_JSONL=$PROGRESS_JSONL"
echo "MAX_ATTEMPTS=$MAX_ATTEMPTS"
echo "OVERWRITE=$OVERWRITE"

ARGS=(
    --input-jsonl "$INPUT_JSONL"
    --output-json "$OUTPUT_JSON"
    --progress-jsonl "$PROGRESS_JSONL"
    --search-until-success
    --max-attempts "$MAX_ATTEMPTS"
)

if [ "$OVERWRITE" = "true" ]; then
    ARGS+=(--overwrite)
fi

python -m poc_stage6.export_qwen_token_trace "${ARGS[@]}"

echo "=== Stage 6 Qwen3 search-until-success finished ==="
date
