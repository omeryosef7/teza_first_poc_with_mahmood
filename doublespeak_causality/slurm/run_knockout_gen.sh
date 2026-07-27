#!/bin/bash
#SBATCH --job-name=ds_ko_gen
#SBATCH --output=doublespeak_causality/logs/ds_ko_gen_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_ko_gen_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
# RQ4 generalization: attention knockout across hijacking concepts/codewords.
#   sbatch --export=ALL,DSMODEL=...,DSREADOUT=30,DSTAG=llama8b,DSONLY="virus_mirror,..." run_knockout_gen.sh
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh; conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs doublespeak_causality/outputs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"; export PYTHONUNBUFFERED=1
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"; : "${DSREADOUT:=30}"; : "${DSTAG:=llama8b}"
DSONLY="${DSONLY-}"   # keep empty if set empty (empty => 09 processes ALL items)
echo "=== knockout-gen: $DSMODEL readout=$DSREADOUT ==="; date; hostname
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
MARK="doublespeak_causality/outputs/.ko_gen_${DSTAG}.COMPLETE"
if [ -f "$MARK" ]; then echo "already COMPLETE"; exit 0; fi
python -u doublespeak_causality/09_attention_knockout.py --model "$DSMODEL" \
  --data doublespeak_causality/data/multi_concept_panel.json --templated --readout-layer "$DSREADOUT" \
  --only "$DSONLY" --out-dir "doublespeak_causality/outputs/ko_gen_${DSTAG}"
# NOTE: --only "" makes 09 process ALL panel items (filter hijackers in analysis);
# never pass a comma-list via sbatch --export (it truncates at the first comma).
echo "COMPLETE $(date)" > "$MARK"; echo "=== done ==="; date
