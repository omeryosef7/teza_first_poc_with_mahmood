#!/bin/bash
# HERETIC-CSI P3/P4 CPU analysis (no GPU). Usage: sbatch p3_p4_cpu.slurm <python args...>
#SBATCH --job-name=hcsi_p3p4
#SBATCH --output=outputs/heretic_csi/logs/p3p4_%j.out
#SBATCH --error=outputs/heretic_csi/logs/p3p4_%j.err
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --time=12:00:00
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=16
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID} $(date -Is) ARGS=$*"
mkdir -p outputs/heretic_csi/p3p4/code_${SLURM_JOB_ID}
cp research/heretic_csi/p3_*.py research/heretic_csi/p4_*.py outputs/heretic_csi/p3p4/code_${SLURM_JOB_ID}/ 2>/dev/null || true
sha256sum research/heretic_csi/p3_*.py research/heretic_csi/p4_*.py 2>/dev/null || true
"$PY" "$@"
echo "DONE_MARKER p3p4 rc=$? $(date -Is)"
