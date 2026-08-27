#!/bin/bash
# PR-26: one-session judging of the three 640-token arms.
#
# Same one-window discipline as scripts/judge_q16_poolB.sh (R6-6): the whole point of PR-26
# is an arm-vs-baseline contrast, so baseline and arms must not be judged in different
# sessions. Three arms only -- matched_d2/d3 were deliberately omitted at pre-registration
# because PR-26 tests a CONFOUND, not the independence of the draws, which R-62 settled.
#
# BANK: boombness_prompt_bank_longpreQ14B.jsonl (sha b2903479258a0f68) -- the same pool B
# the R-62 arms ran against. The ONLY difference from R-62 is --max-new 192 -> 640 and the
# restriction to the two decisive doses, so 80 rows per arm rather than 160.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/boombness_prompt_bank_longpreQ14B.jsonl
STAMP=p26j

ARMS=(
  "A:outputs/boombness/score_behavior/A640_20260827_040740_708673"
  "dp:outputs/boombness/score_behavior/dp640_20260827_040740_708761"
  "c1:outputs/boombness/score_behavior/c1_640_20260827_043749_711377"
)
for entry in "${ARMS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  if [ ! -f "$gens/gens.jsonl" ]; then echo "MISSING gens: $tag -> $gens"; exit 1; fi
  n=$(wc -l < "$gens/gens.jsonl")
  if [ "$n" -ne 80 ]; then echo "WRONG ROW COUNT $tag: $n != 80"; exit 1; fi
  if [ ! -f "$gens/DONE.json" ]; then echo "NOT DONE: $tag"; exit 1; fi
  python -u src/boombness/judge_boombness.py \
    --gens "$gens" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini \
    --tag "${STAMP}_${tag}" &
done
wait
echo "=== all judging done ==="
