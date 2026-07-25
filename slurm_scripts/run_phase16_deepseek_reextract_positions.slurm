#!/bin/bash
#SBATCH --job-name=ds_reextract_pos
#SBATCH --output=logs/ds_reextract_pos_%j.out
#SBATCH --error=logs/ds_reextract_pos_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --constraint=l40s
#SBATCH --exclude=n-804,n-602,n-301,n-801,n-802
#SBATCH --requeue

# §16 REPAIR — re-replay the EXISTING DeepSeek-R1 generation shards with the fixed
# think-marker config (deepseek_r1 emits <think> in the prefill; see
# poc_stage4/model_family_utils.THINK_START_IN_PREFILL_BY_FAMILY). We DO NOT re-generate
# (generation is sampled → would change success labels); we only recompute the segmentation
# positions from the ALREADY-SAVED generation tokens via replay --recompute-positions and
# re-slice the residual streams. Output goes to a FRESH dir so the original extraction is
# preserved for comparison and every row is re-replayed (skip-guard keys off an empty dir).
#
# SINGLE job, all shards in ONE python invocation → the model loads ONCE (replay_hidden_states
# multi-shard mode) and every shard replays through it. Weights are READ OFFLINE from the project
# cache (§31.3-A) — nothing is downloaded, so the earlier node-local disk/download failures are moot.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
# Model-family-parameterized (default deepseek_r1). Reused for phi4 (Phi-4 marker-fix re-replay):
#   MODEL_FAMILY=phi4 RUN_DIR=outputs/phase_phi4_cot/extraction OUT_DIR=outputs/phase_phi4_cot/extraction_fixed
MODEL_FAMILY="${MODEL_FAMILY:-deepseek_r1}"
RUN_DIR="${RUN_DIR:-outputs/phase16_deepseek_cot_heldout25/extraction}"
OUT_DIR="${OUT_DIR:-outputs/phase16_deepseek_cot_heldout25/extraction_fixed}"
GEN_DIR="$RUN_DIR/generation/shards"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$OUT_DIR"

# §31.3-A (Claude extension, user-authorized 2026-07-23): the L40S nodes provide NO node-local scratch
# (sinfo TMP_DISK=0 cluster-wide; /tmp free 1-9GB << 15GB model), so §31.3's node-local-ephemeral rule
# is infeasible for non-Qwen3 models here. Option A: READ the weights ALREADY PRESENT in the project
# cache (deepseek_r1 is fully cached, 15G) with HF_HUB_OFFLINE=1 — no NEW weights are ever downloaded or
# persisted (the original prohibition's intent is preserved). See plan §31.3-A amendment.
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
echo "[reextract] §31.3-A: reading $MODEL_FAMILY weights from project cache (offline) node=$(hostname) date=$(date -u)"

GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then echo "ERROR: expected L40S, got $GPU_NAME"; exit 1; fi

shopt -s nullglob
SHARDS=("$GEN_DIR"/${MODEL_FAMILY}_*.jsonl)
if [ "${#SHARDS[@]}" -eq 0 ]; then echo "[reextract] FATAL: no generation shards in $GEN_DIR" >&2; exit 1; fi
echo "[reextract] ${#SHARDS[@]} generation shards → recompute positions into $OUT_DIR (single model load)"

# Pass ALL shards in ONE invocation: the model loads ONCE (from the offline project cache) and every
# shard replays through the preloaded weights — no per-shard reload.
python -u -m poc_stage_ae.replay_hidden_states \
    --model "$MODEL_FAMILY" \
    --generation-shard "${SHARDS[@]}" \
    --output-dir "$OUT_DIR" --recompute-positions
echo "[reextract] DONE date=$(date -u)"
