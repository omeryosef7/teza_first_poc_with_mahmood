#!/bin/bash
# xL6 CROSSOVER — re-judge L6 angle controls from TWO original judging sessions in ONE new session.
#
# WHY. null_ceiling_session_check found that L6's null ceiling is set by three controls judged in
# session 20260822_165021 (mean +5.0 prompts), while five controls judged in 20260822_163302 -- the
# only control session in the whole sweep with a baseline of its own -- sit at +0.4. The two are 17
# minutes apart in the same submission wave. The arm-vs-ceiling margin at L6 is 4 prompts, so a
# session offset of that size decides the verdict.
#
# That difference is CONFOUNDED: session is confounded with which angles were judged in it. No angle
# in the sweep has ever been judged twice (checked: 0 of 80), so the confound cannot be resolved from
# existing data.
#
# THE DESIGN. Judge all eight angles -- k=1,3,5,7,9 (from 163302) and k=11,13,15 (from 165021) --
# together in ONE new session, with a baseline judged in that same session.
#   * if k=11,13,15 still sit ~5 prompts above k=1..9, the difference is the ANGLES: the ceiling is
#     real and L6's margin is genuinely 4 prompts.
#   * if they converge, the difference was the SESSION: the ceiling was an artifact and the whole
#     cross-session construction of the null needs revisiting, not just L6.
# Either answer is worth having, which is the point of running it.
#
# The generations are byte-identical to what was judged before (same gens dirs, all 495 rows, DONE),
# and were all produced in one generation wave 15:37-15:42, so generation conditions are not a
# competing explanation.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
SB=$R/outputs/boombness/score_behavior

declare -a PAIRS=(
  "base:$SB/ab_base_20260818_185458_3888976"
  "k1:$SB/ang6k1of24_20260822_153720_3114711"
  "k3:$SB/ang6k3of24_20260822_153720_3114712"
  "k5:$SB/ang6k5of24_20260822_153747_3900610"
  "k7:$SB/ang6k7of24_20260822_153747_3900608"
  "k9:$SB/ang6k9of24_20260822_153747_3900607"
  "k11:$SB/ang6k11of24_20260822_153747_3900609"
  "k13:$SB/ang6k13of24_20260822_153747_3900606"
  "k15:$SB/ang6k15of24_20260822_154205_66256"
)

# Verify EVERY input before spending a single API call: 495 rows and DONE, or refuse the batch.
for entry in "${PAIRS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  if [ ! -f "$gens/gens.jsonl" ]; then echo "MISSING gens for $tag: $gens"; exit 1; fi
  if [ ! -f "$gens/DONE.json" ]; then echo "NOT DONE for $tag: $gens"; exit 1; fi
  n=$(wc -l < "$gens/gens.jsonl")
  if [ "$n" -ne 495 ]; then echo "WRONG ROWS $tag: $n"; exit 1; fi
  echo "[xL6] $tag <- $(basename $gens) ($n rows)"
done

for entry in "${PAIRS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" --tag "xL6_${tag}" &
done
wait
echo "=== xL6 crossover judging done ==="
