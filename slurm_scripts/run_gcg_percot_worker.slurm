#!/bin/bash
#SBATCH --job-name=percot_worker
#SBATCH --output=logs/percot_worker_%j.out
#SBATCH --error=logs/percot_worker_%j.err
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

# Per-behavior Native-CoT GCG batched worker: loads Qwen3-14B once, drains one
# job-list shard (many 1-row-manifest optimizations). See
# docs/GCG_PERBEHAVIOR_NATIVECOT_PLAN.md.  Required env: JOBLIST=<shard.jsonl>
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
JOBLIST="${JOBLIST:?set JOBLIST=path/to/joblist_shardK.jsonl}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "==== PER-BEHAVIOR Native-CoT worker ===="
echo "JOB=${SLURM_JOB_ID} NODE=${SLURM_NODELIST} JOBLIST=${JOBLIST}"
echo "jobs in shard: $(wc -l < "${JOBLIST}")  |  date $(date -u)  git $(git rev-parse HEAD)"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
[[ "$GPU_NAME" == *"L40S"* ]] || { echo "ERROR: not L40S ($GPU_NAME)"; exit 1; }

python -m poc_stage_gcg_early.run_batched_perbehavior "${JOBLIST}"

echo "==== worker done $(date -u) ===="
