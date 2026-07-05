#!/bin/bash

#SBATCH --job-name=gcg_state_capture_gpu
#SBATCH --output=logs/gcg_state_capture_gpu_%j.out
#SBATCH --error=logs/gcg_state_capture_gpu_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# Stage 4: GPU integration test — hook capture ≡ output_hidden_states=True for Qwen3-14B.
# Runs test_state_capture.py::TestCaptureEquivalenceQwen3 on real L40S hardware.
# Gate: all equivalence assertions must pass.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

mkdir -p logs

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
export CUDA_LAUNCH_BLOCKING=1

echo "========================================================"
echo "  Stage 4: Hook Capture GPU Integration Test"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST}"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi
echo "GPU check passed: $GPU_NAME"

echo ""
echo "--- Running CPU-only tests first ---"
python -m pytest poc_stage_gcg_early/tests/ -m "not gpu_integration" -q --tb=short
echo "CPU tests passed."

echo ""
echo "--- Running GPU integration test ---"
python -m pytest poc_stage_gcg_early/tests/test_state_capture.py \
    -m gpu_integration -v --tb=long

echo ""
echo "========================================================"
echo "  Stage 4 GPU Integration Test COMPLETE"
echo "  Date: $(date -u)"
echo "========================================================"
