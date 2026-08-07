#!/bin/bash
#SBATCH --job-name=ds_refsuploc
#SBATCH --output=doublespeak_causality/logs/ds_refsuploc_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_refsuploc_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- measured 2026-08-05, do not re-litigate: cpus=4 mem=48G is the fast-allocating
# default (8cpu/64G sat PENDING 3h32m as 716187/716188; the SAME work at 4cpu/48G allocated in 6m32s as
# 717879/717880). Mechanism: node RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=64G
# leaves only 7 of 8 GPUs memory-feasible per node while 48G leaves all 8. --time is NOT the lever.
# Every #SBATCH line below is a DEFAULT: the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_jacobian.sh
# n-801 is back in the nodelist (a full gpu:l40s:8 node = 1/6 of our L40S capacity). Caveat, measured
# over 232 logged runs: every weight-load slower than 15 min happened on n-801 (worst 79 min), while no
# other L40S node ever exceeded 14 min. To avoid a node, DO NOT use --exclude: passing --exclude on the
# sbatch line NULLIFIES this #SBATCH --nodelist and the job then lands anywhere in the partition. That
# happened on 2026-08-06 (jobs 721954/721955 -> n-306, an RTX 3090); only the GPU guard below caught it.
# Pass an explicit REDUCED NODELIST instead, e.g. to skip n-801:
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/<wrapper>.sh
#
# §3 (Master Plan V2) — Refusal-suppression causal localization at the DECISION TOKEN.
# For each (layer L, component C in {resid_pre,attn_out,mlp_out,resid_post}) replace the DS prompt's
# decision-token activation with the matched donor's decision-token activation and read the change in
# the VALIDATED refusal-direction projection (P7 set {L13-20,24,28,29}; anchor L18; NEVER L9).
#   donors: direct/neutral = necessity; rand = norm-matched-random specificity control (§0.4);
#           self = locality/no-op gate (must reproduce ds_base, max|restore|~0).
# Endpoint here is REPRESENTATIONAL; behavioral confirmation of a passing cell is a separate arm.
#
#   SMOKE first (2 items/split, verifies the new rand/neutral donor paths):
#     sbatch --export=ALL,DSN=2 doublespeak_causality/slurm/run_refusal_localize.sh
#   FULL v3 clearharm cohort (default bench):
#     sbatch doublespeak_causality/slurm/run_refusal_localize.sh
#   FULL v3 generated cohort (scalar values only via --export; comma-lists stay in DEFAULTS):
#     sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral_v3/beh_generated.json,DSCOHORT=generated \
#            doublespeak_causality/slurm/run_refusal_localize.sh
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
: "${DSBENCH:=doublespeak_causality/data/behavioral_v3/beh_clearharm.json}"   # v3 = leakage-free confirmatory (§0.5); generated cohort via --export=ALL,DSBENCH=...beh_generated.json,DSCOHORT=generated
: "${DSKIND:=behavioral}"
: "${DSCOHORT:=clearharm}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSDTYPE:=bfloat16}"
: "${DSREFDIR:=doublespeak_causality/outputs/refusal_alllayers}"
: "${DSDIRS:=doublespeak_causality/outputs/unified_directions}"
: "${DSDIRSCOHORT:=}"                                  # default: same as DSCOHORT
: "${DSSPLITS:=train,dev,test}"                        # comma-list kept as a DEFAULT (v3 has train/dev/test; discovery=train,dev / test=frozen full-sweep confirm)
: "${DSCONDS:=direct,neutral,doublespeak}"             # comma-list kept as a DEFAULT
: "${DSTARGETS:=concept,refusal}"                      # comma-list kept as a DEFAULT (never merged)
: "${DSPOS:=final_prompt,probe_last}"                  # comma-list kept as a DEFAULT
: "${DSLAYERS:=}"                                      # comma-list kept as a DEFAULT; empty = full sweep
: "${DSREADOUT:=one_word}"                             # pair bench only
: "${DSREFROW:=-1}"                                    # -1 => hidden-states row num_layers
: "${DSN:=0}"
: "${DSTAYLORCELLS:=3}"
: "${DSTAYLOREPS:=0.5}"
: "${DSTAYLORITEMS:=2}"
: "${DSGRADMODE:=inputs_embeds}"                       # keeps [n_params] grad buffers unallocated
: "${DSADDSPECIAL:=false}"                             # house convention (apply_template emits BOS)
: "${DSSEED:=0}"
: "${DSANCHOR:=18}"                                   # validated readout layer to headline
: "${DSCOMPONENTS:=resid_pre,attn_out,mlp_out,resid_post}"
: "${DSDONORS:=direct,neutral,rand,self}"             # necessity=direct/neutral; specificity=rand (norm-matched); locality gate=self
echo "=== refusal-suppression localize (§3): $DSMODEL bench=$DSBENCH n=$DSN ==="
echo "    splits=$DSSPLITS components=$DSCOMPONENTS donors=$DSDONORS anchor=L$DSANCHOR layers=${DSLAYERS:-all}"
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
GPU_MEM_ALL="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null || true)"
GPU_MEM="${GPU_MEM_ALL%%$'\n'*}"; GPU_MEM="$(printf '%s' "$GPU_MEM" | grep -oE '[0-9]+' | head -1 || true)"; GPU_MEM="${GPU_MEM:-0}"
# VRAM-gated allowlist (>=23GB, bf16-capable Ampere+/Ada): use free a5000/3090 when L40S is booked.
# GPU_TYPE via ${VAR%%...} (no head pipe) is already SIGPIPE-safe; GPU_MEM sanitized from a variable.
case "$GPU_TYPE" in
  *L40S*|*l40s*|*A5000*|*a5000*|*A6000*|*a6000*|*A100*|*A40*|*H100*|*H200*|*L40*|*3090*|*4090*)
    if [ "${GPU_MEM:-0}" -ge 23000 ]; then echo "GPU ok: $GPU_TYPE (${GPU_MEM}MiB)";
    else echo "ERROR: $GPU_TYPE has only ${GPU_MEM}MiB (<23GB)"; exit 1; fi ;;
  *) echo "ERROR: GPU '$GPU_TYPE' (${GPU_MEM}MiB) not in the >=23GB allowlist"; exit 1 ;;
esac
python -u doublespeak_causality/scripts/phase_refusal_suppression_localize.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-dir "$DSREFDIR" \
  --readout-anchor "$DSANCHOR" --components "$DSCOMPONENTS" --donors "$DSDONORS" \
  --layers "$DSLAYERS" --splits "$DSSPLITS" --n "$DSN" --seed "$DSSEED"
echo "=== done ==="; date
