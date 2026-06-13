#!/bin/bash

#SBATCH --job-name=rl_cot_hijack
#SBATCH --output=logs/rl_experiment_%j.out
#SBATCH --error=logs/rl_experiment_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-803,n-804,n-805

# Online REINFORCE RL experiment — live Qwen3-14B mode.
#
# Runs the REINFORCE policy gradient loop with actual Qwen3-14B inference per episode.
# Each episode: policy selects condition → load research prompt → run model → StrongReject.
#
# Reward variant: cost_mechanistic (onset-timing-aware, links to delayed safety commitment).
#   Use --live-variant cost_l22_deflect for the L22-deflection variant.
#
# N_EPISODES: 48 episodes × ~12 min avg (float32 9.5 tok/s; cond A=23min, D=4min, F=3min) ≈ 9.6h worst case.
#   Each episode uses one of the existing Stage 4.7 research prompts (safe, no new content).
#
# Output: outputs/rl_experiment/run_${SLURM_JOB_ID}/
#
# Submit:
#   sbatch slurm_scripts/rl_experiment_live.slurm
#
# Override n-episodes at submission:
#   sbatch --export=ALL,N_EPISODES=32,RL_VARIANT=cost_asr slurm_scripts/rl_experiment_live.slurm

set -euo pipefail

REPO_ROOT="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

cd "${REPO_ROOT}"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"

if [ -f "${REPO_ROOT}/.env" ]; then
    set -a; source "${REPO_ROOT}/.env"; set +a
fi

# Parameters (can be overridden via --export)
N_EPISODES="${N_EPISODES:-48}"
RL_VARIANT="${RL_VARIANT:-cost_mechanistic}"
RL_SEED="${RL_SEED:-42}"
RL_LR="${RL_LR:-0.05}"
RUN_DIR="${SLURM_JOB_ID:-$(date +%Y%m%d_%H%M%S)}"
OUT_DIR="${REPO_ROOT}/outputs/rl_experiment/run_${RUN_DIR}"

mkdir -p "${REPO_ROOT}/logs"
mkdir -p "${OUT_DIR}"

echo "=== RL Experiment (Live Mode) ==="
echo "Job ID:    ${SLURM_JOB_ID:-local}"
echo "Out dir:   ${OUT_DIR}"
echo "Variant:   ${RL_VARIANT}"
echo "Episodes:  ${N_EPISODES}"
echo "LR:        ${RL_LR}"
echo "Seed:      ${RL_SEED}"
echo "Node:      $(hostname)"
echo "GPUs:      $(nvidia-smi --list-gpus 2>/dev/null | wc -l)"
echo "Started:   $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "=================================="

# Run the live RL experiment
python3 "${REPO_ROOT}/run_rl_experiment.py" \
    --out-dir "${OUT_DIR}" \
    --n-episodes "${N_EPISODES}" \
    --lr "${RL_LR}" \
    --seed "${RL_SEED}" \
    --live-eval \
    --live-variant "${RL_VARIANT}"

EXIT_CODE=$?

echo ""
echo "=== Finished ==="
echo "Exit code: ${EXIT_CODE}"
echo "Output:    ${OUT_DIR}"
echo "Ended:     $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "STATUS: SUCCESS"
    # Also run simulation mode to generate all 3 variant traces for comparison
    echo ""
    echo "Running simulation mode for full 3-variant report..."
    python3 "${REPO_ROOT}/run_rl_experiment.py" \
        --out-dir "${OUT_DIR}_sim" \
        --n-episodes 200 \
        --lr "${RL_LR}" \
        --seed "${RL_SEED}"
    echo "Simulation done: ${OUT_DIR}_sim"
else
    echo "STATUS: FAILED (exit ${EXIT_CODE})"
fi

exit ${EXIT_CODE}
