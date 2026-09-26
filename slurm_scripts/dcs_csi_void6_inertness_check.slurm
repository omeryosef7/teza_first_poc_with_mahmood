#!/bin/bash
#SBATCH --job-name=csi_void6
#SBATCH --output=outputs/boombness/logs/csi_void6_%j.out
#SBATCH --error=outputs/boombness/logs/csi_void6_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=geforce_rtx_3090:1
# ================================================================================================
# PR-CSI-003-A VOID 6 INERTNESS CHECK (S-490). ONE ARM. NOT AN EXPERIMENT ARM.
#
# WHY. VOID 6 reads: "src/boombness/score_behavior.py modified between arms of the same
# comparison ... it would void the whole necessity experiment". MEASURED, not inferred: every one
# of the 14 completed necessity arms ran against score_behavior.py blob
#     e94258bd5fc44c70629e707b00504b7acac2a7b7
# (identical across all SEVEN commits those arms recorded in RUNMETA.json: ce116c6f, be0e6818,
# 9c94c149, ee61a767, e43944a4, 95f62711, 4907efe1), and HEAD is
#     9562bdf90b86fdb2fbbcf3a7b75967796b949b2d
# so VOID 6 FIRES for any new arm. The difference is DCS-CSI-291's `--knockout-cells` feature.
#
# STATICALLY the change is inert for a run that does not pass --knockout-cells: `_knock_cells` is
# set to None at :3186 and :3298, every new block is behind `if knock_cells:`, and both production
# call sites pass the new parameter BY KEYWORD, so inserting it between knock_heads and knock_scope
# cannot misbind. This job is the EMPIRICAL half, on the standard S-139 set for exactly this
# question ("Both proven INERT: 230 rows bit-identical across the blob change").
#
# WHAT IT DOES. Replays ONE already-completed arm -- KO_NEC_SHUF0, job 912736, node n-350, blob
# e94258bd -- from the argv its own RUNMETA.json recorded, changing ONLY the --tag. The comparison
# is then results.jsonl against results.jsonl, row for row.
#
# ⛔ THE TAG IS DELIBERATELY DISTINCT. Re-running under csi1_basket_train_KO_NEC_SHUF0 would create
#    a SECOND complete run dir for that tag, and strict_run_dir would then refuse the tag forever
#    -- breaking the necessity read. That is the twin hazard S-487 measured on
#    csi1_basket_train_BASE. VOID6CHK_ keeps this run out of every existing tag's namespace.
# ⛔ PINNED TO A 3090 (VOID 1). The p1 launcher uses --gpus=1; a bf16 comparison against an arm
#    that ran on n-350 must not land on a V100.
# ================================================================================================
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1

SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
# ---- NODE-LOCAL STAGING, COPIED VERBATIM FROM dcs_csi_p1_arms.slurm:55-96 (DCS-CSI-092/S-090).
# Duplicated rather than imported because that launcher is a frozen file under PR-CSI-003-A and
# this check must not touch it. The block SELF-VERIFIES: it size-checks every staged file against
# the source and refuses on any mismatch, so a bad copy cannot silently produce a wrong model.
if [ "${CSI_STAGE:-1}" = "1" ]; then
  LOCAL="/tmp/dcs_snap_${USER}/$(basename "$SNAP")"
  NEED_GB=20
  FREE_GB=$(df -BG --output=avail /tmp 2>/dev/null | tail -1 | tr -dc '0-9'); FREE_GB="${FREE_GB:-0}"
  if [ -d "$LOCAL" ]; then
    echo "[stage] REUSING existing $LOCAL (re-verified below)  $(date -Is)"
  elif [ "$FREE_GB" -lt "$NEED_GB" ]; then
    echo "[stage] REFUSING: /tmp on $(hostname) has ${FREE_GB}G free, need ${NEED_GB}G." >&2; exit 4
  else
    echo "[stage] $SNAP -> $LOCAL  (${FREE_GB}G free)  $(date -Is)"
  fi
  mkdir -p "$LOCAL"
  rsync -aL --exclude 'original/' --exclude '*.pth' "$SNAP"/ "$LOCAL"/
  BAD=0
  for f in "$SNAP"/*; do
    b=$(basename "$f"); [ -f "$f" ] || continue
    src=$(stat -Lc %s "$f"); dst=$(stat -Lc %s "$LOCAL/$b" 2>/dev/null || echo -1)
    if [ "$src" != "$dst" ]; then echo "[stage] SIZE MISMATCH $b src=$src dst=$dst" >&2; BAD=1; fi
  done
  [ "$BAD" = "0" ] || { echo "[stage] REFUSING: staged copy does not match source" >&2; exit 3; }
  echo "[stage] verified $(ls -1 "$LOCAL" | wc -l) files  $(date -Is)"
  SNAP="$LOCAL"
fi

echo "[void6] blob now: $(git hash-object src/boombness/score_behavior.py 2>/dev/null || echo '<no git on node>')"
echo "[void6] replaying KO_NEC_SHUF0 argv from RUNMETA, tag VOID6CHK  $(date -Is)"

python src/boombness/score_behavior.py \
  --bank data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl \
  --model "$SNAP" \
  --query-kinds semantic_one_word --conditions natural_doublespeak --n-examples 4 \
  --readout-ids whole_answer --readout-max-batch 1 \
  --exclude-prompt-ids runargs/dcs_cont/exclude_basket_bomb_sow_train.txt \
  --expect-n 670 --min-option-mass 0.05 --seed 20260913 \
  --dtype bfloat16 --attn-impl eager \
  --intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only \
  --rescue-positions query --rescue-layer 18 --rescue-donor ko \
  --rescue-basis configs/dcs_csi_axis_basket_behavioral_shuf24.pt \
  --rescue-basis-key ctrl_shuffled0 --rescue-norm-match-key cand_rank1 \
  --arm KO_NEC_SHUF0 --tag csi1_basket_train_VOID6CHK_KO_NEC_SHUF0

echo "[void6] done $(date -Is). Compare with:"
echo "  python3 scripts/gates/dcs_csi_void6_compare.py"
