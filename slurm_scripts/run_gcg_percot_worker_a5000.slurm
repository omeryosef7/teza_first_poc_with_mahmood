#!/bin/bash
#SBATCH --job-name=percot_worker_a5k
#SBATCH --output=logs/percot_worker_a5k_%j.out
#SBATCH --error=logs/percot_worker_a5k_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --nodelist=n-503
#SBATCH --gres=gpu:a5000:2
#SBATCH --exclude=n-804,n-602,n-301

# A5000 variant of the per-behavior GCG optimization worker, used when L40S is
# fully booked. n-503 has idle A5000s (Ampere -> native bf16 + flash-attn, same as
# L40S). Qwen3-14B optimization (~28GB weights + backward) does not fit one 24GB
# A5000, so request TWO and let device_map="auto" shard. **VALIDATE with the smoke
# test (compare step0/final task_loss to the L40S pilot) before trusting at scale.**
# Required env: JOBLIST=<shard.jsonl>
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
JOBLIST="${JOBLIST:?set JOBLIST=path/to/joblist.jsonl}"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"; export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"; export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"; export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
echo "==== PER-BEHAVIOR Native-CoT worker (A5000 x2) ===="
echo "JOB=${SLURM_JOB_ID} NODE=${SLURM_NODELIST} JOBLIST=${JOBLIST}"
echo "jobs: $(wc -l < "${JOBLIST}")  date $(date -u)  git $(git rev-parse HEAD)"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
NGPU=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
echo "GPU=$GPU_NAME NGPU=$NGPU"
[[ "$GPU_NAME" == *"A5000"* ]] || { echo "ERROR: not A5000 ($GPU_NAME)"; exit 1; }
[[ "$NGPU" -ge 2 ]] || { echo "ERROR: need >=2 GPUs to shard 14B (got $NGPU)"; exit 1; }
python -m poc_stage_gcg_early.run_batched_perbehavior "${JOBLIST}"
echo "==== worker done $(date -u) ===="
