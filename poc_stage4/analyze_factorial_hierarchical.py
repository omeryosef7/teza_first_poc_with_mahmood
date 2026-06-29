#!/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
"""analyze_factorial_hierarchical.py

Goal-clustered analysis of factorial interaction effects.

The existing interaction_effects.csv treats the 26 Qwen3 source examples
(or 18 Gemma4) as independent observations. But there are only 11 independent
goals — multiple source puzzles per goal are correlated. This script re-runs
the analysis using goals as the primary clustering unit.

Methods:
1. Goal-level aggregation: compute per-goal mean ASR for each condition,
   then the per-goal interaction (A−E) − (D−G).
2. Hierarchical bootstrap: resample goals (not source examples), then
   resample within each chosen goal.
3. Leave-one-goal-out (LOGO): estimate interaction excluding each goal.
4. Permutation test: shuffle goal labels within each source, test at goal level.

Statistical scope: paired contrasts for model × condition analysis.
Runs on the full factorial_attack_dataset.jsonl (11 goals × multiple sources).

Usage (requires poc_stage2 environment):
    /home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python \
        poc_stage4/analyze_factorial_hierarchical.py \
        [--dataset outputs/stage4/factorial_attack_dataset.jsonl] \
        [--output-dir outputs/stage4/factorial_balanced] \
        [--n-bootstrap 10000] [--n-permutation 10000]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import scipy.stats as stats

SCRIPT_VERSION = "1.0.0"

ALL_CONDITIONS = ("A", "D", "E", "F", "G")
CONTRASTS = {
    "A_minus_E": ("A", "E"),       # puzzle+CoT vs. puzzle-only
    "A_minus_D": ("A", "D"),       # puzzle+CoT vs. bare harmful+CoT
    "A_minus_F": ("A", "F"),       # puzzle+CoT vs. benign filler+CoT
    "D_minus_G": ("D", "G"),       # bare harmful CoT vs. bare harmful no-CoT
    "E_minus_G": ("E", "G"),       # puzzle no-CoT vs. bare harmful no-CoT
}
INTERACTION_KEY = "interaction"  # (A−E) − (D−G)


def load_dataset(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return [r for r in rows if r.get("is_valid", True)]


def aggregate_by_goal(
    rows: list[dict], model: str
) -> dict[int, dict[str, list[float]]]:
    """
    For each goal, collect per-source-example success rates per condition.

    Returns:
        {goal_index: {condition: [mean_sr_for_source1, mean_sr_for_source2, ...]}}
    """
    model_rows = [r for r in rows if r["model_family"] == model]

    # Group: goal → source_id → condition → [sr_success values]
    g_s_c: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in model_rows:
        g_s_c[r["goal_index"]][r["source_example_id"]][r["condition"]].append(
            float(r["sr_success"])
        )

    # Collapse to goal → condition → [source means]
    result: dict[int, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for goal, sources in g_s_c.items():
        for source_id, conds in sources.items():
            for cond, vals in conds.items():
                result[goal][cond].append(float(np.mean(vals)))
    return result


def compute_goal_mean_rates(
    goal_data: dict[int, dict[str, list[float]]],
    require_all_conditions: bool = False,
) -> dict[int, dict[str, Optional[float]]]:
    """
    Compute per-goal mean ASR for each condition (averaging across sources).

    If require_all_conditions, only include goals where all 5 conditions exist.
    """
    result = {}
    for goal, conds in goal_data.items():
        if require_all_conditions and not all(c in conds for c in ALL_CONDITIONS):
            continue
        rates = {}
        for c in ALL_CONDITIONS:
            vals = conds.get(c, [])
            rates[c] = float(np.mean(vals)) if vals else None
        result[goal] = rates
    return result


def compute_interaction(rates: dict[str, Optional[float]]) -> Optional[float]:
    """
    Compute factorial interaction: (A−E) − (D−G).
    Returns None if any required condition is missing.
    """
    if any(rates.get(c) is None for c in ("A", "D", "E", "G")):
        return None
    return (rates["A"] - rates["E"]) - (rates["D"] - rates["G"])


def compute_contrast(rates, c1, c2):
    if rates.get(c1) is None or rates.get(c2) is None:
        return None
    return rates[c1] - rates[c2]


def goal_level_effects(goal_rates: dict[int, dict[str, Optional[float]]]) -> list[dict]:
    """One row per goal with interaction and all contrasts."""
    rows = []
    for goal in sorted(goal_rates.keys()):
        r = goal_rates[goal]
        row = {"goal_index": goal}
        for c in ALL_CONDITIONS:
            row[f"p_{c}"] = r.get(c)
        row[INTERACTION_KEY] = compute_interaction(r)
        for name, (c1, c2) in CONTRASTS.items():
            row[name] = compute_contrast(r, c1, c2)
        rows.append(row)
    return rows


def hierarchical_bootstrap_ci(
    goal_data: dict[int, dict[str, list[float]]],
    estimand_fn,
    n_bootstrap: int = 10000,
    alpha: float = 0.05,
    rng: np.random.Generator = None,
) -> dict:
    """
    Two-level hierarchical bootstrap:
      Level 1: resample goals with replacement
      Level 2: resample sources within each goal with replacement

    estimand_fn: takes goal_mean_rates dict → scalar or None
    Returns: dict with mean, ci_lo, ci_hi, n_goals, n_valid_bootstrap
    """
    if rng is None:
        rng = np.random.default_rng(42)

    goals = sorted(goal_data.keys())
    n_goals = len(goals)

    bootstrap_estimates = []
    for _ in range(n_bootstrap):
        # Level 1: resample goals
        sampled_goals = rng.choice(goals, size=n_goals, replace=True)
        # Level 2: resample sources within each chosen goal
        resampled_rates = {}
        for i, g in enumerate(sampled_goals):
            conds = goal_data[g]
            boot_conds = {}
            for c, vals in conds.items():
                if vals:
                    boot_vals = rng.choice(vals, size=len(vals), replace=True)
                    boot_conds[c] = float(np.mean(boot_vals))
            # Use unique key to allow same goal multiple times
            resampled_rates[i] = boot_conds

        # Aggregate across resampled goals
        all_cond_vals = defaultdict(list)
        for cond_dict in resampled_rates.values():
            for c, v in cond_dict.items():
                all_cond_vals[c].append(v)

        grand_rates = {c: float(np.mean(v)) if v else None for c, v in all_cond_vals.items()}
        est = estimand_fn(grand_rates)
        if est is not None:
            bootstrap_estimates.append(est)

    if not bootstrap_estimates:
        return {"mean": None, "ci_lo": None, "ci_hi": None, "n_goals": n_goals, "n_valid_bootstrap": 0}

    arr = np.array(bootstrap_estimates)
    return {
        "mean": float(np.mean(arr)),
        "ci_lo": float(np.percentile(arr, 100 * alpha / 2)),
        "ci_hi": float(np.percentile(arr, 100 * (1 - alpha / 2))),
        "n_goals": n_goals,
        "n_valid_bootstrap": len(bootstrap_estimates),
        "n_bootstrap": n_bootstrap,
    }


def leave_one_goal_out(
    goal_data: dict[int, dict[str, list[float]]],
    estimand_fn,
) -> list[dict]:
    """
    Compute the estimand excluding one goal at a time.
    Returns list of {left_out_goal, estimate, n_goals_used}.
    """
    goals = sorted(goal_data.keys())
    rows = []
    for held_out in goals:
        remaining = {g: v for g, v in goal_data.items() if g != held_out}
        # Aggregate across remaining goals
        all_cond_vals = defaultdict(list)
        for cond_dict in remaining.values():
            for c, vals in cond_dict.items():
                if vals:
                    all_cond_vals[c].extend(vals)
        grand_rates = {c: float(np.mean(v)) if v else None for c, v in all_cond_vals.items()}
        est = estimand_fn(grand_rates)
        rows.append(
            {
                "left_out_goal": held_out,
                "estimate": est,
                "n_goals_used": len(remaining),
            }
        )
    return rows


def goal_level_permutation_test(
    goal_data: dict[int, dict[str, list[float]]],
    estimand_fn,
    n_permutations: int = 10000,
    rng: np.random.Generator = None,
) -> dict:
    """
    Permutation test at the goal level.

    Under H0: shuffle condition labels within each source, preserving
    the number of observations per condition per source.

    The test statistic is the estimand computed from goal-level means.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    goals = sorted(goal_data.keys())

    # Observed statistic
    all_cond_vals_obs = defaultdict(list)
    for cond_dict in goal_data.values():
        for c, vals in cond_dict.items():
            if vals:
                all_cond_vals_obs[c].extend(vals)
    obs_rates = {c: float(np.mean(v)) if v else None for c, v in all_cond_vals_obs.items()}
    obs_stat = estimand_fn(obs_rates)

    if obs_stat is None:
        return {"p_value": None, "observed_statistic": None, "n_permutations": n_permutations}

    # For each source, collect (condition, mean_sr) pairs
    # Then permute condition labels
    source_records = []
    for g in goals:
        cond_dict = goal_data[g]
        for c, vals in cond_dict.items():
            if vals:
                source_records.append((g, c, float(np.mean(vals))))

    perm_stats = []
    for _ in range(n_permutations):
        # Shuffle condition labels across all (goal, source) observations
        conditions = [r[1] for r in source_records]
        rng.shuffle(conditions)
        # Rebuild goal → condition map
        perm_cond_vals = defaultdict(lambda: defaultdict(list))
        for i, (g, _, val) in enumerate(source_records):
            perm_cond_vals[g][conditions[i]].append(val)

        # Aggregate
        all_cond_vals_perm = defaultdict(list)
        for cond_dict in perm_cond_vals.values():
            for c, vals in cond_dict.items():
                all_cond_vals_perm[c].extend(vals)
        perm_rates = {c: float(np.mean(v)) if v else None for c, v in all_cond_vals_perm.items()}
        est = estimand_fn(perm_rates)
        if est is not None:
            perm_stats.append(est)

    if not perm_stats:
        return {"p_value": None, "observed_statistic": obs_stat, "n_permutations": n_permutations}

    perm_arr = np.array(perm_stats)
    p_value = float(np.mean(np.abs(perm_arr) >= abs(obs_stat)))  # two-tailed
    p_value_one_sided = float(np.mean(perm_arr >= obs_stat))  # test: positive interaction

    return {
        "observed_statistic": obs_stat,
        "p_value_two_tailed": p_value,
        "p_value_one_sided_gt0": p_value_one_sided,
        "n_permutations": n_permutations,
        "n_valid_permutations": len(perm_stats),
        "perm_mean": float(np.mean(perm_arr)),
        "perm_std": float(np.std(perm_arr)),
    }


def sign_test_goal_level(goal_effects: list[dict], key: str) -> dict:
    """
    Sign test: H0 that the estimand is 0, using goals as observations.
    Count goals where the estimand is positive.
    """
    vals = [r[key] for r in goal_effects if r[key] is not None]
    n = len(vals)
    n_positive = sum(1 for v in vals if v > 0)
    n_zero = sum(1 for v in vals if v == 0)
    # Use exact binomial test (two-sided p-value)
    # Under H0: P(positive) = 0.5 (excluding ties)
    n_effective = n - n_zero
    n_positive_eff = sum(1 for v in vals if v > 0)
    if n_effective == 0:
        return {"n_goals": n, "n_positive": n_positive, "p_value": None}

    result = stats.binomtest(n_positive_eff, n_effective, 0.5, alternative="two-sided")
    return {
        "n_goals": n,
        "n_positive": n_positive,
        "n_negative": n - n_positive - n_zero,
        "n_zero": n_zero,
        "n_effective": n_effective,
        "p_value_sign_test": float(result.pvalue),
    }


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=_json_default)


def _json_default(obj):
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Not serializable: {type(obj)}")


def _r(v):
    if v is None:
        return None
    return round(float(v), 4)


def run_analysis_for_model(
    rows: list[dict],
    model: str,
    output_dir: Path,
    n_bootstrap: int,
    n_permutation: int,
) -> dict:
    print(f"\n{'='*60}")
    print(f"Model: {model}")
    print(f"{'='*60}")

    goal_data = aggregate_by_goal(rows, model)
    print(f"  {len(goal_data)} goals with data")

    # Goals with all 5 conditions present
    fully_covered = {
        g: d for g, d in goal_data.items()
        if all(c in d and d[c] for c in ALL_CONDITIONS)
    }
    print(f"  {len(fully_covered)} goals with all 5 conditions")

    # Goal-level effect table
    all_goal_rates = compute_goal_mean_rates(goal_data, require_all_conditions=False)
    goal_effects = goal_level_effects(all_goal_rates)

    # Print per-goal interaction
    print(f"\n  Per-goal interaction (A-E)-(D-G):")
    valid_interactions = [(r["goal_index"], r[INTERACTION_KEY]) for r in goal_effects if r[INTERACTION_KEY] is not None]
    for g, ix in valid_interactions:
        print(f"    goal {g}: {ix:+.3f}")

    # Bootstrap CI (over goals with all 5 conditions)
    rng = np.random.default_rng(42)
    print(f"\n  Hierarchical bootstrap CI (n={n_bootstrap}, goals=clusters)...")

    def interaction_fn(rates):
        return compute_interaction(rates)

    boot_result = hierarchical_bootstrap_ci(
        fully_covered, interaction_fn, n_bootstrap=n_bootstrap, rng=rng
    )
    print(f"    Interaction: {_r(boot_result['mean'])} 95%CI [{_r(boot_result['ci_lo'])}, {_r(boot_result['ci_hi'])}]")

    # LOGO
    print(f"\n  Leave-one-goal-out analysis...")
    logo_rows = leave_one_goal_out(fully_covered, interaction_fn)
    for r in logo_rows:
        print(f"    LOGO goal {r['left_out_goal']}: estimate={_r(r['estimate'])}")

    logo_estimates = [r["estimate"] for r in logo_rows if r["estimate"] is not None]
    print(f"    LOGO range: [{_r(min(logo_estimates))}, {_r(max(logo_estimates))}]" if logo_estimates else "    No valid LOGO estimates.")

    # Permutation test
    print(f"\n  Permutation test (n={n_permutation})...")
    perm_result = goal_level_permutation_test(
        fully_covered, interaction_fn, n_permutations=n_permutation, rng=rng
    )
    print(f"    Observed: {_r(perm_result['observed_statistic'])}")
    print(f"    p-value (two-tailed): {perm_result.get('p_value_two_tailed')}")
    print(f"    p-value (one-sided, > 0): {perm_result.get('p_value_one_sided_gt0')}")

    # Sign test at goal level
    sign = sign_test_goal_level(goal_effects, INTERACTION_KEY)
    print(f"\n  Goal-level sign test: {sign['n_positive']}/{sign['n_goals']} positive  p={_r(sign.get('p_value_sign_test'))}")

    # Individual contrasts bootstrap
    contrast_results = {}
    for name, (c1, c2) in CONTRASTS.items():
        def _contrast_fn(rates, _c1=c1, _c2=c2):
            return compute_contrast(rates, _c1, _c2)

        c_boot = hierarchical_bootstrap_ci(fully_covered, _contrast_fn, n_bootstrap=n_bootstrap, rng=rng)
        contrast_results[name] = c_boot

    # Assemble summary
    summary = {
        "model": model,
        "n_goals_total": len(goal_data),
        "n_goals_fully_covered": len(fully_covered),
        "interaction_observed": _r(perm_result.get("observed_statistic")),
        "interaction_bootstrap_mean": _r(boot_result["mean"]),
        "interaction_bootstrap_ci_lo_95": _r(boot_result["ci_lo"]),
        "interaction_bootstrap_ci_hi_95": _r(boot_result["ci_hi"]),
        "interaction_n_goals_positive": sign["n_positive"],
        "interaction_n_goals_negative": sign.get("n_negative"),
        "interaction_sign_test_p": _r(sign.get("p_value_sign_test")),
        "interaction_permutation_p_two_tailed": perm_result.get("p_value_two_tailed"),
        "interaction_permutation_p_one_sided_gt0": perm_result.get("p_value_one_sided_gt0"),
        "interaction_logo_min": _r(min(logo_estimates)) if logo_estimates else None,
        "interaction_logo_max": _r(max(logo_estimates)) if logo_estimates else None,
        "contrasts": {name: {k: _r(v) if isinstance(v, (float, int)) and v is not None else v for k, v in c_boot.items()} for name, c_boot in contrast_results.items()},
        "n_bootstrap": n_bootstrap,
        "n_permutation": n_permutation,
    }

    # Write per-model outputs
    model_dir = output_dir / model
    model_dir.mkdir(parents=True, exist_ok=True)

    write_csv(model_dir / "goal_level_effects.csv", goal_effects)
    write_csv(model_dir / "leave_one_goal_out_interaction.csv", logo_rows)
    write_json(model_dir / "bootstrap_summary.json", {
        "interaction": boot_result,
        "contrasts": contrast_results,
    })
    write_json(model_dir / "permutation_test.json", perm_result)
    write_json(model_dir / "sign_test.json", sign)

    return summary


def print_final_summary(summaries: dict):
    print("\n" + "="*60)
    print("FINAL SUMMARY (goal-clustered analysis)")
    print("="*60)
    for model, s in summaries.items():
        n_fc = s["n_goals_fully_covered"]
        n_tot = s["n_goals_total"]
        print(f"\n{model.upper()}  ({n_fc}/{n_tot} goals fully covered):")
        print(f"  Interaction: {s['interaction_observed']}")
        print(f"    Bootstrap 95% CI: [{s['interaction_bootstrap_ci_lo_95']}, {s['interaction_bootstrap_ci_hi_95']}]")
        print(f"    Goals positive: {s['interaction_n_goals_positive']}/{n_fc}")
        print(f"    Sign test p:    {s['interaction_sign_test_p']}")
        print(f"    Permutation p:  {s['interaction_permutation_p_two_tailed']} (two-tailed)")
        print(f"    LOGO range:     [{s['interaction_logo_min']}, {s['interaction_logo_max']}]")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path,
                        default=Path("outputs/stage4/factorial_attack_dataset.jsonl"))
    parser.add_argument("--output-dir", type=Path,
                        default=Path("outputs/stage4/factorial_balanced"))
    parser.add_argument("--n-bootstrap", type=int, default=10000)
    parser.add_argument("--n-permutation", type=int, default=10000)
    args = parser.parse_args()

    print(f"Loading dataset from {args.dataset}...")
    rows = load_dataset(args.dataset)
    print(f"  {len(rows)} valid rows loaded.")

    summaries = {}
    for model in ("qwen3", "gemma4"):
        s = run_analysis_for_model(
            rows, model, args.output_dir,
            n_bootstrap=args.n_bootstrap,
            n_permutation=args.n_permutation,
        )
        summaries[model] = s

    # Write combined summary
    write_json(args.output_dir / "goal_clustered_interaction_summary.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script_version": SCRIPT_VERSION,
        "models": summaries,
        "note": (
            "Interaction = (A-E)-(D-G). Bootstrap CIs use hierarchical resampling "
            "(goals as clusters). p-values from goal-level permutation test. "
            "Source-level analyses (existing interaction_effects.csv) treated 26/18 "
            "source examples as independent; goal-level analysis uses 11 independent goals."
        ),
    })

    print_final_summary(summaries)
    print(f"Outputs written to {args.output_dir}/")


if __name__ == "__main__":
    main()
