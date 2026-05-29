#!/bin/bash

#SBATCH --job-name=stage4_tok_dyn_smoke
#SBATCH --output=logs/stage4_tok_dyn_smoke_%j.out
#SBATCH --error=logs/stage4_tok_dyn_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,n-301,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_NAME_OR_PATH="${MODEL_NAME_OR_PATH:-Qwen/Qwen3-14B}"
STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/all_traces_redacted}"
REFUSAL_DIR="${REFUSAL_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction}"
LAYERS="${LAYERS:-all}"
MAX_EXAMPLES="${MAX_EXAMPLES:-5}"
MAX_NEW_TOKENS_TO_ANALYZE="${MAX_NEW_TOKENS_TO_ANALYZE:-128}"
DEVICE="${DEVICE:-auto}"
DTYPE="${DTYPE:-bfloat16}"
RUN_NAME="${RUN_NAME:-smoke_$(date +%Y%m%d_%H%M%S)}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/token_dynamics/$RUN_NAME}"
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

echo "=== Stage 4 token-dynamics smoke started ==="
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
echo "MAX_EXAMPLES=$MAX_EXAMPLES"
echo "MAX_NEW_TOKENS_TO_ANALYZE=$MAX_NEW_TOKENS_TO_ANALYZE"
echo "OUTPUT_DIR=$OUTPUT_DIR"
echo "RUN_NAME=$RUN_NAME"
echo "DEVICE=$DEVICE"
echo "DTYPE=$DTYPE"
echo "PYTORCH_CUDA_ALLOC_CONF=$PYTORCH_CUDA_ALLOC_CONF"

if [ ! -d "$STAGE6_INPUT" ] && [ ! -f "$STAGE6_INPUT" ]; then
    echo "ERROR: STAGE6_INPUT does not exist: $STAGE6_INPUT"
    exit 1
fi

if [ ! -f "$REFUSAL_DIR/direction.pt" ]; then
    echo "ERROR: direction.pt not found in REFUSAL_DIR: $REFUSAL_DIR"
    exit 1
fi

if [ ! -f "$REFUSAL_DIR/selected_direction.json" ]; then
    echo "ERROR: selected_direction.json not found in REFUSAL_DIR: $REFUSAL_DIR"
    exit 1
fi

echo ""
echo "=== Checking CLI help ==="
python -m poc_stage4.analyze_stage6_token_dynamics --help

SCRIPT_ARGS=(
    --stage6-input "$STAGE6_INPUT"
    --output-dir "$OUTPUT_DIR"
    --model-name-or-path "$MODEL_NAME_OR_PATH"
    --refusal-direction-path "$REFUSAL_DIR"
    --layers "$LAYERS"
    --max-examples "$MAX_EXAMPLES"
    --max-new-tokens-to-analyze "$MAX_NEW_TOKENS_TO_ANALYZE"
    --run-name "$RUN_NAME"
    --device "$DEVICE"
    --dtype "$DTYPE"
    --smoke
)

if [ "${PLOT:-true}" != "true" ]; then
    SCRIPT_ARGS+=(--no-plot)
fi

echo ""
echo "=== Running Stage 4 token-dynamics smoke ==="
echo "Command: python -m poc_stage4.analyze_stage6_token_dynamics ${SCRIPT_ARGS[*]}"
python -m poc_stage4.analyze_stage6_token_dynamics "${SCRIPT_ARGS[@]}"

echo ""
echo "=== Validating smoke outputs ==="
python - <<'PY'
import json
import sys
from pathlib import Path
import os

output_dir = Path(os.environ["OUTPUT_DIR"])

manifest_path = output_dir / "manifest.json"
per_prompt_path = output_dir / "per_prompt_metrics.jsonl"
token_level_path = output_dir / "token_level_metrics.jsonl"
progress_path = output_dir / "progress.jsonl"
per_example_dir = output_dir / "per_example"

errors = []

if not manifest_path.exists():
    errors.append(f"MISSING: {manifest_path}")
else:
    m = json.loads(manifest_path.read_text())
    if m.get("status") != "completed":
        errors.append(f"manifest status={m.get('status')!r} (expected 'completed')")
    print(f"manifest: examples_completed={m.get('examples_completed')}, failed={m.get('examples_failed')}")

if not per_prompt_path.exists():
    errors.append(f"MISSING: {per_prompt_path}")
else:
    rows = [json.loads(l) for l in per_prompt_path.read_text().splitlines() if l.strip()]
    print(f"per_prompt_metrics.jsonl: {len(rows)} rows")
    if not rows:
        errors.append("per_prompt_metrics.jsonl is empty")

if not token_level_path.exists():
    errors.append(f"MISSING: {token_level_path}")
else:
    rows = [json.loads(l) for l in token_level_path.read_text().splitlines() if l.strip()]
    print(f"token_level_metrics.jsonl: {len(rows)} rows")
    if not rows:
        errors.append("token_level_metrics.jsonl is empty")
    else:
        # Check key fields present
        r = rows[0]
        for field in ("prompt_id", "generated_token_index", "absolute_token_index", "layer", "refusal_projection"):
            if field not in r:
                errors.append(f"token_level_metrics missing field: {field}")
        # Confirm generated_token_index starts at 0 for first token
        first_per_prompt = {}
        for r in rows:
            pid = r["prompt_id"]
            if pid not in first_per_prompt or r["generated_token_index"] < first_per_prompt[pid]:
                first_per_prompt[pid] = r["generated_token_index"]
        for pid, min_idx in first_per_prompt.items():
            if min_idx != 0:
                errors.append(f"generated_token_index does not start at 0 for {pid}: min={min_idx}")

if not per_example_dir.exists() or not any(per_example_dir.iterdir()):
    errors.append(f"per_example/ directory missing or empty: {per_example_dir}")
else:
    per_ex_files = list(per_example_dir.glob("*.json"))
    print(f"per_example/: {len(per_ex_files)} files")
    # Spot-check first per-example file
    first = json.loads(per_ex_files[0].read_text())
    for field in ("prompt_id", "token_level_data", "selected_layers", "analyzed_token_count"):
        if field not in first:
            errors.append(f"per_example JSON missing field: {field}")
    tld = first.get("token_level_data", [])
    if tld:
        entry = tld[0]
        if "layer_projections" not in entry:
            errors.append("per_example token_level_data[0] missing layer_projections")
        if entry.get("generated_token_index") != 0:
            errors.append(f"per_example token_level_data[0].generated_token_index != 0")
    print(f"per_example spot-check: token_level_data length={len(tld)}, layers={len(first.get('selected_layers', []))}")

if errors:
    print("\nVALIDATION ERRORS:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("\nStage 4 token-dynamics smoke output validation OK")
PY

echo ""
echo "=== Stage 4 token-dynamics smoke finished successfully ==="
date
