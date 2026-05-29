#!/bin/bash

# Run the redacted batch exporter across all examples with a large generation cap.
# Submit with:
#   sbatch slurm_scripts/stage6_qwen3_14b_batch_redacted_99999.slurm
#   sbatch --export=ALL,MAX_NEW_TOKENS=12000 slurm_scripts/stage6_qwen3_14b_batch_redacted_99999.slurm
#   sbatch --export=ALL,OUT_DIR=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage6/custom_dir slurm_scripts/stage6_qwen3_14b_batch_redacted_99999.slurm
#   sbatch slurm_scripts/stage6_qwen3_14b_batch_redacted_99999.slurm 5
#
# Optional first positional arg: max_examples to process.

#SBATCH --job-name=poc_stage6_qwen3_batch_redacted_99999
#SBATCH --output=logs/poc_stage6_qwen3_batch_redacted_99999_%j.out
#SBATCH --error=logs/poc_stage6_qwen3_batch_redacted_99999_%j.err
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
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/outputs/stage6/all_traces_redacted_99999}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-99999}"
MAX_ATTEMPTS_FROM_ARG="${1:-}"

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

echo "=== Stage 6 Qwen3-14B batch redacted 99999 started ==="
date
hostname
pwd
python -V

echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUT_DIR=$OUT_DIR"
echo "MODEL_NAME=$MODEL_NAME"
echo "MAX_NEW_TOKENS=$MAX_NEW_TOKENS"
echo "MAX_ATTEMPTS=${MAX_ATTEMPTS_FROM_ARG:-<all>}"
echo "HF_HOME=$HF_HOME"
echo "HF_HUB_CACHE=$HF_HUB_CACHE"
echo "HUGGINGFACE_HUB_CACHE=$HUGGINGFACE_HUB_CACHE"
echo "TRANSFORMERS_CACHE=$TRANSFORMERS_CACHE"
echo "TORCH_HOME=$TORCH_HOME"
echo "TRITON_CACHE_DIR=$TRITON_CACHE_DIR"

ARGS=(
    --input-jsonl "$INPUT_JSONL"
    --out-dir "$OUT_DIR"
    --model "$MODEL_NAME"
    --extra-args "--max-new-tokens $MAX_NEW_TOKENS"
)

if [ -n "$MAX_ATTEMPTS_FROM_ARG" ]; then
    ARGS+=(--max-attempts "$MAX_ATTEMPTS_FROM_ARG")
fi

python -m poc_stage6.batch_redacted_export_all "${ARGS[@]}"

echo "=== Stage 6 Qwen3-14B batch redacted 99999 finished ==="
date
