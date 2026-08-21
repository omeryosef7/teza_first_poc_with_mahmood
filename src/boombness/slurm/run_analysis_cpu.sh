#!/bin/bash
#SBATCH --job-name=boombanalysis
#SBATCH --output=outputs/boombness/logs/analysis_%j.out
#SBATCH --error=outputs/boombness/logs/analysis_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --partition=cpu-killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#
# CPU-only analysis runner. Offline analysis needs no GPU, and the LOGIN NODE is not a safe
# place for it: on 2026-08-21 the login node sat at load average 23 with /home/sharifm 93% full
# and a 12-judge-directory read exceeded a 550 s timeout twice. Same contention that made
# `import openai` hang (see run_judge_cpu.sh).
#
# Usage: sbatch --export=ALL,ANALYSIS_ARGS_FILE=/abs/path/args.txt run_analysis_cpu.sh
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
export PYTHONUNBUFFERED=1
export PYTHONPATH="$PROJECT_DIR/src/boombness:${PYTHONPATH:-}"
# Provenance: batch nodes have no git binary (review #10), so the commit is exported from the
# submitting host by the caller. Recorded as unavailable rather than crashing if absent.
echo "=== analysis ==="; date; hostname
echo "git_commit(env)=${BOOMB_GIT_COMMIT:-UNSET}"
if [ ! -f "$ANALYSIS_ARGS_FILE" ]; then echo "ERROR argsfile not found: $ANALYSIS_ARGS_FILE"; exit 1; fi
ARGS="$(cat "$ANALYSIS_ARGS_FILE")"
echo "args: $ARGS"
# shellcheck disable=SC2086
python -u $ARGS
echo "=== done ==="; date
