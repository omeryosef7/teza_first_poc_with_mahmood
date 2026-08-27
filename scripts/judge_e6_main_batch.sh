#!/bin/bash
# V-25: ledger entry 6 (retrieval knockout), population `main`, at cap 640.
# Both arms in ONE invocation so the ~5% judge floor stays out of the arm-vs-baseline delta --
# the exposure a peer session's invocation audit identified in the original cap-192 runs.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank.jsonl
for spec in \
  "e6j_A_main=$R/outputs/boombness/score_behavior/e6A_main_20260827_232241_875172" \
  "e6j_C_main=$R/outputs/boombness/score_behavior/e6C_main_20260827_234650_2226286" ; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  echo "=== judging $tag ==="
  python -u $R/src/boombness/judge_boombness.py \
    --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260828 --tag "$tag"
done
