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
# NO PIPE. `nvidia-smi | head -1` gets SIGPIPE when head exits first, and under `set -o pipefail`
# that kills the job with exit 13 before a single byte reaches the logs -- job 831537 died in 7s
# with two 0-byte files, while the IDENTICAL script had run fine as 831512. The house runner
# (`run_boombness.sh`) uses parameter expansion for exactly this reason; copied here.
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"
GPU="${GPU_ALL%%$'\n'*}"
case "$GPU" in *L40S*|*l40s*) echo "GPU ok: $GPU";; *) echo "ERROR need L40S got '$GPU'"; exit 1;; esac
echo "git=$(git rev-parse HEAD) dirty=$(git status --porcelain | wc -l)"
python -u scripts/rah3_verify_noncopy_gpu.py $(cat runargs/rah3/verifB_p_frozen.txt)
echo "=== verifier B done ==="
