#!/bin/bash

#SBATCH --job-name=poc_stage5_qwen3_max100
#SBATCH --output=logs/poc_stage5_qwen3_max100_%j.out
#SBATCH --error=logs/poc_stage5_qwen3_max100_%j.err
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

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl}"
DIRECTION_PATH="${DIRECTION_PATH:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction/direction.pt}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage5/qwen3-14b/max100_final}"
RUN_NAME="${RUN_NAME:-stage5_qwen3_max100_final}"
MAX_EXAMPLES="${MAX_EXAMPLES:-100}"
MAX_LENGTH="${MAX_LENGTH:-256}"
LAYERS="${LAYERS:--1}"
TOKEN_REGIONS="${TOKEN_REGIONS:-final_token,last_8,last_32}"
DEVICE="${DEVICE:-auto}"
DTYPE="${DTYPE:-bfloat16}"
CONDITION="${CONDITION:-cot_hijack}"
OVERWRITE="${OVERWRITE:-true}"
NO_PROGRESS="${NO_PROGRESS:-false}"

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

OUTPUT_JSONL="$OUTPUT_DIR/per_example_layer_region_projections.jsonl"
SUMMARY_JSON="$OUTPUT_DIR/projection_summary.json"
ERROR_JSONL="$OUTPUT_DIR/projection_errors.jsonl"
AGGREGATE_JSON="$OUTPUT_DIR/projection_aggregate_summary.json"
AGGREGATE_CSV="$OUTPUT_DIR/projection_aggregate_summary.csv"
EXPECTED_ROWS=300
export OUTPUT_JSONL SUMMARY_JSON ERROR_JSONL AGGREGATE_JSON AGGREGATE_CSV EXPECTED_ROWS

echo "=== Stage 5 Qwen3 max-100 final analysis started ==="
date
hostname
pwd
python -V

echo "MODEL_NAME=$MODEL_NAME"
echo "INPUT_JSONL=$INPUT_JSONL"
echo "DIRECTION_PATH=$DIRECTION_PATH"
echo "OUTPUT_DIR=$OUTPUT_DIR"
echo "OUTPUT_JSONL=$OUTPUT_JSONL"
echo "SUMMARY_JSON=$SUMMARY_JSON"
echo "ERROR_JSONL=$ERROR_JSONL"
echo "AGGREGATE_JSON=$AGGREGATE_JSON"
echo "AGGREGATE_CSV=$AGGREGATE_CSV"
echo "RUN_NAME=$RUN_NAME"
echo "MAX_EXAMPLES=$MAX_EXAMPLES"
echo "MAX_LENGTH=$MAX_LENGTH"
echo "LAYERS=$LAYERS"
echo "TOKEN_REGIONS=$TOKEN_REGIONS"
echo "DEVICE=$DEVICE"
echo "DTYPE=$DTYPE"
echo "CONDITION=$CONDITION"
echo "PYTORCH_CUDA_ALLOC_CONF=$PYTORCH_CUDA_ALLOC_CONF"

if [ ! -f "$INPUT_JSONL" ]; then
    echo "ERROR: INPUT_JSONL does not exist: $INPUT_JSONL"
    exit 1
fi

if [ ! -f "$DIRECTION_PATH" ]; then
    echo "ERROR: DIRECTION_PATH does not exist: $DIRECTION_PATH"
    exit 1
fi

echo ""
echo "=== Checking compute CLI help ==="
python -m poc_stage5.compute_refusal_projection_dynamics --help

echo ""
echo "=== Running Stage 5 Qwen3 max-100 compute ==="
COMPUTE_ARGS=(
    --input-jsonl "$INPUT_JSONL"
    --direction-path "$DIRECTION_PATH"
    --model-name-or-path "$MODEL_NAME"
    --output-jsonl "$OUTPUT_JSONL"
    --summary-json "$SUMMARY_JSON"
    --error-jsonl "$ERROR_JSONL"
    --max-examples "$MAX_EXAMPLES"
    --max-length "$MAX_LENGTH"
    --layers "$LAYERS"
    --token-regions "$TOKEN_REGIONS"
    --device "$DEVICE"
    --dtype "$DTYPE"
    --condition "$CONDITION"
    --run-name "$RUN_NAME"
)

if [ "$OVERWRITE" = "true" ]; then
    COMPUTE_ARGS+=(--overwrite)
fi

if [ "$NO_PROGRESS" = "true" ]; then
    COMPUTE_ARGS+=(--no-progress)
fi

python -m poc_stage5.compute_refusal_projection_dynamics "${COMPUTE_ARGS[@]}"

echo ""
echo "=== Running Stage 5 aggregate summarizer ==="
SUMMARY_ARGS=(
    --input-jsonl "$OUTPUT_JSONL"
    --output-json "$AGGREGATE_JSON"
    --output-csv "$AGGREGATE_CSV"
)

if [ "$OVERWRITE" = "true" ]; then
    SUMMARY_ARGS+=(--overwrite)
fi

python -m poc_stage5.summarize_refusal_projection_dynamics "${SUMMARY_ARGS[@]}"

echo ""
echo "=== Stage 5 max-100 output validation ==="
wc -l "$OUTPUT_JSONL"
echo "Compute summary JSON: $SUMMARY_JSON"
echo "Aggregate summary CSV: $AGGREGATE_CSV"

ROW_COUNT="$(wc -l < "$OUTPUT_JSONL")"
if [ "$ROW_COUNT" -ne "$EXPECTED_ROWS" ]; then
    echo "WARNING: expected $EXPECTED_ROWS projection rows, got $ROW_COUNT"
else
    echo "Projection row count matches expected $EXPECTED_ROWS rows"
fi

echo ""
echo "=== Checking Stage 2/3/4 diff is empty ==="
git diff -- poc_stage2 poc_stage3 poc_stage4

echo ""
echo "=== Stage 5 Qwen3 max-100 final analysis finished successfully ==="
date
