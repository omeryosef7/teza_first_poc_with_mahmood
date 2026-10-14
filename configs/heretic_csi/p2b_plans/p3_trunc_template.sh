# P3 SVD TRUNCATION / COMPONENT-REMOVAL eval of a learned P2b operator (written by F5; NOT YET SUBMITTED).
# GATE (hard): runs ONLY for a (codeword, rank) whose PRIMARY P2b verdict on VALIDATION is PASS. Pass the
#   p2b_analyze VALIDATION output as VAL_VERDICT_JSON; the plan refuses otherwise. A TRAIN-only pass is NOT enough.
# Arms (all under the CSI knockout, population = $SPLIT):
#   KO_TOP{k} (raw top-k components), KO_TOP{k}N (top-k renormed per module to the full norm), KO_DROP{i} (full
#   minus component i), KO_REEXP (CAND re-expressed; must reproduce KO_CAND), per TOP{k}: NRAND rank-k random operators
#   norm-matched per module to that key, per TOP{k}N: NRAND_N such controls (descriptive).
#   Liveness arms (BASE/KO/KO_FULL whole-state rescue/KO_IDENT) are run INSIDE this job (same GPU as every P3 arm).
# Usage (inside p2b_job.slurm): CW=<cw> R=<rank> SPLIT=<train_k4|validation> VAL_VERDICT_JSON=<file> bash p3_trunc_template.sh
set -euo pipefail
D=outputs/heretic_csi/p2b/prod; F=$D/fac; OUT=$D/p3; mkdir -p $OUT
$PY research/heretic_csi/p3_gate.py "$VAL_VERDICT_JSON" "$CW" "$R"
case "$SPLIT" in
  train_k4)   EXCL=runargs/heretic_csi/exclude_${CW}_K4.txt; N=268 ;;
  validation) EXCL=runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt; N=230 ;;
  *) echo "bad SPLIT"; exit 2 ;;
esac
TF=$OUT/trunc_${CW}_r${R}.pt
[ -f $TF ] || $PY research/heretic_csi/p3_make_truncations.py --factors $F/factors_${CW}_r${R}.pt --key CAND --out $TF
A=$D/argv_p3_${CW}_r${R}_${SPLIT}_${ATTEMPT}.txt; : > $A
# within-job liveness (BASE/KO/KO_FULL/KO_IDENT): every P3 comparison stays on ONE GPU (cross-hardware readout noise, S-062)
$PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix hcsi_p3_${CW}_r${R}_${SPLIT} --what liveness --factors-dir $F >> $A
$PY research/heretic_csi/p3p4_emit.py --what p3 --cw $CW --snap $SNAP --excl $EXCL --prefix hcsi_p3_${CW}_r${R}_${SPLIT} --file $TF --nrand ${NRAND:-40} --nrand-n ${NRAND_N:-20} >> $A
sha256sum $F/factors_${CW}_r${R}.pt $TF > $OUT/sha_${CW}_r${R}_${SPLIT}_${ATTEMPT}.txt
mkdir -p $OUT/code_${ATTEMPT}; cp research/heretic_csi/*.py $OUT/code_${ATTEMPT}/
echo "P3_ARGV lines=$(wc -l < $A)"
$PY research/heretic_csi/p2b_runner.py --argv-file $A --out $OUT/runner_${CW}_r${R}_${SPLIT}_${ATTEMPT}.json --expect-n $N
echo "P3_PLAN_DONE $CW r$R $SPLIT"
