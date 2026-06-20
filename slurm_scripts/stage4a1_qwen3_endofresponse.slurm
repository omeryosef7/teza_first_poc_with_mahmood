#!/bin/bash

#SBATCH --job-name=poc_stage4a1_eor
#SBATCH --output=logs/poc_stage4a1_endofresponse_%j.out
#SBATCH --error=logs/poc_stage4a1_endofresponse_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602,n-302,n-303,n-304,n-305

# Stage 4A1-endofresponse: extract refusal direction at EOS token (after full answer).
#
# CONTRAST: complied vs. refused (qwen_run_success field, same as behavioral).
# POSITION: EOS token (<|im_end|>) = last token of full_prompt_plus_generation_token_ids.
#           Only eos_token traces used (max_new_tokens traces are skipped).
#           In all_traces_full_1_11: 206/220 traces qualify.
#
# WHY: Completes the temporal picture of refusal encoding:
#   startofthink (<think>)  AUC=0.731  [L0/L1/L2]
#   endofthink   (</think>) AUC=0.750  [L26/L29]
#   endofresponse (EOS)     ???
#
# SEQUENCES: mean 16798 tokens, max 32800 tokens. Forward pass only (no generation).
#            max_seq_len=20000 cap (reduced from 30000 after OOM on RTX 3090;
#            mean trace length 16798 tokens, so only extreme outliers are skipped).
#
# Output: outputs/stage4/qwen3-14b/refusal_direction_endofresponse/
#   candidate_directions.pt   [1, n_layers, d_model]
#   direction.pt              provisional best layer

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/all_traces_full_1_11}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction_endofresponse}"
GROUP_BY="${GROUP_BY:-qwen_run_success}"
MAX_PER_GROUP="${MAX_PER_GROUP:-110}"
MAX_SEQ_LEN="${MAX_SEQ_LEN:-20000}"
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

echo "[stage4a1_endofresponse] Starting at $(date) on $(hostname)"
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

echo "[stage4a1_endofresponse] Done at $(date)"
