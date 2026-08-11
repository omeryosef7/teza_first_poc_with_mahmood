#!/bin/bash
#SBATCH --job-name=gcg_v3_arm
#SBATCH --output=logs/gcg_v3_arm_%j.out
#SBATCH --error=logs/gcg_v3_arm_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=16:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-301,n-304,n-307,n-801,n-802,n-803,n-804,n-805,t-806

# =====================================================================================
# NEXT sprint Phase-4 — ONE GCG optimization arm on the v3 leakage-0 split.
# Select the arm via  --export=ALL,ARM=<name>,SEED=<n>   (NO commas in export values;
# comma-bearing multilayer flags live INSIDE this script per the sbatch --export comma bug).
#
# ARM in: vanilla | vanilla_direct | refusal_L18 | refusal_rand_L18 | refusal_L12 |
#         refusal_L18_poscorr | refusal_rand_L18_poscorr  (asymmetry sprint Phase 3) |
#         refusal_rand_L12 | concept_L9 | concept_rand_L9 | combined | combined_rand
#
# OFF-BY-ONE FIX (Gate A): direction files named L{k} are fitted at hidden_states[k+1];
# GCG reads hidden_states[layer] directly, so we pass layer = k+1 for every direction arm.
#   refusal L18 -> hs 19 ; refusal L12 -> hs 13 ; concept L9 -> hs 10.
#
# Shared: 74-item v3 train pool (--split train), suffix_len 16, topk 256, bs 64,
#   --no-filter-cand --suffix-placement user --selection-mode weighted --no-thinking.
# Overridable env: N_STEPS (200), SEED (42), LAMBDA_R (0.25), LAMBDA_C (0.25).
# =====================================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"

ARM="${ARM:?must set ARM}"; SEED="${SEED:-42}"
N_STEPS="${N_STEPS:-200}"; LAMBDA_R="${LAMBDA_R:-0.25}"; LAMBDA_C="${LAMBDA_C:-0.25}"
# BATCH/N_STEPS compute-matched: batch64*200steps == batch32*400steps (same candidate-forwards).
# 24GB 3090 fits BATCH=32; 46GB L40S fits BATCH=64. Keep steps*batch CONSTANT across the matrix.
SUFFIX_LEN=16; BATCH="${BATCH:-64}"; TOPK=256; SUBB="${SUBB:-8}"

MODEL_FAMILY="llama"; MODEL_PATH="meta-llama/Llama-3.1-8B-Instruct"
# OPTIMIZATION pool = frozen cluster-diverse 40-item v3 train (keeps 200-step arms < 8h;
# full 74-train would exceed the wall limit). HELD-OUT EVAL uses the FULL v3 test (37 items).
DS_MAN="${DC}/data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak_trainpool40.jsonl"
DIR_MAN="${DC}/data/gcg/clearharm_llama_v3/clearharm_llama_direct_trainpool40.jsonl"
R_L18="${DC}/outputs/refusal_alllayers/refusal_direction_llama_L18.pt"
R_L12="${DC}/outputs/refusal_alllayers/refusal_direction_llama_L12.pt"
R_RAND_L18="${DC}/outputs/gate7_v3_randdirs/refusal_rand_L18_normmatched_seed20260809.pt"
R_RAND_L12="${DC}/outputs/gate7_v3_randdirs/refusal_rand_L12_normmatched_seed20260809.pt"
C_NEG_L9="${DC}/outputs/gate7_v3_conceptdirs/concept_neg_L9_unit.pt"
C_RAND_L9="${DC}/outputs/gate7_v3_conceptdirs/concept_rand_L9_normmatched_seed20260809.pt"
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
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "ARM=$ARM SEED=$SEED N_STEPS=$N_STEPS LAMBDA_R=$LAMBDA_R LAMBDA_C=$LAMBDA_C"
echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | awk 'NR==1{print;exit}')
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | awk 'NR==1{print;exit}')
# Min-VRAM guard (replaces strict L40S): GCG needs >=20GB. Use BATCH=64 on 46GB+ (L40S), BATCH=32 on 24GB (3090).
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then
    echo "ERROR: GPU unusable or <20GB (name='$GPU_NAME' vram='${VRAM_MB}MB')"; exit 1; fi
echo "[guard] GPU OK: $GPU_NAME ${VRAM_MB}MB (BATCH=$BATCH)"

# Common flags (array to preserve quoting)
COMMON=(--model-family "$MODEL_FAMILY" --model-name-or-path "$MODEL_PATH"
        --suffix-length "$SUFFIX_LEN" --n-steps "$N_STEPS" --batch-size "$BATCH" --topk "$TOPK"
        --seed "$SEED" --split train --no-filter-cand --suffix-placement user
        --selection-mode weighted --no-thinking --checkpoint-every 10 --snapshot-every 50)

case "$ARM" in
  vanilla)          MAN="$DS_MAN"; RID="phase9b_v3_arm04_vanilla_ds";        OBJ=(--lambda-refusal-dir 0 --no-repr-in-selection);;
  vanilla_direct)   MAN="$DIR_MAN"; RID="phase9b_v3_arm03_vanilla_direct";   OBJ=(--lambda-refusal-dir 0 --no-repr-in-selection);;
  refusal_L18)      MAN="$DS_MAN"; RID="phase9b_v3_arm07_refusal_down_L18";  OBJ=(--lambda-refusal-dir "$LAMBDA_R" --refusal-dir-layer 19 --refusal-dir-path "$R_L18"   --objective-name refusal_down_L18 --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  refusal_rand_L18) MAN="$DS_MAN"; RID="phase9b_v3_arm07r_refusal_rand_L18"; OBJ=(--lambda-refusal-dir "$LAMBDA_R" --refusal-dir-layer 19 --refusal-dir-path "$R_RAND_L18" --objective-name refusal_rand_L18 --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  refusal_L12)      MAN="$DS_MAN"; RID="phase9b_v3_arm10_refusal_down_L12";  OBJ=(--lambda-refusal-dir "$LAMBDA_R" --refusal-dir-layer 13 --refusal-dir-path "$R_L12"   --objective-name refusal_down_L12_jacpeak --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  # --- ASYMMETRY SPRINT Phase 3: position-corrected objective (defects D1+D2) --------------
  # Identical to refusal_L18 / refusal_rand_L18 in every respect EXCEPT that the refusal
  # projection is read at the LAST PROMPT TOKEN, recomputed PER TASK, instead of at one
  # absolute index taken from train_tasks[0] (correct for 1 of 40 prompts) that also sat 5
  # template tokens before the position where the axis was fitted and causally validated.
  # See doublespeak_causality/docs/ASYMMETRY_SPRINT_EXECUTION_LOG.md E0.3.
  # Gate B PREDICTS these still fail: the first-order surrogate is invalid at one-token step
  # size regardless of which position it reads. "Gate D was just a bug" predicts they succeed.
  refusal_L18_poscorr)      MAN="$DS_MAN"; RID="asym_p3_arm07p_refusal_down_L18_poscorr";  OBJ=(--lambda-refusal-dir "$LAMBDA_R" --refusal-dir-layer 19 --refusal-dir-path "$R_L18"      --refusal-dir-position-mode per_task_decision --objective-name refusal_down_L18_poscorr --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  refusal_rand_L18_poscorr) MAN="$DS_MAN"; RID="asym_p3_arm07pr_refusal_rand_L18_poscorr"; OBJ=(--lambda-refusal-dir "$LAMBDA_R" --refusal-dir-layer 19 --refusal-dir-path "$R_RAND_L18" --refusal-dir-position-mode per_task_decision --objective-name refusal_rand_L18_poscorr --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  refusal_rand_L12) MAN="$DS_MAN"; RID="phase9b_v3_arm10r_refusal_rand_L12"; OBJ=(--lambda-refusal-dir "$LAMBDA_R" --refusal-dir-layer 13 --refusal-dir-path "$R_RAND_L12" --objective-name refusal_rand_L12 --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  concept_L9)       MAN="$DS_MAN"; RID="phase9b_v3_arm06_concept_up_L9";     OBJ=(--lambda-refusal-dir "$LAMBDA_C" --refusal-dir-layer 10 --refusal-dir-path "$C_NEG_L9" --objective-name concept_up_L9 --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  concept_rand_L9)  MAN="$DS_MAN"; RID="phase9b_v3_arm06r_concept_rand_L9";  OBJ=(--lambda-refusal-dir "$LAMBDA_C" --refusal-dir-layer 10 --refusal-dir-path "$C_RAND_L9" --objective-name concept_rand_L9 --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  combined)         MAN="$DS_MAN"; RID="phase9b_v3_arm08_combined";          OBJ=(--refusal-dir-layers "10,19" --refusal-dir-paths "$C_NEG_L9,$R_L18"     --lambda-refusal-dir-per-layer "$LAMBDA_C,$LAMBDA_R" --objective-name concept_up_L9_refusal_down_L18 --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  combined_rand)    MAN="$DS_MAN"; RID="phase9b_v3_arm08r_combined_rand";    OBJ=(--refusal-dir-layers "10,19" --refusal-dir-paths "$C_RAND_L9,$R_RAND_L18" --lambda-refusal-dir-per-layer "$LAMBDA_C,$LAMBDA_R" --objective-name combined_rand --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  *) echo "ERROR unknown ARM=$ARM"; exit 1;;
esac

RUN_ID="${RID}_seed${SEED}"
OUT_DIR="${OUT_BASE}/${RUN_ID}"
mkdir -p "$OUT_DIR"
[ -f "$MAN" ] || { echo "ERROR missing manifest $MAN"; exit 1; }

echo ">>> RUN_ID=$RUN_ID"
python -m poc_stage_gcg_early.run_optimization \
    --run-id "$RUN_ID" --manifest "$MAN" --output-dir "$OUT_DIR" \
    "${COMMON[@]}" "${OBJ[@]}"
python -m poc_stage_gcg_early.audit_run --run-dir "$OUT_DIR" || echo "[audit] non-fatal for $OUT_DIR"
echo "Done ARM=$ARM seed=$SEED at $(date -u)"
