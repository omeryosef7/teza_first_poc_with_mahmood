#!/bin/bash

#SBATCH --job-name=poc_stage2b_qwen3_batch
#SBATCH --output=logs/poc_stage2b_qwen3_batch_%j.out
#SBATCH --error=logs/poc_stage2b_qwen3_batch_%j.err
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

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
# Default: use Stage 3 JSONL so strongreject_score from the original run is available as source metadata.
INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage2b/qwen3-14b}"
RUN_NAME="${RUN_NAME:-stage2b_qwen3_batch}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32768}"
ENABLE_THINKING="${ENABLE_THINKING:-true}"
DO_SAMPLE="${DO_SAMPLE:-false}"
SEED="${SEED:-0}"
MAX_EXAMPLES="${MAX_EXAMPLES:-}"  # empty = all examples
SKIP_JUDGE="${SKIP_JUDGE:-false}"
SKIP_STRONGREJECT="${SKIP_STRONGREJECT:-false}"
RESUME="${RESUME:-false}"
OVERWRITE="${OVERWRITE:-false}"

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

OUTPUT_JSONL="$OUTPUT_DIR/${RUN_NAME}.jsonl"
SUMMARY_JSON="$OUTPUT_DIR/${RUN_NAME}_summary.json"
export OUTPUT_JSONL SUMMARY_JSON

echo "=== Stage 2B Qwen3 batch attack started ==="
date
hostname
pwd
python -V

echo "MODEL_NAME=$MODEL_NAME"
echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUTPUT_JSONL=$OUTPUT_JSONL"
echo "SUMMARY_JSON=$SUMMARY_JSON"
echo "RUN_NAME=$RUN_NAME"
echo "MAX_NEW_TOKENS=$MAX_NEW_TOKENS"
echo "ENABLE_THINKING=$ENABLE_THINKING"
echo "DO_SAMPLE=$DO_SAMPLE"
echo "SEED=$SEED"
echo "MAX_EXAMPLES=${MAX_EXAMPLES:-(all)}"
echo "SKIP_JUDGE=$SKIP_JUDGE"
echo "SKIP_STRONGREJECT=$SKIP_STRONGREJECT"
echo "RESUME=$RESUME"
echo "OVERWRITE=$OVERWRITE"
echo "PYTORCH_CUDA_ALLOC_CONF=$PYTORCH_CUDA_ALLOC_CONF"

if [ ! -f "$INPUT_JSONL" ]; then
    echo "ERROR: INPUT_JSONL does not exist: $INPUT_JSONL"
    exit 1
fi

echo ""
echo "=== Checking Stage 2B CLI help ==="
python -m poc_stage2b.run_batch_attack --help

BATCH_ARGS=(
    --input-jsonl "$INPUT_JSONL"
    --output-jsonl "$OUTPUT_JSONL"
    --summary-json "$SUMMARY_JSON"
    --model-name-or-path "$MODEL_NAME"
    --max-new-tokens "$MAX_NEW_TOKENS"
    --seed "$SEED"
)

if [ "$ENABLE_THINKING" = "true" ]; then
    BATCH_ARGS+=(--enable-thinking)
else
    BATCH_ARGS+=(--no-thinking)
fi

if [ "$DO_SAMPLE" = "true" ]; then
    BATCH_ARGS+=(--do-sample)
fi

if [ -n "$MAX_EXAMPLES" ]; then
    BATCH_ARGS+=(--max-examples "$MAX_EXAMPLES")
fi

if [ "$SKIP_JUDGE" = "true" ]; then
    BATCH_ARGS+=(--skip-judge)
fi

if [ "$SKIP_STRONGREJECT" = "true" ]; then
    BATCH_ARGS+=(--skip-strongreject)
fi

if [ "$RESUME" = "true" ]; then
    BATCH_ARGS+=(--resume)
fi

if [ "$OVERWRITE" = "true" ]; then
    BATCH_ARGS+=(--overwrite)
fi

echo ""
echo "=== Running Stage 2B batch attack ==="
python -m poc_stage2b.run_batch_attack "${BATCH_ARGS[@]}"

echo ""
echo "=== Stage 2B output row count ==="
wc -l "$OUTPUT_JSONL" || true

echo ""
echo "=== Stage 2B summary ==="
python - <<'PY'
import json, os
from pathlib import Path
summary_path = Path(os.environ["SUMMARY_JSON"])
if summary_path.exists():
    summary = json.loads(summary_path.read_text())
    print(f"rows_total:   {summary.get('rows_total')}")
    print(f"rows_written: {summary.get('rows_written')}")
    print(f"rows_failed:  {summary.get('rows_failed')}")
    print(f"rows_skipped: {summary.get('rows_skipped_resume')}")
    print(f"model:        {summary.get('model_name')}")
    print(f"max_tokens:   {summary.get('max_new_tokens')}")
else:
    print("summary JSON not found")
PY

echo ""
echo "=== Stage 2B Qwen3 batch attack finished ==="
date
