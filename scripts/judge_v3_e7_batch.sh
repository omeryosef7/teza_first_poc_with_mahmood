#!/bin/bash
# V-21: ledger entry 7 (refusal channel) at cap 1024 -- baseline, C (refusal project-out) and
# D (joint d_surface + refusal project-out), ALL THREE judged in ONE invocation so the ~5% judge
# floor does not enter the arm-vs-baseline deltas as cross-session noise.
# C1024 is deliberately re-judged here even though 787254 already judged it: that gives a second
# independent draw on identical generations at cap 1024, i.e. a floor measurement at THIS cap.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
for spec in \
  "e7j_base=$R/outputs/boombness/score_behavior/v3_base1024_20260827_221710_2090783" \
  "e7j_C=$R/outputs/boombness/score_behavior/v3_C1024_20260827_213652_709693" \
  "e7j_D=$R/outputs/boombness/score_behavior/v3_D1024_20260827_221613_3095812" ; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  echo "=== judging $tag ==="
  python -u $R/src/boombness/judge_boombness.py \
    --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260827 --tag "$tag"
done
