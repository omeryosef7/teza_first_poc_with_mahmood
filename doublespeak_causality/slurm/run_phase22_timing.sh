#!/bin/bash
#SBATCH --job-name=ds_p22tim
#SBATCH --output=doublespeak_causality/logs/ds_p22tim_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p22tim_%j.err
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
# RESOURCE FOOTPRINT -- measured 2026-08-05, do not re-litigate: cpus=4 mem=48G is the fast-allocating
# default (8cpu/64G sat PENDING 3h32m as 716187/716188; the SAME work at 4cpu/48G allocated in 6m32s as
# 717879/717880). Mechanism: node RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=64G
# leaves only 7 of 8 GPUs memory-feasible per node while 48G leaves all 8. --time is NOT the lever.
# Every #SBATCH line below is a DEFAULT: the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_phase22_timing.sh
# Caveat, measured over 232 logged runs: every weight-load slower than 15 min happened on n-801 (worst
# 79 min); no other L40S node ever exceeded 14 min. To skip a node DO NOT use --exclude (it NULLIFIES
# this #SBATCH --nodelist and the job lands anywhere, e.g. an RTX 3090 -- only the GPU guard catches it).
# Pass an explicit REDUCED NODELIST instead:
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_phase22_timing.sh
#
# ============================================================================================
# §22 TOKEN-TIMING harness (scripts/phase22_timing.py). Sweeps WHEN refusal-state restoration
# is applied during generation -- prefill-only / decision-token / first-token / first-k /
# all-decode -- at matched per-step magnitude (validated refusal dir @ L18, Direct donor for
# the anchor). Endpoint = ΔASR vs ds_base, paired McNemar, per timing arm + self/rand controls.
# Question: is decision-state restoration SUFFICIENT, or must the signal PERSIST through decode?
#
# STRICT L40S (generation wrapper): the GPU guard below hard-fails on any non-L40S device.
#
# SMOKE (2 items/split, verifies capture + donor-replace anchor + every TimedAdd scope + judge
#        + the alpha=0 no-op == ds_base plumbing check):
#   sbatch --export=ALL,DSN=2 slurm/run_phase22_timing.sh
# FULL (all items, frozen test included):
#   sbatch --export=ALL,DSN=0 slurm/run_phase22_timing.sh
# NOTE: comma-list values (DSSPLITS) are DEFAULTS below, NEVER via --export (which truncates at
# the first comma). To change splits, edit the default here or pass a preset-free single split.
# ============================================================================================
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
: "${DSBENCH:=doublespeak_causality/data/behavioral_v3/beh_clearharm.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSREFPT:=doublespeak_causality/outputs/refval_clearharm_20260806_051728_721957/refusal_direction_clearharm_L18.pt}"
: "${DSPATCHLAYER:=18}"        # validated L18; NEVER L9
: "${DSFIRSTK:=8}"
: "${DSMAGMODE:=perstep}"      # perstep (default, the persistence question) | integrated
: "${DSMAXNEW:=200}"
: "${DSN:=0}"
: "${DSSPLITS:=train,dev,test}"   # comma-list kept as a DEFAULT here (NEVER via --export -- truncates)
: "${DSSEED:=0}"
echo "=== phase22 timing: $DSMODEL bench=$DSBENCH L=$DSPATCHLAYER k=$DSFIRSTK mag=$DSMAGMODE maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase22_timing.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-pt "$DSREFPT" \
  --patch-layer "$DSPATCHLAYER" --first-k "$DSFIRSTK" --mag-mode "$DSMAGMODE" \
  --max-new "$DSMAXNEW" --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED" \
  ${DSPERSISTALPHA:+--persist-alpha $DSPERSISTALPHA} ${DSNOMINALLEN:+--nominal-len $DSNOMINALLEN}
echo "=== done ==="; date
