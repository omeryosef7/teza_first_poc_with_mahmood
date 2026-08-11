#!/bin/bash
#SBATCH --job-name=asym_p5
#SBATCH --output=doublespeak_causality/logs/asym_p5_%j.out
#SBATCH --error=doublespeak_causality/logs/asym_p5_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# ASYMMETRY SPRINT Phase 5 (plan §9): two-signal selective defense.
#
#   sbatch --export=ALL,ASYM_N=2,ASYM_GENSPLITS=test --time=01:30:00 slurm/run_asym_p5_defense.sh  # smoke
#   sbatch slurm/run_asym_p5_defense.sh                                                            # full
#   sbatch --export=ALL,ASYM_PROJ=<other summary.json> slurm/run_asym_p5_defense.sh                 # 2nd alpha
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

# v3b-train-fit projection summary (train n=85, matches the v3b bench this run uses).
# The prior Gate-F run used refproj_clearharm_20260804_162641_711392 (v1 bench, train n=44,
# alpha L18=2.83); pass that via ASYM_PROJ for a byte-comparable secondary dose.
: "${ASYM_PROJ:=doublespeak_causality/outputs/refproj_clearharm_20260809_155851_738761/summary.json}"
: "${ASYM_MODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${ASYM_LAYER:=18}"
: "${ASYM_N:=0}"
: "${ASYM_MAXNEW:=200}"
: "${ASYM_MALTHR:=0.5}"
: "${ASYM_GENSPLITS:=train,test}"
: "${ASYM_GPU:=l40s}"
: "${ASYM_SEED:=0}"
SPLITS="train,test"      # features (and thresholds) always need train

echo "=== ASYM P5 two-signal defense: n=$ASYM_N gen_splits=$ASYM_GENSPLITS thr=$ASYM_MALTHR ==="
date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"; echo "proj=$ASYM_PROJ"
test -f "$ASYM_PROJ" || { echo "ERROR missing proj summary $ASYM_PROJ"; exit 1; }
[ -n "${OPENAI_API_KEY:-}" ] || { echo "ERROR OPENAI_API_KEY unset -> StrongREJECT scores null"; exit 1; }
# GPU class guard (plan §3.1). Every Phase-5 contrast is WITHIN one job -- all six arms are
# derived from the same two generations per item -- so one class per run is what matters.
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
GPU_LC="$(echo "$GPU_TYPE" | tr 'A-Z' 'a-z')"
case "$GPU_LC" in
  *"$ASYM_GPU"*) echo "GPU ok: $GPU_TYPE (required class: $ASYM_GPU)";;
  *) echo "ERROR need $ASYM_GPU got '$GPU_TYPE'"; exit 1;;
esac

python -u doublespeak_causality/scripts/asym_p5_defense_2signal.py \
  --model "$ASYM_MODEL" --proj-summary "$ASYM_PROJ" --proj-split train \
  --layer "$ASYM_LAYER" --splits "$SPLITS" --gen-splits "$ASYM_GENSPLITS" \
  --mal-threshold "$ASYM_MALTHR" --max-new "$ASYM_MAXNEW" \
  --n "$ASYM_N" --seed "$ASYM_SEED" --save-gen
echo "=== done ==="; date
