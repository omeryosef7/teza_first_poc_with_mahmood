#!/bin/bash

#SBATCH --job-name=ae_verify_gemma4
#SBATCH --output=logs/ae_verify_gemma4_%j.out
#SBATCH --error=logs/ae_verify_gemma4_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805

# Stage AE — targeted re-verification of the final-layer-norm fix in
# replay_hidden_states.py against the existing Gemma4 smoke-test generation
# shards (goal_index=0, seed=201, A/E/D/G). Does NOT regenerate text —
# reuses shards already produced by job 635886. Mandatory before trusting
# Gemma hidden states at scale (see docs/STAGE_AE_EARLY_TOKEN_PROGRESS.md).

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

if [ -z "${RUN_DIR:-}" ]; then
    echo "ERROR: RUN_DIR must be set via --export=ALL,RUN_DIR=..."
    exit 1
fi

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
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

echo "=== Stage AE — Gemma4 replay-fix re-verification ==="
date; hostname
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
GPU_TYPE=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
if echo "$GPU_TYPE" | grep -qi "A5000\|A4000\|A2000"; then
    echo "ERROR: GPU is $GPU_TYPE — not L40S. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_TYPE"

# Force full re-replay (ignore any prior replayed-row bookkeeping from the
# buggy run) by wiping just the hidden-state output dir for this smoke run.
rm -rf "$RUN_DIR/smoke/gemma4/hidden_states"

FAIL=0
for COND in A E D G; do
    echo ""
    echo "--- Hidden-state replay (--verify-equivalence): condition=$COND ---"
    python -m poc_stage_ae.replay_hidden_states \
        --model gemma4 \
        --generation-shard "$RUN_DIR/smoke/gemma4/generation/shards/gemma4_${COND}_goal0.jsonl" \
        --output-dir "$RUN_DIR/smoke/gemma4" \
        --verify-equivalence --verify-n-examples 1 || FAIL=1
done

echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "=== ALL CONDITIONS: verify-equivalence check completed (see per-condition PASS/FAIL above) ==="
else
    echo "=== One or more replay invocations exited non-zero ==="
fi
date
exit $FAIL
