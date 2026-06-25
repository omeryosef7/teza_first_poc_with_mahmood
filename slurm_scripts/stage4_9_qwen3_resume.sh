#!/bin/bash
# Resume Qwen3 goals 4-10 after partial-completion timeout.
#
# Goals 4-6: resume from existing partial-output dirs (skip already-done rows).
# Goals 7-10: fresh submission (never ran before).
#
# Usage (run AFTER the killed 612424 tasks fully disappear from the queue):
#   bash slurm_scripts/stage4_9_qwen3_resume.sh

set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SCRIPT="$PROJECT_DIR/slurm_scripts/stage4_9_qwen3_goals4_10.slurm"
cd "$PROJECT_DIR"

echo "=== Qwen3 goals 4-10 resume submission ==="
date

# Goal 4 — resume in existing partial dir (11/18 rows done)
J4=$(RUN_DIR="$PROJECT_DIR/outputs/stage4_8_extended/runs/qwen3_run_612426" \
  sbatch --array=4 --time=08:00:00 "$SCRIPT" | awk '{print $NF}')
echo "Goal 4 resume: job $J4 (dir: qwen3_run_612426)"

# Goal 5 — resume in existing partial dir (8/18 rows done)
J5=$(RUN_DIR="$PROJECT_DIR/outputs/stage4_8_extended/runs/qwen3_run_612427" \
  sbatch --array=5 --time=08:00:00 "$SCRIPT" | awk '{print $NF}')
echo "Goal 5 resume: job $J5 (dir: qwen3_run_612427)"

# Goal 6 — resume in existing partial dir (14/18 rows done)
J6=$(RUN_DIR="$PROJECT_DIR/outputs/stage4_8_extended/runs/qwen3_run_612428" \
  sbatch --array=6 --time=08:00:00 "$SCRIPT" | awk '{print $NF}')
echo "Goal 6 resume: job $J6 (dir: qwen3_run_612428)"

# Goals 7-10 — fresh submission (new dirs created by each task)
J710=$(sbatch --array=7-10%3 --time=08:00:00 "$SCRIPT" | awk '{print $NF}')
echo "Goals 7-10 fresh: array job $J710"

echo ""
echo "All submitted. Check status with:"
echo "  squeue -u omeryosef"
echo ""
echo "After all complete, rebuild dataset:"
echo "  cd $PROJECT_DIR && python -m poc_stage4.build_factorial_attack_dataset"
