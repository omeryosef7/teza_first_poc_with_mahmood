#!/bin/bash
#
# Parallel array version of stage6_qwen3_14b_batch_full_all.slurm.
# Splits examples across N_JOBS parallel jobs, each on its own 2-GPU node.
#
# Submit with:
#   INPUT_JSONL=outputs/... OUT_DIR=outputs/stage6/all_traces_full_1_11 MAX_NEW_TOKENS=32768 \
#   sbatch slurm_scripts/stage6_qwen3_14b_batch_full_array.slurm
#
# Each job writes to the same OUT_DIR but processes a non-overlapping slice,
# so there are no write conflicts.

#SBATCH --job-name=poc_stage6_qwen3_full_arr
#SBATCH --output=logs/poc_stage6_qwen3_full_arr_%A_%a.out
#SBATCH --error=logs/poc_stage6_qwen3_full_arr_%A_%a.err
#SBATCH --array=0-3
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-302,n-303,n-304,n-305

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

INPUT_JSONL="${INPUT_JSONL:-$PROJECT_DIR/outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl}"
OUT_DIR="${OUT_DIR:-$PROJECT_DIR/outputs/stage6/all_traces_full}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3-14B}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-32768}"
TOTAL_EXAMPLES="${TOTAL_EXAMPLES:-220}"
N_JOBS=4
RUN_JUDGE="${RUN_JUDGE:-true}"

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

echo "=== Stage 6 array job started: task ${SLURM_ARRAY_TASK_ID}/${N_JOBS} ==="
date
hostname
echo "SLURM_JOB_ID=$SLURM_JOB_ID  ARRAY_TASK_ID=$SLURM_ARRAY_TASK_ID"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""
echo "INPUT_JSONL=$INPUT_JSONL"
echo "OUT_DIR=$OUT_DIR"
echo "MODEL_NAME=$MODEL_NAME"
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
    --max-new-tokens "$MAX_NEW_TOKENS"
    --no-redact
    --start-index "$START_INDEX"
    --end-index "$END_INDEX"
)

if [ "$RUN_JUDGE" = "true" ]; then
    ARGS+=(--run-judge)
fi

echo ""
echo "=== Running batch exporter (slice $START_INDEX-$END_INDEX) ==="
python -m poc_stage6.batch_redacted_export_all "${ARGS[@]}"

echo ""
echo "=== Stage 6 array task ${SLURM_ARRAY_TASK_ID} finished ==="
date
