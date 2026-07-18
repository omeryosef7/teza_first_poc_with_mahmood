#!/bin/bash

#SBATCH --job-name=gcg_9c_unseed
#SBATCH --output=logs/gcg_9c_unseeded_%j.out
#SBATCH --error=logs/gcg_9c_unseeded_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Track 9C — Unseeded generalization eval (seeds 100/200/300).
#
# Seeded eval (seeds 42/43/44) hits 6240 rows in gcg_full_qwen3_9c_lambda03_seed45_full520.
# This job evaluates the same suffix on 520 behaviors with held-out seeds 100/200/300.
# Outputs to gcg_full_qwen3_9c_lambda03_seed45_full520_unseeded/ (no collision).
# Resumable: row_key = task_id + seed + condition_label.
#
# Submit after 9C seeded reaches 6240 rows:
#   sbatch slurm_scripts/run_gcg_full_9c_unseeded.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
BASE="${PROJECT_DIR}/outputs/stage_gcg_full"
SOURCE_RUN_DIR="${BASE}/gcg_full_qwen3_9c_lambda03_seed45_full520"
EVAL_RUN_DIR="${BASE}/gcg_full_qwen3_9c_lambda03_seed45_full520_unseeded"
MANIFEST="${BASE}/advbench_cot_full520_manifest.jsonl"
SEEDS="100,200,300"
TARGET_ROWS=6240

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
echo "  Track 9C — Unseeded Generalization Eval (seeds 100/200/300)"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "SOURCE_RUN_DIR:  ${SOURCE_RUN_DIR}"
echo "EVAL_RUN_DIR:    ${EVAL_RUN_DIR}"
echo "MANIFEST:        ${MANIFEST}"
echo "SEEDS:           ${SEEDS}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

# Ensure source files exist
for f in "${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl" "${SOURCE_RUN_DIR}/CONFIG.json" "${MANIFEST}"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: Required file not found: $f"
        exit 1
    fi
done

# Copy candidates and config to unseeded eval dir (if not already present)
if [ ! -f "${EVAL_RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
    cp "${SOURCE_RUN_DIR}/FINAL_CANDIDATES.jsonl" "${EVAL_RUN_DIR}/FINAL_CANDIDATES.jsonl"
    echo "Copied FINAL_CANDIDATES.jsonl from seeded run."
fi
if [ ! -f "${EVAL_RUN_DIR}/CONFIG.json" ]; then
    cp "${SOURCE_RUN_DIR}/CONFIG.json" "${EVAL_RUN_DIR}/CONFIG.json"
    echo "Copied CONFIG.json from seeded run."
fi

EXISTING=$(wc -l < "${EVAL_RUN_DIR}/FREE_GENERATION_RESULTS.jsonl" 2>/dev/null || echo 0)
echo "Existing unseeded rows: ${EXISTING} / ${TARGET_ROWS}"

python - "$EVAL_RUN_DIR" "$MANIFEST" "$SEEDS" <<'PYEOF'
import sys, json, collections
from pathlib import Path

eval_dir = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
seeds = [int(s) for s in sys.argv[3].split(",")]

sys.path.insert(0, str(Path(".").resolve()))

from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_all_candidates
from poc_stage4.qwen3_model import load_qwen3_model

print("[9C-unseed] Loading Qwen3-14B...", flush=True)
wrapped = load_qwen3_model("Qwen/Qwen3-14B", require_cuda=True, log_device_placement=True)
model = wrapped.model
tokenizer = wrapped.tokenizer
model.eval()

tasks_raw = [json.loads(l) for l in open(manifest_path) if l.strip()]

class Task:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)

tasks = [Task(r) for r in tasks_raw]
print(f"[9C-unseed] {len(tasks)} tasks, seeds={seeds}", flush=True)

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

FINAL=$(wc -l < "${EVAL_RUN_DIR}/FREE_GENERATION_RESULTS.jsonl" 2>/dev/null || echo 0)
echo ""
echo "--- Unseeded rows after this pass: ${FINAL} / ${TARGET_ROWS} ---"

python3 -c "
import json, collections
try:
    rows = [json.loads(l) for l in open('${EVAL_RUN_DIR}/FREE_GENERATION_RESULTS.jsonl') if l.strip()]
    opt = [r for r in rows if 'optimized' in r.get('condition_label','')]
    by_combo = collections.defaultdict(list)
    for r in opt:
        k = (r.get('task_id',''), str(r.get('seed','')))
        by_combo[k].append(str(r.get('strongreject_is_success','False'))=='True')
    wins = sum(1 for v in by_combo.values() if any(v))
    total = len(by_combo)
    asr = wins/total*100 if total else 0
    print(f'Unseeded ASR: {wins}/{total} combos = {asr:.1f}%')
except Exception as e:
    print(f'ASR calc error: {e}')
" 2>/dev/null || true

if [ "${FINAL}" -ge "${TARGET_ROWS}" ]; then
    echo ""
    echo ">>> 9C UNSEEDED EVAL COMPLETE"
else
    echo ""
    echo ">>> Incomplete — resubmit to continue:"
    echo "    sbatch slurm_scripts/run_gcg_full_9c_unseeded.slurm"
fi

echo ""
echo "========================================================"
echo "  9C Unseeded Eval COMPLETE — $(date -u)"
echo "========================================================"
