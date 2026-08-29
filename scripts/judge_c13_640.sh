#!/bin/bash
# PR-39: one-session judging of C13's three 640-cap arms.
# R-82: both/all arms in ONE invocation -- a separate judge session drifts 2-4 rows, which is
# the size of the effect being tested. Each arm carries its OWN bank: the arms differ by bank
# (d10 / longpre / longpre10), not by intervention, so a single --bank would be wrong.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
STAMP=c13j640
ARMS=(
  "b:boombness_prompt_bank_d10.jsonl:outputs/boombness/score_behavior/c13b640_20260829_082520_2256116"
  "p12:boombness_prompt_bank_longpre.jsonl:outputs/boombness/score_behavior/c13p12640_20260829_082521_3664218"
  "p10:boombness_prompt_bank_longpre10.jsonl:outputs/boombness/score_behavior/c13p10640_20260829_082522_3664219"
)
for entry in "${ARMS[@]}"; do
  tag="${entry%%:*}"; rest="${entry#*:}"; bank="${rest%%:*}"; gens="${rest#*:}"
  n=$(wc -l < "$gens/gens.jsonl")
  if [ "$n" -ne 160 ]; then echo "WRONG ROW COUNT $tag: $n"; exit 1; fi
  if [ ! -f "$gens/DONE.json" ]; then echo "NOT DONE: $tag"; exit 1; fi
  if [ ! -f "$R/data/boombness_prompts/$bank" ]; then echo "NO BANK $tag: $bank"; exit 1; fi
  python -u src/boombness/judge_boombness.py --gens "$gens" \
    --bank "$R/data/boombness_prompts/$bank" \
    --pin-judge-model openai/gpt-4o-mini --tag "${STAMP}_${tag}" &
done
wait
echo "=== all judging done ==="
