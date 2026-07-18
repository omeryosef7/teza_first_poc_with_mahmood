#!/bin/bash

#SBATCH --job-name=gcg_replay
#SBATCH --output=logs/gcg_replay_%j.out
#SBATCH --error=logs/gcg_replay_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805,t-806

# Stage GCG-Early — Hidden-state replay on free-generation outputs.
#
# For each row in FREE_GENERATION_RESULTS.jsonl, re-runs the model on the
# generated token sequence (prefix + generated tokens) and captures hidden
# states at the Stage AE positions. Outputs per-candidate .pt files to
# hidden_states/ for detection-delay analysis.
#
# Requires FREE_GENERATION_RESULTS.jsonl from run_gcg_free_generation.slurm.
# Appends to hidden_states/ directory; resumable (skips completed rows).
#
# Usage:
#   sbatch --export=ALL,RUN_DIR=outputs/stage_gcg_early/gcg_qwen3_repr_8b \
#          slurm_scripts/run_gcg_replay.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
RUN_DIR="${RUN_DIR:-}"
LAYERS="${LAYERS:-0,5,10,15,20,25,30,35}"

if [ -z "$RUN_DIR" ]; then
    echo "ERROR: RUN_DIR must be set. Usage: sbatch --export=ALL,RUN_DIR=... run_gcg_replay.slurm"
    exit 1
fi

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs "${RUN_DIR}/hidden_states"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "========================================================"
echo "  Stage GCG-Early — Hidden-State Replay"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "RUN_DIR:         ${RUN_DIR}"
echo "LAYERS:          ${LAYERS}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

FREE_GEN="${RUN_DIR}/FREE_GENERATION_RESULTS.jsonl"
if [ ! -f "$FREE_GEN" ]; then
    echo "ERROR: FREE_GENERATION_RESULTS.jsonl not found at ${FREE_GEN}"
    echo "Run Stage 9 (run_gcg_free_generation.slurm) first."
    exit 1
fi
echo "FREE_GENERATION_RESULTS: $(wc -l < "$FREE_GEN") rows"

echo ""
echo "--- Running hidden-state replay ---"
python - "$RUN_DIR" "$LAYERS" <<'PYEOF'
import sys, json, hashlib
from pathlib import Path

run_dir = Path(sys.argv[1])
layers = [int(x) for x in sys.argv[2].split(",")]

import torch
sys.path.insert(0, str(Path(".").resolve()))

config = json.load(open(run_dir / "CONFIG.json"))
model_family = config.get("model_family", "qwen3")
model_name = config.get("model_name_or_path", "Qwen/Qwen3-14B")
enable_thinking = config.get("enable_thinking", True)

print(f"[replay] Loading model {model_name}...", flush=True)
if model_family == "qwen3":
    from poc_stage4.qwen3_model import load_qwen3_model
    wrapped = load_qwen3_model(model_name, require_cuda=True, log_device_placement=True)
else:
    from poc_stage4.qwen3_model import load_gemma4_model
    wrapped = load_gemma4_model(require_cuda=True, log_device_placement=True)

model = wrapped.model
tokenizer = wrapped.tokenizer
model.eval()

from poc_stage_gcg_early.selected_state_capture import capture_selected_states
from poc_stage_gcg_early.model_adapter import apply_chat_template, tokenize_prompt

free_gen_path = run_dir / "FREE_GENERATION_RESULTS.jsonl"
manifest_path = run_dir / "MANIFEST.jsonl"
hs_dir = run_dir / "hidden_states"
hs_dir.mkdir(exist_ok=True)

rows = [json.loads(l) for l in open(free_gen_path) if l.strip()]
manifest = {r["task_id"]: r for r in [json.loads(l) for l in open(manifest_path) if l.strip()]}
print(f"[replay] {len(rows)} rows to process, {len(manifest)} tasks in manifest", flush=True)

done = 0
skipped = 0
errors = 0
for row in rows:
    suffix_hash = hashlib.sha256(row.get("suffix_str", "").encode()).hexdigest()[:8]
    out_name = f"{row['task_id']}_{row['condition_label']}_{suffix_hash}_{row['seed']}.pt"
    out_path = hs_dir / out_name
    if out_path.exists():
        skipped += 1
        continue

    task_id = row["task_id"]
    if task_id not in manifest:
        print(f"[replay] WARNING: task_id {task_id!r} not in manifest, skipping", flush=True)
        errors += 1
        continue

    instruction = manifest[task_id]["instruction"]
    suffix_str = row.get("suffix_str", "")
    row_enable_thinking = row.get("enable_thinking", enable_thinking)
    gen_text = row.get("generation_text", "")

    # Reconstruct full sequence: formatted_prompt + generated_tokens
    # This preserves the causal context the model had during generation.
    prompt_str = apply_chat_template(
        tokenizer, instruction + suffix_str,
        model_family=model_family, enable_thinking=row_enable_thinking
    )
    prompt_ids = tokenize_prompt(tokenizer, prompt_str)
    gen_ids = tokenizer.encode(gen_text, add_special_tokens=False)

    if not gen_ids:
        errors += 1
        continue

    max_gen_pos = min(len(gen_ids), 32)
    full_ids = prompt_ids + gen_ids[:max_gen_pos]
    gen_start = len(prompt_ids)
    positions = list(range(gen_start, gen_start + max_gen_pos))

    try:
        with torch.no_grad():
            hs = capture_selected_states(
                model,
                torch.tensor(full_ids, dtype=torch.long),
                layers=layers,
                positions=positions,
                preserve_grad=False,
            )
    except Exception as e:
        print(f"[replay] ERROR on {out_name}: {e}", flush=True)
        errors += 1
        continue

    torch.save({
        "task_id": task_id,
        "condition_label": row["condition_label"],
        "seed": row["seed"],
        "suffix_str": suffix_str,
        "gen_start": gen_start,          # absolute index of first generated token
        "gen_tokens": gen_ids[:max_gen_pos],
        "positions": positions,
        "layers": layers,
        "hidden_states": {
            str(l): {str(p): v for p, v in pdict.items()}
            for l, pdict in hs.items()
        },
    }, out_path)
    done += 1
    if done % 5 == 0:
        print(f"[replay] {done} done, {skipped} skipped, {errors} errors", flush=True)

print(f"[replay] Complete: {done} new files, {skipped} skipped, {errors} errors", flush=True)
PYEOF

echo ""
echo "--- Hidden states written ---"
ls "${RUN_DIR}/hidden_states/" | wc -l
echo "files in ${RUN_DIR}/hidden_states/"

echo ""
echo "========================================================"
echo "  Replay COMPLETE"
echo "  Date: $(date -u)"
echo "========================================================"
