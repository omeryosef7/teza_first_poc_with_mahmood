#!/bin/bash
# V-108: the retrieval-knockout reruns at cap 640 (ledger entry 6, plan §12.14/§12.16).
#
# ALL SIX JUDGED IN ONE INVOCATION, deliberately. The comparison this batch exists to serve is
# A-vs-C WITHIN each population, so cross-session judge noise between the two arms would land
# directly on the estimand. Same convention as scripts/judge_2x2_batch.sh.
#
# These replace runs whose Llama C arms were 92-100% truncated at max_new=192 (lbC_window_knife
# 96/96, gnLC 96/96). Truncation at 640 is 0/96 on every arm here, longest 596 of 640.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
D=$R/data/boombness_prompts
S=$R/outputs/boombness/score_behavior
pick () { ls -d $S/$1_* | while read d; do [ -f "$d/DONE.json" ] && echo "$d"; done | tail -1; }
for spec in \
  "k640j_p2A=$(pick k640_p2A)=$D/boombness_prompt_bank.jsonl" \
  "k640j_p2C=$(pick k640_p2C_band)=$D/boombness_prompt_bank.jsonl" \
  "k640j_lbA_ticket_bomb=$(pick k640_lbA_ticket_bomb)=$D/boombness_prompt_bank_ticket_bomb.jsonl" \
  "k640j_lbC_ticket_bomb=$(pick k640_lbC_ticket_bomb)=$D/boombness_prompt_bank_ticket_bomb.jsonl" \
  "k640j_lbA_window_knife=$(pick k640_lbA_window_knife)=$D/boombness_prompt_bank_window_knife.jsonl" \
  "k640j_lbC_window_knife=$(pick k640_lbC_window_knife)=$D/boombness_prompt_bank_window_knife.jsonl" ; do
  tag="${spec%%=*}"; rest="${spec#*=}"; dir="${rest%%=*}"; bank="${rest#*=}"
  if [ -z "$dir" ]; then echo "REFUSING $tag: no run dir carrying DONE.json"; exit 1; fi
  echo "=== judging $tag  <- $(basename "$dir") ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$bank" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260828 --tag "$tag"
done
