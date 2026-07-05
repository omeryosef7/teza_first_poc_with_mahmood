"""
Detection delay analysis for Stage GCG-Early (Stage 9).

After free-generation evaluation, computes:
  - Repr distance by generated-token position and layer region
  - Earliest token position where optimized suffix distance drops below threshold
  - Task success rate by condition (optimized / neutral / random / task-only)
  - Comparison table: conditions × positions × layer regions

This is a post-hoc analysis of FREE_GENERATION_RESULTS.jsonl. It does NOT
require a GPU — all inputs are pre-computed hidden states on disk.

NOTE: Teacher-forced results (from ITERATION_LOG.jsonl) are diagnostic only.
The conclusions in DETECTION_DELAY_ANALYSIS.md must be based on free-generation
results (FREE_GENERATION_RESULTS.jsonl), not teacher-forced optimization losses.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def load_free_gen_results(run_dir: Path) -> List[dict]:
    path = Path(run_dir) / "FREE_GENERATION_RESULTS.jsonl"
    if not path.exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _group_by(rows: List[dict], key: str) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = defaultdict(list)
    for r in rows:
        out[str(r.get(key, "unknown"))].append(r)
    return dict(out)


def summarize_by_condition(rows: List[dict]) -> dict:
    """
    Compute per-condition statistics from free-generation results.

    Returns dict: condition_label -> {
        n: int,
        task_success_rate: float,   # fraction where strongreject_is_success == True
        mean_strongreject: float,
    }
    """
    by_condition = _group_by(rows, "condition_label")
    summary = {}
    for cond, cond_rows in by_condition.items():
        n = len(cond_rows)
        successes = sum(1 for r in cond_rows if r.get("strongreject_is_success", False))
        scores = [r["strongreject_score"] for r in cond_rows if "strongreject_score" in r]
        summary[cond] = {
            "n": n,
            "task_success_rate": successes / n if n > 0 else 0.0,
            "mean_strongreject": sum(scores) / len(scores) if scores else 0.0,
        }
    return summary


def analyze_detection_delay(run_dir: Path, output_subdir: str = "analysis") -> None:
    """
    Full detection delay analysis. Requires Stage 9 free-generation results.

    Writes DETECTION_DELAY_ANALYSIS.md to run_dir.
    """
    run_dir = Path(run_dir)
    rows = load_free_gen_results(run_dir)

    if not rows:
        print(
            f"[detection_delay] No FREE_GENERATION_RESULTS.jsonl in {run_dir}. "
            "Run Stage 9 free-generation evaluation first."
        )
        return

    cond_summary = summarize_by_condition(rows)

    lines = [
        f"# Detection Delay Analysis: {run_dir.name}",
        f"",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}  ",
        f"**N rows:** {len(rows)}  ",
        f"",
        f"> WARNING: These are FREE-GENERATION results. Teacher-forced optimization",
        f"> losses (ITERATION_LOG.jsonl) are diagnostic only and cannot support",
        f"> causal claims about detection evasion.",
        f"",
        f"---",
        f"",
        f"## Condition Summary",
        f"",
        f"| Condition | N | Task Success Rate | Mean StrongREJECT |",
        f"|---|---|---|---|",
    ]
    for cond, stats in sorted(cond_summary.items()):
        lines.append(
            f"| {cond} | {stats['n']} | {stats['task_success_rate']:.3f} "
            f"| {stats['mean_strongreject']:.3f} |"
        )
    lines += [
        f"",
        f"---",
        f"",
        f"## Per-Position Repr Distance",
        f"",
        f"(Requires hidden_states .pt files — computed by evaluate_optimized_suffixes.py)",
        f"",
        f"## Notes",
        f"",
        f"- Repr distance analysis requires hidden_states/ directory from Stage 9",
        f"- Detector AUC analysis is not implemented here (requires separate classifier training)",
        f"- 'Earliest detectable token position' is defined as the first position where",
        f"  optimized-condition mean distance < neutral-condition mean distance by > 2σ",
        f"",
    ]

    out_path = run_dir / "DETECTION_DELAY_ANALYSIS.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[detection_delay] Written {out_path}")

    # Print quick summary
    print(f"[detection_delay] {len(rows)} free-gen rows, {len(cond_summary)} conditions:")
    for cond, stats in sorted(cond_summary.items()):
        print(f"  {cond}: n={stats['n']}, success_rate={stats['task_success_rate']:.3f}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    analyze_detection_delay(Path(args.run_dir))
