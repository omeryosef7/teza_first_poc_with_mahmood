#!/bin/bash

#SBATCH --job-name=ae_smoke_gemma4
#SBATCH --output=logs/ae_smoke_gemma4_%j.out
#SBATCH --error=logs/ae_smoke_gemma4_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805

# Stage AE — Gemma4-E4B-it smoke test: A/E/D/G (goal_index=0, seed=201) generation,
# hidden-state replay with --verify-equivalence, and StrongREJECT+taxonomy scoring.
# Mandatory gate before full launch (submit_qwen_ae.sh).

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

if [ -z "${RUN_DIR:-}" ] || [ -z "${MANIFEST_PATH:-}" ]; then
    echo "ERROR: RUN_DIR and MANIFEST_PATH must be set via --export=ALL,RUN_DIR=...,MANIFEST_PATH=..."
    exit 1
fi

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$RUN_DIR/smoke/gemma4/generation" "$RUN_DIR/smoke/gemma4" \
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

echo "=== Stage AE SMOKE TEST — Gemma4-E4B-it ==="
date; hostname
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
GPU_TYPE=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
if echo "$GPU_TYPE" | grep -qi "A5000\|A4000\|A2000"; then
    echo "ERROR: GPU is $GPU_TYPE — not L40S. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_TYPE"

for COND in A E D G; do
    echo ""
    echo "--- Generation: condition=$COND ---"
    python -m poc_stage_ae.run_ae_generation \
        --model gemma4 --manifest "$MANIFEST_PATH" \
        --goal-index 0 --condition "$COND" \
        --output-dir "$RUN_DIR/smoke/gemma4/generation"
done

echo ""
echo "--- Resume idempotency check: rerunning condition A shard ---"
python -m poc_stage_ae.run_ae_generation \
    --model gemma4 --manifest "$MANIFEST_PATH" \
    --goal-index 0 --condition A \
    --output-dir "$RUN_DIR/smoke/gemma4/generation"
N_ROWS_A=$(wc -l < "$RUN_DIR/smoke/gemma4/generation/shards/gemma4_A_goal0.jsonl")
echo "Rows in condition-A shard after rerun: $N_ROWS_A (expect 1, not 2, if resume works)"

echo ""
echo "--- Hidden-state replay (with --verify-equivalence) ---"
for COND in A E D G; do
    python -m poc_stage_ae.replay_hidden_states \
        --model gemma4 \
        --generation-shard "$RUN_DIR/smoke/gemma4/generation/shards/gemma4_${COND}_goal0.jsonl" \
        --output-dir "$RUN_DIR/smoke/gemma4" \
        --verify-equivalence --verify-n-examples 1
done

echo ""
echo "--- Scoring + taxonomy ---"
for COND in A E D G; do
    python -m poc_stage_ae.score_ae_outputs \
        --model gemma4 \
        --generation-shard "$RUN_DIR/smoke/gemma4/generation/shards/gemma4_${COND}_goal0.jsonl" \
        --output-dir "$RUN_DIR/smoke/gemma4"
done

echo ""
echo "=== Qwen3 smoke test complete ==="
date
