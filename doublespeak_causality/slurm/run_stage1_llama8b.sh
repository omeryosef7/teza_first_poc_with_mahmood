#!/bin/bash
#SBATCH --job-name=ds_stage1_llama8b
#SBATCH --output=doublespeak_causality/logs/ds_stage1_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_stage1_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=gpu-sharifm,killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gres=gpu:l40s:1
#
# Doublespeak Stage-1: plumbing smoke test + representation mapping on
# Llama-3.1-8B-Instruct. Follows slurm_scripts/submit_qwen_ae.sh conventions
# (account/partition/L40S guard/env). Honors user rules: L40S only, no deps,
# HF cache -> project dir. Resumable via completion marker.
#
# Submit:  sbatch doublespeak_causality/slurm/run_stage1_llama8b.sh

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
MODEL="meta-llama/Llama-3.1-8B-Instruct"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p doublespeak_causality/logs doublespeak_causality/outputs \
    "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

echo "=== Doublespeak Stage-1 ==="; date; hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"
python -c "import torch,transformers,sys; print('py',sys.version.split()[0],'torch',torch.__version__,'tfm',transformers.__version__)"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader || true

# L40S guard (avoid CPU-offload / non-comparable hardware) — user rule.
GPU_TYPE=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
if ! echo "$GPU_TYPE" | grep -qi "L40S"; then
    echo "ERROR: GPU is '$GPU_TYPE' — mechanistic runs require L40S. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_TYPE"

MARK="doublespeak_causality/outputs/.stage1_llama8b.COMPLETE"
if [ -f "$MARK" ]; then echo "Already COMPLETE ($MARK) — nothing to do."; exit 0; fi

echo "--- [1/2] plumbing smoke test ---"
python doublespeak_causality/smoke_pipeline.py --model "$MODEL" --max-new-tokens 64

echo "--- [2/2] representation mapping (Stage 1) ---"
python doublespeak_causality/01_map_representations.py \
    --model "$MODEL" --data doublespeak_causality/data/seed_concepts.json --templated

echo "COMPLETE $(date)" > "$MARK"
echo "=== done ==="; date
