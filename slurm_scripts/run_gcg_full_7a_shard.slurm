#!/bin/bash

#SBATCH --job-name=gcg_7a_shard
#SBATCH --output=logs/gcg_7a_shard_%j.out
#SBATCH --error=logs/gcg_7a_shard_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,t-806

# Experiment 7A (sharded) — Evaluate 5A suffix on a manifest shard.
#
# Required env: SHARD_ID (1-6)
# Submit: sbatch --export=ALL,SHARD_ID=<N> slurm_scripts/run_gcg_full_7a_shard.slurm
#
# Resumable: row_key skipping inside evaluate_suffix().
# After all shards complete, merge with scripts/merge_7a_shards.py.

set -euo pipefail

: "${SHARD_ID:?SHARD_ID must be set. Submit with --export=ALL,SHARD_ID=<N>}"

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
STAGE_DIR="${PROJECT_DIR}/outputs/stage_gcg_full"
EVAL_RUN_DIR="${STAGE_DIR}/gcg_full_qwen3_7a_shard${SHARD_ID}"
MANIFEST="${STAGE_DIR}/advbench_cot_shard${SHARD_ID}_manifest.jsonl"
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
echo "  Experiment 7A Shard ${SHARD_ID} — 5A Suffix Eval"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "SHARD_ID:        ${SHARD_ID}"
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

if [ ! -f "${EVAL_RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
    echo "ERROR: FINAL_CANDIDATES.jsonl not found at ${EVAL_RUN_DIR}"
    exit 1
fi

N_TASKS=$(wc -l < "${MANIFEST}")
TOTAL_ROWS=$((N_TASKS * 12))
EXISTING_ROWS=$(wc -l < "${EVAL_RUN_DIR}/FREE_GENERATION_RESULTS.jsonl" 2>/dev/null || echo 0)
echo "Manifest tasks:  ${N_TASKS}"
echo "Expected rows:   ${TOTAL_ROWS}"
echo "Existing rows:   ${EXISTING_ROWS} / ${TOTAL_ROWS}"

python - "$EVAL_RUN_DIR" "$MANIFEST" "$SEEDS" <<'PYEOF'
import sys, json
from pathlib import Path

eval_dir = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
seeds = [int(s) for s in sys.argv[3].split(",")]

sys.path.insert(0, str(Path(".").resolve()))

config = json.load(open(eval_dir / "CONFIG.json"))
model_family = config.get("model_family", "qwen3")
model_name = config.get("model_name_or_path", "Qwen/Qwen3-14B")

print(f"[7A-shard] Loading model {model_name}...", flush=True)
# NOTE: hardcoded to Qwen3; add Gemma4 branch if reusing for Gemma4 experiments
from poc_stage4.qwen3_model import load_qwen3_model
wrapped = load_qwen3_model(model_name, require_cuda=True, log_device_placement=True)
model = wrapped.model
tokenizer = wrapped.tokenizer
model.eval()

from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_suffix

manifest_rows = [json.loads(l) for l in open(manifest_path) if l.strip()]
candidates = [json.loads(l) for l in open(eval_dir / "FINAL_CANDIDATES.jsonl") if l.strip()]

print(f"[7A-shard] {len(candidates)} candidates, {len(manifest_rows)} tasks, seeds={seeds}", flush=True)

done = 0
for task_data in manifest_rows:
    class Task: pass
    task = Task()
    for k, v in task_data.items():
        setattr(task, k, v)

    for seed in seeds:
        for cand in candidates:
            suffix_str = cand.get("suffix_str", "")
            if not suffix_str:
                continue
            label = f"optimized_{cand.get('selection_mode', 'weighted')}"
            res = evaluate_suffix(
                model, tokenizer, model_family,
                task_id=task.task_id,
                instruction=task.instruction,
                suffix_str=suffix_str,
                suffix_label=label,
                enable_thinking=True,
                seed=seed,
                output_dir=eval_dir,
            )
            if res is not None:
                done += 1
                if done % 50 == 0:
                    print(f"[7A-shard] {done} new rows written", flush=True)

        for suffix_str, label in [
            (getattr(task, 'neutral_control_suffix', ' ' * 20), "neutral_control"),
            (" " * 16, "random_spaces"),
            (" ", "task_only"),
        ]:
            evaluate_suffix(
                model, tokenizer, model_family,
                task_id=task.task_id,
                instruction=task.instruction,
                suffix_str=suffix_str,
                suffix_label=label,
                enable_thinking=True,
                seed=seed,
                output_dir=eval_dir,
            )

total = sum(1 for _ in open(eval_dir / "FREE_GENERATION_RESULTS.jsonl") if _.strip())
print(f"[7A-shard] Pass complete. Rows in file: {total}", flush=True)
PYEOF

FINAL_ROWS=$(wc -l < "${EVAL_RUN_DIR}/FREE_GENERATION_RESULTS.jsonl" 2>/dev/null || echo 0)
N_TASKS=$(wc -l < "${MANIFEST}")
TOTAL_ROWS=$((N_TASKS * 12))
echo ""
echo "Rows after this pass: ${FINAL_ROWS} / ${TOTAL_ROWS}"

if [ "${FINAL_ROWS}" -ge "$((TOTAL_ROWS - 12))" ]; then
    echo ">>> Shard ${SHARD_ID} COMPLETE"
    touch "${EVAL_RUN_DIR}/DONE"
else
    echo ">>> Shard ${SHARD_ID} still in progress — resubmit to continue"
    echo "    Resubmit: sbatch --export=ALL,SHARD_ID=${SHARD_ID} slurm_scripts/run_gcg_full_7a_shard.slurm"
fi

echo ""
echo "========================================================"
echo "  7A Shard ${SHARD_ID} COMPLETE — $(date -u)"
echo "========================================================"
