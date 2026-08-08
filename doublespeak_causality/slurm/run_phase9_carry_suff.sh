#!/bin/bash
#SBATCH --job-name=ds_p9suf
#SBATCH --output=doublespeak_causality/logs/ds_p9suf_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p9suf_%j.err
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
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_phase9_carry_suff.sh
# To avoid a node, DO NOT use --exclude: passing --exclude on the sbatch line NULLIFIES this
# #SBATCH --nodelist and the job then lands anywhere in the partition (that is how jobs 721954/721955
# escaped to an RTX 3090). Pass an explicit REDUCED nodelist instead, e.g. to skip n-801:
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_phase9_carry_suff.sh
#
# Phase 9 -- BEHAVIORAL SUFFICIENCY of the L14-21 carry heads DURING GENERATION. Install the DS
# carry-head z-state into a matched CLEAN (neutral/direct) receiver at the DECISION position and
# generate; endpoint ΔASR vs the clean-context baseline (StrongREJECT), paired McNemar. 5 arms
# (baseline / carry_install / rand_install / self_install / write_carry) = 5 generations/item.
# STRICT L40S: this is a real harmful-generation job (throughput + flash-attn on L40S). The install
# hooks (pc.ZHeadPatch / ds_common.LayerPatch) target fixed prompt positions -> fire on prefill,
# skipped on KV-cached decode steps (decode-safe by construction; see script docstring §DECODE-SAFETY).
#   full : sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSRECIP=neutral,DSMAXNEW=220,DSN=0 slurm/run_phase9_carry_suff.sh
#   smoke: sbatch --export=ALL,DSN=2 slurm/run_phase9_carry_suff.sh
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
: "${DSRECIP:=neutral}"        # neutral|direct (single value, no comma)
: "${DSWLAYER:=9}"
: "${DSMAXNEW:=220}"
: "${DSN:=0}"
: "${DSSPLITS:=train,test}"    # comma-list kept as a DEFAULT here (not via --export, which truncates)
: "${DSSEED:=0}"
: "${DSSAVEGEN:=1}"            # 1 = write gens.jsonl (default); 0 = --no-save-gen
for v in DSBENCH DSMODEL DSRECIP DSWLAYER DSMAXNEW DSN DSSEED; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
DSFLAGS=""
[ "$DSSAVEGEN" = "1" ] && DSFLAGS="$DSFLAGS --save-gen" || DSFLAGS="$DSFLAGS --no-save-gen"
echo "=== phase9 carry-suff: $DSMODEL bench=$DSBENCH recip=$DSRECIP wlayer=$DSWLAYER maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS flags=$DSFLAGS ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
# STRICT L40S -- generation job. GPU_ALL keeps the whole newline-separated list (no head -> no SIGPIPE
# under pipefail), then GPU_TYPE = first line only.
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase9_carry_sufficiency.py \
  --bench "$DSBENCH" --model "$DSMODEL" --recipient "$DSRECIP" --write-layer "$DSWLAYER" \
  --max-new "$DSMAXNEW" --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED" $DSFLAGS
echo "=== done ==="; date
