#!/bin/bash
# F-3's specificity test, at the two doses where BOTH arm and magnitude-matched control are
# gate-clean. This is the comparison RETRACTION F-3 asked for and has never had.
#
# WHY THESE ARMS. The add-refusalness intervention is gate-clean only in a window at 0.50-0.75 of
# one diff-of-means; below it the model gives terse refusals (scorable < 0.5), above it generation
# collapses. The matched random control is dosed in D_SURFACE GAP units, not in refusal-norm units,
# so its alpha is the gap FRACTION -- 0.5 and 0.75. Getting that wrong overdosed the first control
# 14.65x and produced a spectacular, meaningless degeneracy (uniq 0.066, 100% truncated).
#
# MAGNITUDES (from the run-time ADD DOSE diagnostic, not from arithmetic on the flag):
#   arm  alpha 7.326731 x 1.0        -> 7.326731     control alpha 0.5  x 14.792503 -> 7.396252
#   arm  alpha 10.990097 x 1.0       -> 10.990097    control alpha 0.75 x 14.792503 -> 11.094378
# Matched to 0.95%, not exactly; report magnitudes, never alphas.
#
# GATE STATUS, all verified OK before this script runs:
#   arm 7.33  uniq 0.940 scor 0.865 | ctl 7.40  uniq 0.909 scor 0.925
#   arm 10.99 uniq 0.750 scor 0.863 | ctl 11.09 uniq 0.731 scor 0.974
#
# ONE JUDGING SESSION for all five arms (R6-6).
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
SB=outputs/boombness/score_behavior

declare -a PAIRS=(
  "base:$SB/ab_base_20260818_185458_3888976"
  "armA:$(ls -d $SB/fuF_addR_g02_* | tail -1)"
  "ctlA:$(ls -d $SB/fuF_addRandM_g02_* | tail -1)"
  "armB:$(ls -d $SB/fuF_addR_g075_* | tail -1)"
  "ctlB:$(ls -d $SB/fuF_addRandM_g075_* | tail -1)"
)
for entry in "${PAIRS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  if [ -z "$gens" ] || [ ! -f "$gens/gens.jsonl" ]; then echo "MISSING gens for $tag: $gens"; exit 1; fi
  n=$(wc -l < "$gens/gens.jsonl"); if [ "$n" -ne 495 ]; then echo "WRONG ROWS $tag: $n"; exit 1; fi
  echo "[f3] $tag <- $gens ($n rows)"
done

for entry in "${PAIRS[@]}"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" --tag "f3d_${tag}" &
done
wait
echo "=== f3 judging done ==="
