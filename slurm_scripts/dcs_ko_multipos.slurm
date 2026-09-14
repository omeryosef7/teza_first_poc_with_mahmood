#!/bin/bash
# Knockout-live MULTIPOSITION extraction for the differ-across-arms causal test (CONT-155).
# Codeword is $1 (button|basket). The command is INLINE here on purpose: passing it through
# `sbatch --export=ALL,DCS_CMD="...,..."` truncates at the first comma (SLURM splits --export on
# commas), which is exactly how CONT-160's first ko run lost its --layers list and every --only-*/
# --capture flag and fell into the frozen single-layer full-bank mode.
#SBATCH --job-name=dcs_komp
#SBATCH --output=outputs/boombness/logs/dcs_komp_%j.out
#SBATCH --error=outputs/boombness/logs/dcs_komp_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
set -euo pipefail
CW="${1:?usage: sbatch dcs_ko_multipos.slurm <button|basket>}"
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
BANK="data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl"
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} CW=$CW $(date -Is)"
python scripts/dcs_extract_under_ko.py \
  --bank "$BANK" --model "$SNAP" \
  --knockout-scope target_surface_row_only --arm demo_all --band 6-14 --attn-impl eager \
  --layers 0,2,4,6,8,10,11,12,13,14,16,18,20,22,24,26,28,30,31 \
  --position codeword_last \
  --only-query-kind behavioral --only-n-examples 4 --only-split train,validation \
  --capture-rel-end=-16..-1 --capture-codeword-occ \
  --tag "cont1ko_behavioral_${CW}_bomb"
echo "---- done rc=$? $(date -Is)"
