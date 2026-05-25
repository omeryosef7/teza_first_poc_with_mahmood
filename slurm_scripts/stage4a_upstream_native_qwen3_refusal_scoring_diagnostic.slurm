#!/bin/bash

#SBATCH --job-name=upstream_qwen3_refusal_diag
#SBATCH --output=logs/upstream_qwen3_refusal_diag_%j.out
#SBATCH --error=logs/upstream_qwen3_refusal_diag_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,n-301,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
UPSTREAM_DIR="$PROJECT_DIR/Chain_of_Thought_Hijacking/refusal_direction"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_PATH="${MODEL_PATH:-Qwen/Qwen3-14B}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction/upstream_native_qwen3_refusal_scoring_diagnostic}"
OUTPUT_JSON="${OUTPUT_JSON:-$OUTPUT_DIR/refusal_scoring_diagnostic.json}"
N_TRAIN="${N_TRAIN:-64}"
N_VAL="${N_VAL:-32}"
SAMPLE_COUNT="${SAMPLE_COUNT:-5}"
TOP_K="${TOP_K:-10}"

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
    "$OUTPUT_DIR" \
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

echo "=== Upstream-Native Qwen3 Refusal-Scoring Diagnostic Started ==="
date
hostname
pwd

python3 -m pipeline.diagnose_refusal_scoring \
  --model-path "$MODEL_PATH" \
  --output-json "$OUTPUT_JSON" \
  --n-train "$N_TRAIN" \
  --n-val "$N_VAL" \
  --sample-count "$SAMPLE_COUNT" \
  --top-k "$TOP_K"

echo "=== Upstream-Native Qwen3 Refusal-Scoring Diagnostic Finished ==="
date
