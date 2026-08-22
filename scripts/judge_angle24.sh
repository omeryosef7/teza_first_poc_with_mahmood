#!/bin/bash
# Judge the 8 new angles per depth (of24, odd k) plus a fresh baseline.
#
# WHY THE BASELINE IS RE-JUDGED HERE. Each control's delta is taken against a baseline; a control
# judged in a different session from its baseline carries that session's offset. Measured earlier:
# re-judging identical generations moved baseline ASR 0.1714 -> 0.1595 while a PAIRED delta
# reproduced to four decimals. So deltas transport across sessions and raw ASRs do not -- provided
# each delta is formed within a session. Re-judging the baseline today costs 495 calls and makes
# the 8 new deltas internally session-matched, exactly as the existing 12 are to theirs.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
SB=outputs/boombness/score_behavior

RUNS=("base:$SB/ab_base_20260818_185458_3888976")
for L in 6 8; do
  for k in 1 3 5 7 9 11 13 15; do
    d=$(ls -d $SB/ang${L}k${k}of24_* 2>/dev/null | tail -1)
    [ -n "$d" ] || { echo "MISSING ang${L}k${k}of24"; exit 1; }
    RUNS+=("L${L}k${k}:$d")
  done
done
for e in "${RUNS[@]}"; do
  t="${e%%:*}"; g="${e#*:}"
  n=$(wc -l < "$g/gens.jsonl"); [ "$n" -eq 495 ] || { echo "WRONG ROWS $t: $n"; exit 1; }
done
echo "[a24] ${#RUNS[@]} runs verified at 495 rows"
i=0
for e in "${RUNS[@]}"; do
  t="${e%%:*}"; g="${e#*:}"
  python -u src/boombness/judge_boombness.py --gens "$g" --bank "$BANK" --tag "a24_${t}" &
  i=$((i+1)); if [ $((i % 6)) -eq 0 ]; then wait; fi
done
wait
echo "=== a24 judging done ==="
