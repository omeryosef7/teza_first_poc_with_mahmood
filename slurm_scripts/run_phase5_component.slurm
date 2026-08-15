#!/bin/bash
#SBATCH --job-name=phase5_comp
#SBATCH --output=logs/phase5_comp_%j.out
#SBATCH --error=logs/phase5_comp_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1

# =====================================================================================
# ROLE-PROBE SPRINT — Phase 5 Q3/Q4: per-example component patching (plan §9)
#
# Install each example's OWN decomposed component of its donor shift (bomb / refusal /
# remainder / full / random) at the codeword over L8-18, and measure ASR. The
# non-redundant behavioural half of Phase 5 (mean-field == Phase 4, E39). Reuses
# dc.load_model / LayerPatch / strongreject; the B9-safe example->vector map is
# unit-tested (14/14) in src/probes/phase5_patch_spec.
#
#   MODE=smoke : first LIMIT prompts, --no-judge -> manipulation check only. The GATE:
#                does per-example subtraction MOVE the downstream Bombness readout? If
#                the bomb arm doesn't lower it (necessity) do not scale.
#   MODE=full  : all test-split prompts, judged, all arms.
#   OBJECTIVE=necessity  (default): base doublespeak_prompt, subtract (sign -1)
#   OBJECTIVE=sufficiency        : base benign_prompt,    add      (sign +1)
# =====================================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"

MODE="${MODE:-smoke}"
LIMIT="${LIMIT:-6}"
COHORT="${COHORT:-clearharm}"
OBJECTIVE="${OBJECTIVE:-necessity}"
ARMS="${ARMS:-base,full,bomb,refusal,remainder,random}"
MODEL="${MODEL:-meta-llama/Llama-3.1-8B-Instruct}"
MTAG="$(echo "$MODEL" | sed 's#.*/##; s/[^A-Za-z0-9]/-/g')"
QUANTIZE="${QUANTIZE:-}"
DONOR="${DONOR:-benign}"
PEREX="${PEREX:-${DC}/outputs/phase5_perexample/comp_${COHORT}_${DONOR}.pt}"
DIRS="${DIRS:-${DC}/outputs/phase4_directions/v_bomb_${COHORT}.pt}"
if [ "$MODEL" != "meta-llama/Llama-3.1-8B-Instruct" ]; then
    DIRS="${DC}/outputs/phase4_directions/v_bomb_${MTAG}.pt"
fi

if [ "$OBJECTIVE" = "sufficiency" ]; then BASE_FIELD="benign_prompt"; else BASE_FIELD="doublespeak_prompt"; fi
STAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT="${DC}/outputs/phase5_component_${MODE}_${OBJECTIVE}_${COHORT}_${MTAG}_${STAMP}_${SLURM_JOB_ID:-local}"

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

echo "MODE=$MODE OBJECTIVE=$OBJECTIVE LIMIT=$LIMIT ARMS=$ARMS BASE_FIELD=$BASE_FIELD"
echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
NV_RC=0
NV_OUT=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>&1) || NV_RC=$?
VRAM_MB=$(printf '%s\n' "$NV_OUT" | awk 'NR==1{print $1}')
if [ "$NV_RC" -ne 0 ]; then echo "ERROR: nvidia-smi probe failed rc=${NV_RC}: ${NV_OUT}"; exit 1; fi
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then
    echo "ERROR: GPU unusable or <20GB (vram='${VRAM_MB}MB')"; exit 1; fi
echo "[guard] GPU OK ${VRAM_MB}MB"

if [ ! -f "$PEREX" ]; then echo "ERROR: per-example artifact not found: $PEREX"; exit 1; fi

cd "$DC"
EXTRA=""
if [ "$MODE" = "smoke" ]; then EXTRA="--no-judge --limit ${LIMIT}"; fi
MODEL_ARG="--model $MODEL"; [ -n "$QUANTIZE" ] && MODEL_ARG="$MODEL_ARG --quantize $QUANTIZE"
echo "PEREX=$PEREX DIRS=$DIRS OUT=$OUT"
python scripts/phase5_component_patch.py \
    --perexample "$PEREX" --directions "$DIRS" $MODEL_ARG \
    --split test --cohort "$COHORT" --base-field "$BASE_FIELD" \
    --arms "$ARMS" --out "$OUT" $EXTRA

echo "[phase5 done] $OUT"
