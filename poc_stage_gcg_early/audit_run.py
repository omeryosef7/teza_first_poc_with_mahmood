"""
Run completeness audit for Stage GCG-Early.

Checks that all expected artifacts are present in a run directory and
writes DONE only when all checks pass. Writes AUDIT_REPORT.md with
a human-readable summary.

Usage:
  python -m poc_stage_gcg_early.audit_run --run-dir outputs/stage_gcg_early/<run_id>
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_REQUIRED_FILES = [
    "CONFIG.json",
    "ENVIRONMENT.json",
    "MANIFEST.jsonl",
    "ITERATION_LOG.jsonl",
    "PARETO_CANDIDATES.jsonl",
    "FINAL_CANDIDATES.jsonl",
    "checkpoint.pt",
]

_STAGE9_FILES = [
    "FREE_GENERATION_RESULTS.jsonl",
]


def audit_run(run_dir: Path, require_stage9: bool = False) -> Tuple[bool, List[str]]:
    """
    Audit a run directory for completeness.

    Returns (passed: bool, issues: list[str]).
    Writes AUDIT_REPORT.md in run_dir.
    """
    run_dir = Path(run_dir)
    issues = []
    ok_items = []

    required = _REQUIRED_FILES + (_STAGE9_FILES if require_stage9 else [])
    for fname in required:
        fpath = run_dir / fname
        if fpath.exists():
            ok_items.append(f"[OK] {fname}")
        else:
            issues.append(f"[MISSING] {fname}")

    # Check CONFIG.json is parseable
    config_path = run_dir / "CONFIG.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            ok_items.append(f"[OK] CONFIG.json parseable (run_id={cfg.get('run_id')})")
        except Exception as e:
            issues.append(f"[CORRUPT] CONFIG.json: {e}")

    # Check ITERATION_LOG.jsonl has at least one entry and all required fields
    iter_log = run_dir / "ITERATION_LOG.jsonl"
    if iter_log.exists():
        required_fields = {"step", "suffix_ids", "task_loss", "repr_loss", "kl_loss",
                           "reg_loss", "total_loss", "wall_time_sec"}
        n_rows = 0
        missing_fields_rows = []
        with open(iter_log, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                n_rows += 1
                try:
                    row = json.loads(line)
                    missing = required_fields - set(row.keys())
                    if missing:
                        missing_fields_rows.append((lineno, missing))
                except json.JSONDecodeError as e:
                    issues.append(f"[CORRUPT] ITERATION_LOG.jsonl line {lineno}: {e}")
        if n_rows == 0:
            issues.append("[EMPTY] ITERATION_LOG.jsonl has no rows")
        else:
            ok_items.append(f"[OK] ITERATION_LOG.jsonl has {n_rows} rows")
        for lineno, missing in missing_fields_rows[:5]:
            issues.append(f"[MISSING_FIELDS] ITERATION_LOG.jsonl line {lineno}: {missing}")

    # Check PARETO_CANDIDATES.jsonl
    pareto_log = run_dir / "PARETO_CANDIDATES.jsonl"
    if pareto_log.exists():
        n_pareto = sum(1 for line in open(pareto_log) if line.strip())
        ok_items.append(f"[OK] PARETO_CANDIDATES.jsonl has {n_pareto} entries")

    # Check for checkpoint snapshots
    snapshots = sorted(run_dir.glob("checkpoint_step_*.pt"))
    if snapshots:
        ok_items.append(f"[OK] {len(snapshots)} checkpoint snapshots found")
    else:
        issues.append("[WARNING] No checkpoint_step_*.pt snapshots found")

    passed = len(issues) == 0

    # Write AUDIT_REPORT.md
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# GCG-Early Run Audit Report",
        f"",
        f"**Run dir:** `{run_dir}`  ",
        f"**Audited at:** {now}  ",
        f"**Result:** {'PASS' if passed else 'FAIL'}",
        f"",
        f"## Issues ({len(issues)})",
        f"",
    ]
    if issues:
        for iss in issues:
            lines.append(f"- {iss}")
    else:
        lines.append("None.")
    lines += [
        f"",
        f"## OK checks ({len(ok_items)})",
        f"",
    ]
    for item in ok_items:
        lines.append(f"- {item}")

    (run_dir / "AUDIT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if passed:
        done_path = run_dir / "DONE"
        if not done_path.exists():
            done_path.write_text(f"Audit passed at {now}\n", encoding="utf-8")
            print(f"[audit] PASS — wrote DONE")
    else:
        print(f"[audit] FAIL — {len(issues)} issues:")
        for iss in issues:
            print(f"  {iss}")

    return passed, issues


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--require-stage9", action="store_true")
    args = parser.parse_args()
    passed, issues = audit_run(Path(args.run_dir), require_stage9=args.require_stage9)
    sys.exit(0 if passed else 1)
