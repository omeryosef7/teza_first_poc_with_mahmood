#!/bin/bash
# 29-domain pool generation (user-directed: "do the whole 19 domains").
#
# WRITES TO A NEW FILE. The canonical data/boombness_prompts/demo_pools.json is the pool set every
# existing bank and claim was generated from; regenerating it in place would change those pools and
# silently invalidate the corpus. This writes demo_pools_29dom.json and leaves the canonical file
# byte-identical.
#
# API work runs on cpu-killable, never the login node: `import openai` hangs >90s under NFS
# contention there, and a 0-byte log under `set -e` reads as "nothing ran" rather than "hung".
#SBATCH --job-name=pools29
#SBATCH --output=outputs/boombness/logs/pools29_%j.out
#SBATCH --error=outputs/boombness/logs/pools29_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=04:00:00
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
# UNBUFFERED. Without this, stdout is block-buffered to the log file and a multi-hour job is
# indistinguishable from a hung one -- the first run showed no output at all for 7 minutes,
# including the startup line. The loop requires detecting stalls from the LOG rather than from
# squeue state, and that is impossible without per-pool progress arriving as it happens.
export PYTHONUNBUFFERED=1
echo "[pools29] starting $(date -Is)"
"$PY" -u src/boombness/demo_pools.py \
  --out "$R/data/boombness_prompts/demo_pools_29dom.json" \
  --seed 20260828 --refresh
echo "[pools29] done $(date -Is)"
