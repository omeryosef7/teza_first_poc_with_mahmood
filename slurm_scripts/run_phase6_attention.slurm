#!/bin/bash
#SBATCH --job-name=phase6_attn
#SBATCH --output=logs/phase6_attn_%j.out
#SBATCH --error=logs/phase6_attn_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301,n-801
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-poc_stage2}"
if [ -f .env ]; then set -a; source .env; set +a; fi
mkdir -p logs
export HF_HOME="$(pwd)/.cache/huggingface"; export HF_HUB_CACHE="$(pwd)/.cache/huggingface/hub"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
python -u scripts/phase6_attention_signal.py \
    --manifest "${MANIFEST:?}" --scores "${SCORES:?}" --out "${OUT:?}"
