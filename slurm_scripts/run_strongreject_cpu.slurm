#!/bin/bash
#SBATCH --job-name=sr_score_cpu
#SBATCH --output=logs/sr_score_cpu_%j.out
#SBATCH --error=logs/sr_score_cpu_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1

# General StrongREJECT scorer (API-only rubric -> no GPU; cpu-killable, unlike the
# GPU-requesting stage3_strongreject.slurm). Reuses poc_stage3.run_strongreject_scoring
# + analyze_strongreject_results. Scores jsonl in the hijacking/Phase-4 row schema
# (goal, target_response, is_success, judge_score, goal_index — all supplied by
# HijackingResultRow). Plan sec 6 (frozen judge) / sec 8.5.
#
# Required env: INPUT_JSONL. Optional: OUTPUT_JSONL, SUMMARY_JSON, ANALYSIS_JSON, EVALUATOR.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-poc_stage2}"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs
export LITELLM_LOCAL_MODEL_COST_MAP="True"

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "OPENAI_API_KEY is not set. StrongREJECT rubric scoring cannot run." >&2
    exit 1
fi

INPUT_JSONL="${INPUT_JSONL:?set INPUT_JSONL=path/to/rows.jsonl}"
# Derive sibling output names from the input stem unless overridden.
STEM="${INPUT_JSONL%.jsonl}"
OUTPUT_JSONL="${OUTPUT_JSONL:-${STEM}_strongreject.jsonl}"
SUMMARY_JSON="${SUMMARY_JSON:-${STEM}_strongreject_summary.json}"
ANALYSIS_JSON="${ANALYSIS_JSON:-${STEM}_strongreject_analysis.json}"
EVALUATOR="${EVALUATOR:-strongreject_rubric}"

echo "[sr] scoring $INPUT_JSONL -> $OUTPUT_JSONL (evaluator=$EVALUATOR)"
python -u -m poc_stage3.run_strongreject_scoring \
    --input-jsonl "$INPUT_JSONL" \
    --output-jsonl "$OUTPUT_JSONL" \
    --summary-json "$SUMMARY_JSON" \
    --evaluator "$EVALUATOR" \
    --resume

python -u -m poc_stage3.analyze_strongreject_results \
    --input-jsonl "$OUTPUT_JSONL" \
    --summary-json "$SUMMARY_JSON" \
    --output-json "$ANALYSIS_JSON"
echo "[sr] done"
