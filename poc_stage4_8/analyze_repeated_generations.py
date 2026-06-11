"""
Stage 4.8 — Behavioral analysis of repeated-generation outputs.

Computes:
  - Success rate per prompt-condition cell
  - Within-cell vs between-prompt variance
  - Condition effects with prompt fixed effects
  - Thinking-length variability
  - Censoring by condition
  - StrongREJECT score distributions

Key output:
  matched_outcome_cells.csv — cells with ≥1 success AND ≥1 failure (both eos_token,
  parsed_from_think_tags).  These are the valid inputs for behavior-conditioned direction.

Usage:
  python -m poc_stage4_8.analyze_repeated_generations
      --run-dir outputs/stage4_8/runs/<timestamp>
      [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_CONDITIONS = ["A", "D", "F"]
_SR_THRESHOLD = 0.5
_N_BOOT = 2000
_BOOT_SEED = 42


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


def _b(x) -> bool | None:
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    s = str(x).lower()
    if s in ("true", "1"):
        return True
    if s in ("false", "0"):
        return False
    return None


def bootstrap_mean_ci(values: list[float], n_boot: int = _N_BOOT, seed: int = _BOOT_SEED) -> dict:
    arr = np.array([v for v in values if not math.isnan(v)])
    if len(arr) == 0:
        return {"mean": None, "ci_low_95": None, "ci_high_95": None, "n": 0}
    rng = np.random.default_rng(seed)
    boots = rng.choice(arr, size=(n_boot, len(arr)), replace=True).mean(axis=1)
    return {
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "ci_low_95": float(np.percentile(boots, 2.5)),
        "ci_high_95": float(np.percentile(boots, 97.5)),
        "n": int(len(arr)),
    }


def build_cell_summary(rows: list[dict]) -> list[dict]:
    """One row per (source_example_id, condition) cell."""
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        key = (r.get("source_example_id", ""), r.get("condition", ""))
        cells[key].append(r)

    summary = []
    for (src, cond), cell_rows in sorted(cells.items()):
        is_censored = [r.get("finish_reason") == "max_new_tokens" for r in cell_rows]
        complete_rows = [r for r in cell_rows if not (r.get("finish_reason") == "max_new_tokens")]
        valid_rows = [
            r for r in complete_rows
            if r.get("thinking_segmentation_status") == "parsed_from_think_tags"
        ]
        scores = [_f(r.get("strongreject_score")) for r in complete_rows]
        scores_valid = [s for s in scores if not math.isnan(s)]
        successes = [_b(r.get("sr_success")) for r in complete_rows]
        n_success = sum(1 for s in successes if s is True)
        n_failure = sum(1 for s in successes if s is False)
        think_toks = [_f(r.get("think_token_count", 0)) for r in complete_rows]

        # Is this a "matched" cell?
        valid_successes = [_b(r.get("sr_success")) for r in valid_rows]
        has_success = any(s is True for s in valid_successes)
        has_failure = any(s is False for s in valid_successes)
        is_matched = has_success and has_failure and len(valid_rows) >= 2

        ci = bootstrap_mean_ci(scores_valid)
        think_ci = bootstrap_mean_ci([t for t in think_toks if not math.isnan(t)])

        summary.append({
            "source_example_id": src,
            "condition": cond,
            "goal_index": cell_rows[0].get("goal_index"),
            "n_seeds": len(cell_rows),
            "n_censored": sum(is_censored),
            "n_complete": len(complete_rows),
            "n_valid_seg": len(valid_rows),
            "n_success": n_success,
            "n_failure": n_failure,
            "success_rate": n_success / len(complete_rows) if complete_rows else None,
            "mean_sr_score": ci["mean"],
            "ci_low_95_sr_score": ci["ci_low_95"],
            "ci_high_95_sr_score": ci["ci_high_95"],
            "sr_score_variance": float(np.var(scores_valid)) if len(scores_valid) > 1 else None,
            "mean_think_tokens": think_ci["mean"],
            "think_token_variance": float(np.var([t for t in think_toks if not math.isnan(t)])) if len(think_toks) > 1 else None,
            "is_matched_outcome_cell": is_matched,
            "has_success": has_success,
            "has_failure": has_failure,
        })
    return summary


def build_condition_summary(rows: list[dict]) -> list[dict]:
    summary = []
    for cond in _CONDITIONS:
        cond_rows = [r for r in rows if r.get("condition") == cond]
        complete = [r for r in cond_rows if r.get("finish_reason") == "eos_token"]
        n_censored = len(cond_rows) - len(complete)
        scores = [_f(r.get("strongreject_score")) for r in complete]
        scores_v = [s for s in scores if not math.isnan(s)]
        n_success = sum(1 for r in complete if _b(r.get("sr_success")) is True)
        ci = bootstrap_mean_ci(scores_v)
        summary.append({
            "condition": cond,
            "n_total": len(cond_rows),
            "n_complete": len(complete),
            "n_censored": n_censored,
            "n_success": n_success,
            "success_rate_complete": n_success / len(complete) if complete else None,
            "mean_sr_score": ci["mean"],
            "ci_low_95": ci["ci_low_95"],
            "ci_high_95": ci["ci_high_95"],
        })
    return summary


def build_variance_decomposition(rows: list[dict]) -> dict:
    """
    Simple variance decomposition: total variance in SR score decomposed into
    between-prompt and within-prompt (between-seed) components.
    """
    complete = [
        r for r in rows
        if r.get("finish_reason") == "eos_token"
        and not math.isnan(_f(r.get("strongreject_score", float("nan"))))
    ]
    if len(complete) < 4:
        return {"note": "too few complete rows for variance decomposition"}

    # Group by (source, condition)
    cells: dict[tuple, list[float]] = defaultdict(list)
    for r in complete:
        key = (r.get("source_example_id", ""), r.get("condition", ""))
        cells[key].append(_f(r.get("strongreject_score")))

    # Within-cell variance (average across cells)
    within_vars = [np.var(vals) for vals in cells.values() if len(vals) > 1]
    between_means = [np.mean(vals) for vals in cells.values()]

    return {
        "n_cells": len(cells),
        "n_complete": len(complete),
        "mean_within_cell_variance": float(np.mean(within_vars)) if within_vars else None,
        "between_cell_variance": float(np.var(between_means)) if len(between_means) > 1 else None,
        "note": (
            "between_cell_variance includes both prompt identity and condition effects. "
            "mean_within_cell_variance is purely seed/stochastic variation within fixed (prompt, condition)."
        ),
    }


def build_matched_outcome_cells(cell_summary: list[dict]) -> list[dict]:
    return [r for r in cell_summary if r.get("is_matched_outcome_cell")]


def _write_csv(path: Path, data: list[dict], fields: list[str] | None = None) -> None:
    if not data:
        path.write_text("")
        return
    fields = fields or list(data[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)
    print(f"  wrote {path} ({len(data)} rows)")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Analyze Stage 4.8 repeated generations.")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=None)
    args = p.parse_args(argv)

    run_dir = args.run_dir
    out_dir = args.output_dir or (run_dir / "analysis")
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        print(f"ERROR: {summary_path} not found")
        return 1

    rows = _load_jsonl(summary_path)
    print(f"Loaded {len(rows)} rows")

    # Cell summary
    cell_summary = build_cell_summary(rows)
    _write_csv(out_dir / "cell_summary.csv", cell_summary, list(cell_summary[0].keys()) if cell_summary else [])

    # Condition summary
    cond_summary = build_condition_summary(rows)
    _write_csv(out_dir / "condition_summary.csv", cond_summary, list(cond_summary[0].keys()) if cond_summary else [])

    # Variance decomposition
    var_decomp = build_variance_decomposition(rows)
    with open(out_dir / "variance_decomposition.json", "w") as f:
        json.dump(var_decomp, f, indent=2)
    print(f"  wrote {out_dir / 'variance_decomposition.json'}")

    # Matched outcome cells (the critical output)
    matched = build_matched_outcome_cells(cell_summary)
    _write_csv(
        out_dir / "matched_outcome_cells.csv",
        matched,
        list(matched[0].keys()) if matched else list(cell_summary[0].keys()) if cell_summary else [],
    )

    # Summary JSON
    summary_result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n_rows": len(rows),
        "n_cells": len(cell_summary),
        "n_matched_cells": len(matched),
        "condition_summary": cond_summary,
        "variance_decomposition": var_decomp,
        "matched_cells": [
            {k: v for k, v in r.items() if k in [
                "source_example_id", "condition", "goal_index",
                "n_success", "n_failure", "n_valid_seg", "success_rate",
            ]}
            for r in matched
        ],
    }
    with open(out_dir / "analysis_summary.json", "w") as f:
        json.dump(summary_result, f, indent=2, default=str)
    print(f"  wrote {out_dir / 'analysis_summary.json'}")

    print("\n=== Stage 4.8 Condition Summary ===")
    for r in cond_summary:
        print(
            f"  {r['condition']}: {r['n_success']}/{r['n_complete']} success "
            f"(censored={r['n_censored']}) mean_sr={r['mean_sr_score']}"
        )

    print(f"\n=== Matched Outcome Cells: {len(matched)} ===")
    for r in matched:
        print(
            f"  {r['source_example_id']} cond={r['condition']} "
            f"success={r['n_success']} failure={r['n_failure']}"
        )

    if not matched:
        print(
            "\n  WARNING: No matched outcome cells found. "
            "Cannot extract behavior-conditioned direction from this run. "
            "See decision gate in the plan."
        )

    print(f"\nVariance decomposition: {var_decomp}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
