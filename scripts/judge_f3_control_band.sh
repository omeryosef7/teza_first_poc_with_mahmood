#!/bin/bash
# F-3 with a CONTROL BAND instead of a single random vector.
#
# WHY. Review #11 found that the two "independent" controls in the first F-3 run were the SAME
# random vector (seed 20260816 at L18, two alphas). A specificity claim certified against one draw
# is what R5-7 warns about. Three further draws (seeds 20260901/2/3) at the identical magnitude
# 7.396252 all pass the coherence gate (scorable 0.974/0.804/0.848), so the control is now n=4.
#
# ONE SESSION for all six arms (R6-6): judging the new controls separately would put arm and
# control in different sessions on the very contrast that carries the claim.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
SB=outputs/boombness/score_behavior

declare -a ARMS=(
  "base:$SB/ab_base_20260818_185458_3888976"
  "arm:$(ls -d $SB/fuF_addR_g02_* | tail -1)"
  "c16:$(ls -d $SB/fuF_addRandM_g02_* | tail -1)"
  "c01:$(ls -d $SB/fuF_addRandS01_* | tail -1)"
  "c02:$(ls -d $SB/fuF_addRandS02_* | tail -1)"
  "c03:$(ls -d $SB/fuF_addRandS03_* | tail -1)"
)
for e in "${ARMS[@]}"; do
  t="${e%%:*}"; g="${e#*:}"
  [ -f "$g/gens.jsonl" ] || { echo "MISSING $t: $g"; exit 1; }
  n=$(wc -l < "$g/gens.jsonl"); [ "$n" -eq 495 ] || { echo "WRONG ROWS $t: $n"; exit 1; }
  echo "[band] $t <- $g ($n)"
done
for e in "${ARMS[@]}"; do
  t="${e%%:*}"; g="${e#*:}"
  python -u src/boombness/judge_boombness.py --gens "$g" --bank "$BANK" --tag "f3b_${t}" &
done
wait
echo "=== band judging done ==="
