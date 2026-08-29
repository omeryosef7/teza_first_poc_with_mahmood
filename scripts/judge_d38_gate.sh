#!/bin/bash
# V-127: the 38-domain Phase 7 gate arm. ONE invocation, one arm -- there is no second arm to keep
# in the same judge session, and the comparison that matters (seen vs unseen domains) lives INSIDE
# this single run, so it cannot straddle a judge boundary by construction.
#
# The run dir is resolved at submit time and pinned by full name below, not globbed. `ls | tail -1`
# on a prefix returns "the latest run whose name starts with X", which in V-109 would have compared
# against a different run entirely.
#
# The bank is the 608-row gate subset (boombness_prompt_bank_38dom_gatesub.jsonl), whose lines were
# verified byte-identical to the parent 38dom bank.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
DIR="$R/outputs/boombness/score_behavior/d38beh2_20260829_033157_4025666"
BANK=$R/data/boombness_prompts/boombness_prompt_bank_38dom_gatesub.jsonl
if [ ! -f "$DIR/DONE.json" ]; then echo "REFUSING: $DIR has no DONE.json"; exit 1; fi
N=$(wc -l < "$DIR/results.jsonl")
if [ "$N" -ne 608 ]; then
  echo "REFUSING: $DIR holds $N rows, not 608. V-124's lesson -- a DONE.json does not mean the rows"
  echo "are there, and a partial gate arm is worse than none because the loss is biased toward"
  echo "successes (write volume correlates with generation length)."
  exit 1
fi
echo "=== judging d38 gate arm  <- $(basename "$DIR")  ($N rows) ==="
python -u $R/src/boombness/judge_boombness.py --gens "$DIR" --bank "$BANK" \
  --pin-judge-model openai/gpt-4o-mini --seed 20260829 --tag d38gj
