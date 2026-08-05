#!/bin/bash
#SBATCH --job-name=ds_refval
#SBATCH --output=doublespeak_causality/logs/ds_refval_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_refval_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,t-806
#
# P7 blocker (plan §5 P7 / §0.10): generation-validate EVERY per-layer refusal direction.
# outputs/refusal_alllayers/ ships 32 .pt files whose .json files carry NO 'validation' key -- only
# a tautological fit separation. Only L12/14/16/18/20 were ever generation-validated and L12 FAILED
# (induce_gain=-0.3333). This runs the bidirectional check (ablate + induce + norm-matched random
# controls) for all 32 layers, on the ClearHarm-native bench, for BOTH the shipped carrot/bomb-fit
# directions and a ClearHarm refit. outputs/refusal_alllayers/ is READ-ONLY here; refit vectors go
# into the new run dir.
#   sbatch slurm/run_refusal_validate.sh
#   sbatch --export=ALL,DSVALN=20,DSMAXNEW=64 slurm/run_refusal_validate.sh
#   sbatch --export=ALL,DSINDMODE=projsummary,DSPROJ=<...>/summary.json slurm/run_refusal_validate.sh
# n-801 excluded (pathologically slow weight loading). Comma-list values (DSFAMILIES, DSLAYERS) are
# DEFAULTS built inside this script -- NEVER pass them via --export, which truncates at the comma.
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
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSBENCH:=doublespeak_causality/data/behavioral/beh_clearharm.json}"
: "${DSREFDIR:=doublespeak_causality/outputs/refusal_alllayers}"
: "${DSFITSPLIT:=train}"
: "${DSEVALSPLIT:=test}"
: "${DSVALN:=20}"          # eval items per arm (0 = all of the eval split)
: "${DSMAXNEW:=64}"
: "${DSABLALPHA:=1.0}"     # full directional ablation (Arditi standard; phase_behav_refusal default)
: "${DSABLSCOPE:=all_layers}"
: "${DSINDSCOPE:=allpos}"  # matches pc.AllPositionAdd in phase_refusal_inject_calibrated.py
: "${DSINDMODE:=gap}"      # per-layer calibrated dose (resolves the alpha-norm confound)
: "${DSINDALPHA:=8.0}"     # only used when DSINDMODE=fixed
: "${DSPROJ:=}"            # phase_refusal_projection summary.json; only used when DSINDMODE=projsummary
: "${DSPROJSPLIT:=train}"
: "${DSSEED:=0}"
: "${DSDRYRUN:=0}"
: "${DSOUTDIR:=}"          # empty => the script mints outputs/refval_<cohort>_<ts>_<jobid>
# comma-lists kept as DEFAULTS here (never via --export, which truncates them)
: "${DSFAMILIES:=existing,clearharm}"
LAYERS="$(seq -s, 0 31)"   # 0,1,...,31 built INSIDE the script (never via --export)
: "${DSLAYERS:=$LAYERS}"
echo "=== refusal-direction validation: $DSMODEL bench=$DSBENCH families=$DSFAMILIES ==="
echo "    layers=$DSLAYERS n=$DSVALN maxnew=$DSMAXNEW abl(a=$DSABLALPHA,$DSABLSCOPE) ind($DSINDSCOPE,$DSINDMODE)"
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
EXTRA=""
[ "$DSDRYRUN" = "1" ] && EXTRA="--dry-run"
[ -n "$DSPROJ" ] && EXTRA="$EXTRA --proj-summary $DSPROJ --proj-split $DSPROJSPLIT"
[ -n "$DSOUTDIR" ] && EXTRA="$EXTRA --out-dir $DSOUTDIR"
if [ "$DSDRYRUN" != "1" ]; then
  GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
  case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
fi
python -u doublespeak_causality/scripts/validate_refusal_directions.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-dir "$DSREFDIR" \
  --layers "$DSLAYERS" --families "$DSFAMILIES" \
  --fit-split "$DSFITSPLIT" --eval-split "$DSEVALSPLIT" --val-n-items "$DSVALN" \
  --max-new "$DSMAXNEW" --ablate-alpha "$DSABLALPHA" --ablate-scope "$DSABLSCOPE" \
  --induce-scope "$DSINDSCOPE" --induce-alpha-mode "$DSINDMODE" --induce-alpha "$DSINDALPHA" \
  --seed "$DSSEED" $EXTRA
echo "=== done ==="; date
