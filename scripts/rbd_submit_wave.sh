#!/bin/bash
# RBD confirmatory matrix submitter. Holds a fixed number of jobs in flight and submits the next
# argsfile only when a slot frees, so the sprint's SLURM rules are enforced by the driver rather
# than by the operator remembering them:
#   * MAX_INFLIGHT caps total concurrent jobs (house rule: <=6).
#   * For Qwen3-14B the cap must be 2 -- the documented "2 per NODE" rule was measured
#     INSUFFICIENT (jobs 781410-781413 sat at 0 rows for 16-28 min at that cap because the
#     bottleneck is shared NFS, not the node), so the real limit is 2 concurrent 14B loads TOTAL.
#   * Never scancel a waiting job to make progress; this script only ever ADDS.
# Usage: MAX_INFLIGHT=6 bash scripts/rbd_submit_wave.sh runargs/rbd/rbdplp*.txt
set -uo pipefail
R="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$R"
: "${MAX_INFLIGHT:=6}"
declare -a SUBMITTED=()
for f in "$@"; do
  while true; do
    n=$(squeue -u "$USER" -h -o "%i" 2>/dev/null | wc -l)
    [ "$n" -lt "$MAX_INFLIGHT" ] && break
    sleep 45
  done
  jid=$(sbatch --parsable --export=ALL,BOOMB_SCRIPT=score_behavior.py,BOOMB_ARGSFILE="$R/$f" \
        src/boombness/slurm/run_boombness.sh 2>&1)
  echo "submitted $(basename "$f" .txt) -> $jid"
  SUBMITTED+=("$jid")
  sleep 8
done
echo "=== all ${#SUBMITTED[@]} submitted: ${SUBMITTED[*]} ==="
