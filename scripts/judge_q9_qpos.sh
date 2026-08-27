#!/bin/bash
# PR-27: one-session judging of the five Q7 (C11-on-Qwen3) arms.
#
# ONE WINDOW (R6-6): the read is arm-vs-baseline and arm-vs-arm, so nothing here may be judged
# in a different session from what it is compared against.
#
# SAME BANK, SAME GENERATION SESSION (C-21): every arm below is pool A (d10) and every one was
# generated today. C-21 was caused by comparing a pool-A arm against a pool-B arm and reading the
# difference as a session effect, so the whole Q7 read is deliberately homogeneous on both axes.
#
# q9_qpos_L5 is NOT a control (C-20): it is byte-identical to q9_ko on 160/160 rows. It is judged
# here only to measure JUDGE non-reproducibility on identical text -- any nonzero difference
# between q9j_L5 and q9j_ko is judge noise, since the completions are the same bytes.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/boombness_prompt_bank_d10.jsonl
STAMP=q9j

ARMS=(
  "A:outputs/boombness/score_behavior/q9A_20260827_070931_1079437"
  "ko:outputs/boombness/score_behavior/q9_ko_20260827_061835_724429"
  "L17:outputs/boombness/score_behavior/q9_qpos_L17_20260827_054256_719520"
  "L12:outputs/boombness/score_behavior/q9_qpos_L12_20260827_063936_725789"
  "L5:outputs/boombness/score_behavior/q9_qpos_L5_20260827_054320_1072840"
)
for entry in "${ARMS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  if [ ! -f "$gens/gens.jsonl" ]; then echo "MISSING gens: $tag -> $gens"; exit 1; fi
  n=$(wc -l < "$gens/gens.jsonl")
  if [ "$n" -ne 160 ]; then echo "WRONG ROW COUNT $tag: $n != 160"; exit 1; fi
  if [ ! -f "$gens/DONE.json" ]; then echo "NOT DONE: $tag"; exit 1; fi
  python -u src/boombness/judge_boombness.py \
    --gens "$gens" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini \
    --tag "${STAMP}_${tag}" &
done
wait
echo "=== all judging done ==="
