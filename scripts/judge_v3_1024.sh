#!/bin/bash
# V-17: judge the cap-1024 rerun arms for ledger entry 7 (refusal channel).
# Pinned judge per the sprint's sprint-grade tier; arms judged in ONE invocation of this script so
# the V-7 cross-session judge floor is minimised rather than merely acknowledged.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
for spec in "$@"; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  echo "=== judging $tag ($dir) ==="
  python -u $R/src/boombness/judge_boombness.py \
    --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini \
    --seed 20260827 --tag "$tag"
done
