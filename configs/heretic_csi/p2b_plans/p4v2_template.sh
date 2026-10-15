# P4 v2 HEAD-RESTRICTED operator eval (PREREG_P4 + AMENDMENT_1; written by F5; NOT YET SUBMITTED). Factors from p4_head_fit_v2.py --mode fit
#   (outputs/heretic_csi/p2b/prod/p4/factors_p4v2_<cw>_r<R>.pt). PREREG: configs/heretic_csi/PREREG_P4.json + PREREG_P4_AMENDMENT_1.json (must be
#   frozen + committed before the first P4 endpoint). Order: SPLIT=train_k4 first, then SPLIT=validation with the
#   SAME frozen factors (no refit).
# Arms under the CSI knockout: KO_TOP8 (candidate), KO_RH8RAW_0..59 (random-8-head fits at own optimum), KO_RH8NC_0..59 (same head sets refit under per-module norm == TOP8), KO_TOP8_L6_14, KO_FULLO, KO_MLP, KO_ATTNMLP, KO_H2, KO_CELL_L10H2 (descriptive), BASE_TOP8.
#   Liveness: BASE/KO/KO_FULL/KO_IDENT are emitted in EVERY rank job at prefix hcsi_p4v2_<cw>_<split>_r<R> (within-job, one GPU).
# Usage (inside p2b_job.slurm): CW=<cw> R=<1|4> SPLIT=<train_k4|validation> bash p4v2_template.sh
set -euo pipefail
D=outputs/heretic_csi/p2b/prod; P4=$D/p4; F=$P4/factors_p4v2_${CW}_r${R}.pt
[ -f $F ] || { echo "P4_FACTORS_ABSENT $F"; exit 3; }
case "$SPLIT" in
  train_k4)   EXCL=runargs/heretic_csi/exclude_${CW}_K4.txt; N=268 ;;
  validation) EXCL=runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt; N=230 ;;
  *) echo "bad SPLIT"; exit 2 ;;
esac
PFX=hcsi_p4v2_${CW}_${SPLIT}
A=$D/argv_p4v2_${CW}_r${R}_${SPLIT}_${ATTEMPT}.txt; : > $A
# within-job liveness for EVERY rank job (BASE/KO/KO_FULL/KO_IDENT at the rank prefix): all comparisons of a rank stay on ONE GPU
$PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix ${PFX}_r${R} --what liveness --factors-dir $D/fac >> $A
$PY research/heretic_csi/p3p4_emit.py --what p4v2 --cw $CW --snap $SNAP --excl $EXCL --prefix ${PFX}_r${R} --file $F --n-rh8 60 >> $A
sha256sum $F > $P4/sha_v2_${CW}_r${R}_${SPLIT}_${ATTEMPT}.txt
mkdir -p $P4/code_${ATTEMPT}; cp research/heretic_csi/*.py $P4/code_${ATTEMPT}/
echo "P4V2_ARGV lines=$(wc -l < $A)"
$PY research/heretic_csi/p2b_runner.py --argv-file $A --out $P4/runner_v2_${CW}_r${R}_${SPLIT}_${ATTEMPT}.json --expect-n $N
echo "P4V2_PLAN_DONE $CW r$R $SPLIT"
