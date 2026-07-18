#!/bin/bash

#SBATCH --job-name=gcg_10a_gemma4_520
#SBATCH --output=logs/gcg_10a_gemma4_520_%j.out
#SBATCH --error=logs/gcg_10a_gemma4_520_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Track 10A — Scale Gemma4 empty_think suffix to all 520 AdvBench behaviors.
#
# Sprint 3 Track 9G (gcg_full_gemma4_9g_emptythink_L31) achieved 2.7% seeded ASR
# on 25 behaviors — the first non-zero Gemma4 attack result across 12+ attempts.
# This track evaluates that same suffix on all 520 behaviors.
#
# Mechanism: empty thinking block forces Gemma4 to generate a response without
# the refusal-reasoning step (safety decision is encoded in thinking content).
#
# Pattern mirrors 9A (Qwen3 Phase 8 suffix → 520 beh).
# Expected: ~2.5% seeded ASR if 25→520 generalization holds.
# Even 1% unseeded = publishable first cross-scale Gemma4 attack.
#
# Resumable: rows already in FREE_GENERATION_RESULTS.jsonl are skipped by row_key.
# Expected total: 520 × 4 conditions × 3 seeds = 6240 rows.
# After seeded: run unseeded via split_unseeded_shards.py / merge_unseeded_shards.py.
#
# Usage:
#   sbatch slurm_scripts/run_gcg_full_10a_gemma4_emptythink_full520.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
BASE="${PROJECT_DIR}/outputs/stage_gcg_full"
SOURCE_RUN_DIR="${BASE}/gcg_full_gemma4_9g_emptythink_L31"
EVAL_RUN_DIR="${BASE}/gcg_full_gemma4_10a_emptythink_full520"
MANIFEST="${BASE}/advbench_gemma4_emptythink_full520_manifest.jsonl"
SEEDS="42,43,44"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs "$EVAL_RUN_DIR"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "========================================================"
echo "  Track 10A — Gemma4 empty_think Suffix on Full 520 Behaviors"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "SOURCE_RUN_DIR:  ${SOURCE_RUN_DIR}"
echo "EVAL_RUN_DIR:    ${EVAL_RUN_DIR}"
echo "MANIFEST:        ${MANIFEST}"
echo "SEEDS:           ${SEEDS}"
echo "NOTE: 9G (25 beh) achieved 2.7% ASR; empty-think bypasses refusal block"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ ! -f "${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
    echo "ERROR: FINAL_CANDIDATES.jsonl not found at ${SOURCE_RUN_DIR}"
    echo "Ensure gcg_full_gemma4_9g_emptythink_L31 optimization is complete."
    exit 1
fi

if [ ! -f "${MANIFEST}" ]; then
    echo "ERROR: Manifest not found: ${MANIFEST}"
    echo "Run: python scripts/build_gemma4_emptythink_full520_manifest.py"
    exit 1
fi

# Copy source artifacts (idempotent)
if [ ! -f "${EVAL_RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
    cp "${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl" "${EVAL_RUN_DIR}/FINAL_CANDIDATES.jsonl"
    echo "Copied FINAL_CANDIDATES.jsonl from source."
fi
if [ ! -f "${EVAL_RUN_DIR}/CONFIG.json" ]; then
    cp "${SOURCE_RUN_DIR}/CONFIG.json" "${EVAL_RUN_DIR}/CONFIG.json"
    echo "Copied CONFIG.json from source."
fi

EXISTING_ROWS=$(wc -l < "${EVAL_RUN_DIR}/FREE_GENERATION_RESULTS.jsonl" 2>/dev/null || echo 0)
echo "Existing rows: ${EXISTING_ROWS} / 6240"
echo "Manifest: $(wc -l < "${MANIFEST}") behaviors"

python - "$EVAL_RUN_DIR" "$MANIFEST" "$SEEDS" <<'PYEOF'
import sys, json
from pathlib import Path

eval_dir = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
seeds = [int(s) for s in sys.argv[3].split(",")]

sys.path.insert(0, str(Path(".").resolve()))

from poc_stage_gcg_early.build_safe_surrogate_manifest import load_manifest
from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_all_candidates

config = json.load(open(eval_dir / "CONFIG.json"))
model_family = config.get("model_family", "gemma4")
model_name = config.get("model_name_or_path", "google/gemma-4-E4B-it")
enable_thinking = config.get("enable_thinking", True)

print(f"[10A] model_family={model_family}, model={model_name}", flush=True)
print(f"[10A] Loading model...", flush=True)

from poc_stage4.qwen3_model import load_gemma4_model
wrapped = load_gemma4_model(model_name, require_cuda=True, log_device_placement=True)
model = wrapped.model
tokenizer = wrapped.tokenizer
model.eval()

tasks = load_manifest(manifest_path)
print(f"[10A] {len(tasks)} tasks, seeds={seeds}", flush=True)

evaluate_all_candidates(
    model=model,
    tokenizer=tokenizer,
    model_family=model_family,
    final_candidates_path=eval_dir / "FINAL_CANDIDATES.jsonl",
    tasks=tasks,
    enable_thinking=enable_thinking,
    seeds=seeds,
    output_dir=eval_dir,
    max_new_tokens=2048,
)
PYEOF

FINAL_ROWS=$(wc -l < "${EVAL_RUN_DIR}/FREE_GENERATION_RESULTS.jsonl" 2>/dev/null || echo 0)
echo ""
echo "Rows after this pass: ${FINAL_ROWS} / 6240"

python3 -c "
import json, collections
rows = [json.loads(l) for l in open('${EVAL_RUN_DIR}/FREE_GENERATION_RESULTS.jsonl') if l.strip()]
by_combo = collections.defaultdict(list)
for r in rows:
    k = (r.get('task_id',''), r.get('seed',''))
    by_combo[k].append(str(r.get('strongreject_is_success','False'))=='True')
wins = sum(1 for v in by_combo.values() if any(v))
print(f'{len(rows)} rows, {len(by_combo)} combos, {wins} wins ({wins/len(by_combo)*100:.1f}% per-combo ASR)')
by_label = collections.defaultdict(list)
for r in rows:
    by_label[r.get('condition_label','')].append(str(r.get('strongreject_is_success','False'))=='True')
for k, v in sorted(by_label.items()):
    print(f'  {k}: {sum(v)/len(v):.3f} ({sum(v)}/{len(v)})')
" 2>/dev/null || true

if [ "${FINAL_ROWS}" -ge 6200 ]; then
    echo ">>> 10A seeded COMPLETE (>=6200 rows)"
    touch "${EVAL_RUN_DIR}/SEEDED_DONE"
    echo ">>> Next: run unseeded evaluation"
    echo "    python scripts/split_unseeded_shards.py --run-dir ${EVAL_RUN_DIR}"
else
    echo ">>> 10A still in progress — resubmit to continue:"
    echo "    sbatch slurm_scripts/run_gcg_full_10a_gemma4_emptythink_full520.slurm"
fi

echo ""
echo "========================================================"
echo "  10A Pass COMPLETE — $(date -u)"
echo "========================================================"
