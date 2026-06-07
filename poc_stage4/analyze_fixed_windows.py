#!/usr/bin/env python3
"""
Phase 2: Fixed-Window Projection Analysis

Compares the provisional refusal-related projection between successful
and failed examples over identical absolute windows at the start of the
thinking phase (first 500, 1000, and 2000 thinking tokens).

Statistical unit: the per-example mean projection (never individual tokens).
Primary outcome: sr_success (strongreject_score >= 0.5).
All 40 layers analysed; layer 22 highlighted as the provisional selected layer
but not treated as automatically optimal.

Outputs
-------
  analysis/fixed_window_per_example.csv      — per-example × window × layer stats
  analysis/fixed_window_group_summary.csv    — group comparisons
  analysis/fixed_window_manifest.json        — run metadata
  plots_analysis_v2/fixed_window_layer22_group_comparison.png
  plots_analysis_v2/fixed_window_effect_by_layer.png
  plots_analysis_v2/fixed_window_mean_difference_by_layer.png
  plots_analysis_v2/fixed_window_sr_correlation_layer22.png

Usage
-----
  python -m poc_stage4.analyze_fixed_windows \\
      --stage4-run-dir outputs/stage4/token_dynamics/full_20260604_101929 \\
      --analysis-dataset outputs/stage4/token_dynamics/full_20260604_101929/analysis/analysis_dataset.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as scipy_stats

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WINDOW_SIZES = [500, 1_000, 2_000]
N_LAYERS = 40
THINK_ROLE = "think"
RANDOM_SEED = 42
N_BOOTSTRAP = 2_000
N_PERMUTATIONS = 10_000
PROVISIONAL_LAYER = 22   # highlighted, not privileged
ALPHA = 0.05

# Colourblind-safe palette (Wong 2011)
COLOR_SUCCESS = "#0072B2"   # blue
COLOR_FAILURE = "#D55E00"   # vermilion
COLOR_JUDGE   = "#009E73"   # green
WINDOW_COLORS = {500: "#56B4E9", 1_000: "#E69F00", 2_000: "#CC79A7"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="python -m poc_stage4.analyze_fixed_windows",
        description="Phase 2: Fixed-Window Projection Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--stage4-run-dir", required=True,
                    help="Stage 4 token-dynamics run directory")
    ap.add_argument("--analysis-dataset", required=True,
                    help="Path to analysis_dataset.csv from Phase 1 audit")
    ap.add_argument("--output-dir", default=None,
                    help="Output directory (default: <stage4-run-dir>/analysis/)")
    ap.add_argument("--plots-dir", default=None,
                    help="Plots directory (default: <stage4-run-dir>/plots_analysis_v2/)")
    ap.add_argument("--window-sizes", type=int, nargs="+", default=WINDOW_SIZES,
                    help=f"Window sizes in think tokens (default: {WINDOW_SIZES})")
    ap.add_argument("--seed", type=int, default=RANDOM_SEED,
                    help=f"Random seed (default: {RANDOM_SEED})")
    ap.add_argument("--n-bootstrap", type=int, default=N_BOOTSTRAP,
                    help=f"Bootstrap iterations (default: {N_BOOTSTRAP})")
    ap.add_argument("--n-permutations", type=int, default=N_PERMUTATIONS,
                    help=f"Permutation iterations (default: {N_PERMUTATIONS})")
    return ap.parse_args()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_analysis_dataset(path: str) -> list[dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # Parse typed fields
    for r in rows:
        r["sr_success"] = r["sr_success"] == "True"
        r["judge_success"] = r["judge_success"] == "True"
        r["right_censored"] = r["right_censored"] == "True"
        r["usable_for_think_analysis"] = r["usable_for_think_analysis"] == "True"
        r["strongreject_score"] = float(r["strongreject_score"])
        r["think_token_count"] = int(r["think_token_count"])
        r["goal_index"] = int(r["goal_index"])
        r["attack_iteration"] = int(r["attack_iteration"])
        r["conversation_id"] = int(r["conversation_id"])
    return rows


def extract_think_projections(
    path: str,
    window_sizes: list[int],
    n_layers: int = N_LAYERS,
) -> dict[int, dict[int, list[float]] | None]:
    """
    Load a per-example JSON and extract per-layer think-token projections.

    Returns {window_size: {layer_idx: [float, ...]}} where each list has
    exactly window_size elements, or {window_size: None} if the example
    does not have enough think tokens for that window.

    Only tokens with role_or_part == 'think' are used.
    Validated: all n_layers layers present, all values finite.
    """
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    think_tokens = [t for t in raw["token_level_data"]
                    if t.get("role_or_part") == THINK_ROLE]
    max_ws = max(window_sizes)

    # Validate the first max_ws think tokens (covers all windows)
    to_validate = think_tokens[:max_ws]
    expected_layer_set = set(range(n_layers))
    for tok_idx, tok in enumerate(to_validate):
        lp = tok["layer_projections"]
        actual = set(int(k) for k in lp.keys())
        if actual != expected_layer_set:
            missing = expected_layer_set - actual
            extra = actual - expected_layer_set
            raise ValueError(
                f"Layer set error in {path} think_token[{tok_idx}]: "
                f"missing={sorted(missing)}, extra={sorted(extra)}"
            )
        for k, v in lp.items():
            if v is None or not math.isfinite(v):
                raise ValueError(
                    f"Non-finite projection at {path} "
                    f"think_token[{tok_idx}] layer={k}: {v!r}"
                )

    result: dict[int, dict[int, list[float]] | None] = {}
    for ws in window_sizes:
        if len(think_tokens) < ws:
            result[ws] = None
            continue
        window_toks = think_tokens[:ws]
        # Final check: exactly ws tokens
        assert len(window_toks) == ws, f"Expected {ws} think tokens, got {len(window_toks)}"
        layer_proj: dict[int, list[float]] = {}
        for li in range(n_layers):
            key = str(li)
            layer_proj[li] = [t["layer_projections"][key] for t in window_toks]
        result[ws] = layer_proj
    return result


# ---------------------------------------------------------------------------
# Per-example statistics
# ---------------------------------------------------------------------------

def window_stats(vals: list[float]) -> dict[str, float]:
    """Compute all required per-example statistics for one layer × window."""
    arr = np.asarray(vals, dtype=np.float64)
    n = len(arr)
    assert n >= 1, "Empty projection list"

    first = float(arr[0])
    last = float(arr[-1])

    # Linear slope via least-squares on token index
    if n >= 2:
        slope, _, _, _, _ = scipy_stats.linregress(np.arange(n), arr)
        # Normalized AUC: area under curve on x in [0,1] via trapezoidal rule
        # = sum of adjacent midpoints, divided by (n-1) intervals
        # comparable across window sizes (units: same as projection)
        norm_auc = float(np.trapezoid(arr, np.linspace(0.0, 1.0, n)))
    else:
        slope = 0.0
        norm_auc = first

    return {
        "token_count_used": n,
        "mean_projection": float(np.mean(arr)),
        "median_projection": float(np.median(arr)),
        "standard_deviation": float(np.std(arr, ddof=1)) if n > 1 else 0.0,
        "minimum_projection": float(np.min(arr)),
        "maximum_projection": float(np.max(arr)),
        "first_projection": first,
        "last_projection": last,
        "projection_change": last - first,
        "linear_slope_over_token_index": float(slope),
        "normalized_auc": norm_auc,
    }


# ---------------------------------------------------------------------------
# Group comparison statistics
# ---------------------------------------------------------------------------

def _pooled_std(a: np.ndarray, b: np.ndarray) -> float:
    n_a, n_b = len(a), len(b)
    if n_a + n_b <= 2:
        return np.nan
    var_a = np.var(a, ddof=1)
    var_b = np.var(b, ddof=1)
    return float(np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)))


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    ps = _pooled_std(a, b)
    if ps == 0 or np.isnan(ps):
        return np.nan
    return float((np.mean(a) - np.mean(b)) / ps)


def hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    d = cohen_d(a, b)
    if np.isnan(d):
        return np.nan
    df = len(a) + len(b) - 2
    if df <= 0:
        return np.nan
    correction = 1.0 - 3.0 / (4.0 * df - 1.0)
    return float(d * correction)


def bootstrap_ci_mean_diff(
    a: np.ndarray, b: np.ndarray, n_boot: int, rng: np.random.Generator
) -> tuple[float, float]:
    """Percentile bootstrap 95% CI on mean(a) - mean(b)."""
    n_a, n_b = len(a), len(b)
    boot_a_idx = rng.integers(0, n_a, size=(n_boot, n_a))
    boot_b_idx = rng.integers(0, n_b, size=(n_boot, n_b))
    diffs = a[boot_a_idx].mean(axis=1) - b[boot_b_idx].mean(axis=1)
    return float(np.percentile(diffs, 100 * ALPHA / 2)), float(np.percentile(diffs, 100 * (1 - ALPHA / 2)))


def permutation_test_mean_diff(
    a: np.ndarray, b: np.ndarray, n_perm: int, rng: np.random.Generator
) -> float:
    """Two-sided permutation p-value for difference in means."""
    observed = abs(np.mean(a) - np.mean(b))
    n_a = len(a)
    pooled = np.concatenate([a, b])
    n = len(pooled)
    perm_idx = np.stack([rng.permutation(n) for _ in range(n_perm)])
    perm_diffs = np.abs(pooled[perm_idx[:, :n_a]].mean(axis=1)
                        - pooled[perm_idx[:, n_a:]].mean(axis=1))
    count = int(np.sum(perm_diffs >= observed))
    return (count + 1) / (n_perm + 1)


def compute_group_stats(
    success_vals: np.ndarray,
    failure_vals: np.ndarray,
    n_boot: int,
    n_perm: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Full group comparison between success and failure per-example means."""
    n_s, n_f = len(success_vals), len(failure_vals)
    if n_s == 0 or n_f == 0:
        return {k: np.nan for k in [
            "success_mean", "failure_mean", "success_std", "failure_std",
            "mean_difference", "cohen_d", "hedges_g",
            "mann_whitney_u", "mann_whitney_p",
            "permutation_p", "bootstrap_ci_low", "bootstrap_ci_high",
        ]} | {"n_success": n_s, "n_failure": n_f}

    s_mean = float(np.mean(success_vals))
    f_mean = float(np.mean(failure_vals))
    s_std = float(np.std(success_vals, ddof=1)) if n_s > 1 else 0.0
    f_std = float(np.std(failure_vals, ddof=1)) if n_f > 1 else 0.0

    # Mann-Whitney U (two-sided)
    mw_result = scipy_stats.mannwhitneyu(
        success_vals, failure_vals, alternative="two-sided"
    )

    ci_low, ci_high = bootstrap_ci_mean_diff(success_vals, failure_vals, n_boot, rng)
    perm_p = permutation_test_mean_diff(success_vals, failure_vals, n_perm, rng)

    return {
        "n_success": n_s,
        "n_failure": n_f,
        "success_mean": s_mean,
        "failure_mean": f_mean,
        "success_std": s_std,
        "failure_std": f_std,
        "mean_difference": s_mean - f_mean,
        "cohen_d": cohen_d(success_vals, failure_vals),
        "hedges_g": hedges_g(success_vals, failure_vals),
        "mann_whitney_u": float(mw_result.statistic),
        "mann_whitney_p": float(mw_result.pvalue),
        "permutation_p": perm_p,
        "bootstrap_ci_low": ci_low,
        "bootstrap_ci_high": ci_high,
    }


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def _layer22_label(ax: plt.Axes) -> None:
    ax.axvline(x=PROVISIONAL_LAYER, color="gray", linestyle="--", linewidth=0.8,
               alpha=0.7, label=f"Layer {PROVISIONAL_LAYER} (provisional)")


def plot_layer22_group_comparison(
    per_example_rows: list[dict[str, Any]],
    window_sizes: list[int],
    output_path: str,
) -> None:
    """
    Strip-plot + box for layer-22 mean projection, success vs. failure,
    one panel per window size.
    """
    fig, axes = plt.subplots(1, len(window_sizes), figsize=(5 * len(window_sizes), 5),
                             sharey=False)
    if len(window_sizes) == 1:
        axes = [axes]

    for ax, ws in zip(axes, window_sizes):
        ws_rows = [r for r in per_example_rows
                   if r["window_size"] == ws and r["layer"] == PROVISIONAL_LAYER]
        if not ws_rows:
            ax.set_title(f"{ws} tokens\n(no data)")
            continue

        s_vals = np.array([r["mean_projection"] for r in ws_rows if r["sr_success"]])
        f_vals = np.array([r["mean_projection"] for r in ws_rows if not r["sr_success"]])

        # strip (jitter)
        rng_jitter = np.random.default_rng(0)
        for vals, color, label, x_center in [
            (s_vals, COLOR_SUCCESS, "Success", 0),
            (f_vals, COLOR_FAILURE, "Failure", 1),
        ]:
            if len(vals) == 0:
                continue
            jitter = rng_jitter.uniform(-0.15, 0.15, size=len(vals))
            ax.scatter(x_center + jitter, vals, color=color, alpha=0.6,
                       s=30, zorder=3, label=f"{label} (n={len(vals)})")
            # group mean
            ax.hlines(np.mean(vals), x_center - 0.3, x_center + 0.3,
                      colors=color, linewidths=2.5, zorder=4)
            # ±1 SD
            m, sd = np.mean(vals), np.std(vals, ddof=1) if len(vals) > 1 else 0
            ax.errorbar(x_center, m, yerr=sd, fmt="none",
                        ecolor=color, elinewidth=1.5, capsize=4, zorder=4)

        ax.set_xlim(-0.5, 1.5)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Success", "Failure"])
        ax.set_title(f"First {ws:,} think tokens\n"
                     f"n_s={len(s_vals)}, n_f={len(f_vals)}")
        ax.set_ylabel("Layer-22 mean projection")
        ax.legend(fontsize=8, loc="upper right")
        ax.axhline(0, color="black", linewidth=0.5, alpha=0.3)

    fig.suptitle("Layer-22 Provisional Projection — Fixed Absolute Windows\n"
                 "(Horizontal bar = group mean ± 1 SD; primary outcome: sr_success)",
                 fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


def plot_effect_by_layer(
    group_summary_rows: list[dict[str, Any]],
    window_sizes: list[int],
    output_path: str,
    metric: str = "hedges_g",
    ylabel: str = "Hedges' g",
) -> None:
    """Effect size by layer, one line per window."""
    fig, ax = plt.subplots(figsize=(12, 5))
    for ws in window_sizes:
        ws_rows = sorted(
            [r for r in group_summary_rows if r["window_size"] == ws and r["subset"] == "all"],
            key=lambda r: r["layer"]
        )
        if not ws_rows:
            continue
        layers = [r["layer"] for r in ws_rows]
        vals = [r[metric] for r in ws_rows]
        ax.plot(layers, vals, color=WINDOW_COLORS[ws], linewidth=1.5,
                label=f"{ws:,} tokens (n={ws_rows[0]['n_success']}+{ws_rows[0]['n_failure']})")

    ax.axvline(PROVISIONAL_LAYER, color="gray", linestyle="--", linewidth=1, alpha=0.8,
               label=f"Layer {PROVISIONAL_LAYER} (provisional)")
    ax.axhline(0, color="black", linewidth=0.5, alpha=0.3)
    ax.set_xlabel("Layer (0–39)")
    ax.set_ylabel(ylabel)
    ax.set_title(f"Fixed-Window Projection — {ylabel} by Layer\n"
                 f"(success − failure, sr_success primary; subset='all')")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


def plot_mean_difference_by_layer(
    group_summary_rows: list[dict[str, Any]],
    window_sizes: list[int],
    output_path: str,
) -> None:
    """Mean difference (success − failure) by layer with bootstrap CI for layer 22."""
    fig, ax = plt.subplots(figsize=(12, 5))
    for ws in window_sizes:
        ws_rows = sorted(
            [r for r in group_summary_rows if r["window_size"] == ws and r["subset"] == "all"],
            key=lambda r: r["layer"]
        )
        if not ws_rows:
            continue
        layers = [r["layer"] for r in ws_rows]
        diffs = [r["mean_difference"] for r in ws_rows]
        ax.plot(layers, diffs, color=WINDOW_COLORS[ws], linewidth=1.5,
                label=f"{ws:,} tokens")
        # Mark L22 CI if available
        l22 = next((r for r in ws_rows if r["layer"] == PROVISIONAL_LAYER), None)
        if l22 and not math.isnan(l22.get("bootstrap_ci_low", float("nan"))):
            ax.errorbar(PROVISIONAL_LAYER, l22["mean_difference"],
                        yerr=[[l22["mean_difference"] - l22["bootstrap_ci_low"]],
                              [l22["bootstrap_ci_high"] - l22["mean_difference"]]],
                        fmt="o", color=WINDOW_COLORS[ws], capsize=4, linewidth=1.5, zorder=5)

    ax.axvline(PROVISIONAL_LAYER, color="gray", linestyle="--", linewidth=1, alpha=0.8,
               label=f"Layer {PROVISIONAL_LAYER}")
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Layer (0–39)")
    ax.set_ylabel("Mean projection difference (success − failure)")
    ax.set_title("Fixed-Window Mean Projection Difference by Layer\n"
                 "(Error bars at layer 22 = 95% bootstrap CI; sr_success primary)")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


def plot_sr_correlation_layer22(
    per_example_rows: list[dict[str, Any]],
    window_sizes: list[int],
    output_path: str,
) -> None:
    """SR score vs. layer-22 mean projection, one panel per window."""
    fig, axes = plt.subplots(1, len(window_sizes), figsize=(5 * len(window_sizes), 5),
                             sharey=False)
    if len(window_sizes) == 1:
        axes = [axes]

    for ax, ws in zip(axes, window_sizes):
        ws_rows = [r for r in per_example_rows
                   if r["window_size"] == ws and r["layer"] == PROVISIONAL_LAYER]
        if not ws_rows:
            ax.set_title(f"{ws} tokens\n(no data)")
            continue

        sr_scores = np.array([r["strongreject_score"] for r in ws_rows])
        proj_vals = np.array([r["mean_projection"] for r in ws_rows])
        colors = [COLOR_SUCCESS if r["sr_success"] else COLOR_FAILURE for r in ws_rows]

        ax.scatter(sr_scores, proj_vals, c=colors, alpha=0.7, s=40, zorder=3)

        # Correlations
        if len(sr_scores) >= 3:
            p_r, p_p = scipy_stats.pearsonr(sr_scores, proj_vals)
            sp_r, sp_p = scipy_stats.spearmanr(sr_scores, proj_vals)
            # Regression line
            slope, intercept, *_ = scipy_stats.linregress(sr_scores, proj_vals)
            x_range = np.linspace(sr_scores.min(), sr_scores.max(), 100)
            ax.plot(x_range, slope * x_range + intercept,
                    color="gray", linewidth=1, linestyle="--", alpha=0.7)
            ax.text(0.03, 0.97,
                    f"Pearson r={p_r:.2f} (p={p_p:.3f})\n"
                    f"Spearman ρ={sp_r:.2f} (p={sp_p:.3f})\n"
                    f"n={len(sr_scores)}",
                    transform=ax.transAxes, fontsize=8, va="top",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

        ax.set_xlabel("StrongREJECT score (continuous)")
        ax.set_ylabel("Layer-22 mean projection")
        ax.set_title(f"First {ws:,} think tokens")
        # Legend patches
        from matplotlib.patches import Patch
        ax.legend(handles=[
            Patch(color=COLOR_SUCCESS, label="sr_success=True"),
            Patch(color=COLOR_FAILURE, label="sr_success=False"),
        ], fontsize=8, loc="lower right")

    fig.suptitle("Layer-22 Projection vs. StrongREJECT Score (Continuous)\n"
                 "Note: SR scores are highly discrete; interpret correlations cautiously.",
                 fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    s4_run = Path(args.stage4_run_dir)
    out_dir = Path(args.output_dir or s4_run / "analysis")
    plots_dir = Path(args.plots_dir or s4_run / "plots_analysis_v2")
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    per_example_dir = s4_run / "per_example"
    window_sizes = sorted(args.window_sizes)
    rng = np.random.default_rng(args.seed)

    # ------------------------------------------------------------------
    # Load analysis dataset
    # ------------------------------------------------------------------
    print(f"[fw] Loading analysis dataset: {args.analysis_dataset}")
    dataset = load_analysis_dataset(args.analysis_dataset)
    eligible = [r for r in dataset if r["usable_for_think_analysis"]]
    print(f"[fw] Total examples: {len(dataset)}  |  usable_for_think: {len(eligible)}")

    # ------------------------------------------------------------------
    # Load projections and compute per-example statistics
    # ------------------------------------------------------------------
    per_example_rows: list[dict[str, Any]] = []
    inclusion: dict[int, dict[str, int]] = {ws: {"included": 0, "excluded_few_tokens": 0,
                                                  "excluded_not_usable": 0}
                                             for ws in window_sizes}
    total_not_usable = len(dataset) - len(eligible)

    print(f"[fw] Computing per-example statistics for {len(eligible)} examples ...")
    for idx, meta in enumerate(eligible, 1):
        example_id = meta["example_id"]
        per_ex_path = str(per_example_dir / f"{_id_to_filename(example_id)}.json")
        print(f"[fw]   {idx:2d}/{len(eligible)}: {example_id[:60]}", end="\r")

        try:
            projections = extract_think_projections(per_ex_path, window_sizes)
        except (FileNotFoundError, ValueError) as exc:
            print(f"\n[fw] ERROR loading {per_ex_path}: {exc}", file=sys.stderr)
            for ws in window_sizes:
                inclusion[ws]["excluded_not_usable"] += 1
            continue

        for ws in window_sizes:
            lp = projections[ws]
            if lp is None:
                inclusion[ws]["excluded_few_tokens"] += 1
                continue
            inclusion[ws]["included"] += 1
            for layer in range(N_LAYERS):
                s = window_stats(lp[layer])
                per_example_rows.append({
                    "example_id": example_id,
                    "goal_index": meta["goal_index"],
                    "attack_iteration": meta["attack_iteration"],
                    "conversation_id": meta["conversation_id"],
                    "target_model": meta["target_model"],
                    "sr_success": meta["sr_success"],
                    "strongreject_score": meta["strongreject_score"],
                    "judge_success": meta["judge_success"],
                    "right_censored": meta["right_censored"],
                    "window_size": ws,
                    "layer": layer,
                    **s,
                })

    print(f"\n[fw] Per-example rows computed: {len(per_example_rows)}")

    # ------------------------------------------------------------------
    # Inclusion / exclusion report
    # ------------------------------------------------------------------
    print(f"\n[fw] Inclusion per window (usable_for_think_analysis=True baseline):")
    for ws in window_sizes:
        inc = inclusion[ws]
        print(f"  {ws:5d} tokens: included={inc['included']}  "
              f"excl_few_tokens={inc['excluded_few_tokens']}  "
              f"excl_not_usable={inc['excluded_not_usable']}")

    # Validate counts
    for ws in window_sizes:
        included_ids = set(r["example_id"]
                           for r in per_example_rows
                           if r["window_size"] == ws and r["layer"] == 0)
        n_s = sum(1 for r in per_example_rows
                  if r["window_size"] == ws and r["layer"] == 0 and r["sr_success"])
        n_f = sum(1 for r in per_example_rows
                  if r["window_size"] == ws and r["layer"] == 0 and not r["sr_success"])
        print(f"  {ws:5d} tokens: n_success={n_s}  n_failure={n_f}  "
              f"total={n_s + n_f}")

    # ------------------------------------------------------------------
    # Compute group summary statistics
    # ------------------------------------------------------------------
    print(f"\n[fw] Computing group statistics ...")
    group_summary_rows: list[dict[str, Any]] = []

    # Two subsets: all eligible, and excluding right-censored
    subsets = {
        "all": lambda r: True,
        "excl_censored": lambda r: not r["right_censored"],
    }

    for ws in window_sizes:
        ws_rows_l0 = {r["example_id"]: r
                      for r in per_example_rows
                      if r["window_size"] == ws and r["layer"] == 0}

        for layer in range(N_LAYERS):
            # Build per-layer index: example_id → mean_projection
            layer_means = {
                r["example_id"]: r["mean_projection"]
                for r in per_example_rows
                if r["window_size"] == ws and r["layer"] == layer
            }

            for subset_name, subset_fn in subsets.items():
                eligible_ids = [eid for eid, r in ws_rows_l0.items()
                                if subset_fn(r)]

                s_vals = np.array([layer_means[eid] for eid in eligible_ids
                                   if ws_rows_l0[eid]["sr_success"]])
                f_vals = np.array([layer_means[eid] for eid in eligible_ids
                                   if not ws_rows_l0[eid]["sr_success"]])

                stats_dict = compute_group_stats(s_vals, f_vals,
                                                 args.n_bootstrap, args.n_permutations, rng)

                # Secondary: judge_success (descriptive only; n too small for tests)
                j_vals = np.array([layer_means[eid] for eid in eligible_ids
                                   if ws_rows_l0[eid]["judge_success"]])
                nj_vals = np.array([layer_means[eid] for eid in eligible_ids
                                    if not ws_rows_l0[eid]["judge_success"]])

                group_summary_rows.append({
                    "window_size": ws,
                    "layer": layer,
                    "subset": subset_name,
                    **stats_dict,
                    "n_judge_success": len(j_vals),
                    "n_judge_failure": len(nj_vals),
                    "judge_success_mean": float(np.mean(j_vals)) if len(j_vals) else float("nan"),
                    "judge_failure_mean": float(np.mean(nj_vals)) if len(nj_vals) else float("nan"),
                })

        print(f"  window={ws:5d} done")

    # ------------------------------------------------------------------
    # Write CSV outputs
    # ------------------------------------------------------------------
    # per-example
    pe_path = out_dir / "fixed_window_per_example.csv"
    if per_example_rows:
        fieldnames = list(per_example_rows[0].keys())
        with open(pe_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(per_example_rows)
        print(f"\n[fw] Wrote {pe_path}  ({len(per_example_rows)} rows)")

    # group summary
    gs_path = out_dir / "fixed_window_group_summary.csv"
    if group_summary_rows:
        fieldnames_gs = list(group_summary_rows[0].keys())
        with open(gs_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames_gs)
            w.writeheader()
            w.writerows(group_summary_rows)
        print(f"[fw] Wrote {gs_path}  ({len(group_summary_rows)} rows)")

    # ------------------------------------------------------------------
    # Manifest
    # ------------------------------------------------------------------
    manifest = {
        "artifact_version": "fixed_window_analysis_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "stage4_run_directory": str(s4_run),
        "analysis_dataset": str(args.analysis_dataset),
        "per_example_directory": str(per_example_dir),
        "window_sizes": window_sizes,
        "layers_analyzed": list(range(N_LAYERS)),
        "provisional_layer": PROVISIONAL_LAYER,
        "primary_binary_outcome": "sr_success = strongreject_score >= 0.5",
        "primary_continuous_outcome": "strongreject_score",
        "secondary_binary_outcome": "judge_success = judge_score == 10",
        "statistical_unit": "per-example mean projection (not individual tokens)",
        "random_seed": args.seed,
        "n_bootstrap": args.n_bootstrap,
        "n_permutations": args.n_permutations,
        "bootstrap_ci_level": f"{int(100 * (1 - ALPHA))}%",
        "permutation_test": "two-sided, absolute difference in means",
        "normalized_auc_definition": (
            "Area under the projection curve when x is normalized to [0,1]: "
            "np.trapz(projections, np.linspace(0, 1, len(projections))). "
            "Approximates the mean value of the function; comparable across window sizes."
        ),
        "think_role_only": True,
        "assistant_or_special_tokens_excluded": True,
        "subsets": {
            "all": "all eligible examples with usable_for_think_analysis=True and sufficient think tokens",
            "excl_censored": "same but excluding right_censored=True examples",
        },
        "inclusion_counts": {
            str(ws): {
                "eligible_base": len(eligible),
                **inclusion[ws],
            }
            for ws in window_sizes
        },
        "output_files": {
            "per_example_csv": str(pe_path),
            "group_summary_csv": str(gs_path),
        },
    }
    manifest_path = out_dir / "fixed_window_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[fw] Wrote {manifest_path}")

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    print(f"\n[fw] Generating plots ...")
    plot_layer22_group_comparison(
        per_example_rows, window_sizes,
        str(plots_dir / "fixed_window_layer22_group_comparison.png")
    )
    plot_effect_by_layer(
        group_summary_rows, window_sizes,
        str(plots_dir / "fixed_window_effect_by_layer.png"),
        metric="hedges_g", ylabel="Hedges' g"
    )
    plot_mean_difference_by_layer(
        group_summary_rows, window_sizes,
        str(plots_dir / "fixed_window_mean_difference_by_layer.png")
    )
    plot_sr_correlation_layer22(
        per_example_rows, window_sizes,
        str(plots_dir / "fixed_window_sr_correlation_layer22.png")
    )

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------
    print()
    print("=" * 72)
    print("  FIXED-WINDOW ANALYSIS SUMMARY")
    print("=" * 72)
    print("  Primary outcome: sr_success  |  Layer 22 = provisional only")
    print()

    for ws in window_sizes:
        ws_l22_all = next(
            (r for r in group_summary_rows
             if r["window_size"] == ws and r["layer"] == PROVISIONAL_LAYER and r["subset"] == "all"),
            None
        )
        ws_l22_excl = next(
            (r for r in group_summary_rows
             if r["window_size"] == ws and r["layer"] == PROVISIONAL_LAYER and r["subset"] == "excl_censored"),
            None
        )
        # Best layer by abs(hedges_g)
        ws_all = [r for r in group_summary_rows if r["window_size"] == ws and r["subset"] == "all"]
        best = max(ws_all, key=lambda r: abs(r["hedges_g"]) if not math.isnan(r["hedges_g"]) else 0)

        print(f"  Window = {ws:,} tokens")
        if ws_l22_all:
            r = ws_l22_all
            ci_str = (f"[{r['bootstrap_ci_low']:.3f}, {r['bootstrap_ci_high']:.3f}]"
                      if not math.isnan(r.get("bootstrap_ci_low", float("nan"))) else "n/a")
            print(f"    Layer 22 (ALL subset):")
            print(f"      n_success={r['n_success']}  n_failure={r['n_failure']}")
            print(f"      success_mean={r['success_mean']:.4f}  "
                  f"failure_mean={r['failure_mean']:.4f}  "
                  f"diff={r['mean_difference']:.4f}")
            print(f"      Cohen's d={r['cohen_d']:.3f}  Hedges' g={r['hedges_g']:.3f}")
            print(f"      MWU p={r['mann_whitney_p']:.4f}  perm_p={r['permutation_p']:.4f}")
            print(f"      Bootstrap 95% CI on diff: {ci_str}")
        if ws_l22_excl:
            r = ws_l22_excl
            print(f"    Layer 22 (excl_censored):")
            print(f"      n_success={r['n_success']}  n_failure={r['n_failure']}  "
                  f"diff={r['mean_difference']:.4f}  g={r['hedges_g']:.3f}")
        print(f"    Best layer by |Hedges' g| (all): "
              f"layer={best['layer']}  g={best['hedges_g']:.3f}  "
              f"diff={best['mean_difference']:.4f}")
        print()

    # Direction check
    print("  Direction of layer-22 effect (success > failure = positive):")
    for ws in window_sizes:
        r = next((r for r in group_summary_rows
                  if r["window_size"] == ws and r["layer"] == PROVISIONAL_LAYER
                  and r["subset"] == "all"), None)
        if r:
            direction = "positive (success > failure)" if r["mean_difference"] > 0 else "negative (success < failure)"
            print(f"    {ws:5d} tokens: {direction}  (diff={r['mean_difference']:.4f})")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _id_to_filename(example_id: str) -> str:
    """Convert example_id to per-example filename stem."""
    # e.g. "goal_index=0|attack_iteration=1|conversation_id=1|target_model=gpt-o4-mini"
    # → "goal_index_0_attack_iteration_1_conversation_id_1_target_model_gpt-o4-mini"
    return (example_id
            .replace("goal_index=", "goal_index_")
            .replace("|attack_iteration=", "_attack_iteration_")
            .replace("|conversation_id=", "_conversation_id_")
            .replace("|target_model=", "_target_model_"))


if __name__ == "__main__":
    main()
