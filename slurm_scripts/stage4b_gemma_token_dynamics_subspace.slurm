#!/bin/bash

#SBATCH --job-name=poc_s4b_gemma_dyn
#SBATCH --output=logs/poc_stage4b_gemma_dyn_sub_%j.out
#SBATCH --error=logs/poc_stage4b_gemma_dyn_sub_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805

# Stage 4B-subspace (Gemma 4): token-level dynamics analysis using K refusal directions.
#
# INPUT: gemma_traces_full_1_11_eos_fixed + direction_subspace.pt from Stage 4A2.
# OUTPUT: Per-token projections onto K directions, plots, flat JSONL metrics.
#
# INPUT_VARIANT controls which subspace to use:
#   "behavioral" (default): outputs/stage4/gemma4-e4b-it/direction_subspace_behavioral/
#   "endofthink":           outputs/stage4/gemma4-e4b-it/direction_subspace_endofthink/
#   "startofthink":         outputs/stage4/gemma4-e4b-it/direction_subspace_startofthink/
#   "endofresponse":        outputs/stage4/gemma4-e4b-it/direction_subspace_endofresponse/
#
# Submit once per variant:
#   sbatch slurm_scripts/stage4b_gemma_token_dynamics_subspace.slurm
#   INPUT_VARIANT=endofthink sbatch slurm_scripts/stage4b_gemma_token_dynamics_subspace.slurm
#   INPUT_VARIANT=startofthink sbatch slurm_scripts/stage4b_gemma_token_dynamics_subspace.slurm
#   INPUT_VARIANT=endofresponse sbatch slurm_scripts/stage4b_gemma_token_dynamics_subspace.slurm
#
# MAX_NEW_TOKENS_TO_ANALYZE=3072: covers early thinking phase, fits within wall time.
# Gemma traces are much shorter (~3-8K tokens) so this should cover most examples fully.
#
# Output: outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_{variant}/

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
INPUT_VARIANT="${INPUT_VARIANT:-behavioral}"

STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/gemma_traces_full_1_11_eos_fixed}"

# Resolve subspace dir and output dir from variant
if [ "$INPUT_VARIANT" = "behavioral" ]; then
    DEFAULT_SUBSPACE="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_behavioral"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_behavioral"
elif [ "$INPUT_VARIANT" = "startofthink" ]; then
    DEFAULT_SUBSPACE="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_startofthink"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_startofthink"
elif [ "$INPUT_VARIANT" = "endofresponse" ]; then
    DEFAULT_SUBSPACE="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_endofresponse"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_endofresponse"
elif [ "$INPUT_VARIANT" = "endofthink" ]; then
    DEFAULT_SUBSPACE="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_endofthink"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_endofthink"
else
    # Generic fallback for hvp_startofthink, dvp_endofthink, etc.
    DEFAULT_SUBSPACE="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/direction_subspace_${INPUT_VARIANT}"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_${INPUT_VARIANT}"
fi

DIRECTION_SUBSPACE_PATH="${DIRECTION_SUBSPACE_PATH:-$DEFAULT_SUBSPACE}"
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT}"

LAYERS="${LAYERS:-}"
if [ -z "$LAYERS" ]; then
    METADATA_PATH="$DIRECTION_SUBSPACE_PATH/direction_subspace_metadata.json"
    if [ -f "$METADATA_PATH" ]; then
        LAYERS=$(python3 -c "
import json, pathlib
d = json.loads(pathlib.Path('$METADATA_PATH').read_text())
layers = [x.get('layer', -1) for x in d.get('directions', [])]
print('all' if (not layers or all(l < 0 for l in layers)) else ','.join(str(l) for l in layers))
")
        echo "[stage4b_gemma] Auto-detected subspace layers from metadata: $LAYERS"
    else
        LAYERS="all"
        echo "[stage4b_gemma] WARNING: subspace metadata not found at $METADATA_PATH, using all layers"
    fi
fi

MAX_EXAMPLES="${MAX_EXAMPLES:-}"
MAX_NEW_TOKENS_TO_ANALYZE="${MAX_NEW_TOKENS_TO_ANALYZE:-3072}"
SMOKE="${SMOKE:-false}"
RESUME="${RESUME:-false}"
PLOT="${PLOT:-true}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs outputs "$OUTPUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton} 2>/dev/null || true

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

echo "[stage4b_gemma_dyn_sub] Starting at $(date) on $(hostname)"
echo "[stage4b_gemma_dyn_sub] INPUT_VARIANT=${INPUT_VARIANT}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

ARGS=(
    --model-family "$MODEL_FAMILY"
    --model-name-or-path "$MODEL_NAME"
    --stage6-input "$STAGE6_INPUT"
    --direction-subspace-path "$DIRECTION_SUBSPACE_PATH"
    --output-dir "$OUTPUT_DIR"
    --layers "$LAYERS"
)

if [ -n "$MAX_EXAMPLES" ]; then
    ARGS+=(--max-examples "$MAX_EXAMPLES")
fi

if [ -n "$MAX_NEW_TOKENS_TO_ANALYZE" ]; then
    ARGS+=(--max-new-tokens-to-analyze "$MAX_NEW_TOKENS_TO_ANALYZE")
fi

if [ "$SMOKE" = "true" ]; then
    ARGS+=(--smoke)
fi

if [ "$RESUME" = "true" ]; then
    ARGS+=(--resume)
fi

if [ "$PLOT" = "false" ]; then
    ARGS+=(--no-plot)
fi

python -m poc_stage4.analyze_token_dynamics_subspace "${ARGS[@]}"

echo "[stage4b_gemma_dyn_sub] Done at $(date)"
