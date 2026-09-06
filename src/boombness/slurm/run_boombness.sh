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
# WIDENED 2026-08-24: n-804 was missing. `sinfo -N` shows SIX L40S nodes in killable
# (n-801..n-805, t-806); this list had five, so every job queued against 5/6 of the available
# hardware for no reason. n-804 also appears in the gpu-sharifm partition, which is group-gated
# and rejects this user -- but the NODE is reachable through killable like any other.
# Do NOT "fix" queueing by adding --exclude on the sbatch line: that nullifies this directive.
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
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

# SILENT-DEFAULT GUARD (2026-09-06, DCS-C-073). ADDITIVE and opt-in: nothing below changes what
# any existing caller does.
#
# WHY. `BOOMB_SCRIPT` defaults to `extract_boombness.py`. Jobs 853040-853045 were exported
# `ARGSFILE=...` -- a variable this runner never reads -- so all six fell through to that default,
# ran the WRONG SCRIPT, and exited `COMPLETED 0:0` in 11-27 minutes. ~1.7 GPU-hours lost, and
# nothing caught it: every artifact guard in this project checks a file that was never written,
# and a missing arm is indistinguishable from an unstarted one.
#
# Two cheap defences that cannot break a working caller:
#   1. say out loud whether BOOMB_SCRIPT was PROVIDED or DEFAULTED, so `grep` over the first ten
#      log lines answers "did this job run what I meant?" without reasoning about env plumbing;
#   2. honour an optional `BOOMB_EXPECT`. When set, it must equal the resolved BOOMB_SCRIPT or the
#      job refuses BEFORE the node does any work. A caller that sets it cannot be silently
#      defaulted, and a caller that does not is unaffected.
# The DCS thesis-scale phase sets BOOMB_EXPECT on every submission.
if [ -n "${BOOMB_SCRIPT:-}" ]; then _BOOMB_SCRIPT_ORIGIN=PROVIDED; else _BOOMB_SCRIPT_ORIGIN=DEFAULTED; fi
: "${BOOMB_SCRIPT:=extract_boombness.py}"
if [ -n "${BOOMB_EXPECT:-}" ] && [ "$BOOMB_EXPECT" != "$BOOMB_SCRIPT" ]; then
  echo "ERROR BOOMB_EXPECT='$BOOMB_EXPECT' but BOOMB_SCRIPT resolved to '$BOOMB_SCRIPT'"
  echo "  origin=$_BOOMB_SCRIPT_ORIGIN. If DEFAULTED, the variable you exported is not one this"
  echo "  runner reads (it reads BOOMB_SCRIPT / BOOMB_ARGSFILE / BOOMB_ARGS / BOOMB_EXPECT)."
  echo "  REFUSING: this is the 853040-853045 failure, which exits COMPLETED 0:0 and looks fine."
  exit 1
fi
if [ ! -f "src/boombness/$BOOMB_SCRIPT" ]; then
  echo "ERROR script not found: src/boombness/$BOOMB_SCRIPT (origin=$_BOOMB_SCRIPT_ORIGIN)"
  echo "  NOTE BOOMB_SCRIPT is a BARE FILENAME; this runner prepends src/boombness/."
  echo "  A script living elsewhere needs a relative path, e.g. ../../scripts/dcs_x.py"
  exit 1
fi
: "${BOOMB_ARGSFILE:=}"
: "${BOOMB_ARGS:=}"
if [ -n "$BOOMB_ARGSFILE" ]; then
  if [ ! -f "$BOOMB_ARGSFILE" ]; then echo "ERROR argsfile not found: $BOOMB_ARGSFILE"; exit 1; fi
  BOOMB_ARGS="$(cat "$BOOMB_ARGSFILE")"
  # QUOTE GUARD (2026-08-19). BOOMB_ARGS is deliberately word-split into flags below, so quote
  # characters in the file are NOT grouping -- they are literal argv characters, and any value
  # containing a space is silently torn into separate arguments. That killed job 766661 in five
  # seconds: a --skip-arms-reason written as "a long sentence" arrived as ["a] plus eight stray
  # positional args, and argparse rejected the run AFTER the node and GPU were allocated.
  # Refuse here instead: a multi-word value must be joined (underscores) by the caller.
  case "$BOOMB_ARGS" in
    *\"*|*\'*)
      echo "ERROR argsfile contains a quote character: $BOOMB_ARGSFILE"
      echo "  BOOMB_ARGS is word-split, so quotes do not group -- they become literal argv chars"
      echo "  and any value with a space is torn apart. Join multi-word values with underscores."
      grep -o "[\"'][^\"']*[\"']" "$BOOMB_ARGSFILE" | head -3
      exit 1 ;;
  esac
fi

echo "=== boombness: $BOOMB_SCRIPT ==="; date; hostname
echo "boomb_script_origin: $_BOOMB_SCRIPT_ORIGIN  expect=${BOOMB_EXPECT:-<unset>}  argsfile=${BOOMB_ARGSFILE:-<unset>}"
echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)  dirty=$(git status --porcelain 2>/dev/null | wc -l)"
echo "args: $BOOMB_ARGS"

# WRITABILITY GUARD (2026-09-02, DCS-002). The user quota on this filesystem is enforced at a limit
# the `quota` command does not display, and when it is reached every write fails EDQUOT -- on the
# COMPUTE NODES too, not just the login node. This has now silently truncated a run TWICE; run
# `d38beh_20260829_022027_2389958` is quarantined for exactly this, with 61 designed rows that no
# file comparison can see because the file simply stops.
#
# Why a real write and not `df`: df reported 5.4T free on the volume while a 100-byte write returned
# EDQUOT, because the binding limit is a qtree/user quota, not volume space. And why 10MB and not a
# few bytes: the failure is SIZE-DEPENDENT at the boundary -- a 5-byte write SUCCEEDED in the same
# second a 100-byte write failed, so a token `touch` reports healthy while every real artifact fails.
#
# Refuse here, before the model is loaded, rather than after hours of GPU time have produced rows
# that cannot be persisted. A crash is a better failure than a silent skip.
_WGUARD="$PROJECT_DIR/outputs/boombness/.writeguard_$$"
if ! head -c 10000000 /dev/zero > "$_WGUARD" 2>/dev/null || [ "$(stat -c %s "$_WGUARD" 2>/dev/null)" != "10000000" ]; then
  echo "ERROR cannot write 10MB to outputs/ -- disk quota is exhausted (EDQUOT)."
  echo "  Wrote: $(stat -c %s "$_WGUARD" 2>/dev/null || echo 0) of 10000000 bytes"
  echo "  quota: $(quota 2>/dev/null | tail -1)"
  echo "  REFUSING to start: this run would consume GPU time and fail to persist its rows."
  rm -f "$_WGUARD"
  exit 1
fi
rm -f "$_WGUARD"
echo "write guard ok: 10MB round-trip to outputs/"

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
