#!/bin/bash
#SBATCH --job-name=boomb
#SBATCH --output=outputs/boombness/logs/boomb_%j.out
#SBATCH --error=outputs/boombness/logs/boomb_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-805,t-806
#
# Generic wrapper for every GPU stage of the Boombness sprint
# (docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md). One script, selected by BOOMB_SCRIPT.
#
# RESOURCE FOOTPRINT: cpus=4 mem=48G is the house fast-allocating default, measured 2026-08-05 —
# node RealMemory/8 GPUs = 64450MB per GPU-share, so --mem=64G leaves only 7 of 8 GPUs feasible
# per node while 48G leaves all 8. --time is not the lever. Do NOT raise these without a reason.
#
# NODELIST: n-804 / n-602 / n-301 are excluded by omission, NOT by --exclude. Passing --exclude on
# the sbatch line NULLIFIES this #SBATCH --nodelist and the job lands anywhere in the partition
# (that happened 2026-08-06 -> an RTX 3090; only the GPU guard caught it). To skip a further node,
# pass a REDUCED --nodelist instead, e.g.
#   sbatch --nodelist=n-802,n-803,n-805,t-806 src/boombness/slurm/run_boombness.sh
# n-801 is in the list but every weight load slower than 15 min in 232 logged runs happened there.
#
# ARGS are passed through BOOMB_ARGS as a single string. Note the house trap: --export with a
# comma-containing value TRUNCATES silently (feedback_sbatch_export_comma), so any comma list must
# be quoted inside BOOMB_ARGS and BOOMB_ARGS itself passed via a file or with commas intact only
# when it is the LAST --export entry. Safest form used below: write the args to a file.
#
# Usage:
#   # smoke (plan §2.3: 2-4 prompts first, always)
#   sbatch --export=ALL,BOOMB_SCRIPT=extract_boombness.py,BOOMB_ARGSFILE=/path/args.txt \
#          src/boombness/slurm/run_boombness.sh
#
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p outputs/boombness/logs outputs/boombness "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONUNBUFFERED=1

: "${BOOMB_SCRIPT:=extract_boombness.py}"
: "${BOOMB_ARGSFILE:=}"
: "${BOOMB_ARGS:=}"
if [ -n "$BOOMB_ARGSFILE" ]; then
  if [ ! -f "$BOOMB_ARGSFILE" ]; then echo "ERROR argsfile not found: $BOOMB_ARGSFILE"; exit 1; fi
  BOOMB_ARGS="$(cat "$BOOMB_ARGSFILE")"
fi

echo "=== boombness: $BOOMB_SCRIPT ==="; date; hostname
echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)  dirty=$(git status --porcelain 2>/dev/null | wc -l)"
echo "args: $BOOMB_ARGS"

# GPU guard. The first line of nvidia-smi only: a job that lands on a mixed node must still fail
# rather than silently run bfloat16 flash attention on a card that cannot do it.
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"
GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in
  *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE" ;;
  *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1 ;;
esac

# shellcheck disable=SC2086  # BOOMB_ARGS is intentionally word-split into flags
python -u "src/boombness/$BOOMB_SCRIPT" $BOOMB_ARGS
echo "=== done ==="; date
