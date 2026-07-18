#!/bin/bash

#SBATCH --job-name=gcg_10g_transfer
#SBATCH --output=logs/gcg_10g_transfer_%j.out
#SBATCH --error=logs/gcg_10g_transfer_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Track 10G — Cross-model transfer: evaluate Gemma4 empty_think suffix on Qwen3.
#
# The 9G-G-EmptyThink suffix (optimized for Gemma4, 2.7% ASR) is evaluated
# on Qwen3 via free-generation. Tests whether the suffix's adversarial semantics
# transfer cross-architecture.
#
# Prior: 4E (Qwen3 → Gemma4 transfer) gave 0%. This is the reverse direction.
# If any transfer: suggests shared refusal-direction subspace across architectures.
#
# Pure eval — no new optimization needed.
# Uses the existing free_generation evaluation pipeline.
#
# Usage:
#   sbatch slurm_scripts/run_gcg_full_10g_gemma4_suffix_to_qwen3.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
BASE="${PROJECT_DIR}/outputs/stage_gcg_full"
SOURCE_RUN_DIR="${BASE}/gcg_full_gemma4_9g_emptythink_L31"
EVAL_RUN_DIR="${BASE}/gcg_full_qwen3_10g_from_gemma4_transfer"
MANIFEST="${BASE}/advbench_cot_target_manifest.jsonl"
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
echo "  Track 10G — Gemma4 Suffix Transfer to Qwen3"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "SOURCE_RUN_DIR:  ${SOURCE_RUN_DIR}"
echo "EVAL_RUN_DIR:    ${EVAL_RUN_DIR}"
echo "MANIFEST:        ${MANIFEST}"
echo "NOTE: Tests Gemma4→Qwen3 transfer (reverse of 4E which failed Qwen3→Gemma4)"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ ! -f "${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
    echo "ERROR: Source candidates not found at ${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl"
    exit 1
fi

# Copy candidates and a Qwen3 config into the eval dir
if [ ! -f "${EVAL_RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
    cp "${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl" "${EVAL_RUN_DIR}/FINAL_CANDIDATES.jsonl"
    echo "Copied FINAL_CANDIDATES.jsonl from Gemma4 source run."
fi

# Write a Qwen3 CONFIG.json so the free-gen eval loads the right model
python3 -c "
import json, os
config_path = '${EVAL_RUN_DIR}/CONFIG.json'
if not os.path.exists(config_path):
    src_config = json.load(open('${SOURCE_RUN_DIR}/CONFIG.json'))
    qwen3_config = dict(src_config)
    qwen3_config['model_family'] = 'qwen3'
    qwen3_config['model_name_or_path'] = 'Qwen/Qwen3-14B'
    qwen3_config['run_id'] = 'gcg_full_qwen3_10g_from_gemma4_transfer'
    json.dump(qwen3_config, open(config_path, 'w'), indent=2)
    print(f'Written Qwen3 CONFIG.json to {config_path}')
else:
    print('CONFIG.json already exists, skipping.')
"

echo "Running free-gen eval with Qwen3 on Gemma4 suffix..."
python - "$EVAL_RUN_DIR" "$MANIFEST" "$SEEDS" <<'PYEOF'
import sys, json
from pathlib import Path

eval_dir = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
seeds = [int(s) for s in sys.argv[3].split(",")]

sys.path.insert(0, str(Path(".").resolve()))

from poc_stage_gcg_early.build_safe_surrogate_manifest import load_manifest
from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_all_candidates

print("[10G] Loading Qwen3-14B...", flush=True)
from poc_stage4.qwen3_model import load_qwen3_model
wrapped = load_qwen3_model("Qwen/Qwen3-14B", require_cuda=True, log_device_placement=True)
model = wrapped.model
tokenizer = wrapped.tokenizer
model.eval()

tasks = load_manifest(manifest_path)
print(f"[10G] {len(tasks)} tasks, seeds={seeds}", flush=True)
print(f"[10G] Evaluating Gemma4-optimized suffix on Qwen3...", flush=True)

evaluate_all_candidates(
    model=model,
    tokenizer=tokenizer,
    model_family="qwen3",
    final_candidates_path=eval_dir / "FINAL_CANDIDATES.jsonl",
    tasks=tasks,
    enable_thinking=True,
    seeds=seeds,
    output_dir=eval_dir,
    max_new_tokens=2048,
)
PYEOF

RESULTS="${EVAL_RUN_DIR}/FREE_GENERATION_RESULTS.jsonl"
echo ""
echo "--- Results summary ---"
if [ -f "$RESULTS" ]; then
    python3 -c "
import json, collections
rows = [json.loads(l) for l in open('${RESULTS}') if l.strip()]
by_combo = collections.defaultdict(list)
for r in rows:
    k = (r.get('task_id',''), r.get('seed',''))
    by_combo[k].append(str(r.get('strongreject_is_success','False'))=='True')
wins = sum(1 for v in by_combo.values() if any(v))
print(f'{len(rows)} rows, {len(by_combo)} combos, {wins} wins ({wins/len(by_combo)*100:.1f}% per-combo ASR)')
print('Cross-arch transfer: Gemma4 empty_think suffix → Qwen3')
" 2>/dev/null || true
fi

echo ""
echo "========================================================"
echo "  10G Transfer Eval COMPLETE — $(date -u)"
echo "========================================================"
