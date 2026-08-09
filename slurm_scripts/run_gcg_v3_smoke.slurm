#!/bin/bash
#SBATCH --job-name=gcg_v3_smoke
#SBATCH --output=logs/gcg_v3_smoke_%j.out
#SBATCH --error=logs/gcg_v3_smoke_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-602,n-801,n-802,n-803,n-804,n-805,t-806

# =====================================================================================
# NEXT sprint Phase-1 SMOKE — validate the CORRECTED GCG pipeline end-to-end on v3.
# Proves: (1) v3 manifest loads; (2) OFF-BY-ONE FIX works (refusal-dir-layer = fit+1 so
# GCG reads hidden_states[fit+1] == the row the direction was fitted on); (3) the refusal
# objective actually DECREASES the projection (refusal_dir_loss falls over steps) while the
# norm-matched random control does NOT systematically fall (Gate-B sign test, discrete form).
# Tiny: 3 items, 8 steps, 2 arms. NOT a scientific result.
# =====================================================================================
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"

MODEL_FAMILY="llama"; MODEL_PATH="meta-llama/Llama-3.1-8B-Instruct"
MANIFEST="${DC}/data/gcg/clearharm_llama_v3/smoke3_doublespeak.jsonl"
# OFF-BY-ONE FIX: fit layer 18 -> pass hidden_states index 19; fit layer 12 -> index 13.
DIR_L18="${DC}/outputs/refusal_alllayers/refusal_direction_llama_L18.pt"
RAND_L18="${DC}/outputs/gate7_v3_randdirs/refusal_rand_L18_normmatched_seed20260809.pt"
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

echo "GIT: $(git rev-parse HEAD 2>/dev/null || echo unknown)  DATE: $(date -u)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR==1{print;exit}')
case "$GPU_NAME" in *L40S*|*A6000*|*a6000*) echo "[guard] 48GB GPU OK: $GPU_NAME";;
  *) echo "ERROR: need L40S/A6000, got '$GPU_NAME'"; exit 1;; esac

run_arm () {
    local run_id="$1"; shift
    local out_dir="${OUT_BASE}/${run_id}"; mkdir -p "$out_dir"
    echo ">>> ARM ${run_id}"
    python -m poc_stage_gcg_early.run_optimization \
        --run-id "$run_id" --model-family "$MODEL_FAMILY" --model-name-or-path "$MODEL_PATH" \
        --manifest "$MANIFEST" --output-dir "$out_dir" \
        --suffix-length 16 --n-steps 8 --batch-size 64 --topk 256 --seed 42 \
        --split train --no-filter-cand --suffix-placement user --selection-mode weighted --no-thinking \
        --checkpoint-every 4 --snapshot-every 100 "$@"
}

# arm: refusal L18 (CORRECTED index 19) — refusal_dir_loss should DECREASE
run_arm smoke_v3_refusal_L18corr_seed42 \
    --lambda-refusal-dir 0.25 --refusal-dir-layer 19 --refusal-dir-path "$DIR_L18" \
    --objective-name refusal_down_L18 --repr-in-selection --repr-selection-sub-batch 8

# arm: norm-matched RANDOM at L18 (CORRECTED index 19) — control
run_arm smoke_v3_refusal_rand_L18corr_seed42 \
    --lambda-refusal-dir 0.25 --refusal-dir-layer 19 --refusal-dir-path "$RAND_L18" \
    --objective-name refusal_rand_L18 --repr-in-selection --repr-selection-sub-batch 8

echo "=== SMOKE refusal_dir_loss trajectory (should fall for real dir) ==="
for r in smoke_v3_refusal_L18corr_seed42 smoke_v3_refusal_rand_L18corr_seed42; do
  echo "--- $r ---"
  python -c "
import json
rows=[json.loads(l) for l in open('${OUT_BASE}/$r/ITERATION_LOG.jsonl')]
vals=[(x.get('step'),x.get('refusal_dir_loss')) for x in rows if 'refusal_dir_loss' in x]
print('n_steps_logged',len(vals))
for s,v in vals[:12]: print(' step',s,'refusal_dir_loss',round(v,5) if v is not None else None)
"
done
echo "Done smoke at $(date -u)"
