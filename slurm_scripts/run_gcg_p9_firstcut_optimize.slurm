#!/bin/bash

#SBATCH --job-name=gcg_p9_firstcut
#SBATCH --output=logs/gcg_p9_firstcut_%j.out
#SBATCH --error=logs/gcg_p9_firstcut_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805

# =====================================================================================
# Gate-7 (§14-18) MINIMAL FIRST-CUT — optimization step (4 arms, seed 42, sequential).
# Ref: reports/GATE7_EXECUTION_PLAN.md §6 ; deviation BUG_AND_DEVIATION_LOG.md 2026-08-08.
#
# Goal: PROVE the objective-in-selection GCG pipeline end-to-end and get an early signal
# BEFORE the full 16-arm x 3-seed matrix. NOT a full result.
#
# ARMS (all: --split train=44 items, suffix_length=16, topk=256, batch_size=64, seed=42,
#       --no-filter-cand, --suffix-placement user, --selection-mode weighted, --no-thinking;
#       manifest = clearharm_llama_doublespeak.jsonl v1):
#   arm04            vanilla GCG baseline (task-only: lambda_refusal_dir=0, no repr-in-selection)
#   arm07-L18        refusal-suppression at VALIDATED L18   (objective refusal_down_L18)
#   arm07-L22        refusal-suppression at FROZEN/unvalidated L22 (objective refusal_down_L22)
#   arm07-rand-L18   specificity control: norm-matched RANDOM dir at L18 (objective refusal_rand_L18)
#
# BOTH-DIRECTIONS deviation (user-approved 2026-08-08): the frozen manifest specifies arm07 at
# L22 with an UNVALIDATED refusal_alllayers vector; P7 validates L18 in both direction families.
# We run BOTH (L22 frozen AND L18 validated) on the SAME v1 GCG manifest (no v3-GCG manifest
# exists) so the comparison isolates the L18-vs-L22 direction axis with the split held at v1.
#
# COMPUTE REDUCTION (first-cut, documented per plan §5):
#   * n_steps reduced 200 -> 100 to bound compute to ~6-8 GPU-h across all 4 arms.
#     Full-plan cost = 200*64*44 = 563,200 fwd/arm (~1.6 GPU-h). Here 100*64*44 = 281,600
#     fwd/arm (~0.8 GPU-h baseline); the 3 refusal arms add repr-in-selection overhead
#     (candidate hidden states, sub-batch 8) ~1.5-2x, so total ~5-6 GPU-h opt. + model loads.
#   * Items NOT capped: full 44 train items retained (>=20/cell satisfied; better early signal).
#   * seed 42 only (first-cut); full matrix runs 42/43/44 later.
#   * Checkpoint-every 10 => a wall-time timeout is resumable (re-submit, same run-id).
#
# LAMBDA: LAMBDA_REFUSAL_DIR default 0.25. Source/justification: Phase 8.1 alpha calibration
#   (reports/PHASE8_1_ALPHA_CALIBRATION.md, outputs/alpha_calibration.json) selected the
#   refusal-ablation operating point at alpha=0.25 on clearharm (sole qualifying dose: in-band
#   ASR + max headroom I_max=+0.477). NOTE: alpha there is an ABLATION intervention strength
#   (h - alpha*proj*d), which is NOT the same knob as the GCG loss weight lambda_refusal_dir;
#   there is no exact alpha->lambda map. 0.25 is also consistent with the project's prior GCG
#   precedent (gcg_full ... lambda03 used lambda_refusal_dir=0.3). It is a PRINCIPLED first-cut
#   starting value only and MUST be train/dev-swept (e.g. 3-point sweep) for the real run.
#   Override at submit time: sbatch --export=ALL,LAMBDA_REFUSAL_DIR=0.3 ...
#
# DO NOT SUBMIT without human go-ahead. No SLURM deps (chain by hand): run this, then the
# generation+StrongREJECT eval step separately.
# =====================================================================================

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

MODEL_FAMILY="llama"
MODEL_PATH="meta-llama/Llama-3.1-8B-Instruct"
MANIFEST="${PROJECT_DIR}/doublespeak_causality/data/gcg/clearharm_llama/clearharm_llama_doublespeak.jsonl"

# Shared hyperparameters (first-cut)
SUFFIX_LEN="${SUFFIX_LEN:-16}"
N_STEPS="${N_STEPS:-100}"          # reduced 200->100 for first-cut (see header)
BATCH_SIZE="${BATCH_SIZE:-64}"
TOPK="${TOPK:-256}"
SEED="${SEED:-42}"
LAMBDA_REFUSAL_DIR="${LAMBDA_REFUSAL_DIR:-0.25}"   # see LAMBDA note in header
REPR_SEL_SUB_BATCH="${REPR_SEL_SUB_BATCH:-8}"

# Direction vectors
DIR_L18_VALID="${PROJECT_DIR}/doublespeak_causality/outputs/refval_clearharm_20260806_051728_721957/refusal_direction_clearharm_L18.pt"
DIR_L22_FROZEN="${PROJECT_DIR}/doublespeak_causality/outputs/refusal_alllayers/refusal_direction_llama_L22.pt"
DIR_RAND_L18="${PROJECT_DIR}/doublespeak_causality/outputs/gate7_firstcut/refusal_rand_L18_normmatched_seed20260808.pt"

OUT_BASE="${PROJECT_DIR}/outputs/stage_gcg_full"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs "$OUT_BASE"

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export TRITON_CACHE_DIR="${PROJECT_DIR}/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "========================================================"
echo "  Gate-7 first-cut — GCG optimization (4 arms, seed ${SEED})"
echo "========================================================"
echo "SLURM_JOB_ID:      ${SLURM_JOB_ID:-NA}"
echo "SLURM_NODELIST:    ${SLURM_NODELIST:-NA}"
echo "n_steps:           ${N_STEPS} (reduced 200->100 for first-cut)"
echo "batch_size:        ${BATCH_SIZE}   topk: ${TOPK}   suffix_len: ${SUFFIX_LEN}"
echo "lambda_refusal:    ${LAMBDA_REFUSAL_DIR} (P8.1 alpha=0.25 proxy; MUST be swept for real run)"
echo "manifest:          ${MANIFEST} (--split train = 44 items)"
echo "GIT_REVISION:      $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:              $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# --- strict L40S guard ---
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: '${GPU_NAME}'. Aborting."
    exit 1
fi
echo "[guard] L40S confirmed: ${GPU_NAME}"

# Sanity: required inputs exist before spending compute
for f in "$MANIFEST" "$DIR_L18_VALID" "$DIR_L22_FROZEN" "$DIR_RAND_L18"; do
    if [ ! -f "$f" ]; then echo "ERROR: missing required input: $f"; exit 1; fi
done

run_arm () {
    local run_id="$1"; shift
    local out_dir="${OUT_BASE}/${run_id}"
    mkdir -p "$out_dir"
    echo ""
    echo ">>> ARM ${run_id}"
    if [ -f "${out_dir}/checkpoint.pt" ]; then
        echo ">>> Resuming from checkpoint in ${out_dir}"
    else
        echo ">>> Starting fresh: ${out_dir}"
    fi
    python -m poc_stage_gcg_early.run_optimization \
        --run-id "$run_id" \
        --model-family "$MODEL_FAMILY" \
        --model-name-or-path "$MODEL_PATH" \
        --manifest "$MANIFEST" \
        --output-dir "$out_dir" \
        --suffix-length "$SUFFIX_LEN" \
        --n-steps "$N_STEPS" \
        --batch-size "$BATCH_SIZE" \
        --topk "$TOPK" \
        --seed "$SEED" \
        --split train \
        --no-filter-cand \
        --suffix-placement user \
        --selection-mode weighted \
        --no-thinking \
        --checkpoint-every 10 \
        --snapshot-every 50 \
        "$@"
    # Harness provenance: CONFIG.json/ENVIRONMENT.json written by run_optimization above;
    # audit_run writes AUDIT_REPORT.md + DONE (the GCG harness's run-metadata/provenance step).
    # NON-FATAL (|| true): audit_run exits non-zero on any issue (e.g. "no snapshots" when
    # n_steps<snapshot-every); under `set -euo pipefail` that would abort the whole multi-arm
    # run after the first arm (caught in smoke 732862 — only arm04 ran). The audit is diagnostic
    # provenance, not a gate, so a single arm's warning must not kill the remaining arms.
    python -m poc_stage_gcg_early.audit_run --run-dir "$out_dir" || echo "[audit] non-fatal issues for $out_dir (see AUDIT_REPORT.md)"
}

# --- arm04 — vanilla GCG baseline (task-only) ---
run_arm phase9_gcg_mac_matrix_arm04_gcg_vanilla_doublespeak_seed${SEED} \
    --lambda-refusal-dir 0 --no-repr-in-selection

# --- arm07-L18 — refusal-suppression, VALIDATED L18 (recommended) ---
run_arm phase9_gcg_mac_matrix_arm07_gcg_refusal_down_L18_seed${SEED} \
    --lambda-refusal-dir "$LAMBDA_REFUSAL_DIR" \
    --refusal-dir-layer 18 \
    --refusal-dir-path "$DIR_L18_VALID" \
    --objective-name refusal_down_L18 \
    --repr-in-selection --repr-selection-sub-batch "$REPR_SEL_SUB_BATCH"

# --- arm07-L22 — refusal-suppression, FROZEN/unvalidated L22 (honors original pre-reg) ---
run_arm phase9_gcg_mac_matrix_arm07_gcg_refusal_down_L22_seed${SEED} \
    --lambda-refusal-dir "$LAMBDA_REFUSAL_DIR" \
    --refusal-dir-layer 22 \
    --refusal-dir-path "$DIR_L22_FROZEN" \
    --objective-name refusal_down_L22 \
    --repr-in-selection --repr-selection-sub-batch "$REPR_SEL_SUB_BATCH"

# --- arm07-rand-L18 — specificity control: norm-matched RANDOM direction at L18 ---
run_arm phase9_gcg_mac_matrix_arm07_gcg_refusal_rand_L18_seed${SEED} \
    --lambda-refusal-dir "$LAMBDA_REFUSAL_DIR" \
    --refusal-dir-layer 18 \
    --refusal-dir-path "$DIR_RAND_L18" \
    --objective-name refusal_rand_L18 \
    --repr-in-selection --repr-selection-sub-batch "$REPR_SEL_SUB_BATCH"

echo ""
echo "Done: Gate-7 first-cut optimization (4 arms) at $(date -u)"
