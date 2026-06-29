#!/bin/bash
#
# Stage 4 P11 Patch Alignment Validation.
#
# Runs validate_p11_patch_alignment.py on 2 examples to gate the
# selectivity pilot. Writes:
#   outputs/stage4/p11_controlled_patching/alignment_validation.json
#
# Check after this completes:
#   python -c "import json; d=json.load(open('outputs/stage4/p11_controlled_patching/alignment_validation.json')); print(d.get('overall_pass'), [r for r in d.get('results', []) if not r.get('pass')])"
#
# If overall_pass=True, submit: sbatch slurm_scripts/stage4_p11_selectivity_pilot.slurm
#
# SLURM rules: L40S only, max 6 parallel, no deps, no trimming.

#SBATCH --job-name=p11_validate
#SBATCH --output=logs/p11_validate_%j.out
#SBATCH --error=logs/p11_validate_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=40G
#SBATCH --time=01:30:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs \
    outputs/stage4/p11_controlled_patching \
    "$RUNTIME_DIR"/{config,data,runtime,ipython} \
    "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONUNBUFFERED=1

echo "=== P11 Patch Alignment Validation ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

python -m poc_stage4.validate_p11_patch_alignment \
    --n-examples 2

echo ""
echo "=== Validation complete ==="
date

RESULT=$(python -c "
import json, sys
try:
    d = json.load(open('outputs/stage4/p11_controlled_patching/alignment_validation.json'))
    print('overall_pass:', d.get('overall_pass'))
    failures = [r for r in d.get('results', []) if not r.get('pass', True)]
    if failures:
        print('FAILURES:')
        for f in failures:
            print(' ', f)
    else:
        print('All gates passed.')
except Exception as e:
    print('ERROR reading result:', e)
    sys.exit(1)
" 2>&1)
echo "$RESULT"

# Exit non-zero if validation failed so the log is obvious
if ! python -c "
import json, sys
d = json.load(open('outputs/stage4/p11_controlled_patching/alignment_validation.json'))
sys.exit(0 if d.get('overall_pass') else 1)
" 2>/dev/null; then
    echo "VALIDATION FAILED — do NOT submit selectivity pilot"
    exit 1
fi

echo "VALIDATION PASSED — safe to submit: sbatch slurm_scripts/stage4_p11_selectivity_pilot.slurm"
