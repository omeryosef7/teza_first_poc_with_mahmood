#!/bin/bash
#SBATCH --job-name=phi_x13_behav
#SBATCH --output=logs/phi_x13_behav_%j.out
#SBATCH --error=logs/phi_x13_behav_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-301,n-304,n-307,n-801,n-802,n-803,n-804,n-805,t-806

# PHASE 5 (Q6) — Phi-4-mini-reasoning behavioral drift = X1 (baseline jailbreak labels, alpha=0.0,
# for the X5 concept/refusal-proj AUC join) + X3 (refusal-ablation DOSE-RESPONSE: does ablating the
# validated Phi refusal direction raise harm, and MORE than a norm-matched random control?).
# Reuses phase_behav_refusal.py verbatim (model-parameterized). StrongREJECT-judged (needs .env key).
# refusal-pt = the VALIDATED selected Phi refusal dir (L14, the only ablate+induce-valid layer).
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"
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
echo "[phi-x13] GPU ${VRAM_MB}MB $(nvidia-smi --query-gpu=name --format=csv,noheader|head -1)"

REFPT="${DC}/outputs/refusal_phi/refusal_direction_llama_L14.pt"
python doublespeak_causality/scripts/phase_behav_refusal.py \
  --bench "${DC}/data/behavioral_v3b/beh_clearharm.json" \
  --model microsoft/Phi-4-mini-reasoning \
  --refusal-pt "$REFPT" \
  --alphas 0.0,0.5,1.0 \
  --splits train,test \
  --max-new 512 \
  --enable-thinking default \
  --n 0 --seed 0
echo "[phi-x13] done $(date -u)"
