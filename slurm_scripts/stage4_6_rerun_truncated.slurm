#!/bin/bash

#SBATCH --job-name=stage4_6_rerun_trunc
#SBATCH --output=logs/stage4_6_rerun_trunc_%j.out
#SBATCH --error=logs/stage4_6_rerun_trunc_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805

# Rerun goals 1 and 3, condition A only, with max_new_tokens=32768.
# Goals 1 and 3 condition A were truncated at 16384 tokens (all thinking,
# no final response). --force removes the stale rows and reruns them.
# Merges results into the existing full run output directory, then
# re-runs analysis and plots.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

# Target the existing full-run output directory so results are merged in
OUTPUT_DIR="${OUTPUT_DIR:-$(ls -td "$PROJECT_DIR/outputs/stage4_6/runs_output_full_"* 2>/dev/null | head -1)}"
ABLATION_PROMPTS="${ABLATION_PROMPTS:-$PROJECT_DIR/outputs/stage4_6/ablation_prompts.jsonl}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$RUNTIME_DIR"/{config,data,runtime,ipython} \
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

echo "=== Stage 4.6 Rerun Truncated Conditions started ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID"
python -V
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

echo ""
echo "OUTPUT_DIR=$OUTPUT_DIR"
echo "Rerunning: goals 1+3, condition A only, max_new_tokens=32768"

python -m poc_stage4_6.run_controlled_ablation \
    --ablation-prompts "$ABLATION_PROMPTS" \
    --output-dir "$OUTPUT_DIR" \
    --goals "1,3" \
    --conditions "A" \
    --max-new-tokens 32768 \
    --force

echo ""
echo "=== Re-running analysis and plots ==="
python -m poc_stage4_6.analyze_controlled_ablation --run-dir "$OUTPUT_DIR"
python -m poc_stage4_6.plot_controlled_ablation   --run-dir "$OUTPUT_DIR"

echo ""
echo "=== Final result summary ==="
python - <<'PY'
import json, os
from pathlib import Path
out = Path(os.environ.get("OUTPUT_DIR", "outputs/stage4_6/runs_output_full"))
rows = [json.loads(l) for l in (out / "run_summary.jsonl").read_text().splitlines() if l.strip()]
by_goal = {}
for r in rows:
    by_goal.setdefault(r["goal_index"], {})[r["condition"]] = r
print("sr_score/sr_success/think_tokens:")
for g in sorted(by_goal):
    parts = []
    for c in ["A","B","C","D","E"]:
        r = by_goal[g].get(c, {})
        sc = r.get("strongreject_score")
        ok = r.get("sr_success")
        tk = r.get("think_token_count","?")
        mnt = r.get("max_new_tokens","?")
        parts.append(f"{sc if sc is not None else 'None'}/{'T' if ok else 'F'}/{tk}[mnt={mnt}]")
    print(f"  goal {g}: " + "  ".join(parts))
PY

echo ""
echo "=== Stage 4.6 Rerun Truncated Conditions finished ==="
date
