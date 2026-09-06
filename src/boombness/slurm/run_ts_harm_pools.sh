#!/bin/bash
#SBATCH --job-name=tsharm
#SBATCH --output=outputs/boombness/logs/tsharm_%j.out
#SBATCH --error=outputs/boombness/logs/tsharm_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
# DCS thesis-scale: generate CONCEPT-SPECIFIC HARM pools (DCS-C-074).
#
# A sibling of run_demo_pools.sh rather than an edit to it: that script drives
# `demo_pools.py`, which regenerates EVERY valence, and regenerating benign/remap/filler per
# concept is exactly the confound that voided the old 6-domain concept banks. This one drives
# `scripts/dcs_ts_gen_concept_harm_pools.py`, which generates the harm pool only and copies the
# other three byte-for-byte from the shared 116-domain pools.
#
# cpu-killable, NEVER the login node: `import openai` has hung >90 s under NFS contention here,
# and a 0-byte log under `set -e` then looks like "nothing ran" rather than "still importing".
# --time=08:00:00 because a full 116-domain concept is ~116 API rounds with up to 8 retries each.
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f .env ]; then set -a; source .env; set +a; fi
: "${OPENAI_API_KEY:?OPENAI_API_KEY not set}"
: "${TSH_CONCEPT:?TSH_CONCEPT not set}"
: "${TSH_OUT:?TSH_OUT not set}"
: "${TSH_SEED:=20260906}"
: "${TSH_DOMAINS:=}"

# Echo the resolved plan on the first lines so `head` on the log answers "did this run what I
# meant?" without reasoning about env plumbing -- the DCS-C-047 lesson, where six jobs ran the
# wrong script and exited COMPLETED 0:0.
echo "=== ts_harm_pools ==="; date; hostname
echo "script:  scripts/dcs_ts_gen_concept_harm_pools.py"
echo "concept: $TSH_CONCEPT"
echo "out:     $TSH_OUT"
echo "seed:    $TSH_SEED"
echo "domains: ${TSH_DOMAINS:-<all 116>}"
echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)  dirty=$(git status --porcelain 2>/dev/null | wc -l)"

python -u scripts/dcs_ts_gen_concept_harm_pools.py \
  --concept "$TSH_CONCEPT" --out "$TSH_OUT" --seed "$TSH_SEED" \
  ${TSH_DOMAINS:+--domains "$TSH_DOMAINS"}
echo "=== done ==="; date
