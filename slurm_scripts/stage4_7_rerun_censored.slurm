#!/bin/bash

#SBATCH --job-name=stage4_7_rerun
#SBATCH --output=logs/stage4_7_rerun_%j.out
#SBATCH --error=logs/stage4_7_rerun_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4.7 — Corrective rerun of 5 censored rows at max_new_tokens=65536.
#
# The 5 rows that hit max_new_tokens=32768 in the original run are rerun here
# with a doubled budget.  Results are written to a SEPARATE directory so the
# original run is never overwritten.
#
# If a row reaches eos_token with this budget, it supersedes the original in
# the canonical analysis; if it is still censored it is retained as unknown.
#
# The 5 censored (source_example_id, condition) pairs:
#   goal_index=0|attack_iteration=2|conversation_id=4  cond=E (lower)
#   goal_index=0|attack_iteration=1|conversation_id=5  cond=E (upper)
#   goal_index=0|attack_iteration=1|conversation_id=6  cond=D (middle)
#   goal_index=1|attack_iteration=2|conversation_id=4  cond=E (middle)
#   goal_index=3|attack_iteration=1|conversation_id=5  cond=F (middle)
#
# Implementation: we target goals 0,1,3 and conditions D,E,F  (superset that
# covers all 5, plus a few non-censored rows that will simply be re-confirmed).
# The corrective manifest records which rows were actually censored originally.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

ORIG_RUN_DIR="$PROJECT_DIR/outputs/stage4_7/runs/run_array_20260610_1442"
CORR_RUN_DIR="${CORR_RUN_DIR:-$PROJECT_DIR/outputs/stage4_7/runs/corrective_rerun_65536}"
REPLICATION_PROMPTS="$PROJECT_DIR/outputs/stage4_7/replication_prompts.jsonl"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$CORR_RUN_DIR" \
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

echo "=== Stage 4.7 Corrective Rerun (max_new_tokens=65536) ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
echo "ORIG_RUN_DIR=$ORIG_RUN_DIR"
echo "CORR_RUN_DIR=$CORR_RUN_DIR"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

# Rerun goals 0,1,3 × conditions D,E,F at 65536 tokens (covers all 5 censored pairs).
# --force ensures we write new results even if a prior corrective run exists.
python -m poc_stage4_7.run_replication \
    --replication-prompts "$REPLICATION_PROMPTS" \
    --output-dir "$CORR_RUN_DIR" \
    --goals "0,1,3" \
    --conditions "D,E,F" \
    --max-new-tokens 65536 \
    --skip-judge \
    --force

echo ""
echo "=== Checking corrective rerun outputs ==="
python - <<'PY'
import json, sys
from pathlib import Path
import os
corr_dir = Path(os.environ["CORR_RUN_DIR"])
summary = corr_dir / "run_summary.jsonl"
if not summary.exists():
    print(f"ERROR: run_summary.jsonl not found in {corr_dir}")
    sys.exit(1)
rows = [json.loads(l) for l in summary.read_text().splitlines() if l.strip()]
print(f"Corrective rerun rows: {len(rows)}")
truncated = [r for r in rows if r.get("finish_reason") == "max_new_tokens"]
complete = [r for r in rows if r.get("finish_reason") == "eos_token"]
print(f"  eos_token (complete): {len(complete)}")
print(f"  max_new_tokens (still censored): {len(truncated)}")
for r in rows:
    print(f"  goal={r.get('goal_index')} cond={r.get('condition')} stratum={r.get('selection_stratum')}"
          f" finish={r.get('finish_reason')} sr={r.get('sr_success')} think={r.get('think_token_count')}")
PY

echo ""
echo "=== Building corrective rerun manifest ==="
python - <<'PY'
import json
from pathlib import Path
import os
from datetime import datetime, timezone

orig_dir = Path(os.environ["ORIG_RUN_DIR"])
corr_dir = Path(os.environ["CORR_RUN_DIR"])

# Load original censored rows
orig_rows = {json.loads(l).get("run_id"): json.loads(l)
             for l in (orig_dir / "run_summary.jsonl").read_text().splitlines() if l.strip()}
orig_censored = {k: v for k, v in orig_rows.items() if v.get("finish_reason") == "max_new_tokens"}

# Load corrective rows
corr_rows = {}
corr_summary = corr_dir / "run_summary.jsonl"
if corr_summary.exists():
    corr_rows = {json.loads(l).get("run_id"): json.loads(l)
                 for l in corr_summary.read_text().splitlines() if l.strip()}

# Build manifest
manifest = {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "orig_run_dir": str(orig_dir),
    "corrective_run_dir": str(corr_dir),
    "max_new_tokens_corrective": 65536,
    "max_new_tokens_original": 32768,
    "original_censored_n": len(orig_censored),
    "replacements": [],
    "still_censored": [],
}
for run_id, orig in orig_censored.items():
    corr = corr_rows.get(run_id)
    if corr:
        if corr.get("finish_reason") == "eos_token":
            manifest["replacements"].append({
                "run_id": run_id,
                "source_example_id": orig.get("source_example_id"),
                "condition": orig.get("condition"),
                "original_finish_reason": orig.get("finish_reason"),
                "corrective_finish_reason": corr.get("finish_reason"),
                "original_sr_success": orig.get("sr_success"),
                "corrective_sr_success": corr.get("sr_success"),
                "corrective_sr_score": corr.get("strongreject_score"),
                "row_source": "corrective_rerun_65536",
            })
        else:
            manifest["still_censored"].append({
                "run_id": run_id,
                "source_example_id": orig.get("source_example_id"),
                "condition": orig.get("condition"),
                "note": "still censored at 65536 tokens — classified as unknown behavioral outcome",
            })
    else:
        manifest["still_censored"].append({
            "run_id": run_id,
            "source_example_id": orig.get("source_example_id"),
            "condition": orig.get("condition"),
            "note": "not found in corrective run",
        })

# Write to orig analysis dir
out_path = orig_dir / "analysis" / "corrective_rerun_manifest.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(manifest, f, indent=2)
print(f"Wrote {out_path}")
print(f"  Replaced (now complete): {len(manifest['replacements'])}")
print(f"  Still censored: {len(manifest['still_censored'])}")
for r in manifest["replacements"]:
    print(f"    SUPERSEDED: {r['run_id']} -> sr_success={r['corrective_sr_success']}")
for r in manifest["still_censored"]:
    print(f"    STILL UNKNOWN: {r['run_id']}: {r['note']}")
PY

echo ""
echo "=== Re-running canonical audit with corrective rerun data ==="
python -m poc_stage4_7.audit_and_canonicalize_results \
    --run-dir "$ORIG_RUN_DIR" \
    --corrective-rerun-dir "$CORR_RUN_DIR"

echo ""
echo "=== Re-running analysis with updated canonical data ==="
python -m poc_stage4_7.analyze_replication \
    --run-dir "$ORIG_RUN_DIR"

echo ""
echo "=== Stage 4.7 Corrective Rerun COMPLETE ==="
date
