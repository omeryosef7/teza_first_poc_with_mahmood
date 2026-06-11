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


def load_canonical_rows(run_dir: Path) -> list[dict]:
    """Load canonical CSV if available, else fall back to run_summary.jsonl."""
    canon_path = run_dir / "analysis" / "canonical_per_run_results.csv"
    if canon_path.exists():
        with open(canon_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        print(f"Loaded {len(rows)} rows from canonical CSV")
        # Cast numeric fields back from strings
        for r in rows:
            for field in [
                "strongreject_score", "think_token_count", "final_token_count",
                "generation_token_count", "source_prompt_tokens", "transformed_prompt_tokens",
                "goal_index", "elapsed_seconds", "length_match_ratio",
            ]:
                if field in r and r[field] not in ("", "None", None):
                    try:
                        r[field] = float(r[field])
                    except (ValueError, TypeError):
                        pass
            for bool_field in ["is_censored", "sr_success", "is_evaluable_final",
                               "sr_success_legacy", "enable_thinking"]:
                if bool_field in r:
                    v = r[bool_field]
                    if v in ("True", "true", "1"):
                        r[bool_field] = True
                    elif v in ("False", "false", "0"):
                        r[bool_field] = False
                    elif v in ("None", "none", ""):
                        r[bool_field] = None
            # sr_success_complete_case and sr_success_with_censoring may be None
            for field in ["sr_success_complete_case", "sr_success_with_censoring"]:
                if field in r:
                    v = r[field]
                    if v in ("True", "true", "1"):
                        r[field] = True
                    elif v in ("False", "false", "0"):
                        r[field] = False
                    else:
                        r[field] = None
        return rows

    # Fallback: run_summary.jsonl
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        raise FileNotFoundError(f"Neither canonical CSV nor run_summary.jsonl found in {run_dir}")
    rows = _load_jsonl(summary_path)
    print(f"Loaded {len(rows)} rows from run_summary.jsonl (no canonical CSV)")
    # Synthesize is_censored and outcome columns
    for r in rows:
        r["is_censored"] = r.get("finish_reason") == "max_new_tokens"
        sr = _b(r.get("sr_success"))
        r["sr_success_complete_case"] = None if r["is_censored"] else sr
        r["sr_success_with_censoring"] = None if r["is_censored"] else sr
        r["sr_success_legacy"] = sr
    return rows


def build_condition_summary_with_censoring(rows: list[dict]) -> list[dict]:
    """Extend build_condition_summary with complete-case and legacy outcome columns."""
    base = build_condition_summary(rows)
    for d in base:
        cond = d["condition"]
        cond_rows = [r for r in rows if r.get("condition") == cond]
        # Complete-case (non-censored only)
        cc_rows = [r for r in cond_rows if not r.get("is_censored")]
        n_cc_success = sum(1 for r in cc_rows if r.get("sr_success_complete_case") is True)
        # Legacy (all rows, censored treated as false)
        n_legacy_success = sum(1 for r in cond_rows if _b(r.get("sr_success_legacy")) is True)
        d["n_censored"] = sum(1 for r in cond_rows if r.get("is_censored"))
        d["n_complete_case"] = len(cc_rows)
        d["n_cc_success"] = n_cc_success
        d["cc_success_rate"] = n_cc_success / len(cc_rows) if cc_rows else None
        d["n_legacy_success"] = n_legacy_success
        d["legacy_success_rate"] = n_legacy_success / len(cond_rows) if cond_rows else None
    return base


def build_sensitivity_table(rows: list[dict]) -> dict:
    """Compare success counts under three outcome definitions per condition."""
    result = {}
    for cond in CONDITIONS:
        cond_rows = [r for r in rows if r.get("condition") == cond]
        n = len(cond_rows)
        n_censored = sum(1 for r in cond_rows if r.get("is_censored"))
        cc_rows = [r for r in cond_rows if not r.get("is_censored")]
        n_cc = sum(1 for r in cc_rows if r.get("sr_success_complete_case") is True)
        n_legacy = sum(1 for r in cond_rows if _b(r.get("sr_success_legacy")) is True)
        result[cond] = {
            "n_total": n,
            "n_censored": n_censored,
            "complete_case_success": f"{n_cc}/{len(cc_rows)}",
            "complete_case_rate": n_cc / len(cc_rows) if cc_rows else None,
            "legacy_success": f"{n_legacy}/{n}",
            "legacy_rate": n_legacy / n if n else None,
            "complete_vs_legacy_diff": (
                (n_cc / len(cc_rows)) - (n_legacy / n)
                if cc_rows and n else None
            ),
        }
    return result


def build_logo_sensitivity(rows: list[dict]) -> dict:
    """
    Leave-one-goal-out (LOGO) sensitivity.  For each goal g, remove all 3 prompts
    from goal g and recompute paired contrasts on the remaining 9 prompts.
    Reports whether the sign direction of A-D and A-F holds across all folds.
    """
    goals = sorted({int(r.get("goal_index", -1)) for r in rows if r.get("goal_index") is not None})
    logo_results = {}
    for g in goals:
        remaining = [r for r in rows if int(r.get("goal_index", -1)) != g]
        _, test_res = build_paired_contrasts(remaining)
        fold = {}
        for key in ["A_vs_D", "A_vs_F", "D_vs_F", "A_vs_E"]:
            if key in test_res:
                t = test_res[key]
                fold[key] = {
                    "n_pairs": t["n_pairs"],
                    "mean_score_diff": t["mean_score_diff"],
                    "sign_positive": t["sign_test"]["n_positive"],
                    "sign_negative": t["sign_test"]["n_negative"],
                    "p_two_sided": t["sign_test"]["p_two_sided"],
                }
        logo_results[f"leave_out_goal_{g}"] = fold
    # Check stability: does A>D hold in every fold?
    stability = {}
    for contrast in ["A_vs_D", "A_vs_F"]:
        signs = []
        for g in goals:
            fold = logo_results.get(f"leave_out_goal_{g}", {})
            cd = fold.get(contrast, {})
            md = cd.get("mean_score_diff")
            if md is not None:
                signs.append(md > 0)
        stability[contrast] = {
            "always_positive": all(signs),
            "n_folds_positive": sum(signs),
            "n_folds": len(signs),
        }
    logo_results["stability"] = stability
    return logo_results


def build_mechanistic_contrasts(rows: list[dict], proj_rows: list[dict]) -> list[dict]:
    """
    Compute paired projection differences for primary contrasts.
    Uses layer22_first_500_mean_projection as the primary feature.
    Returns a list of per-contrast summary dicts.
    """
    import scipy.stats as stats

    # Build merged lookup by run_id
    proj_by_run = {r["run_id"]: r for r in proj_rows}
    merged_rows = []
    for row in rows:
        pr = proj_by_run.get(row.get("run_id"), {})
        merged_rows.append({**row, **pr})

    results = []
    for layer in [22, 13, 16, 38, 39]:
        for window in ["first_500", "first_2000"]:
            feat = f"layer{layer}_{window}_mean_projection"
            for c1, c2 in [("A", "D"), ("A", "F"), ("D", "F")]:
                source_ids = list(dict.fromkeys(r.get("source_example_id") for r in merged_rows))
                diffs = []
                a_vals, b_vals = [], []
                for sid in source_ids:
                    r1 = next((r for r in merged_rows if r.get("source_example_id") == sid and r.get("condition") == c1), None)
                    r2 = next((r for r in merged_rows if r.get("source_example_id") == sid and r.get("condition") == c2), None)
                    if r1 is None or r2 is None:
                        continue
                    v1 = _f(r1.get(feat))
                    v2 = _f(r2.get(feat))
                    if math.isnan(v1) or math.isnan(v2):
                        continue
                    diffs.append(v1 - v2)
                    a_vals.append(v1)
                    b_vals.append(v2)
                if not diffs:
                    continue
                ci = bootstrap_mean_ci(diffs)
                st = sign_test(diffs)
                # Spearman: projection vs sr_score (for condition c1 only)
                c1_vals = [
                    (_f(r.get(feat)), _f(r.get("strongreject_score")))
                    for r in merged_rows
                    if r.get("condition") == c1
                    and not math.isnan(_f(r.get(feat, float("nan"))))
                    and not math.isnan(_f(r.get("strongreject_score", float("nan"))))
                ]
                rho_sr, p_sr = (None, None)
                if len(c1_vals) >= 4:
                    try:
                        rho_sr, p_sr = stats.spearmanr([v[0] for v in c1_vals], [v[1] for v in c1_vals])
                    except Exception:
                        pass
                # Spearman: projection vs log(think_tokens)
                c1_think = [
                    (_f(r.get(feat)), _f(r.get("think_token_count", 0)))
                    for r in merged_rows
                    if r.get("condition") == c1
                    and not math.isnan(_f(r.get(feat, float("nan"))))
                    and _f(r.get("think_token_count", 0)) > 0
                ]
                rho_think, p_think = (None, None)
                if len(c1_think) >= 4:
                    try:
                        rho_think, p_think = stats.spearmanr(
                            [v[0] for v in c1_think],
                            [math.log(v[1]) for v in c1_think],
                        )
                    except Exception:
                        pass

                results.append({
                    "layer": layer,
                    "window": window,
                    "feature": feat,
                    "contrast": f"{c1}_vs_{c2}",
                    "n_pairs": len(diffs),
                    "mean_diff": ci["mean"],
                    "ci_low_95": ci["ci_low_95"],
                    "ci_high_95": ci["ci_high_95"],
                    "sign_positive": st["n_positive"],
                    "sign_negative": st["n_negative"],
                    "sign_p": st["p_two_sided"],
                    "is_primary": layer == 22 and window == "first_500",
                    f"spearman_rho_vs_sr_score_{c1}": rho_sr,
                    f"spearman_p_vs_sr_score_{c1}": p_sr,
                    f"spearman_rho_vs_log_think_{c1}": rho_think,
                    f"spearman_p_vs_log_think_{c1}": p_think,
                })
    return results


def _write_csv(path: Path, data: list[dict], fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)
    print(f"  wrote {path} ({len(data)} rows)")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Analyze Stage 4.7 replication results.")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=None)
    args = p.parse_args(argv)

    run_dir = args.run_dir
    out_dir = args.output_dir or (run_dir / "analysis")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load rows — prefer canonical CSV (with censoring columns) over raw jsonl
    rows = load_canonical_rows(run_dir)

    # Condition summary (with censoring)
    cond_summary = build_condition_summary_with_censoring(rows)
    _write_csv(
        out_dir / "condition_summary.csv",
        cond_summary,
        list(cond_summary[0].keys()),
    )

    # Paired contrasts (use legacy sr_success so behaviour matches original)
    # but also compute complete-case contrasts separately
    print("\nComputing paired contrasts (n by source prompt) ...")
    contrast_rows, test_results = build_paired_contrasts(rows)
    if contrast_rows:
        _write_csv(
            out_dir / "paired_contrasts.csv",
            contrast_rows,
            list(contrast_rows[0].keys()),
        )

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
    if goal_strat:
        _write_csv(
            out_dir / "goal_stratified_summary.csv",
            goal_strat,
            list(goal_strat[0].keys()),
        )

    # Sensitivity: complete-case vs legacy
    print("\nComputing complete-case vs legacy sensitivity ...")
    sensitivity = build_sensitivity_table(rows)
    with open(out_dir / "sensitivity_summary.json", "w") as f:
        json.dump(sensitivity, f, indent=2)
    print(f"  wrote {out_dir / 'sensitivity_summary.json'}")
    for cond, s in sensitivity.items():
        print(
            f"  {cond}: complete_case={s['complete_case_success']} "
            f"({s['complete_case_rate']:.2f}) | "
            f"legacy={s['legacy_success']} ({s['legacy_rate']:.2f}) | "
            f"censored={s['n_censored']}"
        )

    # Leave-one-goal-out sensitivity
    print("\nComputing leave-one-goal-out sensitivity ...")
    logo = build_logo_sensitivity(rows)
    with open(out_dir / "logo_sensitivity.json", "w") as f:
        json.dump(logo, f, indent=2)
    print(f"  wrote {out_dir / 'logo_sensitivity.json'}")
    stab = logo.get("stability", {})
    for contrast, s in stab.items():
        print(
            f"  {contrast}: always_positive={s['always_positive']} "
            f"({s['n_folds_positive']}/{s['n_folds']} folds)"
        )

    # Mechanistic analysis (if projection data available)
    proj_path = run_dir / "projection_analysis" / "projection_summary.jsonl"
    if proj_path.exists():
        proj_rows = _load_jsonl(proj_path)
        print(f"\nLoaded {len(proj_rows)} projection rows")
        # Merge behavioural + projection
        by_run = {r.get("run_id"): r for r in rows}
        merged = []
        for pr in proj_rows:
            beh = by_run.get(pr.get("run_id"), {})
            merged.append({**beh, **pr})
        if merged:
            _write_csv(
                out_dir / "mechanistic_summary.csv",
                merged,
                list(merged[0].keys()),
            )
        mech_contrasts = build_mechanistic_contrasts(rows, proj_rows)
        if mech_contrasts:
            _write_csv(
                out_dir / "mechanistic_contrasts.csv",
                mech_contrasts,
                list(mech_contrasts[0].keys()),
            )
            print("\n=== Primary Mechanistic Contrasts (L22, first-500 tokens) ===")
            for mc in mech_contrasts:
                if mc.get("is_primary"):
                    print(
                        f"  {mc['contrast']}: mean_diff={mc['mean_diff']:.4f} "
                        f"CI=[{mc['ci_low_95']:.4f},{mc['ci_high_95']:.4f}] "
                        f"signs(+/-) = {mc['sign_positive']}/{mc['sign_negative']}"
                    )
    else:
        print("\n[projection_analysis not yet available — figs 5,6,8 require GPU run]")

    print("\n=== Stage 4.7 Condition Summary ===")
    for r in cond_summary:
        censored_note = f" (censored={r['n_censored']})" if r.get("n_censored") else ""
        print(
            f"  {r['condition']} ({r['condition_label']}): "
            f"{r['n_cc_success']}/{r['n_complete_case']} complete-case success"
            f"{censored_note} | "
            f"mean_score={r['mean_sr_score']:.3f} | "
            f"mean_think={r['mean_think_tokens']:.0f}"
        )

    print("\nAnalysis complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
