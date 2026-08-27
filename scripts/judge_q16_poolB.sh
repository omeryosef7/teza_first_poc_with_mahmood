#!/bin/bash
# PR-25: one-session judging of the five pool-B (longpreQ14B) arms.
#
# WHY ALL FIVE IN ONE SESSION. R6-6 established that comparing arms judged in different
# sessions produced a real artifact. The baseline q16A was already judged at 02:10 as the
# PR-25 power gate (tag xj_q_Q14B); it is RE-JUDGED here so that every number in the C7
# pool-B read comes from a single judge window. The power-gate judging stands as its own
# artifact and is not overwritten -- this writes new dirs under the q16j prefix.
#
# BANK: boombness_prompt_bank_longpreQ14B.jsonl (sha b2903479258a0f68), the bank all five
# runs were generated from. Passing --bank is mandatory (R4-4).
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/boombness_prompt_bank_longpreQ14B.jsonl
STAMP=q16j

ARMS=(
  "A:outputs/boombness/score_behavior/q16A_20260827_014106_689620"
  "demoproc:outputs/boombness/score_behavior/q16_demoproc_20260827_022535_694032"
  "d1:outputs/boombness/score_behavior/q16_matched_d1_20260827_024736_695408"
  "d2:outputs/boombness/score_behavior/q16_matched_d2_20260827_025736_696843"
  "d3:outputs/boombness/score_behavior/q16_matched_d3_20260827_025810_1051351"
)
for entry in "${ARMS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  if [ ! -f "$gens/gens.jsonl" ]; then echo "MISSING gens: $tag -> $gens"; exit 1; fi
  n=$(wc -l < "$gens/gens.jsonl")
  if [ "$n" -ne 160 ]; then echo "WRONG ROW COUNT $tag: $n != 160"; exit 1; fi
  if [ ! -f "$gens/DONE.json" ]; then echo "NOT DONE: $tag"; exit 1; fi
  python -u src/boombness/judge_boombness.py \
    --gens "$gens" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini \
    --tag "${STAMP}_${tag}" &
done
wait
echo "=== all judging done ==="
