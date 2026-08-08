#!/bin/bash
#SBATCH --job-name=ds_p11jt
#SBATCH --output=doublespeak_causality/logs/ds_p11jt_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p11jt_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=16:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- copied from run_phase10_powered.sh (measured 2026-08-05, do not re-litigate):
# cpus=4 mem=48G is the fast-allocating default (node RealMemory 515600MB / 8 GPUs = 64450MB per share,
# so 48G leaves all 8 GPUs feasible; 64G leaves only 7). Every #SBATCH line is a DEFAULT overridable by
# the matching sbatch flag. To skip the slow-loading n-801: pass an explicit REDUCED --nodelist (NOT
# --exclude, which nullifies #SBATCH --nodelist and can land on a 3090).
#
# §11 JOINT 2x2 factorial on DOUBLESPEAK prompts: concept circuit {intact/ablated} x refusal {restored/not}.
#   4 cells (all DS, paired within item, StrongReject-judged vs the harmful goal):
#     ds_base(0,0) · concept_abl(1,0) · refusal_restored(0,1) · both(1,1)
#   concept ablation = PhasedMLPZero(L8-11 write, reused from phase_behav_write) + AllPositionZHeadAblate
#     (CARRY, reused from phase_behav_carry); refusal restoration = calibrated pc.AllPositionAdd per
#     refusal layer (dir = refusal_direction_llama_L{L}.pt, alpha = direct-ds proj gap from proj-summary),
#     the phase_defense_utility / calinj recipe VERBATIM. both = all context managers stacked.
#   Primary = within-item DiD interaction on ASR (Ihat, bootstrap CI, sign-flip perm p), POOLED across
#   both v3 cohorts + all splits; FROZEN-test confirmatory. + optional cheap probes (refusal projection
#   per cell, p_concept write-ablation control). walltime 16:00 = 4 gen arms x ~324 items x 220 tokens
#   plus (probe) ~6 single forwards/item.
#   full:  sbatch --export=ALL,DSN=0 slurm/run_phase11_joint.sh
#   smoke: sbatch --export=ALL,DSN=2 slurm/run_phase11_joint.sh
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
# comma-list DEFAULTS kept here (--export truncates comma values); v3 benches POOLED across cohorts.
: "${DSBENCHES:=doublespeak_causality/data/behavioral_v3/beh_clearharm.json,doublespeak_causality/data/behavioral_v3/beh_generated.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSMAXNEW:=220}"
: "${DSN:=0}"
: "${DSSPLITS:=train,dev,test}"        # comma-list DEFAULT (not via --export)
: "${DSWLAYERS:=8-11}"                  # concept-WRITE band (dash-range)
: "${DSRLAYERS:=18}"                    # refusal-RESTORE layer(s) (comma-list; 18 = validated best defense)
: "${DSREFDIR:=doublespeak_causality/outputs/refusal_alllayers}"
: "${DSPROJ:=doublespeak_causality/outputs/refproj_clearharm_20260804_162641_711392/summary.json}"
: "${DSPROJSPLIT:=train}"
: "${DSSEED:=0}"
: "${DSTHINK:=default}"                 # default/true/false (Llama=default; Qwen3=false)
: "${DSPROBE:=1}"                       # 1 = cheap probes on (default); 0 = --no-probe
: "${DSSAVEGEN:=1}"                     # 1 = write gens.jsonl (default); 0 = --no-save-gen
DSFLAGS=""
[ "$DSPROBE" = "1" ] && DSFLAGS="$DSFLAGS --probe" || DSFLAGS="$DSFLAGS --no-probe"
[ "$DSSAVEGEN" = "1" ] && DSFLAGS="$DSFLAGS --save-gen" || DSFLAGS="$DSFLAGS --no-save-gen"
echo "=== p11 joint 2x2: $DSMODEL benches=$DSBENCHES write=$DSWLAYERS refusal=$DSRLAYERS proj=$DSPROJ($DSPROJSPLIT) maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS flags=$DSFLAGS ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase11_joint_2x2.py \
  --benches "$DSBENCHES" --model "$DSMODEL" --max-new "$DSMAXNEW" \
  --write-layers "$DSWLAYERS" --refusal-layers "$DSRLAYERS" \
  --refusal-dir "$DSREFDIR" --proj-summary "$DSPROJ" --proj-split "$DSPROJSPLIT" \
  --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED" --enable-thinking "$DSTHINK" $DSFLAGS
echo "=== done ==="; date
