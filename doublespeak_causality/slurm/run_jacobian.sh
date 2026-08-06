#!/bin/bash
#SBATCH --job-name=ds_jacobian
#SBATCH --output=doublespeak_causality/logs/ds_jacobian_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_jacobian_%j.err
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
# P6 — Jacobian / projection-matrix readout (plan §5 P6).  Per (layer, position) local linear map
# from a residual perturbation to a target scalar, for TWO SEPARATE targets:
#   concept = logit(concept) - logit(codeword)   |   refusal = <hs[R][-1], unit(refusal dir L{R-1})>
# reported next to the PLAIN concept/refusal/signature projections so the lenses share one table.
# Fits nothing (a gradient needs no training), so train and test are computed in one pass.
# (n-801 was previously excluded for slow weight loading -- see the nodelist note above.)
#
#   SMOKE first (2 items/split, ~2 min):
#     sbatch --export=ALL,DSN=2 doublespeak_causality/slurm/run_jacobian.sh
#   FULL:
#     sbatch doublespeak_causality/slurm/run_jacobian.sh
#   Fixed-pair bench instead of the behavioral one:
#     sbatch --export=ALL,DSKIND=pair,DSBENCH=doublespeak_causality/data/pair_benchmark/pair_carrot_bomb.json \
#            doublespeak_causality/slurm/run_jacobian.sh
#   (comma-list values live in the DEFAULTS below, never via --export, which truncates them)
# DSGRADMODE=inputs_embeds roots the autograd graph at the embeddings so the frozen weights never
# allocate a [n_params] gradient buffer (~16GB saved on 8B bf16). If a transformers version ever
# refuses the inputs_embeds path, fall back to 48_attribution_patching's proven route:
#     sbatch --export=ALL,DSGRADMODE=params doublespeak_causality/slurm/run_jacobian.sh
# (identical numbers, higher memory).
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
: "${DSKIND:=behavioral}"
: "${DSCOHORT:=clearharm}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSDTYPE:=bfloat16}"
: "${DSREFDIR:=doublespeak_causality/outputs/refusal_alllayers}"
: "${DSDIRS:=doublespeak_causality/outputs/unified_directions}"
: "${DSDIRSCOHORT:=}"                                  # default: same as DSCOHORT
: "${DSSPLITS:=train,test}"                            # comma-list kept as a DEFAULT (pair bench: dev,heldout)
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
echo "=== P6 jacobian readout: $DSMODEL bench=$DSBENCH kind=$DSKIND cohort=$DSCOHORT n=$DSN ==="
echo "    splits=$DSSPLITS conds=$DSCONDS targets=$DSTARGETS pos=$DSPOS refrow=$DSREFROW grad=$DSGRADMODE"
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase6_jacobian_readout.py \
  --bench "$DSBENCH" --bench-kind "$DSKIND" --cohort "$DSCOHORT" \
  --model "$DSMODEL" --dtype "$DSDTYPE" \
  --refusal-dir "$DSREFDIR" --dirs "$DSDIRS" --dirs-cohort "$DSDIRSCOHORT" \
  --splits "$DSSPLITS" --conditions "$DSCONDS" --targets "$DSTARGETS" --positions "$DSPOS" \
  --layers "$DSLAYERS" --readout "$DSREADOUT" --refusal-hs-row "$DSREFROW" --n "$DSN" \
  --taylor-cells "$DSTAYLORCELLS" --taylor-eps "$DSTAYLOREPS" --taylor-items "$DSTAYLORITEMS" \
  --grad-mode "$DSGRADMODE" --add-special-tokens "$DSADDSPECIAL" --seed "$DSSEED"
echo "=== done ==="; date
