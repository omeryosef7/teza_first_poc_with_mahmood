#!/bin/bash
#SBATCH --job-name=ds_dose
#SBATCH --output=doublespeak_causality/logs/ds_dose_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_dose_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- copied from run_defense_utility.sh (measured 2026-08-05, do not re-litigate):
# cpus=4 mem=48G is the fast-allocating default; --mem=64G leaves only 7/8 GPUs feasible per node while
# 48G leaves all 8. --time is NOT the lever. Every #SBATCH line is a DEFAULT: the matching sbatch flag
# overrides it with no file edit. To skip the slow n-801 node pass an explicit REDUCED nodelist (NOT
# --exclude, which nullifies #SBATCH --nodelist and lands the job anywhere):
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_phase6_dose.sh
#
# §6 DEMONSTRATION-COUNT dose-response: for each v3 clearharm item sweep n_demo over NESTED demo
# subsets and measure p_concept (forced-choice patchscope), decision-token L18 refusal projection, and
# ASR (generate + behav_judge). Descriptive fits only. 3 endpoints x 8 doses x items -> long; --time=12h.
# SMOKE (2 items/split; comma-lists are DEFAULTS below, never via --export which truncates at first comma):
#   sbatch --export=ALL,DSN=2 slurm/run_phase6_dose.sh
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
: "${DSN:=0}"
: "${DSSPLITS:=train,test}"       # comma-list kept as a DEFAULT here (not via --export, which truncates)
: "${DSREFVAL:=doublespeak_causality/outputs/refval_clearharm_20260806_051728_721957}"  # validated L16/L18 (NEVER L9)
: "${DSNDEMOS:=0,1,2,4,6,8,10,12}"  # NESTED demo counts; comma-list = DEFAULT (never --export)
: "${DSANCHOR:=18}"               # headline validated refusal layer
: "${DSMAXNEW:=200}"
: "${DSSEED:=0}"
echo "=== dose-response: $DSMODEL bench=$DSBENCH ndemos=$DSNDEMOS anchor=L$DSANCHOR maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase6_dose_response.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refval-dir "$DSREFVAL" \
  --n-demos "$DSNDEMOS" --readout-anchor "$DSANCHOR" --max-new "$DSMAXNEW" --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED"
echo "=== done ==="; date
