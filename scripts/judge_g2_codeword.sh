#!/bin/bash
# PR-29: one-session judging of the five lexical-generality arms (codeword = basket).
#
# ONE WINDOW (R6-6): C1 is an arm-vs-baseline refusal contrast across four scopes, so nothing
# here may be judged in a different session from what it is compared against.
#
# BANK: boombness_prompt_bank_basket_bomb.jsonl -- codeword 'basket', concept 'bomb'.
# Structurally identical to d10 (same blocks/conditions/query kinds); ONLY the codeword differs.
# Passing --bank is mandatory (R4-4).
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/boombness_prompt_bank_basket_bomb.jsonl
STAMP=g2j

ARMS=(
  "A:outputs/boombness/score_behavior/g2A_20260827_091838_739916"
  "legacy:outputs/boombness/score_behavior/g2_legacy_all_query_20260827_093840_742076"
  "qpre:outputs/boombness/score_behavior/g2_query_prefill_only_20260827_093840_742077"
  "demoproc:outputs/boombness/score_behavior/g2_demo_processing_only_20260827_091838_739915"
  "respq:outputs/boombness/score_behavior/g2_response_query_only_20260827_094825_743996"
)
for entry in "${ARMS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  if [ ! -f "$gens/gens.jsonl" ]; then echo "MISSING gens: $tag -> $gens"; exit 1; fi
  n=$(wc -l < "$gens/gens.jsonl")
  if [ "$n" -ne 96 ]; then echo "WRONG ROW COUNT $tag: $n != 96"; exit 1; fi
  if [ ! -f "$gens/DONE.json" ]; then echo "NOT DONE: $tag"; exit 1; fi
  python -u src/boombness/judge_boombness.py \
    --gens "$gens" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini \
    --tag "${STAMP}_${tag}" &
done
wait
echo "=== all judging done ==="
