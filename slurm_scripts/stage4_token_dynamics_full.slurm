#!/bin/bash

#SBATCH --job-name=stage4_tok_dyn_full
#SBATCH --output=logs/stage4_tok_dyn_full_%j.out
#SBATCH --error=logs/stage4_tok_dyn_full_%j.err
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
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_NAME_OR_PATH="${MODEL_NAME_OR_PATH:-Qwen/Qwen3-14B}"
# Default to the larger redacted batch (99999 run) if present, else fall back
STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/all_traces_redacted_99999}"
REFUSAL_DIR="${REFUSAL_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction}"
LAYERS="${LAYERS:-all}"
# Leave unset to analyze all generated tokens
# MAX_EXAMPLES — unset: process all examples
# MAX_NEW_TOKENS_TO_ANALYZE — unset: analyze full generation
DEVICE="${DEVICE:-auto}"
DTYPE="${DTYPE:-bfloat16}"
RESUME="${RESUME:-true}"
RUN_NAME="${RUN_NAME:-full_$(date +%Y%m%d_%H%M%S)}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/token_dynamics/$RUN_NAME}"
export OUTPUT_DIR
PLOT="${PLOT:-true}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUTPUT_DIR" "$OUTPUT_DIR/per_example" \
    "$RUNTIME_DIR"/{config,data,runtime,ipython} \
    "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

echo "=== Stage 4 token-dynamics full run started ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
pwd
python -V
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

echo ""
echo "MODEL_NAME_OR_PATH=$MODEL_NAME_OR_PATH"
echo "STAGE6_INPUT=$STAGE6_INPUT"
echo "REFUSAL_DIR=$REFUSAL_DIR"
echo "LAYERS=$LAYERS"
echo "MAX_EXAMPLES=${MAX_EXAMPLES:-<all>}"
echo "MAX_NEW_TOKENS_TO_ANALYZE=${MAX_NEW_TOKENS_TO_ANALYZE:-<all>}"
echo "OUTPUT_DIR=$OUTPUT_DIR"
echo "RUN_NAME=$RUN_NAME"
echo "RESUME=$RESUME"
echo "DEVICE=$DEVICE"
echo "DTYPE=$DTYPE"
echo "PYTORCH_CUDA_ALLOC_CONF=$PYTORCH_CUDA_ALLOC_CONF"

# Fall back to default Stage 6 input if the specified path doesn't exist
if [ ! -d "$STAGE6_INPUT" ] && [ ! -f "$STAGE6_INPUT" ]; then
    FALLBACK_STAGE6="$PROJECT_DIR/outputs/stage6/all_traces_redacted"
    echo "WARNING: STAGE6_INPUT not found ($STAGE6_INPUT), trying fallback: $FALLBACK_STAGE6"
    if [ ! -d "$FALLBACK_STAGE6" ] && [ ! -f "$FALLBACK_STAGE6" ]; then
        echo "ERROR: No valid STAGE6_INPUT found. Set STAGE6_INPUT env var."
        exit 1
    fi
    STAGE6_INPUT="$FALLBACK_STAGE6"
    echo "Using fallback STAGE6_INPUT=$STAGE6_INPUT"
fi

if [ ! -f "$REFUSAL_DIR/direction.pt" ]; then
    echo "ERROR: direction.pt not found in REFUSAL_DIR: $REFUSAL_DIR"
    exit 1
fi

if [ ! -f "$REFUSAL_DIR/selected_direction.json" ]; then
    echo "ERROR: selected_direction.json not found in REFUSAL_DIR: $REFUSAL_DIR"
    exit 1
fi

SCRIPT_ARGS=(
    --stage6-input "$STAGE6_INPUT"
    --output-dir "$OUTPUT_DIR"
    --model-name-or-path "$MODEL_NAME_OR_PATH"
    --refusal-direction-path "$REFUSAL_DIR"
    --layers "$LAYERS"
    --run-name "$RUN_NAME"
    --device "$DEVICE"
    --dtype "$DTYPE"
    --allow-provisional-direction
)

if [ -n "${MAX_EXAMPLES:-}" ]; then
    SCRIPT_ARGS+=(--max-examples "$MAX_EXAMPLES")
fi

if [ -n "${MAX_NEW_TOKENS_TO_ANALYZE:-}" ]; then
    SCRIPT_ARGS+=(--max-new-tokens-to-analyze "$MAX_NEW_TOKENS_TO_ANALYZE")
fi

if [ "$RESUME" = "true" ]; then
    SCRIPT_ARGS+=(--resume)
fi

if [ "${PLOT:-true}" != "true" ]; then
    SCRIPT_ARGS+=(--no-plot)
fi

echo ""
echo "=== Running Stage 4 token-dynamics full run ==="
echo "Command: python -m poc_stage4.analyze_stage6_token_dynamics ${SCRIPT_ARGS[*]}"
python -m poc_stage4.analyze_stage6_token_dynamics "${SCRIPT_ARGS[@]}"

echo ""
echo "=== Checking outputs ==="
python - <<'PY'
import json
import sys
from pathlib import Path
import os

output_dir = Path(os.environ["OUTPUT_DIR"])
manifest_path = output_dir / "manifest.json"
per_prompt_path = output_dir / "per_prompt_metrics.jsonl"
token_level_path = output_dir / "token_level_metrics.jsonl"
per_example_dir = output_dir / "per_example"

errors = []

if not manifest_path.exists():
    errors.append(f"MISSING: {manifest_path}")
else:
    m = json.loads(manifest_path.read_text())
    print(f"manifest: status={m.get('status')}, completed={m.get('examples_completed')}, failed={m.get('examples_failed')}, skipped={m.get('examples_skipped')}")
    if m.get("examples_failed", 0) > 0:
        print(f"WARNING: {m['examples_failed']} examples failed — check progress.jsonl")

if per_prompt_path.exists():
    rows = [l for l in per_prompt_path.read_text().splitlines() if l.strip()]
    print(f"per_prompt_metrics.jsonl: {len(rows)} rows")
else:
    errors.append(f"MISSING: {per_prompt_path}")

if token_level_path.exists():
    rows = [l for l in token_level_path.read_text().splitlines() if l.strip()]
    print(f"token_level_metrics.jsonl: {len(rows)} rows")
else:
    errors.append(f"MISSING: {token_level_path}")

if per_example_dir.exists():
    per_ex_files = list(per_example_dir.glob("*.json"))
    print(f"per_example/: {len(per_ex_files)} files")
else:
    errors.append(f"MISSING: {per_example_dir}")

if errors:
    for e in errors:
        print(f"ERROR: {e}")
    sys.exit(1)

print("Output check OK")
PY

echo ""
echo "=== Stage 4 token-dynamics full run finished ==="
date
