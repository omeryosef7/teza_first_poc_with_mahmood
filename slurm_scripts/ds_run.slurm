#!/bin/bash
#SBATCH --job-name=ds_run
#SBATCH --output=logs/ds_run_%j.out
#SBATCH --error=logs/ds_run_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# Generic NEXT3 GPU runner: runs `python $CMD` in the doublespeak_causality dir with
# the house env + L40S guard. Pass the full python argline via CMD env.
#   CMD="46_forced_choice_patchscope.py --bench ... --out ..." sbatch slurm_scripts/ds_run.slurm
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
DSC="$PROJECT_DIR/doublespeak_causality"; CONDA_ENV="${CONDA_ENV:-poc_stage2}"
: "${CMD:?set CMD to the python argline}"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface" HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch" TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}" PYTHONUNBUFFERED=1
echo "=== ds_run ==="; date; hostname; echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true); echo "GPU: $GPU"
echo "$GPU" | grep -qi "L40S" || { echo "FATAL: GPU not L40S ($GPU)" >&2; exit 1; }
echo "CMD: python $CMD"
cd "$DSC"
python $CMD
echo "=== DONE ==="; date