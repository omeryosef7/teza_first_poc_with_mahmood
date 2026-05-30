#!/bin/bash

#SBATCH --job-name=poc_stage3_strongreject
#SBATCH --output=logs/poc_stage3_strongreject_%j.out
#SBATCH --error=logs/poc_stage3_strongreject_%j.err
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
INPUT_JSONL="$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small.jsonl"
OUTPUT_JSONL="$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl"
SUMMARY_JSON="$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject_summary.json"
ANALYSIS_JSON="$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject_analysis.json"

cd "$PROJECT_DIR"

# Initialize conda for the batch shell.
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh

# Activate the environment that has the project dependencies.
# If you created a dedicated Stage 3 environment, replace this name.
conda activate poc_stage2

# Load API keys and other local environment variables when present.
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs outputs "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,triton}

# Keep runtime caches local to the project workspace.
export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"

# Fail early if the API key is missing, because the rubric evaluator requires OpenAI.
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "OPENAI_API_KEY is not set. Stage 3 StrongREJECT scoring cannot run." >&2
    exit 1
fi

python -m poc_stage3.run_strongreject_scoring \
    --input-jsonl "$INPUT_JSONL" \
    --output-jsonl "$OUTPUT_JSONL" \
    --summary-json "$SUMMARY_JSON" \
    --evaluator strongreject_rubric

python -m poc_stage3.analyze_strongreject_results \
    --input-jsonl "$OUTPUT_JSONL" \
    --summary-json "$SUMMARY_JSON" \
    --output-json "$ANALYSIS_JSON"
