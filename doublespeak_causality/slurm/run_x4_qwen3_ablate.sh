#!/bin/bash
#SBATCH --job-name=ds_x4qwen
#SBATCH --output=doublespeak_causality/logs/ds_x4qwen_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_x4qwen_%j.err
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
# §27 X4 -- CROSS-MODEL causal test on Qwen3-14B: does refusal ABLATION raise harmful behavior
# (direct_refabl vs direct_base) AND is Doublespeak already at the refusal-suppression ceiling
# (ds_refabl vs ds_base, ds_base vs direct_refabl)? Reuses phase_behav_refusal.py's proven Arditi
# directional-ablation behavioral harness (arms: direct_base / direct_refabl / direct_randabl /
# ds_base / ds_refabl, StrongREJECT-judged). direct_randabl = norm-matched RANDOM-direction control
# (specificity). GENERATION -> STRICT L40S.
#
# mem=64G: REQUIRED for the 14B model (48G is the 8B fast-alloc default; 14B weights + KV overflow
# it). Node RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=64G leaves 7 of 8 GPUs
# memory-feasible per node -- fine, just marginally slower to allocate than 48G. --time is NOT the
# lever for alloc speed.
#
# Qwen3 is a THINKING model: DSENABLETHINK=false runs thinking-OFF (injects empty <think></think>)
# so answers are direct and are NOT truncated mid-CoT by --max-new (the §27 cross-model confound).
# --enable-thinking is threaded dc.parse_enable_thinking -> apply_template for BOTH direct and ds.
#
# Every #SBATCH line is a DEFAULT; the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 doublespeak_causality/slurm/run_x4_qwen3_ablate.sh
# Caveat (232 logged runs): every weight-load slower than 15 min happened on n-801 (worst 79 min);
# no other L40S node exceeded 14 min. To skip n-801 pass an explicit REDUCED --nodelist (NEVER
# --exclude: it NULLIFIES this #SBATCH --nodelist and the job lands anywhere in the partition, e.g.
# an RTX 3090, which only the GPU guard below would catch).
#
#   SMOKE:  sbatch --export=ALL,DSN=2 doublespeak_causality/slurm/run_x4_qwen3_ablate.sh
#   FULL v3b clearharm (alpha=1.0, full ablation/restoration):
#           sbatch doublespeak_causality/slurm/run_x4_qwen3_ablate.sh
#   FULL v3b generated cohort:
#           sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral_v3b/beh_generated.json doublespeak_causality/slurm/run_x4_qwen3_ablate.sh
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
: "${DSMAXNEW:=220}"
: "${DSN:=0}"
: "${DSSPLITS:=train,test}"   # comma-list kept as a DEFAULT here (not via --export, which truncates)
# VALIDATED Qwen3 refusal direction (outputs/refusal_qwen3): mid layer L24 (sep=0.698, thinking-OFF
# extraction). L28 (sep=0.845) is the deeper alternative: pass DSREFPT=.../refusal_direction_llama_L28.pt
: "${DSREFPT:=doublespeak_causality/outputs/refusal_qwen3/refusal_direction_llama_L24.pt}"
: "${DSALPHA:=1.0}"
: "${DSSEED:=0}"
: "${DSENABLETHINK:=false}"    # Qwen3 thinking-OFF: direct answer, no CoT-truncation confound (§27 X4)
# Single-alpha run (no --alphas): reproduces the historical 5-arm design exactly
# (direct_base/direct_refabl/direct_randabl/ds_base/ds_refabl). A P8-style alpha sweep is NOT part of
# X4; leave DSALPHAS unset. If ever needed, edit a DSALPHAS_DEFAULT here -- NEVER pass a comma-list
# through sbatch --export (it silently truncates at the first comma).
# scalar vars must not contain a comma (same truncation bug); DSSPLITS is a list by design.
for v in DSBENCH DSMODEL DSMAXNEW DSN DSREFPT DSALPHA DSSEED DSENABLETHINK; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
echo "=== X4 qwen3 ablate: $DSMODEL bench=$DSBENCH maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS alpha=$DSALPHA refpt=$DSREFPT think=$DSENABLETHINK ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
# --save-gen is ON by default in the harness (gens.jsonl, gitignored); DSNOSAVEGEN=1 turns it off.
python -u doublespeak_causality/scripts/phase_behav_refusal.py \
  --bench "$DSBENCH" --model "$DSMODEL" --max-new "$DSMAXNEW" --refusal-pt "$DSREFPT" \
  --alpha "$DSALPHA" ${DSNOSAVEGEN:+--no-save-gen} --n "$DSN" --splits "$DSSPLITS" \
  --seed "$DSSEED" --enable-thinking "$DSENABLETHINK"
echo "=== done ==="; date
