#!/bin/bash
#SBATCH --job-name=ds_p8path
#SBATCH --output=doublespeak_causality/logs/ds_p8path_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p8path_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- mirrors run_phase5_headz.sh (measured 2026-08-05): cpus=4 mem=48G is the
# fast-allocating default. Node RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=48G
# leaves all 8 GPUs memory-feasible per node (--mem=64G would strand one). --time is NOT the lever.
# Every #SBATCH line is a DEFAULT: the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --time=03:00:00 --mem=64G --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_phase8_path.sh
#
# §8 full head->MLP PATH PATCHING (scripts/phase8_head_mlp_path.py) -- extends the head->head
# path patcher (50_path_patching.py) to MLP receivers. FORWARD/PATCHING only (no generation), so
# the >=23GB GPU allowlist applies (identical guard to run_phase5_headz.sh).
#
# CONFIG via --export env vars (all SCALARS; NO comma-lists -- the sender/receiver selections use
# scalar band bounds + --from-head-attr, never comma-list --export values which silently truncate).
#   # 8.1 concept
#   sbatch --export=ALL,DSFAMILY=concept,DSBENCH=doublespeak_causality/data/pair_benchmark/pair_carrot_bomb.json,\
# DSFROMHEADATTR=doublespeak_causality/outputs/head_attr_<...>/head_attribution.json,DSMLPLO=8,DSMLPHI=13 \
#     doublespeak_causality/slurm/run_phase8_path.sh
#   # 8.2 refusal
#   sbatch --export=ALL,DSFAMILY=refusal,DSBENCH=doublespeak_causality/data/behavioral_v3/beh_clearharm.json,\
# DSFROMHEADATTR=doublespeak_causality/outputs/head_attr_<...>/head_attribution.json,DSMLPLO=8,DSMLPHI=17,DSREFLAYER=18,DSSPLIT=test \
#     doublespeak_causality/slurm/run_phase8_path.sh
#   # smoke: DSTOPN=2 DSMLPLO=<a> DSMLPHI=<a+1> DSRANDS=1 DSRANDR=1
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"; export PYTHONUNBUFFERED=1

: "${DSFAMILY:?set DSFAMILY=concept|refusal}"
: "${DSBENCH:?set DSBENCH to a pair_*.json (concept) or beh_*.json (refusal)}"
: "${DSFROMHEADATTR:?set DSFROMHEADATTR to a head_attribution.json (or use DSSENDERHEADS)}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSLO:=7}"; : "${DSHI:=14}"; : "${DSTOPN:=6}"
: "${DSMLPLO:=8}"; : "${DSMLPHI:=13}"
: "${DSMETRIC:=p_concept}"
: "${DSSPLIT:=}"                 # empty -> script default (concept=heldout, refusal=test)
: "${DSREFLAYER:=18}"; : "${DSCORRUPT:=neutral}"; : "${DSITEMIDX:=0}"
: "${DSRANDS:=2}"; : "${DSRANDR:=2}"; : "${DSSEED:=0}"
: "${DSRECON:=0}"               # 1 -> add --recon-full (also computes head-edges for the recon gate)
: "${DSENABLE:=default}"        # Qwen3 thinking: default|true|false
: "${DSSENDERHEADS:=}"          # optional explicit "L:h" -- kept EMPTY by default (no comma via --export)

# comma guard: every --export-passed value must be a SINGLE scalar (--export truncates comma-lists)
for v in DSFAMILY DSBENCH DSFROMHEADATTR DSMODEL DSLO DSHI DSTOPN DSMLPLO DSMLPHI DSMETRIC DSSPLIT \
         DSREFLAYER DSCORRUPT DSITEMIDX DSRANDS DSRANDR DSSEED DSRECON DSENABLE; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done

echo "=== Phase8 head->MLP path: family=$DSFAMILY bench=$DSBENCH ==="; date; hostname
echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
# memory.total sanitized to DIGITS ONLY from a VARIABLE (no unguarded nvidia-smi pipe under pipefail;
# see run_phase5_headz.sh for the full SIGPIPE / trailing-unit rationale).
GPU_MEM_RAW="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 || true)"
GPU_MEM="$(printf '%s' "$GPU_MEM_RAW" | grep -oE '[0-9]+' | head -1 || true)"
GPU_MEM="${GPU_MEM:-0}"
# FORWARD-PASS-ONLY patching job (no generation): the >=23GB allowlist applies (Ampere+ run
# Llama-3.1-8B bf16 identically for within-run activation differences).
case "$GPU_TYPE" in
  *L40S*|*l40s*|*A5000*|*a5000*|*A6000*|*a6000*|*A100*|*A40*|*H100*|*H200*|*L40*|*3090*|*4090*)
    if [ "${GPU_MEM:-0}" -ge 23000 ]; then echo "GPU ok: $GPU_TYPE (${GPU_MEM}MiB)";
    else echo "ERROR: $GPU_TYPE has only ${GPU_MEM}MiB (<23GB); Llama-8B bf16 needs ~18GB"; exit 1; fi ;;
  *) echo "ERROR: GPU '$GPU_TYPE' (${GPU_MEM}MiB) not in the allowlist"; exit 1 ;;
esac

EXTRA=()
[ "$DSRECON" = "1" ] && EXTRA+=(--recon-full)
[ -n "$DSSPLIT" ] && EXTRA+=(--split "$DSSPLIT")
[ -n "$DSSENDERHEADS" ] && EXTRA+=(--sender-heads "$DSSENDERHEADS")

python -u doublespeak_causality/scripts/phase8_head_mlp_path.py \
  --family "$DSFAMILY" --bench "$DSBENCH" --model "$DSMODEL" \
  --from-head-attr "$DSFROMHEADATTR" \
  --lo "$DSLO" --hi "$DSHI" --topn "$DSTOPN" \
  --mlp-lo "$DSMLPLO" --mlp-hi "$DSMLPHI" \
  --metric "$DSMETRIC" \
  --refusal-layer "$DSREFLAYER" --corrupt-cond "$DSCORRUPT" --item-idx "$DSITEMIDX" \
  --rand-senders "$DSRANDS" --rand-receivers "$DSRANDR" \
  --enable-thinking "$DSENABLE" --seed "$DSSEED" \
  "${EXTRA[@]}"
