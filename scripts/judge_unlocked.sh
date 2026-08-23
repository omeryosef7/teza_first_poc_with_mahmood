#!/bin/bash
# Judge the L10/L12 densification (28 controls) plus a fresh baseline.
# Manifest is built and cardinality-asserted in Python (28 expected) BEFORE submission -- the
# fan-out-asserts-its-own-count rule added after the zsh word-split incident.
#
# MANIFEST LIVES ON THE SHARED FS, NOT /tmp. The first version read it from
# /tmp/claude-47249/, which is NODE-LOCAL: written on the login node, absent on the compute
# node, so the loop would have read an empty file and judged ZERO controls while the job
# exited 0 saying "judging done: 0 controls". Caught before it ran (recorded hazard:
# feedback_slurm_argsfile_shared_fs).
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$R/.env" ]; then set -a; source "$R/.env"; set +a; fi
export PYTHONPATH="$R/src/boombness:${PYTHONPATH:-}"
BANK=$R/data/boombness_prompts/external/advbench_heldout_495.jsonl
python -u src/boombness/judge_boombness.py --gens outputs/boombness/score_behavior/ab_base_20260818_185458_3888976 --bank "$BANK" --tag unlk_base
i=0
while IFS=: read -r tag gens; do
  [ -n "$tag" ] || continue
  python -u src/boombness/judge_boombness.py --gens "$gens" --bank "$BANK" --tag "unlk_${tag}" &
  i=$((i+1)); if [ $((i % 6)) -eq 0 ]; then wait; fi
done < "$R/outputs/boombness/argsfiles/unlock_runs.txt"
wait
echo "=== a24b judging done: $i controls ==="
