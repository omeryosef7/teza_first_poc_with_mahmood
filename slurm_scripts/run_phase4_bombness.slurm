#!/bin/bash
#SBATCH --job-name=phase4_bomb
#SBATCH --output=logs/phase4_bomb_%j.out
#SBATCH --error=logs/phase4_bomb_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1

# =====================================================================================
# ROLE-PROBE SPRINT — Phase 4: is Bombness behaviourally causal? (plan §8)
#
# Ablate v_bomb at the codeword over the write+carry band in Doublespeak prompts;
# compare ASR vs a norm-matched random ablation (specificity), with a manipulation
# check (downstream Bombness readout must drop). Reuses dc.load_model / LayerPatch /
# strongreject_scoring (same judge as phase_behav_refusal).
#
# Select via --export=ALL,MODE=<smoke|full>,LIMIT=<n>,WITH_REFUSAL=<0|1>
#   MODE=smoke : first LIMIT prompts, --no-judge (manipulation check only, fast) --
#                the §8.3 gate: does the ablation move Bombness? If not, do not scale.
#   MODE=full  : all test-split DS prompts, judged, + the refusal positive-control arm.
# =====================================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"

MODE="${MODE:-smoke}"
LIMIT="${LIMIT:-6}"
WITH_REFUSAL="${WITH_REFUSAL:-0}"
FACTORIAL="${FACTORIAL:-0}"
ALPHA="${ALPHA:-1.0}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT="${DC}/outputs/phase4_bombness_${MODE}_${STAMP}_${SLURM_JOB_ID:-local}"
DIRS="${DC}/outputs/phase4_directions/v_bomb_clearharm.pt"

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

echo "MODE=$MODE LIMIT=$LIMIT WITH_REFUSAL=$WITH_REFUSAL ALPHA=$ALPHA"
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
EXTRA=""
if [ "$MODE" = "smoke" ]; then EXTRA="--no-judge --limit ${LIMIT}"; fi
if [ "$WITH_REFUSAL" = "1" ]; then EXTRA="$EXTRA --with-refusal"; fi
if [ "$FACTORIAL" = "1" ]; then EXTRA="$EXTRA --factorial"; fi
echo "FACTORIAL=$FACTORIAL"

python scripts/phase4_bombness_intervention.py \
    --directions "$DIRS" --split test --cohort clearharm --alpha "$ALPHA" \
    --out "$OUT" $EXTRA

echo "[phase4 done] $OUT"
