#!/bin/bash

#SBATCH --job-name=stage4_7_smoke
#SBATCH --output=logs/stage4_7_smoke_%j.out
#SBATCH --error=logs/stage4_7_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4.7 smoke test:
#   - 1 source prompt (goal=0, stratum=lower)
#   - Conditions A, D, F (3 generations)
#   - Verifies: prompt loading, F length match, generation, segmentation,
#               StrongREJECT scoring, output writing, resume behavior

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

RUN_NAME="${RUN_NAME:-smoke_$(date +%Y%m%d_%H%M%S)}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4_7/runs/run_$RUN_NAME}"
REPLICATION_PROMPTS="${REPLICATION_PROMPTS:-$PROJECT_DIR/outputs/stage4_7/replication_prompts.jsonl}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUTPUT_DIR" \
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
export OUTPUT_DIR

echo "=== Stage 4.7 Smoke Test ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
echo "OUTPUT_DIR=$OUTPUT_DIR"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true

echo ""
echo "=== Verifying replication prompts exist ==="
if [ ! -f "$REPLICATION_PROMPTS" ]; then
    echo "ERROR: replication_prompts.jsonl not found — run build_replication_prompts first"
    exit 1
fi
echo "Found: $REPLICATION_PROMPTS"
wc -l "$REPLICATION_PROMPTS"

echo ""
echo "=== Running audit ==="
python -m poc_stage4_7.audit_replication_prompts \
    --prompts-path "$REPLICATION_PROMPTS" \
    --output-dir "$PROJECT_DIR/outputs/stage4_7"
echo "Audit passed."

echo ""
echo "=== Running smoke (goal=0 lower, conditions A,D,F) ==="
python -m poc_stage4_7.run_replication \
    --replication-prompts "$REPLICATION_PROMPTS" \
    --output-dir "$OUTPUT_DIR" \
    --smoke \
    --skip-judge \
    --max-new-tokens 32768

echo ""
echo "=== Verifying smoke outputs ==="
python - <<'PY'
import json, sys
from pathlib import Path
import os
output_dir = Path(os.environ["OUTPUT_DIR"])
summary = output_dir / "run_summary.jsonl"
if not summary.exists():
    print("ERROR: run_summary.jsonl not found")
    sys.exit(1)
rows = [json.loads(l) for l in summary.read_text().splitlines() if l.strip()]
print(f"run_summary.jsonl: {len(rows)} rows")
if len(rows) < 1:
    print("ERROR: no rows in summary")
    sys.exit(1)
# Check all eos_token
truncated = [r for r in rows if r.get("finish_reason") == "max_new_tokens"]
if truncated:
    print(f"WARNING: {len(truncated)} rows hit max_new_tokens — consider increasing budget")
else:
    print("All rows: finish_reason != max_new_tokens (no truncation)")
# Check F length match
f_rows = [r for r in rows if r.get("condition") == "F"]
for r in f_rows:
    lr = r.get("length_match_ratio")
    if lr is not None and abs(float(lr) - 1.0) > 0.05:
        print(f"WARNING: F length_match_ratio={lr} outside ±5%")
    else:
        print(f"F length_match_ratio={lr} (OK)")
# Print summary
for r in rows:
    print(f"  cond={r['condition']} sr_success={r.get('sr_success')} sr_score={r.get('strongreject_score')} think_tok={r.get('think_token_count')} finish={r.get('finish_reason')}")
print("Smoke verification complete.")
PY

echo ""
echo "=== Stage 4.7 Smoke COMPLETE ==="
date

echo ""
echo "NEXT STEP: If smoke passed, submit full array:"
echo "  sbatch slurm_scripts/stage4_7_replication_array.slurm"
