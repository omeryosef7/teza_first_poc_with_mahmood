#!/bin/bash
#SBATCH --job-name=gcg_perprompt
#SBATCH --output=logs/gcg_perprompt_%j.out
#SBATCH --error=logs/gcg_perprompt_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=16:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1

# =====================================================================================
# ASYMMETRY SPRINT §7.5 — PER-PROMPT GCG (per Mahmood).
# One suffix optimized INDEPENDENTLY for each prompt, vs the universal-suffix matrix.
#
# Select via --export=ALL,ARM=<name>,SEED=<n>,SHARD=<i>,NSHARD=<k>  (NO commas in values,
# per the sbatch --export comma bug).
#   ARM in: vanilla | mechanism | matched_random
#   SHARD/NSHARD split the 37 prompts across <=6 concurrent jobs (SHARD is 0-based).
#   N_STEPS=200 is the full-budget arm; N_STEPS=5 is the COMPUTE-MATCHED arm
#     (200 universal steps / 37 prompts ~= 5), which §7.5 requires alongside it --
#     a per-prompt arm at 200 steps/prompt spends ~37x the universal arm's compute,
#     so "per-prompt beats universal" is uninterpretable without both.
#
# Everything scientific is held identical to the universal matrix (suffix_len 16, topk 256,
# --no-filter-cand, --suffix-placement user, --selection-mode weighted, --no-thinking).
# The ONLY difference is that each job optimizes against a 1-ROW manifest.
#
# D1/D2: at n=1 legacy_fixed collapses to per_task_suffix (its index comes from the only
# prompt), but that is still NOT the decision position -- D2 persists. So the mechanism arm
# passes --refusal-dir-position-mode per_task_decision, matching asym_p3_arm07p*.
#
# TWO SILENT FAILURE MODES this script guards (both otherwise exit 0 with garbage):
#   1. split!=train without --split all  -> empty train list -> loop breaks at step 0 ->
#      EMPTY ITERATION_LOG, exit 0.  The joblist carries the correct flag; we assert after.
#   2. config_hash() excludes manifest_path AND output_dir, so two prompts sharing an
#      output dir load each other's checkpoint with NO mismatch. The splitter asserts
#      unique dirs; we re-assert the manifest copied into each dir has exactly 1 row.
# =====================================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"

ARM="${ARM:?must set ARM}"; SEED="${SEED:-42}"
N_STEPS="${N_STEPS:-200}"; LAMBDA_R="${LAMBDA_R:-0.25}"
SHARD="${SHARD:-0}"; NSHARD="${NSHARD:-1}"
SPLIT_NAME="${SPLIT_NAME:-test}"
SUFFIX_LEN=16; BATCH="${BATCH:-64}"; TOPK=256; SUBB="${SUBB:-8}"

MODEL_FAMILY="llama"; MODEL_PATH="meta-llama/Llama-3.1-8B-Instruct"
DS_MAN="${DC}/data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak.jsonl"
R_L18="${DC}/outputs/refusal_alllayers/refusal_direction_llama_L18.pt"
R_RAND_L18="${DC}/outputs/gate7_v3_randdirs/refusal_rand_L18_normmatched_seed20260809.pt"
OUT_BASE="${PROJECT_DIR}/outputs/stage_gcg_perprompt"
PP_DATA="${DC}/data/gcg/clearharm_llama_v3/perprompt_${SPLIT_NAME}"

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p logs "$OUT_BASE" "$PP_DATA"
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "ARM=$ARM SEED=$SEED N_STEPS=$N_STEPS SHARD=$SHARD/$NSHARD SPLIT=$SPLIT_NAME"
echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
# The probe is split out of the assignment on purpose. As `VRAM_MB=$(nvidia-smi ... )` under
# `set -e`, a probe that exits non-zero aborts the whole job AT THE ASSIGNMENT with the probe's
# own exit code -- so the ERROR branch below was unreachable dead code, and `2>/dev/null` threw
# away the only diagnostic. That is what killed 757702 (14 s, exit 13, empty stderr, no guard
# line) on rack-gww-dgx1. Keep stderr, keep going, and let the guard do the deciding.
NV_RC=0
NV_OUT=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>&1) || NV_RC=$?
VRAM_MB=$(printf '%s\n' "$NV_OUT" | awk 'NR==1{print $1}')
if [ "$NV_RC" -ne 0 ]; then
    echo "ERROR: nvidia-smi probe failed rc=${NV_RC}: ${NV_OUT}"; exit 1; fi
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then
    echo "ERROR: GPU unusable or <20GB (vram='${VRAM_MB}MB')"; exit 1; fi
echo "[guard] GPU OK ${VRAM_MB}MB (BATCH=$BATCH)"

# Budget tag keeps the compute-matched arm from colliding with the full-budget checkpoints.
# Written as an if-statement rather than `[ ... ] && BUDTAG=...` on purpose. Under `set -e`
# the && form is harmless HERE (a failing test mid-script does not abort), but it exits 1 if it
# ever becomes the last command of a script or function -- which would mark the SLURM job FAILED
# after the work completed. The if-form is immune to that refactor.
BUDTAG=""
if [ "$N_STEPS" != "200" ]; then BUDTAG="_s${N_STEPS}"; fi
ARMTAG="asym_p75_${ARM}${BUDTAG}"

case "$ARM" in
  vanilla)        OBJ=(--lambda-refusal-dir 0 --no-repr-in-selection);;
  mechanism)      OBJ=(--lambda-refusal-dir "$LAMBDA_R" --refusal-dir-layer 19 --refusal-dir-path "$R_L18"
                       --refusal-dir-position-mode per_task_decision --objective-name pp_refusal_down_L18
                       --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  matched_random) OBJ=(--lambda-refusal-dir "$LAMBDA_R" --refusal-dir-layer 19 --refusal-dir-path "$R_RAND_L18"
                       --refusal-dir-position-mode per_task_decision --objective-name pp_refusal_rand_L18
                       --repr-in-selection --repr-selection-sub-batch "$SUBB");;
  *) echo "ERROR unknown ARM=$ARM"; exit 1;;
esac

# --- Build the 1-row manifests + joblist (idempotent; data only, no GPU) --------------
JOBLIST="${PP_DATA}/joblist_${ARMTAG}_seed${SEED}.jsonl"
python "${DC}/scripts/split_manifest_perprompt.py" \
    --manifest "$DS_MAN" --split "$SPLIT_NAME" --out-dir "$PP_DATA" \
    --joblist "$JOBLIST" --run-root "$OUT_BASE" --arm "$ARMTAG" --seed "$SEED"

NJOBS=$(wc -l < "$JOBLIST")
echo ">>> $NJOBS prompts total; this job runs shard $SHARD of $NSHARD"

COMMON=(--model-family "$MODEL_FAMILY" --model-name-or-path "$MODEL_PATH"
        --suffix-length "$SUFFIX_LEN" --n-steps "$N_STEPS" --batch-size "$BATCH" --topk "$TOPK"
        --seed "$SEED" --no-filter-cand --suffix-placement user
        --selection-mode weighted --no-thinking --checkpoint-every 10 --snapshot-every 50)

i=0; ran=0; skipped=0
while IFS= read -r line; do
    if [ $(( i % NSHARD )) -ne "$SHARD" ]; then i=$((i+1)); continue; fi
    i=$((i+1))
    TASK_ID=$(echo "$line"   | python -c 'import json,sys; print(json.loads(sys.stdin.read())["task_id"])')
    PP_MAN=$(echo "$line"    | python -c 'import json,sys; print(json.loads(sys.stdin.read())["manifest"])')
    PP_OUT=$(echo "$line"    | python -c 'import json,sys; print(json.loads(sys.stdin.read())["output_dir"])')
    PP_RID=$(echo "$line"    | python -c 'import json,sys; print(json.loads(sys.stdin.read())["run_id"])')
    PP_SPLIT=$(echo "$line"  | python -c 'import json,sys; print(json.loads(sys.stdin.read())["split_flag"])')

    if [ -f "${PP_OUT}/FINAL_CANDIDATES.jsonl" ]; then
        skipped=$((skipped+1)); echo "[pp] SKIP done ${PP_RID}"; continue
    fi
    # GUARD 2: the manifest must be exactly one row, or this is not a per-prompt run.
    NROW=$(wc -l < "$PP_MAN")
    [ "$NROW" -eq 1 ] || { echo "ERROR ${PP_MAN} has $NROW rows, expected 1"; exit 1; }

    mkdir -p "$PP_OUT"
    echo "[pp] ($i/$NJOBS) RUN ${PP_RID}  split_flag=${PP_SPLIT}  $(date -u +%H:%M:%S)"
    # `< /dev/null`: this loop's stdin IS the joblist; without it a child that reads stdin
    # would silently swallow the remaining prompts.
    python -m poc_stage_gcg_early.run_optimization \
        --run-id "$PP_RID" --manifest "$PP_MAN" --output-dir "$PP_OUT" \
        --split "$PP_SPLIT" "${COMMON[@]}" "${OBJ[@]}" < /dev/null

    # GUARD 1: an empty ITERATION_LOG means the train list was empty (exit code was still 0).
    python - "$PP_OUT" "$N_STEPS" <<'PYEOF'
import json, sys, pathlib
out, want = pathlib.Path(sys.argv[1]), int(sys.argv[2])
p = out / "ITERATION_LOG.jsonl"
rows = [json.loads(l) for l in open(p)] if p.exists() else []
if not rows:
    raise SystemExit(f"FATAL {out.name}: EMPTY ITERATION_LOG -- empty train list (see guard 1)")
bad = {r.get("n_train_tasks") for r in rows} - {1}
if bad:
    raise SystemExit(f"FATAL {out.name}: n_train_tasks={bad}, expected 1 -- not a per-prompt run")
if len(rows) < want:
    print(f"[pp][warn] {out.name}: {len(rows)}/{want} steps (resumable)", flush=True)
print(f"[pp][ok] {out.name}: {len(rows)} steps, n_train_tasks=1", flush=True)
PYEOF
    ran=$((ran+1))
done < "$JOBLIST"

echo "Done ARM=$ARM seed=$SEED shard=$SHARD: ran=$ran skipped=$skipped at $(date -u)"
