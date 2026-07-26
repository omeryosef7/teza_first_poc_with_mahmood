#!/bin/bash
#SBATCH --job-name=soft_prompt_gate3
#SBATCH --output=logs/soft_prompt_gate3_%j.out
#SBATCH --error=logs/soft_prompt_gate3_%j.err
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
# GATE-3 SOFT-PROMPT BEHAVIORAL UPPER BOUND (docs/REINFORCE_TROPT_IMPLEMENTATION.md §10 +
# docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md §D5 / §5 "Pkg 3" / Gate 3).
# Drives scripts/reinforce_objective/soft_prompt_reinforce.py::soft_prompt_upper_bound — the
# CEILING test: can a CONTINUOUS soft prompt (the most powerful input intervention) raise
# BEHAVIORAL ASR via the expected-reward objective? If the continuous ceiling can't, the strictly
# weaker discrete REINFORCE-MAC (Gate 4) can't either, so Gate 3 gates Gate 4.
#
# Reuses poc_stage4/qwen3_model.py loaders, the chat-template adapter, the verified RLOO/advantage/
# signed-CE estimator (reinforce.py), the stop-gradient surrogate (gpu_runner.py), the TROPT
# soft-prompt embed-splice pattern (SoftPrompt__schwinn2024.py), and — per hard rule §2.7 — the SAME
# StrongREJECT judge as the Gate-1 eval (poc_stage3.strongreject_scoring; success = score >= 0.5).
# No optimizer/model/reward logic reimplemented. Runs under the TROPT venv.
#
# TWO ARMS (Gate-3 read is behavioral ASR, REINFORCE vs Prefix-CE):
#   prefix_ce  — the differentiable target-prefix CE (TROPT PrefillCELoss) COMPARISON baseline.
#   reinforce  — the EXPECTED-REWARD policy-gradient objective (RLOO advantages, signed CE;
#                logprob differentiable in the continuous soft prompt -> clean autograd).
# lengths L in {5,20}; SMOKE uses 1 init seed (--seeds 0); the main run bumps to --seeds 0,1,2.
#
# TARGET SET: data/manifests/clearharm_gate3_5.csv (created by a sibling task). If ABSENT the runner
# falls back to data/manifests/clearharm_opt15.csv first-5 and records manifest_fallback= in each
# output row (see soft_prompt_reinforce._resolve_manifest) — the job still runs, apples-to-apples
# with Gate-1's clearharm_opt set.
#
# REWARD: strong_reject reuses poc_stage3.strongreject_scoring directly (loaded once, cached). It
# needs the StrongREJECT judge/API configured in .env; if unavailable it errors loudly at runtime
# (intentional — no silent mock). Swap REWARD=synthetic for a judge-free plumbing/sign check.
#
# RESUME-SAFE: one JSONL line per (instruction, objective, L, seed) run, flushed; the runner SKIPS
# any run already present in the output file, so re-running `sbatch` re-does only the missing runs.
#
# enable_thinking is threaded consistently through the differentiable optimization pass AND the
# free-generation the reward scores, and echoed into every run log (docs/TROPT_PIN_AND_BYTEVERIFY.md
# §C2). NOT SUBMITTED — for the deferred GPU run only.
set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs

# Reuse the existing HF cache (Qwen3-14B already downloaded by prior work). No downloads.
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

# Use the conda env that has BOTH torch AND the StrongREJECT judge (the SAME env
# Gate-1's eval used) — TROPT/.venv has torch but NOT the strong_reject checkout,
# which made 683064 fail loudly at reward construction. poc_stage2 = torch 2.7.1+cu126
# + transformers + strong_reject + our reinforce_objective modules all import cleanly,
# and it guarantees env-level judge consistency with the Gate-1 eval (§2.7).
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
echo "[soft-prompt-gate3] conda env active: $CONDA_ENV ($(python -c 'import torch;print("torch",torch.__version__)'))"
TROPT_PY="python"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MANIFEST="${MANIFEST:-data/manifests/clearharm_gate3_5.csv}"   # sibling task; falls back to clearharm_opt15 first-5
LIMIT="${LIMIT:-5}"
LENGTHS="${LENGTHS:-5,20}"
SEEDS="${SEEDS:-0}"                 # SMOKE: 1 seed. Main run: SEEDS=0,1,2
OBJECTIVES="${OBJECTIVES:-prefix_ce,reinforce}"
STEPS="${STEPS:-30}"
KVAL="${KVAL:-4}"
LR="${LR:-0.001}"
REWARD="${REWARD:-strong_reject}"   # strong_reject (same judge as Gate-1) | synthetic (judge-free)
OUT="${OUT:-outputs/phase_d_soft_prompt_gate3/runs.jsonl}"

echo "[soft-prompt-gate3] model=$MODEL_NAME manifest=$MANIFEST limit=$LIMIT lengths=$LENGTHS seeds=$SEEDS objectives=$OBJECTIVES steps=$STEPS K=$KVAL reward=$REWARD"
# NON-FATAL GPU banner (copied from run_reinforce_mac_smoke.slurm: the old
# `nvidia-smi | awk exit` aborted the whole job under `set -euo pipefail`. `--constraint=l40s`
# already guarantees the GPU type, so this is informational only and must never kill the run.)
GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1 || true)"
case "$GPU_NAME" in
  *L40S*) : ;;
  *) echo "[soft-prompt-gate3] WARN: GPU name '$GPU_NAME' not confirmed L40S (constraint=l40s already enforces it); continuing." ;;
esac
echo "[soft-prompt-gate3] GPU: ${GPU_NAME:-unknown}  git=$(git rev-parse HEAD 2>/dev/null || echo unknown)  date=$(date -u)"

mkdir -p "$(dirname "$OUT")"
"$TROPT_PY" -u -m scripts.reinforce_objective.soft_prompt_reinforce \
    --model-name "$MODEL_NAME" \
    --model-family "$MODEL_FAMILY" \
    --manifest "$MANIFEST" \
    --limit "$LIMIT" \
    --lengths "$LENGTHS" \
    --seeds "$SEEDS" \
    --objectives "$OBJECTIVES" \
    --steps "$STEPS" \
    --K "$KVAL" \
    --learning-rate "$LR" \
    --reward "$REWARD" \
    --enable-thinking \
    --out "$OUT"

echo "[soft-prompt-gate3] DONE date=$(date -u)"
