# OVERLAP check for a resumed primary r1 cell (PREREG AMENDMENT 5): re-run KO, KO_CAND_r1, KO_RAND_r1_0, KO_DER_r1_0
# (all completed by the preempted job ORIG) under the distinct prefix hcsi_p2b_<cw>_k4ovl -- never read by p2b_analyze --
# in THIS allocation, then require per-row |dy| <= 1e-6 vs ORIG's dirs. Usage: CW=<cw> ORIG=<preempted job id> bash ovl_template.sh
set -euo pipefail
D=outputs/heretic_csi/p2b/prod; F=$D/fac
if [ "${POP:-k4}" = "val" ]; then BP=hcsi_p2b_${CW}_val; EXCL=runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt; N=230
else BP=hcsi_p2b_${CW}_k4; EXCL=runargs/heretic_csi/exclude_${CW}_K4.txt; N=268; fi
OP=${BP}ovl${OVLSFX:-}
A=$D/argv_ovl_${CW}${OVLSFX:-}_${ATTEMPT}.txt
{ $PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix $OP --what liveness --factors-dir $F
  $PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix $OP --what rank --factors-dir $F --ranks 1 --nrand 1 --nshuf 0 --nder 1 --no-base-cand
} | grep -P -- "--arm (KO|KO_CAND_r1|KO_RAND_r1_0|KO_DER_r1_0) " > $A
[ "$(wc -l < $A)" = "4" ] || { echo "OVL_ARGV_WRONG $(wc -l < $A)"; exit 3; }
$PY research/heretic_csi/p2b_runner.py --argv-file $A --out $D/runner_ovl_${CW}${OVLSFX:-}_${ATTEMPT}.json --expect-n $N
set +e
$PY research/heretic_csi/p2b_overlap_check.py --prefix $BP --ovl-prefix $OP --arms KO,KO_CAND_r1,KO_RAND_r1_0,KO_DER_r1_0 \
   --expect-n $N --orig-job $ORIG --out $D/overlap_${CW}${POP:-}${OVLSFX:-}_${ATTEMPT}.json
echo "OVL_CHECK_RC=$? -> $D/overlap_${CW}${POP:-}${OVLSFX:-}_${ATTEMPT}.json"
