#!/bin/bash
# W2: the section 3.4 TRUE-PATCH GATE over W1's screen. TRAIN only.
# Takes SCREEN=<path> in the environment; refuses without it.
#SBATCH --job-name=csi_w2gate
#SBATCH --output=outputs/boombness/logs/csi_w2gate_%j.out
#SBATCH --error=outputs/boombness/logs/csi_w2gate_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=04:00:00
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
if [ -z "${CSI_GIT_BLOB:-}" ]; then
  echo "REFUSING: CSI_GIT_BLOB not exported by the submitter (git does not exist on the node)" >&2
  exit 3
fi
echo "BLOB ${CSI_GIT_BLOB}  PORCELAIN [${CSI_GIT_PORCELAIN:-<UNSET>}]"
[ "${CSI_GIT_PORCELAIN:-<UNSET>}" = "clean" ] || { echo "REFUSING: dirty worktree at submit" >&2; exit 4; }
if [ -z "${SCREEN:-}" ]; then echo "REFUSING: SCREEN not set" >&2; exit 5; fi
if [ ! -s "${SCREEN}" ]; then echo "REFUSING: SCREEN does not exist or is empty: ${SCREEN}" >&2; exit 6; fi
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
python scripts/dcs_csi_head_patch_gate.py \
  --screen "${SCREEN}" \
  --codeword basket --concept bomb --split train --band 6-14 \
  --gate-rows 40 --topk 40 --min-corr 0.7 \
  --model "$SNAP" \
  --out outputs/boombness/dcs_csi/w2_patch_gate_train_basket_${SLURM_JOB_ID}.json
echo "---- done rc=$? $(date -Is)"
