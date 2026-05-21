#!/bin/bash

#SBATCH --job-name=poc_stage5_projection_core_validation
#SBATCH --output=logs/poc_stage5_projection_core_validation_%j.out
#SBATCH --error=logs/poc_stage5_projection_core_validation_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:20:00
#SBATCH --partition=studentkillable
#SBATCH --account=gpu-students
#SBATCH --exclude=s-002

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"

echo "=== Stage 5 projection core validation started ==="
date
hostname
pwd
python -V

echo ""
echo "=== Checking compute CLI help ==="
python -m poc_stage5.compute_refusal_projection_dynamics --help

echo ""
echo "=== Checking projection imports ==="
python -c "from poc_stage5.projection import ProjectionConfig, summarize_token_regions, compute_layer_token_projections; print('projection imports ok')"

echo ""
echo "=== Running synthetic tensor projection smoke test ==="
python - <<'PY'
import json
import sys

import torch

from poc_stage5.projection import compute_layer_token_projections, summarize_token_regions

assert "transformers" not in sys.modules

hidden_states = tuple(torch.randn(1, 10, 4) for _ in range(3))
direction = torch.randn(4)
direction = direction / direction.norm()

projections = compute_layer_token_projections(hidden_states, direction)
summary = summarize_token_regions(
    projections,
    torch.arange(10).unsqueeze(0),
    tokenizer=None,
    token_regions=["all", "last_8", "final_token"],
)

required_stats = {"mean", "max", "min", "final", "abs_mean", "num_tokens"}
assert set(projections) == {0, 1, 2}
for layer_summary in summary.values():
    assert set(layer_summary) == {"all", "last_8", "final_token"}
    for stats in layer_summary.values():
        assert required_stats <= set(stats)
        json.dumps(stats, sort_keys=True)
json.dumps(summary, sort_keys=True)

assert "transformers" not in sys.modules
print("synthetic projection smoke ok")
PY

echo ""
echo "=== Checking that no Stage 5 output artifacts were created ==="
if compgen -G "outputs/stage5/test_should_not_be_created*.json*" > /dev/null; then
    echo "ERROR: validation created Stage 5 output artifacts"
    exit 1
fi

echo ""
echo "=== Checking Stage 2/3/4 diff is empty ==="
git diff -- poc_stage2 poc_stage3 poc_stage4

echo ""
echo "=== Stage 5 projection core validation finished successfully ==="
date
