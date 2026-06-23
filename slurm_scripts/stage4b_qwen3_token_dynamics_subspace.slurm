#!/bin/bash

#SBATCH --job-name=poc_stage4b_qwen3_dyn_sub
#SBATCH --output=logs/poc_stage4b_qwen3_dyn_sub_%j.out
#SBATCH --error=logs/poc_stage4b_qwen3_dyn_sub_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=23:59:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-801,n-802,n-803,n-805

# Stage 4B (subspace): token-level dynamics analysis using K refusal directions.
#
# SCRIPT: poc_stage4.analyze_token_dynamics_subspace  (multi-direction variant)
#         distinct from analyze_stage6_token_dynamics (single direction).
#
# INPUT:  Stage 6 traces + direction_subspace.pt from Stage 4A2-subspace.
# OUTPUT: Per-token projections onto K directions, plots, flat JSONL metrics.
#
# INPUT_VARIANT controls which subspace to use:
#   "endofthink" (default): outputs/stage4/qwen3-14b/direction_subspace_endofthink/
#   "behavioral":           outputs/stage4/qwen3-14b/direction_subspace_behavioral/
#
# RESUME: pass RESUME=true to skip already-processed examples (per-example JSON exists).
#
# MAX_NEW_TOKENS_TO_ANALYZE: limits the forward pass to the first N generated tokens.
#   Default: 3072. Reduces per-example time from ~59 min (full 17K tokens) to ~3 min.
#   Rationale: forward pass is O(n²) in sequence length; 3072 tokens covers the early
#   thinking phase and fits all 220 examples within 23:59:00 (~11h total).
#   Set to empty string ("") to process all tokens (will require multiple RESUME resubmissions).
#
# Output: outputs/stage4/qwen3-14b/token_dynamics_subspace_{endofthink,behavioral}/
#   per_example/<id>.json         per-token × per-layer × per-rank projections
#   per_prompt_metrics.jsonl      one row per example with generation stats
#   token_level_metrics.jsonl     flat (prompt_id, gen_tok_idx, layer, rank, refusal_projection)
#   plots/                        K direction traces per example + aggregate
#   manifest.json                 run metadata

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
INPUT_VARIANT="${INPUT_VARIANT:-endofthink}"   # "endofthink", "behavioral", or "startofthink"

STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/all_traces_full_1_11}"

# Resolve subspace dir and output dir from variant
if [ "$INPUT_VARIANT" = "behavioral" ]; then
    DEFAULT_SUBSPACE="$PROJECT_DIR/outputs/stage4/qwen3-14b/direction_subspace_behavioral"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/token_dynamics_subspace_behavioral"
elif [ "$INPUT_VARIANT" = "startofthink" ]; then
    DEFAULT_SUBSPACE="$PROJECT_DIR/outputs/stage4/qwen3-14b/direction_subspace_startofthink"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/token_dynamics_subspace_startofthink"
elif [ "$INPUT_VARIANT" = "endofthink" ]; then
    DEFAULT_SUBSPACE="$PROJECT_DIR/outputs/stage4/qwen3-14b/direction_subspace_endofthink"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/token_dynamics_subspace_endofthink"
else
    # Generic fallback for hvp_startofthink, dvp_endofthink, etc.
    DEFAULT_SUBSPACE="$PROJECT_DIR/outputs/stage4/qwen3-14b/direction_subspace_${INPUT_VARIANT}"
    DEFAULT_OUTPUT="$PROJECT_DIR/outputs/stage4/qwen3-14b/token_dynamics_subspace_${INPUT_VARIANT}"
fi

DIRECTION_SUBSPACE_PATH="${DIRECTION_SUBSPACE_PATH:-$DEFAULT_SUBSPACE}"
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUTPUT}"

# LAYERS: auto-read from direction_subspace_metadata.json so we only extract the K=5
# subspace layers (not all 40). Reduces per_example JSON from ~22 MB to ~2.7 MB (8× smaller).
# Override with LAYERS=all to extract all layers, or LAYERS=0,5,22 for a custom subset.
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
        echo "[stage4b] Auto-detected subspace layers from metadata: $LAYERS"
    else
        LAYERS="all"
        echo "[stage4b] WARNING: subspace metadata not found at $METADATA_PATH, using all layers"
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
