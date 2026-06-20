#!/bin/bash

#SBATCH --job-name=poc_stage4_subspace_stats
#SBATCH --output=logs/poc_stage4_subspace_stats_%j.out
#SBATCH --error=logs/poc_stage4_subspace_stats_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602,n-302,n-303,n-304,n-305

# Stage 4 subspace dynamics statistical analysis — CPU-only.
# Runs analyze_subspace_dynamics_stats.py on the output of
# analyze_token_dynamics_subspace.py (token_level_metrics.jsonl).
# No GPU required; streams the file rather than loading it all at once.
#
# INPUT_VARIANT controls which track to analyse:
#   "behavioral" (default): outputs/stage4/qwen3-14b/token_dynamics_subspace_behavioral/
#   "endofthink":           outputs/stage4/qwen3-14b/token_dynamics_subspace_endofthink/
#
# To run both variants back-to-back, submit twice with INPUT_VARIANT=behavioral and
# INPUT_VARIANT=endofthink, or use the submit_stage4_stats_chain.sh helper.
#
# FOCUS_LAYERS: comma-separated layer indices to include in statistics.
#   Default: "manifest" = use the K subspace layers listed in manifest.json.
#   Set to "all" to include all 40 layers (slower, larger outputs).
#
# Usage examples:
#   sbatch slurm_scripts/stage4_subspace_stats.slurm
#   INPUT_VARIANT=endofthink sbatch slurm_scripts/stage4_subspace_stats.slurm
#   INPUT_VARIANT=behavioral FOCUS_LAYERS=all sbatch slurm_scripts/stage4_subspace_stats.slurm
#   N_BINS=20 sbatch slurm_scripts/stage4_subspace_stats.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_VARIANT="${INPUT_VARIANT:-behavioral}"  # "behavioral", "endofthink", or "startofthink"
N_BINS="${N_BINS:-10}"
FOCUS_LAYERS="${FOCUS_LAYERS:-manifest}"  # "manifest" | "all" | "0,3,20,21,22,23,26"
NO_PLOTS="${NO_PLOTS:-false}"

# Resolve input/output dirs from variant
if [ "$INPUT_VARIANT" = "endofthink" ]; then
    DEFAULT_DYN_DIR="$PROJECT_DIR/outputs/stage4/qwen3-14b/token_dynamics_subspace_endofthink"
    DEFAULT_OUT_DIR="$PROJECT_DIR/outputs/stage4/qwen3-14b/subspace_stats_endofthink"
    VARIANT_LABEL="endofthink"
elif [ "$INPUT_VARIANT" = "startofthink" ]; then
    DEFAULT_DYN_DIR="$PROJECT_DIR/outputs/stage4/qwen3-14b/token_dynamics_subspace_startofthink"
    DEFAULT_OUT_DIR="$PROJECT_DIR/outputs/stage4/qwen3-14b/subspace_stats_startofthink"
    VARIANT_LABEL="startofthink"
else
    DEFAULT_DYN_DIR="$PROJECT_DIR/outputs/stage4/qwen3-14b/token_dynamics_subspace_behavioral"
    DEFAULT_OUT_DIR="$PROJECT_DIR/outputs/stage4/qwen3-14b/subspace_stats_behavioral"
    VARIANT_LABEL="behavioral"
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

ARGS=(
    --token-dynamics-dir "$TOKEN_DYN_DIR"
    --variant-name "$VARIANT_LABEL"
    --output-dir "$OUTPUT_DIR"
    --n-bins "$N_BINS"
)

# Resolve focus_layers
if [ "$FOCUS_LAYERS" = "manifest" ]; then
    : # default behaviour — script reads from manifest.json
elif [ "$FOCUS_LAYERS" = "all" ]; then
    ARGS+=(--focus-layers all)
else
    ARGS+=(--focus-layers "$FOCUS_LAYERS")
fi

if [ "$NO_PLOTS" = "true" ]; then
    ARGS+=(--no-plots)
fi

python -m poc_stage4.analyze_subspace_dynamics_stats "${ARGS[@]}"
