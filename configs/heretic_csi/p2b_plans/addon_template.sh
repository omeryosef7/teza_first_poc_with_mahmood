# PREREG AMENDMENT 3 add-on (DESCRIPTIVE): MEANBIAS (all rows / codeword row / clean) + raw-norm DER/SHUF at ranks 1,4.
# Usage: CW=<cw> POP=<k4|val> bash addon_template.sh   (inside p2b_job.slurm). Needs prod/fac/meanbias_<cw>.pt
# (built on CPU by p2b_meanbias.py from the TRAIN captures) and the frozen factors.
set -euo pipefail
D=outputs/heretic_csi/p2b/prod; F=$D/fac; MB=$F/meanbias_${CW}.pt
if [ "$POP" = "k4" ]; then PFX=hcsi_p2b_${CW}_k4; EXCL=runargs/heretic_csi/exclude_${CW}_K4.txt; N=268
else PFX=hcsi_p2b_${CW}_val; EXCL=runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt; N=230; fi
[ -f $F/fit_summary_${CW}.json ] && [ -f $MB ] || { echo "FACTORS_OR_MEANBIAS_ABSENT"; exit 3; }
A=$D/argv_addon_${CW}_${POP}_${ATTEMPT}.txt
$PY research/heretic_csi/p2b_emit.py --cw $CW --snap $SNAP --excl $EXCL --prefix $PFX --what addon --factors-dir $F --ranks 1,4 --nder 15 --nshuf 5 --meanbias $MB > $A
sha256sum $MB $F/factors_${CW}_r1.pt $F/factors_${CW}_r4.pt > $D/addon_inputs_sha_${CW}_${POP}_${ATTEMPT}.txt
echo "ADDON_ARGV lines=$(wc -l < $A) cw=$CW pop=$POP"
$PY research/heretic_csi/p2b_runner.py --argv-file $A --out $D/runner_addon_${CW}_${POP}_${ATTEMPT}.json --expect-n $N
echo "ADDON_PLAN_DONE $CW $POP"
