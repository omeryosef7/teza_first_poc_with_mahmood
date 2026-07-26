#!/bin/bash
#SBATCH --job-name=reinforce_mac_smoke
#SBATCH --output=logs/reinforce_mac_smoke_%j.out
#SBATCH --error=logs/reinforce_mac_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-805,t-806,n-804,n-602,n-301
#
# REINFORCE-MAC optimizer smoke (docs/REINFORCE_TROPT_IMPLEMENTATION.md §9 +
# docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md §D4/§D6).
# Drives scripts/reinforce_objective/reinforce_mac.py::reinforce_mac_optimize, the
# end-to-end discrete optimizer that ties the review-cleared pieces together:
#   reinforce_trigger_gradient (PROPOSAL) + MAC momentum (mu=0.6) + GCG candidate
#   sampling  ->  behavioral SELECTION on real free generations (§15.6).
# Reuses poc_stage4/qwen3_model.py loaders, the chat-template adapter, TROPT
# TokenConstraints, and scripts/jailbreak_rewards.py — no optimizer/model/reward
# logic reimplemented. Runs under the TROPT venv.
#
# SAME 3 clearharm_opt15 instructions Gate-1 used (first 3 rows of the manifest),
# K=2, ~10 steps, injected StrongREJECT reward — so the result is DIRECTLY
# comparable to the Gate-1 GCG/MAC Prefix-CE 0/3 (loss=0.003 -> 0/3 ASR). If
# REINFORCE-MAC (which SELECTS on real generations) beats 0/3, that is the §15.6
# thesis confirmed; if it also lands 0/3, the behavioral objective is refuted on
# these behaviors — either way it is an apples-to-apples comparison.
#
# NOTE: real StrongREJECT grader wiring is a GPU/API call-site DEFERRED in
# gpu_runner._build_real_reward_fn (raises NotImplementedError until the grader /
# API key is injected at submission time). The --reward strong_reject path will
# fail loudly until that one-line injection is done — intentional, per hard rules.
# Swap --reward synthetic (with --synthetic-rewards) for a judge-free wiring check.
#
# Per-instruction resume-safe JSONL (one line per step, flushed; skips steps
# already present) under:
#   outputs/phase_d_reinforce_mac_smoke/<task_id>/checkpoints.jsonl
# Re-running `sbatch slurm_scripts/run_reinforce_mac_smoke.slurm` re-does only the
# missing steps/instructions.
#
# enable_thinking is left at the Qwen3 chat-template default (== enable_thinking
# =True) and threaded consistently through optimize AND the selection
# free-generations; the loop RECORDS it in every checkpoint (§C2 consistency).
set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs

# Reuse the existing HF cache (Qwen3-14B already downloaded by prior work). No downloads.
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

# Use poc_stage2 (torch + strong_reject + our reinforce_objective modules). TROPT/.venv
# has torch but NOT the StrongREJECT checkout, so --reward strong_reject fails there
# (root cause of 683064/683117). poc_stage2 = the SAME judge env as the Gate-1 eval (§2.7).
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
echo "[reinforce-mac-smoke] conda env: $CONDA_ENV ($(python -c 'import torch;print("torch",torch.__version__)'))"
TROPT_PY="python"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MANIFEST="${MANIFEST:-data/manifests/clearharm_opt15.csv}"
LIMIT="${LIMIT:-3}"                 # FIRST 3 instructions of the manifest (Gate-1 set)
TRIGGER="${TRIGGER:-! ! ! ! ! ! ! ! ! !}"
KVAL="${KVAL:-2}"
BVAL="${BVAL:-64}"
STEPS="${STEPS:-10}"
MOMENTUM="${MOMENTUM:-0.6}"
REWARD="${REWARD:-strong_reject}"   # strong_reject (deferred grader) | synthetic
OUT_DIR="${OUT_DIR:-outputs/phase_d_reinforce_mac_smoke}"

echo "[reinforce-mac-smoke] model=$MODEL_NAME manifest=$MANIFEST limit=$LIMIT K=$KVAL B=$BVAL steps=$STEPS momentum=$MOMENTUM reward=$REWARD"
# NON-FATAL GPU banner (copied from run_clearharm_smoke.slurm: the old
# `nvidia-smi | awk exit` aborted the whole job under `set -euo pipefail` — awk's
# early exit SIGPIPE'd nvidia-smi. `--constraint=l40s` already guarantees the GPU
# type, so this is informational only and must never kill the run.)
GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1 || true)"
case "$GPU_NAME" in
  *L40S*) : ;;
  *) echo "[reinforce-mac-smoke] WARN: GPU name '$GPU_NAME' not confirmed L40S (constraint=l40s already enforces it); continuing." ;;
esac
echo "[reinforce-mac-smoke] GPU: ${GPU_NAME:-unknown}  git=$(git rev-parse HEAD 2>/dev/null || echo unknown)  date=$(date -u)"

mkdir -p "$OUT_DIR"
"$TROPT_PY" -u -m scripts.reinforce_objective.reinforce_mac \
    --model-name "$MODEL_NAME" \
    --model-family "$MODEL_FAMILY" \
    --manifest "$MANIFEST" \
    --limit "$LIMIT" \
    --trigger "$TRIGGER" \
    --K "$KVAL" \
    --B "$BVAL" \
    --steps "$STEPS" \
    --momentum "$MOMENTUM" \
    --reward "$REWARD" \
    --enable-thinking \
    --out-dir "$OUT_DIR"

echo "[reinforce-mac-smoke] DONE date=$(date -u)"
