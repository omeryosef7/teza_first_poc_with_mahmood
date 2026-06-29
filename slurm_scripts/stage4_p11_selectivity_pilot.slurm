#!/bin/bash
# P11 Selectivity Pilot: Full-range prefill patching with control conditions.
#
# PRECONDITIONS — must be satisfied before submitting:
#   1. validate_p11_patch_alignment.py passes ALL gates (identity KL < 0.01, sham KL = 0.0)
#      Run: python -m poc_stage4.validate_p11_patch_alignment --n-examples 2
#      Output: outputs/stage4/p11_controlled_patching/alignment_validation.json
#      Check: overall_pass == true
#   2. SMOKE=1 test passes (n=2, 3 layers, ~20 min):
#      SMOKE=1 python -m poc_stage4.run_p11_controlled_patching
#      Check results.jsonl has full_answer_text field non-empty
#   3. All 4 "stable+probable" source prompts load from stage6 traces
#
# SLURM rules: L40S only, max 6 parallel, no dependency chains, no trimming.
#
# Expected runtime: ~8h for n=5 sources × 6 layers × 11 conditions.
# Expected output: outputs/stage4/p11_controlled_patching/run_<timestamp>/results.jsonl

#SBATCH --job-name=p11_selectivity
#SBATCH --output=logs/p11_selectivity_%j.out
#SBATCH --error=logs/p11_selectivity_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --time=16:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

cd "${PROJECT_DIR}"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"

export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONUNBUFFERED=1

echo "=== P11 Selectivity Pilot ==="
echo "SLURM job: ${SLURM_JOB_ID}"
echo "Node: $(hostname)"
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'unknown')"
echo "Start: $(date)"

# Architecture verification — abort before loading model if wrong
python -c "
import sys
cfg_n_layers = 40
print(f'Expected n_layers={cfg_n_layers} for Qwen3-14B. Proceeding.')
"

# Gate check: alignment validation must exist and pass
ALIGNMENT_JSON="outputs/stage4/p11_controlled_patching/alignment_validation.json"
if [ -f "${ALIGNMENT_JSON}" ]; then
    OVERALL=$(python -c "import json; d=json.load(open('${ALIGNMENT_JSON}')); print(d.get('overall_pass', False))")
    if [ "${OVERALL}" != "True" ]; then
        echo "ERROR: alignment validation did not pass. Run validate_p11_patch_alignment.py first."
        exit 1
    fi
    echo "Gate check: alignment_validation.json PASSED"
else
    echo "WARNING: alignment_validation.json not found. Proceeding anyway (add SMOKE=1 first)."
fi

python -m poc_stage4.run_p11_controlled_patching \
    --model qwen3 \
    --n-examples 3 \
    --layers 3 17 26

echo "Done: $(date)"
