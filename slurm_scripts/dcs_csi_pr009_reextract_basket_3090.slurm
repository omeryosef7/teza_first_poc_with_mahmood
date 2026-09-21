#!/bin/bash
# PR-CSI-009: re-extract basket's BEHAVIOURAL corpus on an RTX 3090.
#
# ONE TOKEN differs from the committed cont1_behavioral_basket_bomb_20260910_113902_3966018:
#   --layers 0,2,4,...,30,31  ->  --layers 18,20
# plus the two exemptions VOID condition 3 names (--tag, --model), amended into the prereg BEFORE
# this script was written. Every other flag is copied verbatim from that run's own config.json args.
#
# THE COMMAND IS INLINE. `sbatch --export=ALL,CMD="..."` truncates at the first comma and --layers is
# a comma list -- the lesson slurm_scripts/dcs_csi_extract_sow_basket.slurm records in its header.
#
# --gpus=geforce_rtx_3090:1 is a POSITIVE architecture constraint, never an exclude-list (job 906421).
# The V100 is the whole point of the experiment: it is what the committed corpus ran on.
#
#SBATCH --job-name=csi_re3090
#SBATCH --output=outputs/boombness/logs/csi_re3090_%j.out
#SBATCH --error=outputs/boombness/logs/csi_re3090_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
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
echo "PR-CSI-009 | prereg 51731fc8 | blob $(git hash-object src/boombness/score_behavior.py | cut -c1-8) | porcelain '$(git status --porcelain src/boombness/score_behavior.py scripts/dcs_extract_under_ko.py)'"
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
python scripts/dcs_extract_under_ko.py \
  --bank data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl \
  --model "$SNAP" \
  --no-knockout \
  --arm demo_all --band 6-14 --knockout-scope legacy_all_query --knockout-random-row-draw -1 \
  --layers 18,20 \
  --multipos --position codeword_last \
  --only-query-kind behavioral --only-n-examples 4 --only-split train,validation \
  --on-no-demo-block skip \
  --capture-rel-end=-16..-1 --capture-codeword-occ \
  --dtype bfloat16 --attn-impl eager --seed 20260905 \
  --tag cont1re_behavioral_basket_bomb
echo "---- done rc=$? $(date -Is)"
