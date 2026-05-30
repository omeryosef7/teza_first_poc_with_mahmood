#!/bin/bash

#SBATCH --job-name=upstream_qwen3_5ex
#SBATCH --output=logs/upstream_qwen3_5ex_%j.out
#SBATCH --error=logs/upstream_qwen3_5ex_%j.err
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
UPSTREAM_DIR="$PROJECT_DIR/Chain_of_Thought_Hijacking/refusal_direction"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

OUTPUT_ROOT="${OUTPUT_ROOT:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction/upstream_native_qwen3_5examples}"
MODEL_PATH="${MODEL_PATH:-Qwen/Qwen3-14B}"
N_TRAIN="${N_TRAIN:-5}"
N_VAL="${N_VAL:-5}"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

cd "$UPSTREAM_DIR"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p \
    "$PROJECT_DIR/logs" \
    "$PROJECT_DIR/outputs" \
    "$OUTPUT_ROOT" \
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

REQUIRED_MODULES=(torch transformers jaxtyping einops matplotlib)
MISSING_PACKAGES=()

for module in "${REQUIRED_MODULES[@]}"; do
    if ! python3 - <<PY
import importlib.util
import sys
sys.exit(0 if importlib.util.find_spec("$module") is not None else 1)
PY
    then
        case "$module" in
            torch) MISSING_PACKAGES+=("torch==2.3.0") ;;
            transformers) MISSING_PACKAGES+=("transformers==4.44.2") ;;
            jaxtyping) MISSING_PACKAGES+=("jaxtyping==0.2.29") ;;
            einops) MISSING_PACKAGES+=("einops==0.8.0") ;;
            matplotlib) MISSING_PACKAGES+=("matplotlib==3.9.0") ;;
        esac
    fi
done

if [ "${#MISSING_PACKAGES[@]}" -gt 0 ]; then
    echo "Installing missing upstream pipeline dependencies: ${MISSING_PACKAGES[*]}"
    python3 -m pip install "${MISSING_PACKAGES[@]}"
fi

echo "=== Upstream-Native Qwen3 5-Example Smoke Started ==="
date
hostname
pwd

python3 -m pipeline.run_pipeline \
  --model_path "$MODEL_PATH" \
  --stop-after-selection \
  --output-root "$OUTPUT_ROOT" \
  --n-train "$N_TRAIN" \
  --n-val "$N_VAL"

echo "=== Upstream-Native Qwen3 5-Example Smoke Finished ==="
date
