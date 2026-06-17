#!/bin/bash
#
# Smoke test for Gemma 4 Stage 6 token-trace with enable_thinking=True.
# Runs 3 examples to verify:
#   - AutoProcessor loads correctly
#   - enable_thinking=True produces <|channel>thought markers
#   - thinking_segmentation_status = "parsed_from_thought_channel"
#   - think_text and final_assistant_text are both populated
#   - token_table has "think" and "final" role_or_part entries
#   - token_table_reconstruction_status = "exact"
#
# Submit with:
#   sbatch slurm_scripts/stage6_gemma_smoke_thinking.slurm

#SBATCH --job-name=stage6_gemma_smoke_think
#SBATCH --output=logs/stage6_gemma_smoke_thinking_%j.out
#SBATCH --error=logs/stage6_gemma_smoke_thinking_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
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
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/outputs/stage6/gemma_smoke_thinking}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-4096}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"

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

echo "=== Stage 6 Gemma thinking smoke test started ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""
echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUT_DIR=$OUT_DIR"
echo "MODEL_NAME=$MODEL_NAME"
echo "MODEL_FAMILY=$MODEL_FAMILY"
echo "MAX_NEW_TOKENS=$MAX_NEW_TOKENS"
echo "MAX_ATTEMPTS=$MAX_ATTEMPTS"

if [ ! -f "$INPUT_JSONL" ]; then
    echo "ERROR: INPUT_JSONL not found: $INPUT_JSONL"
    exit 1
fi

echo ""
echo "=== Running smoke (${MAX_ATTEMPTS} examples, enable_thinking=True) ==="
python -m poc_stage6.batch_redacted_export_all \
    --input-jsonl "$INPUT_JSONL" \
    --out-dir "$OUT_DIR" \
    --model "$MODEL_NAME" \
    --model-family "$MODEL_FAMILY" \
    --max-new-tokens "$MAX_NEW_TOKENS" \
    --max-attempts "$MAX_ATTEMPTS" \
    --no-redact

echo ""
echo "=== Verifying thinking was captured ==="
python - <<'PY'
import json, glob, sys
from pathlib import Path
import os

out_dir = Path(os.environ["OUT_DIR"])
artifacts = sorted(out_dir.glob("*.json"))
artifacts = [p for p in artifacts if p.name != "batch_summary.json"]

if not artifacts:
    print("ERROR: no artifact files found in", out_dir)
    sys.exit(1)

print(f"Found {len(artifacts)} artifact(s). Checking first one: {artifacts[0].name}")
a = json.loads(artifacts[0].read_text())

seg = a.get("thinking_segmentation_status")
think = a.get("think_text")
final = a.get("final_assistant_text")
version = a.get("artifact_version")
recon = a.get("token_table_reconstruction_status")
token_table = a.get("token_table") or []

think_rows = [r for r in token_table if r.get("role_or_part") == "think"]
final_rows  = [r for r in token_table if r.get("role_or_part") == "final"]

print(f"  artifact_version:              {version}")
print(f"  thinking_segmentation_status:  {seg}")
print(f"  think_text populated:          {think is not None and len(think) > 0}")
print(f"  final_assistant_text populated:{final is not None and len(final) > 0}")
print(f"  token_table_reconstruction:    {recon}")
print(f"  think-role rows:               {len(think_rows)}")
print(f"  final-role rows:               {len(final_rows)}")

errors = []
if version != "poc_stage6_model_token_trace_v1":
    errors.append(f"  FAIL: artifact_version={version!r}, expected poc_stage6_model_token_trace_v1")
if seg != "parsed_from_thought_channel":
    errors.append(f"  FAIL: thinking_segmentation_status={seg!r}, expected parsed_from_thought_channel")
if not think:
    errors.append("  FAIL: think_text is empty/null — model may not have generated thinking")
if not final:
    errors.append("  FAIL: final_assistant_text is empty/null")
if recon != "exact":
    errors.append(f"  FAIL: token_table_reconstruction_status={recon!r}, expected exact")
if len(think_rows) == 0:
    errors.append("  FAIL: no token rows with role_or_part='think'")
if len(final_rows) == 0:
    errors.append("  FAIL: no token rows with role_or_part='final'")

if errors:
    print("\nSMOKE FAILED:")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("\nSMOKE PASSED: Gemma 4 thinking tokens correctly captured.")
PY

echo ""
echo "=== Stage 6 Gemma thinking smoke COMPLETE ==="
date
echo ""
echo "NEXT STEP: If smoke passed, submit full run:"
echo "  sbatch slurm_scripts/stage6_gemma_batch_full_all.slurm"
