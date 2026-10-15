#!/bin/bash
# HERETIC-CSI P6: rank-1/4/16 candidates + rank-matched control families for ONE new codeword (CPU).
# Same dcs_csi_axis.py recipe as axisfit_ranksweep.slurm (fit-prompt behavioral, site rel-6, force-layer 18,
# 46 random + 10 shuffled controls per rank, seed 20260915), with ranks limited to {1,4,16} (P6 DEV curve) and
# CORPUS/READOUT read from the Stage-0 manifest (no hard-coded paths).
#SBATCH --job-name=hcsi_p6axis
#SBATCH --output=outputs/heretic_csi/logs/p6axis_%j.out
#SBATCH --error=outputs/heretic_csi/logs/p6axis_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --no-requeue
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1
CW="${1:?usage: sbatch p6_axisfit.slurm <codeword> [--dry-run]}"
DRY="${2:-}"
MAN=outputs/heretic_csi/p6/stage0_${CW}.json
OUT=/specific/scratches/scratch/omeryosef/hcsi_p6/axes/hcsi_p6_axis_${CW}.pt
mkdir -p "$(dirname "$OUT")"
if [ "$DRY" == "--dry-run" ] && [ ! -s "$MAN" ]; then
  echo "DRY (no manifest yet): python scripts/dcs_csi_axis.py --codeword $CW --corpus <stage0.extract_dir> --readout <stage0.readout_dir> --fit-prompt behavioral --site rel-6 --force-layer 18 --max-rank 16 --rank-controls 1,4,16 --n-random-rank 46 --n-shuffled-rank 10 --seed 20260915 --out $OUT"
  echo "DRY_OK $CW"; exit 0
fi
[ -s "$MAN" ] || { echo "MISSING stage0 manifest $MAN"; exit 2; }
CORPUS=$(python -c "import json;print(json.load(open('$MAN'))['extract_dir'])")
READOUT=$(python -c "import json;print(json.load(open('$MAN'))['readout_dir'])")
RJ=$(python -c "import json;m=json.load(open('$MAN'));print(m.get('readout_slurm_job') or m['slurm_job'])")
XJ=$(python -c "import json;m=json.load(open('$MAN'));print(m.get('extract_slurm_job') or m['slurm_job'])")
ST=$(python -c "import json;print(json.load(open('$MAN')).get('status'))")
[ "$ST" == "G3_PASS" ] || { echo "REFUSING: stage0 status=$ST (only G3_PASS codewords get an axis fit)"; exit 3; }
# each dir must belong to ITS recorded Stage-0 job and be DONE (no stale/preempted partial dirs; readout may be reused
# from an earlier job while extraction ran in a later one)
python research/heretic_csi/p6_select_run.py --job "$RJ" --verify "$READOUT" || { echo "READOUT dir not from job $RJ or not DONE"; exit 3; }
python research/heretic_csi/p6_select_run.py --job "$XJ" --verify "$CORPUS" || { echo "CORPUS dir not from job $XJ or not DONE"; exit 3; }
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} CW=$CW CORPUS=$CORPUS READOUT=$READOUT $(date -Is)"
python scripts/dcs_csi_axis.py --codeword "$CW" --corpus "$CORPUS" --readout "$READOUT" \
  --fit-prompt behavioral --site rel-6 --force-layer 18 --max-rank 16 --rank-controls 1,4,16 \
  --n-random-rank 46 --n-shuffled-rank 10 --seed 20260915 --out "$OUT"
SHA=$(sha256sum "$OUT" | cut -d' ' -f1); echo "$SHA  $OUT"
# record the axis basis + its sha256 in the Stage-0 manifest (review #7 item 4)
python - "$MAN" "$OUT" "$SHA" <<'PY'
import json, os, sys
man, out, sha = sys.argv[1:]
m = json.load(open(man))
m["axis"] = {"path": out, "sha256": sha, "axisfit_job": os.environ.get("SLURM_JOB_ID"),
             "recipe": "dcs_csi_axis.py --fit-prompt behavioral --site rel-6 --force-layer 18 --max-rank 16 --rank-controls 1,4,16 --n-random-rank 46 --n-shuffled-rank 10 --seed 20260915"}
json.dump(m, open(man, "w"), indent=1)
PY
echo "DONE_MARKER p6_axisfit cw=$CW out=$OUT sha256=$SHA rc=0 $(date -Is)"
