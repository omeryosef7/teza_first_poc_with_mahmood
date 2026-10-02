#!/bin/bash
# HERETIC-CSI P2a: fit the rank-sweep candidate + rank-matched control bases for one codeword.
# CPU-only (PLS on pre-extracted clean reps); NO GPU. Reuses scripts/dcs_csi_axis.py unchanged.
#
# Emits ONE axis .pt with: cand_rank1, cand_pls{2..MAXRANK}, and for each rank in RANK_CONTROLS the
# matched controls ctrl_random_r{r}_{i} (N_RANDOM) + ctrl_shuffled_pls{r}_{j} (N_SHUF). These are the
# arms the P2a rescue sweep then scores against each candidate at its own rank.
#
#SBATCH --job-name=hcsi_axisfit
#SBATCH --output=outputs/heretic_csi/logs/axisfit_%j.out
#SBATCH --error=outputs/heretic_csi/logs/axisfit_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1
mkdir -p outputs/heretic_csi/logs configs/heretic_csi

CW="${1:?usage: sbatch axisfit_ranksweep.slurm <basket|button>}"
case "$CW" in
  basket)
    CORPUS=outputs/boombness/extract_boombness/cont1_behavioral_basket_bomb_20260910_113902_3966018
    READOUT=outputs/boombness/score_behavior/ts116m_readout_basket_bomb_20260907_152329_3191150 ;;
  button)
    CORPUS=outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_20260910_152806_272296
    READOUT=outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103 ;;
  *) echo "unknown codeword $CW"; exit 2 ;;
esac

OUT=configs/heretic_csi/hcsi_ranksweep_${CW}.pt
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} CW=$CW $(date -Is)"
echo "CORPUS=$CORPUS"
echo "READOUT=$READOUT"

# force-layer 18 = the dissociation layer (comparability with the inherited rank-1 PASS/NEGATIVE).
# max-rank 32 => candidates cand_pls2..32; rank-controls at the swept ranks with a 46-random family
# (matches the hardened n46 rank test) + 10 shuffled-label PLS controls per rank.
python scripts/dcs_csi_axis.py \
  --codeword "$CW" --corpus "$CORPUS" --readout "$READOUT" \
  --fit-prompt behavioral --site rel-6 --force-layer 18 \
  --max-rank 32 --rank-controls 1,2,4,8,16,32 \
  --n-random-rank 46 --n-shuffled-rank 10 \
  --seed 20260915 --out "$OUT"

echo "---- AXISFIT DONE rc=$? CW=$CW OUT=$OUT $(date -Is)"
python - "$OUT" <<'PY'
import sys, torch, json
o = torch.load(sys.argv[1], map_location="cpu", weights_only=False)
ks = list(o["bases"].keys())
cand = sorted(k for k in ks if k.startswith("cand"))
print("DONE_MARKER n_bases=%d n_cand=%d" % (len(ks), len(cand)))
print("candidates:", cand[:10], "..." if len(cand) > 10 else "")
PY
