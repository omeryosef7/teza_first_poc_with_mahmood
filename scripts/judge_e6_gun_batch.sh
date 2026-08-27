#!/bin/bash
# V-33: entry 6, population basket_gun, cap 640. Both arms in ONE invocation.
# This is the INFORMATIVE test (V-13): a population WITH headroom (baseline 10/96) that showed
# nothing at cap 192 (net -1). If it stays null the dissociation holds at a usable cap; if it moves,
# V-13's decomposition needs revisiting. Chosen so the rerun can demonstrate detecting ABSENCE,
# not only presence.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_basket_gun.jsonl
for spec in \
  "e6j_A_gun=$R/outputs/boombness/score_behavior/e6A_basket_gun_20260828_003641_719673" \
  "e6j_C_gun=$R/outputs/boombness/score_behavior/e6C_basket_gun_20260828_012256_2233773" ; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  echo "=== judging $tag ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260828 --tag "$tag"
done
