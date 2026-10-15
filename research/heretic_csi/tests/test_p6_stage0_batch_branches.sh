#!/bin/bash
# CPU branch test of research/heretic_csi/slurm/p6_stage0_batch.slurm under `bash -u` (parent request after 1040533's
# `RRC: unbound variable`). Runs the REAL script text in a sandbox with python components stubbed (tests/p6_stub.py).
# Branches: reuse-readout (lamp), fresh readout rc=4 + G3 PASS + extraction (kettle), G3 FAIL (pencil),
# health fail (ladder), readout crash/no DONE (blanket), extraction fail (bucket). Exits non-zero on any mismatch.
set -euo pipefail
REPO=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
SB=$(mktemp -d /tmp/claude-47249/-home-sharifm-students-omeryosef-first-poc-teza-first-poc-with-mahmood/b2d5e7b5-e18e-4ee6-ba19-55fa20bf97cb/scratchpad/p6sb.XXXX)
mkdir -p "$SB/outputs/boombness/score_behavior" "$SB/outputs/boombness/extract_boombness" "$SB/outputs/heretic_csi/p6" "$SB/scratch_extract" "$SB/research/heretic_csi/slurm"
ln -s "$REPO/data" "$SB/data"; ln -s "$REPO/src" "$SB/src"; ln -s "$REPO/scripts" "$SB/scripts"
cp "$REPO/research/heretic_csi/p6_select_run.py" "$REPO/research/heretic_csi/p6_write_manifest.py" "$SB/research/heretic_csi/"
STUB="$REPO/research/heretic_csi/tests/p6_stub.py"
sed -e "s#^cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood#cd $SB#" \
    -e '/^source .*conda.sh/d' -e '/^conda activate/d' -e '/^nvidia-smi/d' \
    -e "s#^XDST=.*#XDST=$SB/scratch_extract#" \
    -e 's#^AVAIL_KB=.*#AVAIL_KB=0; MODEL="$SCR"#' \
    -e '/^if \[ "${AVAIL_KB:-0}" -ge 18000000 \] && cp/,/^else rm -rf/d' \
    -e "s#\"\$PY\" src/boombness/score_behavior.py#\"\$PY\" $STUB score#" \
    -e "s#\"\$PY\" scripts/dcs_extract_under_ko.py#\"\$PY\" $STUB extract#" \
    -e "s#\"\$PY\" research/heretic_csi/p6_g3.py#\"\$PY\" $STUB g3#" \
    -e "s#\"\$PY\" research/heretic_csi/p6_install_strength.py#\"\$PY\" $STUB g1#" \
    "$REPO/research/heretic_csi/slurm/p6_stage0_batch.slurm" > "$SB/batch.sh"
cp "$SB/batch.sh" "$SB/research/heretic_csi/slurm/p6_stage0_batch.slurm"
# reuse branch: a valid earlier readout for lamp from "job 999" with a manifest pointing at it
mkdir -p "$SB/outputs/boombness/score_behavior/ts116m_readout_lamp_bomb_OLD"
echo '{"slurm_job_id": "999"}' > "$SB/outputs/boombness/score_behavior/ts116m_readout_lamp_bomb_OLD/RUNMETA.json"
echo '{}' > "$SB/outputs/boombness/score_behavior/ts116m_readout_lamp_bomb_OLD/DONE.json"
echo pass > "$SB/outputs/boombness/score_behavior/ts116m_readout_lamp_bomb_OLD/plan.txt"
echo '{"readout_dir": "outputs/boombness/score_behavior/ts116m_readout_lamp_bomb_OLD", "slurm_job": "999"}' > "$SB/outputs/heretic_csi/p6/stage0_lamp.json"
export STUB_PLAN="kettle:pass,pencil:g3fail,ladder:health,blanket:noreadout,bucket:extractfail" SLURM_JOB_ID=4242
bash -u "$SB/batch.sh" lamp,kettle,pencil,ladder,blanket,bucket > "$SB/out.log" 2>&1 || { echo "SCRIPT EXITED rc=$?"; tail -20 "$SB/out.log"; exit 1; }
grep -q "unbound variable" "$SB/out.log" && { echo "FAIL unbound"; exit 1; }
want="lamp:G3_PASS kettle:G3_PASS pencil:G3_FAIL ladder:ERROR_HEALTH blanket:ERROR bucket:ERROR_EXTRACT"
fail=0
for w in $want; do cw=${w%%:*}; st=${w#*:}
  got=$(grep "DONE_MARKER p6_stage0 cw=$cw " "$SB/out.log" | sed 's/.*status=\([A-Z0-9_]*\).*/\1/')
  [ "$got" == "$st" ] && echo "OK   $cw $got" || { echo "FAIL $cw want=$st got=$got"; fail=1; }
done
grep -q "REUSE_READOUT cw=lamp" "$SB/out.log" && echo "OK   lamp reused readout" || { echo "FAIL lamp not reused"; fail=1; }
python3 - "$SB" <<'PY' || fail=1
import json, os, sys
sb = sys.argv[1]
m = json.load(open(f"{sb}/outputs/heretic_csi/p6/stage0_kettle.json"))
assert m["status"] == "G3_PASS" and m["extract_dir"] and os.path.islink(os.path.join(sb, m["extract_dir"])), m
assert m["readout_slurm_job"] == "4242" and m["extract_slurm_job"] == "4242", m
l = json.load(open(f"{sb}/outputs/heretic_csi/p6/stage0_lamp.json"))
assert l["readout_slurm_job"] == "999" and l["extract_slurm_job"] == "4242", l
p = json.load(open(f"{sb}/outputs/heretic_csi/p6/stage0_pencil.json"))
assert p["extract_dir"] is None and p["g1"] is None, p
assert m["g1"]["install_strength_C_minus_A"] == 0.5 and m["g1_provenance"]["readout_dir"], m
assert m["rc"]["readout"] == "4" and m["rc"]["extract"] == "0", m["rc"]
b = json.load(open(f"{sb}/outputs/heretic_csi/p6/stage0_blanket.json"))
assert b["status"] == "ERROR" and b["rc"]["readout"] == "1", b
x = json.load(open(f"{sb}/outputs/heretic_csi/p6/stage0_bucket.json"))
assert x["status"] == "ERROR_EXTRACT" and x["rc"]["extract"] == "1" and x["g1"] is not None, x
h = json.load(open(f"{sb}/outputs/heretic_csi/p6/stage0_ladder.json"))
assert h["status"] == "ERROR_HEALTH" and h["g1"] is None, h
print("OK   error-path manifests + rc + G1 provenance")
print("OK   manifests (kettle extract symlinked + jobs; lamp readout 999 / extract 4242; pencil no extract)")
PY
grep -q "BATCH_DONE" "$SB/out.log" && echo "OK   BATCH_DONE" || { echo "FAIL no BATCH_DONE"; fail=1; }
rm -rf "$SB"
[ $fail -eq 0 ] && echo "ALL_BRANCHES_OK" || { echo "BRANCH_TEST_FAILED"; exit 1; }
