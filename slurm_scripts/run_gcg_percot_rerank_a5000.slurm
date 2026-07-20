#!/bin/bash
#SBATCH --job-name=percot_rerank_a5k
#SBATCH --output=logs/percot_rerank_a5k_%j.out
#SBATCH --error=logs/percot_rerank_a5k_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --nodelist=n-501
#SBATCH --gres=gpu:a5000:2

# A5000 fallback for the per-behavior staged ASR-rerank harness, used when the
# L40S partition is fully booked cluster-wide. n-501 (gpu-sharifm) has free
# A5000s (Ampere -> native bf16, unlike V100). Qwen3-14B (~29.6GB bf16) does not
# fit one 24GB A5000, so request TWO and let device_map="auto" shard the model.
# Scoring is a pure generation/StrongREJECT eval (no L40S-specific dependence).
# Env: BEHAVIORS=comma,list (default=auto-discover completed runs).
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
echo "==== per-behavior STAGED ASR-RERANK (A5000 x2) ===="
echo "JOB=${SLURM_JOB_ID} NODE=${SLURM_NODELIST} BEHAVIORS=${BEHAVIORS:-<auto>} date $(date -u)"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
NGPU=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
echo "GPU=$GPU_NAME NGPU=$NGPU"
[[ "$GPU_NAME" == *"A5000"* ]] || { echo "ERROR: not A5000 ($GPU_NAME)"; exit 1; }
[[ "$NGPU" -ge 2 ]] || { echo "ERROR: need >=2 GPUs to shard 14B (got $NGPU)"; exit 1; }
if [ -n "$BEHAVIORS" ]; then
  python scripts/staged_asr_rerank.py --behaviors "$BEHAVIORS"
else
  python scripts/staged_asr_rerank.py
fi
echo "==== rerank done $(date -u) ===="
