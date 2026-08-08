#!/bin/bash

#SBATCH --job-name=gcg_p9_firstcut_eval
#SBATCH --output=logs/gcg_p9_firstcut_eval_%j.out
#SBATCH --error=logs/gcg_p9_firstcut_eval_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-802,n-803,n-805,t-806

# Gate-7 first-cut EVAL (plan §17 / reports/GATE7_EXECUTION_PLAN.md §4 + §6-B).
#
# For each optimized arm run-dir, applies its GCG suffix (FINAL_CANDIDATES.jsonl row[0].suffix_str,
# suffix_placement=user) to the HELD-OUT (test) split of the clearharm_llama doublespeak manifest,
# generates GREEDILY (max_new=2048), StrongREJECT-judges, and writes a scalar per-arm summary
# (p9_heldout_asr_summary.json): ASR / mean StrongREJECT score / refusal_rate / empty_rate.
#
# Decisive comparison (see combined summary at the end):
#   arm07 (refusal-suppression, L18/L22)  vs  arm04 (vanilla baseline)  at matched compute,
#   with arm07-rand-L18 (norm-matched random direction) as the specificity control.
#
# REUSE: doublespeak_causality/26_eval_p9_gcg_heldout_asr.py, which wraps
# poc_stage_gcg_early.evaluate_optimized_suffixes.evaluate_suffix (generate + StrongREJECT).
# Resume-safe: rows already in each arm's FREE_GENERATION_RESULTS.jsonl are skipped by row_key.
#
# NEEDS OPENAI_API_KEY (StrongREJECT judge) — sourced from .env below.
#
# DO NOT launch until the optimization job (arm run-dirs FINAL_CANDIDATES.jsonl) is COMPLETE.
# No SLURM deps — chain by hand after optimization finishes.
#
# Usage:
#   sbatch slurm_scripts/run_gcg_p9_firstcut_eval.slurm

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
ARM_ROOT="${PROJECT_DIR}/outputs/stage_gcg_full"
MANIFEST="${PROJECT_DIR}/doublespeak_causality/data/gcg/clearharm_llama/clearharm_llama_doublespeak.jsonl"
SPLIT="test"
SEED=42
MODEL_FAMILY="llama"
MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
MAX_NEW_TOKENS=2048
DRIVER="${PROJECT_DIR}/doublespeak_causality/26_eval_p9_gcg_heldout_asr.py"

# The four first-cut arms (glob pattern per arm; each must resolve to exactly one dir with
# FINAL_CANDIDATES.jsonl). Patterns are permissive on the slug so they match whatever run-id the
# optimization job used, as long as the arm number / layer / rand tag are in the dir name.
ARM_GLOBS=(
  "phase9_gcg_mac_matrix_arm04*seed${SEED}"
  "phase9_gcg_mac_matrix_arm07*L18*seed${SEED}"
  "phase9_gcg_mac_matrix_arm07*L22*seed${SEED}"
  "phase9_gcg_mac_matrix_arm07*rand*L18*seed${SEED}"
)

cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi

mkdir -p logs

export HF_HOME="${PROJECT_DIR}/.cache/huggingface"
export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export TORCH_HOME="${PROJECT_DIR}/.cache/torch"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

echo "========================================================"
echo "  Gate-7 first-cut EVAL — held-out (${SPLIT}) StrongREJECT ASR"
echo "========================================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID:-none}"
echo "SLURM_NODELIST:  ${SLURM_NODELIST:-none}"
echo "MANIFEST:        ${MANIFEST}"
echo "SPLIT/SEED:      ${SPLIT} / ${SEED}"
echo "MODEL:           ${MODEL_NAME} (${MODEL_FAMILY})"
echo "GIT_REVISION:    $(git rev-parse HEAD 2>/dev/null || echo unknown)"
echo "DATE:            $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Strict L40S guard (generation job).
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
if [[ "$GPU_NAME" != *"L40S"* ]]; then
    echo "ERROR: Expected L40S GPU, got: $GPU_NAME. Aborting."
    exit 1
fi

# OPENAI_API_KEY presence check (StrongREJECT judge) — warn loudly but do not abort
# (the run would still produce generations; scores would be null / judge_fail).
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "WARNING: OPENAI_API_KEY not set — StrongREJECT scores will be null (judge_fail). Fix .env."
else
    echo "OPENAI_API_KEY: present"
fi

# Resolve each arm glob to a single run-dir; eval each with per-arm NON-FATAL guard (|| true)
# so one arm's failure (OOM/judge/etc.) never aborts the others.
RESOLVED_DIRS=()
for pat in "${ARM_GLOBS[@]}"; do
    # shellcheck disable=SC2086
    matches=$(ls -d ${ARM_ROOT}/${pat}/ 2>/dev/null || true)
    n=$(echo -n "$matches" | grep -c '/' || true)
    if [ "$n" -eq 0 ]; then
        echo ">>> SKIP: no run-dir matches '${pat}' (arm not present yet)"
        continue
    fi
    if [ "$n" -gt 1 ]; then
        echo ">>> WARN: pattern '${pat}' matched ${n} dirs; evaluating each:"
        echo "$matches"
    fi
    while IFS= read -r d; do
        [ -z "$d" ] && continue
        RESOLVED_DIRS+=("${d%/}")
    done <<< "$matches"
done

echo ""
echo "Arms to evaluate: ${#RESOLVED_DIRS[@]}"
for d in "${RESOLVED_DIRS[@]}"; do echo "  - $(basename "$d")"; done
echo ""

for RUN_DIR in "${RESOLVED_DIRS[@]}"; do
    ARM="$(basename "$RUN_DIR")"
    echo "--------------------------------------------------------"
    echo ">>> ARM ${ARM}"
    if [ ! -f "${RUN_DIR}/FINAL_CANDIDATES.jsonl" ]; then
        echo ">>> SKIP ${ARM}: no FINAL_CANDIDATES.jsonl (optimization incomplete)"
        continue
    fi
    python "$DRIVER" \
        --run-dir "$RUN_DIR" \
        --manifest "$MANIFEST" \
        --split "$SPLIT" \
        --model-family "$MODEL_FAMILY" \
        --model-name-or-path "$MODEL_NAME" \
        --seed "$SEED" \
        --max-new-tokens "$MAX_NEW_TOKENS" \
        --arm-label "$ARM" || echo ">>> ARM ${ARM} eval FAILED (non-fatal, continuing)"
done

# Combined scalar summary + decisive comparison (non-fatal).
echo ""
echo "========================================================"
echo "  COMBINED SUMMARY"
echo "========================================================"
python - "$ARM_ROOT" <<'PYEOF' || true
import sys, json, glob, os
root = sys.argv[1]
rows = []
for p in sorted(glob.glob(os.path.join(root, "phase9_gcg_mac_matrix_arm*seed42", "p9_heldout_asr_summary.json"))):
    try:
        rows.append(json.load(open(p)))
    except Exception as e:
        print(f"  (skip {p}: {e})")
if not rows:
    print("  no per-arm summaries found yet")
else:
    hdr = f"{'arm':<52} {'n':>4} {'ASR':>7} {'refuse':>7} {'empty':>7} {'meanSR':>7} {'jfail':>6}"
    print(hdr); print("  " + "-" * (len(hdr)))
    for r in rows:
        print(f"{r.get('arm_label',''):<52} {str(r.get('n_tasks')):>4} "
              f"{str(r.get('asr')):>7} {str(r.get('refusal_rate')):>7} {str(r.get('empty_rate')):>7} "
              f"{str(r.get('mean_strongreject_score')):>7} {str(r.get('judge_fail_frac')):>6}")
    def find(sub, excl=None):
        for r in rows:
            lab = r.get("arm_label", "")
            if sub in lab and (excl is None or excl not in lab):
                return r
        return None
    base = find("arm04")
    ref18 = find("L18", excl="rand")
    ref22 = find("L22", excl="rand")
    rand = find("rand")
    print("\n  DECISIVE COMPARISON (held-out ASR):")
    if base: print(f"    baseline arm04         ASR={base.get('asr')}")
    if ref18: print(f"    refusal arm07-L18      ASR={ref18.get('asr')}")
    if ref22: print(f"    refusal arm07-L22      ASR={ref22.get('asr')}")
    if rand: print(f"    control arm07-rand-L18 ASR={rand.get('asr')}")
    print("    (expect refusal-arm ASR > baseline, and random-dir control NOT > baseline)")
PYEOF

echo ""
echo "========================================================"
echo "  Gate-7 first-cut EVAL pass COMPLETE — $(date -u)"
echo "========================================================"
