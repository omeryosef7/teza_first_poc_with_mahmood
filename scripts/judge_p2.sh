#!/bin/bash
# PHASE 2 -- all five arms judged in ONE session against one baseline.
#
# WHY ONE SESSION. The headline is a RECOVERY FRACTION, (ASR_A - ASR_arm) / (ASR_A - ASR_B). Both
# the numerator and the denominator are arm-vs-arm contrasts, and cross-session judge drift does NOT
# cancel in those -- it cancels only in a paired arm-vs-baseline delta where the baseline is removed
# algebraically. Gate E7 was rendered unreadable by exactly this, and job 776368's design repeated
# it. A ratio built from two contrasts is twice as exposed.
#
# Staggered 3 at a time with an echo before each launch: a silent script made a 13-minute NFS import
# stall indistinguishable from a hang earlier today, and I drafted a cancellation twice on that.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/boombness_prompt_bank.jsonl
# PARAMETERISED so one driver serves several phases. A near-copy of this file for Phase 3 is how two
# scripts drift apart and one quietly keeps an old assertion.
MANIFEST=${P2_MANIFEST:-$R/outputs/boombness/argsfiles/p2_arms.txt}
EXPECTED=${P2_EXPECTED:-5}
PREFIX=${P2_PREFIX:-p2j}
EXPECT_ROWS=${P2_EXPECT_ROWS:-96}
N=$(grep -c ':' "$MANIFEST")
echo "[p2] manifest has $N rows (expected $EXPECTED)"
[ "$N" -eq "$EXPECTED" ] || { echo "[p2] REFUSING: cardinality $N != $EXPECTED" >&2; exit 2; }
date '+[p2] start %H:%M:%S'
i=0; PIDS=""; TAGS=""
# reap: wait on each PID individually so a non-zero exit is seen. `wait` with no args cannot fail.
reap() {
  for pid in $PIDS; do
    if ! wait "$pid"; then echo "[p2] REFUSING: judge pid $pid exited non-zero" >&2; exit 3; fi
  done
  PIDS=""
}
while IFS=: read -r tag gens; do
  [ -n "$tag" ] || continue
  i=$((i+1))
  date "+[p2] launching $i/$N tag=p2j_${tag} at %H:%M:%S"
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" --tag "${PREFIX}_${tag}" &
  PIDS="$PIDS $!"; TAGS="$TAGS ${PREFIX}_${tag}"
  sleep 15
  if [ $((i % 3)) -eq 0 ]; then echo "[p2] wave boundary at $i"; reap; fi
done < "$MANIFEST"
reap
# A bare `wait` returns 0 unconditionally even under `set -euo pipefail`, so a judge that died
# mid-wave was invisible: the script printed ALL DONE and exited 0, and the analysis then silently
# omitted an arm. Review finding S1. Reap each PID individually and assert the count.
[ "$i" -eq "$N" ] || { echo "[p2] REFUSING: launched $i of $N" >&2; exit 4; }
for t in $TAGS; do
  d=$(ls -dt "$R/outputs/boombness/judge/${t}_"*/ 2>/dev/null | head -1)
  [ -n "$d" ] || { echo "[p2] REFUSING: no judge dir for $t" >&2; exit 5; }
  [ -f "$d/DONE.json" ] || { echo "[p2] REFUSING: $t has no DONE.json" >&2; exit 5; }
  n=$(wc -l < "$d/results.jsonl")
  [ "$n" -eq "$EXPECT_ROWS" ] || { echo "[p2] REFUSING: $t has $n rows, expected $EXPECT_ROWS" >&2; exit 5; }
  echo "  verified $t ($n rows)"
done
date "+[p2] ALL DONE, $i runs, %H:%M:%S"
