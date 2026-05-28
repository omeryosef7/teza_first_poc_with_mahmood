#!/bin/bash

# Run the redacted batch exporter across all examples without overwriting existing artifacts.
# Submit with:
#   sbatch --partition=killable slurm_scripts/stage6_qwen3_14b_batch_redacted_all.slurm
# Optional first positional arg: max_examples to process.

#SBATCH --job-name=poc_stage6_qwen3_batch_redacted
#SBATCH --output=logs/poc_stage6_qwen3_batch_redacted_%j.out
#SBATCH --error=logs/poc_stage6_qwen3_batch_redacted_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,n-301,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl}"
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/outputs/stage6/all_traces_redacted}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
MAX_ATTEMPTS_FROM_ARG="${1:-}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

mkdir -p logs "$OUT_DIR"

echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUT_DIR=$OUT_DIR"
echo "MODEL_NAME=$MODEL_NAME"
echo "MAX_ATTEMPTS=${MAX_ATTEMPTS_FROM_ARG:-<all>}"

ARGS=(
    --input-jsonl "$INPUT_JSONL"
    --out-dir "$OUT_DIR"
    --model "$MODEL_NAME"
)

if [ -n "$MAX_ATTEMPTS_FROM_ARG" ]; then
    ARGS+=(--max-attempts "$MAX_ATTEMPTS_FROM_ARG")
fi

python -m poc_stage6.batch_redacted_export_all "${ARGS[@]}"
