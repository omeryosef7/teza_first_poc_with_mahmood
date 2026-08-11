#!/bin/bash
#SBATCH --job-name=phi_x2_ref
#SBATCH --output=logs/phi_x2_ref_%j.out
#SBATCH --error=logs/phi_x2_ref_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-301,n-304,n-307,n-801,n-802,n-803,n-804,n-805,t-806

# PHASE 5 (Q6) — X2 refusal side on THIRD family Phi-4-mini-reasoning.
# Build refusal directions (harmful=direct vs harmless=neutral) at multiple layers on Phi's own
# activations, using the SAME model-agnostic bench that Llama used (pair_carrot_bomb.json:
# direct/neutral fields; n_harmful=60/n_harmless=20). --validate runs the induced-refusal check.
# Phi is ~3.8B -> min-VRAM guard (>=20GB) accepts any healthy GPU.
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
echo "GIT: $(git rev-parse HEAD)  DATE: $(date -u)"
echo "[phi-x2] GPU ${VRAM_MB}MB $(nvidia-smi --query-gpu=name --format=csv,noheader|head -1)"

BENCH="${DC}/data/pair_benchmark/pair_carrot_bomb.json"
OUT="${DC}/outputs/refusal_phi"
mkdir -p "$OUT"
python doublespeak_causality/build_refusal_direction_llama.py \
  --model microsoft/Phi-4-mini-reasoning \
  --bench "$BENCH" \
  --layers 12,14,16,18,20,22 \
  --out "$OUT" \
  --dtype bfloat16 \
  --validate --val-n-items 20 \
  --enable-thinking default
echo "[phi-x2] done $(date -u)"
