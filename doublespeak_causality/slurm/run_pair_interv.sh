#!/bin/bash
#SBATCH --job-name=ds_pairinterv
#SBATCH --output=doublespeak_causality/logs/ds_pairinterv_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_pairinterv_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# CAUSAL_CORE_PLAN §4/§5 (S5/S6/S7): fixed-pair intervention sweeps.
#
# COMMA SAFETY: sbatch --export SILENTLY TRUNCATES comma-list values, so list-valued
# knobs are passed COLON-separated (DSALPHAS="-2:-1:1:2", DSLAYERS="10:14:18") and
# translated to commas here. Every var is still comma-guarded below.
#   sbatch --export=ALL,DSMODE=layer_scan,DSALPHAS=1.0:2.0,DSREPS=<dir>,DSDIRS=<dir> run_pair_interv.sh
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
: "${DSBENCH:=doublespeak_causality/data/pair_benchmark/pair_carrot_bomb.json}"
: "${DSREPS:?DSREPS (reps dir) is required}"
: "${DSDIRS:?DSDIRS (directions dir) is required}"
: "${DSMODE:=layer_scan}"
: "${DSREADOUT:=cloze}"
: "${DSSITE:=codeword_last}"
: "${DSALPHAS:=1.0}"      # colon-separated
: "${DSLAYERS:=}"         # colon-separated; empty => all layers
: "${DSWINS:=}"           # colon-separated window names (replace mode)
: "${DSNPROMPTS:=20}"
: "${DSSPLITS:=dev:heldout}"
: "${DSCROSSFIT:=true}"
: "${DSGEN:=0}"           # 1 => also record the one-word label
: "${DSGROUPS:=single}"   # single | windows | both
: "${DSALPHAMODE:=absolute}"  # absolute | relative (fraction of residual norm)
for v in DSMODEL DSBENCH DSREPS DSDIRS DSMODE DSREADOUT DSSITE DSALPHAS DSLAYERS DSWINS DSNPROMPTS DSSPLITS DSCROSSFIT DSGEN DSGROUPS DSALPHAMODE; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' contains a comma; sbatch --export SILENTLY TRUNCATES comma-lists. Use ':' separators."; exit 1;; esac
done
ALPHAS="$(echo "$DSALPHAS" | tr ':' ',')"
SPLITS="$(echo "$DSSPLITS" | tr ':' ',')"
LAYER_ARG=""; [ -n "$DSLAYERS" ] && LAYER_ARG="--layers $(echo "$DSLAYERS" | tr ':' ',')"
WIN_ARG="";   [ -n "$DSWINS" ]   && WIN_ARG="--windows $(echo "$DSWINS" | tr ':' ',')"
GEN_ARG="";   [ "$DSGEN" = "1" ] && GEN_ARG="--generate"
echo "=== pair intervention: mode=$DSMODE readout=$DSREADOUT site=$DSSITE alphas=$ALPHAS groups=$DSGROUPS alpha_mode=$DSALPHAMODE ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/34_intervention_sweep.py \
  --bench "$DSBENCH" --reps-dir "$DSREPS" --dir-dir "$DSDIRS" --model "$DSMODEL" \
  --out-root doublespeak_causality/outputs --mode "$DSMODE" --readout "$DSREADOUT" \
  --site "$DSSITE" --alphas "$ALPHAS" --splits "$SPLITS" \
  --n-prompts "$DSNPROMPTS" --crossfit "$DSCROSSFIT" \
  --layer-groups "$DSGROUPS" --alpha-mode "$DSALPHAMODE" $LAYER_ARG $WIN_ARG $GEN_ARG
echo "=== done ==="; date
