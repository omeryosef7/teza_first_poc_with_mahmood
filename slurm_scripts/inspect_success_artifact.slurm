#!/bin/bash
# SBATCH example to run the artifact inspector on the cluster
# Adjust partition, account, and environment activation to your cluster.
# Usage: sbatch inspect_success_artifact.slurm /path/to/artifact.json

#SBATCH --job-name=inspect_qwen_artifact
#SBATCH --output=logs/inspect_qwen_artifact_%j.out
#SBATCH --error=logs/inspect_qwen_artifact_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=2
#SBATCH --nodelist=n-802,n-803,n-804,n-805,n-302,n-303,n-304,n-305

set -euo pipefail

ARTIFACT_PATH="${1:-/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage6/qwen_token_trace_search_full_gpu_alltraces_20260527_183600/qwen3_14b_success_trace_goal_index_0_attack_iteration_1_conversation_id_1_target_model_gpt-o4-mini.json}"

OUTDIR="outputs/slurm_inspect_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR"

echo "Inspecting artifact: $ARTIFACT_PATH"

# Activate python environment - edit as needed for your cluster setup
# Example: source /etc/profile.d/modules.sh; module load anaconda; conda activate teza
if command -v conda >/dev/null 2>&1; then
  # try to activate a named env if it exists
  if conda info --envs | grep -q teza; then
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate teza || true
  fi
fi

# Fallback: run with whatever `python` is available
PYCMD=${PYTHON:-python}

echo "Using python: $($PYCMD --version 2>&1)"

# Run the inspector and emit a JSON summary
SUMMARY_JSON="$OUTDIR/inspect_summary_${SLURM_JOB_ID:-local}.json"
"$PYCMD" -m poc_stage6.inspect_qwen_artifact "$ARTIFACT_PATH" --json > "$SUMMARY_JSON"

echo "Summary written to: $SUMMARY_JSON"

# Optional: copy summary back to your local machine (edit user/host/path)
# scp $SUMMARY_JSON youruser@your.local.host:/path/to/local/dir/

exit 0
