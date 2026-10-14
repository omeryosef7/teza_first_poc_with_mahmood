#!/bin/bash
#SBATCH --job-name=hcsi_meanbias
#SBATCH --output=outputs/heretic_csi/logs/meanbias_%j.out
#SBATCH --error=outputs/heretic_csi/logs/meanbias_%j.err
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
D=outputs/heretic_csi/p2b/prod
for CW in basket button; do
  $PY research/heretic_csi/p2b_meanbias.py --clean $D/cap/cap_${CW}_BASE.pt --ko $D/cap/cap_${CW}_KO.pt --codeword $CW --out $D/fac/meanbias_${CW}.pt
done
sha256sum $D/fac/meanbias_*.pt
echo "DONE_MARKER meanbias"
