#!/bin/bash
# Judge the control-band draw that was excluded for the WRONG reason.
#
# `ab_Bband_20260903` (random:project_out:8-8:1.0, seed 20260903) was dropped from the arm-B control
# band on `scorable_frac 0.446 < 0.5`, with its own report note conceding the degeneracy statistics
# were healthy (uniq 0.833, trigram 0.014). A repo-wide sweep of all 26 gate verdicts has since shown
# scorable_frac is a LENGTH proxy wearing a coherence label: it flags short REFUSALS, not broken text,
# and six runs it excluded are lexically healthier than the untreated model.
#
# Excluding a draw shrinks the band, which flatters the arm. The generations were complete (495 rows,
# DONE) and simply never judged. This judges them, plus a baseline IN THE SAME SESSION so the delta is
# session-matched rather than differenced across sessions like the other draws.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
SB=$R/outputs/boombness/score_behavior

declare -a PAIRS=(
  "base:$SB/ab_base_20260818_185458_3888976"
  "s903:$SB/ab_Bband_20260903_20260819_040029_1413029"
)
for e in "${PAIRS[@]}"; do
  tag="${e%%:*}"; gens="${e#*:}"
  [ -f "$gens/gens.jsonl" ] || { echo "MISSING $tag"; exit 1; }
  [ -f "$gens/DONE.json" ] || { echo "NOT DONE $tag"; exit 1; }
  n=$(wc -l < "$gens/gens.jsonl"); [ "$n" -eq 495 ] || { echo "WRONG ROWS $tag: $n"; exit 1; }
  echo "[band903] $tag <- $(basename $gens) ($n rows)"
done
for e in "${PAIRS[@]}"; do
  tag="${e%%:*}"; gens="${e#*:}"
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" --tag "b903_${tag}" &
done
wait
echo "=== band903 judging done ==="
