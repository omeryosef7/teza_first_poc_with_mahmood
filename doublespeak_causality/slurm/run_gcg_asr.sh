#!/bin/bash
#SBATCH --job-name=ds_gcgasr
#SBATCH --output=doublespeak_causality/logs/ds_gcgasr_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_gcgasr_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- measured 2026-08-05, do not re-litigate: cpus=4 mem=48G is the fast-allocating
# default repo-wide (8cpu/64G sat PENDING 3h32m as 716187/716188; the SAME work at 4cpu/48G allocated in
# 6m32s as 717879/717880). Mechanism: node RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so
# --mem=64G leaves only 7 of 8 GPUs memory-feasible per node while 48G leaves all 8. --time is NOT the lever.
# EXCEPTION, deliberate: this wrapper stays at mem=64G because it loads Qwen3-14B, ~28GB of bf16 weights
# streamed through host page cache per load -- 2x the 8B footprint the A/B above was measured on. The
# allocation win is untested at 14B; drop it to 48G with the flag below if this job queues.
# Every #SBATCH line below is a DEFAULT: the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_gcg_asr.sh
#
# Track B (temporal-GCG) step 5: held-out ASR (Level-5 test). Applies temporal vs baseline optimized
# suffixes to the held-out Neutral prompts, generates, judges harmful compliance.
#   sbatch --export=ALL,DSTEMP=doublespeak_causality/outputs/gcg/opt_qwen3_temporal,DSBASE=doublespeak_causality/outputs/gcg/opt_qwen3_baseline run_gcg_asr.sh
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
: "${DSTEMP:?set DSTEMP (temporal run dir)}"
: "${DSBASE:?set DSBASE (baseline run dir)}"
: "${DSMANIFEST:=doublespeak_causality/data/gcg/curated_qwen3_neutral.jsonl}"
: "${DSMATRIX:=doublespeak_causality/data/behavioral_benchmark/screening_matrix_curated_v1.json}"
: "${DSMODEL:=Qwen/Qwen3-14B}"
: "${DSSPLIT:=val}"
: "${DSTHINK:=off}"
: "${DSMAXTOK:=200}"
echo "=== gcg ASR: temporal=$DSTEMP baseline=$DSBASE split=$DSSPLIT ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/25_eval_gcg_asr.py \
  --neutral-manifest "$DSMANIFEST" --matrix "$DSMATRIX" \
  --temporal-dir "$DSTEMP" --baseline-dir "$DSBASE" \
  --model "$DSMODEL" --split "$DSSPLIT" --enable-thinking "$DSTHINK" --max-new-tokens "$DSMAXTOK"
echo "=== done ==="; date
