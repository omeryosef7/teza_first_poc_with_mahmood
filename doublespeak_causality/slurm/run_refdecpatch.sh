#!/bin/bash
#SBATCH --job-name=ds_refdecpatch
#SBATCH --output=doublespeak_causality/logs/ds_refdecpatch_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_refdecpatch_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# §23 / Gate B — BEHAVIORAL confirmation of the §3 decision-token refusal restoration.
# GENERATION job -> STRICT L40S (generation wrappers are L40S-only per Appendix A).
# Every #SBATCH is a DEFAULT; override on the sbatch line (comma-lists stay in DEFAULTS below, never
# via --export which truncates). To skip slow n-801: sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 ...
#   SMOKE:  sbatch --export=ALL,DSN=2 doublespeak_causality/slurm/run_refdecpatch.sh
#   FULL v3 clearharm (default bench):  sbatch doublespeak_causality/slurm/run_refdecpatch.sh
#   FULL v3 generated:  sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral_v3/beh_generated.json,DSCOHORT=generated doublespeak_causality/slurm/run_refdecpatch.sh
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
: "${DSBAND:=15,16,17}"           # resid_post layers for the direct-donor necessity arms (comma-list DEFAULT)
: "${DSHEAD:=17}"                 # layer for the rand + self control arms
: "${DSSPLITS:=train,dev,test}"  # comma-list DEFAULT
: "${DSMAXNEW:=200}"
: "${DSN:=0}"
: "${DSSEED:=0}"
: "${DSBIDIR:=0}"                 # 1 => add --bidirectional (reverse arm: DS resid -> Direct prompt)
BIDIR_FLAG=""; [ "$DSBIDIR" = "1" ] && BIDIR_FLAG="--bidirectional"
echo "=== refusal decision-patch behav (§23/Gate B): $DSMODEL bench=$DSBENCH band=$DSBAND head=$DSHEAD maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase_refusal_decision_patch_behav.py \
  --bench "$DSBENCH" --model "$DSMODEL" --band "$DSBAND" --head-layer "$DSHEAD" \
  --max-new "$DSMAXNEW" --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED" $BIDIR_FLAG
echo "=== done ==="; date
