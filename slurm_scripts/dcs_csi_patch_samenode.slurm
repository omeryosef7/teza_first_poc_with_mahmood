#!/bin/bash
# P0.6 -- ALL FOUR button patch arms in ONE allocation on ONE node.
#
# WHY. The published button patch arms ran on three different nodes (ctrl/ko on t-806, rescue on
# n-801, size-match on n-803). All four were l40s, so the GPU ARCHITECTURE matched and the
# comparison is not invalid. But the recovery effect rests on FIVE refusal rows out of 180, and
# this project carries a standing finding that greedy generation churns across hardware (573/670
# completions changed in the cross-GPU case). Five rows is well inside the range a churn artifact
# could manufacture, so "same architecture" is not a strong enough guarantee for THIS effect size.
# Running all four arms back-to-back in one allocation makes the hardware bit-identical across
# arms by construction, and comparing the result against the existing runs MEASURES the same-
# architecture churn instead of assuming it is zero.
#
# It also amortises the model load: the matanbentov-hub NFS load has taken up to ~72 min, and
# paying it once instead of four times is most of the wall-clock saving here.
#
# The commands are INLINE. Passing them through `sbatch --export=ALL,CMD="...,..."` truncates at
# the first comma, which is how an earlier run silently lost its --layers list and every
# --only-*/--capture flag.
#
#SBATCH --job-name=csi_patch
#SBATCH --output=outputs/boombness/logs/csi_patch_%j.out
#SBATCH --error=outputs/boombness/logs/csi_patch_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=05:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2

SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
BANK=data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl
EXCL=runargs/patch/exclude_button.txt
COMMON="--bank $BANK --model $SNAP --query-kinds behavioral --conditions natural_doublespeak \
--n-examples 4 --bank-blocks cds_n4 --exclude-prompt-ids $EXCL --expect-n 180 --max-new 192 \
--dtype bfloat16 --attn-impl eager"
KO="--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only"

echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} $(date -Is)"
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader || true
echo "===================================================================="

echo ">>> ARM 1/4 CTRL $(date -Is)"
python src/boombness/score_behavior.py $COMMON --arm CTRL --tag p0cmp_ctrl_button

echo ">>> ARM 2/4 KO $(date -Is)"
python src/boombness/score_behavior.py $COMMON $KO --arm KO --tag p0cmp_ko_button

echo ">>> ARM 3/4 RESCUE_CLEAN $(date -Is)"
python src/boombness/score_behavior.py $COMMON $KO \
  --rescue-donor clean --rescue-positions query --rescue-layer 20 \
  --arm RESCUE_CLEAN --tag p0cmp_rescue_clean_button

echo ">>> ARM 4/4 SIZEMATCH12 $(date -Is)"
python src/boombness/score_behavior.py $COMMON $KO \
  --rescue-donor clean --rescue-positions query --rescue-layer 20 --rescue-n-positions 12 \
  --arm SIZEMATCH12 --tag p0cmp_sizematch_button

echo "---- ALL FOUR ARMS DONE rc=$? $(date -Is) HOST=$(hostname)"
