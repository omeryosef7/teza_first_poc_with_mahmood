#!/bin/bash
#
# Parallel array run for google/gemma-4-E4B-it Stage 6 token-trace.
# Splits 220 examples across 4 jobs, each on its own L40S node with 1 GPU.
# L40S only (46GB VRAM) — A5000 nodes (n-501,n-503) are 24GB and too small.
# 1 GPU per job — Gemma4 E4B-it fits on 1×L40S; 2-GPU splits cause CUDA errors.
# Thinking is ENABLED (enable_thinking=True, <|channel>thought markers).
# MAX_NEW_TOKENS=32768 — no truncation of thinking chains.
#
# Submit with:
#   sbatch slurm_scripts/stage6_gemma_batch_full_array.slurm
#
# Override defaults:
#   INPUT_JSONL=... OUT_DIR=... MAX_NEW_TOKENS=32768 sbatch ...

#SBATCH --job-name=stage6_gemma_full_arr
#SBATCH --output=logs/stage6_gemma_full_arr_%A_%a.out
#SBATCH --error=logs/stage6_gemma_full_arr_%A_%a.err
#SBATCH --array=0-1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-601,n-602

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_1_11_strongreject.jsonl}"
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/outputs/stage6/gemma_traces_full_1_11}"
MODEL_NAME="${MODEL_NAME:-google/gemma-4-E4B-it}"
MODEL_FAMILY="${MODEL_FAMILY:-gemma4}"
ENABLE_THINKING="${ENABLE_THINKING:-true}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32768}"
TOTAL_EXAMPLES="${TOTAL_EXAMPLES:-220}"
N_JOBS=2
RUN_JUDGE="${RUN_JUDGE:-true}"
STRICT_VALIDATION="${STRICT_VALIDATION:-true}"

# Compute this job's slice
PER_JOB=$(( (TOTAL_EXAMPLES + N_JOBS - 1) / N_JOBS ))
START_INDEX=$(( SLURM_ARRAY_TASK_ID * PER_JOB ))
END_INDEX=$(( START_INDEX + PER_JOB ))
if [ $END_INDEX -gt $TOTAL_EXAMPLES ]; then END_INDEX=$TOTAL_EXAMPLES; fi

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$OUT_DIR" "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="$HF_HUB_CACHE"
export TRANSFORMERS_CACHE="$HF_HUB_CACHE"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

echo "=== Stage 6 Gemma array job started: task ${SLURM_ARRAY_TASK_ID}/${N_JOBS} ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID  ARRAY_TASK_ID=$SLURM_ARRAY_TASK_ID"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""
echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUT_DIR=$OUT_DIR"
echo "MODEL_NAME=$MODEL_NAME"
echo "MODEL_FAMILY=$MODEL_FAMILY"
echo "ENABLE_THINKING=$ENABLE_THINKING"
echo "MAX_NEW_TOKENS=$MAX_NEW_TOKENS"
echo "Slice: examples[$START_INDEX:$END_INDEX]"

if [ ! -f "$INPUT_JSONL" ]; then
    echo "ERROR: INPUT_JSONL not found: $INPUT_JSONL"
    exit 1
fi

ARGS=(
    --input-jsonl "$INPUT_JSONL"
    --out-dir "$OUT_DIR"
    --model "$MODEL_NAME"
    --model-family "$MODEL_FAMILY"
    --max-new-tokens "$MAX_NEW_TOKENS"
    --no-redact
    --start-index "$START_INDEX"
    --end-index "$END_INDEX"
)

if [ "$ENABLE_THINKING" = "false" ]; then
    ARGS+=(--no-enable-thinking)
fi

if [ "$RUN_JUDGE" = "true" ]; then
    ARGS+=(--run-judge)
fi

if [ "$STRICT_VALIDATION" = "true" ]; then
    ARGS+=(--strict-generation-validation)
fi

echo ""
echo "=== Running batch exporter (slice $START_INDEX-$END_INDEX) ==="
python -m poc_stage6.batch_redacted_export_all "${ARGS[@]}"

echo ""
echo "=== Stage 6 Gemma array task ${SLURM_ARRAY_TASK_ID} finished ==="
date
