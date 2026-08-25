#!/bin/bash
#SBATCH --job-name=dpools
#SBATCH --output=outputs/boombness/logs/dpools_%j.out
#SBATCH --error=outputs/boombness/logs/dpools_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
# Generates a demonstration pool via the OpenAI API. On cpu-killable, NEVER the login node:
# `import openai` has hung >90s under NFS contention there, and a 0-byte log under `set -e` then
# looks like "nothing ran" rather than "still importing".
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f .env ]; then set -a; source .env; set +a; fi
: "${OPENAI_API_KEY:?OPENAI_API_KEY not set}"
: "${DP_CONCEPT:?DP_CONCEPT not set}"
: "${DP_CODEWORD:?DP_CODEWORD not set}"
: "${DP_OUT:?DP_OUT not set}"
# DP_SEED defaults to the value this script hardcoded until 2026-08-25, so every prior invocation
# reproduces byte-for-byte. It is a parameter now because Section 20 Q5 asks whether the mechanism
# survives an INDEPENDENT demonstration pool, and independence here means new demonstration
# SENTENCES from the same design -- which is exactly what a different generator seed produces.
: "${DP_SEED:=20260816}"
echo "[dpools] concept=$DP_CONCEPT codeword=$DP_CODEWORD seed=$DP_SEED -> $DP_OUT"
python -u src/boombness/demo_pools.py \
  --concept "$DP_CONCEPT" --codeword "$DP_CODEWORD" --seed "$DP_SEED" --out "$DP_OUT"
