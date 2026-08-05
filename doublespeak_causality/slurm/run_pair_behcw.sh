#!/bin/bash
#SBATCH --job-name=ds_pairbehcw
#SBATCH --output=doublespeak_causality/logs/ds_pairbehcw_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_pairbehcw_%j.err
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
# RESOURCE FOOTPRINT -- measured 2026-08-05, do not re-litigate: cpus=4 mem=48G is the fast-allocating
# default (8cpu/64G sat PENDING 3h32m as 716187/716188; the SAME work at 4cpu/48G allocated in 6m32s as
# 717879/717880). Mechanism: node RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=64G
# leaves only 7 of 8 GPUs memory-feasible per node while 48G leaves all 8. --time is NOT the lever.
# Every #SBATCH line below is a DEFAULT: the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --exclude=n-801 slurm/run_pair_behcw.sh
#
# CAUSAL_CORE_PLAN §8.1/§8.2 + §9 (S12 first slice): does selecting codewords by the SAFE
# semantic causal score improve HELD-OUT BEHAVIORAL malicious rate? Success is behavior,
# never a representation loss.
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
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSBENCH:=doublespeak_causality/data/pair_benchmark/pair_carrot_bomb.json}"
: "${DSCWSUM:?DSCWSUM (S13 codeword_summary.json) is required}"
: "${DSK:=5}"
: "${DSNBASES:=12}"
: "${DSSTYLE:=news}"
: "${DSNDEMOS:=12}"
: "${DSMAXTOK:=200}"
for v in DSMODEL DSBENCH DSCWSUM DSK DSNBASES DSSTYLE DSNDEMOS DSMAXTOK; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' contains a comma; sbatch --export SILENTLY TRUNCATES comma-lists."; exit 1;; esac
done
echo "=== pair behavioral codeword eval: k=$DSK n_bases=$DSNBASES ==="; date; hostname
echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/40_behavioral_codeword_eval.py \
  --bench "$DSBENCH" --codeword-summary "$DSCWSUM" --model "$DSMODEL" \
  --out-root doublespeak_causality/outputs --k "$DSK" --n-bases "$DSNBASES" \
  --demo-style "$DSSTYLE" --n-demos "$DSNDEMOS" --max-new-tokens "$DSMAXTOK" --include-neutral "${DSNEUTRAL:-true}"
echo "=== done ==="; date
