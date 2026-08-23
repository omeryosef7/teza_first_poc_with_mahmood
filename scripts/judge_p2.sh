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
MANIFEST=$R/outputs/boombness/argsfiles/p2_arms.txt
EXPECTED=5
N=$(grep -c ':' "$MANIFEST")
echo "[p2] manifest has $N rows (expected $EXPECTED)"
[ "$N" -eq "$EXPECTED" ] || { echo "[p2] REFUSING: cardinality $N != $EXPECTED" >&2; exit 2; }
date '+[p2] start %H:%M:%S'
i=0
while IFS=: read -r tag gens; do
  [ -n "$tag" ] || continue
  i=$((i+1))
  date "+[p2] launching $i/$N tag=p2j_${tag} at %H:%M:%S"
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" --tag "p2j_${tag}" &
  sleep 15
  if [ $((i % 3)) -eq 0 ]; then echo "[p2] wave boundary at $i"; wait; fi
done < "$MANIFEST"
wait
date "+[p2] ALL DONE, $i runs, %H:%M:%S"
