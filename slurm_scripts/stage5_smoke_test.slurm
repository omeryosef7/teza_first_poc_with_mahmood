#!/bin/bash

#SBATCH --job-name=poc_stage5_smoke
#SBATCH --output=logs/poc_stage5_smoke_%j.out
#SBATCH --error=logs/poc_stage5_smoke_%j.err
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

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl}"
DIRECTION_PATH="${DIRECTION_PATH:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction/direction.pt}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs outputs "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"

echo "=== Stage 5 smoke test started ==="
date
hostname
pwd
python -V

echo "INPUT_JSONL=$INPUT_JSONL"
echo "DIRECTION_PATH=$DIRECTION_PATH"

if [ ! -f "$INPUT_JSONL" ]; then
    echo "ERROR: INPUT_JSONL does not exist: $INPUT_JSONL"
    echo "Available JSONL files:"
    find outputs -type f -name "*.jsonl" | sort | head -50
    exit 1
fi

if [ ! -f "$DIRECTION_PATH" ]; then
    echo "ERROR: DIRECTION_PATH does not exist: $DIRECTION_PATH"
    echo "Available direction-like files:"
    find outputs -type f | grep -i direction | head -50
    exit 1
fi

echo ""
echo "=== Checking CLI help ==="
python -m poc_stage5.compute_refusal_projection_dynamics --help
python -m poc_stage5.summarize_refusal_projection_dynamics --help

echo ""
echo "=== Running Stage 5 loader + direction smoke test ==="
python -m poc_stage5.compute_refusal_projection_dynamics \
    --input-jsonl "$INPUT_JSONL" \
    --direction-path "$DIRECTION_PATH" \
    --model-name-or-path Qwen/Qwen3-14B \
    --output-jsonl outputs/stage5/test_should_not_be_created.jsonl \
    --summary-json outputs/stage5/test_should_not_be_created_summary.json \
    --max-examples 3 \
    --max-length 512 \
    --device cpu \
    --dtype auto \
    --layers auto \
    --token-regions last_32,final_token \
    --no-progress

echo ""
echo "=== Checking optional internal self tests ==="
python -c 'import importlib; mods=["poc_stage5.data_loading","poc_stage5.direction_loading"]; [getattr(importlib.import_module(m), "_self_test", lambda: None)() for m in mods]; print("self tests passed or were skipped")'

echo ""
echo "=== Checking that Stage 5 did not create output artifacts ==="
if [ -e outputs/stage5/test_should_not_be_created.jsonl ]; then
    echo "ERROR: compute stub created output JSONL too early"
    exit 1
fi

if [ -e outputs/stage5/test_should_not_be_created_summary.json ]; then
    echo "ERROR: compute stub created summary JSON too early"
    exit 1
fi

echo ""
echo "=== Checking Stage 2/3/4 were not modified ==="
git diff -- poc_stage2 poc_stage3 poc_stage4

echo ""
echo "=== Stage 5 smoke test finished successfully ==="
date
