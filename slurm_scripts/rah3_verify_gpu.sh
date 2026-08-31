#!/bin/bash
#SBATCH --job-name=rah3vb
#SBATCH --output=outputs/boombness/logs/rah3vb_%j.out
#SBATCH --error=outputs/boombness/logs/rah3vb_%j.err
#SBATCH --ntasks=1 --cpus-per-task=4 --mem=48G --time=02:00:00
#SBATCH --partition=killable --account=gpu-research --nodes=1 --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate poc_stage2
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export PYTHONUNBUFFERED=1
GPU="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)"
case "$GPU" in *L40S*) echo "GPU ok: $GPU";; *) echo "ERROR need L40S got '$GPU'"; exit 1;; esac
echo "git=$(git rev-parse HEAD) dirty=$(git status --porcelain | wc -l)"
python -u scripts/rah3_verify_noncopy_gpu.py $(cat runargs/rah3/verifB_p_frozen.txt)
echo "=== verifier B done ==="
