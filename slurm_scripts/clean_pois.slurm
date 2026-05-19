#!/bin/bash

#SBATCH --job-name=poc_stage2_hijacking
#SBATCH --output=logs/poc_stage2_hijacking_%j.out
#SBATCH --error=logs/poc_stage2_hijacking_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --partition=studentkillable
#SBATCH --account=gpu-students
#SBATCH --gres=gpu:1                # Request 1 GPU

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"

cd "$PROJECT_DIR"

# Initialize conda for the batch shell.
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh

# Activate your virtual environment
conda activate poc_stage2

# Load API keys and other local environment variables when present.
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs outputs "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,triton}

# Tell Jupyter and IPython to use that folder instead of your home dir
export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"

python -m poc_stage2.collect_hijacking_results \
    --target-model gpt-o4-mini \
    --start-example 1 \
    --end-example 4 \
    --output-dir outputs
