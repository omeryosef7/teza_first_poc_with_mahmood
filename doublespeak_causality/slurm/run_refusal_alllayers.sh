#!/bin/bash
#SBATCH --job-name=ds_refusal32
#SBATCH --output=doublespeak_causality/logs/ds_refusal32_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_refusal32_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- measured 2026-08-05, do not re-litigate: cpus=4 mem=48G is the fast-allocating
# default (8cpu/64G sat PENDING 3h32m as 716187/716188; the SAME work at 4cpu/48G allocated in 6m32s as
# 717879/717880). Mechanism: node RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=64G
# leaves only 7 of 8 GPUs memory-feasible per node while 48G leaves all 8. --time is NOT the lever.
# Every #SBATCH line below is a DEFAULT: the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_refusal_alllayers.sh
#
# CAUSAL_CIRCUIT_MASTER_PLAN Phase 2.2 + granularity A: build refusal_direction[L] for ALL 32
# layers (existing artifact only covered L12-20). Layers are hardcoded via seq to AVOID the
# sbatch --export comma-truncation bug (project memory). Optional validation via DSVALIDATE=1.
#   sbatch run_refusal_alllayers.sh                 # build 32-layer direction vectors (fast)
#   sbatch --export=ALL,DSVALIDATE=1 run_refusal_alllayers.sh   # + per-layer ablate/induce validation
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
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSBENCH:=doublespeak_causality/data/pair_benchmark/pair_carrot_bomb.json}"
: "${DSVALIDATE:=0}"
LAYERS="$(seq -s, 0 31)"   # 0,1,...,31 built INSIDE the script (never via --export)
echo "=== refusal direction all-32-layer build: $DSMODEL ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
VAL_ARG=""; [ "$DSVALIDATE" = "1" ] && VAL_ARG="--validate"
python -u doublespeak_causality/build_refusal_direction_llama.py \
  --bench "$DSBENCH" --model "$DSMODEL" --layers "$LAYERS" \
  --out doublespeak_causality/outputs/refusal_alllayers $VAL_ARG
echo "=== done ==="; date
