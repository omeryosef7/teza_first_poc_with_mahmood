#!/bin/bash

#SBATCH --job-name=poc_stage4c_qwen3_report
#SBATCH --output=logs/poc_stage4c_qwen3_report_%j.out
#SBATCH --error=logs/poc_stage4c_qwen3_report_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=24:00:00
#SBATCH --partition=studentkillable
#SBATCH --account=gpu-students

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
REFUSAL_DIRECTION_DIR="${REFUSAL_DIRECTION_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction}"
REFUSAL_DAMPENING_DIR="${REFUSAL_DAMPENING_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_dampening}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/report}"
ALLOW_DEBUG_INPUTS="${ALLOW_DEBUG_INPUTS:-false}"
SKIP_PLOTS="${SKIP_PLOTS:-false}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

mkdir -p logs outputs "$OUTPUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"

ARGS=(
    --model-name "$MODEL_NAME"
    --refusal-direction-dir "$REFUSAL_DIRECTION_DIR"
    --refusal-dampening-dir "$REFUSAL_DAMPENING_DIR"
    --output-dir "$OUTPUT_DIR"
)

if [ "$ALLOW_DEBUG_INPUTS" = "true" ]; then
    ARGS+=(--allow-debug-inputs)
fi

if [ "$SKIP_PLOTS" = "true" ]; then
    ARGS+=(--skip-plots)
fi

python -m poc_stage4.build_stage4_report "${ARGS[@]}"
