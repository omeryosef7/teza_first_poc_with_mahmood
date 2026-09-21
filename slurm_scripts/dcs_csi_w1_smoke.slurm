#!/bin/bash
# W1 smoke: 2 rows, end-to-end, to prove the AtP path runs before any screen is believed.
#SBATCH --job-name=csi_w1smoke
#SBATCH --output=outputs/boombness/logs/csi_w1smoke_%j.out
#SBATCH --error=outputs/boombness/logs/csi_w1smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:40:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=geforce_rtx_3090:1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} $(date -Is)"
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader || true
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
python scripts/dcs_csi_head_atp.py \
  --bank data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl \
  --codeword basket --concept bomb --split train --band 6-14 \
  --model "$SNAP" --limit 2 \
  --out outputs/boombness/dcs_csi/w1_smoke_${SLURM_JOB_ID}.json
echo "---- done rc=$? $(date -Is)"
