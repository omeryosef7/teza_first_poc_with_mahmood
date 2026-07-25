#!/bin/bash
#SBATCH --job-name=phase5_ae_extract
#SBATCH --output=logs/phase5_ae_extract_%A_%a.out
#SBATCH --error=logs/phase5_ae_extract_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301,n-801
#SBATCH --array=0-49%5

# Phase-5 (§9) FULL AE extraction — one array task per (goal_index,condition) tuple from
# outputs/phase5_mechanistic/extraction_tuples.txt. Runs poc_stage_ae.run_ae_generation then
# replay_hidden_states → residual streams [n_rows, n_pos, n_layers+1, d_model] at §9.4 positions.
# %5 concurrency stays within the ≤6 SLURM budget alongside the running Qwen3 attack.
# Env: MANIFEST, TUPLES_FILE, RUN_DIR (all have sensible defaults).
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MANIFEST="${MANIFEST:-outputs/phase5_mechanistic/qwen3_phase5_ae_manifest.jsonl}"
TUPLES_FILE="${TUPLES_FILE:-outputs/phase5_mechanistic/extraction_tuples.txt}"
RUN_DIR="${RUN_DIR:-outputs/phase5_mechanistic/extraction}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$RUN_DIR/generation"
MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
# §31.3-A (Claude extension, user-authorized 2026-07-23): the L40S nodes have NO node-local scratch
# (sinfo TMP_DISK=0; /tmp too small for 15GB weights), so §31.3 node-local-ephemeral is infeasible.
# Option A: all families read from the project cache; non-Qwen3 additionally sets HF_HUB_OFFLINE=1 so
# only ALREADY-PRESENT weights are used and NO new weights are ever downloaded/persisted (a not-yet-
# cached non-Qwen3 model fails loudly here → surface it for a separate one-time decision). Plan §31.3-A.
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
if [ "$MODEL_FAMILY" != "qwen3" ]; then
    export HF_HUB_OFFLINE=1
    export TRANSFORMERS_OFFLINE=1
    echo "[extract] §31.3-A: MODEL_FAMILY=$MODEL_FAMILY reads project cache (offline; no new downloads)"
fi
export HF_HUB_CACHE="$HF_HOME/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

# Fail-loud if the tuple file is LONGER than the static --array bound (0-49 = 50 tasks): SLURM cannot
# compute the array header at runtime, so extra tuples would be silently dropped with no failed-task
# record (§23.4). Assert once (on task 0) that every tuple is covered; regenerate the header via a
# submit wrapper `sbatch --array=0-$(($(wc -l < TUPLES_FILE)-1))%5 ...` if the file grew.
ARRAY_MAX="${ARRAY_MAX:-49}"
# awk NR counts lines robustly even when the file lacks a trailing newline (wc -l would undercount by
# one — exactly the off-by-one boundary this guard exists to catch).
NTUPLES=$(awk 'END{print NR}' "$TUPLES_FILE")
if [ "${SLURM_ARRAY_TASK_ID:-0}" -eq 0 ] && [ "$NTUPLES" -gt $((ARRAY_MAX + 1)) ]; then
  echo "[extract] FATAL: $TUPLES_FILE has $NTUPLES tuples but --array covers only $((ARRAY_MAX+1)); tuples $((ARRAY_MAX+2))+ would be dropped. Resubmit with --array=0-$((NTUPLES-1))%5." >&2
  exit 1
fi

# Pick this task's tuple (1-indexed line = array_task_id + 1).
LINE=$((SLURM_ARRAY_TASK_ID + 1))
TUPLE=$(sed -n "${LINE}p" "$TUPLES_FILE")
if [ -z "$TUPLE" ]; then echo "[extract] no tuple at line $LINE — nothing to do"; exit 0; fi
GI="${TUPLE%%:*}"; COND="${TUPLE##*:}"
echo "[extract] task=$SLURM_ARRAY_TASK_ID tuple=$TUPLE (goal_index=$GI condition=$COND) node=$(hostname) date=$(date -u)"

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then echo "ERROR: expected L40S, got $GPU_NAME"; exit 1; fi

python -u -m poc_stage_ae.run_ae_generation \
    --model "$MODEL_FAMILY" --manifest "$MANIFEST" \
    --goal-index "$GI" --condition "$COND" \
    --output-dir "$RUN_DIR/generation"

SHARD="$RUN_DIR/generation/shards/${MODEL_FAMILY}_${COND}_goal${GI}.jsonl"
python -u -m poc_stage_ae.replay_hidden_states \
    --model "$MODEL_FAMILY" --generation-shard "$SHARD" \
    --output-dir "$RUN_DIR"

echo "[extract] task $SLURM_ARRAY_TASK_ID DONE ($TUPLE) date=$(date -u)"
