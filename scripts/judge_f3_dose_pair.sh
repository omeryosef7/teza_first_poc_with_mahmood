#!/bin/bash
# F-3's specificity test at the one dose that is gate-clean.
#
# THE QUESTION (RETRACTION F-3): does adding REFUSALNESS suppress ASR where a magnitude-matched
# RANDOM direction does not? The alpha=1.0 version was retracted for a 14.8x dose mismatch, and
# alpha=14.65 destroys generation. alpha=7.33 (half of one diff-of-means) is gate-clean:
# scorable 0.865, uniq 0.940, trigram 0.004 -- the healthiest run in the dose table.
#
# GATE FIRST, as pre-registered: the random control is 7x the magnitude of the alpha=1.0 random add
# that was previously gate-clean, so it may itself degenerate. If it does, the comparison is blocked
# and that is a statement about ANY add-intervention at this dose, not about refusalness.
#
# ONE JUDGING SESSION for all three arms (R6-6). The arm-minus-control contrast is immune to
# baseline judge noise, but the per-arm deltas vs baseline are not.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
SB=outputs/boombness/score_behavior

ARM=$(ls -d $SB/fuF_addR_g02_* 2>/dev/null | tail -1)
CTL=$(ls -d $SB/fuF_addRand_g02_* 2>/dev/null | tail -1)
BASE=$SB/ab_base_20260818_185458_3888976
for d in "$ARM" "$CTL" "$BASE"; do
  if [ -z "$d" ] || [ ! -f "$d/gens.jsonl" ]; then echo "MISSING gens: $d"; exit 1; fi
  n=$(wc -l < "$d/gens.jsonl"); if [ "$n" -ne 495 ]; then echo "WRONG ROWS $d: $n"; exit 1; fi
done

echo "=== coherence gate (control must pass before any judging) ==="
python -u src/boombness/coherence_gate.py "$CTL" --out /tmp/f3_ctl_gate.json | tail -3
if ! python - <<'PY'
import json,sys
g=json.load(open('/tmp/f3_ctl_gate.json'))
ok=all(r.get('coherent') for r in g)
print(f"[f3] control coherent={ok}")
sys.exit(0 if ok else 1)
PY
then
  echo "[f3] BLOCKED: the dose-matched random control is itself degenerate at alpha=7.33."
  echo "[f3] No judging performed. This blocks the comparison for ANY add-intervention at this"
  echo "[f3] dose and is NOT evidence about refusalness."
  exit 2
fi

echo "=== judging all three arms in one session ==="
for entry in "arm:$ARM" "ctl:$CTL" "base:$BASE"; do
  tag="${entry%%:*}"; gens="${entry#*:}"
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" --tag "f3d_${tag}" &
done
wait
echo "=== f3 judging done ==="
