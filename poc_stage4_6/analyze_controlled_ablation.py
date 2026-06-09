"""
Stage 4.6 — Analyze controlled ablation results.

Reads run_summary.jsonl and produces comparison tables:
  - per_run_results.csv
  - condition_summary.csv
  - goal_condition_summary.csv
  - thinking_mode_comparison.csv
  - puzzle_fraction_trend.csv

Uses paired comparisons by source prompt (not cross-prompt pooled tests).
With small N, uses exact counts, bootstrap CIs, Wilcoxon signed-rank for
paired conditions. Reports effect direction and per-prompt consistency —
not significance claims.

Usage:
  python -m poc_stage4_6.analyze_controlled_ablation [--run-dir PATH] [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

_OUTPUT_BASE = _REPO_ROOT / "outputs" / "stage4_6"
CONDITIONS = ["A", "B", "C", "D", "E"]
CONDITION_LABELS = {
    "A": "Full puzzle (thinking=on)",
    "B": "50% puzzle (thinking=on)",
    "C": "25% puzzle (thinking=on)",
    "D": "No puzzle (thinking=on)",
    "E": "Full puzzle (thinking=off)",
}
PUZZLE_FRACTIONS = {"A": 1.0, "B": 0.5, "C": 0.25, "D": 0.0, "E": 1.0}


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------

def bootstrap_mean_ci(
    values: list[float],
    n_boot: int = 1000,
    ci: float = 0.95,
    rng_seed: int = 42,
) -> tuple[float, float, float]:
    """Return (mean, ci_low, ci_high)."""
    if not values:
        return float("nan"), float("nan"), float("nan")
    arr = np.array(values, dtype=float)
    rng = np.random.default_rng(rng_seed)
    boot = rng.choice(arr, size=(n_boot, len(arr)), replace=True).mean(axis=1)
    alpha = 1.0 - ci
    lo = float(np.percentile(boot, 100 * alpha / 2))
    hi = float(np.percentile(boot, 100 * (1 - alpha / 2)))
    return float(arr.mean()), lo, hi


def wilcoxon_signed_rank(x: list[float], y: list[float]) -> dict[str, Any]:
    """Paired Wilcoxon signed-rank test between x and y."""
    if len(x) != len(y) or len(x) < 2:
        return {"statistic": None, "p_value": None, "n_pairs": len(x), "note": "insufficient_data"}
    try:
        from scipy.stats import wilcoxon
        diffs = [a - b for a, b in zip(x, y)]
        diffs = [d for d in diffs if d != 0]
        if not diffs:
            return {"statistic": None, "p_value": None, "n_pairs": len(x), "note": "all_ties"}
        stat, p = wilcoxon(diffs)
        return {"statistic": float(stat), "p_value": float(p), "n_pairs": len(x), "note": "ok"}
    except Exception as exc:
        return {"statistic": None, "p_value": None, "n_pairs": len(x), "note": str(exc)}


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze(run_dir: Path, output_dir: Path) -> None:
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        raise FileNotFoundError(f"run_summary.jsonl not found in {run_dir}")

    rows: list[dict] = []
    with open(summary_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    if not rows:
        print("No rows in run_summary.jsonl — nothing to analyze.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Cast types
    for r in rows:
        r["goal_index"] = int(r.get("goal_index", -1))
        r["sr_success"] = _to_bool(r.get("sr_success"))
        r["judge_success"] = _to_bool(r.get("judge_success"))
        r["is_success"] = _to_bool(r.get("is_success"))
        r["strongreject_score"] = _to_float(r.get("strongreject_score"))
        r["think_token_count"] = _to_int(r.get("think_token_count", 0))
        r["puzzle_fraction_target"] = _to_float(r.get("puzzle_fraction_target", 1.0))
        r["puzzle_tokens_kept"] = _to_int(r.get("puzzle_tokens_kept", 0))
        r["puzzle_tokens_total"] = _to_int(r.get("puzzle_tokens_total", 0))

    # 1. per_run_results.csv
    per_run_fields = [
        "run_id", "source_example_id", "condition", "goal_index",
        "enable_thinking", "puzzle_fraction_target",
        "puzzle_tokens_kept", "puzzle_tokens_total",
        "prompt_token_count", "generation_token_count",
        "think_token_count", "final_token_count",
        "thinking_segmentation_status", "finish_reason",
        "sr_success", "strongreject_score",
        "judge_success", "judge_score", "is_success",
        "elapsed_seconds", "created_utc",
    ]
    common.write_csv(output_dir / "per_run_results.csv", rows, per_run_fields)
    print(f"per_run_results.csv: {len(rows)} rows")

    # 2. condition_summary.csv — per condition across all goals
    cond_summary = _condition_summary(rows)
    cond_fields = [
        "condition", "label", "puzzle_fraction_target",
        "n", "sr_success_count", "sr_success_rate",
        "judge_success_count", "judge_success_rate",
        "is_success_count", "is_success_rate",
        "mean_strongreject_score", "sr_ci_low", "sr_ci_high",
        "mean_think_tokens", "median_think_tokens",
    ]
    common.write_csv(output_dir / "condition_summary.csv", cond_summary, cond_fields)
    print(f"condition_summary.csv: {len(cond_summary)} rows")

    # 3. goal_condition_summary.csv
    goal_cond_summary = _goal_condition_summary(rows)
    gc_fields = [
        "goal_index", "condition", "label", "puzzle_fraction_target",
        "n", "sr_success_count", "sr_success_rate",
        "judge_success_count", "judge_success_rate",
        "mean_strongreject_score", "mean_think_tokens",
    ]
    common.write_csv(output_dir / "goal_condition_summary.csv", goal_cond_summary, gc_fields)
    print(f"goal_condition_summary.csv: {len(goal_cond_summary)} rows")

    # 4. thinking_mode_comparison.csv — A vs E paired by source
    thinking_cmp = _paired_comparison(rows, "A", "E", "puzzle_full_thinking_on_vs_off")
    common.atomic_write_json(output_dir / "thinking_mode_comparison.json", thinking_cmp)
    thinking_rows = _comparison_to_rows(thinking_cmp, "A", "E")
    common.write_csv(output_dir / "thinking_mode_comparison.csv", thinking_rows,
                     list(thinking_rows[0].keys()) if thinking_rows else [])
    print(f"thinking_mode_comparison.csv: {len(thinking_rows)} rows")

    # 5. puzzle_fraction_trend.csv — A/B/C/D per source (thinking=on)
    trend = _puzzle_fraction_trend(rows)
    common.write_csv(output_dir / "puzzle_fraction_trend.csv", trend,
                     list(trend[0].keys()) if trend else [])
    print(f"puzzle_fraction_trend.csv: {len(trend)} rows")

    # 6. Paired comparisons json
    paired = {}
    for cond_b in ("B", "C", "D", "E"):
        key = f"A_vs_{cond_b}"
        paired[key] = _paired_comparison(rows, "A", cond_b, key)
    common.atomic_write_json(output_dir / "paired_comparisons.json", paired)
    print(f"paired_comparisons.json written")

    print(f"\nAll analysis outputs written to {output_dir}")


def _to_bool(v: Any) -> bool | None:
    if v is True or v == "True":
        return True
    if v is False or v == "False":
        return False
    return None


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def _to_int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _condition_summary(rows: list[dict]) -> list[dict]:
    from collections import defaultdict

    by_cond: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    result = []
    for cond in CONDITIONS:
        group = by_cond.get(cond, [])
        n = len(group)
        sr_successes = [r for r in group if r["sr_success"] is True]
        judge_successes = [r for r in group if r["judge_success"] is True]
        is_successes = [r for r in group if r["is_success"] is True]
        sr_scores = [r["strongreject_score"] for r in group if not np.isnan(r["strongreject_score"])]
        think_tokens = [r["think_token_count"] for r in group if r["think_token_count"] > 0]

        mean_sr, ci_lo, ci_hi = bootstrap_mean_ci(sr_scores) if sr_scores else (float("nan"),) * 3

        result.append({
            "condition": cond,
            "label": CONDITION_LABELS.get(cond, cond),
            "puzzle_fraction_target": PUZZLE_FRACTIONS.get(cond, ""),
            "n": n,
            "sr_success_count": len(sr_successes),
            "sr_success_rate": round(len(sr_successes) / n, 3) if n else float("nan"),
            "judge_success_count": len(judge_successes),
            "judge_success_rate": round(len(judge_successes) / n, 3) if n else float("nan"),
            "is_success_count": len(is_successes),
            "is_success_rate": round(len(is_successes) / n, 3) if n else float("nan"),
            "mean_strongreject_score": round(mean_sr, 3) if not np.isnan(mean_sr) else "",
            "sr_ci_low": round(ci_lo, 3) if not np.isnan(ci_lo) else "",
            "sr_ci_high": round(ci_hi, 3) if not np.isnan(ci_hi) else "",
            "mean_think_tokens": round(float(np.mean(think_tokens)), 1) if think_tokens else "",
            "median_think_tokens": round(float(np.median(think_tokens)), 0) if think_tokens else "",
        })
    return result


def _goal_condition_summary(rows: list[dict]) -> list[dict]:
    from collections import defaultdict

    by_gc: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_gc[(r["goal_index"], r["condition"])].append(r)

    result = []
    for gi in range(4):
        for cond in CONDITIONS:
            group = by_gc.get((gi, cond), [])
            n = len(group)
            if n == 0:
                continue
            sr_successes = [r for r in group if r["sr_success"] is True]
            judge_successes = [r for r in group if r["judge_success"] is True]
            sr_scores = [r["strongreject_score"] for r in group if not np.isnan(r["strongreject_score"])]
            think_tokens = [r["think_token_count"] for r in group]

            result.append({
                "goal_index": gi,
                "condition": cond,
                "label": CONDITION_LABELS.get(cond, cond),
                "puzzle_fraction_target": PUZZLE_FRACTIONS.get(cond, ""),
                "n": n,
                "sr_success_count": len(sr_successes),
                "sr_success_rate": round(len(sr_successes) / n, 3) if n else float("nan"),
                "judge_success_count": len(judge_successes),
                "judge_success_rate": round(len(judge_successes) / n, 3) if n else float("nan"),
                "mean_strongreject_score": round(float(np.mean(sr_scores)), 3) if sr_scores else "",
                "mean_think_tokens": round(float(np.mean(think_tokens)), 1) if think_tokens else "",
            })
    return result


def _paired_comparison(rows: list[dict], cond_a: str, cond_b: str, label: str) -> dict:
    """Paired comparison of cond_a vs cond_b, matched by source_example_id."""
    a_map = {r["source_example_id"]: r for r in rows if r["condition"] == cond_a}
    b_map = {r["source_example_id"]: r for r in rows if r["condition"] == cond_b}
    common_ids = sorted(set(a_map) & set(b_map))

    if not common_ids:
        return {"label": label, "n_pairs": 0, "note": "no_common_sources"}

    sr_a = [float(a_map[eid]["strongreject_score"]) for eid in common_ids]
    sr_b = [float(b_map[eid]["strongreject_score"]) for eid in common_ids]
    think_a = [float(a_map[eid]["think_token_count"]) for eid in common_ids]
    think_b = [float(b_map[eid]["think_token_count"]) for eid in common_ids]
    success_a = [1 if a_map[eid]["is_success"] is True else 0 for eid in common_ids]
    success_b = [1 if b_map[eid]["is_success"] is True else 0 for eid in common_ids]

    sr_diff = [a - b for a, b in zip(sr_a, sr_b)]
    per_pair = []
    for eid in common_ids:
        ra = a_map[eid]
        rb = b_map[eid]
        per_pair.append({
            "source_example_id": eid,
            "goal_index": ra["goal_index"],
            f"sr_score_{cond_a}": ra["strongreject_score"],
            f"sr_score_{cond_b}": rb["strongreject_score"],
            f"sr_score_diff_{cond_a}_minus_{cond_b}": _to_float(ra["strongreject_score"]) - _to_float(rb["strongreject_score"]),
            f"think_tokens_{cond_a}": ra["think_token_count"],
            f"think_tokens_{cond_b}": rb["think_token_count"],
            f"is_success_{cond_a}": ra["is_success"],
            f"is_success_{cond_b}": rb["is_success"],
        })

    wsr = wilcoxon_signed_rank(sr_a, sr_b)
    wsr_think = wilcoxon_signed_rank(think_a, think_b)

    valid_sr = [d for d in sr_diff if not np.isnan(d)]
    return {
        "label": label,
        "cond_a": cond_a,
        "cond_b": cond_b,
        "n_pairs": len(common_ids),
        "mean_sr_score_a": float(np.mean(sr_a)) if sr_a else None,
        "mean_sr_score_b": float(np.mean(sr_b)) if sr_b else None,
        "mean_sr_diff_a_minus_b": float(np.mean(valid_sr)) if valid_sr else None,
        "n_a_higher": sum(1 for d in valid_sr if d > 0),
        "n_b_higher": sum(1 for d in valid_sr if d < 0),
        "n_tied": sum(1 for d in valid_sr if d == 0),
        "sr_wilcoxon_stat": wsr.get("statistic"),
        "sr_wilcoxon_p": wsr.get("p_value"),
        "sr_wilcoxon_note": wsr.get("note"),
        "mean_think_tokens_a": float(np.mean(think_a)) if think_a else None,
        "mean_think_tokens_b": float(np.mean(think_b)) if think_b else None,
        "think_wilcoxon_stat": wsr_think.get("statistic"),
        "think_wilcoxon_p": wsr_think.get("p_value"),
        "n_success_a": sum(success_a),
        "n_success_b": sum(success_b),
        "per_pair": per_pair,
    }


def _comparison_to_rows(cmp: dict, cond_a: str, cond_b: str) -> list[dict]:
    per_pair = cmp.get("per_pair", [])
    if not per_pair:
        return [{"note": "no_data"}]
    return per_pair


def _puzzle_fraction_trend(rows: list[dict]) -> list[dict]:
    """One row per (source_example_id, condition) for A/B/C/D (thinking=on)."""
    thinking_on_conds = ["A", "B", "C", "D"]
    result = []
    for r in rows:
        if r["condition"] in thinking_on_conds:
            result.append({
                "source_example_id": r["source_example_id"],
                "goal_index": r["goal_index"],
                "condition": r["condition"],
                "puzzle_fraction_target": r["puzzle_fraction_target"],
                "puzzle_tokens_kept": r["puzzle_tokens_kept"],
                "puzzle_tokens_total": r["puzzle_tokens_total"],
                "prompt_token_count": r.get("prompt_token_count"),
                "generation_token_count": r.get("generation_token_count"),
                "think_token_count": r["think_token_count"],
                "strongreject_score": r["strongreject_score"],
                "sr_success": r["sr_success"],
                "judge_success": r["judge_success"],
                "is_success": r["is_success"],
                "finish_reason": r.get("finish_reason"),
                "thinking_segmentation_status": r.get("thinking_segmentation_status"),
            })
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Analyze Stage 4.6 controlled ablation results.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--run-dir", type=Path, default=_OUTPUT_BASE / "runs_output")
    p.add_argument("--output-dir", type=Path, default=None)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = args.output_dir or (args.run_dir / "analysis")
    analyze(run_dir=args.run_dir, output_dir=out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
