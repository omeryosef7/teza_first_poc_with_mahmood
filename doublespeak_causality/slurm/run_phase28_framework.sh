#!/bin/bash
#SBATCH --job-name=ds_p28fw
#SBATCH --output=doublespeak_causality/logs/ds_p28fw_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p28fw_%j.err
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
# §28 FRAMEWORK/IMPLEMENTATION ROBUSTNESS -- head-to-head house vs from-scratch refusal ablation
# + an nnsight forward cross-check. GENERATION job -> STRICT L40S guard (same as run_behav_refusal.sh).
# Every #SBATCH is a DEFAULT; override on the sbatch line.
#   SMOKE:  sbatch --export=ALL,DSN=4,DSNNITEMS=1 doublespeak_causality/slurm/run_phase28_framework.sh
#   FULL test split (n=42): sbatch doublespeak_causality/slurm/run_phase28_framework.sh
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs doublespeak_causality/outputs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"; export PYTHONUNBUFFERED=1
: "${DSBENCH:=doublespeak_causality/data/behavioral_v3/beh_clearharm.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSREFPT:=doublespeak_causality/outputs/stage_gcg_full/refusal_direction_llama_L18.pt}"
: "${DSALPHA:=1.0}"
: "${DSSPLITS:=test}"
: "${DSMAXNEW:=200}"
: "${DSN:=0}"
: "${DSNNITEMS:=2}"
: "${DSSEED:=0}"
: "${DSENABLE:=default}"
for v in DSBENCH DSMODEL DSREFPT DSALPHA DSSPLITS DSMAXNEW DSN DSNNITEMS DSSEED DSENABLE; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
echo "=== §28 framework robustness: $DSMODEL bench=$DSBENCH alpha=$DSALPHA n=$DSN nnitems=$DSNNITEMS splits=$DSSPLITS ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase28_framework_robustness.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-pt "$DSREFPT" --alpha "$DSALPHA" \
  --splits "$DSSPLITS" --max-new "$DSMAXNEW" --n "$DSN" --nnsight-items "$DSNNITEMS" \
  --seed "$DSSEED" --enable-thinking "$DSENABLE"
echo "=== done ==="; date
