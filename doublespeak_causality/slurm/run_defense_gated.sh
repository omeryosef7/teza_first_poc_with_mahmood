#!/bin/bash
#SBATCH --job-name=ds_defgate
#SBATCH --output=doublespeak_causality/logs/ds_defgate_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_defgate_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- measured 2026-08-05, do not re-litigate: cpus=4 mem=48G is the fast-allocating
# default (8cpu/64G sat PENDING 3h32m; the SAME work at 4cpu/48G allocated in 6m32s). Mechanism: node
# RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=64G leaves only 7 of 8 GPUs
# memory-feasible per node while 48G leaves all 8. --time is NOT the lever.
# Every #SBATCH line below is a DEFAULT: the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_defense_gated.sh
# n-801 is a full gpu:l40s:8 node (1/6 of L40S capacity). Caveat over 232 logged runs: every weight-load
# slower than 15 min happened on n-801 (worst 79 min); no other L40S node ever exceeded 14 min. To avoid
# a node DO NOT use --exclude: passing --exclude on the sbatch line NULLIFIES this #SBATCH --nodelist and
# the job lands anywhere in the partition (that happened 2026-08-06 -> an RTX 3090; only the GPU guard
# caught it). Pass an explicit REDUCED NODELIST instead, e.g. to skip n-801:
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_defense_gated.sh
#
# MECHANISM-TRIGGERED (gated) refusal-restoration defense (plan §19.3): fire the §19-21 restoration ONLY
# when the decision-token refusal projection is anomalously LOW (suppressed), to rescue SELECTIVITY that
# the unconditional defense lacks. Threshold T is FIT ON TRAIN ONLY, frozen for test.
# SMOKE (2 items/split, quick sanity -- comma-lists are DEFAULTS below, never via --export which truncates):
#   sbatch --export=ALL,DSN=2 slurm/run_defense_gated.sh
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
: "${DSBENCH:=doublespeak_causality/data/behavioral_v3b/beh_clearharm.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSN:=0}"
: "${DSSPLITS:=train,test}"   # comma-list kept as a DEFAULT here (not via --export, which truncates)
: "${DSREFDIR:=doublespeak_causality/outputs/refusal_alllayers}"
: "${DSPROJ:=doublespeak_causality/outputs/refproj_clearharm_20260804_162641_711392/summary.json}"
: "${DSLAYER:=18}"            # single validated defense/readout layer (§0.5)
: "${DSPROJSPLIT:=train}"     # which proj-summary split supplies the calibrated alpha
# GATE threshold T (fit ON TRAIN ONLY, frozen for test). Leave both empty for the default fit
# (T = train mean of the Direct-harmful "refusing" projection). Set ONE of:
#   DSTHRESHPCT (percentile of the TRAIN Direct-harmful projection, e.g. 50 or 10), or
#   DSTHRESH    (an explicit fixed T, skips the fit).
: "${DSTHRESHPCT:=}"
: "${DSTHRESH:=}"
: "${DSMAXNEW:=200}"
: "${DSSEED:=0}"
echo "=== defense-gated: $DSMODEL bench=$DSBENCH layer=$DSLAYER threshpct='$DSTHRESHPCT' thresh='$DSTHRESH' maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
EXTRA=()
if [ -n "$DSTHRESHPCT" ]; then EXTRA+=(--threshold-percentile "$DSTHRESHPCT"); fi
if [ -n "$DSTHRESH" ]; then EXTRA+=(--threshold "$DSTHRESH"); fi
python -u doublespeak_causality/scripts/phase_defense_gated.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-dir "$DSREFDIR" --proj-summary "$DSPROJ" \
  --layer "$DSLAYER" --proj-split "$DSPROJSPLIT" --max-new "$DSMAXNEW" --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED" \
  "${EXTRA[@]}"
echo "=== done ==="; date
