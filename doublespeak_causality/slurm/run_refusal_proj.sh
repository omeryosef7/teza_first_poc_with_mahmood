#!/bin/bash
#SBATCH --job-name=ds_refproj
#SBATCH --output=doublespeak_causality/logs/ds_refproj_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_refproj_%j.err
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
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_refusal_proj.sh
# n-801 is back in the nodelist (a full gpu:l40s:8 node = 1/6 of our L40S capacity). Caveat, measured
# over 232 logged runs: every weight-load slower than 15 min happened on n-801 (worst 79 min), while no
# other L40S node ever exceeded 14 min. To avoid a node, DO NOT use --exclude: passing --exclude on the
# sbatch line NULLIFIES this #SBATCH --nodelist and the job then lands anywhere in the partition. That
# happened on 2026-08-06 (jobs 721954/721955 -> n-306, an RTX 3090); only the GPU guard below caught it.
# Pass an explicit REDUCED NODELIST instead, e.g. to skip n-801:
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/<wrapper>.sh
#
# Behavioral necessity of the L14-21 carry heads: baseline vs carry-ablated vs random-ablated
# DS generation, StrongReject-judged. (n-801 was previously excluded for slow weight loading -- see the nodelist note above.)
#   sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSMAXNEW=220,DSN=0,DSSPLITS=train,test run_behav_carry.sh
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
: "${DSBENCH:=doublespeak_causality/data/behavioral/beh_clearharm.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSMAXNEW:=220}"
: "${DSN:=0}"
: "${DSSPLITS:=train,test}"   # comma-list kept as a DEFAULT here (not via --export, which truncates)
: "${DSREFDIR:=doublespeak_causality/outputs/refusal_alllayers}"
: "${DSALPHAS:=4,8,12}"
: "${DSSEED:=0}"
: "${DSENABLETHINK:=default}"   # thinking-model control (Qwen3)
echo "=== behav carry: $DSMODEL bench=$DSBENCH maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
# refproj is FORWARD-ONLY (no generation) -> DSGPUALLOW=23gb relaxes to the >=23GB Ampere+ allowlist.
if [ "${DSGPUALLOW:-}" = "23gb" ]; then
  GM="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null|head -1|grep -oE '[0-9]+'|head -1)"; GM="${GM:-0}"
  case "$GPU_TYPE" in *L40S*|*A5000*|*a5000*|*A6000*|*a6000*|*A100*|*A40*|*H100*|*H200*|*L40*|*3090*|*4090*) [ "$GM" -ge 23000 ] && echo "GPU ok (23gb): $GPU_TYPE ${GM}MiB" || { echo "ERR <23GB"; exit 1; };; *) echo "ERR gpu $GPU_TYPE"; exit 1;; esac
else case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac; fi
python -u doublespeak_causality/scripts/phase_refusal_projection.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-dir "$DSREFDIR" --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED" --enable-thinking "$DSENABLETHINK"
echo "=== done ==="; date
