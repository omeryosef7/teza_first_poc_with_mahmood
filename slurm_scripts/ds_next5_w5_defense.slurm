#!/bin/bash

#SBATCH --job-name=ds_n5_w5def
#SBATCH --output=logs/ds_n5_w5def_%j.out
#SBATCH --error=logs/ds_n5_w5def_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# NEXT5 W5 — mechanism-derived defense: ADD +alpha*v_refusal at late (use) layers throughout
# generation, measure Doublespeak malicious_rate drop vs benign over-refusal cost. Args with
# shell metachars (';' in --layer-sets) are quoted INLINE here, never via unquoted $CMD.
#
# Usage:  sbatch slurm_scripts/ds_next5_w5_defense.slurm
# Overrides: BENCH=, REFUSAL_PT=, N_ITEMS=, ALPHAS=, LAYER_SETS=, MAX_NEW_TOKENS=

set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
DSC="$PROJECT_DIR/doublespeak_causality"; CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MODEL="meta-llama/Llama-3.1-8B-Instruct"
BENCH="${BENCH:-$DSC/data/pair_benchmark/pair_carrot_bomb.json}"
REFUSAL_PT="${REFUSAL_PT:-$DSC/outputs/stage_gcg_full/refusal_direction_llama_L18.pt}"
N_ITEMS="${N_ITEMS:-30}"
ALPHAS="${ALPHAS:-8,16}"
LAYER_SETS="${LAYER_SETS:-late:24,26,28,30;midfit:14,16,18,20}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-200}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface" HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch" TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" PYTHONUNBUFFERED=1

echo "=== NEXT5 W5 mechanism-derived defense ==="; date; hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local} N_ITEMS=$N_ITEMS ALPHAS=$ALPHAS LAYER_SETS=$LAYER_SETS"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true); echo "GPU: $GPU_NAME"
echo "$GPU_NAME" | grep -qi "L40S" || { echo "FATAL: GPU not L40S ($GPU_NAME)" >&2; exit 1; }
[ -e "$BENCH" ] || { echo "FATAL: missing bench $BENCH" >&2; exit 1; }
[ -e "$REFUSAL_PT" ] || { echo "FATAL: missing refusal pt $REFUSAL_PT" >&2; exit 1; }
cd "$DSC"

python next5_w5_defense_eval.py --bench "$BENCH" --refusal-pt "$REFUSAL_PT" --model "$MODEL" \
    --n-items "$N_ITEMS" --alphas "$ALPHAS" --layer-sets "$LAYER_SETS" \
    --max-new-tokens "$MAX_NEW_TOKENS" --seed 0

echo "=== DONE ==="; date
