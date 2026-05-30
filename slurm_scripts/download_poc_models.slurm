#!/bin/bash

#SBATCH --job-name=poc_download_models
#SBATCH --output=logs/poc_download_models_%j.out
#SBATCH --error=logs/poc_download_models_%j.err
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

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
RUNTIME_DIR="/home/sharifm/students/omeryosef/jupyter_runtime"
CONDA_ENV="${CONDA_ENV:-poc_stage2}"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

mkdir -p logs "$RUNTIME_DIR"/{config,data,runtime,ipython} "$PROJECT_DIR/.cache"/{huggingface,torch,triton}

export JUPYTER_CONFIG_DIR="$RUNTIME_DIR/config"
export JUPYTER_DATA_DIR="$RUNTIME_DIR/data"
export JUPYTER_RUNTIME_DIR="$RUNTIME_DIR/runtime"
export IPYTHONDIR="$RUNTIME_DIR/ipython"
export HF_HOME="$PROJECT_DIR/.cache/huggingface"
export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HUGGINGFACE_HUB_CACHE="$HF_HUB_CACHE"
export TRANSFORMERS_CACHE="$HF_HUB_CACHE"
export TORCH_HOME="$PROJECT_DIR/.cache/torch"
export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"

echo "=== POC model cache download started ==="
date
hostname
pwd
python -V
echo "CONDA_ENV=$CONDA_ENV"
echo "HF_HOME=$HF_HOME"
echo "HF_HUB_CACHE=$HF_HUB_CACHE"

python - <<'PY'
import os
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except ImportError as exc:
    raise SystemExit(
        "huggingface_hub is not installed in the active conda environment. "
        "Install it with: pip install huggingface_hub"
    ) from exc

models = [
    "Qwen/Qwen3-8B",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "mistralai/Mistral-7B-Instruct-v0.3",
]

cache_dir = Path(os.environ["HF_HUB_CACHE"])
cache_dir.mkdir(parents=True, exist_ok=True)

print("Downloading model snapshots into Hugging Face cache:")
for model_id in models:
    print(f"\n=== Downloading {model_id} ===", flush=True)
    snapshot_path = snapshot_download(
        repo_id=model_id,
        repo_type="model",
        cache_dir=str(cache_dir),
        local_files_only=False,
    )
    snapshot = Path(snapshot_path)
    if not snapshot.exists():
        raise SystemExit(f"snapshot path does not exist after download: {snapshot}")
    files = [path for path in snapshot.rglob("*") if path.is_file()]
    print(f"Snapshot path: {snapshot}")
    print(f"Files present: {len(files)}")

print("\nAll requested model snapshots are present in the repo-local cache.")
PY

echo ""
echo "=== Cache size ==="
du -sh "$HF_HOME" "$HF_HUB_CACHE" || true

echo ""
echo "=== POC model cache download finished successfully ==="
date
