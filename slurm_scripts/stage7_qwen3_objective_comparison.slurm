#!/bin/bash

#SBATCH --job-name=poc_stage7_qwen3_objective
#SBATCH --output=logs/poc_stage7_qwen3_objective_%j.out
#SBATCH --error=logs/poc_stage7_qwen3_objective_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

STAGE5_JSONL="${STAGE5_JSONL:-$PROJECT_DIR/outputs/stage5/qwen3-14b/max100_final/per_example_layer_region_projections.jsonl}"
STAGE6_JSONL="${STAGE6_JSONL:-$PROJECT_DIR/outputs/stage6/qwen3-14b/maxall_token_delay/token_delay.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage7/qwen3-14b/objective_comparison_v1}"

mkdir -p "$PROJECT_DIR/logs" "$OUTPUT_DIR"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

OUTPUT_JSONL="$OUTPUT_DIR/objective_comparison.jsonl"
SUMMARY_JSON="$OUTPUT_DIR/objective_comparison_summary.json"
export STAGE5_JSONL STAGE6_JSONL OUTPUT_JSONL SUMMARY_JSON

echo "=== Stage 7 Qwen3 objective comparison started ==="
date
hostname
pwd
python -V

echo "STAGE5_JSONL=$STAGE5_JSONL"
echo "STAGE6_JSONL=$STAGE6_JSONL"
echo "OUTPUT_JSONL=$OUTPUT_JSONL"
echo "SUMMARY_JSON=$SUMMARY_JSON"

if [ ! -f "$STAGE5_JSONL" ]; then
    echo "ERROR: STAGE5_JSONL does not exist: $STAGE5_JSONL"
    exit 1
fi

python - <<'PY'
import json
import os
from pathlib import Path

from poc_stage7.objectives import ObjectiveParameters, Stage7Config, parse_regions, run_stage7_comparison, write_stage7_outputs

stage5_jsonl = Path(os.environ["STAGE5_JSONL"])
stage6_jsonl_value = os.environ.get("STAGE6_JSONL", "")
stage6_jsonl = Path(stage6_jsonl_value) if stage6_jsonl_value and Path(stage6_jsonl_value).exists() else None
output_jsonl = Path(os.environ["OUTPUT_JSONL"])
summary_json = Path(os.environ["SUMMARY_JSON"])

config = Stage7Config(
    stage5_jsonl=stage5_jsonl,
    stage6_jsonl=stage6_jsonl,
    output_jsonl=output_jsonl,
    summary_json=summary_json,
    regions=parse_regions("final_token,last_8,last_32"),
    hidden_state_index=40,
    objective_parameters=ObjectiveParameters(
        lambda_refusal=1.0,
        lambda_preserve=1.0,
        alpha=1.0,
        beta=1.0,
        delta=1.0,
    ),
    overwrite=True,
)

output_rows, summary = run_stage7_comparison(config)
write_stage7_outputs(output_rows, config, summary)
print(json.dumps(summary, indent=2, ensure_ascii=False))
PY

echo "=== Stage 7 objective comparison finished successfully ==="
date
