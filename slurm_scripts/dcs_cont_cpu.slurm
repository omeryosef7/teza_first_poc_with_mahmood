#!/bin/bash
# Generic CPU-only analysis runner for the DCS continuation phase.
#
# WHY THIS EXISTS. The candidate-scoring scripts read the ~11 GB multiposition_reps.pt cache.
# Even memory-mapped (RSS ~0.5 GB) they fill the OS page cache, and on the shared interactive
# node c-001 that repeatedly tripped the session's low-memory guard and the job was killed.
# A SLURM compute node with reserved memory runs outside that monitor and cannot be starved by
# other users. No GPU is used by the analysis; --gpus=1 is only to satisfy the killable
# partition's scheduling and is released in minutes.
#
# Usage:
#   sbatch --export=ALL,DCS_CMD="python scripts/dcs_cont_qprobe.py --n-perm 200" \
#          slurm_scripts/dcs_cont_cpu.slurm
#
#SBATCH --job-name=dcs_cpu
#SBATCH --output=outputs/boombness/logs/dcs_cpu_%j.out
#SBATCH --error=outputs/boombness/logs/dcs_cpu_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -z "${DCS_CMD:-}" ]; then echo "ERROR: DCS_CMD not exported"; exit 2; fi
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} $(date -Is)"
echo "DCS_CMD=$DCS_CMD"
echo "----"
eval "$DCS_CMD"
echo "---- done rc=$? $(date -Is)"
