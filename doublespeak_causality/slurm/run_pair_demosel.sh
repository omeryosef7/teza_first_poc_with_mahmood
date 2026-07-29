#!/bin/bash
#SBATCH --job-name=ds_pairdemosel
#SBATCH --output=doublespeak_causality/logs/ds_pairdemosel_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_pairdemosel_%j.err
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
# CAUSAL_CORE_PLAN §8.2/§8.3 + §9 (S12 slice 2): demonstration SELECTION -- causal objective
# vs behavioral objective vs random search vs the paper default, scored on HELD-OUT ASR.
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
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSBENCH:=doublespeak_causality/data/pair_benchmark/pair_carrot_bomb.json}"
: "${DSSTYLE:=news}"
: "${DSNDEMOS:=12}"
: "${DSK:=6}"
: "${DSNTRAIN:=8}"
: "${DSNEVAL:=12}"
: "${DSNRAND:=5}"
: "${DSNRANDSEARCH:=20}"
: "${DSMAXTOK:=200}"
for v in DSMODEL DSBENCH DSSTYLE DSNDEMOS DSK DSNTRAIN DSNEVAL DSNRAND DSNRANDSEARCH DSMAXTOK; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' contains a comma; sbatch --export SILENTLY TRUNCATES comma-lists."; exit 1;; esac
done
echo "=== demo selection: k=$DSK of $DSNDEMOS, train=$DSNTRAIN eval=$DSNEVAL ==="; date; hostname
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/42_demo_selection.py \
  --bench "$DSBENCH" --model "$DSMODEL" --out-root doublespeak_causality/outputs \
  --demo-style "$DSSTYLE" --n-demos "$DSNDEMOS" --k "$DSK" \
  --n-train "$DSNTRAIN" --n-eval "$DSNEVAL" --n-random "$DSNRAND" \
  --n-random-search "$DSNRANDSEARCH" --max-new-tokens "$DSMAXTOK"
echo "=== done ==="; date
