#!/bin/bash
# GATE DOSE -- read the L12 dose ladder as a CURVE, from ONE judging session (776797).
#
# NO NEW ANALYSIS CODE. analyze_external_arms.py already computes paired arm-vs-baseline deltas with
# domain-clustered CIs and p_cl, which is exactly what each rung needs. The ladder is 12 arms plus
# two controls read against one baseline; the curve is the result, so every rung must come from the
# same session (a rung judged elsewhere carries a drift that does not cancel rung-to-rung).
#
# The two dose metrics (C-2) are NOT recomputed here: they are properties of the DIRECTION and alpha,
# already recorded per run by realized_dose_record. This script supplies the ASR side of the curve.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
J=$R/outputs/boombness/judge
d(){ ls -d $J/p1b_$1_* 2>/dev/null | tail -1; }

EXPECTED="base a100 a038 a030 a020 a015 a010 a008 a006 a056 a045 a003 ctrlrnd ctrlort"
for t in $EXPECTED; do
  p=$(d $t)
  [ -n "$p" ] || { echo "MISSING judge dir for $t" >&2; exit 3; }
  [ -f "$p/DONE.json" ] || { echo "NOT DONE: $t" >&2; exit 3; }
  n=$(wc -l < "$p/results.jsonl")
  [ "$n" -eq 495 ] || { echo "SHORT: $t has $n rows, expected 495" >&2; exit 3; }
  echo "  ok $t ($n rows)"
done

ARGS=()
for t in a100 a038 a030 a020 a015 a010 a008 a006 a056 a045 a003 ctrlrnd ctrlort; do
  ARGS+=(--arm "$t=$(d $t)")
done
python -u src/boombness/analyze_external_arms.py \
  --baseline "$(d base)" "${ARGS[@]}" \
  --label "Gate DOSE (one session, job 776797): the L12 d_surface dose ladder, alpha 0.03 -> 1.0, on AdvBench-495, with a random and an in-subspace-orthogonal control at full dose" \
  --out "$R/outputs/boombness_followup/gate_dose_ladder.json"
echo "=== GATE DOSE ARTIFACT WRITTEN ==="
