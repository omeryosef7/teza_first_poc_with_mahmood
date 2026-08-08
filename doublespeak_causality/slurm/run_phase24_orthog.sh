#!/bin/bash
#SBATCH --job-name=ds_orthog
#SBATCH --output=doublespeak_causality/logs/ds_orthog_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_orthog_%j.err
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
# RESOURCE FOOTPRINT -- cpus=4 mem=48G is the fast-allocating default for the 8B model (measured
# 2026-08-05; --mem=64G leaves only 7/8 GPUs memory-feasible per node, 48G leaves all 8). --time is
# NOT the allocation lever. Every #SBATCH line is a DEFAULT the matching sbatch flag overrides with no
# file edit, e.g. to skip the slow n-801 node pass an explicit REDUCED nodelist (NOT --exclude, which
# nullifies #SBATCH --nodelist and lets the job land on a non-L40S GPU):
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_phase24_orthog.sh
#
# §24 ORTHOGONALIZATION: inject concept / refusal / concept⊥refusal / refusal⊥concept / both into the
# Doublespeak generation; measure concept readout, refusal projection, and attack ASR per arm. Goal:
# behavioral control survives removing the concept overlap from refusal -> it lives in the refusal comp.
# SMOKE (2 items/split -- comma-lists are DEFAULTS below, NEVER via --export which truncates at comma):
#   sbatch --export=ALL,DSN=2 slurm/run_phase24_orthog.sh
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs doublespeak_causality/outputs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"; export PYTHONUNBUFFERED=1
: "${DSBENCH:=doublespeak_causality/data/behavioral_v3b/beh_clearharm.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSN:=0}"
: "${DSSPLITS:=train,test}"     # comma-list kept as a DEFAULT here (not via --export, which truncates)
# Concept axis (unified_directions, train/dev-fit) + refusal axis (validated refval clearharm, train-fit).
: "${DSUNIFIED:=doublespeak_causality/outputs/unified_directions/clearharm.npz}"
: "${DSREFPTDIR:=doublespeak_causality/outputs/refval_clearharm_20260806_051728_721957}"
: "${DSLAYERS:=18}"             # validated decoder layer(s); comma-list = DEFAULT (never --export)
: "${DSALPHAS:=8.0}"            # absolute residual-space add magnitude(s); comma-list = DEFAULT
: "${DSMAXNEW:=200}"
: "${DSSEED:=0}"
echo "=== orthog: $DSMODEL bench=$DSBENCH layers=$DSLAYERS alphas=$DSALPHAS maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase24_orthogonalization.py \
  --bench "$DSBENCH" --model "$DSMODEL" --unified-npz "$DSUNIFIED" --refusal-pt-dir "$DSREFPTDIR" \
  --layers "$DSLAYERS" --alphas "$DSALPHAS" --max-new "$DSMAXNEW" --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED"
echo "=== done ==="; date
