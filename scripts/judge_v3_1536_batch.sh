#!/bin/bash
# V-22: the d_surface project-out arm and its baseline at cap 1536, judged in ONE invocation.
# At 640 the ARM's cap bound on 0.302 of rows, so --require-sprint-grade refused it (V-19).
# Section 0.2's pre-registered rule is to raise the cap until it does not bind; both arms are
# re-run and re-judged, never just the one that failed.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_basket_bomb.jsonl
for spec in \
  "j1536_A=$R/outputs/boombness/score_behavior/v3_A1536_20260827_225209_3133325" \
  "j1536_W=$R/outputs/boombness/score_behavior/v3_W1536_20260827_225215_2220789" ; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  echo "=== judging $tag ==="
  python -u $R/src/boombness/judge_boombness.py \
    --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260827 --tag "$tag"
done
