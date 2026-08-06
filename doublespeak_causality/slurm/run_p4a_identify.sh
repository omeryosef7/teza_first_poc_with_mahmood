#!/bin/bash
#SBATCH --job-name=ds_p4aid
#SBATCH --output=doublespeak_causality/logs/ds_p4aid_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p4aid_%j.err
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
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_p4a_identify.sh
#
# P4a IDENTIFICATION (plan §5 P4a): per-head attention mass from the query codeword back to the demo
# codewords, on a ClearHarm bench. ZERO NEW ANALYSIS CODE -- next7_attention_retrieval.py already
# computes exactly this; it had simply never been pointed at a ClearHarm bench, so the project's only
# induction-head evidence is a band-mean 3.508x ratio on n=12 of the OLD carrot/bomb pair.
# This replaces that with n=44 ClearHarm train items. Still head-averaged (that is P4a's remaining gap),
# but no longer a single-pair artifact.
#   sbatch slurm/run_p4a_identify.sh
#   sbatch --export=ALL,DSSPLIT=heldout,DSNITEMS=42 slurm/run_p4a_identify.sh
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
: "${DSBENCH:?set DSBENCH}"; : "${DSNPROMPTS:=0}"; : "${DSLAYERS:=all}"; : "${DSMODE:=perhead}"
for v in DSMODEL DSBENCH DSNPROMPTS DSLAYERS DSMODE; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates."; exit 1;; esac
done
if [ "$DSLAYERS" = "all" ]; then LAYER_ARG="";
else A="${DSLAYERS%-*}"; B="${DSLAYERS#*-}"; LAYER_ARG="--layers $(seq -s, "$A" "$B")"; fi
echo "=== Phase4 edgeKO: $DSBENCH n=$DSNPROMPTS layers=$DSLAYERS ($LAYER_ARG) ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
: "${DSBENCH:=doublespeak_causality/data/bench/bench_clearharm.json}"
: "${DSREADOUT:=fixed}"
: "${DSSPLIT:=dev}"
: "${DSNITEMS:=44}"
: "${DSBANDLO:=7}"
: "${DSBANDHI:=14}"
for v in DSBENCH DSREADOUT DSSPLIT DSNITEMS DSBANDLO DSBANDHI; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
echo "=== P4a identify: bench=$DSBENCH readout=$DSREADOUT split=$DSSPLIT n=$DSNITEMS band=$DSBANDLO-$DSBANDHI ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/next7_attention_retrieval.py \
  --bench "$DSBENCH" --readout "$DSREADOUT" --split "$DSSPLIT" \
  --n-items "$DSNITEMS" --band-lo "$DSBANDLO" --band-hi "$DSBANDHI"
echo "=== done ==="; date
