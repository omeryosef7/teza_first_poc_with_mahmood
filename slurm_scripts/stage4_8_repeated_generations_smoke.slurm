#!/bin/bash

#SBATCH --job-name=stage4_8_smoke
#SBATCH --output=logs/stage4_8_smoke_%j.out
#SBATCH --error=logs/stage4_8_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Stage 4.8 smoke test — 6 stochastic generations (1 source prompt × 3 conditions × 2 seeds).
#
# Validates:
#   - Generation infrastructure works with do_sample=True, temperature=0.7, top_p=0.95
#   - Seeds 101+102 produce different generation_hashes (stochasticity confirmed)
#   - Segmentation runs
#   - StrongREJECT scoring runs
#   - Output schema correct (seed in run_id, etc.)
#   - No duplicate rows
#   - Resume behavior works
#
# If this smoke passes, submit stage4_8_repeated_generations_array.slurm.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

SMOKE_DIR="${SMOKE_DIR:-$PROJECT_DIR/outputs/stage4_8/runs/smoke_$(date +%Y%m%d_%H%M%S)}"
MANIFEST="$PROJECT_DIR/outputs/stage4_8/repeated_generation_manifest.jsonl"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$SMOKE_DIR" \
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

echo "=== Stage 4.8 Smoke Test ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
echo "SMOKE_DIR=$SMOKE_DIR"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

# Run smoke: goal 0 prompt, conditions A/D/F, seeds 101+102 = 6 generations
python -m poc_stage4_8.run_repeated_generations \
    --manifest "$MANIFEST" \
    --output-dir "$SMOKE_DIR" \
    --smoke \
    --skip-judge

echo ""
echo "=== Auditing smoke output ==="
export SMOKE_DIR
python -m poc_stage4_8.audit_repeated_generations \
    --run-dir "$SMOKE_DIR" \
    --smoke

echo ""
echo "=== Checking generation diversity (seeds must differ) ==="
python - <<'PY'
import json, sys
from pathlib import Path
import os
smoke_dir = Path(os.environ["SMOKE_DIR"])
rows = [json.loads(l) for l in (smoke_dir / "run_summary.jsonl").read_text().splitlines() if l.strip()]
print(f"Rows: {len(rows)}")
from collections import defaultdict
cells = defaultdict(list)
for r in rows:
    cells[(r.get("source_example_id",""), r.get("condition",""))].append(r.get("generation_hash",""))
n_diverse = sum(1 for hashes in cells.values() if len(set(h for h in hashes if h)) > 1)
print(f"Cells with diverse generation_hashes: {n_diverse}/{len(cells)}")
if n_diverse == 0:
    print("WARNING: All seeds produced identical outputs — seeding may not be working")
else:
    print("PASS: Seeds produce different outputs")
for r in rows:
    print(f"  cond={r.get('condition')} seed={r.get('seed')} "
          f"finish={r.get('finish_reason')} sr={r.get('sr_success')} "
          f"think={r.get('think_token_count')} hash={r.get('generation_hash','')[:12]}")
PY

echo ""
echo "=== Smoke COMPLETE ==="
echo "If audit passed and diversity confirmed, submit full array:"
echo "  sbatch slurm_scripts/stage4_8_repeated_generations_array.slurm"
date
