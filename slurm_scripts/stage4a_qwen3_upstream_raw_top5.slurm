#!/bin/bash

#SBATCH --job-name=poc_stage4a_qwen3_upstream_raw_top5
#SBATCH --output=logs/poc_stage4a_qwen3_upstream_raw_top5_%j.out
#SBATCH --error=logs/poc_stage4a_qwen3_upstream_raw_top5_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction/upstream_direction_validation_raw_top5}"
NO_PROGRESS="${NO_PROGRESS:-true}"

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

echo "=== Stage 4A Upstream Fallback Raw Top-5 Smoke Test Started ==="
date
hostname
pwd

ARGS=(
  --output-dir "$OUTPUT_DIR"
  --model-name "Qwen/Qwen3-14B"
  --enable-thinking "false"
  --batch-size "1"
  --num-harmful "64"
  --num-harmless "64"
  --positions=-1,-2,-3,-4
  --direction-normalization "raw"
  --top-k-projection "5"
  --num-harmful-val "32"
  --num-harmless-val "32"
  --validation-seed "42"
  --kl-threshold "0.1"
  --induce-refusal-threshold "0.0"
  --prune-layer-percentage "0.2"
)

if [ "$NO_PROGRESS" = "true" ]; then
  ARGS+=(--no-progress)
fi

python3 -m poc_stage4.validate_upstream_direction "${ARGS[@]}"

echo "=== Stage 4A Upstream Fallback Raw Top-5 Smoke Test Finished ==="
date
