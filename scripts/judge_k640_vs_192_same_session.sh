#!/bin/bash
# V-109: OLD (cap 192) and NEW (cap 640) arms judged in ONE invocation.
#
# WHY. V-108 claimed the knockout effect GREW when the cap was released -- 18 -> 23 rows on main,
# 20 -> 28 on ticket_bomb. The cap-640 numbers came from one judge session (2026-08-28) and the
# cap-192 numbers from another (2026-08-24). The A-vs-C contrast WITHIN each cap is therefore clean,
# but the old-vs-new comparison crosses judge sessions -- the exact noise the batch convention in
# scripts/judge_2x2_batch.sh exists to keep out of a contrast. The "grew" claim rests on that
# crossing and nothing else does.
#
# So all eight arms are re-judged together here. The released-cap result (28/96 -> 1/96 on
# ticket_bomb, at_cap 0.0) does not depend on this; only the direction-of-change claim does.
set -euo pipefail
# THE CAP-192 DIRS ARE PINNED BY NAME, NOT PICKED. `pick p2A` returns the LATEST run whose name
# starts with p2A -- which is p2A_20260825_094249, a DIFFERENT run from the p2A_20260823_212414
# that xb_manifest10.txt and ledger entry (2) actually cite. Selecting "the latest matching run"
# would have silently compared the cap-640 arms against a run the claim was never built on.
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
D=$R/data/boombness_prompts
S=$R/outputs/boombness/score_behavior
pick () { ls -d $S/$1_* 2>/dev/null | while read d; do [ -f "$d/DONE.json" ] && echo "$d"; done | tail -1; }
for spec in \
  "ss192_p2A=$S/p2A_20260823_212414_245187=$D/boombness_prompt_bank.jsonl" \
  "ss192_p2C=$S/p2C_band_20260823_214819_248269=$D/boombness_prompt_bank.jsonl" \
  "ss192_lbA_ticket_bomb=$S/lbA_ticket_bomb_20260824_120544_2283985=$D/boombness_prompt_bank_ticket_bomb.jsonl" \
  "ss192_lbC_ticket_bomb=$S/lbC_ticket_bomb_20260824_153015_684017=$D/boombness_prompt_bank_ticket_bomb.jsonl" \
  "ss640_p2A=$(pick k640_p2A)=$D/boombness_prompt_bank.jsonl" \
  "ss640_p2C=$(pick k640_p2C_band)=$D/boombness_prompt_bank.jsonl" \
  "ss640_lbA_ticket_bomb=$(pick k640_lbA_ticket_bomb)=$D/boombness_prompt_bank_ticket_bomb.jsonl" \
  "ss640_lbC_ticket_bomb=$(pick k640_lbC_ticket_bomb)=$D/boombness_prompt_bank_ticket_bomb.jsonl" ; do
  tag="${spec%%=*}"; rest="${spec#*=}"; dir="${rest%%=*}"; bank="${rest#*=}"
  if [ -z "$dir" ]; then echo "REFUSING $tag: no run dir carrying DONE.json"; exit 1; fi
  echo "=== judging $tag  <- $(basename "$dir") ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$bank" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260828 --tag "$tag"
done
