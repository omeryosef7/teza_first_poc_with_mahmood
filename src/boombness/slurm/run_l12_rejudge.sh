#!/bin/bash
#SBATCH --job-name=l12rj
#SBATCH --output=outputs/boombness/logs/l12rj_%j.out
#SBATCH --error=outputs/boombness/logs/l12rj_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=03:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
set -a; source /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/.env; set +a
export PYTHONPATH=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/src/boombness:${PYTHONPATH:-}
python -u src/boombness/judge_boombness.py --gens "outputs/boombness/score_behavior/abL12_B_20260819_063539_2455409"   --bank /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/data/boombness_prompts/external/advbench_heldout_495.jsonl   --seed 20260816 --tag a24c_ARM_L12
