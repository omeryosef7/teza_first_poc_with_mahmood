#!/bin/bash
# PR-CSI-001 PRIMARY ARMS. Usage: sbatch dcs_csi_p1_arms.slurm <codeword> <axis.pt> <split> <group>
#   group A = the gates + the primary contrast + the rank-r candidate  (7 arms)
#   group B = the rank-1 control DISTRIBUTION: 4 shuffled + 6 random    (10 arms + 1 anchor)
#   group C = the RANK-5 matched control distribution for KO_PLS         (10 arms + 1 anchor)
#
# WHY TWO GROUPS AND WHY KO_AXIS APPEARS IN BOTH. At ~29 min per 670-row readout arm, 17 arms do
# not fit one allocation. The split is chosen so that everything the PREREGISTERED PRIMARY
# CONTRAST depends on -- BASE, KO, KO_SELF, KO_FULL, KO_AXIS, KO_ORTH -- runs in ONE allocation on
# ONE node, so the headline is hardware-internal by construction. Group B then compares the
# candidate to the control family ACROSS allocations, so KO_AXIS is re-run inside group B as an
# ANCHOR: the A-vs-B difference on that identical arm MEASURES the cross-allocation drift instead
# of leaving it as an assumption. (Readout endpoints have been far more hardware-stable than
# generation in this project, but "more stable" is not "measured".)
#
# Everything is INLINE (sbatch --export truncates at commas). Layer and rank come from the axis
# artifact, never hardcoded.
#
#SBATCH --job-name=csi_p1
#SBATCH --output=outputs/boombness/logs/csi_p1_%j.out
#SBATCH --error=outputs/boombness/logs/csi_p1_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1

CW="${1:?codeword}"; AXIS="${2:?axis .pt}"; SPLIT="${3:?train|validation}"; GROUP="${4:?A|B}"
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
BANK="data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl"
EXCL="runargs/dcs_cont/exclude_${CW}_bomb_sow_${SPLIT}.txt"
[ -f "$EXCL" ] || { echo "no exclusion file $EXCL"; exit 2; }
NKEEP=$(python -c "
import json,sys
bank='$BANK'; ex={l.strip() for l in open('$EXCL') if l.strip() and not l.startswith('#')}
n=0
for l in open(bank):
    r=json.loads(l)
    if (r.get('query_kind')=='semantic_one_word' and r.get('bank_block')=='cds_n4_sow'
        and r.get('condition')=='natural_doublespeak' and r['prompt_id'] not in ex): n+=1
print(n)")
LAYER=$(python -c "import json;print(json.load(open('${AXIS%.pt}.json'))['selected_layer'])")
RANK=$(python -c "import json;d=json.load(open('${AXIS%.pt}.json'));print(d.get('selected_rank',1))")
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} CW=$CW SPLIT=$SPLIT GROUP=$GROUP LAYER=$LAYER RANK=$RANK EXPECT_N=$NKEEP $(date -Is)"
nvidia-smi --query-gpu=name --format=csv,noheader || true

P="csi1_${CW}_${SPLIT}"
COMMON="--bank $BANK --model $SNAP --query-kinds semantic_one_word \
--conditions natural_doublespeak --n-examples 4 --readout-ids whole_answer --readout-max-batch 1 \
--exclude-prompt-ids $EXCL --expect-n $NKEEP --min-option-mass 0.05 --seed 20260913 \
--dtype bfloat16 --attn-impl eager"
KO="--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only"
R="--rescue-positions query --rescue-layer $LAYER --rescue-donor clean"
SB="python src/boombness/score_behavior.py"

sub () {  # sub <arm> <basis-key> [norm-match-key]
  local arm="$1" key="$2" nm="${3:-}"
  echo ">>> $arm $(date -Is)"
  if [ -z "$nm" ]; then
    $SB $COMMON $KO $R --rescue-basis "$AXIS" --rescue-basis-key "$key" --arm "$arm" --tag "${P}_${arm}"
  else
    $SB $COMMON $KO $R --rescue-basis "$AXIS" --rescue-basis-key "$key" \
        --rescue-norm-match-key "$nm" --arm "$arm" --tag "${P}_${arm}"
  fi
}

if [ "$GROUP" = "A" ]; then
  echo ">>> BASE $(date -Is)";    $SB $COMMON                         --arm BASE    --tag ${P}_BASE
  echo ">>> KO $(date -Is)";      $SB $COMMON $KO                     --arm KO      --tag ${P}_KO
  echo ">>> KO_SELF $(date -Is)"; $SB $COMMON $KO --rescue-positions query --rescue-layer $LAYER \
                                     --rescue-donor self              --arm KO_SELF --tag ${P}_KO_SELF
  echo ">>> KO_FULL $(date -Is)"; $SB $COMMON $KO $R                  --arm KO_FULL --tag ${P}_KO_FULL
  sub KO_AXIS cand_rank1
  sub KO_PLS  "cand_pls${RANK}"
  sub KO_ORTH ctrl_orth cand_rank1
elif [ "$GROUP" = "B" ]; then
  sub KO_AXIS_ANCHOR cand_rank1
  for j in 0 1 2 3;       do sub "KO_SHUF${j}" "ctrl_shuffled${j}" cand_rank1; done
  for i in 0 1 2 3 4 5;   do sub "KO_RAND${i}" "ctrl_random${i}"   cand_rank1; done
else
  # GROUP C -- the RANK-MATCHED control distribution for the rank-r candidate (DCS-CSI-048).
  # Group B's controls are all rank 1, so KO_PLS (rank 5) had nothing to be compared against at its
  # own rank and its advantage over the rank-1 axis was confounded with DOSE: a rank-r subspace
  # captures ~sqrt(r/d) of any vector before any information enters it. Every arm here is rank 5 and
  # norm-matched to cand_pls5, so the only thing that varies is WHICH five directions.
  sub KO_PLS_ANCHOR "cand_pls${RANK}"
  for i in 0 1 2 3 4 5; do sub "KO_R5RAND${i}" "ctrl_random_r${RANK}_${i}"    "cand_pls${RANK}"; done
  for j in 0 1 2 3;     do sub "KO_R5SHUF${j}" "ctrl_shuffled_pls${RANK}_${j}" "cand_pls${RANK}"; done
fi
echo "---- GROUP $GROUP DONE rc=$? $(date -Is) HOST=$(hostname)"
