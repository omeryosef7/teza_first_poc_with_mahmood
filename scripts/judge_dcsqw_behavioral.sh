#!/bin/bash
# PR-014: the eight Qwen3-14B behavioural arms (cell C, query_prefill_only, band 7-17, n=380).
#
# ALL EIGHT JUDGED IN ONE INVOCATION, deliberately. DCS-C-016a caught the opposite: two arms
# judged in separate sessions drifted by 18 attacks on BYTE-IDENTICAL completions. The estimand
# here is KO-3 vs each control WITHIN this population, so cross-session judge noise would land
# directly on it.
#
# Judged AFTER PR-014 was committed. `refused` is judge-free (kw_refusal), so the whole design --
# including C-023's finding that no Qwen control is refusal-neutral -- was fixed before any
# attack number existed.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_cds38_button_bomb.jsonl
S=$R/outputs/boombness/score_behavior
pick () { ls -d $S/$1_* 2>/dev/null | while read d; do [ -f "$d/DONE.json" ] && echo "$d"; done | tail -1; }
for tag in dcsqwb_C_baseline dcsqwb_C_qpo_demo dcsqwb_C_ctrl_d1 dcsqwb_C_ctrl_d2 \
           dcsqwb_C_s20260901_d3 dcsqwb_C_s20260904_d1 dcsqwb_C_s20260904_d2 dcsqwb_C_s20260904_d3; do
  dir=$(pick "$tag")
  if [ -z "$dir" ]; then echo "REFUSING $tag: no run dir carrying DONE.json"; exit 1; fi
  rows=$(wc -l < "$dir/results.jsonl")
  if [ "$rows" -ne 380 ]; then echo "REFUSING $tag: $rows rows, expected 380"; exit 1; fi
  echo "=== judging $tag  <- $(basename "$dir")  rows=$rows ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260904 --tag "qwj_${tag}"
done
