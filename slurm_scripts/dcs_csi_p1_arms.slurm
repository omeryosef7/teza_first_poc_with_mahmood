#!/bin/bash
# PR-CSI-001 PRIMARY ARMS. Usage: sbatch dcs_csi_p1_arms.slurm <codeword> <axis.pt> <split> <group>
#   group A = the gates + the primary contrast + the rank-r candidate  (7 arms)
#   group B = the rank-1 control DISTRIBUTION: 4 shuffled + 6 random    (10 arms + 1 anchor)
#   group C = the RANK-5 matched control distribution for KO_PLS         (10 arms + 1 anchor)
#   group D = the POSITION ladder: full-state rescue at k of ~28 positions (7 arms)
#   group E = POSITION IDENTITY: full-state rescue at ONE named rel_end position (5 arms)
#   group F = LAYER control: BASE/KO/KO_FULL at a layer given by CSI_LAYER=<n> (P1-j)
#   group G = FINE SCAN of the span tail: rel -2,-3,-4,-5,-8 (5 arms)
#   group H = the CODEWORD ROW (rel -10) + accounting-gap positions (6 arms)
#   group I = EXTENDED control family to reach >=19 controls (24 arms)
#   group J = Phase 1 re-asked AT THE CODEWORD ROW: subspace rescue restricted to rel -10 (16 arms)
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
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1

CW="${1:?codeword}"; AXIS="${2:?axis .pt}"; SPLIT="${3:?train|validation}"; GROUP="${4:?A|B|C|D|E|F|G|H|I|J|K}"
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
# ---- OPTIONAL NODE-LOCAL STAGING (DCS-CSI-092, BLOCKER-S090) -------------------------------
# The n-30x rack's NFS path reads the shared snapshot at 2-7 MB/s (S-090, measured per node). A
# sequential copy at that rate is ~40 min for the 15 GB of weights; the HF loader's RANDOM mmap
# access over the same path is 20+ HOURS. Staging converts the pathological access pattern into one
# sequential copy, then loads from node-local disk (measured 7-12 GB/s, 171 G free).
# Off by default: it is a workaround for a broken rack, not the normal path. CSI_STAGE=1 enables it.
# `original/` is excluded -- it holds a .pth duplicate of the same weights (31 G on disk vs 15 G of
# safetensors) that transformers does not read.
if [ "${CSI_STAGE:-0}" = "1" ]; then
  LOCAL="/tmp/dcs_snap_${USER}/$(basename "$SNAP")"
  echo "[stage] $SNAP -> $LOCAL  $(date -Is)"
  mkdir -p "$LOCAL"
  # -L DEREFERENCES. Every file in an HF snapshot dir is a SYMLINK into ../../blobs/. Plain
  # `rsync -a` faithfully copies the symlinks, which then dangle because ../../blobs is not under
  # /tmp -- the first attempt (job 898564) staged 11 dangling links in 23 s and the size check
  # below refused it with dst=-1 on every file. See DCS-CSI-093.
  rsync -aL --exclude 'original/' --exclude '*.pth' "$SNAP"/ "$LOCAL"/
  # VERIFY, because a silently truncated weight file would produce a model that runs and is wrong.
  # rsync guarantees transfer fidelity by its own checksum; this re-checks SIZE against the source
  # for every file, which is the failure mode staging itself could introduce (full disk, killed copy).
  BAD=0
  for f in "$SNAP"/*; do
    b=$(basename "$f"); [ -f "$f" ] || continue
    src=$(stat -Lc %s "$f"); dst=$(stat -Lc %s "$LOCAL/$b" 2>/dev/null || echo -1)
    if [ "$src" != "$dst" ]; then echo "[stage] SIZE MISMATCH $b src=$src dst=$dst" >&2; BAD=1; fi
  done
  if [ "$BAD" != "0" ]; then echo "[stage] REFUSING: staged copy does not match source" >&2; exit 3; fi
  echo "[stage] index sha256: $(sha256sum "$LOCAL/model.safetensors.index.json" | cut -c1-32)"
  echo "[stage] verified $(ls -1 "$LOCAL" | wc -l) files, $(du -sh "$LOCAL" | cut -f1)  $(date -Is)"
  SNAP="$LOCAL"
fi
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
# LAYER OVERRIDE IS AN ENV VAR, NOT $5 (DCS-CSI-076). It was $5, and group I later took $5 as its
# half-selector -- so `... train I 1` silently meant "layer 1", and two basket control jobs ran at
# L1/L2 instead of L18. A positional argument that means different things in different groups is
# the bug; a named variable cannot collide with a group's own sub-selector.
LAYER="${CSI_LAYER:-}"
if [ -n "${5:-}" ] && [ "$GROUP" != "I" ]; then
  echo "REFUSING: \$5 is a GROUP-SPECIFIC sub-selector (only group I uses it). To override the "\
       "layer, set CSI_LAYER=<n> in the environment. See DCS-CSI-076." >&2
  exit 2
fi
if [ -z "$LAYER" ]; then
  LAYER=$(python -c "import json;print(json.load(open('${AXIS%.pt}.json'))['selected_layer'])")
else
  # LAYER OVERRIDE (DCS-CSI-063 / P1-j). Basket's rescue ran at L18 and button's at L20 -- each
  # codeword's own TRAIN-selected layer -- so the 53% vs 34% recovery gap is confounded between
  # CODEWORD and LAYER. Running one codeword at the other's layer separates them. Only the
  # whole-state arms are meaningful under an override: a subspace basis fit at one layer must not
  # be written at another (review M2 refuses that), so group A's subspace arms will refuse and
  # that is correct.
  echo "[layer-override] using L$LAYER instead of the axis artifact's selected layer"
fi
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
elif [ "$GROUP" = "J" ]; then
  # GROUP J -- PHASE 1 ASKED AT THE RIGHT PLACE (DCS-CSI-075). Phase 1 restored a low-dimensional
  # component across ALL 28 positions, of a direction fit at an offset the causal map later showed
  # carries 1% of the effect. This asks the same question at the CODEWORD ROW (rel -10), which
  # carries 46.6%: restore only the axis component OF THAT ROW. The benchmark is KO_AT10 = +0.03289,
  # the full state at the same row, so candidate and positive control differ only in the projection.
  # The basis is fit at behavioural cw_query and FORCED to L20 to match the causal evidence (S-073).
  CWR="--rescue-rel-end-rows -10"
  echo ">>> KO_CW_FULL $(date -Is)"
  $SB $COMMON $KO $R $CWR --arm KO_CW_FULL --tag ${P}_KO_CW_FULL
  subcw () { local arm="$1" key="$2" nm="${3:-}"
    echo ">>> $arm $(date -Is)"
    if [ -z "$nm" ]; then
      $SB $COMMON $KO $R $CWR --rescue-basis "$AXIS" --rescue-basis-key "$key" --arm "$arm" --tag "${P}_${arm}"
    else
      $SB $COMMON $KO $R $CWR --rescue-basis "$AXIS" --rescue-basis-key "$key"           --rescue-norm-match-key "$nm" --arm "$arm" --tag "${P}_${arm}"
    fi; }
  subcw KO_CW_AXIS cand_rank1
  subcw KO_CW_PLS  "cand_pls${RANK}"
  for i in 0 1 2 3 4 5 6 7; do subcw "KO_CW_RAND${i}" "ctrl_random${i}"   cand_rank1; done
  for j in 0 1 2 3 4;       do subcw "KO_CW_SHUF${j}" "ctrl_shuffled${j}" cand_rank1; done
elif [ "$GROUP" = "X" ]; then
  # GROUP X -- RESUME a specific list of arms (DCS-CSI-084). A node fault or a cancellation leaves a
  # handful of arms missing out of a group of twelve; re-running the whole group would re-spend GPU
  # on arms that already hold complete, verified rows. CSI_ARMS names exactly the arms to run, as
  # SPACE-separated "ARM:basis_key" pairs -- space, not comma, because a comma-bearing value is the
  # sbatch --export truncation hazard this repo has been bitten by before, and a space-separated
  # value survives --export=ALL intact. CSI_RELROWS optionally supplies --rescue-rel-end-rows so the
  # codeword-row arms of group J can be resumed by the same path.
  : "${CSI_ARMS:?group X requires CSI_ARMS=\"ARM:key ARM:key ...\" (space-separated)}"
  RR=""; [ -n "${CSI_RELROWS:-}" ] && RR="--rescue-rel-end-rows ${CSI_RELROWS}"
  for spec in $CSI_ARMS; do
    arm="${spec%%:*}"; key="${spec#*:}"
    if [ "$arm" = "$spec" ] || [ -z "$key" ]; then
      echo "REFUSING: CSI_ARMS entry '$spec' is not ARM:key" >&2; exit 2
    fi
    echo ">>> $arm $(date -Is)"
    $SB $COMMON $KO $R $RR --rescue-basis "$AXIS" --rescue-basis-key "$key" \
        --rescue-norm-match-key cand_rank1 --arm "$arm" --tag "${P}_${arm}"
  done
elif [ "$GROUP" = "K" ]; then
  # GROUP K -- TWELVE MORE SHUFFLED-LABEL CONTROLS (review R5). R5 tested whether the 22 random and
  # 12 shuffled controls form one exchangeable null and found they do IN LOCATION (exact two-sample
  # permutation p=0.714) -- but the shuffled family's sd is 1.9x the random family's at the same
  # mean. Fitting capacity on permuted labels buys VARIANCE, not recovery, so the controls that come
  # closest to the candidate are all shuffled (top three of 34) and the SHUFFLED TAIL is what sets
  # the margin. Adding more RANDOM draws would lower the pooled rank-p floor while sampling the wrong
  # tail -- a p-value that improves without the test getting harder. These twelve make the binding
  # subfamily certifiable on its own: shuffled-only rank floor 1/13 = 0.0769 -> 1/25 = 0.0400.
  # REQUIRES the shuf24 axis file, whose 41 pre-existing bases -- cand_rank1 and all 22 randoms
  # included -- were verified BIT-IDENTICAL to the frozen file before this group was written, so the
  # norm-match reference is unchanged and these controls are comparable to the 34 already run.
  for j in 12 13 14 15 16 17 18 19 20 21 22 23; do sub "KO_SHUF${j}" "ctrl_shuffled${j}" cand_rank1; done
elif [ "$GROUP" = "I" ]; then
  # GROUP I -- EXTENDED control family (DCS-CSI-072). S-071 left basket INCONCLUSIVE: the candidate
  # is strictly the largest of its 10 controls, but 1/(10+1) = 0.0909 is above 0.05, so rank 1 is
  # the best attainable outcome and still cannot certify. The verdict named its own remedy -- >=19
  # controls -- and these are the extra arms. Same norm-matching, same layer, same positions; only
  # the number of draws changes.
  # Split into halves ($5 = 1|2; group I is the ONLY group that reads $5 -- see DCS-CSI-076). A 24-arm / 12 h request pended 60 min on (Resources) and broke
  # the 30-minute rule; two 12-arm / 6 h requests schedule. Per S-045 a readout endpoint needs the
  # arms to share an ARCHITECTURE, not an allocation -- the anchor measured zero allocation drift --
  # so splitting costs nothing scientifically.
  if [ "${5:-1}" = "1" ]; then
    for i in 6 7 8 9 10 11; do sub "KO_RAND${i}" "ctrl_random${i}" cand_rank1; done
    for j in 4 5 6 7 8 9;    do sub "KO_SHUF${j}" "ctrl_shuffled${j}" cand_rank1; done
  else
    for i in 12 13 14 15 16 17 18 19 20 21; do sub "KO_RAND${i}" "ctrl_random${i}" cand_rank1; done
    for j in 10 11;                          do sub "KO_SHUF${j}" "ctrl_shuffled${j}" cand_rank1; done
  fi
elif [ "$GROUP" = "H" ]; then
  # GROUP H -- the CODEWORD ROW, correctly located, plus positions to close the accounting gap
  # (DCS-CSI-068). Two problems group G exposed:
  #   (1) rel -10 is the codeword, NOT rel -11. score_behavior resolves idx = len(span) + rel_end,
  #       and the codeword sits at span index 18 of 28 -> rel_end -10, measured on all 670 rows.
  #       S-066's "cw_query" arm tested rel -11, the token BEFORE the codeword.
  #   (2) the nine positions measured so far sum to 35.7% of the whole-state effect, so most of it
  #       is still unaccounted for; these sample the unmeasured stretch.
  for RE in -10 -7 -9 -12 -15 -25; do
    NAME="KO_AT$(echo $RE | tr -d '-')"
    echo ">>> ${NAME} (rel_end ${RE}) $(date -Is)"
    $SB $COMMON $KO $R --rescue-rel-end-rows "$RE" --arm "$NAME" --tag "${P}_${NAME}"
  done
elif [ "$GROUP" = "G" ]; then
  # GROUP G -- FINE SCAN of the span's tail (DCS-CSI-066). Group E found rel-1 carrying 6.1x a
  # random position while rel-6, -11, -20, -28 carry ~nothing, so the effect is concentrated near
  # the END of the query span rather than spread over it. This maps the concentration at
  # single-position resolution over the last stretch.
  for RE in -2 -3 -4 -5 -8; do
    NAME="KO_AT$(echo $RE | tr -d '-')"
    echo ">>> ${NAME} (rel_end ${RE}) $(date -Is)"
    $SB $COMMON $KO $R --rescue-rel-end-rows "$RE" --arm "$NAME" --tag "${P}_${NAME}"
  done
elif [ "$GROUP" = "F" ]; then
  # GROUP F -- the LAYER control (P1-j). Whole-state arms only: BASE and KO are layer-independent,
  # and KO_FULL is the quantity whose recovery fraction we are trying to attribute.
  echo ">>> BASE $(date -Is)";    $SB $COMMON                    --arm BASE    --tag ${P}_L${LAYER}_BASE
  echo ">>> KO $(date -Is)";      $SB $COMMON $KO                --arm KO      --tag ${P}_L${LAYER}_KO
  echo ">>> KO_FULL $(date -Is)"; $SB $COMMON $KO $R             --arm KO_FULL --tag ${P}_L${LAYER}_KO_FULL
elif [ "$GROUP" = "E" ]; then
  # GROUP E -- POSITION IDENTITY (DCS-CSI-060). The ladder (group D) draws RANDOM subsets, so it
  # measures a position's AVERAGE contribution and found recovery linear in k (R^2 0.997). It
  # cannot say whether particular positions differ. Each arm here restores the full clean state at
  # exactly ONE named position, by rel_end within the query span (-1 = last token). If the span is
  # uniform every arm should land near the ladder's k=1 value (+0.00281); a position that carries
  # more would show up as a clear outlier. rel-6 is the site the AXIS was fit at and rel-11 is
  # cw_query, the codeword row the knockout actually edits -- the two positions with a prior reason
  # to be special.
  for RE in -1 -6 -11 -20 -28; do
    NAME="KO_AT$(echo $RE | tr -d '-')"
    echo ">>> ${NAME} (rel_end ${RE}) $(date -Is)"
    $SB $COMMON $KO $R --rescue-rel-end-rows "$RE" --arm "$NAME" --tag "${P}_${NAME}"
  done
elif [ "$GROUP" = "D" ]; then
  # GROUP D -- the POSITION ladder (DCS-CSI-051). Phase 1's result is that recovery tracks HOW MUCH
  # of the state is restored rather than WHICH directions. The dimension ladder said that for
  # directions; this says it for POSITIONS. Each arm restores the FULL clean state at a
  # seeded-random subset of k of the ~28 query-span positions, so the only thing varying is how
  # many positions are restored. If recovery scales smoothly with k the effect is distributed over
  # the span too; if a few positions carry it, that is localisation and a real finding.
  # --rescue-n-positions is the existing size-match mechanism (seeded by prompt_id, refuses a row
  # that cannot supply k), so no new code is involved.
  for K in 1 2 4 8 14 20 28; do
    echo ">>> KO_POS${K} $(date -Is)"
    $SB $COMMON $KO $R --rescue-n-positions "$K" --arm "KO_POS${K}" --tag "${P}_KO_POS${K}"
  done
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
