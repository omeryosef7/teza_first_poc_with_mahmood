#!/bin/bash

#SBATCH --job-name=poc_s4a1_g4_dvp_eor
#SBATCH --output=logs/poc_stage4a1_gemma_dvp_endofresponse_%j.out
#SBATCH --error=logs/poc_stage4a1_gemma_dvp_endofresponse_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602,n-302,n-303,n-304,n-305

# Stage 4A1 ptype_vs_puzzle (Gemma 4 E4B-it): direct_harm vs puzzle at endofresponse.
# Contrast: mean(puzzle_at_EOS) − mean(direct_harm_at_EOS)
# Group A: raw harmful goals, full response generation required
# Group B: all 220 Gemma puzzle attack traces (from artifacts, no generation)
# Output: outputs/stage4/gemma4-e4b-it/refusal_direction_dvp_endofresponse/

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/gemma_traces_full_1_11_eos_fixed}"
BASELINE_JSONL="${BASELINE_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_1_11_strongreject.jsonl}"
GROUP_A_TYPE="direct_harm"
POSITION="endofresponse"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/gemma4-e4b-it/refusal_direction_dvp_endofresponse}"
NUM_GROUP_A="${NUM_GROUP_A:-64}"
MAX_GEN_TOKENS="${MAX_GEN_TOKENS:-8192}"
MAX_SEQ_LEN="${MAX_SEQ_LEN:-20000}"
SEED="${SEED:-42}"
DRY_RUN="${DRY_RUN:-false}"
RESUME="${RESUME:-false}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUTPUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton} 2>/dev/null || true

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONUNBUFFERED=1

echo "[stage4a1_gemma_dvp_endofresponse] Starting at $(date) on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

ARGS=(
    --model-family "$MODEL_FAMILY"
    --model-name "$MODEL_NAME"
    --stage6-input "$STAGE6_INPUT"
    --baseline-jsonl "$BASELINE_JSONL"
    --group-a-type "$GROUP_A_TYPE"
    --position "$POSITION"
    --output-dir "$OUTPUT_DIR"
    --num-group-a "$NUM_GROUP_A"
    --max-generation-tokens "$MAX_GEN_TOKENS"
    --max-seq-len "$MAX_SEQ_LEN"
    --seed "$SEED"
)

if [ "$DRY_RUN" = "true" ]; then ARGS+=(--dry-run); fi
if [ "$RESUME" = "true" ]; then ARGS+=(--resume); fi

python -m poc_stage4.extract_refusal_direction_ptype_vs_puzzle "${ARGS[@]}"

echo "[stage4a1_gemma_dvp_endofresponse] Done at $(date)"
