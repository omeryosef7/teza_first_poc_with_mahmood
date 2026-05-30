#!/bin/bash

#SBATCH --job-name=poc_stage5_qwen3_smoke
#SBATCH --output=logs/poc_stage5_qwen3_smoke_%j.out
#SBATCH --error=logs/poc_stage5_qwen3_smoke_%j.err
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
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage5/qwen3-14b/smoke_max1_final}"
RUN_NAME="${RUN_NAME:-stage5_qwen3_smoke_max1_final}"
MAX_EXAMPLES="${MAX_EXAMPLES:-1}"
MAX_LENGTH="${MAX_LENGTH:-128}"
LAYERS="${LAYERS:--1}"
TOKEN_REGIONS="${TOKEN_REGIONS:-final_token,last_8}"
DEVICE="${DEVICE:-auto}"
DTYPE="${DTYPE:-bfloat16}"
OVERWRITE="${OVERWRITE:-true}"
NO_PROGRESS="${NO_PROGRESS:-false}"
STORE_TEXT_HASHES="${STORE_TEXT_HASHES:-false}"
INCLUDE_RESPONSE_CONTEXT="${INCLUDE_RESPONSE_CONTEXT:-false}"

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
export OUTPUT_JSONL SUMMARY_JSON ERROR_JSONL

echo "=== Stage 5 Qwen3 projection smoke started ==="
date
hostname
pwd
python -V

echo "MODEL_NAME=$MODEL_NAME"
echo "INPUT_JSONL=$INPUT_JSONL"
echo "DIRECTION_PATH=$DIRECTION_PATH"
echo "OUTPUT_JSONL=$OUTPUT_JSONL"
echo "SUMMARY_JSON=$SUMMARY_JSON"
echo "MAX_EXAMPLES=$MAX_EXAMPLES"
echo "MAX_LENGTH=$MAX_LENGTH"
echo "LAYERS=$LAYERS"
echo "TOKEN_REGIONS=$TOKEN_REGIONS"
echo "DEVICE=$DEVICE"
echo "DTYPE=$DTYPE"
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

ARGS=(
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
    --run-name "$RUN_NAME"
)

if [ "$OVERWRITE" = "true" ]; then
    ARGS+=(--overwrite)
fi

if [ "$NO_PROGRESS" = "true" ]; then
    ARGS+=(--no-progress)
fi

if [ "$STORE_TEXT_HASHES" = "true" ]; then
    ARGS+=(--store-text-hashes)
fi

if [ "$INCLUDE_RESPONSE_CONTEXT" = "true" ]; then
    ARGS+=(--include-response-context)
fi

echo ""
echo "=== Running Stage 5 Qwen3 projection smoke ==="
python -m poc_stage5.compute_refusal_projection_dynamics "${ARGS[@]}"

echo ""
echo "=== Validating smoke outputs ==="
python - <<'PY'
import json
import os
from pathlib import Path

output_jsonl = Path(os.environ["OUTPUT_JSONL"])
summary_json = Path(os.environ["SUMMARY_JSON"])

if not output_jsonl.exists():
    raise SystemExit(f"missing output JSONL: {output_jsonl}")
if not summary_json.exists():
    raise SystemExit(f"missing summary JSON: {summary_json}")

rows = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
summary = json.loads(summary_json.read_text(encoding="utf-8"))
if not rows:
    raise SystemExit("output JSONL has no rows")

forbidden_fields = {
    "prompt",
    "prompt_text",
    "response",
    "response_text",
    "token",
    "tokens",
    "token_strings",
    "hidden_state",
    "hidden_states",
}
for row in rows:
    overlap = forbidden_fields.intersection(row)
    if overlap:
        raise SystemExit(f"raw-text/raw-state field(s) present: {sorted(overlap)}")
    if row.get("hidden_state_index") is None:
        raise SystemExit("missing hidden_state_index")
    if row.get("region") not in {"final_token", "last_8"}:
        raise SystemExit(f"unexpected region: {row.get('region')}")

if summary.get("loaded_examples") != 1:
    raise SystemExit(f"expected loaded_examples=1, got {summary.get('loaded_examples')}")
if summary.get("rows_written") != len(rows):
    raise SystemExit("summary rows_written does not match output JSONL row count")

print("stage5 qwen3 smoke output validation ok")
PY

echo ""
echo "=== Checking Stage 2/3/4 diff is empty ==="
git diff -- poc_stage2 poc_stage3 poc_stage4

echo ""
echo "=== Stage 5 Qwen3 projection smoke finished successfully ==="
date
