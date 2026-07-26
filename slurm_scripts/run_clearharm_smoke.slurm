#!/bin/bash
#SBATCH --job-name=clearharm_smoke
#SBATCH --output=logs/clearharm_smoke_%A_%a.out
#SBATCH --error=logs/clearharm_smoke_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301
#SBATCH --array=0-2%3
#
# Package-1 ClearHarm optimization smoke (docs/PACKAGE1_CLEARHARM_SMOKE_PLAN.md).
# Optimizes TROPT triggers for the FIRST 3 instructions of
#   data/manifests/clearharm_opt15.csv
# under three conditions (one per array index). Reuses scripts/phase3_tropt_optimize.py
# and the TROPT recipes (no optimizer logic reimplemented). Runs under the TROPT venv.
#
#   task 0  -> Condition 1: TROPT GCG  + Prefill-CE   (gcg__zou2023,  target-style empty_think)
#   task 1  -> Condition 2: TROPT MAC  + Prefill-CE   (mac__wang2024, momentum 0.6, num_steps 20)
#   task 2  -> Condition 3: MAC proposals + behavioral candidate reranking  -> BLOCKED (see below)
#
# Each condition writes to a SEPARATE sub-dir so triggers.jsonl append + the task_id
# resume-set never cross-contaminate between optimizers:
#   outputs/phase_c_clearharm_smoke/{gcg,mac,mac_rerank}/triggers.jsonl
#
# RESUME / RESUBMIT: triggers.jsonl is resume-safe by task_id, and each task early-exits
# if its triggers.jsonl already holds all EXPECTED behaviors. Re-running
#   sbatch slurm_scripts/run_clearharm_smoke.slurm
# therefore re-does only the missing/incomplete condition(s) and behaviors.
#
# 1 optimization seed (TROPT recipe default). enable_thinking is left at the Qwen3 chat-template
# default at optimize time (== enable_thinking=True), which the eval MUST match (greedy.yaml has
# enable_thinking: true). See docs/TROPT_PIN_AND_BYTEVERIFY.md.
set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs

# Reuse the existing HF cache (Qwen3-14B already downloaded by prior work). No downloads.
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

TROPT_PY="$PROJECT_DIR/TROPT/.venv/bin/python"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
MANIFEST="${MANIFEST:-data/manifests/clearharm_opt15.csv}"
TARGET_STYLE="${TARGET_STYLE:-empty_think}"
LIMIT="${LIMIT:-3}"                 # FIRST 3 instructions of the manifest
SMOKE_ROOT="${SMOKE_ROOT:-outputs/phase_c_clearharm_smoke}"
IDX="${SLURM_ARRAY_TASK_ID:-0}"

# ---- helper: skip a condition whose triggers.jsonl already covers all $LIMIT behaviors ----
already_complete () {
  local jsonl="$1"
  [ -f "$jsonl" ] || return 1
  local n; n=$(wc -l < "$jsonl" | tr -d ' ')
  [ "$n" -ge "$LIMIT" ]
}

echo "[smoke] array_task=$IDX model=$MODEL_NAME manifest=$MANIFEST style=$TARGET_STYLE limit=$LIMIT"
# NON-FATAL GPU banner (fix: the old `nvidia-smi | awk exit` aborted the whole job under
# `set -euo pipefail` — awk's early exit SIGPIPE'd nvidia-smi. `--constraint=l40s` already
# guarantees the GPU type, so this is informational only and must never kill the run.)
GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1 || true)"
case "$GPU_NAME" in
  *L40S*) : ;;
  *) echo "[smoke] WARN: GPU name '$GPU_NAME' not confirmed L40S (constraint=l40s already enforces it); continuing." ;;
esac
echo "[smoke] GPU: ${GPU_NAME:-unknown}  git=$(git rev-parse HEAD 2>/dev/null || echo unknown)  date=$(date -u)"

case "$IDX" in
  0)
    # ---------- Condition 1: TROPT GCG + Prefill-CE ----------
    # NOTE: gcg__zou2023 HARDCODES num_steps=500 (no CLI override); --num-steps is ignored
    # for --optimizer gcg. The plan's "~50 steps" is NOT reachable via CLI without editing
    # TROPT internals (forbidden). Smoke runs the recipe-default 500 steps on 3 behaviors.
    OUT_DIR="$SMOKE_ROOT/gcg"
    if already_complete "$OUT_DIR/triggers.jsonl"; then
      echo "[smoke] cond1 GCG already complete ($OUT_DIR/triggers.jsonl) — skipping."; exit 0
    fi
    echo "[smoke] cond1 GCG -> $OUT_DIR"
    "$TROPT_PY" -u scripts/phase3_tropt_optimize.py \
        --optimizer gcg \
        --target-style "$TARGET_STYLE" \
        --model-name "$MODEL_NAME" \
        --manifest "$MANIFEST" \
        --out-dir "$OUT_DIR" \
        --limit "$LIMIT"
    ;;
  1)
    # ---------- Condition 2: TROPT MAC + Prefill-CE (momentum 0.6, 20 steps) ----------
    # mac__wang2024 default momentum=0.6 (paper mu). --num-steps 20 is honored by the driver.
    OUT_DIR="$SMOKE_ROOT/mac"
    if already_complete "$OUT_DIR/triggers.jsonl"; then
      echo "[smoke] cond2 MAC already complete ($OUT_DIR/triggers.jsonl) — skipping."; exit 0
    fi
    echo "[smoke] cond2 MAC -> $OUT_DIR"
    "$TROPT_PY" -u scripts/phase3_tropt_optimize.py \
        --optimizer mac \
        --target-style "$TARGET_STYLE" \
        --model-name "$MODEL_NAME" \
        --manifest "$MANIFEST" \
        --out-dir "$OUT_DIR" \
        --num-steps 20 \
        --limit "$LIMIT"
    ;;
  2)
    # ---------- Condition 3: MAC proposals + behavioral candidate reranking -> BLOCKED ----------
    # DEPENDENCY: no scripts/reinforce_objective(.py) module exists. Behavioral reranking of a
    # MAC candidate POOL by real-generation StrongREJECT cannot run because:
    #   (a) scripts/phase3_tropt_optimize.py records only best_trigger_str/best_loss — it does
    #       NOT emit MAC's per-step candidate pool, so there is nothing to rerank; capturing the
    #       pool needs a TROPT tracker wired into the driver (a new project-local module + test).
    #   (b) scripts/staged_asr_rerank.py (the existing behavioral reranker) reads percot run
    #       artifacts (FINAL_CANDIDATES.jsonl / ITERATION_LOG.jsonl), not TROPT triggers.jsonl.
    #   (c) scripts/jailbreak_rewards.py is a CPU-only frozen reward INTERFACE (D2), no CLI/runner.
    # No-op so the array completes cleanly; see docs/PACKAGE1_CLEARHARM_SMOKE_PLAN.md "Condition 3".
    echo "[smoke] cond3 BLOCKED: missing scripts/reinforce_objective + no MAC candidate-pool capture."
    echo "[smoke] cond3 see docs/PACKAGE1_CLEARHARM_SMOKE_PLAN.md for the unblock plan. Exiting 0."
    exit 0
    ;;
  *)
    echo "ERROR: unexpected SLURM_ARRAY_TASK_ID=$IDX (expected 0-2)"; exit 1;
    ;;
esac

echo "[smoke] array_task=$IDX DONE date=$(date -u)"
