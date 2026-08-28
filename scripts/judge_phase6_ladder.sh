#!/bin/bash
# V-113: PHASE 6 dose ladder. ALL SEVEN RUNS IN ONE INVOCATION.
#
# WHY ONE INVOCATION. The estimand is a dose-response curve WITHIN a bank, so the low doses and the
# high doses are the two ends of the contrast. The judge's gross per-row flip rate on byte-identical
# text is 6.5-7.0% (measured three times, 507 rows, V-111/V-112). Judging {0,12,16} in a different
# session from {1,2,4,8} would put a 7% instrument boundary in the middle of the curve and it would
# read as dose-response.
#
# THE LADDER IS DOSE-IMBALANCED BY CONSTRUCTION and the analysis must handle it: doses 1/2/4/8 carry
# core2x2 AND core2x2_slot3 (24 rows each), while 0/12/16 exist only in core2x2 (12 rows). The
# balanced comparison is core2x2-only at 12 rows for every dose; the unbalanced one is reported
# beside it, never instead of it.
#
# n=12 lives in its own bank (boombness_prompt_bank_ne12.jsonl, preset main_ne12) and exists for
#  only -- so the 12 cell appears on one bank and cannot be compared across banks.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
BK=$R/data/boombness_prompts
S=$R/outputs/boombness/score_behavior
for spec in \
  "p6j_main_d016=$S/ph6_main_d016_20260829_010153_1966577=$BK/boombness_prompt_bank.jsonl" \
  "p6j_ticket_d016=$S/ph6_ticket_d016_20260829_010901_2419603=$BK/boombness_prompt_bank_ticket_bomb.jsonl" \
  "p6j_basket_d016=$S/ph6_basket_d016_20260829_010901_2419602=$BK/boombness_prompt_bank_basket_gun.jsonl" \
  "p6j_main_d12=$S/ph6_main_d12_20260829_011124_2625511=$BK/boombness_prompt_bank_ne12.jsonl" \
  "p6j_main_d1248=$S/e6A_main_20260827_232241_875172=$BK/boombness_prompt_bank.jsonl" \
  "p6j_ticket_d1248=$S/e6A_ticket_bomb_20260828_002321_882523=$BK/boombness_prompt_bank_ticket_bomb.jsonl" \
  "p6j_basket_d1248=$S/e6A_basket_gun_20260828_003641_719673=$BK/boombness_prompt_bank_basket_gun.jsonl" ; do
  tag="${spec%%=*}"; rest="${spec#*=}"; dir="${rest%%=*}"; bank="${rest#*=}"
  if [ ! -f "$dir/DONE.json" ]; then echo "REFUSING $tag: $dir has no DONE.json"; exit 1; fi
  echo "=== judging $tag  <- $(basename "$dir") ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$bank" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260829 --tag "$tag"
done
