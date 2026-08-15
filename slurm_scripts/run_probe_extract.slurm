#!/bin/bash
#SBATCH --job-name=probe_extract
#SBATCH --output=logs/probe_extract_%j.out
#SBATCH --error=logs/probe_extract_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1

# =====================================================================================
# ROLE-PROBE SPRINT — Phase 1 Bombness activation extraction (plan §5, §2A.5).
#
# Extracts resid_post (== hidden_states[L+1], D1 space) at the query codeword and the
# decision token, all layers, for the v3 binding conditions. Reuses the validated
# ds_common.load_model + pair_common.capture_components path — no new hooks.
#
# Select via --export=ALL,MODE=<smoke|full>,COHORT=<clearharm|generated|all>
#   MODE=smoke : first LIMIT items only (default 24) — the §2A.5 pipeline sanity check:
#                proves positions resolve, activations extract, and a probe fits above
#                chance end-to-end, before any full extraction is trusted.
#   MODE=full  : all items for the chosen cohort.
#
# GPU guard mirrors run_gcg_perprompt.slurm (the unreachable-error-branch fix that
# killed 757702 is kept). L40S preferred; 20GB+ required (8B bf16 fits easily).
# =====================================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"

MODE="${MODE:-smoke}"
COHORT="${COHORT:-clearharm}"
CONDITIONS="${CONDITIONS:-doublespeak,benign,neutral}"
LIMIT="${LIMIT:-24}"
REVISION="${REVISION:-}"           # pin the HF revision for the run (recorded in RUNMETA)
MODEL="${MODEL:-meta-llama/Llama-3.1-8B-Instruct}"
MTAG="$(echo "$MODEL" | sed 's#.*/##; s/[^A-Za-z0-9]/-/g')"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
OUT="${DC}/outputs/probe_bombness_${MODE}_${COHORT}_${MTAG}_${STAMP}_${SLURM_JOB_ID:-local}"

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

echo "MODE=$MODE COHORT=$COHORT CONDITIONS=$CONDITIONS LIMIT=$LIMIT"
echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
NV_RC=0
NV_OUT=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>&1) || NV_RC=$?
VRAM_MB=$(printf '%s\n' "$NV_OUT" | awk 'NR==1{print $1}')
if [ "$NV_RC" -ne 0 ]; then echo "ERROR: nvidia-smi probe failed rc=${NV_RC}: ${NV_OUT}"; exit 1; fi
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then
    echo "ERROR: GPU unusable or <20GB (vram='${VRAM_MB}MB')"; exit 1; fi
echo "[guard] GPU OK ${VRAM_MB}MB"

COHORT_ARG=""; [ "$COHORT" != "all" ] && COHORT_ARG="--cohort $COHORT"
LIMIT_ARG="";  [ "$MODE" = "smoke" ] && LIMIT_ARG="--limit $LIMIT"
REV_ARG="";    [ -n "$REVISION" ] && REV_ARG="--revision $REVISION"
SPACE_ARG=""; [ -n "${SPACE:-}" ] && SPACE_ARG="--space $SPACE"
QUANT_ARG=""; [ -n "${QUANTIZE:-}" ] && QUANT_ARG="--quantize $QUANTIZE"
# CORPUS override (Phase 10 §14.3: second corpus = AdvBench). Default keeps clearharm_v3.
CORPUS_ARG=""; [ -n "${CORPUS:-}" ] && CORPUS_ARG="--corpus $CORPUS"

cd "$DC"
echo "MODEL=$MODEL CORPUS=${CORPUS:-<default clearharm_v3>}"
python -m src.probes.activation_extraction \
    --out "$OUT" --model "$MODEL" $COHORT_ARG $CORPUS_ARG --conditions "$CONDITIONS" $LIMIT_ARG $REV_ARG $QUANT_ARG $SPACE_ARG

echo "[extract done] $OUT"

# Smoke mode: immediately fit a probe on the extracted slice to prove the pipeline
# end-to-end (the §2A.5 sanity check). Above-chance dev AUC on a handful of examples
# is the pass criterion; a full Gate-1 evaluation is a later, larger run.
if [ "$MODE" = "smoke" ]; then
    python -m src.probes.smoke_fit --run "$OUT" || echo "[smoke_fit] non-fatal: see log"
fi
echo "[all done] $OUT"
