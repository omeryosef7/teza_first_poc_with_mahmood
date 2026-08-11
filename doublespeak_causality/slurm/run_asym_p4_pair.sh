#!/bin/bash
#SBATCH --job-name=asym_p4
#SBATCH --output=doublespeak_causality/logs/asym_p4_%j.out
#SBATCH --error=doublespeak_causality/logs/asym_p4_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=10:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# ASYMMETRY SPRINT Phase 4 (plan §8): minimal causal battery for ONE concept pair.
# Pure reuse of the published harnesses -- no new causal code. One pair per job.
#
#   sbatch --export=ALL,ASYM_PAIR=grenade,ASYM_STAGE=refusal  slurm/run_asym_p4_pair.sh
#   sbatch --export=ALL,ASYM_PAIR=grenade,ASYM_STAGE=concept  slurm/run_asym_p4_pair.sh
#   sbatch --export=ALL,ASYM_PAIR=grenade,ASYM_STAGE=repr     slurm/run_asym_p4_pair.sh
#   sbatch --export=ALL,ASYM_PAIR=grenade,ASYM_STAGE=refusal,ASYM_N=2 ...   # smoke
#
# STAGES
#   repr     phase_refusal_projection.py  -- refusal projection under Direct/Neutral/DS (fast, no judge)
#   refusal  phase_behav_refusal.py       -- refusal ablation vs matched random, dose sweep (judge)
#   concept  phase10_powered_concept_ablation.py -- whole concept circuit vs matched random (judge)
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1
export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONUNBUFFERED=1

: "${ASYM_PAIR:?set ASYM_PAIR=bomb|grenade|pistol|chlorine|cocaine}"
: "${ASYM_STAGE:?set ASYM_STAGE=repr|refusal|concept}"
: "${ASYM_MODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${ASYM_N:=0}"
: "${ASYM_MAXNEW:=220}"
: "${ASYM_SEED:=0}"
BENCH="doublespeak_causality/data/behavioral_pairs/beh_pair_${ASYM_PAIR}.json"
# The frozen, VALIDATED pooled refusal axis (plan §8.2: do NOT reselect per pair).
# stage_gcg_full/L18 is md5-identical to refusal_alllayers/L18 but is the copy that carries
# the ablate+induce validation block, so cite that one.
REFPT="doublespeak_causality/outputs/stage_gcg_full/refusal_direction_llama_L18.pt"
# comma lists built HERE, never through --export (project memory: --export comma truncation)
ALPHAS="0.0,0.5,1.0"
SPLITS="train,test"
CONCEPT_LAYERS="8-11"

echo "=== ASYM P4 pair=$ASYM_PAIR stage=$ASYM_STAGE n=$ASYM_N ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"
test -f "$BENCH" || { echo "ERROR missing bench $BENCH (run scripts/asym_pair_to_behavioral.py)"; exit 1; }
test -f "$REFPT" || { echo "ERROR missing $REFPT"; exit 1; }
python -c "
import json,sys; d=json.load(open('$BENCH')); m=d['_meta']
print('[bench]', m['cohort'], 'items', len(d['items']), m['per_split'], 'rt', m['round_trip_verified'])
assert min(m['per_split'].values())>=20, 'plan 8.1 needs >=20 per split'"
if [ -z "${OPENAI_API_KEY:-}" ] && [ "$ASYM_STAGE" != "repr" ]; then
  echo "ERROR: OPENAI_API_KEY unset -> StrongREJECT would silently score null (plan 3.6)"; exit 1
fi
# GPU class guard. Plan §3.1 forbids MIXING GPU classes within a direct comparison. Every
# contrast Phase 4 makes (refusal-abl vs matched-random-abl, concept-abl vs matched-random)
# is WITHIN one job and therefore within one GPU, and Gate F is a meta-analysis over those
# within-pair effects -- but to keep the cross-pair table clean we still pin ALL five pairs
# to ONE class via ASYM_GPU. Set ASYM_GPU=a5000 to use the idle a5000 nodes when L40S
# fair-share is throttled; the class actually used is echoed and lands in RUNMETA.
: "${ASYM_GPU:=l40s}"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
GPU_LC="$(echo "$GPU_TYPE" | tr 'A-Z' 'a-z')"
case "$GPU_LC" in
  *"$ASYM_GPU"*) echo "GPU ok: $GPU_TYPE (required class: $ASYM_GPU)";;
  *) echo "ERROR need $ASYM_GPU got '$GPU_TYPE'"; exit 1;;
esac
export ASYM_GPU_CLASS="$GPU_TYPE"

case "$ASYM_STAGE" in
  repr)
    python -u doublespeak_causality/scripts/phase_refusal_projection.py \
      --bench "$BENCH" --model "$ASYM_MODEL" \
      --refusal-dir doublespeak_causality/outputs/refusal_alllayers \
      --splits "$SPLITS" --n "$ASYM_N" --seed "$ASYM_SEED"
    ;;
  refusal)
    python -u doublespeak_causality/scripts/phase_behav_refusal.py \
      --bench "$BENCH" --model "$ASYM_MODEL" --refusal-pt "$REFPT" \
      --alphas "$ALPHAS" --splits "$SPLITS" \
      --max-new "$ASYM_MAXNEW" --n "$ASYM_N" --seed "$ASYM_SEED" --save-gen
    ;;
  concept)
    python -u doublespeak_causality/scripts/phase10_powered_concept_ablation.py \
      --benches "$BENCH" --model "$ASYM_MODEL" --layers "$CONCEPT_LAYERS" \
      --splits "$SPLITS" --max-new "$ASYM_MAXNEW" --n "$ASYM_N" \
      --seed "$ASYM_SEED" --save-gen
    ;;
  *) echo "unknown ASYM_STAGE=$ASYM_STAGE"; exit 1;;
esac
echo "=== done ==="; date
