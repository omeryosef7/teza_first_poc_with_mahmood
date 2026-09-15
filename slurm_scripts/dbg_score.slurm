#!/bin/bash
#SBATCH --job-name=dbg_score
#SBATCH --output=outputs/boombness/logs/dbg_score_%j.out
#SBATCH --error=outputs/boombness/logs/dbg_score_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=96G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --gpus=1
set -uo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
DBG=outputs/boombness/logs/dbg_score_capture.log
python -u src/boombness/score_behavior.py   --bank data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl --model /home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659   --query-kinds behavioral --conditions natural_doublespeak --n-examples 4 --max-new 64 --dtype bfloat16   --attn-impl eager --intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only   --limit 3 --arm KO_dbg --tag patch_dbg_ko_button > "$DBG" 2>&1
echo "PYTHON_RC=$?" >> "$DBG"
