#!/bin/bash
#SBATCH --job-name=ds_p5pos
#SBATCH --output=doublespeak_causality/logs/ds_p5pos_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p5pos_%j.err
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
# RESOURCE FOOTPRINT -- cpus=4 mem=48G is the fast-allocating default for the 8B on L40S (measured
# 2026-08-05, see run_defense_utility.sh: --mem=64G leaves only 7/8 GPUs memory-feasible per node while
# 48G leaves all 8; --time is NOT the allocation lever). Generation over ~9 arms/item is the cost, so
# --time is generous (8h). Every #SBATCH line is a DEFAULT overridable by the matching sbatch flag with
# no file edit, e.g.  sbatch --time=04:00:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_phase5_position.sh
# DO NOT use --exclude (it NULLIFIES the #SBATCH --nodelist and the job can land on a non-L40S GPU that
# only the guard below catches); pass an explicit REDUCED --nodelist to skip a node (e.g. slow n-801).
#
# §5 position/content causality: matched DEMO-TEXT variants (full / neutral / mapping_altered /
# codeword_randomized / benign_format / shuffled / reduced_count / single_demo + direct reference).
# Measures decision-token refusal projection (reused proj_last, §3), ASR (reused generate+judge,
# defense_utility), and p_concept (reused forced-choice, phase3). FLAGGED not-constructible: demo_answers_removed.
# SMOKE (2 items/split, short gen; comma-lists are DEFAULTS below, NEVER via --export which truncates):
#   sbatch --export=ALL,DSN=2,DSMAXNEW=64 slurm/run_phase5_position.sh
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
: "${DSREFDIR:=doublespeak_causality/outputs/refusal_alllayers}"
: "${DSANCHOR:=18}"
: "${DSSPLITS:=train,test}"   # comma-list kept as a DEFAULT here (not via --export, which truncates)
: "${DSARMS:=direct,full,neutral,mapping_altered,codeword_randomized,benign_format,shuffled,reduced_count,single_demo}"  # comma-list = DEFAULT (never --export)
: "${DSMAXNEW:=200}"
: "${DSENABLETHINK:=default}"  # thinking models (Qwen3): default|true|false
: "${DSN:=0}"
: "${DSSEED:=0}"
echo "=== phase5-position: $DSMODEL bench=$DSBENCH anchor=L$DSANCHOR arms=$DSARMS maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS think=$DSENABLETHINK ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase5_position.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-dir "$DSREFDIR" --readout-anchor "$DSANCHOR" \
  --arms "$DSARMS" --splits "$DSSPLITS" --max-new "$DSMAXNEW" --enable-thinking "$DSENABLETHINK" \
  --n "$DSN" --seed "$DSSEED"
echo "=== done ==="; date