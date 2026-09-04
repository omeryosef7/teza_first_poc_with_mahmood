#!/bin/bash
# PR-019 / PR-019a plausibility ratings, driven through run_judge_cpu.sh.
#
# WHY NOT THE LOGIN NODE. dcs_plausibility_rating.py uses stdlib urllib, not the `openai` package,
# so it does NOT trigger the specific failure `feedback_judge_cpu_not_login` records (an `import
# openai` that hung >90s on an NFS directory listing). It runs here anyway because the script's own
# docstring declares "never runs on the login node", and relaxing a declared constraint to save two
# minutes is the pattern this phase's log exists to catch. The cost is one cpu-killable slot.
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood

# 1. REGRESSION: re-run PR-019's ORIGINAL batched instrument after the per-item refactor moved its
#    loop into `_batched`. `R-045` is a published result and a refactor that silently changed it
#    would be invisible. Same seed, same rubric => must reproduce 5-of-38 over the gate.
echo "=== [1/2] regression: PR-019 batched instrument, must reproduce R-045 ==="
python -u "$R/scripts/dcs_plausibility_rating.py" --tag dcs_plausibility_regression

# 2. PR-019a: per-item, two rubric paraphrases, no batching and therefore no order axis.
echo "=== [2/2] PR-019a: per-item, paraphrase-gated ==="
python -u "$R/scripts/dcs_plausibility_rating.py" --per-item --tag dcs_plausibility_peritem
