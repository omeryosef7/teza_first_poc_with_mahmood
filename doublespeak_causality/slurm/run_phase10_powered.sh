#!/bin/bash
#SBATCH --job-name=ds_p10pow
#SBATCH --output=doublespeak_causality/logs/ds_p10pow_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p10pow_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=16:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- measured 2026-08-05, do not re-litigate: cpus=4 mem=48G is the fast-allocating
# default (8cpu/64G sat PENDING 3h32m; the SAME work at 4cpu/48G allocated in 6m32s). Mechanism: node
# RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=64G leaves only 7 of 8 GPUs feasible
# per node while 48G leaves all 8. --time is NOT the lever. Every #SBATCH line is a DEFAULT: the matching
# sbatch flag overrides it with no file edit. To skip the slow-loading n-801 node, pass an explicit
# REDUCED NODELIST (NOT --exclude, which nullifies #SBATCH --nodelist and lets the job land on a 3090):
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_phase10_powered.sh
#
# §10 REPOWERED behavioral-inertness of the CONCEPT circuit (powered, leakage-free, v3-POOLED).
#   arms: baseline · write_abl · carry_abl · write_carry_abl · rand_abl   (StrongReject-judged)
#   write = PhasedMLPZero (decode-safe, reused from phase_behav_write); carry = AllPositionZHeadAblate
#   (reused from phase_behav_carry); write+carry = both stacked; rand = count-matched specificity ctrl.
#   Primary = paired McNemar on ASR (baseline vs write_carry_abl), POOLED across both v3 cohorts and
#   all splits (n>=275 target for ΔASR=0.09); FROZEN-test reported as a confirmatory subset.
#   walltime 16:00 = 5 arms x ~324 items x 220 tokens (vs 3 arms in the older behav wrappers).
#   full:  sbatch --export=ALL,DSN=0 slurm/run_phase10_powered.sh
#   smoke: sbatch --export=ALL,DSN=2 slurm/run_phase10_powered.sh
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
# comma-list of v3 benches kept as a DEFAULT here (--export truncates comma values); POOLED for power.
: "${DSBENCHES:=doublespeak_causality/data/behavioral_v3/beh_clearharm.json,doublespeak_causality/data/behavioral_v3/beh_generated.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSMAXNEW:=220}"
: "${DSN:=0}"
: "${DSSPLITS:=train,dev,test}"   # comma-list DEFAULT (not via --export); all splits => pooled n>=275
: "${DSLAYERS:=8-11}"
: "${DSSEED:=0}"
: "${DSSAVEGEN:=1}"               # 1 = write gens.jsonl (default); 0 = --no-save-gen
DSFLAGS=""
[ "$DSSAVEGEN" = "1" ] && DSFLAGS="$DSFLAGS --save-gen" || DSFLAGS="$DSFLAGS --no-save-gen"
echo "=== p10 powered concept ablation: $DSMODEL benches=$DSBENCHES layers=$DSLAYERS maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS flags=$DSFLAGS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase10_powered_concept_ablation.py \
  --benches "$DSBENCHES" --model "$DSMODEL" --max-new "$DSMAXNEW" --layers "$DSLAYERS" \
  --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED" $DSFLAGS
echo "=== done ==="; date
