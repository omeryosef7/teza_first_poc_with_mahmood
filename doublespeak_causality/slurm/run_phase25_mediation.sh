#!/bin/bash
#SBATCH --job-name=ds_p25med
#SBATCH --output=doublespeak_causality/logs/ds_p25med_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p25med_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=05:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# §25 FULL BEHAVIORAL MEDIATION (scripts/phase25_full_mediation.py). GENERATION+judge job. DEFAULT strict
# L40S; DSGPUALLOW=23gb relaxes to the >=23GB Ampere+ allowlist (greedy generation is valid on any GPU).
#   SMOKE: sbatch --export=ALL,DSN=3 doublespeak_causality/slurm/run_phase25_mediation.sh
#   FULL test: sbatch doublespeak_causality/slurm/run_phase25_mediation.sh
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
: "${DSBENCH:=doublespeak_causality/data/behavioral_v3/beh_clearharm.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSBAND:=15,16,17}"          # comma-list DEFAULT (never via --export)
: "${DSHEADLAYER:=17}"
: "${DSSPLITS:=test}"
: "${DSMAXNEW:=200}"
: "${DSN:=0}"
: "${DSSEED:=0}"
for v in DSBENCH DSMODEL DSHEADLAYER DSSPLITS DSMAXNEW DSN DSSEED; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
echo "=== §25 full mediation: $DSMODEL bench=$DSBENCH band=$DSBAND head=$DSHEADLAYER splits=$DSSPLITS n=$DSN ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
if [ "${DSGPUALLOW:-}" = "23gb" ]; then
  GPU_MEM_RAW="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 || true)"
  GPU_MEM="$(printf '%s' "$GPU_MEM_RAW" | grep -oE '[0-9]+' | head -1 || true)"; GPU_MEM="${GPU_MEM:-0}"
  case "$GPU_TYPE" in
    *L40S*|*l40s*|*A5000*|*a5000*|*A6000*|*a6000*|*A100*|*A40*|*H100*|*H200*|*L40*|*3090*|*4090*)
      if [ "${GPU_MEM:-0}" -ge 23000 ]; then echo "GPU ok (23gb allowlist): $GPU_TYPE (${GPU_MEM}MiB)";
      else echo "ERROR: $GPU_TYPE has only ${GPU_MEM}MiB (<23GB)"; exit 1; fi ;;
    *) echo "ERROR: GPU '$GPU_TYPE' not in the 23GB allowlist"; exit 1 ;;
  esac
else
  case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
fi
python -u doublespeak_causality/scripts/phase25_full_mediation.py \
  --bench "$DSBENCH" --model "$DSMODEL" --band "$DSBAND" --head-layer "$DSHEADLAYER" \
  --splits "$DSSPLITS" --max-new "$DSMAXNEW" --n "$DSN" --seed "$DSSEED"
echo "=== done ==="; date
