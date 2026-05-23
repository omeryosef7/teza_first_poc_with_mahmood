#!/bin/bash

#SBATCH --job-name=poc_stage8a_sandbox_smoke
#SBATCH --output=logs/poc_stage8a_sandbox_smoke_%j.out
#SBATCH --error=logs/poc_stage8a_sandbox_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage8/sandbox_smoke}"
STAGE7_JSONL="${STAGE7_JSONL:-$PROJECT_DIR/outputs/stage7/qwen3-14b/objective_comparison_v1/objective_comparison.jsonl}"

mkdir -p "$PROJECT_DIR/logs" "$OUTPUT_DIR"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

OUTPUT_JSONL="$OUTPUT_DIR/sandbox.jsonl"
SUMMARY_JSON="$OUTPUT_DIR/sandbox_summary.json"
export OUTPUT_JSONL SUMMARY_JSON

echo "=== Stage 8A sandbox smoke started ==="
date
hostname
pwd
python -V

ARGS=(
    --output-jsonl "$OUTPUT_JSONL"
    --summary-json "$SUMMARY_JSON"
    --num-episodes 3
    --max-steps 5
    --reward-mode strongreject_only
    --seed 7
    --overwrite
)

if [ -f "$STAGE7_JSONL" ]; then
    ARGS+=(--stage7-jsonl "$STAGE7_JSONL")
fi

python -m poc_stage8.run_sandbox "${ARGS[@]}"
python -m poc_stage8.summarize_sandbox \
  --input-jsonl "$OUTPUT_JSONL" \
  --output-json "$OUTPUT_DIR/sandbox_aggregate_summary.json" \
  --output-csv "$OUTPUT_DIR/sandbox_aggregate_summary.csv" \
  --overwrite

python - <<'PY'
import json
import os
from pathlib import Path

output_jsonl = Path(os.environ["OUTPUT_JSONL"])
forbidden = {
    "prompt",
    "prompt_text",
    "response",
    "response_text",
    "tokens",
    "token_strings",
    "logits",
    "hidden_state",
    "hidden_states",
}

with output_jsonl.open("r", encoding="utf-8") as handle:
    rows = [json.loads(line) for line in handle if line.strip()]

for row in rows:
    bad = forbidden.intersection(row)
    if bad:
        raise SystemExit(f"Forbidden fields found: {sorted(bad)}")

if len(rows) != 15:
    raise SystemExit(f"Expected 15 rows, found {len(rows)}")

print(json.dumps({"rows": len(rows), "forbidden_fields": []}, indent=2))
PY

echo "=== Stage 8A sandbox smoke finished successfully ==="
date