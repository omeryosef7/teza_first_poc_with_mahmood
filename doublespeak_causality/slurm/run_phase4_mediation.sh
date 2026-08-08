#!/bin/bash
#SBATCH --job-name=ds_p4med
#SBATCH --output=doublespeak_causality/logs/ds_p4med_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p4med_%j.err
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
# §4 REFUSAL CARRY-vs-READOUT mediation (scripts/phase4_refusal_mediation.py). FORWARD/PATCHING only
# (no generation) -> the >=23GB GPU allowlist applies (same guard as run_phase8_path.sh). Every #SBATCH
# is a DEFAULT; override on the sbatch line, e.g. widen the nodelist to Ampere killable:
#   sbatch --nodelist=n-301,n-302,... --time=03:00:00 doublespeak_causality/slurm/run_phase4_mediation.sh
#   SMOKE: sbatch --export=ALL,DSN=3,DSHEADS=L16H4,L13H18 doublespeak_causality/slurm/run_phase4_mediation.sh
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
: "${DSREFPT:=doublespeak_causality/outputs/stage_gcg_full/refusal_direction_llama_L18.pt}"
: "${DSHEADS:=L16H4,L13H18,L16H10,L13H11,L13H9,L15H7}"   # §7 test top-6; comma-list DEFAULT (NOT via --export)
: "${DSSPLITS:=test}"
: "${DSN:=0}"
: "${DSSEED:=0}"
: "${DSENABLE:=default}"
# DSHEADS/DSSPLITS are comma-lists by design (kept as DEFAULTS). scalars must not contain a comma.
for v in DSBENCH DSMODEL DSREFPT DSN DSSEED DSENABLE; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
# allow DSHEADS via --export ONLY if a single head (no comma); else edit the DEFAULT here
if [ -n "${DSHEADS_OVERRIDE:-}" ]; then
  case "$DSHEADS_OVERRIDE" in *,*) echo "ERROR: DSHEADS_OVERRIDE has a comma; --export truncates it. Edit DSHEADS default."; exit 1;; esac
  DSHEADS="$DSHEADS_OVERRIDE"
fi
echo "=== §4 refusal mediation: $DSMODEL bench=$DSBENCH heads=$DSHEADS splits=$DSSPLITS n=$DSN ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
GPU_MEM_RAW="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 || true)"
GPU_MEM="$(printf '%s' "$GPU_MEM_RAW" | grep -oE '[0-9]+' | head -1 || true)"; GPU_MEM="${GPU_MEM:-0}"
case "$GPU_TYPE" in
  *L40S*|*l40s*|*A5000*|*a5000*|*A6000*|*a6000*|*A100*|*A40*|*H100*|*H200*|*L40*|*3090*|*4090*)
    if [ "${GPU_MEM:-0}" -ge 23000 ]; then echo "GPU ok: $GPU_TYPE (${GPU_MEM}MiB)";
    else echo "ERROR: $GPU_TYPE has only ${GPU_MEM}MiB (<23GB); Llama-8B bf16 needs ~18GB"; exit 1; fi ;;
  *) echo "ERROR: GPU '$GPU_TYPE' (${GPU_MEM}MiB) not in the allowlist"; exit 1 ;;
esac
python -u doublespeak_causality/scripts/phase4_refusal_mediation.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-pt "$DSREFPT" --heads "$DSHEADS" \
  --splits "$DSSPLITS" --n "$DSN" --seed "$DSSEED" --enable-thinking "$DSENABLE"
echo "=== done ==="; date
