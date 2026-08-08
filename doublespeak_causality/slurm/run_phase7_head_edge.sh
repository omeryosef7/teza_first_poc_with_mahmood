#!/bin/bash
#SBATCH --job-name=ds_p7he
#SBATCH --output=doublespeak_causality/logs/ds_p7he_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_p7he_%j.err
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
# RESOURCE FOOTPRINT -- cpus=4 mem=48G is the fast-allocating default (node RealMemory/8 GPUs = ~64G per
# GPU-share, so --mem=48G leaves all 8 GPUs memory-feasible; 64G leaves only 7). Every #SBATCH line is a
# DEFAULT the matching sbatch flag overrides with no file edit, e.g.
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803 slurm/run_phase7_head_edge.sh
#
# CAUSAL_CIRCUIT_MASTER_PLAN §7: targeted REFUSAL head/edge analysis in the active band L13-20.
# FORWARD/PATCHING ONLY (no generation) -> the >=23GB allowlist applies (not STRICT L40S). eager attn is
# asserted inside the script for the edge part. All tunables are DEFAULTS below and via --export; NONE may
# contain a comma (--export truncates comma-lists) -- the band is passed as a dash-range and expanded by
# the python arg parser, not here.
#   Smoke: sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral_v3/beh_clearharm.json,DSN=2,DSBAND=17-18,DSSPLITS=test slurm/run_phase7_head_edge.sh
#   Full : sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral_v3/beh_clearharm.json,DSN=0,DSBAND=13-20 slurm/run_phase7_head_edge.sh
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
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSBENCH:=doublespeak_causality/data/behavioral_v3/beh_clearharm.json}"
: "${DSREFDIR:=doublespeak_causality/outputs/refusal_alllayers}"
: "${DSBAND:=13-20}"      # active refusal band, dash-range (decoder layers)
: "${DSANCHOR:=18}"       # headline readout layer (P7-validated); hs row = DSANCHOR+1
: "${DSPARTS:=head-edge}" # head, edge, or both -- dash-joined here, converted to a comma list below
: "${DSSPLITS:=train-test}"   # dash-joined -> comma list below (never a comma through --export)
: "${DSN:=0}"             # items per split (0 = all)
: "${DSSEED:=0}"
: "${DSTHINK:=default}"
for v in DSMODEL DSBENCH DSREFDIR DSBAND DSANCHOR DSN DSSEED DSTHINK; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
PARTS="$(echo "$DSPARTS" | tr '-' ',')"
SPLITS="$(echo "$DSSPLITS" | tr '-' ',')"
case "$PARTS" in *[!a-z,]*) echo "ERROR: DSPARTS='$DSPARTS' -> '$PARTS' not a comma list of names"; exit 1 ;; esac
echo "=== Phase7 head/edge: bench=$DSBENCH band=$DSBAND parts=$PARTS splits=$SPLITS n=$DSN anchor=L$DSANCHOR ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
# GPU query guarded against SIGPIPE under pipefail (|| true), then sanitized to digits from a VARIABLE.
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
GPU_MEM_RAW="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 || true)"
GPU_MEM="$(printf '%s' "$GPU_MEM_RAW" | grep -oE '[0-9]+' | head -1 || true)"; GPU_MEM="${GPU_MEM:-0}"
# FORWARD/PATCHING-ONLY job -> >=23GB allowlist (same rationale as run_phase5_headz.sh): no generation, no
# flash-throughput dependence; within-run proj differences cancel any tiny cross-GPU numeric drift.
case "$GPU_TYPE" in
  *L40S*|*l40s*|*A5000*|*a5000*|*A6000*|*a6000*|*A100*|*A40*|*H100*|*H200*|*L40*|*3090*|*4090*)
    if [ "${GPU_MEM:-0}" -ge 23000 ]; then echo "GPU ok: $GPU_TYPE (${GPU_MEM}MiB)";
    else echo "ERROR: $GPU_TYPE has only ${GPU_MEM}MiB (<23GB); Llama-8B bf16 needs ~18GB"; exit 1; fi ;;
  *) echo "ERROR: GPU '$GPU_TYPE' (${GPU_MEM}MiB) not in the allowlist"; exit 1 ;;
esac
python -u doublespeak_causality/scripts/phase7_refusal_head_edge.py \
  --bench "$DSBENCH" --model "$DSMODEL" --refusal-dir "$DSREFDIR" \
  --band "$DSBAND" --readout-anchor "$DSANCHOR" --parts "$PARTS" \
  --splits "$SPLITS" --n "$DSN" --seed "$DSSEED" --enable-thinking "$DSTHINK"
echo "=== done ==="; date
