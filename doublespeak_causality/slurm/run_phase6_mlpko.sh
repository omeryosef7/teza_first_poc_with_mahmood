#!/bin/bash
#SBATCH --job-name=ds_mlpko
#SBATCH --output=doublespeak_causality/logs/ds_mlpko_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_mlpko_%j.err
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
# CAUSAL_CIRCUIT_MASTER_PLAN Phase 6 causal MLP-output write test (necessity+sufficiency)
# (necessity) with the working forced-choice readout. Windows are hardcoded (never via --export,
# which truncates comma-lists). Control coverage: DSNPROMPTS (0=all), DSGRAN (window|layer).
#   sbatch --export=ALL,DSBENCH=doublespeak_causality/data/bench/bench_curated.json,DSNPROMPTS=2,DSGRAN=window run_phase3_demoko.sh
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
: "${DSBENCH:?set DSBENCH to a data/bench/bench_<cohort>.json}"
: "${DSNPROMPTS:=0}"
: "${DSGRAN:=window}"
: "${DSPOS:=demo}"
: "${DSCOMP:=mlp_out}"
for v in DSMODEL DSBENCH DSNPROMPTS DSGRAN DSPOS DSCOMP; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
echo "=== Phase6 mlpKO: $DSBENCH n=$DSNPROMPTS gran=$DSGRAN pos=$DSPOS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase6_mlp_causal.py \
  --bench "$DSBENCH" --model "$DSMODEL" --splits dev,heldout --windows early,mid,late \
  --granularity "$DSGRAN" --positions "$DSPOS" --component "$DSCOMP" --n-prompts "$DSNPROMPTS"
echo "=== done ==="; date
