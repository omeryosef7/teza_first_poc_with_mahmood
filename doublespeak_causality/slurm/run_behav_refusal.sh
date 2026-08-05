#!/bin/bash
#SBATCH --job-name=ds_behref
#SBATCH --output=doublespeak_causality/logs/ds_behref_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_behref_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,t-806
#
# BEHAV-REFUSAL: is refusal-bypass the behaviorally sufficient locus of Doublespeak? Direct /
# Direct+refusal-ablation / Direct+random-ablation / DS / DS+refusal-ablation, StrongReject-judged.
# Now also runs the plan §5 P8.1 ALPHA CALIBRATION sweep (see DSALPHAS below).
# n-801 excluded (pathologically slow weight loading).
#   sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSMAXNEW=220,DSN=0 run_behav_refusal.sh
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
: "${DSREFPT:=doublespeak_causality/outputs/stage_gcg_full/refusal_direction_llama_L18.pt}"
: "${DSALPHA:=1.0}"
: "${DSSEED:=0}"
# --- P8.1 alpha calibration grid (plan §5 P8.1: 0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0; a=0 is also the
# no-op positive control, §1.6). This is a comma-list, so it MUST be a DEFAULT here and can NEVER
# come through sbatch --export (which silently truncates at the first comma: "0.25,0.5" -> "0.25").
# Edit DSALPHAS_DEFAULT to change the grid; set it to "" for the historical single-DSALPHA run.
# Cost: 2 + 3*len(grid) generations per item (7 alphas = 23 arms; ~4.9 s/gen measured on job 708038,
# so 86 items ~= 2.7 h, inside the 6 h limit).
DSALPHAS_DEFAULT="0,0.25,0.5,0.75,1.0,1.5,2.0"
if [ -n "${DSALPHAS+x}" ]; then
  echo "ERROR: DSALPHAS='$DSALPHAS' came from the environment/--export; sbatch --export SILENTLY TRUNCATES comma-lists. Edit DSALPHAS_DEFAULT in this wrapper instead."; exit 1
fi
DSALPHAS="$DSALPHAS_DEFAULT"
# scalar vars must not contain a comma (same truncation bug); DSSPLITS/DSALPHAS are lists by design.
for v in DSBENCH DSMODEL DSMAXNEW DSN DSREFPT DSALPHA DSSEED; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
echo "=== behav refusal: $DSMODEL bench=$DSBENCH maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS alpha=$DSALPHA alphas='$DSALPHAS' ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
# --save-gen is ON by default in the harness (gens.jsonl, gitignored); DSNOSAVEGEN=1 turns it off.
python -u doublespeak_causality/scripts/phase_behav_refusal.py \
  --bench "$DSBENCH" --model "$DSMODEL" --max-new "$DSMAXNEW" --refusal-pt "$DSREFPT" --alpha "$DSALPHA" ${DSALPHAS:+--alphas "$DSALPHAS"} ${DSNOSAVEGEN:+--no-save-gen} --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED"
echo "=== done ==="; date
