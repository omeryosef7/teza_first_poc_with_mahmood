#!/bin/bash
#SBATCH --job-name=f13_attn_probe
#SBATCH --output=logs/f13_attn_probe_%A_%a.out
#SBATCH --error=logs/f13_attn_probe_%A_%a.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-805,t-806,n-804,n-602,n-301
#
# PHASE-F1.3 ATTENTION-TO-SPAN PROBE (docs/COT_HIJACKING_EXACT_MECHANISM_REPORT.md §6.2).
# INTERPRETABILITY ONLY: one forward pass (output_attentions=True, EAGER attention) over the EXISTING
# Phase-F1.1-annotated attack PROMPTS; measures prompt-internal attention mass among the labelled span
# components at generation start, contrasting successful vs failed attacks on the DISCOVERY split.
# NO new text is generated; no new attacks are created. Reuses the verified CPU stack
# (scripts/phase_f_attention_probe.py core + scripts/phase_f_probe_driver.py orchestration).
#
# Array: task 0 = Qwen3-14B, task 1 = Phi-4-mini-reasoning.
set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs results

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

# poc_stage2 = torch + transformers + our modules import cleanly (same env as Gate-1 eval / Gate-3).
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
echo "[f13] conda env: $CONDA_ENV ($(python -c 'import torch;print("torch",torch.__version__)'))"

# Non-fatal GPU banner (constraint=l40s already enforces the type).
GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1 || true)"
echo "[f13] GPU: ${GPU_NAME:-unknown}  git=$(git rev-parse HEAD 2>/dev/null || echo unknown)  date=$(date -u)"

case "${SLURM_ARRAY_TASK_ID:-0}" in
  0)
    MODEL="Qwen/Qwen3-14B"
    SPANS="outputs/phase_f_cot_spans/Qwen_Qwen3-14B_spans.jsonl"
    ATTACKED="outputs/phase5_qwen3_cot/phase4_cot_hf_Qwen_Qwen3-14B_dev25.jsonl"
    OUT="results/COT_F13_qwen3_14b.csv"
    ;;
  1)
    MODEL="microsoft/Phi-4-mini-reasoning"
    SPANS="outputs/phase_f_cot_spans/microsoft_Phi-4-mini-reasoning_spans.jsonl"
    ATTACKED="outputs/phase4_hf_local/phase4_cot_hf_microsoft_Phi-4-mini-reasoning_dev25.jsonl"
    OUT="results/COT_F13_phi4_mini.csv"
    ;;
  *) echo "[f13] unknown array task ${SLURM_ARRAY_TASK_ID}"; exit 1 ;;
esac

echo "[f13] model=$MODEL spans=$SPANS attacked=$ATTACKED out=$OUT"
python -u scripts/phase_f_run_probe.py \
    --spans "$SPANS" \
    --attacked "$ATTACKED" \
    --model "$MODEL" \
    --out-csv "$OUT" \
    --confound-log \
    --dtype bfloat16 \
    --device cuda

echo "[f13] DONE task ${SLURM_ARRAY_TASK_ID} date=$(date -u)"
