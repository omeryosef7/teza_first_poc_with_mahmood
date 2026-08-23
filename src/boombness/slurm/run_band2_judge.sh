#!/bin/bash
#SBATCH --job-name=bnd2judge
#SBATCH --output=outputs/boombness/logs/bnd2judge_%j.out
#SBATCH --error=outputs/boombness/logs/bnd2judge_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
bash scripts/judge_band2.sh
