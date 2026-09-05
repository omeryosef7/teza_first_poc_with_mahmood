#!/bin/bash
#SBATCH --job-name=p28judge
#SBATCH --output=outputs/boombness/logs/p28judge_%j.out
#SBATCH --error=outputs/boombness/logs/p28judge_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
bash scripts/judge_pr028_all10.sh
