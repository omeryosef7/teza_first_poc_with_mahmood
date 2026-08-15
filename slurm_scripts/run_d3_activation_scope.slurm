#!/bin/bash
#SBATCH --job-name=d3_actscope
#SBATCH --output=logs/d3_actscope_%j.out
#SBATCH --error=logs/d3_actscope_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1

# =====================================================================================
# ASYMMETRY / D3 — intervention-scope-matched activation control (gap-matrix §D3)
#
# Run the SAME refusal-direction activation ablation at three scopes on the held-out
# split, to separate MEDIUM from SCOPE (the R3/D3 confound: the published activation
# result ablates every layer/position/step; a token attack touches one layer/one
# position). alpha fixed at 1.0 — nothing is selected on the eval split for the
# activation arm, so this is a clean held-out scope comparison.
#
#   SCOPE=all_layers   : Arditi ablation (every layer, every position, every step)
#   SCOPE=single_layer : one layer (L), all positions/steps
#   SCOPE=decision     : one layer (L), decision position only, prefill only  <-- D3 control
#
# Select via --export=ALL,SCOPE=<...>,LAYER=18,SPLIT=test,VALN=<0=all|n for smoke>
# =====================================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"

SCOPE="${SCOPE:-decision}"
LAYER="${LAYER:-18}"
SPLIT="${SPLIT:-test}"
VALN="${VALN:-0}"
ALPHA="${ALPHA:-1.0}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT="${DC}/outputs/d3_actscope_${SCOPE}_L${LAYER}_${SPLIT}_${STAMP}_${SLURM_JOB_ID:-local}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "SCOPE=$SCOPE LAYER=$LAYER SPLIT=$SPLIT VALN=$VALN ALPHA=$ALPHA"
echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
NV_RC=0
NV_OUT=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>&1) || NV_RC=$?
VRAM_MB=$(printf '%s\n' "$NV_OUT" | awk 'NR==1{print $1}')
if [ "$NV_RC" -ne 0 ]; then echo "ERROR: nvidia-smi probe failed rc=${NV_RC}: ${NV_OUT}"; exit 1; fi
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then
    echo "ERROR: GPU unusable or <20GB (vram='${VRAM_MB}MB')"; exit 1; fi
echo "[guard] GPU OK ${VRAM_MB}MB"

cd "$DC"
python scripts/validate_refusal_directions.py \
    --refusal-dir outputs/refusal_alllayers \
    --families existing,clearharm \
    --ablate-scope "$SCOPE" --layers "$LAYER" --ablate-alpha "$ALPHA" \
    --eval-split "$SPLIT" --val-n-items "$VALN" \
    --out-dir "$OUT"

echo "[d3 done] $OUT"
