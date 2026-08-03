#!/bin/bash
#SBATCH --job-name=ds_p4bp
#SBATCH --output=doublespeak_causality/logs/ds_p4bp_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p4bp_%j.err
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
# CAUSAL_CIRCUIT_MASTER_PLAN Phase 6 causal MLP-output write test (necessity+sufficiency)
# (necessity) with the working forced-choice readout. Windows are hardcoded (never via --export,
# which truncates comma-lists). Control coverage: DSNPROMPTS (0=all), DSGRAN (window|layer).
#   sbatch --export=ALL,DSBENCH=doublespeak_causality/data/bench/bench_curated.json,DSNPROMPTS=2,DSGRAN=window run_phase3_demoko.sh
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"; export PYTHONUNBUFFERED=1
echo "=== run_ds_p4bp smoke ==="; date; hostname
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase4b_pattern.py --bench "${DSBENCH:-doublespeak_causality/data/bench/bench_curated.json}" --n-prompts "${DSNPROMPTS:-2}" --splits "${DSSPLITS:-dev}" --carry "${DSCARRY:-L14H4_L14H5_L14H23_L15H8_L17H27_L18H20_L21H10}"
  --granularity "$DSGRAN" --positions "$DSPOS" --component "$DSCOMP" --n-prompts "$DSNPROMPTS"
echo "=== done ==="; date
