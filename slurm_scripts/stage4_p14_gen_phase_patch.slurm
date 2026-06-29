#!/bin/bash

#SBATCH --job-name=stage4_p14
#SBATCH --output=logs/stage4_p14_%j.out
#SBATCH --error=logs/stage4_p14_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=20:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s

# Stage 4 P14: Generation-Phase Activation Patching.
#
# Tests whether injecting D-condition activations DURING GENERATION (not
# during prefill as in P6) can break the CoT hijacking attack.
#
# P6 showed prefill-phase patching is NON-CAUSAL. If the mechanism operates
# during thinking-phase generation, patching at that phase should break it.
#
# Conditions per example × layer:
#   gen_thinking_L{l}: inject D's last-pos hidden during all thinking tokens
#   gen_answer_L{l}:   inject D's last-pos hidden during all answer tokens
#
# Decision gate:
#   gen_thinking_L{l} breaks attack (ASR < 0.5) → attack mechanism during thinking
#   gen_answer_L{l} breaks attack → model commits to compliance in the answer phase
#   Both non-causal → mechanism is in prefill (contradicts P6 — unlikely)
#
# Usage (smoke: 2 examples, layer 26 only):
#   SMOKE=1 sbatch slurm_scripts/stage4_p14_gen_phase_patch.slurm
#
# Usage (full: all 11 examples, layers [10, 26]):
#   sbatch slurm_scripts/stage4_p14_gen_phase_patch.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

OUT_DIR="$PROJECT_DIR/outputs/stage4/p14_gen_phase_patch"
SMOKE_FLAG="${SMOKE:-0}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

mkdir -p logs "$OUT_DIR" \
    "$RUNTIME_DIR"/{config,data,runtime,ipython} \
    "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export PYTHONUNBUFFERED=1

echo "=== Stage 4 P14: Generation-Phase Activation Patching ==="
date
hostname
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || true
echo ""

if [ "$SMOKE_FLAG" = "1" ]; then
    echo "=== SMOKE MODE: 2 examples, layer 26, phases [thinking, answer] ==="
    SMOKE=1 python -m poc_stage4.run_generation_phase_patching \
        --model qwen3 \
        --n-examples 2 \
        --layers 26 \
        --phases thinking answer \
        --output-dir "$OUT_DIR"
else
    echo "=== FULL: all 11 pure_cot_hijack, layers [10, 26], phases [thinking, answer, full] ==="
    python -m poc_stage4.run_generation_phase_patching \
        --model qwen3 \
        --layers 10 26 \
        --phases thinking answer full \
        --output-dir "$OUT_DIR"
fi

echo ""
echo "=== P14 generation-phase patching complete ==="
date
