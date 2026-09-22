#!/bin/bash
# A5-8: bound the false negatives the AtP screen may have missed, per AtP* (LIT C1).
# The gate verified the top-40 cells; this samples the UNVERIFIED remainder and patches them for real.
#SBATCH --job-name=csi_fnbound
#SBATCH --output=outputs/boombness/logs/csi_fnbound_%j.out
#SBATCH --error=outputs/boombness/logs/csi_fnbound_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=03:00:00
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
[ -n "${CSI_GIT_BLOB:-}" ] || { echo "REFUSING: no CSI_GIT_BLOB" >&2; exit 3; }
echo "BLOB ${CSI_GIT_BLOB}  PORCELAIN [${CSI_GIT_PORCELAIN:-<UNSET>}]"
[ "${CSI_GIT_PORCELAIN:-<UNSET>}" = "clean" ] || { echo "REFUSING: dirty worktree" >&2; exit 4; }
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
python scripts/dcs_csi_head_fn_bound.py \
  --screen outputs/boombness/dcs_csi/w1_screen_train_basket_916132.json \
  --gate   outputs/boombness/dcs_csi/w2_patch_gate_train_basket_916044.json \
  --codeword basket --concept bomb --split train --band 6-14 \
  --n-cells 48 --rows 40 --seed 20260922 \
  --model "$SNAP" \
  --out reports/DCS_CSI_PR010_FN_BOUND.json
echo "---- done rc=$? $(date -Is)"
