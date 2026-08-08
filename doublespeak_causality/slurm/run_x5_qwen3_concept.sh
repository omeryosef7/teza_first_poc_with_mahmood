#!/bin/bash
#SBATCH --job-name=ds_x5qwen3cpt
#SBATCH --output=doublespeak_causality/logs/ds_x5qwen3cpt_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_x5qwen3cpt_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# §27 X5 (LAST cross-model gate) -- does the CONCEPT readout FAIL to explain behavior on
# Qwen3-14B, while the REFUSAL readout succeeds (per X3/X4)? One script, two steps (mirrors X2's
# fit+validate), reusing proven harnesses unchanged in structure:
#   (a) FIT a diff-of-means CONCEPT direction (concept-token vs codeword-token last-hidden) at a
#       layer sweep -- the build_refusal_direction_llama.py diff-of-means recipe with the concept
#       contrast; token ids via pair_common.word_first_ids. -> outputs/concept_qwen3/
#   (b) PROJECT each doublespeak item's last-prompt-token residual onto the concept axis (and, as
#       the positive control, onto the X2 Qwen3 REFUSAL axis in outputs/refusal_qwen3 + a
#       norm-matched RANDOM axis), then reuse the P6 analyze_jacobian_predicts_behavior.py AUC +
#       bootstrap-CI pattern to test whether each projection PREDICTS Qwen3 jailbreak (--beh join
#       on the X4 behav_refusal ds_base label, by id).
# ENDPOINT: concept-proj AUC ~= 0.5 (fails) vs refusal-proj AUC > 0.5 (succeeds).
#
# FORWARD-ONLY (no generation): may run on the >=23GB forward/patching allowlist, but the #SBATCH
# nodelist keeps it on the L40S band by default (a 14B model wants the memory anyway). The GPU guard
# below only requires CUDA, not L40S specifically -- forward passes are not the STRICT-L40S class.
#
# mem=64G: REQUIRED for the 14B model (project rule). Node RealMemory=515600MB / 8 GPUs =
# 64450MB per GPU-share, so --mem=64G leaves 7 of 8 GPUs memory-feasible per node -- fine, just
# marginally slower to allocate than a 48G 8B job. --time is NOT the alloc-speed lever.
#
# THINKING model: DSENABLETHINK=false (empty <think></think>) so no live <think> control token
# precedes the last-token readout and no CoT truncation confounds it. Threaded
# dc.parse_enable_thinking -> apply_template in BOTH the fit and the projection steps.
#
# LAYER SWEEP defaults to 16,20,24,28,32 to MATCH the outputs/refusal_qwen3 layers, so the concept
# vs refusal AUC comparison is at identical layers. Choose another sweep via DSLAYERSET (DASH list,
# comma-safe through --export), e.g. DSLAYERSET=16-24-32.
#
# Every #SBATCH line is a DEFAULT overridable on the sbatch line with no file edit, e.g. to skip the
# slow-weight-load node n-801:
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 doublespeak_causality/slurm/run_x5_qwen3_concept.sh
# Do NOT pass --exclude (it NULLIFIES this #SBATCH --nodelist and the job lands anywhere, e.g. a 3090).
#
# USAGE
#   SMOKE (no behavioral join needed; small):
#     sbatch --export=ALL,DSN=3,DSLAYERSET=16-24 doublespeak_causality/slurm/run_x5_qwen3_concept.sh
#   FULL clearharm (with the X4 Qwen3 behavioral labels for the AUC join):
#     sbatch --export=ALL,DSBEH=doublespeak_causality/outputs/behav_refusal_clearharm_a1.0_<ts>_<job> \
#            doublespeak_causality/slurm/run_x5_qwen3_concept.sh
#   FULL generated cohort:
#     sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral_v3b/beh_generated.json,DSBEH=<qwen3 behav_refusal dir> \
#            doublespeak_causality/slurm/run_x5_qwen3_concept.sh
# Comma-list values (DSLAYERS) are DEFAULTS built INSIDE this script -- NEVER pass them via --export
# (sbatch truncates a comma value at the first comma). Pick layers via DSLAYERSET (dash list).
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

: "${DSBENCH:=doublespeak_causality/data/behavioral_v3b/beh_clearharm.json}"
: "${DSMODEL:=Qwen/Qwen3-14B}"
: "${DSREFDIR:=doublespeak_causality/outputs/refusal_qwen3}"       # X2 Qwen3 refusal axes (positive control)
: "${DSCPTOUT:=doublespeak_causality/outputs/concept_qwen3}"       # where the fit concept axes are written
: "${DSFITSPLIT:=train}"                                           # fit concept dir here (out-of-sample eval)
: "${DSEVALSPLITS:=train,test}"                                    # comma-list DEFAULT (never via --export)
: "${DSBEH:=}"                                                     # X4 Qwen3 behav_refusal dir for the AUC join; empty => skip AUC
: "${DSN:=0}"                                                      # cap items/split (smoke lever)
: "${DSSEED:=0}"
: "${DSENABLETHINK:=false}"                                        # thinking-OFF (empty <think></think>)
: "${DSDTYPE:=bfloat16}"

# ---- layer sweep: DASH list via --export (comma-safe), translated to commas INSIDE the script ----
case "${DSLAYERSET:-refusalmatch}" in
  refusalmatch) LAYERS="16,20,24,28,32" ;;             # MATCH outputs/refusal_qwen3 layers (default)
  onset)        LAYERS="12,16,20,24,28,32,36" ;;       # wider sweep incl. earlier onset probe
  *)            case "$DSLAYERSET" in
                  *,*) LAYERS="${DSLAYERSET}" ;;        # inline comma (from a script, not --export)
                  *)   LAYERS="$(echo "$DSLAYERSET" | tr '-' ',')" ;;  # dash list from --export
                esac
                case "$LAYERS" in
                  *[!0-9,]*) echo "ERROR: DSLAYERSET='$DSLAYERSET' -> LAYERS='$LAYERS' is not a list of integers"; exit 1 ;;
                esac ;;
esac
: "${DSLAYERS:=$LAYERS}"

# scalar vars must not contain a comma (--export truncation bug); DSEVALSPLITS/DSLAYERS are lists by design
for v in DSBENCH DSMODEL DSREFDIR DSCPTOUT DSFITSPLIT DSBEH DSN DSSEED DSENABLETHINK DSDTYPE; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done

echo "=== §27 X5 Qwen3-14B CONCEPT readout: FIT + PROJECT + PREDICT ==="
echo "    model=$DSMODEL bench=$DSBENCH layers=$DSLAYERS think=$DSENABLETHINK"
echo "    fit_split=$DSFITSPLIT eval_splits=$DSEVALSPLITS refdir=$DSREFDIR cpt_out=$DSCPTOUT"
echo "    beh(AUC join)=${DSBEH:-<none: AUC skipped>}  n=$DSN seed=$DSSEED"
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"

# ---- GPU guard: forward-only, so require CUDA (any allowlist GPU), not STRICT L40S ----
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in "") echo "ERROR: no GPU visible (nvidia-smi empty)"; exit 1;; *) echo "GPU ok: $GPU_TYPE";; esac

python -u doublespeak_causality/scripts/phase_x5_concept_qwen3.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-dir "$DSREFDIR" --concept-out "$DSCPTOUT" \
  --layers "$DSLAYERS" --fit-split "$DSFITSPLIT" --eval-splits "$DSEVALSPLITS" \
  ${DSBEH:+--beh "$DSBEH"} --n "$DSN" --seed "$DSSEED" \
  --enable-thinking "$DSENABLETHINK" --dtype "$DSDTYPE"
echo "=== done ==="; date
