#!/bin/bash
#SBATCH --job-name=phase5_ae_smoke
#SBATCH --output=logs/phase5_ae_smoke_%j.out
#SBATCH --error=logs/phase5_ae_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301

# Phase-5 (§9) AE-extraction SMOKE: run poc_stage_ae generation + hidden-state replay for a couple of
# (goal_index,condition) tuples from our §9 manifest, to validate the residual-stream capture at the
# §9.4 critical positions BEFORE the full extraction. Reuses run_ae_generation + replay_hidden_states.
# Env: MANIFEST (default our phase5 manifest), RUN_DIR, TUPLES="167:G 42:A" (goal_index:condition ...)
set -euo pipefail
echo "[ae-smoke] START job=${SLURM_JOB_ID:-?} node=$(hostname) date=$(date -u)"
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MANIFEST="${MANIFEST:-outputs/phase5_mechanistic/qwen3_phase5_ae_manifest.jsonl}"
RUN_DIR="${RUN_DIR:-outputs/phase5_mechanistic/ae_smoke}"
TUPLES="${TUPLES:-167:G 42:A}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$RUN_DIR/generation"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then echo "ERROR: expected L40S, got $GPU_NAME"; exit 1; fi
echo "[ae-smoke] GPU ok: $GPU_NAME  manifest=$MANIFEST  tuples=$TUPLES"

for T in $TUPLES; do
    GI="${T%%:*}"; COND="${T##*:}"
    echo "--- generation goal_index=$GI condition=$COND ---"
    python -u -m poc_stage_ae.run_ae_generation \
        --model qwen3 --manifest "$MANIFEST" \
        --goal-index "$GI" --condition "$COND" \
        --output-dir "$RUN_DIR/generation"
    SHARD="$RUN_DIR/generation/shards/qwen3_${COND}_goal${GI}.jsonl"
    echo "--- replay goal_index=$GI condition=$COND ($SHARD) ---"
    python -u -m poc_stage_ae.replay_hidden_states \
        --model qwen3 --generation-shard "$SHARD" \
        --output-dir "$RUN_DIR" --verify-equivalence --verify-n-examples 1
done

echo "[ae-smoke] project cache (unchanged):"; du -sh "$PROJECT_DIR/.cache/huggingface" 2>/dev/null || true
echo "[ae-smoke] COMPLETE date=$(date -u)"
