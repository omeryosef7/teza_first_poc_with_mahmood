#!/bin/bash
#SBATCH --job-name=p3judge
#SBATCH --output=outputs/boombness/logs/p3judge_%j.out
#SBATCH --error=outputs/boombness/logs/p3judge_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
# Same driver as Phase 2, parameterised. All FOUR cells of the 2x2 in one session -- p2A and
# p2C_band are re-judged here rather than reused from the Phase 2 session, because a 2x2 read across
# two sessions carries a drift that does not cancel in the arm-vs-arm cells.
export P2_MANIFEST=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/boombness/argsfiles/p3_arms.txt
export P2_EXPECTED=4
export P2_PREFIX=p3j
bash scripts/judge_p2.sh
