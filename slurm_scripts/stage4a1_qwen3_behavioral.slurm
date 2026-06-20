#!/bin/bash

#SBATCH --job-name=poc_stage4a1_qwen3_behavioral
#SBATCH --output=logs/poc_stage4a1_qwen3_behavioral_%j.out
#SBATCH --error=logs/poc_stage4a1_qwen3_behavioral_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602

# Stage 4A1-behavioral: extract refusal direction from behavioral outcomes at </think>.
#
# CONTRAST: complied vs. refused — outcome-based, using qwen_run_success field.
#           qwen_run_success=True  (complied): StrongREJECT score>=0.5 OR judge_score=10
#           qwen_run_success=False (refused):  StrongREJECT score<0.5  AND judge_score=1
#
# WHY qwen_run_success instead of judge_score alone:
#   In outputs/stage6/all_traces_full_1_11, the Gemini judge scored 219/220 traces as
#   refused (judge_score=1), leaving only 1 complied example — far too few for a direction.
#   StrongREJECT reveals 113 traces with SR>=0.5, giving a clean 113 complied / 107 refused
#   split that is already encoded in the qwen_run_success field.
#
# POSITION: </think> token in existing Stage 6 token sequences (no new generation).
#
# INPUT: Stage 6 trace artifacts in STAGE6_INPUT — requires full_prompt_plus_generation_token_ids
#        and qwen_run_success for each trace.
#
# Output: outputs/stage4/qwen3-14b/refusal_direction_behavioral/
#   candidate_directions.pt   [1, n_layers, d_model]  DiM = mean(complied) - mean(refused)
#   direction.pt              provisional best layer
#   group_summary.json        complied/refused counts and source info

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/all_traces_full_1_11}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction_behavioral}"
GROUP_BY="${GROUP_BY:-qwen_run_success}"
MAX_PER_GROUP="${MAX_PER_GROUP:-110}"
DIRECTION_NORMALIZATION="${DIRECTION_NORMALIZATION:-unit}"
DRY_RUN="${DRY_RUN:-false}"
OVERWRITE="${OVERWRITE:-true}"

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

ARGS=(
    --model-family "$MODEL_FAMILY"
    --model-name "$MODEL_NAME"
    --stage6-input "$STAGE6_INPUT"
    --output-dir "$OUTPUT_DIR"
    --group-by "$GROUP_BY"
    --direction-normalization "$DIRECTION_NORMALIZATION"
    --no-progress
)

if [ -n "$MAX_PER_GROUP" ]; then
    ARGS+=(--max-per-group "$MAX_PER_GROUP")
fi

if [ "$DRY_RUN" = "true" ]; then
    ARGS+=(--dry-run)
fi

if [ "$OVERWRITE" = "true" ]; then
    ARGS+=(--overwrite)
fi

python -m poc_stage4.extract_refusal_direction_behavioral "${ARGS[@]}"
