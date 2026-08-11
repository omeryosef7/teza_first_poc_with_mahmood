#!/bin/bash
#SBATCH --job-name=gcg_v3_mech
#SBATCH --output=logs/gcg_v3_mech_%j.out
#SBATCH --error=logs/gcg_v3_mech_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-304,n-307,n-801,n-802,n-803,n-804,n-805

# Gate-7 §17 MECHANISTIC-VALIDITY (Q5): does each optimized suffix move its intended internal
# projection on held-out v3 test, and MORE than the random-direction suffix? Forward-pass only.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"
DC="${PROJECT_DIR}/doublespeak_causality"
SEED="${SEED:-42}"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
export HF_HOME="${PROJECT_DIR}/.cache/huggingface"; export HF_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="${PROJECT_DIR}/.cache/huggingface/hub"; export TRANSFORMERS_CACHE="${PROJECT_DIR}/.cache/huggingface/transformers"
export HF_HUB_OFFLINE=1; export TRANSFORMERS_OFFLINE=1; export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | awk 'NR==1{print;exit}')
if [ -z "${VRAM_MB:-}" ] || [ "$VRAM_MB" -lt 20000 ] 2>/dev/null; then echo "ERROR GPU <20GB"; exit 1; fi
echo "[mech] seed=$SEED GPU ${VRAM_MB}MB $(nvidia-smi --query-gpu=name --format=csv,noheader|head -1)"

B="outputs/stage_gcg_full/phase9b_v3"
python doublespeak_causality/scripts/phase_gate7_mech_validity.py \
  --manifest doublespeak_causality/data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak.jsonl \
  --split test \
  --arm refusal_L18=${B}_arm07_refusal_down_L18_seed${SEED} \
  --arm refusal_rand_L18=${B}_arm07r_refusal_rand_L18_seed${SEED} \
  --arm concept_L9=${B}_arm06_concept_up_L9_seed${SEED} \
  --arm concept_rand_L9=${B}_arm06r_concept_rand_L9_seed${SEED} \
  --out doublespeak_causality/reports/GATE7_V3_MECH_VALIDITY_seed${SEED}.json
echo "[mech] done"
