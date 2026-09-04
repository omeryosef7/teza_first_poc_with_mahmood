#!/bin/bash
# PR-024 / B-009: generate demonstration pools for the 78 NEW domains only.
#
# WHY SLURM AND NOT THE LOGIN NODE. demo_pools.py reaches the API through prepare_demos.gen_demos,
# which imports the `openai` client -- the exact import that hung >90s under NFS contention
# (`feedback_judge_cpu_not_login`). Its own docstring also says "Run in the MAIN loop or SLURM,
# never a subagent".
#
# WHY A NEW OUTPUT FILE. The existing 38-domain pools are an input to every committed bank. This
# writes demo_pools_78new.json and merges afterwards, so the canonical file is never touched --
# and demo_pools.py refuses to overwrite an existing --out without --refresh anyway.
#
# PARAMETERS ARE COPIED FROM THE EXISTING POOLS' OWN META, not from the CLI defaults, so the two
# halves of the 116-domain bank are homogeneous: seed 20260828 (not the default 20260816),
# codeword carrot, concept bomb, gpt-4o-mini, 40 per pool.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
DOMS=$(cat "$R/runargs/dcs/pr024_new_domains.txt")
n=$(awk -F, '{print NF}' <<< "$DOMS")
echo "[pr024] generating pools for $n new domains, seed 20260828, gpt-4o-mini"
python -u "$R/src/boombness/demo_pools.py" \
  --concept bomb --codeword carrot --model gpt-4o-mini --seed 20260828 \
  --n-per-pool 40 --domains "$DOMS" \
  --out "$R/data/boombness_prompts/demo_pools_78new.json"
