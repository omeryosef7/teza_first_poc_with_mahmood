# P4 HEAD-RESTRICTED operator eval (written by F5; NOT YET SUBMITTED). Factors from p4_head_fit.py
#   (outputs/heretic_csi/p2b/prod/p4/factors_p4_<cw>_r<R>.pt). PREREG: configs/heretic_csi/PREREG_P4.json (must be
#   frozen + committed before the first P4 endpoint). Order: SPLIT=train_k4 first, then SPLIT=validation with the
#   SAME frozen factors (no refit).
# Arms under the CSI knockout: KO_TOP8 (primary candidate), KO_RH8_0..59 (fitted random-8-head controls, rescaled per
#   module to TOP8's norm), KO_FULLO, KO_MLP, KO_ATTNMLP, KO_H2, KO_CELL_L10H2 (descriptive), BASE_TOP8.
#   Liveness: LIVE=1 adds BASE/KO/KO_FULL/KO_IDENT via p2b_emit --what liveness.
# Usage (inside p2b_job.slurm): CW=<cw> R=<1|4> SPLIT=<train_k4|validation> LIVE=<0|1> bash p4_template.sh
set -euo pipefail
D=outputs/heretic_csi/p2b/prod; P4=$D/p4; F=$P4/factors_p4_${CW}_r${R}.pt
[ -f $F ] || { echo "P4_FACTORS_ABSENT $F"; exit 3; }
case "$SPLIT" in
  train_k4)   EXCL=runargs/heretic_csi/exclude_${CW}_K4.txt; N=268 ;;
  validation) EXCL=runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt; N=230 ;;
  *) echo "bad SPLIT"; exit 2 ;;
esac
PFX=hcsi_p4_${CW}_${SPLIT}
A=$D/argv_p4_${CW}_r${R}_${SPLIT}_${ATTEMPT}.txt; : > $A
[ "${LIVE:-0}" = "1" ] && $PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix $PFX --what liveness --factors-dir $D/fac >> $A
$PY research/heretic_csi/p3p4_emit.py --what p4 --cw $CW --snap $SNAP --excl $EXCL --prefix ${PFX}_r${R} --file $F --n-rh8 60 --base-arm >> $A
sha256sum $F > $P4/sha_${CW}_r${R}_${SPLIT}_${ATTEMPT}.txt
mkdir -p $P4/code_${ATTEMPT}; cp research/heretic_csi/*.py $P4/code_${ATTEMPT}/
echo "P4_ARGV lines=$(wc -l < $A)"
$PY research/heretic_csi/p2b_runner.py --argv-file $A --out $P4/runner_${CW}_r${R}_${SPLIT}_${ATTEMPT}.json --expect-n $N
echo "P4_PLAN_DONE $CW r$R $SPLIT"
