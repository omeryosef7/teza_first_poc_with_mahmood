#!/bin/bash
#SBATCH --job-name=ds_behwrite
#SBATCH --output=doublespeak_causality/logs/ds_behwrite_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_behwrite_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=10:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,t-806
#
# P10: behavioral necessity of the L8-11 MLP demo-codeword WRITE, run in BOTH phasings so the
# prefill-only/decode-safe difference is measurable inside one experiment:
#   baseline · write_abl_prefill · rand_pos_abl_prefill        (historical arms; ComponentOutSwap)
#   write_abl_decodesafe · rand_pos_abl_decodesafe             (DSDECODESAFE=1, the default)
#   write_abl_allpos                                           (DSALLPOS=1, opt-in upper bound)
# StrongReject-judged. n-801 excluded (pathologically slow weight loading).
# NOTE the walltime bump 06:00 -> 10:00: the default is now 5 generations/item, not 3.
#   sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSMAXNEW=220,DSN=0 slurm/run_behav_write.sh
#   smoke: sbatch --export=ALL,DSN=2 slurm/run_behav_write.sh
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs doublespeak_causality/outputs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"; export PYTHONUNBUFFERED=1
: "${DSBENCH:=doublespeak_causality/data/behavioral/beh_clearharm.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSMAXNEW:=220}"
: "${DSN:=0}"
: "${DSSPLITS:=train,test}"   # comma-list kept as a DEFAULT here (not via --export, which truncates)
: "${DSLAYERS:=8-11}"
: "${DSSEED:=0}"
: "${DSDECODESAFE:=1}"        # 1 = also run the decode-safe arms (P10 default); 0 = historical 3 arms
: "${DSALLPOS:=0}"            # 1 = add write_abl_allpos (AllPositionMLPAblate; strictly broader)
: "${DSSAVEGEN:=1}"           # 1 = write gens.jsonl (default); 0 = --no-save-gen
DSFLAGS=""
[ "$DSDECODESAFE" = "1" ] && DSFLAGS="$DSFLAGS --decode-safe" || DSFLAGS="$DSFLAGS --no-decode-safe"
[ "$DSALLPOS" = "1" ]     && DSFLAGS="$DSFLAGS --allpos-arm" || DSFLAGS="$DSFLAGS --no-allpos-arm"
[ "$DSSAVEGEN" = "1" ]    && DSFLAGS="$DSFLAGS --save-gen"   || DSFLAGS="$DSFLAGS --no-save-gen"
echo "=== behav write: $DSMODEL bench=$DSBENCH layers=$DSLAYERS maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS flags=$DSFLAGS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase_behav_write.py \
  --bench "$DSBENCH" --model "$DSMODEL" --max-new "$DSMAXNEW" --layers "$DSLAYERS" --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED" $DSFLAGS
echo "=== done ==="; date
