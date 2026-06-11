"""
Stage 4.8 — Audit repeated-generation outputs.

Validates:
  - Row count (60 full / subset for smoke)
  - No duplicate run_ids
  - Seeds differ → at least some generation_hashes differ within each (source, condition) cell
  - Sampling config consistent
  - Finish reason distribution
  - Censoring count per condition
  - StrongREJECT coverage

Writes: <run_dir>/audit.json

Usage:
  python -m poc_stage4_8.audit_repeated_generations
      --run-dir outputs/stage4_8/runs/<timestamp>
      [--smoke]  # allow fewer than 60 rows
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_EXPECTED_TOTAL = 60
_EXPECTED_SEEDS = [101, 102, 103, 104, 105]
_EXPECTED_CONDITIONS = ["A", "D", "F"]
_EXPECTED_GOALS = [0, 1, 2, 3]
_DO_SAMPLE = True
_TEMPERATURE = 0.7
_TOP_P = 0.95
_MAX_NEW_TOKENS = 32768


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _f(x, default=float("nan")) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def audit(run_dir: Path, smoke: bool = False) -> dict:
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        return {
            "passed": False,
            "errors": [f"run_summary.jsonl not found in {run_dir}"],
            "warnings": [],
        }

    rows = _load_jsonl(summary_path)
    errors = []
    warnings = []

    n = len(rows)
    expected_n = _EXPECTED_TOTAL if not smoke else None

    if not smoke and n != _EXPECTED_TOTAL:
        errors.append(f"Expected {_EXPECTED_TOTAL} rows, got {n}")
    elif smoke and n == 0:
        errors.append("No rows found in smoke run")

    # Duplicate run_ids
    run_ids = [r.get("run_id", "") for r in rows]
    dups = [k for k, v in Counter(run_ids).items() if v > 1]
    if dups:
        errors.append(f"Duplicate run_ids: {dups[:5]}")

    # Sampling config consistency
    for r in rows:
        if not r.get("do_sample"):
            warnings.append(f"do_sample not True for {r.get('run_id')}")
        temp = _f(r.get("sampling_temperature", r.get("temperature", float("nan"))))
        if not math.isnan(temp) and abs(temp - _TEMPERATURE) > 0.01:
            errors.append(f"temperature mismatch {temp} for {r.get('run_id')}")
        top_p = _f(r.get("sampling_top_p", r.get("top_p", float("nan"))))
        if not math.isnan(top_p) and abs(top_p - _TOP_P) > 0.01:
            errors.append(f"top_p mismatch {top_p} for {r.get('run_id')}")

    # Seeds present
    seeds = sorted(set(int(_f(r.get("seed", -1))) for r in rows if r.get("seed") is not None))
    if not smoke and seeds != sorted(_EXPECTED_SEEDS):
        errors.append(f"Seeds mismatch: got {seeds}, expected {sorted(_EXPECTED_SEEDS)}")

    # Generation hash diversity: within each (source, condition) cell, seeds should differ
    cells: dict[tuple, list[str]] = {}
    for r in rows:
        cell_key = (r.get("source_example_id", ""), r.get("condition", ""))
        gen_hash = r.get("generation_hash", "")
        cells.setdefault(cell_key, []).append(gen_hash)

    n_diverse_cells = sum(1 for hashes in cells.values() if len(set(h for h in hashes if h)) > 1)
    n_cells = len(cells)
    if n_cells > 0 and n_diverse_cells == 0 and not smoke:
        warnings.append(
            "No cells show generation_hash diversity across seeds — "
            "all seeds may have produced identical outputs"
        )
    elif n_diverse_cells > 0:
        pass  # good

    # Finish reason distribution
    finish_reasons = Counter(r.get("finish_reason", "unknown") for r in rows)
    n_censored = finish_reasons.get("max_new_tokens", 0)
    n_complete = finish_reasons.get("eos_token", 0)

    # Segmentation status
    seg_status = Counter(r.get("thinking_segmentation_status", "unknown") for r in rows)

    # SR coverage
    n_sr_scored = sum(1 for r in rows if r.get("strongreject_score") is not None)
    n_sr_missing = n - n_sr_scored
    if n_sr_missing > 0:
        warnings.append(f"{n_sr_missing} rows missing strongreject_score")

    # Censoring by condition
    cens_by_cond = {}
    for cond in _EXPECTED_CONDITIONS:
        cond_rows = [r for r in rows if r.get("condition") == cond]
        cens_by_cond[cond] = sum(1 for r in cond_rows if r.get("finish_reason") == "max_new_tokens")

    # run_id format check
    for r in rows:
        seed_val = r.get("seed")
        run_id = r.get("run_id", "")
        if seed_val is not None and f"__seed_{seed_val}" not in run_id:
            errors.append(f"run_id {run_id!r} missing seed component __seed_{seed_val}")
            break  # report once

    passed = len(errors) == 0

    return {
        "passed": passed,
        "n_rows": n,
        "n_complete": n_complete,
        "n_censored": n_censored,
        "n_diverse_cells": n_diverse_cells,
        "n_cells": n_cells,
        "n_sr_scored": n_sr_scored,
        "seeds_present": seeds,
        "finish_reasons": dict(finish_reasons),
        "segmentation_status": dict(seg_status),
        "censoring_by_condition": cens_by_cond,
        "sampling_config_checked": {
            "do_sample": _DO_SAMPLE,
            "temperature": _TEMPERATURE,
            "top_p": _TOP_P,
        },
        "errors": errors,
        "warnings": warnings,
        "is_smoke": smoke,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Audit Stage 4.8 repeated-generation outputs.")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--smoke", action="store_true", default=False)
    args = p.parse_args(argv)

    print(f"Auditing {args.run_dir} ...")
    result = audit(args.run_dir, smoke=args.smoke)

    result["created_utc"] = datetime.now(timezone.utc).isoformat()
    out_path = args.run_dir / "audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {out_path}")

    status = "PASSED" if result["passed"] else "FAILED"
    print(f"\n=== Audit {status} ===")
    print(f"  rows={result.get('n_rows','?')} complete={result.get('n_complete','?')} censored={result.get('n_censored','?')}")
    print(f"  cells={result.get('n_cells','?')} diverse={result.get('n_diverse_cells','?')}")
    print(f"  SR scored={result.get('n_sr_scored','?')}")
    print(f"  Seeds present: {result.get('seeds_present', [])}")
    for e in result.get("errors", []):
        print(f"  ERROR: {e}")
    for w in result.get("warnings", []):
        print(f"  WARNING: {w}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
