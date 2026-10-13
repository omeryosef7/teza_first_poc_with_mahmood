#!/bin/bash
# HERETIC-CSI Phase B (mandate §6): native last-position Heretic ARA as a CONTROL on our frozen populations.
#SBATCH --job-name=hcsi_phaseB
#SBATCH --output=outputs/heretic_csi/logs/phaseB_%j.out
#SBATCH --error=outputs/heretic_csi/logs/phaseB_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=10:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=l40s:1
#SBATCH --exclude=n-803
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
PY=/specific/scratches/scratch/omeryosef/envs/heretic_csi/bin/python
export PYTHONUNBUFFERED=1
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1
export HF_DATASETS_CACHE=/specific/scratches/scratch/omeryosef/cache/hf_datasets
# verified mirror (SHA256SUMS) of matanbentov HF snapshot 0e9e39f249a16976918f6564b8830bc894c89659
SNAP=/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2
ATT="${SLURM_JOB_ID:-none}_r${SLURM_RESTART_COUNT:-0}_$(date +%s)"
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} RESTART=${SLURM_RESTART_COUNT:-0} ATT=$ATT $(date -Is)"
nvidia-smi --query-gpu=name,compute_cap,driver_version --format=csv,noheader || true

export TMPDIR="${SLURM_TMPDIR:-/tmp/${USER}/${SLURM_JOB_ID:-$$}}"
mkdir -p "$TMPDIR" 2>/dev/null || { export TMPDIR=/specific/scratches/scratch/omeryosef/tmp/job_${SLURM_JOB_ID:-$$}; mkdir -p "$TMPDIR"; echo "node /tmp unusable -> TMPDIR=$TMPDIR"; }
trap 'rm -rf "$TMPDIR/llama31" 2>/dev/null || true' EXIT TERM INT
AVAIL_KB=$(df --output=avail -k "$TMPDIR" 2>/dev/null | tail -1 || echo 0)
if [ "${AVAIL_KB:-0}" -lt 18000000 ]; then
  echo "STAGE_IN SKIPPED: node-local ${AVAIL_KB}KB < 18G -> loading directly from the scratch mirror $SNAP"
else
  mkdir -p "$TMPDIR/llama31"
  echo "STAGE_IN start $(date -Is)"
  if cp -L "$SNAP"/*.safetensors "$SNAP"/*.json "$SNAP"/tokenizer* "$TMPDIR/llama31/" 2>/dev/null; then
    SNAP="$TMPDIR/llama31"; echo "STAGE_IN done $(date -Is) model=$SNAP"
  else echo "STAGE_IN FAILED -- loading from mirror $SNAP"; fi
fi

CW="${1:?usage: sbatch phaseB_native_ara.slurm <basket|button> [NTRIALS] [NRAND]}"
NT="${2:-16}"; NR="${3:-39}"
case "$CW" in
  basket) XC=outputs/boombness/score_behavior/hcsi_p2a_basket_BASE_20261003_011736_2629822,outputs/boombness/score_behavior/hcsi_p2a_basket_BASE_20261003_095601_2131856 ;;
  button) XC=outputs/boombness/score_behavior/hcsi_p2a_button_BASE_20261003_012037_2630629,outputs/boombness/score_behavior/hcsi_p2a_button_BASE_20261003_095601_2131858 ;;
  *) XC="" ;;
esac
"$PY" research/heretic_csi/phaseB_native_ara.py --codeword "$CW" --model "$SNAP" \
  --workdir /specific/scratches/scratch/omeryosef/hcsi_work/phaseB_$CW \
  --blob-dir /specific/scratches/scratch/omeryosef/hcsi_blobs/phaseB_$CW \
  --out-dir reports/heretic_csi/phaseB --rank 50 --n-trials "$NT" --n-startup 8 --n-rand "$NR" --n-shuffle 3 --extra-ranks 1,8 --xcheck-run-dirs "$XC"
echo "---- PHASEB EXIT $(date -Is)"
echo "DONE_MARKER phaseB cw=$CW att=$ATT"
