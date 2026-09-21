#!/bin/bash
# W3 EQUIVALENCE TEST: the same three smoke arms, run IN ONE PROCESS, must reproduce the
# separate-process results of job 916390 EXACTLY. If in-process looping changed any number, the
# 11.5 GPU-hours it saves would be bought with a silent difference in every arm.
#SBATCH --job-name=csi_w3val
#SBATCH --output=outputs/boombness/logs/csi_w3val_%j.out
#SBATCH --error=outputs/boombness/logs/csi_w3val_%j.err
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
[ -n "${CSI_GIT_BLOB:-}" ] || { echo "REFUSING: no CSI_GIT_BLOB" >&2; exit 3; }
echo "BLOB ${CSI_GIT_BLOB}  PORCELAIN [${CSI_GIT_PORCELAIN:-<UNSET>}]"
[ "${CSI_GIT_PORCELAIN:-<UNSET>}" = "clean" ] || { echo "REFUSING: dirty worktree" >&2; exit 4; }

SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
BANK=data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl
EXC=runargs/dcs_cont/exclude_basket_bomb_sow_train.txt
C="--bank $BANK --model $SNAP --query-kinds semantic_one_word --conditions natural_doublespeak --n-examples 4 --exclude-prompt-ids $EXC --limit 24 --readout-ids whole_answer --readout-max-batch 1 --answer-prefix Answer: --min-option-mass 0.05 --semantic-options bank_pair --option-mass-gate-scope pooled --option-mass-gate-min-dose 1 --attn-impl eager --dtype bfloat16 --seed 20260913 --intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only"

A=/tmp/w3_argv_${SLURM_JOB_ID}.txt
{
  echo "python src/boombness/score_behavior.py $C --arm W3_HD_KO  --tag csi3_w3_basket_W3_HD_KO"
  echo "python src/boombness/score_behavior.py $C --knockout-heads 0,1,2,3,4,5,6,7 --arm W3_HD_8 --tag csi3_w3_basket_W3_HD_8"
  echo "python src/boombness/score_behavior.py $C --arm W3_HD_KO2 --tag csi3_w3_basket_W3_HD_KO2"
} > $A
echo "--- argv file:"; cat $A | sed 's/--model [^ ]*/--model <SNAP>/' | cut -c1-150

python scripts/dcs_csi_arm_runner.py --argv-file $A \
  --out outputs/boombness/dcs_csi/w3_validate_${SLURM_JOB_ID}.json
echo "---- done rc=$? $(date -Is)"
