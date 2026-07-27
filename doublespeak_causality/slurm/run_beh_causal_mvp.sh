#!/bin/bash
#SBATCH --job-name=ds_behmvp
#SBATCH --output=doublespeak_causality/logs/ds_behmvp_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_behmvp_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# Phase 3 behavioral-causal MVP: necessity (18) + sufficiency (19) in one job (one model load).
#   sbatch --export=ALL,DSMODEL="meta-llama/Llama-3.1-8B-Instruct",DSSCREEN=doublespeak_causality/outputs/behavioral_screen_llama8b_v1,DSMATRIX=doublespeak_causality/data/behavioral_benchmark/screening_matrix_v1.json,DSMAXCLEAN=40,DSMAXBASES=40 run_beh_causal_mvp.sh
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
: "${DSSCREEN:=doublespeak_causality/outputs/behavioral_screen_llama8b_v1}"
: "${DSMATRIX:=doublespeak_causality/data/behavioral_benchmark/screening_matrix_v1.json}"
: "${DSMAXCLEAN:=40}"
: "${DSMAXBASES:=40}"
echo "=== behavioral causal MVP: $DSMODEL screen=$DSSCREEN ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
echo "--- necessity (18) ---"
python -u doublespeak_causality/18_run_behavioral_necessity.py \
  --screen-dir "$DSSCREEN" --matrix "$DSMATRIX" --model "$DSMODEL" --max-clean "$DSMAXCLEAN"
echo "--- sufficiency (19) ---"
python -u doublespeak_causality/19_run_behavioral_sufficiency.py \
  --screen-dir "$DSSCREEN" --matrix "$DSMATRIX" --model "$DSMODEL" --max-bases "$DSMAXBASES"
echo "=== done ==="; date
