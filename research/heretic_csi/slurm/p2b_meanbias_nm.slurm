#!/bin/bash
#SBATCH --job-name=hcsi_mbnm
#SBATCH --output=outputs/heretic_csi/logs/meanbias_nm_%j.out
#SBATCH --error=outputs/heretic_csi/logs/meanbias_nm_%j.err
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --no-requeue
# AMENDMENT 6: norm-matched mean-gap bias per codeword x primary rank (TRAIN captures + frozen CAND factors only).
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
D=outputs/heretic_csi/p2b/prod; T=$D/fac/tmp_rederive_${SLURM_JOB_ID}; mkdir -p $T
for CW in basket button; do
  $PY research/heretic_csi/p2b_meanbias.py --clean $D/cap/cap_${CW}_BASE.pt --ko $D/cap/cap_${CW}_KO.pt --codeword $CW \
     --out $T/meanbias_${CW}.pt --nm-factors $D/fac/factors_${CW}_r1.pt,$D/fac/factors_${CW}_r4.pt \
     --nm-out $D/fac/meanbias_nm_${CW}_r1.pt,$D/fac/meanbias_nm_${CW}_r4.pt
  $PY - <<PYEOF
import torch
a = torch.load("$D/fac/meanbias_${CW}.pt")["bias"]; b = torch.load("$T/meanbias_${CW}.pt")["bias"]
assert set(a) == set(b) and all(torch.equal(a[k], b[k]) for k in a), "re-derived mean gap != frozen meanbias_${CW}.pt"
print("REDERIVE_EQUAL ${CW}")
PYEOF
done
sha256sum $D/fac/meanbias_nm_*.pt
echo "DONE_MARKER meanbias_nm"
