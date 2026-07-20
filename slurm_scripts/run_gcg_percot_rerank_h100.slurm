#!/bin/bash
#SBATCH --job-name=percot_rerank_h100
#SBATCH --output=logs/percot_rerank_h100_%j.out
#SBATCH --error=logs/percot_rerank_h100_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=gpu-h100-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1

# H100 variant of the per-behavior staged ASR-rerank harness.
# Used only when the L40S partition is fully booked cluster-wide. Scoring is a
# pure generation/StrongREJECT eval (no L40S-specific correctness dependence);
# H100 (80GB) fits Qwen3-14B comfortably. Env: BEHAVIORS=comma,list (default=auto).
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
echo "==== per-behavior STAGED ASR-RERANK (H100) ===="
echo "JOB=${SLURM_JOB_ID} NODE=${SLURM_NODELIST} BEHAVIORS=${BEHAVIORS:-<auto>} date $(date -u)"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
[[ "$GPU_NAME" == *"H100"* ]] || { echo "ERROR: not H100 ($GPU_NAME)"; exit 1; }
if [ -n "$BEHAVIORS" ]; then
  python scripts/staged_asr_rerank.py --behaviors "$BEHAVIORS"
else
  python scripts/staged_asr_rerank.py
fi
echo "==== rerank done $(date -u) ===="
