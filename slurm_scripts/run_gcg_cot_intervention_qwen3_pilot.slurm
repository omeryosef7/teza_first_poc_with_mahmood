#!/bin/bash

#SBATCH --job-name=gcg_t2_intervene
#SBATCH --output=logs/gcg_t2_intervene_%j.out
#SBATCH --error=logs/gcg_t2_intervene_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Sprint 2 / Track 2 -- validation pilot for run_cot_intervention.py on Qwen3.
#
# Small pilot (10 tasks x 6 conditions = 60 rows) using the 5A/gcg_full_qwen3_cot_target
# suffix, BEFORE committing to a larger run or attempting a Gemma4 pilot. Read-only
# against the source run (only reads FINAL_CANDIDATES.jsonl); writes to a brand new
# directory under outputs/stage_gcg_early/cot_intervention/.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="poc_stage2"
SOURCE_RUN="${PROJECT_DIR}/outputs/stage_gcg_full/gcg_full_qwen3_cot_target"
OUTPUT_DIR="${PROJECT_DIR}/outputs/stage_gcg_early/cot_intervention/qwen3_5a_pilot"
N_TASKS=10
SEED=42

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs "${OUTPUT_DIR}"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "========================================================"
echo "  Sprint 2 Track 2 -- CoT Intervention Pilot (Qwen3)"
echo "========================================================"
echo "SLURM_JOB_ID:  ${SLURM_JOB_ID}"
echo "SOURCE_RUN:    ${SOURCE_RUN}"
echo "OUTPUT_DIR:    ${OUTPUT_DIR}"
echo "N_TASKS:       ${N_TASKS}"
echo "DATE:          $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

if [ ! -f "${SOURCE_RUN}/FINAL_CANDIDATES.jsonl" ]; then
    echo "ERROR: Source run has no FINAL_CANDIDATES.jsonl: ${SOURCE_RUN}"
    exit 1
fi

python -m poc_stage_gcg_early.run_cot_intervention \
    --suffix-source-run "${SOURCE_RUN}" \
    --model-family qwen3 \
    --model-name-or-path Qwen/Qwen3-14B \
    --output-dir "${OUTPUT_DIR}" \
    --n-tasks "${N_TASKS}" \
    --seed "${SEED}"

echo ""
echo "========================================================"
echo "  Sprint 2 Track 2 pilot COMPLETE"
echo "  $(date -u)"
echo "========================================================"
