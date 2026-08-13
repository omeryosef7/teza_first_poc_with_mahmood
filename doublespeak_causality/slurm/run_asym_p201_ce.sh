#!/bin/bash
#SBATCH --job-name=asym_ce
#SBATCH --output=doublespeak_causality/logs/asym_ce_%j.out
#SBATCH --error=doublespeak_causality/logs/asym_ce_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=2:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806

# §20.1 post-hoc CE scoring of frozen soft prompts. One model load scores every arm.
#   sbatch --export=ALL,ARM_DIRS="dirA dirB dirC" doublespeak_causality/slurm/run_asym_p201_ce.sh
# All arms in one contrast MUST be scored in a single job -- the script asserts they share
# model/manifest/layer, and a shared model load removes any load-order confound.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
: "${ARM_DIRS:?set ARM_DIRS to a space-separated list of asym_p2_soft_* dirs}"
: "${ASYM_GPU:=l40s}"
: "${CE_OUT:=doublespeak_causality/outputs/asym_p201_ce_scores.json}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
GPU_TYPE="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
case "$(echo "$GPU_TYPE" | tr 'A-Z' 'a-z')" in
  *"$ASYM_GPU"*) echo "GPU ok: $GPU_TYPE (required class: $ASYM_GPU)";;
  *) echo "ERROR need $ASYM_GPU got '$GPU_TYPE'"; exit 1;;
esac

# Fail loudly if an arm dir is missing its frozen solution, rather than scoring a subset.
ARGS=()
for d in $ARM_DIRS; do
  [ -f "$d/soft_suffix.pt" ] || { echo "ERROR: $d has no soft_suffix.pt"; exit 1; }
  [ -f "$d/RUNMETA.json" ]   || { echo "ERROR: $d has no RUNMETA.json"; exit 1; }
  ARGS+=(--arm-dir "$d")
done
echo "scoring ${#ARGS[@]} args over $(echo $ARM_DIRS | wc -w) arms"

python -u doublespeak_causality/scripts/asym_p201_score_ce.py "${ARGS[@]}" --out "$CE_OUT"
echo "=== done $(date -u) ==="
