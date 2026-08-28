#!/bin/bash
# V-44: the codeword x concept 2x2 (V-42). ticket_bomb already measured at 30/96 cap 640; these are
# the other three cells. All judged in ONE invocation so no cross-session judge noise enters the
# between-cell comparison.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
D=$R/data/boombness_prompts
for spec in \
  "x22_ticket_knife=$R/outputs/boombness/score_behavior/tk_ticket_knife_20260828_044227_2421528=$D/boombness_prompt_bank_ticket_knife.jsonl" \
  "x22_window_bomb=$R/outputs/boombness/score_behavior/tk_window_bomb_20260828_044435_2422133=$D/boombness_prompt_bank_window_bomb.jsonl" \
  "x22_window_knife=$R/outputs/boombness/score_behavior/tk_window_knife_20260828_044435_2422132=$D/boombness_prompt_bank_window_knife.jsonl" ; do
  tag="${spec%%=*}"; rest="${spec#*=}"; dir="${rest%%=*}"; bank="${rest#*=}"
  echo "=== judging $tag ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$bank" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260828 --tag "$tag"
done
