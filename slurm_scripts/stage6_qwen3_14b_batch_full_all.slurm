#!/bin/bash
#
# Full (non-redacted) token-trace batch run.
# Generates complete Qwen3-14B traces for all 42 examples with:
#   - max_new_tokens=16384  (enough for full thinking + answer; no artificial cap)
#   - no --redact-generation (saves think_text, final_assistant_text, full decoded strings)
#
# Each per-example JSON artifact will contain:
#   prompt_token_ids          : list[int]   — input token IDs
#   prompt_token_strings      : list[str]   — input vocab strings
#   prompt_single_token_decodes: list[str]  — input decoded strings
#   generation_token_ids      : list[int]   — all generated token IDs (thinking + answer)
#   generation_token_strings  : list[str]   — generated vocab strings
#   generation_single_token_decodes: list[str] — generated decoded strings
#   think_text                : str|null    — decoded thinking section
#   final_assistant_text      : str|null    — decoded answer section
#   token_table               : list[dict]  — per-token: id, string, decoded, role_or_part
#     role_or_part values: "user", "system", "special", "think", "final"
#   thinking_segmentation_status: "parsed_from_think_tags" when complete
#
# Submit with:
#   sbatch slurm_scripts/stage6_qwen3_14b_batch_full_all.slurm

#SBATCH --job-name=poc_stage6_qwen3_full
#SBATCH --output=logs/poc_stage6_qwen3_full_%j.out
#SBATCH --error=logs/poc_stage6_qwen3_full_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,n-301,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl}"
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/outputs/stage6/all_traces_full}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
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

echo "=== Stage 6 Qwen3 full token-trace batch started ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""
echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUT_DIR=$OUT_DIR"
echo "MODEL_NAME=$MODEL_NAME"
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
    --max-new-tokens "$MAX_NEW_TOKENS"
    --no-redact
)

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

out_dir = Path(os.environ.get("OUT_DIR", "outputs/stage6/all_traces_full"))
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

parsed = sum(1 for r in completed + skipped if r.get("thinking_segmentation_status") == "parsed_from_think_tags")
not_sep = sum(1 for r in completed + skipped if r.get("thinking_segmentation_status") == "not_separable")
print(f"thinking parsed: {parsed}")
print(f"thinking not_separable (still truncated): {not_sep}")

if not_sep > 0:
    print(f"WARNING: {not_sep} examples still truncated — consider increasing MAX_NEW_TOKENS beyond {os.environ.get('MAX_NEW_TOKENS', '16384')}")

if failed:
    print(f"FAILED examples: {[r['example_id'] for r in failed]}")
PY
export OUT_DIR

echo ""
echo "=== Stage 6 Qwen3 full token-trace batch finished ==="
date
