#!/bin/bash

#SBATCH --job-name=poc_s4a1_q3_hvp_eot
#SBATCH --output=logs/poc_stage4a1_qwen3_hvp_endofthink_%j.out
#SBATCH --error=logs/poc_stage4a1_qwen3_hvp_endofthink_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602

# Stage 4A1 ptype_vs_puzzle (Qwen3-14B): harmless vs puzzle at endofthink.
# Contrast: mean(puzzle_at_</think>) − mean(harmless_at_</think>)
# Group A: harmless prompts, generation required until </think> appears
# Group B: all 220 puzzle attack traces (from artifacts, no generation)
# Output: outputs/stage4/qwen3-14b/refusal_direction_hvp_endofthink/

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="${MODEL_FAMILY:-qwen3}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
STAGE6_INPUT="${STAGE6_INPUT:-$PROJECT_DIR/outputs/stage6/all_traces_full_1_11}"
BASELINE_JSONL="${BASELINE_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_1_11_strongreject.jsonl}"
GROUP_A_TYPE="harmless"
POSITION="endofthink"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/outputs/stage4/qwen3-14b/refusal_direction_hvp_endofthink}"
NUM_GROUP_A="${NUM_GROUP_A:-64}"
MAX_GEN_TOKENS="${MAX_GEN_TOKENS:-8192}"
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

mkdir -p logs "$OUTPUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

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

echo "[stage4a1_qwen3_hvp_endofthink] Starting at $(date) on $(hostname)"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true

ARGS=(
    --model-family "$MODEL_FAMILY"
    --model-name "$MODEL_NAME"
    --stage6-input "$STAGE6_INPUT"
    --group-a-type "$GROUP_A_TYPE"
    --position "$POSITION"
    --output-dir "$OUTPUT_DIR"
    --num-group-a "$NUM_GROUP_A"
    --max-generation-tokens "$MAX_GEN_TOKENS"
    --seed "$SEED"
)

if [ "$DRY_RUN" = "true" ]; then ARGS+=(--dry-run); fi
if [ "$RESUME" = "true" ]; then ARGS+=(--resume); fi

python -m poc_stage4.extract_refusal_direction_ptype_vs_puzzle "${ARGS[@]}"

echo "[stage4a1_qwen3_hvp_endofthink] Done at $(date)"
