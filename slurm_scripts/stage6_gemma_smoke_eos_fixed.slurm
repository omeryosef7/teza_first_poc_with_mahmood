#!/bin/bash
#
# Smoke test for the Gemma 4 EOS fix — 15 examples, strict validation, 1 GPU.
# Purpose: verify that Gemma 4 now stops natively at <turn|> (token 106) and that
# no example reaches max_new_tokens or produces repeated <turn|> tokens.
#
# Pass criteria (all 15 examples must satisfy):
#   - generation_finish_reason == "eos_token"
#   - generation_is_valid == true
#   - turn_end_count <= 1
#   - final_assistant_text is non-empty and does not contain "<turn|>"
#   - (if thinking enabled) think_text is non-empty
#
# If --strict-generation-validation is set and any example fails, the job exits
# with a non-zero code and the SLURM task is marked FAILED.
#
# Only proceed to the full 220-example run after this smoke test passes completely.
#
# Submit with:
#   sbatch slurm_scripts/stage6_gemma_smoke_eos_fixed.slurm
#
# Override defaults:
#   OUT_DIR=... MAX_NEW_TOKENS=... sbatch ...

#SBATCH --job-name=stage6_gemma_smoke
#SBATCH --output=logs/stage6_gemma_smoke_%j.out
#SBATCH --error=logs/stage6_gemma_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_1_11_strongreject.jsonl}"
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/outputs/stage6/gemma_turn_stop_smoke}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
ENABLE_THINKING="${ENABLE_THINKING:-true}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32768}"
STRICT_VALIDATION="${STRICT_VALIDATION:-true}"

# 15 representative smoke examples
SMOKE_START=0
SMOKE_END=15

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

echo "=== Stage 6 Gemma EOS-fix smoke test ==="
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
echo "STRICT_VALIDATION=$STRICT_VALIDATION"
echo "Smoke examples: [$SMOKE_START:$SMOKE_END]"

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
    --start-index "$SMOKE_START"
    --end-index "$SMOKE_END"
)

if [ "$ENABLE_THINKING" = "false" ]; then
    ARGS+=(--no-enable-thinking)
fi

if [ "$STRICT_VALIDATION" = "true" ]; then
    ARGS+=(--strict-generation-validation)
fi

echo ""
echo "=== Running smoke batch (examples $SMOKE_START-$SMOKE_END) ==="
python -m poc_stage6.batch_redacted_export_all "${ARGS[@]}"

echo ""
echo "=== Smoke test finished ==="
date

echo ""
echo "=== Smoke validation summary ==="
python - <<'PYEOF'
import json, pathlib, sys

out_dir = pathlib.Path("outputs/stage6/gemma_turn_stop_smoke")
summary_path = out_dir / "batch_summary.json"

if not summary_path.exists():
    print("ERROR: batch_summary.json not found", file=sys.stderr)
    sys.exit(1)

summary = json.loads(summary_path.read_text())
results = summary.get("results", [])

total = len(results)
valid_count = 0
invalid_count = 0
max_tok_count = 0
repeated_turn_count = 0
empty_answer_count = 0
turn_in_answer_count = 0
think_missing_count = 0

for row in results:
    if row.get("status") == "skipped_existing":
        artifact_path = pathlib.Path(row["artifact_path"])
        artifact = json.loads(artifact_path.read_text())
    elif row.get("status") != "completed":
        invalid_count += 1
        print(f"  FAILED: {row.get('example_id')} status={row.get('status')} error={row.get('error_message')}")
        continue
    else:
        artifact_path = pathlib.Path(row["artifact_path"])
        artifact = json.loads(artifact_path.read_text())

    fin = artifact.get("generation_finish_reason")
    val_status = artifact.get("generation_validation_status", "unknown")
    gemma_val = artifact.get("gemma_generation_validation") or {}
    final_text = artifact.get("final_assistant_text") or ""
    think_text = artifact.get("think_text")

    is_valid = val_status == "valid"
    if is_valid:
        valid_count += 1
    else:
        invalid_count += 1

    if fin == "max_new_tokens":
        max_tok_count += 1

    turn_end_count = gemma_val.get("turn_end_count", 0)
    if turn_end_count > 1:
        repeated_turn_count += 1

    if not final_text.strip():
        empty_answer_count += 1

    if "<turn|>" in final_text:
        turn_in_answer_count += 1

    if think_text is None or not str(think_text).strip():
        think_missing_count += 1

    print(f"  {row.get('example_id','?')[:60]:60s}  finish={fin}  valid={is_valid}  turn_end_count={turn_end_count}  sr={row.get('strongreject_score','?')}")

print()
print(f"Total examples:              {total}")
print(f"Valid native generations:    {valid_count}")
print(f"Invalid generations:         {invalid_count}")
print(f"max_new_tokens finishes:     {max_tok_count}")
print(f"Repeated <turn|> instances:  {repeated_turn_count}")
print(f"Empty final answers:         {empty_answer_count}")
print(f"<turn|> in final answer:     {turn_in_answer_count}")
print(f"Missing think_text:          {think_missing_count}")
print()

if invalid_count > 0 or max_tok_count > 0 or repeated_turn_count > 0 or turn_in_answer_count > 0:
    print("SMOKE TEST FAILED — do not launch the full run.")
    sys.exit(1)
else:
    print("SMOKE TEST PASSED — all examples produced clean native outputs.")
PYEOF
