#!/bin/bash
#SBATCH --job-name=ds_panel07_llama8b
#SBATCH --output=doublespeak_causality/logs/ds_panel07_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_panel07_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- measured 2026-08-05, do not re-litigate: cpus=4 mem=48G is the fast-allocating
# default (8cpu/64G sat PENDING 3h32m as 716187/716188; the SAME work at 4cpu/48G allocated in 6m32s as
# 717879/717880). Mechanism: node RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=64G
# leaves only 7 of 8 GPUs memory-feasible per node while 48G leaves all 8. --time is NOT the lever.
# Every #SBATCH line below is a DEFAULT: the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --exclude=n-801 slurm/run_panel07_llama8b.sh
#
# Doublespeak Stage-2: plumbing smoke test + representation mapping on
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
export PYTHONUNBUFFERED=1          # so stdout is not lost if the job dies

echo "=== Doublespeak Stage-2 ==="; date; hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"
python -c "import torch,transformers,sys; print('py',sys.version.split()[0],'torch',torch.__version__,'tfm',transformers.__version__)"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader || true

# L40S guard (avoid CPU-offload / non-comparable hardware) — user rule.
# Pipe-free first-line extraction (a `| head -1` under `set -o pipefail` can abort
# on SIGPIPE when nvidia-smi lists a full 8-GPU node — suspected cause of the
# silent exit-13 in job 686494).
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"
GPU_TYPE="${GPU_ALL%%$'\n'*}"
echo "GPU_TYPE='$GPU_TYPE'"
case "$GPU_TYPE" in
    *L40S*|*l40s*) echo "GPU check passed: $GPU_TYPE" ;;
    *) echo "ERROR: GPU is '$GPU_TYPE' — mechanistic runs require L40S. Aborting."; exit 1 ;;
esac
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"

MARK="doublespeak_causality/outputs/.panel07_llama8b.COMPLETE"
if [ -f "$MARK" ]; then echo "Already COMPLETE ($MARK) — nothing to do."; exit 0; fi

echo "--- Stage 2b: Patchscopes necessity+sufficiency readout (GPT-4o-mini concepts) ---"
python -u doublespeak_causality/07_patchscope_readout.py \
    --model "$MODEL" --data doublespeak_causality/data/virus_codeword_panel.json --templated --readout-layer 30

echo "COMPLETE $(date)" > "$MARK"
echo "=== done ==="; date
