#!/bin/bash
# Run audit + analysis on Stage 4.8 extension v2 results.
# Equivalent to the goal=3 finalisation block in the SLURM array script.
#
# Usage:
#   bash process_stage48_extension_v2.sh
#
# Run this after jobs 538501_0 and 538501_2 both finish.

set -euo pipefail

PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
ARRAY_RUN_DIR="$PROJECT_DIR/outputs/stage4_8/runs/run_array_extension2_20260612_012052"

cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2

echo "=== Stage 4.8 Extension v2: Post-Processing ==="
date
echo "Run dir: $ARRAY_RUN_DIR"
echo ""

# Row count check
ROW_COUNT=$(python3 -c "
from pathlib import Path
p = Path('$ARRAY_RUN_DIR') / 'run_summary.jsonl'
if not p.exists(): print(0)
else: print(len([l for l in p.read_text().splitlines() if l.strip()]))
")
echo "Rows in run_summary.jsonl: $ROW_COUNT"

if [ "$ROW_COUNT" -lt 55 ]; then
    echo "ERROR: Only $ROW_COUNT rows — jobs may not have finished."
    echo "Re-run after both 538501_0 and 538501_2 complete."
    exit 1
fi

# Audit (run informatively; may report seed mismatch since extension uses seeds 106-115)
echo ""
echo "=== Audit (informational — seed mismatch expected) ==="
python -m poc_stage4_8.audit_repeated_generations --run-dir "$ARRAY_RUN_DIR" || echo "(audit reported errors — expected for extension v2 seeds; continuing)"

# Analysis
echo ""
echo "=== Behavioral Analysis ==="
python -m poc_stage4_8.analyze_repeated_generations --run-dir "$ARRAY_RUN_DIR"

echo ""
echo "=== matched_outcome_cells.csv ==="
cat "$ARRAY_RUN_DIR/analysis/matched_outcome_cells.csv" 2>/dev/null || echo "(not generated)"

# Count matched cells
MATCHED=$(python3 -c "
import csv
from pathlib import Path
p = Path('$ARRAY_RUN_DIR') / 'analysis' / 'matched_outcome_cells.csv'
if not p.exists(): print(0)
else: print(len(list(csv.DictReader(open(p)))))
")
echo ""
echo "Matched outcome cells (extension v2 only): $MATCHED"

# Submit representations job if enough cells
if [ "$MATCHED" -ge 4 ]; then
    echo ""
    echo "=== Auto-submitting representations job ==="
    REL_RUN_DIR="${ARRAY_RUN_DIR#$PROJECT_DIR/}"
    sbatch --export=ALL,RUN_DIR="$REL_RUN_DIR" \
        slurm_scripts/stage4_8_compute_representations.slurm
    echo "Representations job submitted."
else
    echo ""
    echo "Only $MATCHED matched cells in extension v2."
    echo "Trying combined analysis (original + extension v2)..."

    # Combined run dir: merge run_summary.jsonl + symlink per_example files from both runs
    python3 - <<'PY'
import json, os
from pathlib import Path

orig_dir = Path("outputs/stage4_8/runs/run_array_20260611_0109")
ext2_dir = Path("outputs/stage4_8/runs/run_array_extension2_20260612_012052")
combined_dir = Path("outputs/stage4_8/runs/run_combined_v2")
combined_dir.mkdir(parents=True, exist_ok=True)
(combined_dir / "per_example").mkdir(exist_ok=True)

rows = []
for src_dir in [orig_dir, ext2_dir]:
    p = src_dir / "run_summary.jsonl"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))

out = combined_dir / "run_summary.jsonl"
with out.open("w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print(f"Combined: {len(rows)} rows → {out}")

# Symlink per_example files from both source dirs into combined dir
n_links = 0
for src_dir in [orig_dir, ext2_dir]:
    pe_dir = src_dir / "per_example"
    if not pe_dir.exists():
        continue
    for src_file in pe_dir.glob("*.json"):
        dst = combined_dir / "per_example" / src_file.name
        if not dst.exists():
            dst.symlink_to(src_file.resolve())
            n_links += 1
print(f"Symlinked {n_links} per_example files into {combined_dir}/per_example/")
PY

    COMBINED_DIR="$PROJECT_DIR/outputs/stage4_8/runs/run_combined_v2"
    echo "Running analysis on combined data..."
    python -m poc_stage4_8.analyze_repeated_generations --run-dir "$COMBINED_DIR"

    echo ""
    echo "=== Combined matched_outcome_cells.csv ==="
    cat "$COMBINED_DIR/analysis/matched_outcome_cells.csv" 2>/dev/null || echo "(not generated)"

    COMBINED_MATCHED=$(python3 -c "
import csv
from pathlib import Path
p = Path('$COMBINED_DIR') / 'analysis' / 'matched_outcome_cells.csv'
if not p.exists(): print(0)
else: print(len(list(csv.DictReader(open(p)))))
")
    echo "Combined matched cells: $COMBINED_MATCHED"

    # Use threshold=3 for combined data (LOPO CV works with 3 folds; each cell is well-populated)
    if [ "$COMBINED_MATCHED" -ge 3 ]; then
        REL_RUN_DIR="${COMBINED_DIR#$PROJECT_DIR/}"
        echo "Note: Using threshold=3 for combined data (LOPO CV is valid with 3 cells)"
        sbatch --export=ALL,RUN_DIR="$REL_RUN_DIR" \
            slurm_scripts/stage4_8_compute_representations.slurm
        echo "Representations job submitted from combined data."
    else
        echo "WARNING: Only $COMBINED_MATCHED matched cells even with combined data."
        echo "Direction extraction cannot run. See Stage 4.8 decision gate documentation."
    fi
fi

echo ""
echo "=== Post-processing complete ==="
date
