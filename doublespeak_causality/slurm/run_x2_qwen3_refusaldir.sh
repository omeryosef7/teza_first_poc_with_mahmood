#!/bin/bash
#SBATCH --job-name=ds_x2qwen3ref
#SBATCH --output=doublespeak_causality/logs/ds_x2qwen3ref_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_x2qwen3ref_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# §27 X2 -- fit + validate a diff-of-means REFUSAL DIRECTION on Qwen/Qwen3-14B (40 hidden layers,
# a different model family from Llama-3.1-8B). REUSES two proven harnesses unchanged in structure:
#   (a) FIT      build_refusal_direction_llama.py  (generic dc.load_model / forward_hidden_states /
#                apply_template stack; --model + --layers) -> outputs/refusal_qwen3/
#   (b) VALIDATE scripts/validate_refusal_directions.py (family 'existing' loads the just-fit .pt;
#                bidirectional ablate+induce generation gate with norm-matched random controls).
#
# Qwen3-14B is a THINKING model: --enable-thinking false is threaded into BOTH steps (fit last-token
# readout AND every validation generation arm) so a live <think> block / CoT truncation at --max-new
# does not confound the last-token residual or the refusal judge. On Llama this flag is 'default' and
# both scripts stay byte-identical (dc.parse_enable_thinking None => kwarg not passed).
#
# LAYER SWEEP. Qwen3-14B has 40 layers; Llama's validated refusal band onsets ~L13/32 (~40% depth),
# so Qwen3's is expected ~L16+ (40% of 40). Default sweep = mid-late 16,20,24,28,32 (all < 40).
#
# RESOURCE FOOTPRINT. mem=64G is REQUIRED for the 14B model (per project rule). CAVEAT (measured on
# the L40S nodes, RealMemory 515600MB / 8 GPUs = 64450MB per GPU-share): --mem=64G leaves only 7 of 8
# GPUs memory-feasible per node, so it allocates slightly slower than the 48G 8B jobs -- expected, do
# not drop below 64G for a 14B model. Every #SBATCH line is a DEFAULT overridable on the sbatch line
# with no file edit, e.g. to skip the slow-weight-load node n-801:
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_x2_qwen3_refusaldir.sh
# Do NOT pass --exclude (it NULLIFIES this #SBATCH --nodelist and the job lands anywhere, e.g. a 3090).
#
# USAGE
#   sbatch slurm/run_x2_qwen3_refusaldir.sh                                  # full: fit + validate
#   sbatch --export=ALL,DSLAYERSET=16-20-24-28-32 slurm/run_x2_qwen3_refusaldir.sh
#   sbatch --export=ALL,DSVALN=4,DSMAXNEW=16,DSLAYERSET=16-24 slurm/run_x2_qwen3_refusaldir.sh   # smoke
#   sbatch --export=ALL,DSDRYRUN=1 slurm/run_x2_qwen3_refusaldir.sh          # validate step CPU dry-run
# Comma-list values (DSLAYERS, DSFAMILIES) are DEFAULTS built INSIDE this script -- NEVER pass them via
# --export (sbatch truncates a comma value at the first comma). Choose layers via DSLAYERSET (dash list).
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

: "${DSMODEL:=Qwen/Qwen3-14B}"
: "${DSENABLETHINK:=false}"     # thinking model -> false (empty <think></think>, no CoT truncation)
: "${DSFITBENCH:=doublespeak_causality/data/pair_benchmark/pair_carrot_bomb.json}"   # (a) FIT: pair format (behavioral 'direct'/'neutral')
: "${DSVALBENCH:=doublespeak_causality/data/behavioral_v3b/beh_clearharm.json}"      # (b) VALIDATE: behavioral format (+benign_prompt)
: "${DSOUTDIR:=doublespeak_causality/outputs/refusal_qwen3}"                          # (a) writes refusal_direction_llama_L{L}.pt here; (b) reads them
: "${DSFAMILIES:=existing}"     # validate the just-fit dirs; add ',clearharm' for an out-of-sample refit comparison
: "${DSFITSPLIT:=train}"
: "${DSEVALSPLIT:=test}"
: "${DSVALN:=20}"               # eval items per validation arm (>=20/cell rule)
: "${DSMAXNEW:=64}"
: "${DSABLALPHA:=1.0}"          # full directional ablation (Arditi standard)
: "${DSABLSCOPE:=all_layers}"
: "${DSINDSCOPE:=allpos}"
: "${DSINDMODE:=gap}"           # per-layer calibrated dose (resolves the alpha-norm confound across a 40-layer sweep)
: "${DSINDALPHA:=8.0}"          # only used when DSINDMODE=fixed
: "${DSINDEVAL:=benign}"        # OUT-OF-SAMPLE induce population (v3b carries benign_prompt); 'harmless' is in-sample for 'existing'
: "${DSSEED:=0}"
: "${DSDRYRUN:=0}"              # 1 => skip FIT, run the validate step in CPU dry-run (PLAN.json only)

# ---- layer sweep: DASH list via --export (comma-safe), translated to commas INSIDE the script ----
case "${DSLAYERSET:-midlate}" in
  midlate)  LAYERS="16,20,24,28,32" ;;                 # default mid-late band for a 40-layer model
  onset)    LAYERS="12,16,20,24,28,32,36" ;;           # wider sweep incl. earlier onset probe
  *)        case "$DSLAYERSET" in
              *,*) LAYERS="${DSLAYERSET}" ;;            # inline comma (from a script, not --export)
              *)   LAYERS="$(echo "$DSLAYERSET" | tr '-' ',')" ;;   # dash list from --export
            esac
            case "$LAYERS" in
              *[!0-9,]*) echo "ERROR: DSLAYERSET='$DSLAYERSET' -> LAYERS='$LAYERS' is not a list of integers"; exit 1 ;;
            esac ;;
esac
: "${DSLAYERS:=$LAYERS}"

echo "=== §27 X2 Qwen3-14B refusal direction: FIT + VALIDATE ==="
echo "    model=$DSMODEL enable_thinking=$DSENABLETHINK layers=$DSLAYERS out=$DSOUTDIR"
echo "    fit_bench=$DSFITBENCH  val_bench=$DSVALBENCH  families=$DSFAMILIES"
echo "    val: n=$DSVALN maxnew=$DSMAXNEW abl($DSABLALPHA,$DSABLSCOPE) ind($DSINDSCOPE,$DSINDMODE,eval=$DSINDEVAL)"
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"

# ---- STRICT L40S guard (generation runs on L40S only); skipped on a CPU dry-run ----
if [ "$DSDRYRUN" != "1" ]; then
  GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
  case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
fi

# ---- (a) FIT: diff-of-means refusal directions at the layer sweep -> $DSOUTDIR ----
if [ "$DSDRYRUN" != "1" ]; then
  echo "--- (a) FIT build_refusal_direction_llama.py ---"; date
  python -u doublespeak_causality/build_refusal_direction_llama.py \
    --bench "$DSFITBENCH" --model "$DSMODEL" --layers "$DSLAYERS" \
    --enable-thinking "$DSENABLETHINK" --out "$DSOUTDIR"
fi

# ---- (b) VALIDATE: bidirectional ablate+induce gate on the just-fit directions ----
echo "--- (b) VALIDATE validate_refusal_directions.py ---"; date
VAL_EXTRA=""; [ "$DSDRYRUN" = "1" ] && VAL_EXTRA="--dry-run"
python -u doublespeak_causality/scripts/validate_refusal_directions.py \
  --bench "$DSVALBENCH" --model "$DSMODEL" --refusal-dir "$DSOUTDIR" \
  --layers "$DSLAYERS" --families "$DSFAMILIES" \
  --fit-split "$DSFITSPLIT" --eval-split "$DSEVALSPLIT" --val-n-items "$DSVALN" \
  --max-new "$DSMAXNEW" --ablate-alpha "$DSABLALPHA" --ablate-scope "$DSABLSCOPE" \
  --induce-scope "$DSINDSCOPE" --induce-alpha-mode "$DSINDMODE" --induce-alpha "$DSINDALPHA" \
  --induce-eval "$DSINDEVAL" --enable-thinking "$DSENABLETHINK" \
  --seed "$DSSEED" $VAL_EXTRA
echo "=== done ==="; date
