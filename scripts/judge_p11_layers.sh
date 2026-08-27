#!/bin/bash
# PR-28: one-session judging of the four Llama layer-specificity arms.
#
# ONE WINDOW (R6-6). Refusal is measured by kw_refusal, which DR-10 showed is deterministic
# (0/160 disagreement on identical text), so the refusal read does not actually depend on the
# judge session -- but ASR does, and the window costs nothing extra.
#
# SAME BANK (C-21): all four arms are d10 pool A. Three of them already existed and are NOT
# regenerated; only p11_qpos_L10 is new.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/boombness_prompt_bank_d10.jsonl
STAMP=p11j
SB=outputs/boombness/score_behavior

ARMS=(
  "A:$SB/p4bA_20260825_104739_439513"
  "ko:$SB/p4b_demo_processing_only_20260825_104739_439514"
  "L14:$SB/p9_rescue_qpos_L14_20260826_021101_535635"
  "L10:outputs/boombness/score_behavior/p11_qpos_L10_20260827_081318_733459"
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
