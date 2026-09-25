#!/bin/bash
# S-404: the PR-CSI-021 VALIDATION measurement. This is the HELD-OUT read.
#
# ⛔ NOT EXPLORATORY. Everything the smoke and the train pilot were allowed to be, this is not.
#    It measures the population the prereg freezes -- 230 rows over 23 VALIDATION domains -- and
#    its artefact is the input to scripts/dcs_csi_pr021_rung2_read.py, which computes the verdict.
#
# ⛔ EXPLORATORY. NOT a preregistered family. It computes no verdict and no p, and NOTHING it
#    produces may be quoted as a result. Its purpose is to find out whether the instrument RUNS --
#    R35 established it never had, and four blockers survived its 13 tests because of that.
#
# WHY TRAIN. The rung-2 design's population is VALIDATION, and validation is what a future prereg
#    would read. Burning it on a smoke would mean the first real read was the second look. TRAIN
#    is the discovery split by the manifest's own discipline line, and the instrument ENFORCES the
#    split from data/boombness_prompts/dcs_ts116_domain_split.json, so --split train reads train.
#
# ⛔ TEST IS UNREACHABLE HERE, and by construction rather than by declaration (R35-B/C, S-385):
#    the split manifest is enforced per row, the three preregistered whole-population domains are
#    excluded, and the population must match --expect-n/--expect-domains or the run REFUSES.
#    Passing the exclusion file alone is NOT sufficient -- it removes only the non-split part of
#    ONE bank_block/condition slice, which is how the first draft selected 116 domains including
#    all 23 TEST ones.
#
# WHAT IS FROZEN HERE AND WHY EACH IS EXPLICIT RATHER THAN DEFAULTED:
#    --dtype bfloat16      what every PR-CSI-020 arm ran. float32 is ~32 GB (does not fit a 3090)
#                          and is a MORE precise forward than the family this sits beside.
#    --answer-prefix       the endpoint reads templated + "Answer:" (score_behavior.py:87). The
#                          bare prompt end is 2 tokens earlier, at a position measured at a median
#                          5.6e-06 option mass and abandoned 2026-08-18 (R35-A/B, S-385).
#    --concept/--codeword  ' bomb'/' Bomb' vs ' basket'/' Basket'. NO DEFAULTS: the existing
#                          logit-lens control hardcodes ' button' (S-380), and the BARE-cased ids
#                          are different tokens again (13054 vs 79444), so four plausible wrong
#                          ids exist for the same four words.
#
#SBATCH --job-name=csi_rung2_val
#SBATCH --output=outputs/boombness/logs/csi_rung2_val_%j.out
#SBATCH --error=outputs/boombness/logs/csi_rung2_val_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=geforce_rtx_3090:1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} $(date -Is)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
echo "BLOB ${CSI_GIT_BLOB:-unset}  PORCELAIN [${CSI_GIT_PORCELAIN:-unset}]"

MODEL=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
LIMIT="${LIMIT:-0}"     # 0 = the full declared population. A limited VALIDATION run is not a read.
# ⚠ S-396: THE OUTPUT PATH WAS HARDCODED TO ..._SMOKE_... A full-population run (LIMIT=0) would
#   have OVERWRITTEN the committed smoke artefact AND landed a 670-row result under a filename
#   saying SMOKE. The artefact's own `IS_SMOKE` field would have said false while its NAME said
#   otherwise -- a file that contradicts itself is worse than either version alone. Caught at
#   submit time (927323 cancelled <1 min in, before the model load). The path now derives from
#   LIMIT so the two can never disagree.
# ⚠ S-396's lesson applies here too: the path must not be able to disagree with the content.
if [ "$LIMIT" -ne 0 ]; then
  echo "REFUSING: --limit %s on the VALIDATION read. A limited, domain-CONTIGUOUS sample is not" "$LIMIT"
  echo "  the declared population, and the reader refuses a SMOKE artefact anyway." >&2
  exit 1
fi
OUT=reports/DCS_CSI_RUNG2_VALIDATION_basket_full.json
echo "LIMIT=$LIMIT -> OUT=$OUT"
# ⚠ S-391: THE FIRST ATTEMPT (926941) BUDGETED ONE HOUR FOR A ~23-MINUTE MODEL LOAD PLUS AN
#   UNKNOWN PER-PROMPT COST, AND LEARNED NOTHING. It hit TIMEOUT at 01:00:15 with no artefact and
#   -- because stdout was unflushed and SIGKILL discards the buffer -- no record of how far it got.
#   This run exists to MEASURE the per-prompt cost, so it asks for 3 prompts and 4 hours: the load
#   dominates either way, and the script now prints a flushed heartbeat with s/prompt and writes
#   `timing.projected_full_population_min` into the artefact. Three prompts is enough to price the
#   design; twenty was enough to hide it.

# ⚠ --limit takes a CONTIGUOUS block of rows, and the bank is domain-clustered in file order, so
#   LIMIT=20 is 2 WHOLE DOMAINS, not 20 domains thinly (R35-C F7). That is fine for a smoke and
#   the artefact records `IS_SMOKE` and `limit_applied` so it cannot be mistaken for a full read.
python scripts/dcs_csi_rung2_celldecode.py \
  --bank data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl \
  --split validation \
  --exclude-prompt-ids runargs/dcs_cont/exclude_basket_bomb_sow_validation.txt \
  --bank-block cds_n4_sow --condition natural_doublespeak \
  --expect-n 230 --expect-domains 23 \
  --model "$MODEL" \
  --snapshot-glob "$MODEL" \
  --dtype bfloat16 \
  --answer-prefix "Answer:" \
  --band 6-14 \
  --heads 4,6,10,11,13,18,21,27 \
  --concept-ids 13054,33909 \
  --codeword-ids 14351,34217 \
  --limit "$LIMIT" \
  --out "$OUT"

echo "EXIT=$? $(date -Is)"
