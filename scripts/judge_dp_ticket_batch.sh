#!/bin/bash
# V-35: demo_processing_only on ticket_bomb, cap 640 -- the cell separating SCOPE from BANK.
# Judged against the SAME baseline used for the legacy arm (e6A_ticket_bomb), re-judged here so the
# three-way comparison (baseline / legacy / demoproc) sits inside ONE invocation.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_ticket_bomb.jsonl
for spec in \
  "dpj_A_ticket=$R/outputs/boombness/score_behavior/e6A_ticket_bomb_20260828_002321_882523" \
  "dpj_L_ticket=$R/outputs/boombness/score_behavior/e6C_ticket_bomb_20260828_002302_2763864" \
  "dpj_D_ticket=$R/outputs/boombness/score_behavior/dp_ticket_behav_20260828_022509_1185303" ; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  echo "=== judging $tag ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260828 --tag "$tag"
done
