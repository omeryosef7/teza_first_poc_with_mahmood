#!/bin/bash
# Consolidate goals 4-10 run dirs and rebuild the factorial dataset.
#
# Usage (run after all Qwen3 and Gemma4 extended jobs complete):
#   bash poc_stage4_8/consolidate_and_rebuild.sh

set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"

source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2

RUNS_DIR="$PROJECT_DIR/outputs/stage4_8_extended/runs"
QWEN3_CONSOLIDATED="$RUNS_DIR/consolidated_qwen3"
GEMMA4_CONSOLIDATED="$RUNS_DIR/consolidated_gemma4"

echo "=== Step 1: Consolidate run dirs ==="
date

mkdir -p "$QWEN3_CONSOLIDATED" "$GEMMA4_CONSOLIDATED"

# Merge all qwen3 run summaries (exclude smoke and consolidated dirs)
python3 - <<'PY'
import json
from pathlib import Path
from collections import Counter

runs_dir = Path("outputs/stage4_8_extended/runs")
out_q = runs_dir / "consolidated_qwen3" / "run_summary.jsonl"
out_g = runs_dir / "consolidated_gemma4" / "run_summary.jsonl"

q_by_id, g_by_id = {}, {}
for d in sorted(runs_dir.iterdir()):
    p = d / "run_summary.jsonl"
    if not p.exists():
        continue
    if "smoke" in d.name or "consolidated" in d.name:
        continue
    rows = [json.loads(l) for l in p.read_text().strip().split("\n") if l.strip()]
    for r in rows:
        run_id = r.get("run_id", "")
        if d.name.startswith("qwen3_"):
            q_by_id[run_id] = r  # last write wins (doesn't matter, same content)
        elif d.name.startswith("gemma4_"):
            g_by_id[run_id] = r

q_rows = list(q_by_id.values())
g_rows = list(g_by_id.values())

print(f"Qwen3 rows (deduplicated by run_id): {len(q_rows)}")
print(f"Gemma4 rows (deduplicated by run_id): {len(g_rows)}")

for label, rows in [("Qwen3", q_rows), ("Gemma4", g_rows)]:
    goals = sorted(set(r.get("goal_index") for r in rows))
    conds = Counter(r.get("condition") for r in rows)
    print(f"  {label}: goals={goals} conds={dict(conds)}")

out_q.write_text("\n".join(json.dumps(r) for r in q_rows) + "\n")
out_g.write_text("\n".join(json.dumps(r) for r in g_rows) + "\n")
print("Consolidated files written.")
PY

echo ""
echo "=== Step 2: Rebuild factorial_attack_dataset.jsonl ==="
date

python -m poc_stage4.build_factorial_attack_dataset \
    --stage49-qwen3-dir "$QWEN3_CONSOLIDATED" \
    --stage49-gemma4-dir "$GEMMA4_CONSOLIDATED"

echo ""
echo "=== Step 3: Classify attack mechanisms ==="
date

python -m poc_stage4.classify_attack_mechanisms

echo ""
echo "=== Step 4: Analyze factorial effects ==="
date

python -m poc_stage4.analyze_factorial_attack_effects

echo ""
echo "=== Done ==="
date

echo ""
echo "Key output files:"
echo "  outputs/stage4/factorial_attack_dataset.jsonl"
echo "  outputs/stage4/mechanism_classification.jsonl"
echo "  outputs/stage4/mechanism_summary.json"
echo "  outputs/stage4/factorial_analysis/paired_contrasts.csv"
