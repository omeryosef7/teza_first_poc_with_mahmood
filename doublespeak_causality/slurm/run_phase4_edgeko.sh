#!/bin/bash
#SBATCH --job-name=ds_edgeko
#SBATCH --output=doublespeak_causality/logs/ds_edgeko_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_edgeko_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# CAUSAL_CIRCUIT_MASTER_PLAN Phase 4.2: surgical per-head query->demo attention-edge knockout (eager).
# DSLAYERS = "all" or an inclusive dash-range "A-B" (expanded to a comma list INSIDE this script so the
# comma never passes through --export, which truncates comma-lists). DSNPROMPTS = examples per split.
#   sbatch --export=ALL,DSBENCH=...,DSNPROMPTS=2,DSLAYERS=8-11 run_phase4_edgeko.sh   # smoke
#   sbatch --export=ALL,DSBENCH=...,DSNPROMPTS=25,DSLAYERS=all run_phase4_edgeko.sh   # full
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
: "${DSBENCH:?set DSBENCH}"; : "${DSNPROMPTS:=0}"; : "${DSLAYERS:=all}"
for v in DSMODEL DSBENCH DSNPROMPTS DSLAYERS; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates."; exit 1;; esac
done
if [ "$DSLAYERS" = "all" ]; then LAYER_ARG="";
else A="${DSLAYERS%-*}"; B="${DSLAYERS#*-}"; LAYER_ARG="--layers $(seq -s, "$A" "$B")"; fi
echo "=== Phase4 edgeKO: $DSBENCH n=$DSNPROMPTS layers=$DSLAYERS ($LAYER_ARG) ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase4_edge_knockout.py \
  --bench "$DSBENCH" --model "$DSMODEL" --splits dev,heldout --n-prompts "$DSNPROMPTS" $LAYER_ARG
echo "=== done ==="; date
