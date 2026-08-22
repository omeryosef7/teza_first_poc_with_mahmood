#!/bin/bash
#SBATCH --job-name=xL6judge
#SBATCH --output=outputs/boombness/logs/xL6_%j.out
#SBATCH --error=outputs/boombness/logs/xL6_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
# CPU-only: judging is pure API traffic. NOT the login node -- `import openai` hung >90s there
# under NFS contention and a prior batch died silently with a 0-byte log.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
echo "=== xL6 crossover ==="; date; hostname
bash "$PROJECT_DIR/scripts/judge_xL6_crossover.sh"
echo "=== done ==="; date
