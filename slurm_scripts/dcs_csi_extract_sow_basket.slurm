#!/bin/bash
# Phase 1 prerequisite: the semantic_one_word activation corpus for BASKET.
# The button corpus (cont1_semantic_one_word_button_bomb_20260910_163857_282805, 3720 rows,
# 873 s) already exists; basket has only a BEHAVIORAL corpus. Phase 1 fits its installation
# axis on the SAME forward pass it will intervene on -- the semantic_one_word prompt -- so a
# basket semantic corpus is required before basket can replicate the subspace rescue.
#
# The command is INLINE: --layers is a comma list and `sbatch --export=ALL,CMD="..."` truncates
# at the first comma. Flags copied verbatim from the button run's metadata.json command, with
# only --bank and --tag changed, so the two corpora are captured identically.
#
#SBATCH --job-name=csi_sowbk
#SBATCH --output=outputs/boombness/logs/csi_sowbk_%j.out
#SBATCH --error=outputs/boombness/logs/csi_sowbk_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=01:30:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} $(date -Is)"
nvidia-smi --query-gpu=name --format=csv,noheader || true
# --model MUST be the local snapshot. The button corpus's metadata records `--model null`, which
# resolved to the HF id `meta-llama/Llama-3.1-8B-Instruct`; on n-306 that has no weights in the
# cache and job 896365 died in 71 s with "does not appear to have a file named model.safetensors".
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
python scripts/dcs_extract_under_ko.py \
  --bank data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl \
  --model "$SNAP" \
  --no-knockout \
  --layers 0,2,4,6,8,10,11,12,13,14,16,18,20,22,24,26,28,30,31 \
  --position codeword_last \
  --only-query-kind semantic_one_word --only-n-examples 4 --only-split train,validation \
  --capture-rel-end=-16..-1 --capture-codeword-occ \
  --tag cont1_semantic_one_word_basket_bomb
echo "---- done rc=$? $(date -Is)"
