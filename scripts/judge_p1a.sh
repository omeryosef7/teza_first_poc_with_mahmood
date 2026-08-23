#!/bin/bash
# Phase 1A -- Gate E7, judged as ONE session against ONE baseline.
#
# WHY THIS EXISTS RATHER THAN REUSING judge_band2.sh.
# band2 judges the three new control draws (r01/r02/r03) fresh, but leaves the arm (dS50) and the
# original single control (rnd50) in the OLDER `unlk` judging session. The contrast that decides
# Gate E7 -- dS50 minus rnd50, read against the r01..r03 band -- would then span two sessions.
# Cross-session drift does NOT cancel in an arm-vs-control contrast (it cancels only in a paired
# arm-vs-baseline delta, where the baseline is algebraically removed). That is the exact confound
# that produced the L6 reversal and the F-3 retraction. So every arm in the Gate E7 family is
# re-judged here, together, including the two that already have scores.
#
# STAGGERED LAUNCH, 3 AT A TIME.
# The precedent batch (776368) launched six `python -u` processes simultaneously and produced ZERO
# bytes of output and ZERO RunDirs in 11 minutes, while its own predecessor (774835) created its
# first RunDir within a minute. Six concurrent cold imports of torch/transformers/openai off NFS is
# the leading explanation. This launches 3 at a time with a stagger, and echoes before each so a
# hang is distinguishable from slowness in the log rather than by inference.
#
# MANIFEST IS ON THE SHARED FS. /tmp is node-local: a manifest written on the login node reads as
# EMPTY on the compute node, the loop runs zero iterations, and the job exits 0 claiming success.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
export BOOMB_GIT_COMMIT="${BOOMB_GIT_COMMIT:-unknown}"

BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
MANIFEST=$R/outputs/boombness/argsfiles/p1a_gateE7.txt

# Cardinality assert BEFORE spending anything: an empty or short manifest must fail loudly, not
# silently judge nothing and exit 0.
EXPECTED=7
N=$(grep -c ':' "$MANIFEST")
echo "[p1a] manifest $MANIFEST has $N rows (expected $EXPECTED)"
if [ "$N" -ne "$EXPECTED" ]; then
  echo "[p1a] REFUSING: manifest cardinality $N != $EXPECTED" >&2
  exit 2
fi
echo "[p1a] bank=$BANK"
echo "[p1a] commit=$BOOMB_GIT_COMMIT"
date '+[p1a] start %H:%M:%S'

i=0
while IFS=: read -r tag gens; do
  [ -n "$tag" ] || continue
  i=$((i+1))
  date "+[p1a] launching $i/$N tag=p1a_${tag} at %H:%M:%S"
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" --tag "p1a_${tag}" &
  sleep 20                      # stagger the cold imports off NFS
  if [ $((i % 3)) -eq 0 ]; then
    echo "[p1a] wave boundary at $i -- waiting"
    wait
    date '+[p1a] wave done %H:%M:%S'
  fi
done < "$MANIFEST"
wait
date "+[p1a] ALL DONE, $i runs judged, %H:%M:%S"
