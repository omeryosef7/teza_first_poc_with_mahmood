#!/bin/bash
#SBATCH --job-name=asym_p1
#SBATCH --output=doublespeak_causality/logs/asym_p1_%j.out
#SBATCH --error=doublespeak_causality/logs/asym_p1_%j.err
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
# ASYMMETRY SPRINT Phase 1 (plan §5): token -> activation reachability geometry.
# Resource footprint copied from slurm/run_refusal_alllayers.sh (4cpu/48G is the
# fast-allocating shape on these nodes -- do not re-litigate, see that file's header).
#
# Usage (env vars, never comma-lists via --export -- see project memory on the
# sbatch --export comma-truncation bug; comma lists are built INSIDE this script):
#   sbatch --export=ALL,ASYM_SPLIT=train,ASYM_SMOKE=1 slurm/run_asym_p1_reach.sh
#   sbatch --export=ALL,ASYM_SPLIT=train  slurm/run_asym_p1_reach.sh
#   sbatch --export=ALL,ASYM_SPLIT=test,ASYM_NMAX=37 slurm/run_asym_p1_reach.sh
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
: "${ASYM_SPLIT:=train}"
: "${ASYM_NMAX:=40}"
: "${ASYM_NRANDOM:=100}"
: "${ASYM_NSUBTOK:=24}"
: "${ASYM_SUBBATCH:=16}"
: "${ASYM_SEED:=42}"
: "${ASYM_QUANT:=}"
: "${ASYM_SMOKE:=0}"
: "${ASYM_TAG:=}"
: "${ASYM_GPU:=l40s}"   # must be set BEFORE $OUT below, which tags the dir with it
# comma lists built HERE, never passed through --export
REFUSAL_FIT_LAYERS="18"
CONCEPT_FIT_LAYERS="9"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="doublespeak_causality/outputs/asym_p1_reach_${ASYM_SPLIT}${ASYM_TAG:+_$ASYM_TAG}${ASYM_QUANT:+_$ASYM_QUANT}_gpu${ASYM_GPU}_${STAMP}_${SLURM_JOB_ID:-local}"

echo "=== ASYM P1 reachability: split=$ASYM_SPLIT n=$ASYM_NMAX smoke=$ASYM_SMOKE ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"; echo "out=$OUT"
# GPU class guard (plan §3.1). Phase 7 compares bf16 vs 4-bit reachability, so BOTH
# precisions must run on the same class; ASYM_GPU pins it and the run dir is tagged.
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
GPU_LC="$(echo "$GPU_TYPE" | tr 'A-Z' 'a-z')"
case "$GPU_LC" in
  *"$ASYM_GPU"*) echo "GPU ok: $GPU_TYPE (required class: $ASYM_GPU)";;
  *) echo "ERROR need $ASYM_GPU got '$GPU_TYPE'"; exit 1;;
esac

EXTRA=""
[ "$ASYM_SMOKE" = "1" ] && EXTRA="--smoke"
[ -n "$ASYM_QUANT" ] && EXTRA="$EXTRA --quantize $ASYM_QUANT"

python -u doublespeak_causality/scripts/asym_p1_reachability.py \
  --model "$ASYM_MODEL" --manifest "$ASYM_MANIFEST" --split "$ASYM_SPLIT" \
  --n-max "$ASYM_NMAX" --n-random "$ASYM_NRANDOM" --random-seed "$ASYM_SEED" \
  --refusal-fit-layers "$REFUSAL_FIT_LAYERS" --concept-fit-layers "$CONCEPT_FIT_LAYERS" \
  --n-sub-tokens "$ASYM_NSUBTOK" --sub-batch "$ASYM_SUBBATCH" \
  --out-dir "$OUT" $EXTRA
echo "=== done ==="; date
