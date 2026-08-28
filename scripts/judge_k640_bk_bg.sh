#!/bin/bash
# V-111: button_knife and basket_gun -- the last two of the five Llama knockout populations.
#
# EVERY RUN DIR IS PINNED BY FULL NAME, never selected by pattern. `ls | tail -1` on a prefix
# returns "the latest run whose name starts with X", which in V-109 would have silently compared
# against p2A_20260825_094249 instead of the p2A_20260823_212414 that entry (2) actually cites.
# Four variants of that bug turned up across both sessions in one night (a glob that could not match
# g3A640, a regex matching only bolded ids, ls|tail -1, and a population-name substring that pulled
# QWEN rows into a Llama table). Flat rule now: pin by name.
#
# 192 AND 640 IN THE SAME INVOCATION, built that way from the start. V-108 judged the A-vs-C axis
# together and the 192-vs-640 axis across sessions, and the judge moves up to 3 rows in 96 on
# unchanged generations (V-109), which is the size of the effect that comparison was reporting.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
D=$R/data/boombness_prompts
S=$R/outputs/boombness/score_behavior
for spec in \
  "bb192_lbA_button_knife=$S/lbA_button_knife_20260824_114612_2280721=$D/boombness_prompt_bank_button_knife.jsonl" \
  "bb192_lbC_button_knife=$S/lbC_button_knife_20260824_115545_2282473=$D/boombness_prompt_bank_button_knife.jsonl" \
  "bb640_lbA_button_knife=$S/k640_lbA_button_knife_20260828_224956_1948054=$D/boombness_prompt_bank_button_knife.jsonl" \
  "bb640_lbC_button_knife=$S/k640_lbC_button_knife_20260828_225719_809667=$D/boombness_prompt_bank_button_knife.jsonl" \
  "bb192_gnLA=$S/gnLA_20260824_221640_2352538=$D/boombness_prompt_bank_basket_gun.jsonl" \
  "bb192_gnLC=$S/gnLC_20260824_222648_376555=$D/boombness_prompt_bank_basket_gun.jsonl" \
  "bb640_gnLA=$S/k640_gnLA_20260828_235658_3134414=$D/boombness_prompt_bank_basket_gun.jsonl" \
  "bb640_gnLC=$S/k640_gnLC_20260829_000053_3135409=$D/boombness_prompt_bank_basket_gun.jsonl" ; do
  tag="${spec%%=*}"; rest="${spec#*=}"; dir="${rest%%=*}"; bank="${rest#*=}"
  if [ ! -f "$dir/DONE.json" ]; then echo "REFUSING $tag: $dir has no DONE.json"; exit 1; fi
  echo "=== judging $tag  <- $(basename "$dir") ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$bank" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260828 --tag "$tag"
done
