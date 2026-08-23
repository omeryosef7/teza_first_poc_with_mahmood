#!/bin/bash
# Gate E7 -- does the exp-7 directional effect survive a REAL between-seed control band?
#
# Reuses analyze_external_arms.py unchanged: it already implements --band (>=3 draws) AND the R-12
# guard that REFUSES a band whose draws are not distinct (it fingerprints the source generations,
# because the historical failure was a "3-draw band" that was one draw stated three times).
#
# ALL SEVEN ARMS COME FROM ONE JUDGING SESSION (job 776397). The point of re-judging dS50 and rnd50
# here, when they already had scores from the `unlk` session, is that an arm-vs-control contrast
# does NOT cancel cross-session drift -- only a paired arm-vs-baseline delta does, where the
# baseline is removed algebraically. Reading a fresh band against an old arm is the confound that
# produced the L6 reversal.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
J=$R/outputs/boombness/judge
d(){ ls -d $J/p1a_$1_* 2>/dev/null | tail -1; }

for t in base dS50 rnd50 rnd75 r01 r02 r03; do
  p=$(d $t)
  [ -n "$p" ] || { echo "MISSING judge dir for $t" >&2; exit 3; }
  [ -f "$p/DONE.json" ] || { echo "NOT DONE: $t" >&2; exit 3; }
  n=$(wc -l < "$p/results.jsonl")
  [ "$n" -eq 495 ] || { echo "SHORT: $t has $n rows, expected 495" >&2; exit 3; }
  echo "  ok $t -> $(basename $p) ($n rows)"
done

python -u src/boombness/analyze_external_arms.py \
  --baseline "$(d base)" \
  --arm "dS50=$(d dS50)" \
  --arm "rnd75=$(d rnd75)" \
  --band "rnd50=$(d rnd50)" \
  --band "r01=$(d r01)" \
  --band "r02=$(d r02)" \
  --band "r03=$(d r03)" \
  --label "Gate E7 (one judging session, job 776397): d_surface:add at 0.5 gap on AdvBench-495, against a 4-draw matched random:add band at the same dose" \
  --out "$R/outputs/boombness_followup/gate_e7_band.json"
echo "=== GATE E7 ARTIFACT WRITTEN ==="
