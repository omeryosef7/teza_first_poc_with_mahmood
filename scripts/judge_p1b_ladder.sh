#!/bin/bash
# Phase 1B -- the L12 dose ladder, judged as ONE session against ONE baseline.
#
# Fourteen arms spanning alpha 0.03 -> 1.0 plus two controls. The point of one session is that the
# ladder is read as a CURVE: a rung judged in a different session carries a drift that does not
# cancel in a rung-to-rung comparison, and the whole shape is the result here.
#
# Staggered 3-at-a-time: six simultaneous cold imports off NFS delayed an earlier batch by ~13
# minutes with zero output, which is indistinguishable from a hang until you know the script has no
# progress echo. This one echoes before every launch.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
MANIFEST=$R/outputs/boombness/argsfiles/p1b_ladder_L12.txt
EXPECTED=14
N=$(grep -c ':' "$MANIFEST")
echo "[p1b] manifest has $N rows (expected $EXPECTED)"
[ "$N" -eq "$EXPECTED" ] || { echo "[p1b] REFUSING: cardinality $N != $EXPECTED" >&2; exit 2; }
date '+[p1b] start %H:%M:%S'
i=0
while IFS=: read -r tag gens; do
  [ -n "$tag" ] || continue
  i=$((i+1))
  date "+[p1b] launching $i/$N tag=p1b_${tag} at %H:%M:%S"
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" --tag "p1b_${tag}" &
  sleep 15
  if [ $((i % 3)) -eq 0 ]; then echo "[p1b] wave boundary at $i"; wait; fi
done < "$MANIFEST"
wait
date "+[p1b] ALL DONE, $i runs, %H:%M:%S"
