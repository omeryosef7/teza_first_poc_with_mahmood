#!/bin/bash
# PR-36: judge BOTH 640-cap Llama C9 arms in ONE invocation window.
# R-82 measured 2-4 rows of cross-invocation judge drift on identical completions, and C9's
# surviving effect (C-64's T2) is ~7 rows -- so judging the arm and its comparator in separate
# windows would put the drift at half the signal. One job, one window, one pinned model.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_d10.jsonl
for pair in "p7r640_L14_20260828_225719_809668:p7r640j_L14" "p7r640_L5_20260828_225909_2351979:p7r640j_L5"; do
  gens="${pair%%:*}"; tag="${pair##*:}"
  echo "--- judging $gens -> $tag"
  python $R/src/boombness/judge_boombness.py \
    --gens $R/outputs/boombness/score_behavior/$gens \
    --bank $BANK --tag $tag --pin-judge-model openai/gpt-4o-mini
done
