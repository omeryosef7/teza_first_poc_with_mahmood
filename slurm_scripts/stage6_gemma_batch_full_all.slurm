#!/bin/bash
#
# Full (non-redacted) token-trace batch run for google/gemma-4-E4B-it.
# Mirrors stage6_qwen3_14b_batch_full_all.slurm but targets Gemma.
# Gemma 4B fits on 1 GPU; thinking is ENABLED via <|channel>thought markers.
#
# Submit with:
#   sbatch slurm_scripts/stage6_gemma_batch_full_all.slurm
#
# Override defaults:
#   INPUT_JSONL=... OUT_DIR=... MAX_NEW_TOKENS=32768 sbatch ...

#SBATCH --job-name=stage6_gemma_full
#SBATCH --output=logs/stage6_gemma_full_%j.out
#SBATCH --error=logs/stage6_gemma_full_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_1_11_strongreject.jsonl}"
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/outputs/stage6/gemma_traces_full_1_11}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
ENABLE_THINKING="${ENABLE_THINKING:-true}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-16384}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-}"
RUN_JUDGE="${RUN_JUDGE:-true}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="$HF_HUB_CACHE"
export TRANSFORMERS_CACHE="$HF_HUB_CACHE"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export OUT_DIR

echo "=== Stage 6 Gemma full token-trace batch started ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""
echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUT_DIR=$OUT_DIR"
echo "MODEL_NAME=$MODEL_NAME"
echo "MODEL_FAMILY=$MODEL_FAMILY"
echo "ENABLE_THINKING=$ENABLE_THINKING"
echo "MAX_NEW_TOKENS=$MAX_NEW_TOKENS"
echo "MAX_ATTEMPTS=${MAX_ATTEMPTS:-(all)}"
echo "RUN_JUDGE=$RUN_JUDGE"

if [ ! -f "$INPUT_JSONL" ]; then
    echo "ERROR: INPUT_JSONL not found: $INPUT_JSONL"
    exit 1
fi

ARGS=(
    --input-jsonl "$INPUT_JSONL"
    --out-dir "$OUT_DIR"
    --model "$MODEL_NAME"
    --model-family "$MODEL_FAMILY"
    --max-new-tokens "$MAX_NEW_TOKENS"
    --no-redact
)

if [ "$ENABLE_THINKING" = "false" ]; then
    ARGS+=(--no-enable-thinking)
fi

if [ -n "$MAX_ATTEMPTS" ]; then
    ARGS+=(--max-attempts "$MAX_ATTEMPTS")
fi

if [ "$RUN_JUDGE" = "true" ]; then
    ARGS+=(--run-judge)
fi

echo ""
echo "=== Running full batch exporter ==="
python -m poc_stage6.batch_redacted_export_all "${ARGS[@]}"

echo ""
echo "=== Checking outputs ==="
python - <<'PY'
import json
from pathlib import Path
import os

out_dir = Path(os.environ.get("OUT_DIR", "outputs/stage6/gemma_traces_full_1_11"))
summary_path = out_dir / "batch_summary.json"

if not summary_path.exists():
    print("ERROR: batch_summary.json not found")
    raise SystemExit(1)

summary = json.loads(summary_path.read_text())
results = summary.get("results", [])
completed = [r for r in results if r.get("status") == "completed"]
skipped = [r for r in results if r.get("status") == "skipped_existing"]
failed = [r for r in results if r.get("status") not in ("completed", "skipped_existing")]

print(f"examples_seen:   {summary.get('examples_seen')}")
print(f"completed:       {len(completed)}")
print(f"skipped:         {len(skipped)}")
print(f"failed:          {len(failed)}")

if failed:
    print(f"FAILED examples: {[r['example_id'] for r in failed]}")
PY

echo ""
echo "=== Stage 6 Gemma full token-trace batch finished ==="
date
