#!/bin/bash
# HERETIC-CSI P2b generic GPU job: stage the pinned Llama snapshot to node-local disk ONCE, then run a
# PLAN script (bash) that calls p2b_emit/p2b_runner/p2b_fit with $SNAP. Same staging + bf16-native-GPU
# rules as rescue_sweep.slurm (S-014/S-029). --no-requeue: a preempted job is NOT silently re-run (S-051);
# the runner's --expect-n skip-if-done makes a manual resubmission resume without duplicate run dirs.
#SBATCH --job-name=hcsi_p2b
#SBATCH --output=outputs/heretic_csi/logs/p2b_%j.out
#SBATCH --error=outputs/heretic_csi/logs/p2b_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=110G
#SBATCH --time=23:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=a5000:1
#SBATCH --no-requeue
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1
export PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
PLAN="${1:?usage: sbatch p2b_job.slurm <plan.sh>}"
export ATTEMPT="${SLURM_JOB_ID:-0}_r${SLURM_RESTART_COUNT:-0}"
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} ATTEMPT=$ATTEMPT PLAN=$PLAN $(date -Is)"
nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv,noheader || true
ls /specific/scratches/scratch/omeryosef/hcsi_p2b >/dev/null || { echo "SCRATCH_NOT_VISIBLE"; exit 1; }
export TMPDIR="${SLURM_TMPDIR:-/tmp/${USER}/${SLURM_JOB_ID:-$$}}"
mkdir -p "$TMPDIR"
trap 'rm -rf "$TMPDIR/llama31" 2>/dev/null || true' EXIT TERM INT
AVAIL_KB=$(df --output=avail -k "$TMPDIR" 2>/dev/null | tail -1 || echo 0)
if [ "${AVAIL_KB:-0}" -lt 18000000 ]; then echo "INSUFFICIENT_TMP ${AVAIL_KB}KB"; exit 1; fi
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
# Prefer the VERIFIED byte-identical copy on /specific/scratches (home-fs, a different server from the
# contended netapp): LFS shards' sha256 == HF blob names, small files cmp-identical (F2, 2026-10-13).
# netapp staging ran at ~2 MB/s under contention (job 1022701: 1h46m for 15G).
SCR=/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2
[ -f "$SCR/VERIFIED" ] && SNAP="$SCR" && echo "STAGE_SOURCE scratch-verified $SCR" || echo "STAGE_SOURCE netapp $SNAP"
mkdir -p "$TMPDIR/llama31"
echo "STAGE_IN start $(date -Is)"
if cp -L "$SNAP"/*.safetensors "$SNAP"/*.json "$SNAP"/tokenizer* "$SNAP"/special_tokens_map.json "$TMPDIR/llama31/" 2>/dev/null; then
  SNAP="$TMPDIR/llama31"; echo "STAGE_IN done $(date -Is) $(du -sh $SNAP | cut -f1)"
else echo "STAGE_IN FAILED -- NFS fallback"; fi
export SNAP
# CODE PROVENANCE (review #8): snapshot every research/heretic_csi source this job could run, at job start.
CODEDIR=outputs/heretic_csi/p2b/code_snapshots/${ATTEMPT}; mkdir -p $CODEDIR
cp research/heretic_csi/*.py "$PLAN" $CODEDIR/ && sha256sum $CODEDIR/* > $CODEDIR/SHA256SUMS && echo "CODE_SNAPSHOT $CODEDIR"
set +e
bash "$PLAN"
RC=$?
set -e
echo "---- P2B JOB DONE rc=$RC $(date -Is) HOST=$(hostname)"
echo "DONE_MARKER plan=$PLAN attempt=$ATTEMPT rc=$RC"
