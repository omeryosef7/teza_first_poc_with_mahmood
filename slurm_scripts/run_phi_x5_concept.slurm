#!/bin/bash
#SBATCH --job-name=phi_x5_concept
#SBATCH --output=logs/phi_x5_concept_%j.out
#SBATCH --error=logs/phi_x5_concept_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-301,n-304,n-307,n-801,n-802,n-803,n-804,n-805,t-806

# PHASE 5 (Q6) — X5 on Phi-4-mini-reasoning: does the CONCEPT readout FAIL to predict jailbreak
# while the REFUSAL readout succeeds (the representation!=behavior dissociation), cross-family?
# Fits a diff-of-means concept direction on Phi (train), projects concept + Phi-refusal (L14 axis via
# refusal_phi) + norm-matched random onto held-out test doublespeak items, joins the Phi X1 behavioral
# jailbreak labels (--beh), reports per-projection AUC + geometry cos(concept,refusal). Forward-only.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"; DC="${PROJECT_DIR}/doublespeak_causality"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"; export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"; export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1; export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | awk 'NR==1{print;exit}')
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then echo "ERROR GPU <20GB"; exit 1; fi
echo "[phi-x5] GPU ${VRAM_MB}MB $(nvidia-smi --query-gpu=name --format=csv,noheader|head -1)"

BEH="${DC}/outputs/behav_refusal_clearharm_asweep0.0-1.0_20260811_103912_745950"
python doublespeak_causality/scripts/phase_x5_concept_qwen3.py \
  --model microsoft/Phi-4-mini-reasoning \
  --refusal-dir "${DC}/outputs/refusal_phi" \
  --layers 12,14,16,18,20,22 \
  --bench "${DC}/data/behavioral_v3b/beh_clearharm.json" \
  --concept-out "${DC}/outputs/concept_phi" \
  --beh "$BEH" \
  --fit-split train --eval-splits test \
  --enable-thinking false --dtype bfloat16
echo "[phi-x5] done $(date -u)"
