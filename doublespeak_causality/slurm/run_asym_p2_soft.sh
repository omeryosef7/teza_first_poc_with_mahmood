#!/bin/bash
#SBATCH --job-name=asym_p2
#SBATCH --output=doublespeak_causality/logs/asym_p2_%j.out
#SBATCH --error=doublespeak_causality/logs/asym_p2_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# ASYMMETRY SPRINT Phase 2 (plan §6 + §19.4): continuous soft-prompt reachability.
# One ARM per job. Keep <=6 alive (plan §3.1).
#
#   sbatch --export=ALL,ASYM_OBJ=refusal,ASYM_PARAM=free,ASYM_BUDGETREL=1.0,ASYM_SEED=42 slurm/run_asym_p2_soft.sh
#   sbatch --export=ALL,ASYM_OBJ=random,ASYM_PARAM=free,ASYM_BUDGETREL=1.0,ASYM_SEED=42 slurm/run_asym_p2_soft.sh
#   sbatch --export=ALL,ASYM_OBJ=refusal,ASYM_PARAM=simplex,ASYM_SEED=42 slurm/run_asym_p2_soft.sh
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1
export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONUNBUFFERED=1

: "${ASYM_MODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${ASYM_MANIFEST:=doublespeak_causality/data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak.jsonl}"
: "${ASYM_TRAIN_MANIFEST:=doublespeak_causality/data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak_trainpool40.jsonl}"
: "${ASYM_OBJ:=refusal}"
: "${ASYM_PARAM:=free}"
: "${ASYM_BUDGETREL:=}"
: "${ASYM_STEPS:=300}"
: "${ASYM_LR:=}"
: "${ASYM_BATCH:=8}"
: "${ASYM_SEED:=42}"
: "${ASYM_TESTSPLIT:=test}"
: "${ASYM_SMOKE:=0}"
: "${ASYM_GEN:=1}"

# sensible per-parameterization default learning rates (simplex must clear the
# 2*init_scale=20 logit gap, see 37_soft_prompt_objective.py's budget check)
if [ -z "$ASYM_LR" ]; then
  case "$ASYM_PARAM" in
    free)    ASYM_LR=0.05 ;;
    simplex) ASYM_LR=0.5  ;;
  esac
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="doublespeak_causality/outputs/asym_p2_soft_${ASYM_OBJ}_${ASYM_PARAM}${ASYM_BUDGETREL:+_b$ASYM_BUDGETREL}_seed${ASYM_SEED}_${STAMP}_${SLURM_JOB_ID:-local}"

echo "=== ASYM P2 soft prompt: obj=$ASYM_OBJ param=$ASYM_PARAM budget_rel=${ASYM_BUDGETREL:-none} seed=$ASYM_SEED ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"; echo "out=$OUT"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
case "$GPU_TYPE" in
  *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";;
  *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;;
esac

EXTRA=""
[ "$ASYM_SMOKE" = "1" ] && EXTRA="--smoke"
[ "$ASYM_GEN" = "0" ] && EXTRA="$EXTRA --no-generate"
[ -n "$ASYM_BUDGETREL" ] && EXTRA="$EXTRA --budget-rel $ASYM_BUDGETREL"

python -u doublespeak_causality/scripts/asym_p2_softprompt.py \
  --model "$ASYM_MODEL" --manifest "$ASYM_MANIFEST" \
  --train-manifest "$ASYM_TRAIN_MANIFEST" --test-split "$ASYM_TESTSPLIT" \
  --objective "$ASYM_OBJ" --param "$ASYM_PARAM" \
  --steps "$ASYM_STEPS" --lr "$ASYM_LR" --batch "$ASYM_BATCH" --seed "$ASYM_SEED" \
  --out-dir "$OUT" $EXTRA
echo "=== done ==="; date
