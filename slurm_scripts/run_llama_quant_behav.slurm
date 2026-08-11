#!/bin/bash
#SBATCH --job-name=llama_quant_behav
#SBATCH --output=logs/llama_quant_behav_%j.out
#SBATCH --error=logs/llama_quant_behav_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=10:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-301,n-304,n-307,n-801,n-802,n-803,n-804,n-805,t-806

# PHASE 6 (Q7) — quantization robustness of the refusal-ablation behavioral effect on Llama-3.1-8B.
# Same refusal direction (L18, the validated readout axis) + same doublespeak bench + same alpha
# dose grid as the bf16 run, but the MODEL is loaded under bnb quantization (QUANT env: 8bit|4bit).
# Endpoint: does ablating the refusal direction move behavior the SAME way under quantization as at
# bf16 (dose-response shape + vs norm-matched random)? Reuses phase_behav_refusal.py verbatim.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"; DC="${PROJECT_DIR}/doublespeak_causality"
QUANT="${QUANT:?set QUANT=bf16|8bit|4bit}"   # bf16 => no --quantize (full-precision control)
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"; export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"; export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1; export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | awk 'NR==1{print;exit}')
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then echo "ERROR GPU <20GB"; exit 1; fi
if [ -z "${OPENAI_API_KEY:-}" ]; then echo "WARN OPENAI_API_KEY unset -> StrongREJECT null"; fi
echo "[quant $QUANT] GPU ${VRAM_MB}MB $(nvidia-smi --query-gpu=name --format=csv,noheader|head -1)"

REFPT="${DC}/outputs/stage_gcg_full/refusal_direction_llama_L18.pt"
QFLAG=(); if [ "$QUANT" != "bf16" ] && [ "$QUANT" != "none" ]; then QFLAG=(--quantize "$QUANT"); fi
python doublespeak_causality/scripts/phase_behav_refusal.py \
  --bench "${DC}/data/behavioral_v3b/beh_clearharm.json" \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --refusal-pt "$REFPT" \
  "${QFLAG[@]}" \
  --alphas 0.0,0.5,1.0 \
  --splits test \
  --max-new 220 \
  --enable-thinking default \
  --n 0 --seed 0
echo "[quant $QUANT] done $(date -u)"
