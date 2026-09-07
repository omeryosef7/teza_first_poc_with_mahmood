#!/bin/bash
#SBATCH --job-name=tsanal
#SBATCH --output=outputs/boombness/logs/tsanal_%j.out
#SBATCH --error=outputs/boombness/logs/tsanal_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
# DCS thesis-scale CONFIRMATORY ANALYSIS. CPU only -- the representations already exist, so
# nothing here touches a GPU, and taking a GPU slot for a scikit-learn job would be waste in a
# queue where fair-share is already depleted.
#
# WHY SLURM AND NOT THE LOGIN NODE. This is ~1 hour of saturated multi-core compute: 10,000
# permutation draws, parallelised. Mandate 26.17 -- no long inference on the login node -- and the
# practical reason behind it: a login-node run competes with every other user, and a run that is
# killed halfway through is a run whose test split has been read for nothing.
#
# --cpus-per-task=16 because the permutation is embarrassingly parallel and joblib takes n_jobs=-1.
# --mem=64G because six rep caches at ~1.65 GB each are loaded, plus float32 copies for sklearn.
#
# OMP_NUM_THREADS is PINNED. A-031 DECISION 1 records that se_mcnemar is BLAS-thread-dependent and
# that OMP_NUM_THREADS=4 is a binding reproduction constant elsewhere in this project. Here the
# concern is different but real: leaving BLAS free to pick a thread count makes the numerics depend
# on how busy the node was, so two runs of the same frozen analyzer could disagree in the last
# digits. Pinned to 1 per worker, with parallelism taken at the joblib level instead -- one place
# to reason about, and it is the place the speedup actually comes from.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTHONUNBUFFERED=1

: "${TSA_PREREG:?TSA_PREREG not set}"
: "${TSA_TAG_PREFIX:=ts116m_full}"
: "${TSA_OUT:=}"
: "${TSA_EXTRA:=}"

# Echo the resolved plan first, so `head` on the log answers "did this run what I meant?" without
# reasoning about env plumbing -- the DCS-C-047 lesson.
echo "=== ts_analysis ==="; date; hostname
echo "script:  scripts/dcs_ts_pr048_analysis.py"
echo "prereg:  $TSA_PREREG"
echo "tag:     $TSA_TAG_PREFIX"
echo "out:     ${TSA_OUT:-<derived from prereg id>}"
echo "extra:   ${TSA_EXTRA:-<none>}"
echo "threads: OMP=$OMP_NUM_THREADS cpus=${SLURM_CPUS_PER_TASK:-?}"
echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"

# shellcheck disable=SC2086
python -u scripts/dcs_ts_pr048_analysis.py \
  --prereg "$TSA_PREREG" \
  --reps outputs/boombness/extract_boombness \
  --tag-prefix "$TSA_TAG_PREFIX" \
  ${TSA_OUT:+--out "$TSA_OUT"} \
  $TSA_EXTRA
echo "=== done ==="; date
