#!/bin/bash
#SBATCH --job-name=ds_qwen3emg
#SBATCH --output=doublespeak_causality/logs/ds_qwen3emg_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_qwen3emg_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# Second-model generality: emergence (Direct-early vs Doublespeak-late) on Qwen3-14B.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs doublespeak_causality/outputs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONUNBUFFERED=1
echo "=== Qwen3 generality ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"
GPU_TYPE="${GPU_ALL%%$'\n'*}"; echo "GPU_TYPE='$GPU_TYPE'"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR: need L40S, got '$GPU_TYPE'"; exit 1;; esac

MARK="doublespeak_causality/outputs/.qwen3emg.COMPLETE"
if [ -f "$MARK" ]; then echo "already COMPLETE"; exit 0; fi

# emergence on Qwen3-14B (Direct/Neutral/Doublespeak per-layer decode) for the panel
python -u doublespeak_causality/11_emergence_trajectory.py \
    --model "Qwen/Qwen3-14B" \
    --data doublespeak_causality/data/virus_codeword_panel.json --only "" --templated

# necessity/sufficiency on Qwen3-14B (readout near late layers: 40-4=36)
python -u doublespeak_causality/07_patchscope_readout.py \
    --model "Qwen/Qwen3-14B" \
    --data doublespeak_causality/data/virus_codeword_panel.json --templated --readout-layer 36

echo "COMPLETE $(date)" > "$MARK"
echo "=== done ==="; date
