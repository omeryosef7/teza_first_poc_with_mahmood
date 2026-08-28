#!/bin/bash
# V-51: Phase 3.1 -- the aggressive POSITIVE patch, plus its sign-flip and matched random control.
# Judged with the baseline in ONE invocation. This is also ledger entry 4's rerun: the original
# steering evidence was cap-192 with 100% truncation.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_ticket_bomb.jsonl
for spec in \
  "p3j_base=$R/outputs/boombness/score_behavior/e6A_ticket_bomb_20260828_002321_882523" \
  "p3j_pos=$R/outputs/boombness/score_behavior/p3_add_pos_20260828_062646_3980322" \
  "p3j_neg=$R/outputs/boombness/score_behavior/p3_add_neg_20260828_062646_3980321" \
  "p3j_rand=$R/outputs/boombness/score_behavior/p3_rand_20260828_062646_1456768" ; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  echo "=== judging $tag ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260828 --tag "$tag"
done
