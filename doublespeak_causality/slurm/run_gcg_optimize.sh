#!/bin/bash
#SBATCH --job-name=ds_gcgopt
#SBATCH --output=doublespeak_causality/logs/ds_gcgopt_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_gcgopt_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# Track B (temporal-GCG) step 4: optimize a suffix on the Neutral prompt.
#   TEMPORAL: DSLAMBDA>0 + DSCACHEDIR=mixed cache (early-benign/late-harmful repr_loss).
#   BASELINE: DSLAMBDA=0 (task-only GCG), no reference cache.
# Compare held-out ASR (evaluate_optimized_suffixes) → Level-5 test (temporal > standard).
#   sbatch --export=ALL,DSMANIFEST=doublespeak_causality/data/gcg/curated_qwen3_neutral.jsonl,DSOUTDIR=doublespeak_causality/outputs/gcg/opt_qwen3_temporal,DSRUNID=qwen3_temporal,DSLAMBDA=0.3,DSCACHEDIR=doublespeak_causality/outputs/gcg/cache_qwen3_mixed,DSSTEPS=200 run_gcg_optimize.sh
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"; export PYTHONUNBUFFERED=1
: "${DSMANIFEST:?set DSMANIFEST}"
: "${DSOUTDIR:?set DSOUTDIR}"
: "${DSRUNID:?set DSRUNID}"
: "${DSLAMBDA:=0.0}"
: "${DSCACHEDIR:=}"
: "${DSSTEPS:=200}"
: "${DSSPLIT:=train}"
: "${DSFAMILY:=qwen3}"
: "${DSMODEL:=Qwen/Qwen3-14B}"
: "${DSNOTHINK:=1}"
NOTHINK_ARG=""; [ "$DSNOTHINK" = "1" ] && NOTHINK_ARG="--no-thinking"
REPR_ARGS=""
# reference cache only when the repr term is active (lambda>0)
if [ "$(python -c "print(1 if float('$DSLAMBDA')>0 else 0)")" = "1" ]; then
  : "${DSCACHEDIR:?DSLAMBDA>0 requires DSCACHEDIR (mixed reference cache)}"
  REPR_ARGS="--lambda-repr $DSLAMBDA --reference-cache-dir $DSCACHEDIR --repr-positions 3 --repr-layers 0,5,10,15,20,25,30,35"
fi
echo "=== gcg optimize: run=$DSRUNID lambda_repr=$DSLAMBDA split=$DSSPLIT steps=$DSSTEPS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u -m poc_stage_gcg_early.run_optimization \
  --run-id "$DSRUNID" --model-family "$DSFAMILY" --model-name-or-path "$DSMODEL" \
  --manifest "$DSMANIFEST" --output-dir "$DSOUTDIR" \
  --suffix-length 16 --n-steps "$DSSTEPS" --split "$DSSPLIT" \
  --no-filter-cand $NOTHINK_ARG $REPR_ARGS
echo "=== done ==="; date
