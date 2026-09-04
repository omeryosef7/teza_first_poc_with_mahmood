#!/bin/bash
# PR-024 / B-009: the five 116-domain behavioural arms (cell C, query_prefill_only, band 6-14,
# n=1160 -- 116 domains x 10 rows).
#
# ALL FIVE JUDGED IN ONE INVOCATION, deliberately, and this is not a style preference. DCS-C-016a
# caught two arms judged in separate sessions drifting by 18 attacks on BYTE-IDENTICAL completions,
# and DCS-R-049 measured the same endpoint's own noise floor at 18/380 labels. PR-024a's estimand is
# KO-3 vs each control WITHIN this population, so cross-session drift would land directly on it.
#
# COST: 5 arms x 1160 rows at roughly $0.08 per 380 rows = about $1.22.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_cds116_button_bomb.jsonl
S=$R/outputs/boombness/score_behavior
pick () { ls -d $S/$1_* 2>/dev/null | while read d; do [ -f "$d/DONE.json" ] && echo "$d"; done | tail -1; }
for tag in dcsp24_base dcsp24_demo dcsp24_d1 dcsp24_d2 dcsp24_d3; do
  dir=$(pick "$tag")
  if [ -z "$dir" ]; then echo "REFUSING $tag: no run dir carrying DONE.json"; exit 1; fi
  rows=$(wc -l < "$dir/results.jsonl")
  if [ "$rows" -ne 1160 ]; then echo "REFUSING $tag: $rows rows, expected 1160"; exit 1; fi
  echo "=== judging $tag  <- $(basename "$dir")  rows=$rows ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260904 --tag "p24j_${tag}"
done
