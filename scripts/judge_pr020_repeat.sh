#!/bin/bash
# PR-020 / B-014: re-judge ONE arm at byte-identical settings, in a fresh invocation.
#
# The arm is dcsqwb_C_baseline and it was named in PR-020 BEFORE 849653 finished, so it cannot have
# been chosen for its answer. One arm, one extra pass, one look -- PR-020 forbids re-judging any
# other arm and forbids a second attempt if the first is inconvenient.
#
# Settings are copied from judge_dcsqw_behavioral.sh verbatim: same pin, same seed, same bank.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BANK=$R/data/boombness_prompts/boombness_prompt_bank_cds38_button_bomb.jsonl
S=$R/outputs/boombness/score_behavior
tag=dcsqwb_C_baseline
dir=$(ls -d $S/${tag}_* 2>/dev/null | while read d; do [ -f "$d/DONE.json" ] && echo "$d"; done | tail -1)
[ -n "$dir" ] || { echo "REFUSING: no run dir for $tag carrying DONE.json"; exit 1; }
rows=$(wc -l < "$dir/results.jsonl")
[ "$rows" -eq 380 ] || { echo "REFUSING $tag: $rows rows, expected 380"; exit 1; }
echo "=== PR-020 repeat judging of $tag  <- $(basename "$dir")  rows=$rows ==="
python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$BANK" \
  --pin-judge-model openai/gpt-4o-mini --seed 20260904 --tag "qwj2_${tag}"
