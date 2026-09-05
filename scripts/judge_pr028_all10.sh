#!/bin/bash
# PR-028b: ALL TEN arms of the K=8 primary, judged in ONE invocation.
#
# WHY RE-JUDGE THE FIVE PR-024 ARMS THAT ALREADY HAVE LABELS. The K=8 primary compares KO-3 against
# the control DISTRIBUTION. KO-3 and 3 controls were judged in session `p24j`; the 5 new controls
# would otherwise be judged now. A session offset would therefore land on 5 of 8 controls but NOT
# on KO-3, biasing the primary by (5/8)*offset. The two existing drift estimates disagree by 8x --
# judge_session_drift.json measures 0.0020 (13 sessions, AdvBench, ASR 0.065) and DCS-R-049 measures
# net +6/380 = 0.0158 on this bank -- i.e. between 3% and 25% of the -0.0391 effect. R-049's net is
# only 1.41 sd from zero under symmetric flipping, so it is not even established as an offset. We
# cannot tell which is right, so we remove the term instead of assuming it away.
#
# BONUS, AND IT IS NOT SMALL: re-judging the 5 old arms yields a DIRECT in-population drift estimate
# on 5 x 1160 byte-identical completions -- far more data than either existing number, and it
# settles that disagreement rather than inheriting it.
#
# COST: 10 arms x 1160 rows, roughly $2.50.
# ⛔ RUN ON cpu-killable, NEVER THE LOGIN NODE (`import openai` hangs >90s under NFS contention).
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
# CONDA + .env, matching scripts/judge_angle24.sh. Without these the run dies under sbatch with
# "OPENAI_API_KEY is not set" -- the key lives in .env and is NOT in the batch environment.
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
# B-016: the artifacts record only the judge ALIAS, so bound the served SNAPSHOT around the run.
snap () { curl -s --max-time 20 -H "Authorization: Bearer ${OPENAI_API_KEY:-}" \
    -H "Content-Type: application/json" \
    -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"ok"}],"max_tokens":1}' \
    https://api.openai.com/v1/chat/completions | python -c \
    'import json,sys; print(json.load(sys.stdin).get("model","UNKNOWN"))' 2>/dev/null || echo UNKNOWN; }
BANK=$R/data/boombness_prompts/boombness_prompt_bank_cds116_button_bomb.jsonl
S=$R/outputs/boombness/score_behavior
# `|| true` IS LOAD-BEARING. Without it `ls -d` on a not-yet-created arm returns non-zero, and
# under `set -e -o pipefail` the enclosing `dir=$(pick ...)` assignment kills the script BEFORE the
# REFUSING message prints -- an exit 1 with no reason, which is the worst possible failure mode for
# a pre-flight whose whole job is to say WHICH arm is not ready.
# THE TRAILING `|| true` IS LOAD-BEARING, and it took two tries to get right. Under `set -e -o
# pipefail` this pipeline returns non-zero in TWO ways: `ls -d` fails when the arm dir does not
# exist yet, AND the `while` loop exits non-zero whenever its last `[ -f ... ] && echo` is false
# (i.e. whenever the newest arm has no DONE.json -- exactly the case a pre-flight exists to catch).
# Either one kills `dir=$(pick ...)` BEFORE the REFUSING message prints, giving an exit 1 with no
# reason: the worst failure mode for a check whose only job is to name the arm that is not ready.
pick () { { ls -d $S/$1_* 2>/dev/null | while read d; do [ -f "$d/DONE.json" ] && echo "$d"; done | tail -1; } || true; }

TAGS="dcsp24_base dcsp24_demo dcsp24_d1 dcsp24_d2 dcsp24_d3 \
dcsp28_s20260905_d1 dcsp28_s20260905_d2 dcsp28_s20260905_d3 \
dcsp28_s20260906_d1 dcsp28_s20260906_d2"

# PRE-FLIGHT EVERY ARM BEFORE JUDGING ANY. A partial arm judged is money spent on a corpus that
# cannot enter the primary, and a short arm silently changes the paired denominator of the others.
for tag in $TAGS; do
  dir=$(pick "$tag")
  if [ -z "$dir" ]; then echo "REFUSING $tag: no run dir carrying DONE.json"; exit 1; fi
  rows=$(wc -l < "$dir/results.jsonl")
  if [ "$rows" -ne 1160 ]; then echo "REFUSING $tag: $rows rows, expected 1160"; exit 1; fi
  echo "pre-flight OK  $tag  <- $(basename "$dir")  rows=$rows"
done
echo "=== all 10 arms present and complete; judging in ONE invocation ==="
SNAP_BEFORE=$(snap); echo "B-016 served snapshot BEFORE: $SNAP_BEFORE"

for tag in $TAGS; do
  dir=$(pick "$tag")
  echo "=== judging $tag  <- $(basename "$dir") ==="
  python -u $R/src/boombness/judge_boombness.py --gens "$dir" --bank "$BANK" \
    --pin-judge-model openai/gpt-4o-mini --seed 20260905 --tag "p28j_${tag}"
done
SNAP_AFTER=$(snap)
echo "B-016 served snapshot BEFORE: $SNAP_BEFORE"
echo "B-016 served snapshot AFTER : $SNAP_AFTER"
if [ "$SNAP_BEFORE" != "$SNAP_AFTER" ]; then
  echo "⛔ SNAPSHOT ROTATED MID-RUN ($SNAP_BEFORE -> $SNAP_AFTER): the p28j labels are an average"
  echo "   over two judges. PR-028c's drift number and the primary both need this stated."
fi
