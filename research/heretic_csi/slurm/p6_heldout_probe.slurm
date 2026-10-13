#!/bin/bash
#SBATCH --job-name=hcsi_p6probe
#SBATCH --output=outputs/heretic_csi/logs/p6probe_%j.out
#SBATCH --error=outputs/heretic_csi/logs/p6probe_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
# HERETIC-CSI P5/C1: held-out (VALIDATION) probe quality, basket + button. CPU only.
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} $(date -Is)"
python research/heretic_csi/p6_heldout_probe.py --codeword basket \
  --corpus outputs/boombness/extract_boombness/cont1_behavioral_basket_bomb_20260910_113902_3966018 \
  --readout outputs/boombness/score_behavior/ts116m_readout_basket_bomb_20260907_152329_3191150 \
  --out reports/heretic_csi/hcsi_p6_heldout_probe_basket.json
python research/heretic_csi/p6_heldout_probe.py --codeword button \
  --corpus outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_20260910_152806_272296 \
  --readout outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103 \
  --out reports/heretic_csi/hcsi_p6_heldout_probe_button.json
echo "---- P6PROBE DONE $(date -Is)"
