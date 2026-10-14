# PREREG AMENDMENT 6 (DESCRIPTIVE ONLY): KO_MEANBIAS_NM_r{1,4} + BASE_MEANBIAS_NM_r{1,4} per codeword, plus an
# in-allocation KO re-run per codeword for the overlap gate vs that codeword's liveness job.
# Usage (inside p2b_job.slurm): POP=<k4|val> LIVE_basket=<job> LIVE_button=<job> bash addon_nm_template.sh
set -euo pipefail
D=outputs/heretic_csi/p2b/prod; F=$D/fac
for CW in basket button; do
  if [ "$POP" = "k4" ]; then PFX=hcsi_p2b_${CW}_k4; EXCL=runargs/heretic_csi/exclude_${CW}_K4.txt; N=268
  else PFX=hcsi_p2b_${CW}_val; EXCL=runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt; N=230; fi
  LJ=$(eval echo \${LIVE_$CW})
  A=$D/argv_addonnm_${CW}_${POP}_${ATTEMPT}.txt
  $PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix $PFX --what addon_nm --factors-dir $F --ranks 1,4 > $A
  $PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix ${PFX}nmovl --what liveness --factors-dir $F | grep -P -- "--arm KO " >> $A
  sha256sum $F/meanbias_nm_${CW}_r1.pt $F/meanbias_nm_${CW}_r4.pt > $D/addonnm_inputs_sha_${CW}_${POP}_${ATTEMPT}.txt
  echo "ADDON_NM_ARGV lines=$(wc -l < $A) cw=$CW pop=$POP"
  $PY research/heretic_csi/p2b_runner.py --argv-file $A --out $D/runner_addonnm_${CW}_${POP}_${ATTEMPT}.json --expect-n $N
  set +e
  $PY research/heretic_csi/p2b_overlap_check.py --prefix $PFX --ovl-prefix ${PFX}nmovl --arms KO --expect-n $N --orig-job $LJ \
     --out $D/overlap_addonnm_${CW}_${POP}_${ATTEMPT}.json
  echo "ADDON_NM_OVL_RC=$?"
  set -e
done
echo "ADDON_NM_PLAN_DONE $POP"
