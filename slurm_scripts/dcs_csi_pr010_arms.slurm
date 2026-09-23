#!/bin/bash
# PR-CSI-010, section 4: the 24-arm head-level causal family for ONE split, via W3.
# Takes SPLIT=train|validation. The argv is GENERATED FROM THE PREREGISTRATION so no arm's head list
# can drift from what was frozen (VOID condition 5).
#
# IDEMPOTENT: W3 skips any arm that already resolves to exactly one COMPLETE run. A preempted
# allocation therefore resumes rather than duplicating tags (S-104/S-127).
#SBATCH --job-name=csi_pr010arms
#SBATCH --output=outputs/boombness/logs/csi_pr010arms_%j.out
#SBATCH --error=outputs/boombness/logs/csi_pr010arms_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=geforce_rtx_3090:1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} $(date -Is)"
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader || true
# VOID 1: one GPU architecture. sm_86 is requested positively above; record what was granted.
[ -n "${CSI_GIT_BLOB:-}" ] || { echo "REFUSING: no CSI_GIT_BLOB exported by the submitter" >&2; exit 3; }
echo "BLOB ${CSI_GIT_BLOB}  PORCELAIN [${CSI_GIT_PORCELAIN:-<UNSET>}]"
[ "${CSI_GIT_PORCELAIN:-<UNSET>}" = "clean" ] || { echo "REFUSING: dirty worktree at submit" >&2; exit 4; }
: "${SPLIT:?REFUSING: SPLIT must be train or validation}"
case "$SPLIT" in
  train)      EXPECT=670 ;;
  validation) EXPECT=230 ;;
  *) echo "REFUSING: SPLIT=$SPLIT is neither train nor validation" >&2; exit 5 ;;
esac
# PREREG and TAG_PREFIX are parameters, defaulting to PR-CSI-010 so its behaviour is unchanged.
PREREG="${PREREG:-configs/dcs_csi_pr010_head_causal_basket.json}"
TAG_PREFIX="${TAG_PREFIX:-csi3_head_basket}"
FAMILY="${FAMILY:-pr010}"
echo "SPLIT=$SPLIT EXPECT_N=$EXPECT PREREG=$PREREG TAG_PREFIX=$TAG_PREFIX FAMILY=$FAMILY"

# ⛔ THE TAG PREFIX MUST MATCH THE PREREGISTRATION IT CAME FROM.
# S-227 fixed two preregs naming different head sets HD_RAND00; the same collision exists one level
# down in the TAGS. Writing PR-CSI-011's arms under csi3_head_basket_* would put two families'
# arms under one tag namespace, and strict_run_dir would then resolve a tag to two complete runs and
# refuse BOTH families -- or worse, admit the wrong one. The prereg's own id decides the prefix.
PR_ID=$(python -c "import json,sys; print(json.load(open('$PREREG'))['id'])")
case "$PR_ID" in
  PR-CSI-010) WANT_PREFIX=csi3_head_basket ;;
  PR-CSI-011) WANT_PREFIX=csi4_all32_basket ;;
  PR-CSI-012) WANT_PREFIX=csi5_census_basket ;;
  PR-CSI-013) WANT_PREFIX=csi6_btnhead_button ;;
  PR-CSI-014) WANT_PREFIX=csi7_cell_basket ;;
  PR-CSI-015) WANT_PREFIX=csi8_cell3_basket ;;
  *) echo "REFUSING: no tag prefix is registered for prereg id $PR_ID" >&2; exit 6 ;;
esac
if [ "$TAG_PREFIX" != "$WANT_PREFIX" ]; then
  echo "REFUSING: prereg $PR_ID requires TAG_PREFIX=$WANT_PREFIX but got $TAG_PREFIX -- two families" >&2
  echo "  must never share a tag namespace (S-104 at the family level, S-227 at the arm level)." >&2
  exit 7
fi

# 1. the argv, generated from the prereg, with every flag checked against the real CLI first
python scripts/gates/dcs_csi_pr010_argv.py --prereg "$PREREG" --split "$SPLIT" \
  --tag-prefix "$TAG_PREFIX" --check
A=/tmp/${FAMILY}_argv_${SPLIT}_${SLURM_JOB_ID}.txt
python scripts/gates/dcs_csi_pr010_argv.py --prereg "$PREREG" --split "$SPLIT" \
  --tag-prefix "$TAG_PREFIX" > "$A"
echo "argv lines: $(wc -l < "$A")"

# 2. the family, one model load for the whole allocation
python scripts/dcs_csi_arm_runner.py --argv-file "$A" --expect-n "$EXPECT" \
  --out outputs/boombness/dcs_csi/${FAMILY}_arms_${SPLIT}_${SLURM_JOB_ID}.json
echo "---- done rc=$? $(date -Is)"
