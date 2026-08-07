#!/bin/bash
#SBATCH --job-name=ds_defutil
#SBATCH --output=doublespeak_causality/logs/ds_defutil_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_defutil_%j.err
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
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_defense_utility.sh
# n-801 is a full gpu:l40s:8 node (1/6 of L40S capacity). Caveat over 232 logged runs: every weight-load
# slower than 15 min happened on n-801 (worst 79 min); no other L40S node ever exceeded 14 min. To avoid
# a node DO NOT use --exclude: passing --exclude on the sbatch line NULLIFIES this #SBATCH --nodelist and
# the job lands anywhere in the partition (that happened 2026-08-06 -> an RTX 3090; only the GPU guard
# caught it). Pass an explicit REDUCED NODELIST instead, e.g. to skip n-801:
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_defense_utility.sh
#
# Calibrated refusal restoration as a DEFENSE + its utility cost (plan §19-21 Gate F) on the v3b
# confirmatory cohort. ATTACK arms (Doublespeak) should DROP in ASR; BENIGN arms should NOT over-refuse.
# SMOKE (2 items/split, quick sanity -- comma-lists are DEFAULTS below, never via --export which truncates):
#   sbatch --export=ALL,DSN=2 slurm/run_defense_utility.sh
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
: "${DSLAYERS:=16,18,20}"     # validated defense layers (§0.5); comma-list = DEFAULT (never --export)
# Dose sweep (plan §21 minimal effective intervention): multipliers on the calibrated per-layer alpha.
# COMMA-LIST -> set it here as a DEFAULT (edit this line, or `export DSDOSESCALES=... ; sbatch ...`),
# NEVER via `sbatch --export=ALL,DSDOSESCALES=0.25,0.5,...` -- --export truncates at the first comma.
# Default "1.0" reproduces the fixed-dose run byte-for-byte (arms stay un-suffixed).
: "${DSDOSESCALES:=1.0}"
: "${DSPROJSPLIT:=train}"
: "${DSMAXNEW:=200}"
: "${DSSEED:=0}"
echo "=== defense-util: $DSMODEL bench=$DSBENCH layers=$DSLAYERS dose=$DSDOSESCALES maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase_defense_utility.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-dir "$DSREFDIR" --proj-summary "$DSPROJ" \
  --layers "$DSLAYERS" --dose-scales "$DSDOSESCALES" --proj-split "$DSPROJSPLIT" --max-new "$DSMAXNEW" --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED"
echo "=== done ==="; date
