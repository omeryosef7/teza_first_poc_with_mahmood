#!/bin/bash
#SBATCH --job-name=ds_p20norm
#SBATCH --output=doublespeak_causality/logs/ds_p20norm_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p20norm_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
# §20 unrelated-normal utility (generation). DSGPUALLOW=23gb relaxes to Ampere+ allowlist.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"; cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"; export PYTHONUNBUFFERED=1
: "${DSPROJ:=doublespeak_causality/outputs/refproj_clearharm_20260804_162641_711392/summary.json}"
: "${DSLAYERS:=16,18,20}"; : "${DSN:=0}"
echo "=== §20 unrelated-normal: proj=$DSPROJ layers=$DSLAYERS n=$DSN ==="; date; hostname
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)"
if [ "${DSGPUALLOW:-}" = "23gb" ]; then
  GM="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null|head -1|grep -oE '[0-9]+'|head -1)"; GM="${GM:-0}"
  case "$GPU_TYPE" in *L40S*|*A5000*|*a5000*|*A6000*|*a6000*|*A100*|*A40*|*H100*|*H200*|*L40*|*3090*|*4090*) [ "$GM" -ge 23000 ] && echo "GPU ok $GPU_TYPE ${GM}MiB" || { echo "ERR <23GB"; exit 1; };; *) echo "ERR gpu $GPU_TYPE"; exit 1;; esac
else case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok $GPU_TYPE";; *) echo "ERROR need L40S"; exit 1;; esac; fi
python -u doublespeak_causality/scripts/phase20_unrelated_normal.py \
  --bench doublespeak_causality/data/behavioral_v3/unrelated_normal.json \
  --proj-summary "$DSPROJ" --proj-split train --layers "$DSLAYERS" --n "$DSN"
echo "=== done ==="; date
