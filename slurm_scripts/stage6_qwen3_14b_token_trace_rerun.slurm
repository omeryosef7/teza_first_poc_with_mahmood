#!/bin/bash

# Submit with:
#   sbatch --export=ALL,EXAMPLE_ID=<EXAMPLE_ID> slurm_scripts/stage6_qwen3_14b_token_trace_rerun.slurm
# Or edit the EXAMPLE_ID default below before submitting.

#SBATCH --job-name=poc_stage6_qwen3_token_trace
#SBATCH --output=logs/poc_stage6_qwen3_token_trace_%j.out
#SBATCH --error=logs/poc_stage6_qwen3_token_trace_%j.err
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

# Set EXAMPLE_ID with `sbatch --export=ALL,EXAMPLE_ID=...` or edit this line before submitting.
EXAMPLE_ID="${EXAMPLE_ID:-REPLACE_ME}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl}"
OUTPUT_JSON="${OUTPUT_JSON:-$PROJECT_DIR/outputs/stage6/qwen_token_trace/qwen3_14b_success_trace_${EXAMPLE_ID}.json}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
ENABLE_THINKING="${ENABLE_THINKING:-true}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-2048}"
DO_SAMPLE="${DO_SAMPLE:-false}"
TEMPERATURE="${TEMPERATURE:-1.0}"
TOP_P="${TOP_P:-1.0}"
TOP_K="${TOP_K:-50}"
SEED="${SEED:-0}"
MODE="${MODE:-rerun}"
MANUAL_SUCCESS="${MANUAL_SUCCESS:-}"
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
mkdir -p "$(dirname "$OUTPUT_JSON")"

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

if [ "$EXAMPLE_ID" = "REPLACE_ME" ]; then
    echo "ERROR: EXAMPLE_ID is required. Submit with --export=ALL,EXAMPLE_ID=<EXAMPLE_ID> or edit the script."
    exit 1
fi

if [ ! -f "$INPUT_JSONL" ]; then
    echo "ERROR: INPUT_JSONL does not exist: $INPUT_JSONL"
    exit 1
fi

echo "=== Stage 6 Qwen3-14B token-trace rerun started ==="
date
hostname
pwd
python -V

echo "EXAMPLE_ID=$EXAMPLE_ID"
echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUTPUT_JSON=$OUTPUT_JSON"
echo "MODEL_NAME=$MODEL_NAME"
echo "ENABLE_THINKING=$ENABLE_THINKING"
echo "MAX_NEW_TOKENS=$MAX_NEW_TOKENS"
echo "DO_SAMPLE=$DO_SAMPLE"
echo "TEMPERATURE=$TEMPERATURE"
echo "TOP_P=$TOP_P"
echo "TOP_K=$TOP_K"
echo "SEED=$SEED"
echo "MODE=$MODE"
echo "HF_HOME=$HF_HOME"
echo "HF_HUB_CACHE=$HF_HUB_CACHE"
echo "HUGGINGFACE_HUB_CACHE=$HUGGINGFACE_HUB_CACHE"
echo "TRANSFORMERS_CACHE=$TRANSFORMERS_CACHE"

if [ -n "$MANUAL_SUCCESS" ]; then
    if [ "$OVERWRITE" = "true" ]; then
        python -m poc_stage6.export_qwen_token_trace \
            --input-jsonl "$INPUT_JSONL" \
            --example-id "$EXAMPLE_ID" \
            --mode "$MODE" \
            --model-name-or-path "$MODEL_NAME" \
            --enable-thinking "$ENABLE_THINKING" \
            --max-new-tokens "$MAX_NEW_TOKENS" \
            --do-sample "$DO_SAMPLE" \
            --temperature "$TEMPERATURE" \
            --top-p "$TOP_P" \
            --top-k "$TOP_K" \
            --seed "$SEED" \
            --output-json "$OUTPUT_JSON" \
            --manual-success "$MANUAL_SUCCESS" \
            --overwrite
    else
        python -m poc_stage6.export_qwen_token_trace \
            --input-jsonl "$INPUT_JSONL" \
            --example-id "$EXAMPLE_ID" \
            --mode "$MODE" \
            --model-name-or-path "$MODEL_NAME" \
            --enable-thinking "$ENABLE_THINKING" \
            --max-new-tokens "$MAX_NEW_TOKENS" \
            --do-sample "$DO_SAMPLE" \
            --temperature "$TEMPERATURE" \
            --top-p "$TOP_P" \
            --top-k "$TOP_K" \
            --seed "$SEED" \
            --output-json "$OUTPUT_JSON" \
            --manual-success "$MANUAL_SUCCESS"
    fi
else
    if [ "$OVERWRITE" = "true" ]; then
        python -m poc_stage6.export_qwen_token_trace \
            --input-jsonl "$INPUT_JSONL" \
            --example-id "$EXAMPLE_ID" \
            --mode "$MODE" \
            --model-name-or-path "$MODEL_NAME" \
            --enable-thinking "$ENABLE_THINKING" \
            --max-new-tokens "$MAX_NEW_TOKENS" \
            --do-sample "$DO_SAMPLE" \
            --temperature "$TEMPERATURE" \
            --top-p "$TOP_P" \
            --top-k "$TOP_K" \
            --seed "$SEED" \
            --output-json "$OUTPUT_JSON" \
            --overwrite
    else
        python -m poc_stage6.export_qwen_token_trace \
            --input-jsonl "$INPUT_JSONL" \
            --example-id "$EXAMPLE_ID" \
            --mode "$MODE" \
            --model-name-or-path "$MODEL_NAME" \
            --enable-thinking "$ENABLE_THINKING" \
            --max-new-tokens "$MAX_NEW_TOKENS" \
            --do-sample "$DO_SAMPLE" \
            --temperature "$TEMPERATURE" \
            --top-p "$TOP_P" \
            --top-k "$TOP_K" \
            --seed "$SEED" \
            --output-json "$OUTPUT_JSON"
    fi
fi

python -c 'print("summary")'

echo "=== Stage 6 Qwen3-14B token-trace rerun finished ==="
date
