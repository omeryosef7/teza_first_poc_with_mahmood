"""
Stage 4.7 — Behavioral and mechanistic analysis of replication outputs.

Inference unit: source prompt (n=12 total, n=3 per goal).

Produces:
  analysis/condition_summary.csv
  analysis/paired_contrasts.csv
  analysis/goal_stratified_summary.csv
  analysis/mechanistic_summary.csv  (if projection_analysis/ exists)
  analysis/bootstrap_cis.json
  analysis/sign_tests.json

Usage:
  python -m poc_stage4_7.analyze_replication
      --run-dir outputs/stage4_7/runs/<run_timestamp>
      [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONDITIONS = ["A", "D", "F", "E"]
CONDITION_LABELS = {
    "A": "Full puzzle, thinking=on",
    "D": "No puzzle, thinking=on",
    "F": "Benign wrapper, thinking=on",
    "E": "Full puzzle, thinking=off",
}
SR_THRESHOLD = 0.5
PRIMARY_CONTRASTS = [("A", "D"), ("A", "F"), ("D", "F"), ("A", "E")]
N_BOOT = 2000
BOOT_SEED = 42


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _f(x, default=float("nan")):
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


def bootstrap_mean_ci(values: list[float], n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
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


def sign_test(diffs: list[float]) -> dict:
    """Exact sign test for paired differences."""
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    ties = sum(1 for d in diffs if d == 0)
    n_eff = pos + neg
    if n_eff == 0:
        return {"n_positive": pos, "n_negative": neg, "n_tied": ties, "p_two_sided": None, "note": "all_ties"}
    # Exact binomial p-value
    try:
        from scipy.stats import binom_test
        p = binom_test(min(pos, neg), n=n_eff, p=0.5, alternative="two-sided")
    except Exception:
        try:
            from scipy.stats import binomtest
            p = binomtest(min(pos, neg), n=n_eff, p=0.5, alternative="two-sided").pvalue
        except Exception:
            p = None
    return {
        "n_positive": pos,
        "n_negative": neg,
        "n_tied": ties,
        "n_effective": n_eff,
        "p_two_sided": float(p) if p is not None else None,
        "note": "exact_binomial_sign_test",
    }


def mcnemar_exact(a_success: list[bool], b_success: list[bool]) -> dict:
    """McNemar exact test for paired binary outcomes."""
    n_01 = sum(1 for a, b in zip(a_success, b_success) if not a and b)
    n_10 = sum(1 for a, b in zip(a_success, b_success) if a and not b)
    n_11 = sum(1 for a, b in zip(a_success, b_success) if a and b)
    n_00 = sum(1 for a, b in zip(a_success, b_success) if not a and not b)
    discordant = n_01 + n_10
    if discordant == 0:
        return {"n_01": n_01, "n_10": n_10, "n_11": n_11, "n_00": n_00,
                "discordant": 0, "p_two_sided": None, "note": "no_discordant_pairs"}
    try:
        from scipy.stats import binom_test
        p = binom_test(min(n_01, n_10), n=discordant, p=0.5, alternative="two-sided")
    except Exception:
        try:
            from scipy.stats import binomtest
            p = binomtest(min(n_01, n_10), n=discordant, p=0.5, alternative="two-sided").pvalue
        except Exception:
            p = None
    return {
        "n_01": n_01, "n_10": n_10, "n_11": n_11, "n_00": n_00,
        "discordant": discordant,
        "p_two_sided": float(p) if p is not None else None,
        "note": "mcnemar_exact",
    }


def build_condition_summary(rows: list[dict]) -> list[dict]:
    results = []
    for cond in CONDITIONS:
        cond_rows = [r for r in rows if r.get("condition") == cond]
        scores = [_f(r.get("strongreject_score")) for r in cond_rows]
        scores = [s for s in scores if not math.isnan(s)]
        successes = [_b(r.get("sr_success")) for r in cond_rows]
        n_success = sum(1 for s in successes if s is True)
        think = [_f(r.get("think_token_count", 0)) for r in cond_rows]
        final = [_f(r.get("final_token_count", 0)) for r in cond_rows]
        truncated = sum(1 for r in cond_rows if r.get("finish_reason") == "max_new_tokens")
        ci = bootstrap_mean_ci(scores)
        results.append({
            "condition": cond,
            "condition_label": CONDITION_LABELS.get(cond, ""),
            "n": len(cond_rows),
            "n_sr_success": n_success,
            "sr_success_rate": n_success / len(cond_rows) if cond_rows else None,
            "mean_sr_score": ci["mean"],
            "median_sr_score": ci["median"],
            "ci_low_95_sr_score": ci["ci_low_95"],
            "ci_high_95_sr_score": ci["ci_high_95"],
            "mean_think_tokens": float(np.mean(think)) if think else None,
            "median_think_tokens": float(np.median(think)) if think else None,
            "mean_final_tokens": float(np.mean(final)) if final else None,
            "n_truncated": truncated,
        })
    return results


def build_paired_contrasts(rows: list[dict]) -> tuple[list[dict], dict]:
    contrast_rows = []
    test_results = {}
    source_ids = list(dict.fromkeys(r.get("source_example_id") for r in rows))

    for c1, c2 in PRIMARY_CONTRASTS:
        by_source: dict[str, tuple[dict | None, dict | None]] = {}
        for sid in source_ids:
            r1 = next((r for r in rows if r.get("source_example_id") == sid and r.get("condition") == c1), None)
            r2 = next((r for r in rows if r.get("source_example_id") == sid and r.get("condition") == c2), None)
            by_source[sid] = (r1, r2)

        score_diffs = []
        think_diffs = []
        think_ratios = []
        a_success_list = []
        b_success_list = []

        for sid, (r1, r2) in by_source.items():
            if r1 is None or r2 is None:
                continue
            s1 = _f(r1.get("strongreject_score"))
            s2 = _f(r2.get("strongreject_score"))
            if not math.isnan(s1) and not math.isnan(s2):
                score_diffs.append(s1 - s2)

            t1 = _f(r1.get("think_token_count", 0))
            t2 = _f(r2.get("think_token_count", 0))
            if not math.isnan(t1) and not math.isnan(t2):
                think_diffs.append(t1 - t2)
                if t2 > 0:
                    think_ratios.append(t1 / t2)

            suc1 = _b(r1.get("sr_success"))
            suc2 = _b(r2.get("sr_success"))
            if suc1 is not None and suc2 is not None:
                a_success_list.append(suc1)
                b_success_list.append(suc2)

            goal = r1.get("goal_index")
            stratum = r1.get("selection_stratum", "")
            contrast_rows.append({
                "contrast": f"{c1}_vs_{c2}",
                "cond_ref": c1,
                "cond_comp": c2,
                "source_example_id": sid,
                "goal_index": goal,
                "selection_stratum": stratum,
                "score_ref": s1,
                "score_comp": s2,
                "score_diff_ref_minus_comp": s1 - s2 if not math.isnan(s1) and not math.isnan(s2) else None,
                "sr_success_ref": _b(r1.get("sr_success")),
                "sr_success_comp": _b(r2.get("sr_success")),
                "think_tokens_ref": t1,
                "think_tokens_comp": t2,
                "think_diff": t1 - t2 if not math.isnan(t1) and not math.isnan(t2) else None,
                "think_ratio_ref_over_comp": t1 / t2 if not math.isnan(t2) and t2 > 0 else None,
                "finish_reason_ref": r1.get("finish_reason"),
                "finish_reason_comp": r2.get("finish_reason"),
            })

        key = f"{c1}_vs_{c2}"
        st = sign_test(score_diffs)
        mc = mcnemar_exact(a_success_list, b_success_list) if a_success_list else None
        ci_diff = bootstrap_mean_ci(score_diffs)
        ci_think_ratio = bootstrap_mean_ci(think_ratios) if think_ratios else None
        test_results[key] = {
            "n_pairs": len(score_diffs),
            "mean_score_diff": ci_diff["mean"],
            "ci_low_95_score_diff": ci_diff["ci_low_95"],
            "ci_high_95_score_diff": ci_diff["ci_high_95"],
            "sign_test": st,
            "mcnemar": mc,
            "mean_think_ratio": ci_think_ratio["mean"] if ci_think_ratio else None,
            "mean_think_diff": float(np.mean(think_diffs)) if think_diffs else None,
        }
        print(f"  Contrast {c1} vs {c2}: n={len(score_diffs)} "
              f"mean_diff={ci_diff['mean']:.3f} "
              f"signs(+/-/0)={st['n_positive']}/{st['n_negative']}/{st['n_tied']}")

    return contrast_rows, test_results


def build_goal_stratified(rows: list[dict]) -> list[dict]:
    results = []
    goals = sorted({int(r.get("goal_index", -1)) for r in rows if r.get("goal_index") is not None})
    for goal in goals:
        for cond in CONDITIONS:
            cond_rows = [r for r in rows if int(r.get("goal_index", -1)) == goal and r.get("condition") == cond]
            if not cond_rows:
                continue
            scores = [_f(r.get("strongreject_score")) for r in cond_rows]
            scores = [s for s in scores if not math.isnan(s)]
            n_success = sum(1 for r in cond_rows if _b(r.get("sr_success")) is True)
            think = [_f(r.get("think_token_count", 0)) for r in cond_rows]
            results.append({
                "goal_index": goal,
                "condition": cond,
                "n": len(cond_rows),
                "n_sr_success": n_success,
                "mean_sr_score": float(np.mean(scores)) if scores else None,
                "mean_think_tokens": float(np.mean(think)) if think else None,
            })
    return results


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Analyze Stage 4.7 replication results.")
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

    def _write_csv(path, data, fields):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(data)
        print(f"  wrote {path} ({len(data)} rows)")

    # Condition summary
    cond_summary = build_condition_summary(rows)
    _write_csv(out_dir / "condition_summary.csv", cond_summary, list(cond_summary[0].keys()))

    # Paired contrasts
    print("\nComputing paired contrasts (n by source prompt) ...")
    contrast_rows, test_results = build_paired_contrasts(rows)
    _write_csv(out_dir / "paired_contrasts.csv", contrast_rows, list(contrast_rows[0].keys()) if contrast_rows else [])

    with open(out_dir / "sign_tests.json", "w") as f:
        json.dump(test_results, f, indent=2)
    print(f"  wrote {out_dir / 'sign_tests.json'}")

    # Bootstrap CIs
    boot_results = {}
    for cond in CONDITIONS:
        scores = [_f(r.get("strongreject_score")) for r in rows if r.get("condition") == cond]
        boot_results[cond] = bootstrap_mean_ci([s for s in scores if not math.isnan(s)])
    with open(out_dir / "bootstrap_cis.json", "w") as f:
        json.dump(boot_results, f, indent=2)
    print(f"  wrote {out_dir / 'bootstrap_cis.json'}")

    # Goal-stratified
    goal_strat = build_goal_stratified(rows)
    _write_csv(out_dir / "goal_stratified_summary.csv", goal_strat, list(goal_strat[0].keys()) if goal_strat else [])

    # Projection analysis (if available)
    proj_path = run_dir / "projection_analysis" / "projection_summary.jsonl"
    if proj_path.exists():
        proj_rows = _load_jsonl(proj_path)
        print(f"\nLoaded {len(proj_rows)} projection rows")
        # Merge with behavioral data
        merged = []
        for pr in proj_rows:
            beh_row = next((r for r in rows if r.get("run_id") == pr.get("run_id")), {})
            merged_row = {**beh_row, **pr}
            merged.append(merged_row)
        if merged:
            _write_csv(out_dir / "mechanistic_summary.csv", merged, list(merged[0].keys()))

    print("\n=== Stage 4.7 Condition Summary ===")
    for r in cond_summary:
        print(f"  {r['condition']} ({r['condition_label']}): "
              f"{r['n_sr_success']}/{r['n']} success "
              f"mean_score={r['mean_sr_score']:.3f} "
              f"mean_think={r['mean_think_tokens']:.0f}")

    print("\nAnalysis complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
