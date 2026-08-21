#!/bin/bash
# One-session judging of the full Qwen3 internal-bank decomposition.
#
# WHY ALL SIX IN ONE BATCH. R6-6 established that comparing arms judged in
# different sessions produced a real artifact (the L12 "near-miss"). The four
# existing arms were re-judged together on 08-20; the two new ones generate today.
# Judging only the new pair would put arm B and its baseline in different sessions
# on the contrast that carries the whole decomposition. So all six are re-judged
# together, which also re-derives the committed +0.3476 as a replication check.
#
# BANK: the pinned 2352-row bank, verified content-identical to the one the 08-18
# arms ran against (0 missing ids, 0 content diffs vs the current 2736-row file).
# Passing --bank is mandatory here: R4-4 found these arms were originally judged
# with bank=None, scoring every row against the EMPTY STRING.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
BANK=$R/data/boombness_prompts/boombness_prompt_bank_pinned_82bc1a3c_2352.jsonl
SB=outputs/boombness/score_behavior
STAMP=q3dec

# tag:gens_dir
ARMS=(
  "base:$SB/qwen3nt_base_20260817_163110_3560487"
  "C20:$SB/q3_C20_20260818_154112_366026"
  "D20:$SB/q3_D20_20260818_154112_366027"
  "D20ctrl:$SB/q3_D20ctrl_20260818_154112_366028"
  "B11:__B11__"
  "B11ctrl:__B11CTRL__"
)
for entry in "${ARMS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  if [ ! -f "$gens/gens.jsonl" ]; then echo "MISSING gens: $tag -> $gens"; exit 1; fi
  n=$(wc -l < "$gens/gens.jsonl")
  if [ "$n" -ne 960 ]; then echo "WRONG ROW COUNT $tag: $n != 960"; exit 1; fi
  for off in 0 480; do
    python -u src/boombness/judge_boombness.py \
      --gens "$gens" --bank "$BANK" --offset "$off" --limit 480 \
      --tag "${STAMP}_${tag}" &
  done
done
wait
echo "=== all judging done ==="
