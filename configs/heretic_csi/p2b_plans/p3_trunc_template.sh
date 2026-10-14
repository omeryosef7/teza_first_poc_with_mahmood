# P3 SVD TRUNCATION / COMPONENT-REMOVAL eval of a learned P2b operator (written by F5; NOT YET SUBMITTED).
# GATE (hard): runs ONLY for a (codeword, rank) whose PRIMARY P2b verdict on VALIDATION is PASS. Pass the
#   p2b_analyze VALIDATION output as VAL_VERDICT_JSON; the plan refuses otherwise. A TRAIN-only pass is NOT enough.
# Arms (all under the CSI knockout, population = $SPLIT): KO_FULL (re-expressed CAND; must match KO_CAND),
#   KO_TOP{k} (raw top-k components), KO_TOP{k}N (top-k renormed per module to the full norm), KO_DROP{i} (full
#   minus component i), and per TOP{k}: NRAND rank-k random operators norm-matched per module to that key.
#   Liveness arms (BASE/KO/KO_FULL-rescue/KO_IDENT) come from the matching P2b run of the same split.
# Usage (inside p2b_job.slurm): CW=<cw> R=<rank> SPLIT=<train_k4|validation> VAL_VERDICT_JSON=<file> bash p3_trunc_template.sh
set -euo pipefail
D=outputs/heretic_csi/p2b/prod; F=$D/fac; OUT=$D/p3; mkdir -p $OUT
$PY - "$VAL_VERDICT_JSON" "$CW" "$R" <<'PYEOF'
import json, sys
f, cw, r = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = json.load(open(f))
assert d.get("codeword") == cw and d.get("split") == "validation", f"gate: {f} is not a {cw} VALIDATION verdict"
row = [x for x in d["rows"] if int(x.get("rank", -1)) == r]
assert row and str(row[0].get("verdict", "")).startswith("PASS"), f"gate: {cw} r{r} did not PASS on validation -> P3 not run"
print("P3_GATE_OK", cw, r, row[0]["verdict"])
PYEOF
case "$SPLIT" in
  train_k4)   EXCL=runargs/heretic_csi/exclude_${CW}_K4.txt; N=268 ;;
  validation) EXCL=runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt; N=230 ;;
  *) echo "bad SPLIT"; exit 2 ;;
esac
TF=$OUT/trunc_${CW}_r${R}.pt
[ -f $TF ] || $PY research/heretic_csi/p3_make_truncations.py --factors $F/factors_${CW}_r${R}.pt --key CAND --out $TF
A=$D/argv_p3_${CW}_r${R}_${SPLIT}_${ATTEMPT}.txt
$PY research/heretic_csi/p3p4_emit.py --what p3 --cw $CW --snap $SNAP --excl $EXCL --prefix hcsi_p3_${CW}_r${R}_${SPLIT} --file $TF --nrand ${NRAND:-40} > $A
sha256sum $F/factors_${CW}_r${R}.pt $TF > $OUT/sha_${CW}_r${R}_${SPLIT}_${ATTEMPT}.txt
mkdir -p $OUT/code_${ATTEMPT}; cp research/heretic_csi/*.py $OUT/code_${ATTEMPT}/
echo "P3_ARGV lines=$(wc -l < $A)"
$PY research/heretic_csi/p2b_runner.py --argv-file $A --out $OUT/runner_${CW}_r${R}_${SPLIT}_${ATTEMPT}.json --expect-n $N
echo "P3_PLAN_DONE $CW r$R $SPLIT"
