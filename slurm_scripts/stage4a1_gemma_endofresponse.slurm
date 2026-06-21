#!/bin/bash

#SBATCH --job-name=poc_s4a1_gemma_eor
#SBATCH --output=logs/poc_stage4a1_gemma_endofresponse_%j.out
#SBATCH --error=logs/poc_stage4a1_gemma_endofresponse_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602,n-302,n-303,n-304,n-305

# Stage 4A1-endofresponse (Gemma 4): extract refusal direction at EOS token (after full answer).
#
# CONTRAST: complied vs. refused (qwen_run_success field, same as behavioral).
# POSITION: EOS token — last token of full_prompt_plus_generation_token_ids.
#           Only eos_token traces used (all 220 traces in eos_fixed qualify).
#
# WHY: Completes the temporal picture of refusal encoding:
#   startofthink (<|channel>thought)  → endofthink (<channel|>) → endofresponse (EOS)
#
# SEQUENCES: Gemma traces in eos_fixed have median ~3-8K tokens (much shorter than
#            Qwen3's ~17K). MAX_SEQ_LEN=16000 caps extreme outliers only.
#            Forward pass only — no generation.
#
# MAX_PER_GROUP=66 matches the number of complied traces.
#
# Output: outputs/stage4/gemma4-e4b-it/refusal_direction_endofresponse/

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/gemma_traces_full_1_11_eos_fixed}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/refusal_direction_endofresponse}"
GROUP_BY="${GROUP_BY:-qwen_run_success}"
MAX_PER_GROUP="${MAX_PER_GROUP:-66}"
MAX_SEQ_LEN="${MAX_SEQ_LEN:-16000}"
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
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONUNBUFFERED=1

echo "[stage4a1_gemma_endofresponse] Starting at $(date) on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

ARGS=(
    --model-family "$MODEL_FAMILY"
    --model-name "$MODEL_NAME"
    --stage6-input "$STAGE6_INPUT"
    --output-dir "$OUTPUT_DIR"
    --group-by "$GROUP_BY"
    --max-seq-len "$MAX_SEQ_LEN"
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

python -m poc_stage4.extract_refusal_direction_endofresponse "${ARGS[@]}"

echo "[stage4a1_gemma_endofresponse] Done at $(date)"
