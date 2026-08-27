#!/bin/bash
# PR-30: one-session judging of the two 640-token codeword arms.
# Same design as PR-26, which resolved the identical question for C7.
# BANK: basket_bomb (codeword 'basket'). Only --max-new differs from the PR-29 arms.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/boombness_prompt_bank_basket_bomb.jsonl
STAMP=g3j
ARMS=("A:outputs/boombness/score_behavior/g3A640_20260827_105828_1094826" "dp:outputs/boombness/score_behavior/g3dp640_20260827_105828_1094827")
for entry in "${ARMS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  n=$(wc -l < "$gens/gens.jsonl")
  if [ "$n" -ne 96 ]; then echo "WRONG ROW COUNT $tag: $n"; exit 1; fi
  if [ ! -f "$gens/DONE.json" ]; then echo "NOT DONE: $tag"; exit 1; fi
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --tag "${STAMP}_${tag}" &
done
wait
echo "=== all judging done ==="
