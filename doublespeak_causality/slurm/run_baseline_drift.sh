#!/bin/bash
#SBATCH --job-name=ds_basedrift
#SBATCH --output=doublespeak_causality/logs/ds_basedrift_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_basedrift_%j.err
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
# §1.2 — GPU baseline / judge-noise drift envelope. GENERATION -> STRICT L40S.
# Every #SBATCH is a DEFAULT; override on the sbatch line (comma-lists stay in DEFAULTS, never --export).
#   SMOKE:  sbatch --export=ALL,DSN=2 doublespeak_causality/slurm/run_baseline_drift.sh
#   FULL v3b clearharm:  sbatch doublespeak_causality/slurm/run_baseline_drift.sh
#   FULL v3b generated:  sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral_v3b/beh_generated.json,DSCOHORT=generated doublespeak_causality/slurm/run_baseline_drift.sh
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
: "${DSBENCH:=doublespeak_causality/data/behavioral_v3b/beh_clearharm.json}"   # v3b has benign_prompt
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSSPLITS:=train,test}"      # comma-list DEFAULT
: "${DSREJUDGE:=3}"
: "${DSMAXNEW:=200}"
: "${DSN:=0}"
: "${DSSEED:=0}"
: "${DSENABLETHINK:=default}"     # thinking-model control (Qwen3/Phi-4): default|true|false
echo "=== baseline drift (§1.2): $DSMODEL bench=$DSBENCH rejudge=$DSREJUDGE maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/phase_baseline_drift.py \
  --bench "$DSBENCH" --model "$DSMODEL" --splits "$DSSPLITS" --rejudge "$DSREJUDGE" \
  --max-new "$DSMAXNEW" --n "$DSN" --seed "$DSSEED" --enable-thinking "$DSENABLETHINK"
echo "=== done ==="; date
