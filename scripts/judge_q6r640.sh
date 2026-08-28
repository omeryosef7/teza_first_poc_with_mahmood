#!/bin/bash
# PR-36, Qwen3 half: both cap-640 arms in ONE invocation, dirs pinned by full name.
# Bank is d10_poolB, matching the arms' own RUNMETA.argv -- not assumed from the Llama half.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_d10_poolB.jsonl
for pair in "q6r640_L17_20260828_225928_810651:q6r640j_L17" "q6r640_L5_20260828_234159_3039651:q6r640j_L5"; do
  gens="${pair%%:*}"; tag="${pair##*:}"
  echo "--- judging $gens -> $tag"
  python $R/src/boombness/judge_boombness.py \
    --gens $R/outputs/boombness/score_behavior/$gens \
    --bank $BANK --tag $tag --pin-judge-model openai/gpt-4o-mini
done
