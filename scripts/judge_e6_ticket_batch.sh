#!/bin/bash
# V-29: entry 6, population ticket_bomb, cap 640. Both arms in ONE invocation.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_ticket_bomb.jsonl
for spec in \
  "e6j_A_ticket=$R/outputs/boombness/score_behavior/e6A_ticket_bomb_20260828_002321_882523" \
  "e6j_C_ticket=$R/outputs/boombness/score_behavior/e6C_ticket_bomb_20260828_002302_2763864" ; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  echo "=== judging $tag ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260828 --tag "$tag"
done
