#!/bin/bash
# PR-CSI-001 SMOKE. Six arms, few rows, ONE allocation -- the intervention-liveness test that
# must pass before the full 15-arm spend.
#
# WHAT IT IS ACTUALLY TESTING, and why it is not optional. The whole-state rescue has only ever
# been run on BEHAVIOURAL prompts. Phase 1 runs it on `semantic_one_word` prompts, where the
# query span is a different shape, and `score_behavior`'s rescue block FAILS THE ROW if the query
# span resolves empty (`ledger.fail("rescue:no_query_positions")`). A run in which every row
# failed that way still produces a DONE.json. So this smoke checks, on real rows:
#   1. the knockout is live on semantic prompts (prefill edits > 0, decode edits == 0);
#   2. the query span is non-empty, so the rescue has positions to write;
#   3. KO_SELF is INERT -- writing a run's own activations back must reproduce it exactly;
#   4. the rank-1 axis arm writes a NONZERO delta (a subspace rescue that writes ~0 is
#      indistinguishable from one that never fired);
#   5. the norm-matched control writes the SAME norm as the candidate, per row, with zero
#      norm-match-degenerate positions.
#
# Commands are INLINE (sbatch --export truncates at commas). Layer and rank come from the axis
# artifact, never hardcoded, so the smoke cannot silently test a different layer than the fit.
#
#SBATCH --job-name=csi_p1sm
#SBATCH --output=outputs/boombness/logs/csi_p1sm_%j.out
#SBATCH --error=outputs/boombness/logs/csi_p1sm_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1          # otherwise progress is invisible until the process exits

CW="${1:?usage: sbatch dcs_csi_p1_smoke.slurm <codeword> <axis.pt>}"
AXIS="${2:?need the axis .pt}"
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
BANK="data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl"
EXCL="runargs/dcs_cont/exclude_${CW}_bomb_sow_train.txt"

# Layer and the TRAIN-selected PLS rank come FROM THE ARTIFACT.
LAYER=$(python -c "import json;print(json.load(open('${AXIS%.pt}.json'))['selected_layer'])")
RANK=$(python -c "import json;d=json.load(open('${AXIS%.pt}.json'));print(d.get('selected_rank',1))")
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} CW=$CW LAYER=$LAYER RANK=$RANK $(date -Is)"
nvidia-smi --query-gpu=name --format=csv,noheader || true

COMMON="--bank $BANK --model $SNAP --query-kinds semantic_one_word \
--conditions natural_doublespeak --n-examples 4 --readout-ids whole_answer --readout-max-batch 1 \
--exclude-prompt-ids $EXCL --limit 24 --min-option-mass 0.05 --seed 20260913 \
--dtype bfloat16 --attn-impl eager"
KO="--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only"
RESC="--rescue-positions query --rescue-layer $LAYER"

run () { echo ">>> $1 $(date -Is)"; shift; python src/boombness/score_behavior.py "$@"; }

run BASE     $COMMON                                     --arm BASE     --tag csi1sm_${CW}_BASE
run KO       $COMMON $KO                                 --arm KO       --tag csi1sm_${CW}_KO
run KO_SELF  $COMMON $KO $RESC --rescue-donor self       --arm KO_SELF  --tag csi1sm_${CW}_KO_SELF
run KO_FULL  $COMMON $KO $RESC --rescue-donor clean      --arm KO_FULL  --tag csi1sm_${CW}_KO_FULL
run KO_AXIS  $COMMON $KO $RESC --rescue-donor clean \
     --rescue-basis "$AXIS" --rescue-basis-key cand_rank1 \
     --arm KO_AXIS  --tag csi1sm_${CW}_KO_AXIS
run KO_ORTH  $COMMON $KO $RESC --rescue-donor clean \
     --rescue-basis "$AXIS" --rescue-basis-key ctrl_orth --rescue-norm-match-key cand_rank1 \
     --arm KO_ORTH  --tag csi1sm_${CW}_KO_ORTH

echo "---- SMOKE ARMS DONE rc=$? $(date -Is) HOST=$(hostname)"
