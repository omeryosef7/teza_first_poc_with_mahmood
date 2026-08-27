#!/bin/bash
#SBATCH --job-name=q3judge
#SBATCH --output=outputs/boombness/logs/judge_%j.out
#SBATCH --error=outputs/boombness/logs/judge_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#
# CPU-only judging. Judging is pure OpenAI API traffic -- no model, no GPU -- so it does not
# belong on run_boombness.sh (which demands an L40S and would idle a GPU for the whole batch).
#
# WHY NOT THE LOGIN NODE (2026-08-21): `import openai` hung for >90s there, stalled in
# importlib `_fill_cache` -- an NFS directory listing. Login node load average was 19.3 with 86
# users and /home/sharifm is 93% full. The first launch of the six-arm batch died silently for
# exactly this reason: a 0-byte log and no processes, because the interpreter never finished
# importing. Compute nodes do not share that contention.
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
export PYTHONUNBUFFERED=1
export PYTHONPATH="$PROJECT_DIR/src/boombness:${PYTHONPATH:-}"
echo "=== judge batch ==="; date; hostname
echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)"
bash "$PROJECT_DIR/${JUDGE_BATCH:-scripts/judge_qwen3_decomposition.sh}"
echo "=== done ==="; date
