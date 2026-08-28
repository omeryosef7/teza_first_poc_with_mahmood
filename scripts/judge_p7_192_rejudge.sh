#!/bin/bash
# PR-37: re-judge the two cap-192 C9 arms in ONE fresh invocation, on the SAME generation files
# already judged on 2026-08-25 (p7j_rescueL14 / p7j_rescueL5).
#
# Purpose is NOT a new result. It measures the stability of T2 -- the quantity C-64's "Llama leg is
# below margin" turns on -- because T2 is -6.9 against an 8.3-row margin and the gap is 1.4 rows.
# Their 797129 found the judge moves up to 3 rows in 96 on generations that did not change, with a
# SIGN FLIP, so the drift is not one-directional and cannot be corrected for.
#
# Dirs are pinned by FULL name, never `ls | tail -1`: that idiom selects the newest dir sharing a
# tag prefix, which for p2A returns a run their claim was never built on.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_d10.jsonl
for pair in "p7_rescue_L14_20260825_212626_873635:p7rj2_L14" "p7_rescue_L5_20260825_213537_875011:p7rj2_L5"; do
  gens="${pair%%:*}"; tag="${pair##*:}"
  echo "--- re-judging $gens -> $tag"
  python $R/src/boombness/judge_boombness.py \
    --gens $R/outputs/boombness/score_behavior/$gens \
    --bank $BANK --tag $tag --pin-judge-model openai/gpt-4o-mini
done
