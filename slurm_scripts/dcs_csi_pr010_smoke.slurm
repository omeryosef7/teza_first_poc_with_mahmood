#!/bin/bash
# PR-CSI-010 / design section 7.3: THE SMOKE THAT MUST PASS BEFORE ANYTHING IN 7.2 IS LAUNCHED.
#   1. SMOKE_HD_KO  -- 24 rows, ALL heads
#   2. SMOKE_HD_8   -- the SAME 24 rows, --knockout-heads 0,1,2,3,4,5,6,7
#                      A FIXED PLACEHOLDER SET, NOT AN AtP RESULT. This is a wiring test, and the
#                      design requires the placeholder be DISCARDED before the real arms run.
#   3. SMOKE_ATP    -- W1 on 8 rows
# It also MEASURES the section 7.2 cost risk: a head-restricted arm takes the am.expand(...).clone()
# branch that an all-head arm does not. If the wall ratio exceeds 1.5x, section 7.2's table is
# re-derived from the measured factor and NOTHING is launched on the old estimate.
#SBATCH --job-name=csi_pr010smoke
#SBATCH --output=outputs/boombness/logs/csi_pr010smoke_%j.out
#SBATCH --error=outputs/boombness/logs/csi_pr010smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=02:00:00
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

SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
BANK=data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl
EXC=runargs/dcs_cont/exclude_basket_bomb_sow_train.txt
COMMON="--bank $BANK --model $SNAP --query-kinds semantic_one_word --conditions natural_doublespeak \
 --n-examples 4 --exclude-prompt-ids $EXC --limit 24 \
 --readout-ids whole_answer --readout-max-batch 1 --answer-prefix Answer: \
 --min-option-mass 0.05 --semantic-options bank_pair --option-mass-gate-scope pooled \
 --option-mass-gate-min-dose 1 --attn-impl eager --dtype bfloat16 --seed 20260913 \
 --intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only"

echo "===== 1. SMOKE_HD_KO (all heads) ====="
python src/boombness/score_behavior.py $COMMON \
  --arm SMOKE_HD_KO --tag csi3_smoke_basket_SMOKE_HD_KO

echo "===== 2. SMOKE_HD_8 (placeholder 0..7 -- NOT an AtP result) ====="
python src/boombness/score_behavior.py $COMMON \
  --knockout-heads 0,1,2,3,4,5,6,7 \
  --arm SMOKE_HD_8 --tag csi3_smoke_basket_SMOKE_HD_8

echo "===== 3. SMOKE_ATP (W1 on 8 rows) ====="
python scripts/dcs_csi_head_atp.py \
  --bank $BANK --codeword basket --concept bomb --split train --band 6-14 \
  --model "$SNAP" --limit 8 \
  --out outputs/boombness/dcs_csi/pr010_smoke_atp_${SLURM_JOB_ID}.json

echo "---- done rc=$? $(date -Is)"
