#!/bin/bash

#SBATCH --job-name=poc_s4_stats_gemma
#SBATCH --output=logs/poc_stage4_subspace_stats_gemma_%j.out
#SBATCH --error=logs/poc_stage4_subspace_stats_gemma_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602,n-302,n-303,n-304,n-305

# Stage 4C subspace stats (Gemma 4): AUC and statistical analysis — CPU-only.
# Reads token_level_metrics.jsonl from Stage 4B output.
#
# INPUT_VARIANT controls which track to analyse:
#   "behavioral" (default): outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_behavioral/
#   "endofthink":           outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_endofthink/
#   "startofthink":         outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_startofthink/
#   "endofresponse":        outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_endofresponse/
#
# Submit once per variant:
#   sbatch slurm_scripts/stage4_subspace_stats_gemma.slurm
#   INPUT_VARIANT=endofthink sbatch slurm_scripts/stage4_subspace_stats_gemma.slurm
#   INPUT_VARIANT=startofthink sbatch slurm_scripts/stage4_subspace_stats_gemma.slurm
#   INPUT_VARIANT=endofresponse sbatch slurm_scripts/stage4_subspace_stats_gemma.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_VARIANT="${INPUT_VARIANT:-behavioral}"
N_BINS="${N_BINS:-10}"
FOCUS_LAYERS="${FOCUS_LAYERS:-manifest}"
NO_PLOTS="${NO_PLOTS:-false}"

# Resolve input/output dirs from variant
if [ "$INPUT_VARIANT" = "endofthink" ]; then
    DEFAULT_DYN_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_endofthink"
    DEFAULT_OUT_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/subspace_stats_endofthink"
    VARIANT_LABEL="endofthink"
elif [ "$INPUT_VARIANT" = "startofthink" ]; then
    DEFAULT_DYN_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_startofthink"
    DEFAULT_OUT_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/subspace_stats_startofthink"
    VARIANT_LABEL="startofthink"
elif [ "$INPUT_VARIANT" = "endofresponse" ]; then
    DEFAULT_DYN_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_endofresponse"
    DEFAULT_OUT_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/subspace_stats_endofresponse"
    VARIANT_LABEL="endofresponse"
elif [ "$INPUT_VARIANT" = "behavioral" ]; then
    DEFAULT_DYN_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_behavioral"
    DEFAULT_OUT_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/subspace_stats_behavioral"
    VARIANT_LABEL="behavioral"
else
    # Generic fallback for hvp_startofthink, dvp_endofthink, etc.
    DEFAULT_DYN_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/token_dynamics_subspace_${INPUT_VARIANT}"
    DEFAULT_OUT_DIR="$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/subspace_stats_${INPUT_VARIANT}"
    VARIANT_LABEL="${INPUT_VARIANT}"
fi

TOKEN_DYN_DIR="${TOKEN_DYN_DIR:-$DEFAULT_DYN_DIR}"
OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_OUT_DIR}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUTPUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export PYTHONUNBUFFERED=1

echo "[stage4_subspace_stats_gemma] Starting at $(date) on $(hostname)"
echo "[stage4_subspace_stats_gemma] INPUT_VARIANT=${INPUT_VARIANT}"

ARGS=(
    --token-dynamics-dir "$TOKEN_DYN_DIR"
    --variant-name "$VARIANT_LABEL"
    --output-dir "$OUTPUT_DIR"
    --n-bins "$N_BINS"
)

if [ "$FOCUS_LAYERS" = "manifest" ]; then
    :
elif [ "$FOCUS_LAYERS" = "all" ]; then
    ARGS+=(--focus-layers all)
else
    ARGS+=(--focus-layers "$FOCUS_LAYERS")
fi

if [ "$NO_PLOTS" = "true" ]; then
    ARGS+=(--no-plots)
fi

python -m poc_stage4.analyze_subspace_dynamics_stats "${ARGS[@]}"

echo "[stage4_subspace_stats_gemma] Done at $(date)"
