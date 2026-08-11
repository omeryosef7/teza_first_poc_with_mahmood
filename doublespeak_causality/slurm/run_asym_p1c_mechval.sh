#!/bin/bash
#SBATCH --job-name=asym_p1c
#SBATCH --output=doublespeak_causality/logs/asym_p1c_%j.out
#SBATCH --error=doublespeak_causality/logs/asym_p1c_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# ASYMMETRY SPRINT Phase 1c (plan §19.1 a-d + §19.2): extended mechanistic-validity readout
# over ALL THREE SEEDS, both pools (frozen train pool + held-out test), a L10-L24 layer
# sweep, and both target positions. Forward passes only -- no optimization.
#
#   sbatch --export=ALL,ASYM_SMOKE=1 slurm/run_asym_p1c_mechval.sh
#   sbatch slurm/run_asym_p1c_mechval.sh
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

: "${ASYM_SMOKE:=0}"
: "${ASYM_NMAX:=0}"
: "${ASYM_NRANDSUF:=0}"
G="outputs/stage_gcg_full"
EVAL_MANIFEST="doublespeak_causality/data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak.jsonl"
TRAIN_MANIFEST="doublespeak_causality/data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak_trainpool40.jsonl"
# comma list built HERE, never via --export (project memory: sbatch --export comma bug)
REFUSAL_LAYERS="$(seq -s, 10 24)"
CONCEPT_LAYERS="9,16"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="doublespeak_causality/outputs/asym_p1c_mechval_${STAMP}_${SLURM_JOB_ID:-local}"
echo "=== ASYM P1c extended mech-validity (all seeds, both pools, L10-24) ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"; echo "out=$OUT"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
case "$GPU_TYPE" in
  *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";;
  *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;;
esac

EXTRA=""
if [ "$ASYM_SMOKE" = "1" ]; then
  REFUSAL_LAYERS="18"; CONCEPT_LAYERS="9"; EXTRA="--n-max 20"
elif [ "$ASYM_NMAX" != "0" ]; then
  EXTRA="--n-max $ASYM_NMAX"
fi

ARMS=""
for s in 42 43 44; do
  ARMS="$ARMS --arm vanilla_ds_s${s}=$G/phase9b_v3_arm04_vanilla_ds_seed${s}"
  ARMS="$ARMS --arm refusal_s${s}=$G/phase9b_v3_arm07_refusal_down_L18_seed${s}"
  ARMS="$ARMS --arm refusal_rand_s${s}=$G/phase9b_v3_arm07r_refusal_rand_L18_seed${s}"
  ARMS="$ARMS --arm concept_s${s}=$G/phase9b_v3_arm06_concept_up_L9_seed${s}"
  ARMS="$ARMS --arm concept_rand_s${s}=$G/phase9b_v3_arm06r_concept_rand_L9_seed${s}"
done

python -u doublespeak_causality/scripts/asym_p1c_mech_validity_ext.py \
  --manifest "${EVAL_MANIFEST}:test" \
  --manifest "${TRAIN_MANIFEST}:train" \
  --refusal-fit-layers "$REFUSAL_LAYERS" --concept-fit-layers "$CONCEPT_LAYERS" \
  $ARMS --n-random-suffix "$ASYM_NRANDSUF" --out-dir "$OUT" $EXTRA
echo "=== done ==="; date
