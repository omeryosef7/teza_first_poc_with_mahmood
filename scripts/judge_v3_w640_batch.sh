#!/bin/bash
# V-18: the d_surface project-out arm at cap 640 AND its baseline, judged in ONE invocation.
# The baseline g3A640 already has a pinned judge run, but that is a DIFFERENT session, and the
# ~5% judge floor applies to cross-session deltas. Re-judging both here costs 192 rows and removes
# the exposure entirely rather than caveating it.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_basket_bomb.jsonl
for spec in \
  "w640j_A=$R/outputs/boombness/score_behavior/g3A640_20260827_105828_1094826" \
  "w640j_W=$R/outputs/boombness/score_behavior/v3_W640_20260827_221613_3095811" ; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  echo "=== judging $tag ==="
  python -u $R/src/boombness/judge_boombness.py \
    --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260827 --tag "$tag"
done
