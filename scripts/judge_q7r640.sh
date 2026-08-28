#!/bin/bash
# PR-38: both cap-640 q7 arms in ONE invocation, dirs pinned by full name, bank read from
# each arm's own RUNMETA.argv (d10) rather than inherited from the q6b half.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_d10.jsonl
for pair in "q7r640_L17_20260829_013823_2385945:q7r640j_L17" "q7r640_L5_20260829_013823_2385944:q7r640j_L5"; do
  gens="${pair%%:*}"; tag="${pair##*:}"
  echo "--- judging $gens -> $tag"
  python $R/src/boombness/judge_boombness.py \
    --gens $R/outputs/boombness/score_behavior/$gens \
    --bank $BANK --tag $tag --pin-judge-model openai/gpt-4o-mini
done
