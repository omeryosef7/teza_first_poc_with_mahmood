#!/bin/bash
#SBATCH --job-name=percot_rerank
#SBATCH --output=logs/percot_rerank_%j.out
#SBATCH --error=logs/percot_rerank_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301

# Staged ASR-rerank harness for the per-behavior Native-CoT pilot.
# Loads Qwen3-14B once; scores per-behavior candidates by real StrongREJECT ASR.
# Env: BEHAVIORS=comma,list  (optional; default=auto-discover completed runs)
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"; BEHAVIORS="${BEHAVIORS:-}"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"; export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"; export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"; export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
echo "==== per-behavior STAGED ASR-RERANK ===="
echo "JOB=${SLURM_JOB_ID} NODE=${SLURM_NODELIST} BEHAVIORS=${BEHAVIORS:-<auto>} date $(date -u)"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
[[ "$GPU_NAME" == *"L40S"* ]] || { echo "ERROR: not L40S ($GPU_NAME)"; exit 1; }
if [ -n "$BEHAVIORS" ]; then
  python scripts/staged_asr_rerank.py --behaviors "$BEHAVIORS"
else
  python scripts/staged_asr_rerank.py
fi
echo "==== rerank done $(date -u) ===="
