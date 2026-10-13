# P2b VALIDATION eval (PREREG_P2B_VALIDATION.json): FROZEN TRAIN operators from prod/fac (NO refit), population
# exclude_<cw>_bomb_sow_validation.txt = 230 rows / 23 validation domains. Same arm families/counts as the TRAIN
# primary + secondary cells: 61 RAND + 5 SHUF + 15 DER (81, all rows) and 61 CWRAND + 15 CWDER (76, codeword
# row only), + CAND, BASE_CAND, CWONLY, ATLAST, NEUT, CAPOP. RAND/CWRAND seeds = 7000+100r+i exactly as on TRAIN
# and norm-matched to the SAME frozen CAND => byte-identical control operators (see prereg for why).
# Usage: CW=<basket|button> R=<1|4> LIVE=<0|1> bash val_template.sh   (run inside p2b_job.slurm: needs $SNAP $PY $ATTEMPT)
set -euo pipefail
D=outputs/heretic_csi/p2b/prod; F=$D/fac; PFX=hcsi_p2b_${CW}_val; EXCL=runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt
[ -f $F/fit_summary_${CW}.json ] || { echo "FROZEN_FACTORS_ABSENT for $CW"; exit 3; }
A=$D/argv_val_${CW}_r${R}_${ATTEMPT}.txt; : > $A
mkdir -p $D/capop_val
[ "${LIVE:-0}" = "1" ] && $PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix $PFX --what liveness --factors-dir $F >> $A
$PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix $PFX --what rank --factors-dir $F --ranks $R \
   --nrand 61 --nshuf 5 --nder 15 --capop --capdir $D/capop_val --cw-nrand 61 --cw-nder 15 >> $A
sha256sum $F/factors_${CW}_r${R}.pt $F/factors_${CW}_r1.pt > $D/val_factors_sha_${CW}_r${R}_${ATTEMPT}.txt
mkdir -p $D/code_val_${ATTEMPT}; cp research/heretic_csi/*.py $D/code_val_${ATTEMPT}/
echo "VAL_ARGV lines=$(wc -l < $A) cw=$CW r=$R"
$PY research/heretic_csi/p2b_runner.py --argv-file $A --out $D/runner_val_${CW}_r${R}_${ATTEMPT}.json --expect-n 230
echo "VAL_PLAN_DONE $CW r$R"
