#!/usr/bin/env python3
"""
Phase 3: Normalized-Progress Projection Analysis

Divides each thinking sequence into 10 equal normalized-progress bins and
compares the provisional refusal-related projection between successful and
failed examples across all bins at all 40 layers.

Statistical unit: the per-example mean projection within each bin (never
individual tokens).  Primary outcome: sr_success (strongreject_score >= 0.5).
All 40 layers analysed; layer 22 highlighted as the provisional selected layer
but not treated as automatically optimal.

Benjamini–Hochberg correction applied over all 40 × 10 = 400 tests per subset.

Outputs
-------
  analysis/normalized_progress_per_example.csv    — 41×40×10 = 16,400 rows
  analysis/normalized_progress_group_summary.csv  — 40×10×2  =    800 rows
  analysis/normalized_progress_manifest.json      — run metadata + pkg versions
  plots_analysis_v2/normalized_progress_layer22.png
  plots_analysis_v2/normalized_progress_layer22_difference.png
  plots_analysis_v2/normalized_progress_effect_heatmap.png
  plots_analysis_v2/normalized_progress_mean_difference_heatmap.png
  plots_analysis_v2/normalized_progress_selected_layers.png
  plots_analysis_v2/earliest_divergence_by_layer.png

Usage
-----
  python -m poc_stage4.analyze_normalized_progress \\
      --stage4-run-dir outputs/stage4/token_dynamics/full_20260604_101929 \\
      --analysis-dataset outputs/stage4/token_dynamics/full_20260604_101929/analysis/analysis_dataset.csv
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
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import scipy
from scipy import stats as scipy_stats
from scipy.stats import false_discovery_control

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

N_LAYERS = 40
N_BINS = 10
THINK_ROLE = "think"
RANDOM_SEED = 42
N_BOOTSTRAP = 2_000
N_PERMUTATIONS = 10_000
PROVISIONAL_LAYER = 22
ALPHA = 0.05
SELECTED_LAYERS = [13, 16, 22, 26, 30, 39]

BIN_LABELS = [f"{i*10}–{(i+1)*10}%" for i in range(N_BINS)]
BIN_START_FRACTIONS = [i / N_BINS for i in range(N_BINS)]
BIN_END_FRACTIONS = [(i + 1) / N_BINS for i in range(N_BINS)]

# Colourblind-safe palette (Wong 2011)
COLOR_SUCCESS = "#0072B2"
COLOR_FAILURE = "#D55E00"
COLOR_SUCCESS_CI = "#80B9D9"
COLOR_FAILURE_CI = "#EAB090"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="python -m poc_stage4.analyze_normalized_progress",
        description="Phase 3: Normalized-Progress Projection Analysis",
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
    ap.add_argument("--n-bins", type=int, default=N_BINS,
                    help=f"Number of normalized-progress bins (default: {N_BINS})")
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


def _id_to_filename(example_id: str) -> str:
    """Convert example_id to per-example filename stem."""
    return (example_id
            .replace("goal_index=", "goal_index_")
            .replace("|attack_iteration=", "_attack_iteration_")
            .replace("|conversation_id=", "_conversation_id_")
            .replace("|target_model=", "_target_model_"))


# ---------------------------------------------------------------------------
# Binning
# ---------------------------------------------------------------------------

def assign_bins(n_tokens: int, n_bins: int = N_BINS) -> list[int]:
    """
    Assign each token index (0..n_tokens-1) to one of n_bins bins using
    equal-size partitioning. Bins are indexed 0..n_bins-1.

    Boundary rule: boundaries[b] = round(b * n_tokens / n_bins) for b in
    range(n_bins+1). Bin b contains tokens at positions [boundaries[b],
    boundaries[b+1]).  This guarantees every token is in exactly one bin and
    sum(bin_sizes) == n_tokens, with sizes differing by at most 1.
    """
    boundaries = [round(i * n_tokens / n_bins) for i in range(n_bins + 1)]
    assignments: list[int] = []
    for b in range(n_bins):
        for _ in range(boundaries[b + 1] - boundaries[b]):
            assignments.append(b)
    assert len(assignments) == n_tokens, (
        f"Bin assignment length mismatch: {len(assignments)} != {n_tokens}"
    )
    return assignments


# ---------------------------------------------------------------------------
# Per-example extraction
# ---------------------------------------------------------------------------

def bin_stats(vals: np.ndarray) -> dict[str, Any]:
    """Compute required statistics for one bin's token projections."""
    n = len(vals)
    assert n >= 1, "Empty bin — should not happen for valid binning"
    first = float(vals[0])
    last = float(vals[-1])
    if n >= 2:
        slope_result = scipy_stats.linregress(np.arange(n, dtype=np.float64), vals)
        slope = float(slope_result.slope)
    else:
        slope = 0.0
    return {
        "token_count_in_bin": n,
        "mean_projection": float(np.mean(vals)),
        "median_projection": float(np.median(vals)),
        "standard_deviation": float(np.std(vals, ddof=1)) if n > 1 else 0.0,
        "minimum_projection": float(np.min(vals)),
        "maximum_projection": float(np.max(vals)),
        "first_projection": first,
        "last_projection": last,
        "projection_change": last - first,
        "linear_slope_within_bin": slope,
    }


def extract_think_bins_for_example(
    path: str,
    n_bins: int = N_BINS,
    n_layers: int = N_LAYERS,
) -> dict[str, Any]:
    """
    Load per-example JSON, extract think tokens, assign to bins, and compute
    per-bin statistics for all layers.

    Returns:
      think_token_count    int
      bin_boundaries       list[int] of length n_bins+1
      layer_bin_stats      dict[int, dict[int, dict]]  layer → bin → stats
    """
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    think_tokens = [t for t in raw["token_level_data"]
                    if t.get("role_or_part") == THINK_ROLE]
    N = len(think_tokens)
    if N == 0:
        raise ValueError(f"No think tokens in {path}")

    # Validate layers on first token (spot-check)
    expected_keys = set(str(i) for i in range(n_layers))
    first_lp = think_tokens[0]["layer_projections"]
    actual_keys = set(first_lp.keys())
    if actual_keys != expected_keys:
        missing = expected_keys - actual_keys
        raise ValueError(f"Layer key mismatch in {path}: missing={sorted(missing)}")

    # Build projection matrix [N × n_layers] for efficiency
    layer_keys = [str(li) for li in range(n_layers)]
    proj_matrix = np.empty((N, n_layers), dtype=np.float64)
    for i, tok in enumerate(think_tokens):
        lp = tok["layer_projections"]
        for li, k in enumerate(layer_keys):
            proj_matrix[i, li] = lp[k]

    # Validate finiteness on a sample (first and last token)
    for check_i in [0, N - 1]:
        row = proj_matrix[check_i]
        if not np.all(np.isfinite(row)):
            bad = np.where(~np.isfinite(row))[0].tolist()
            raise ValueError(f"Non-finite projections at token {check_i} in {path}: layers={bad}")

    # Assign bins
    bin_assignments = assign_bins(N, n_bins)
    boundaries = [round(i * N / n_bins) for i in range(n_bins + 1)]
    bin_arr = np.array(bin_assignments, dtype=np.int32)

    # Compute per-layer × per-bin statistics
    layer_bin_stats: dict[int, dict[int, dict[str, Any]]] = {}
    for li in range(n_layers):
        layer_proj = proj_matrix[:, li]
        layer_bin_stats[li] = {}
        for b in range(n_bins):
            mask = bin_arr == b
            vals = layer_proj[mask]
            if len(vals) == 0:
                continue
            layer_bin_stats[li][b] = bin_stats(vals)

    return {
        "think_token_count": N,
        "bin_boundaries": boundaries,
        "layer_bin_stats": layer_bin_stats,
    }


# ---------------------------------------------------------------------------
# Group comparison statistics
# ---------------------------------------------------------------------------

def _pooled_std(a: np.ndarray, b: np.ndarray) -> float:
    n_a, n_b = len(a), len(b)
    if n_a + n_b <= 2:
        return float("nan")
    var_a = float(np.var(a, ddof=1))
    var_b = float(np.var(b, ddof=1))
    return float(np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)))


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    ps = _pooled_std(a, b)
    if math.isnan(ps) or ps == 0.0:
        return float("nan")
    return float((np.mean(a) - np.mean(b)) / ps)


def hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    d = cohen_d(a, b)
    if math.isnan(d):
        return float("nan")
    df = len(a) + len(b) - 2
    if df <= 0:
        return float("nan")
    return float(d * (1.0 - 3.0 / (4.0 * df - 1.0)))


def bootstrap_ci_mean_diff(
    a: np.ndarray, b: np.ndarray, n_boot: int, rng: np.random.Generator,
) -> tuple[float, float]:
    """Percentile bootstrap 95% CI on mean(a) - mean(b)."""
    n_a, n_b = len(a), len(b)
    boot_a = rng.integers(0, n_a, size=(n_boot, n_a))
    boot_b = rng.integers(0, n_b, size=(n_boot, n_b))
    diffs = a[boot_a].mean(axis=1) - b[boot_b].mean(axis=1)
    return (float(np.percentile(diffs, 100 * ALPHA / 2)),
            float(np.percentile(diffs, 100 * (1 - ALPHA / 2))))


def bootstrap_ci_group_mean(
    vals: np.ndarray, n_boot: int, rng: np.random.Generator,
) -> tuple[float, float]:
    """Percentile bootstrap 95% CI on the mean of a single group."""
    n = len(vals)
    if n < 2:
        m = float(np.mean(vals)) if n == 1 else float("nan")
        return m, m
    boot_idx = rng.integers(0, n, size=(n_boot, n))
    boot_means = vals[boot_idx].mean(axis=1)
    return (float(np.percentile(boot_means, 100 * ALPHA / 2)),
            float(np.percentile(boot_means, 100 * (1 - ALPHA / 2))))


def permutation_test_mean_diff(
    a: np.ndarray, b: np.ndarray, n_perm: int, rng: np.random.Generator,
) -> float:
    """Two-sided permutation p-value for difference in means."""
    observed = abs(float(np.mean(a) - np.mean(b)))
    n_a = len(a)
    pooled = np.concatenate([a, b])
    n = len(pooled)
    perm_idx = np.stack([rng.permutation(n) for _ in range(n_perm)])
    perm_diffs = np.abs(
        pooled[perm_idx[:, :n_a]].mean(axis=1) - pooled[perm_idx[:, n_a:]].mean(axis=1)
    )
    return (int(np.sum(perm_diffs >= observed)) + 1) / (n_perm + 1)


def compute_group_stats(
    success_vals: np.ndarray,
    failure_vals: np.ndarray,
    n_boot: int,
    n_perm: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Full group comparison including per-group bootstrap CIs for trajectory plots."""
    n_s, n_f = len(success_vals), len(failure_vals)
    nan = float("nan")

    if n_s == 0 or n_f == 0:
        return {
            "n_success": n_s, "n_failure": n_f,
            "success_mean": nan, "failure_mean": nan,
            "success_std": nan, "failure_std": nan,
            "mean_difference": nan,
            "cohen_d": nan, "hedges_g": nan,
            "success_ci_low": nan, "success_ci_high": nan,
            "failure_ci_low": nan, "failure_ci_high": nan,
            "mann_whitney_u": nan, "mann_whitney_p": nan,
            "permutation_p": nan,
            "bootstrap_ci_low": nan, "bootstrap_ci_high": nan,
        }

    s_mean = float(np.mean(success_vals))
    f_mean = float(np.mean(failure_vals))
    s_std = float(np.std(success_vals, ddof=1)) if n_s > 1 else 0.0
    f_std = float(np.std(failure_vals, ddof=1)) if n_f > 1 else 0.0

    mw = scipy_stats.mannwhitneyu(success_vals, failure_vals, alternative="two-sided")

    ci_diff_low, ci_diff_high = bootstrap_ci_mean_diff(
        success_vals, failure_vals, n_boot, rng
    )
    s_ci_low, s_ci_high = bootstrap_ci_group_mean(success_vals, n_boot, rng)
    f_ci_low, f_ci_high = bootstrap_ci_group_mean(failure_vals, n_boot, rng)
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
        "success_ci_low": s_ci_low,
        "success_ci_high": s_ci_high,
        "failure_ci_low": f_ci_low,
        "failure_ci_high": f_ci_high,
        "mann_whitney_u": float(mw.statistic),
        "mann_whitney_p": float(mw.pvalue),
        "permutation_p": perm_p,
        "bootstrap_ci_low": ci_diff_low,
        "bootstrap_ci_high": ci_diff_high,
    }


# ---------------------------------------------------------------------------
# BH correction
# ---------------------------------------------------------------------------

def apply_bh_correction(group_summary_rows: list[dict[str, Any]]) -> None:
    """Add mann_whitney_q_bh to each row in-place (400 tests per subset)."""
    for subset_name in ("all", "excl_censored"):
        rows = [r for r in group_summary_rows if r["subset"] == subset_name]
        p_arr = np.array([r["mann_whitney_p"] for r in rows], dtype=np.float64)
        valid = ~np.isnan(p_arr)
        q_arr = np.full(len(p_arr), float("nan"))
        if valid.sum() > 0:
            q_arr[valid] = false_discovery_control(p_arr[valid], method="bh")
        for i, r in enumerate(rows):
            r["mann_whitney_q_bh"] = float(q_arr[i])


# ---------------------------------------------------------------------------
# Earliest stable divergence
# ---------------------------------------------------------------------------

def find_earliest_stable_divergence(
    layer_rows: list[dict[str, Any]],
) -> int | None:
    """
    Find earliest bin where the bootstrap CI on (success − failure) excludes
    zero for that bin AND the immediately following bin, both in the same
    direction. Returns the bin index (0-indexed) or None.
    """
    by_bin = {r["progress_bin"]: r for r in layer_rows}
    for b in range(N_BINS - 1):
        r0 = by_bin.get(b)
        r1 = by_bin.get(b + 1)
        if r0 is None or r1 is None:
            continue
        ci0_low, ci0_high = r0["bootstrap_ci_low"], r0["bootstrap_ci_high"]
        ci1_low, ci1_high = r1["bootstrap_ci_low"], r1["bootstrap_ci_high"]
        if any(math.isnan(v) for v in [ci0_low, ci0_high, ci1_low, ci1_high]):
            continue
        # Positive direction: both CIs strictly above zero
        if ci0_low > 0 and ci1_low > 0:
            return b
        # Negative direction: both CIs strictly below zero
        if ci0_high < 0 and ci1_high < 0:
            return b
    return None


# ---------------------------------------------------------------------------
# Plot 1: Layer-22 trajectory
# ---------------------------------------------------------------------------

def plot_layer22_trajectory(
    group_summary_rows: list[dict[str, Any]],
    output_path: str,
) -> None:
    subset_rows = sorted(
        [r for r in group_summary_rows
         if r["layer"] == PROVISIONAL_LAYER and r["subset"] == "all"],
        key=lambda r: r["progress_bin"],
    )
    x = np.arange(N_BINS)
    s_means = np.array([r["success_mean"] for r in subset_rows])
    f_means = np.array([r["failure_mean"] for r in subset_rows])
    s_ci_lo = np.array([r["success_ci_low"] for r in subset_rows])
    s_ci_hi = np.array([r["success_ci_high"] for r in subset_rows])
    f_ci_lo = np.array([r["failure_ci_low"] for r in subset_rows])
    f_ci_hi = np.array([r["failure_ci_high"] for r in subset_rows])

    n_s = subset_rows[0]["n_success"] if subset_rows else 0
    n_f = subset_rows[0]["n_failure"] if subset_rows else 0

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(x, s_ci_lo, s_ci_hi, alpha=0.25, color=COLOR_SUCCESS_CI)
    ax.fill_between(x, f_ci_lo, f_ci_hi, alpha=0.25, color=COLOR_FAILURE_CI)
    ax.plot(x, s_means, color=COLOR_SUCCESS, linewidth=2,
            marker="o", markersize=5, label=f"Success (n={n_s})")
    ax.plot(x, f_means, color=COLOR_FAILURE, linewidth=2,
            marker="o", markersize=5, label=f"Failure (n={n_f})")
    ax.axhline(0, color="black", linewidth=0.5, alpha=0.4, linestyle="--")
    ax.set_xticks(x)
    ax.set_xticklabels(BIN_LABELS, rotation=35, ha="right", fontsize=9)
    ax.set_xlabel("Normalized thinking progress (10 equal bins)")
    ax.set_ylabel("Mean projection (provisional direction)")
    ax.set_title(
        f"Layer-{PROVISIONAL_LAYER} Projection Trajectory Across Normalized Thinking Progress\n"
        "(subset='all'; shaded = 95% bootstrap CI on group mean; primary outcome: sr_success)"
    )
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


# ---------------------------------------------------------------------------
# Plot 2: Layer-22 success–failure difference
# ---------------------------------------------------------------------------

def plot_layer22_difference(
    group_summary_rows: list[dict[str, Any]],
    output_path: str,
) -> None:
    subset_rows = sorted(
        [r for r in group_summary_rows
         if r["layer"] == PROVISIONAL_LAYER and r["subset"] == "all"],
        key=lambda r: r["progress_bin"],
    )
    x = np.arange(N_BINS)
    diffs = np.array([r["mean_difference"] for r in subset_rows])
    ci_lo = np.array([r["bootstrap_ci_low"] for r in subset_rows])
    ci_hi = np.array([r["bootstrap_ci_high"] for r in subset_rows])
    q_vals = np.array([r.get("mann_whitney_q_bh", float("nan")) for r in subset_rows])

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(x, ci_lo, ci_hi, alpha=0.25, color="#999999")
    ax.plot(x, diffs, color="#333333", linewidth=2, marker="o", markersize=5)
    ax.axhline(0, color="black", linewidth=1.0, alpha=0.6)

    # Mark bins where BH-corrected q < 0.05
    for b, q in enumerate(q_vals):
        if not math.isnan(q) and q < ALPHA:
            ax.axvspan(b - 0.5, b + 0.5, color="#FFEB3B", alpha=0.25, zorder=0)

    ax.set_xticks(x)
    ax.set_xticklabels(BIN_LABELS, rotation=35, ha="right", fontsize=9)
    ax.set_xlabel("Normalized thinking progress (10 equal bins)")
    ax.set_ylabel("Success mean − Failure mean")
    ax.set_title(
        f"Layer-{PROVISIONAL_LAYER} Projection Difference (Success − Failure) "
        f"Across Normalized Progress\n"
        "(subset='all'; shaded = 95% bootstrap CI on difference; "
        "yellow bands = BH q < 0.05)"
    )
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


# ---------------------------------------------------------------------------
# Plot 3 & 4: Heatmaps (Hedges' g and mean difference)
# ---------------------------------------------------------------------------

def _build_heatmap_matrix(
    group_summary_rows: list[dict[str, Any]],
    metric: str,
    subset: str = "all",
) -> np.ndarray:
    mat = np.full((N_LAYERS, N_BINS), float("nan"))
    for r in group_summary_rows:
        if r["subset"] == subset:
            li = int(r["layer"])
            b = int(r["progress_bin"])
            v = r.get(metric, float("nan"))
            if not math.isnan(v):
                mat[li, b] = v
    return mat


def _plot_heatmap(
    matrix: np.ndarray,
    title: str,
    cbar_label: str,
    output_path: str,
    cmap: str = "RdBu_r",
) -> None:
    # Display layer 0 at top, layer 39 at bottom → matches natural top-to-bottom
    # reading but we flip so layer 0 is at bottom (higher = deeper layer)
    mat_display = matrix[::-1, :]   # row 0 of display = layer 39

    finite_vals = matrix[np.isfinite(matrix)]
    if len(finite_vals) == 0:
        print(f"[plot] No finite values for heatmap {output_path}, skipping")
        return
    vmax = float(np.max(np.abs(finite_vals))) * 1.05
    vmin = -vmax

    fig, ax = plt.subplots(figsize=(9, 10))
    im = ax.imshow(mat_display, aspect="auto", cmap=cmap,
                   vmin=vmin, vmax=vmax, origin="upper")

    ax.set_xticks(np.arange(N_BINS))
    ax.set_xticklabels(BIN_LABELS, rotation=40, ha="right", fontsize=8)
    ax.set_xlabel("Normalized thinking progress (10 equal bins)", fontsize=9)

    # Y ticks: show every 5th layer; layer numbers increase downward in display
    ytick_pos = [N_LAYERS - 1 - li for li in range(0, N_LAYERS, 5)]
    ytick_labels = [str(li) for li in range(0, N_LAYERS, 5)]
    ax.set_yticks(ytick_pos)
    ax.set_yticklabels(ytick_labels, fontsize=8)
    ax.set_ylabel("Layer (0 = embedding, 39 = last)", fontsize=9)

    # Highlight provisional layer row
    l22_display_row = N_LAYERS - 1 - PROVISIONAL_LAYER
    rect = mpatches.Rectangle(
        (-0.5, l22_display_row - 0.5), N_BINS, 1,
        linewidth=1.5, edgecolor="gold", facecolor="none", zorder=5,
    )
    ax.add_patch(rect)
    ax.text(
        N_BINS + 0.1, l22_display_row, f"L{PROVISIONAL_LAYER}",
        va="center", ha="left", fontsize=7.5, color="goldenrod",
    )

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.08)
    cbar.set_label(cbar_label, fontsize=9)

    ax.set_title(title, fontsize=10, pad=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


def plot_effect_heatmap(
    group_summary_rows: list[dict[str, Any]],
    output_path: str,
) -> None:
    mat = _build_heatmap_matrix(group_summary_rows, "hedges_g")
    _plot_heatmap(
        mat,
        title=(
            "Hedges' g by Layer and Normalized-Progress Bin\n"
            "(success − failure; subset='all'; gold box = provisional layer 22)"
        ),
        cbar_label="Hedges' g",
        output_path=output_path,
    )


def plot_mean_diff_heatmap(
    group_summary_rows: list[dict[str, Any]],
    output_path: str,
) -> None:
    mat = _build_heatmap_matrix(group_summary_rows, "mean_difference")
    _plot_heatmap(
        mat,
        title=(
            "Mean Projection Difference (Success − Failure) by Layer and Bin\n"
            "(subset='all'; gold box = provisional layer 22)"
        ),
        cbar_label="Mean difference",
        output_path=output_path,
    )


# ---------------------------------------------------------------------------
# Plot 5: Selected layers
# ---------------------------------------------------------------------------

def plot_selected_layers(
    group_summary_rows: list[dict[str, Any]],
    output_path: str,
    selected: list[int] = SELECTED_LAYERS,
) -> None:
    n_sel = len(selected)
    ncols = 3
    nrows = math.ceil(n_sel / ncols)
    fig, axes = plt.subplots(nrows, ncols,
                              figsize=(5.5 * ncols, 4.2 * nrows),
                              sharey=False)
    axes_flat = axes.flatten() if hasattr(axes, "flatten") else [axes]

    x = np.arange(N_BINS)

    for ax_idx, layer in enumerate(selected):
        ax = axes_flat[ax_idx]
        layer_rows = sorted(
            [r for r in group_summary_rows
             if r["layer"] == layer and r["subset"] == "all"],
            key=lambda r: r["progress_bin"],
        )
        if not layer_rows:
            ax.set_visible(False)
            continue

        s_means = np.array([r["success_mean"] for r in layer_rows])
        f_means = np.array([r["failure_mean"] for r in layer_rows])
        s_ci_lo = np.array([r["success_ci_low"] for r in layer_rows])
        s_ci_hi = np.array([r["success_ci_high"] for r in layer_rows])
        f_ci_lo = np.array([r["failure_ci_low"] for r in layer_rows])
        f_ci_hi = np.array([r["failure_ci_high"] for r in layer_rows])
        n_s = layer_rows[0]["n_success"]
        n_f = layer_rows[0]["n_failure"]

        prov_label = " (provisional)" if layer == PROVISIONAL_LAYER else ""
        ax.fill_between(x, s_ci_lo, s_ci_hi, alpha=0.25, color=COLOR_SUCCESS_CI)
        ax.fill_between(x, f_ci_lo, f_ci_hi, alpha=0.25, color=COLOR_FAILURE_CI)
        ax.plot(x, s_means, color=COLOR_SUCCESS, linewidth=1.8,
                marker="o", markersize=4, label=f"Success (n={n_s})")
        ax.plot(x, f_means, color=COLOR_FAILURE, linewidth=1.8,
                marker="o", markersize=4, label=f"Failure (n={n_f})")
        ax.axhline(0, color="black", linewidth=0.4, alpha=0.4, linestyle="--")
        ax.set_xticks(x)
        ax.set_xticklabels(BIN_LABELS, rotation=40, ha="right", fontsize=7)
        ax.set_title(f"Layer {layer}{prov_label}", fontsize=10)
        ax.set_ylabel("Mean projection", fontsize=8)
        ax.legend(fontsize=7.5)
        ax.grid(axis="y", alpha=0.2)

    for ax_idx in range(n_sel, len(axes_flat)):
        axes_flat[ax_idx].set_visible(False)

    fig.suptitle(
        "Normalized-Progress Trajectories — Selected Layers\n"
        "(subset='all'; shaded = 95% bootstrap CI on group mean; primary outcome: sr_success)",
        fontsize=11, y=1.01,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


# ---------------------------------------------------------------------------
# Plot 6: Earliest stable divergence by layer
# ---------------------------------------------------------------------------

def plot_earliest_divergence(
    group_summary_rows: list[dict[str, Any]],
    output_path: str,
) -> None:
    NO_DIV_Y = N_BINS + 0.4   # y-position for "no stable divergence" markers

    earliest: list[float] = []
    for li in range(N_LAYERS):
        layer_rows = [r for r in group_summary_rows
                      if r["layer"] == li and r["subset"] == "all"]
        b = find_earliest_stable_divergence(layer_rows)
        earliest.append(float(b) if b is not None else NO_DIV_Y)

    earliest_arr = np.array(earliest)
    layers = np.arange(N_LAYERS)

    has_div = earliest_arr < N_BINS
    no_div = ~has_div

    fig, ax = plt.subplots(figsize=(13, 5))

    ax.scatter(layers[has_div], earliest_arr[has_div],
               color=COLOR_SUCCESS, s=55, zorder=3,
               label="Stable divergence found")
    ax.scatter(layers[no_div], np.full(no_div.sum(), NO_DIV_Y),
               color=COLOR_FAILURE, marker="x", s=55, linewidths=1.5, zorder=3,
               label=f"No stable divergence (n={int(no_div.sum())})")

    # Mark provisional layer
    ax.axvline(PROVISIONAL_LAYER, color="gray", linestyle="--", linewidth=1,
               alpha=0.7, label=f"Layer {PROVISIONAL_LAYER} (provisional)")

    ax.set_xlabel("Layer (0–39)")
    ax.set_ylabel("Earliest stable-divergence bin")
    ax.set_yticks(list(range(N_BINS)) + [int(NO_DIV_Y)])
    ax.set_yticklabels(BIN_LABELS + ["none"])
    ax.set_xlim(-0.5, N_LAYERS - 0.5)
    ax.grid(axis="y", alpha=0.25)
    ax.axhline(N_BINS, color="black", linewidth=0.5, alpha=0.4, linestyle=":")
    ax.set_title(
        "Earliest Stable Divergence Bin by Layer\n"
        "(earliest bin where 95% bootstrap CI on difference excludes zero "
        "for that bin and the next; subset='all')"
    )
    ax.legend(fontsize=9)
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
    n_bins = args.n_bins
    rng = np.random.default_rng(args.seed)

    # ------------------------------------------------------------------
    # Load analysis dataset
    # ------------------------------------------------------------------
    print(f"[np] Loading analysis dataset: {args.analysis_dataset}")
    dataset = load_analysis_dataset(args.analysis_dataset)
    eligible = [r for r in dataset if r["usable_for_think_analysis"]]
    print(f"[np] Total examples: {len(dataset)}  |  usable_for_think: {len(eligible)}")

    n_expected_primary = len(eligible) * N_LAYERS * n_bins
    print(f"[np] Expected per-example rows: "
          f"{len(eligible)} × {N_LAYERS} × {n_bins} = {n_expected_primary}")

    # ------------------------------------------------------------------
    # Per-example extraction
    # ------------------------------------------------------------------
    per_example_rows: list[dict[str, Any]] = []
    failed_examples: list[str] = []

    print(f"[np] Extracting bins for {len(eligible)} examples ...")
    for idx, meta in enumerate(eligible, 1):
        example_id = meta["example_id"]
        per_ex_path = str(per_example_dir / f"{_id_to_filename(example_id)}.json")
        print(f"[np]   {idx:2d}/{len(eligible)}: {example_id[:65]}", end="\r")

        try:
            result = extract_think_bins_for_example(per_ex_path, n_bins, N_LAYERS)
        except (FileNotFoundError, ValueError) as exc:
            print(f"\n[np] ERROR loading {per_ex_path}: {exc}", file=sys.stderr)
            failed_examples.append(example_id)
            continue

        lbs = result["layer_bin_stats"]
        for layer in range(N_LAYERS):
            if layer not in lbs:
                continue
            for b in range(n_bins):
                if b not in lbs[layer]:
                    continue
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
                    "layer": layer,
                    "progress_bin": b,
                    "bin_start_fraction": BIN_START_FRACTIONS[b],
                    "bin_end_fraction": BIN_END_FRACTIONS[b],
                    **lbs[layer][b],
                })

    print(f"\n[np] Per-example rows: {len(per_example_rows)}")

    # Validate row count
    n_loaded = len(eligible) - len(failed_examples)
    n_expected = n_loaded * N_LAYERS * n_bins
    if len(per_example_rows) != n_expected:
        print(f"[np] WARNING: expected {n_expected} rows, got {len(per_example_rows)}",
              file=sys.stderr)
    else:
        print(f"[np] Row count validated: {len(per_example_rows)} == "
              f"{n_loaded}×{N_LAYERS}×{n_bins}")

    # ------------------------------------------------------------------
    # Build per-cell index for group stats
    # ------------------------------------------------------------------
    # cell_index: (layer, bin) → {example_id → row_fields}
    cell_index: dict[tuple[int, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in per_example_rows:
        key = (r["layer"], r["progress_bin"])
        cell_index[key][r["example_id"]] = {
            "mean_projection": r["mean_projection"],
            "sr_success": r["sr_success"],
            "right_censored": r["right_censored"],
            "judge_success": r["judge_success"],
        }

    # ------------------------------------------------------------------
    # Group summary statistics
    # ------------------------------------------------------------------
    print(f"\n[np] Computing group statistics (40 layers × {n_bins} bins × 2 subsets) ...")
    group_summary_rows: list[dict[str, Any]] = []

    subsets: list[tuple[str, bool]] = [("all", False), ("excl_censored", True)]

    for li in range(N_LAYERS):
        for b in range(n_bins):
            cell = cell_index.get((li, b), {})
            for subset_name, excl_censored in subsets:
                eligible_cell = {
                    eid: v for eid, v in cell.items()
                    if not (excl_censored and v["right_censored"])
                }
                s_vals = np.array([
                    v["mean_projection"] for v in eligible_cell.values()
                    if v["sr_success"]
                ], dtype=np.float64)
                f_vals = np.array([
                    v["mean_projection"] for v in eligible_cell.values()
                    if not v["sr_success"]
                ], dtype=np.float64)

                gs = compute_group_stats(s_vals, f_vals,
                                         args.n_bootstrap, args.n_permutations, rng)

                # Secondary descriptive: judge_success
                j_vals = np.array([
                    v["mean_projection"] for v in eligible_cell.values()
                    if v["judge_success"]
                ], dtype=np.float64)
                nj_vals = np.array([
                    v["mean_projection"] for v in eligible_cell.values()
                    if not v["judge_success"]
                ], dtype=np.float64)

                group_summary_rows.append({
                    "layer": li,
                    "progress_bin": b,
                    "bin_start_fraction": BIN_START_FRACTIONS[b],
                    "bin_end_fraction": BIN_END_FRACTIONS[b],
                    "subset": subset_name,
                    **gs,
                    # Placeholder for BH correction (added below)
                    "mann_whitney_q_bh": float("nan"),
                    # Secondary
                    "n_judge_success": len(j_vals),
                    "n_judge_failure": len(nj_vals),
                    "judge_success_mean": float(np.mean(j_vals)) if len(j_vals) else float("nan"),
                    "judge_failure_mean": float(np.mean(nj_vals)) if len(nj_vals) else float("nan"),
                })

        if li % 10 == 9 or li == N_LAYERS - 1:
            print(f"  layer {li + 1:2d}/{N_LAYERS} done")

    # ------------------------------------------------------------------
    # Benjamini–Hochberg correction
    # ------------------------------------------------------------------
    print(f"[np] Applying Benjamini–Hochberg correction ...")
    apply_bh_correction(group_summary_rows)

    # ------------------------------------------------------------------
    # Write CSV outputs
    # ------------------------------------------------------------------
    # Per-example CSV
    pe_path = out_dir / "normalized_progress_per_example.csv"
    if per_example_rows:
        fieldnames = list(per_example_rows[0].keys())
        with open(pe_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(per_example_rows)
        print(f"\n[np] Wrote {pe_path}  ({len(per_example_rows)} rows)")

    # Group summary CSV
    gs_path = out_dir / "normalized_progress_group_summary.csv"
    if group_summary_rows:
        fieldnames_gs = list(group_summary_rows[0].keys())
        with open(gs_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames_gs)
            w.writeheader()
            w.writerows(group_summary_rows)
        print(f"[np] Wrote {gs_path}  ({len(group_summary_rows)} rows)")

    # ------------------------------------------------------------------
    # Manifest (including package versions)
    # ------------------------------------------------------------------
    import matplotlib as _mpl
    import scipy as _scipy
    import numpy as _np

    manifest = {
        "artifact_version": "normalized_progress_analysis_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "stage4_run_directory": str(s4_run),
        "analysis_dataset": str(args.analysis_dataset),
        "per_example_directory": str(per_example_dir),
        "n_bins": n_bins,
        "bin_labels": BIN_LABELS,
        "binning_rule": (
            "boundaries[b] = round(b * N / n_bins); "
            "bin b contains tokens at positions [boundaries[b], boundaries[b+1]). "
            "Sum of bin sizes equals N exactly; sizes differ by at most 1."
        ),
        "layers_analyzed": list(range(N_LAYERS)),
        "provisional_layer": PROVISIONAL_LAYER,
        "selected_layers_for_plot5": SELECTED_LAYERS,
        "primary_binary_outcome": "sr_success = strongreject_score >= 0.5",
        "secondary_binary_outcome": "judge_success = judge_score == 10",
        "statistical_unit": "per-example mean projection within each bin (not individual tokens)",
        "random_seed": args.seed,
        "n_bootstrap": args.n_bootstrap,
        "n_permutations": args.n_permutations,
        "bootstrap_ci_level": f"{int(100 * (1 - ALPHA))}%",
        "multiple_comparison_correction": (
            "Benjamini–Hochberg FDR correction over all "
            f"{N_LAYERS} × {n_bins} = {N_LAYERS * n_bins} tests per subset; "
            "scipy.stats.false_discovery_control(method='bh')"
        ),
        "permutation_test": "two-sided, absolute difference in means",
        "think_role_only": True,
        "assistant_or_special_tokens_excluded": True,
        "subsets": {
            "all": "all eligible examples with usable_for_think_analysis=True",
            "excl_censored": "same but excluding right_censored=True examples",
        },
        "n_eligible": len(eligible),
        "n_failed": len(failed_examples),
        "failed_examples": failed_examples,
        "total_per_example_rows": len(per_example_rows),
        "total_group_summary_rows": len(group_summary_rows),
        "package_versions": {
            "python": sys.version.split()[0],
            "numpy": _np.__version__,
            "scipy": _scipy.__version__,
            "matplotlib": _mpl.__version__,
        },
        "output_files": {
            "per_example_csv": str(pe_path),
            "group_summary_csv": str(gs_path),
        },
    }
    manifest_path = out_dir / "normalized_progress_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[np] Wrote {manifest_path}")

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    print(f"\n[np] Generating 6 plots ...")
    plot_layer22_trajectory(
        group_summary_rows,
        str(plots_dir / "normalized_progress_layer22.png"),
    )
    plot_layer22_difference(
        group_summary_rows,
        str(plots_dir / "normalized_progress_layer22_difference.png"),
    )
    plot_effect_heatmap(
        group_summary_rows,
        str(plots_dir / "normalized_progress_effect_heatmap.png"),
    )
    plot_mean_diff_heatmap(
        group_summary_rows,
        str(plots_dir / "normalized_progress_mean_difference_heatmap.png"),
    )
    plot_selected_layers(
        group_summary_rows,
        str(plots_dir / "normalized_progress_selected_layers.png"),
    )
    plot_earliest_divergence(
        group_summary_rows,
        str(plots_dir / "earliest_divergence_by_layer.png"),
    )

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------
    print()
    print("=" * 72)
    print("  NORMALIZED-PROGRESS ANALYSIS SUMMARY")
    print("=" * 72)
    print(f"  n_bins={n_bins}  |  primary outcome: sr_success  "
          f"|  Layer {PROVISIONAL_LAYER} = provisional only")
    print()

    for subset_name in ("all", "excl_censored"):
        l22_rows = sorted(
            [r for r in group_summary_rows
             if r["layer"] == PROVISIONAL_LAYER and r["subset"] == subset_name],
            key=lambda r: r["progress_bin"],
        )
        print(f"  Layer {PROVISIONAL_LAYER} — subset='{subset_name}':")
        if l22_rows:
            r0 = l22_rows[0]
            print(f"    n_success={r0['n_success']}  n_failure={r0['n_failure']}")
            for r in l22_rows:
                ci_str = (f"[{r['bootstrap_ci_low']:.3f}, {r['bootstrap_ci_high']:.3f}]"
                          if not math.isnan(r.get("bootstrap_ci_low", float("nan")))
                          else "n/a")
                sig = "*" if (not math.isnan(r.get("mann_whitney_q_bh", float("nan")))
                              and r["mann_whitney_q_bh"] < ALPHA) else " "
                print(f"    bin {r['progress_bin']} ({BIN_LABELS[r['progress_bin']]:8s}): "
                      f"diff={r['mean_difference']:+.4f}  g={r['hedges_g']:+.3f}  "
                      f"mwu_p={r['mann_whitney_p']:.4f}  q_bh={r['mann_whitney_q_bh']:.4f}{sig}  "
                      f"CI={ci_str}")
        print()

    # Best layer by max abs Hedges' g across all bins (subset=all)
    all_rows = [r for r in group_summary_rows if r["subset"] == "all"]
    by_layer_maxg: dict[int, float] = {}
    for r in all_rows:
        g = r["hedges_g"]
        if not math.isnan(g):
            li = r["layer"]
            by_layer_maxg[li] = max(by_layer_maxg.get(li, 0.0), abs(g))
    if by_layer_maxg:
        best_layer = max(by_layer_maxg, key=by_layer_maxg.__getitem__)
        best_g_for_layer = [r for r in all_rows
                            if r["layer"] == best_layer
                            and not math.isnan(r["hedges_g"])]
        best_bin_row = max(best_g_for_layer, key=lambda r: abs(r["hedges_g"]))
        print(f"  Best (layer, bin) by |Hedges' g| (all): "
              f"layer={best_bin_row['layer']}  "
              f"bin={best_bin_row['progress_bin']} ({BIN_LABELS[best_bin_row['progress_bin']]})  "
              f"g={best_bin_row['hedges_g']:+.3f}")

    # BH-significant cells
    sig_all = [r for r in group_summary_rows
               if r["subset"] == "all"
               and not math.isnan(r.get("mann_whitney_q_bh", float("nan")))
               and r["mann_whitney_q_bh"] < ALPHA]
    sig_excl = [r for r in group_summary_rows
                if r["subset"] == "excl_censored"
                and not math.isnan(r.get("mann_whitney_q_bh", float("nan")))
                and r["mann_whitney_q_bh"] < ALPHA]
    print(f"\n  BH-significant (q < {ALPHA}) cells: "
          f"all={len(sig_all)}/{N_LAYERS * n_bins}  "
          f"excl_censored={len(sig_excl)}/{N_LAYERS * n_bins}")

    # Earliest stable divergence at provisional layer
    l22_all_rows = [r for r in group_summary_rows
                    if r["layer"] == PROVISIONAL_LAYER and r["subset"] == "all"]
    l22_div = find_earliest_stable_divergence(l22_all_rows)
    if l22_div is not None:
        print(f"\n  Layer {PROVISIONAL_LAYER} earliest stable divergence: "
              f"bin {l22_div} ({BIN_LABELS[l22_div]})")
    else:
        print(f"\n  Layer {PROVISIONAL_LAYER}: no stable divergence found")

    # Layers with stable divergence in first bin (bin 0)
    early_layers = []
    for li in range(N_LAYERS):
        lrows = [r for r in group_summary_rows
                 if r["layer"] == li and r["subset"] == "all"]
        d = find_earliest_stable_divergence(lrows)
        if d is not None and d == 0:
            early_layers.append(li)
    if early_layers:
        print(f"  Layers with stable divergence from bin 0: {early_layers}")

    print("=" * 72)
    print(f"\n[np] Done. Outputs in {out_dir}")


if __name__ == "__main__":
    main()
