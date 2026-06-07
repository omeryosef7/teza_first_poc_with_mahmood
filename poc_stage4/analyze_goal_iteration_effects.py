#!/usr/bin/env python3
"""
Phase 7 — Exploratory goal-level and attack-iteration analysis.

All results are EXPLORATORY. Group sizes are small (goals 0–2: ~11–12 examples;
goal 3: 6 examples). Subgroup p-values should not be treated as confirmatory.
No adjusted models are fit within individual goals.

Projection values are onto the *provisional harmful-versus-harmless contrast
direction* (diagnostic only; not causally validated).

Offline, CPU-only. Does not load model weights. Does not modify any prior
Stage 4 or Stage 6 artifacts.
"""

import argparse
import csv
import json
import math
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE = Path("outputs/stage4/token_dynamics/full_20260604_101929")
ANA  = BASE / "analysis"
PLOT = BASE / "plots_analysis_v2"

IN_AUDIT    = ANA / "analysis_dataset.csv"
IN_FIXED    = ANA / "fixed_window_per_example.csv"
IN_NORM     = ANA / "normalized_progress_per_example.csv"
IN_TRAJ_SUM = ANA / "per_prompt_trajectory_summary.csv"
IN_LAYER    = ANA / "per_prompt_layer_summary.csv"

OUT_GOAL_BEH   = ANA / "goal_behavior_summary.csv"
OUT_GOAL_PROJ  = ANA / "goal_projection_summary.csv"
OUT_GOAL_NORM  = ANA / "goal_normalized_trajectories.csv"
OUT_ITER       = ANA / "iteration_summary.csv"
OUT_CONV       = ANA / "conversation_stream_summary.csv"
OUT_TRAJ_TYPE  = ANA / "trajectory_type_summary.csv"
OUT_MANIFEST   = ANA / "goal_iteration_manifest.json"

# ─── Constants ────────────────────────────────────────────────────────────────

SCRIPT_VERSION  = "analyze_goal_iteration_effects_v1"
RANDOM_SEED     = 42
N_BOOTSTRAP     = 2000
ALPHA           = 0.05
Z95             = 1.959964  # scipy.stats.norm.ppf(0.975)
PRIMARY_LAYER   = 22
REPORT_LAYERS   = [13, 16, 22]   # for goal-normalized trajectories
GOAL_NORM_LAYERS = [13, 16, 22]  # Part C

EXPLORATORY_WARNING = (
    "All results in this file are EXPLORATORY. Group sizes are small "
    "(goals 0-2: ~11-12 examples each; goal 3: 6 examples). "
    "Subgroup confidence intervals are descriptive, not confirmatory. "
    "Do not interpret isolated subgroup intervals excluding zero as "
    "statistically significant. These results are hypothesis-generating."
)

# Wong (2011) colorblind-safe palette
COL_SUCCESS = "#0072B2"
COL_FAILURE = "#D55E00"
GOAL_COLORS = {0: "#0072B2", 1: "#009E73", 2: "#E69F00", 3: "#CC79A7"}
LAYER_COLORS = {13: "#0072B2", 16: "#56B4E9", 22: "#009E73"}

# ─── Utilities ────────────────────────────────────────────────────────────────

def cb(v):
    return str(v).strip().lower() in ("true", "1", "yes")

def cf(v, default=np.nan):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def ci_int(v, default=None):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def wilson_ci(k: int, n: int) -> tuple[float, float]:
    """Wilson score 95% CI for proportion k/n. Returns (lo, hi)."""
    if n == 0:
        return (np.nan, np.nan)
    p_hat = k / n
    z2    = Z95 ** 2
    denom = n + z2
    center = (k + z2 / 2) / denom
    half   = Z95 * math.sqrt(max(0.0, n * p_hat * (1 - p_hat) + z2 / 4)) / denom
    return (max(0.0, center - half), min(1.0, center + half))

def hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    """Hedges' g (small-sample corrected Cohen's d), a=group1, b=group2."""
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return np.nan
    s1 = np.var(a, ddof=1)
    s2 = np.var(b, ddof=1)
    sp = math.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    if sp == 0:
        return np.nan
    d  = (np.mean(a) - np.mean(b)) / sp
    correction = 1 - 3 / (4 * (n1 + n2) - 9)
    return d * correction

def bootstrap_ci(a: np.ndarray, b: np.ndarray, rng: np.random.Generator,
                 stat_fn=None, n_boot: int = N_BOOTSTRAP
                 ) -> tuple[float, float]:
    """Bootstrap 95% CI for difference of means (a_mean - b_mean)."""
    if stat_fn is None:
        stat_fn = lambda x, y: np.mean(x) - np.mean(y)
    if len(a) == 0 or len(b) == 0:
        return (np.nan, np.nan)
    boot = np.array([
        stat_fn(
            rng.choice(a, size=len(a), replace=True),
            rng.choice(b, size=len(b), replace=True),
        )
        for _ in range(n_boot)
    ])
    return (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

def bootstrap_mean_ci(arr: np.ndarray, rng: np.random.Generator,
                      n_boot: int = N_BOOTSTRAP) -> tuple[float, float]:
    """Bootstrap 95% CI for the mean of arr."""
    if len(arr) == 0:
        return (np.nan, np.nan)
    boot = np.array([np.mean(rng.choice(arr, size=len(arr), replace=True))
                     for _ in range(n_boot)])
    return (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

def fmt(v, decimals=3):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return f"{v:.{decimals}f}"

# ─── Data Loading ─────────────────────────────────────────────────────────────

def load_audit() -> list[dict]:
    with open(IN_AUDIT, newline="") as f:
        return list(csv.DictReader(f))

def load_fixed() -> list[dict]:
    with open(IN_FIXED, newline="") as f:
        return list(csv.DictReader(f))

def load_norm() -> list[dict]:
    with open(IN_NORM, newline="") as f:
        return list(csv.DictReader(f))

def load_traj_sum() -> list[dict]:
    with open(IN_TRAJ_SUM, newline="") as f:
        return list(csv.DictReader(f))

def load_layer_sum() -> list[dict]:
    with open(IN_LAYER, newline="") as f:
        return list(csv.DictReader(f))

# ─── Feature extraction helpers ───────────────────────────────────────────────

def fixed_vals(fixed_rows: list[dict], layer: int, window: int) -> dict[str, float]:
    """Return {example_id: mean_projection} for given layer + window."""
    return {
        r["example_id"]: cf(r["mean_projection"])
        for r in fixed_rows
        if int(r["layer"]) == layer and int(r["window_size"]) == window
    }

def norm_vals(norm_rows: list[dict], layer: int, bin_idx: int) -> dict[str, float]:
    """Return {example_id: mean_projection} for given layer + bin."""
    return {
        r["example_id"]: cf(r["mean_projection"])
        for r in norm_rows
        if int(r["layer"]) == layer and int(r["progress_bin"]) == bin_idx
    }

def layer_field(layer_rows: list[dict], layer: int, field: str) -> dict[str, float]:
    """Return {example_id: field_value} from per_prompt_layer_summary for given layer."""
    return {
        r["example_id"]: cf(r[field])
        for r in layer_rows
        if int(r["layer"]) == layer
    }

def group_stats(vals: np.ndarray, label: str, rng: np.random.Generator) -> dict:
    """Descriptive statistics for a group of values."""
    n = len(vals)
    if n == 0:
        return dict(label=label, n=0, mean=np.nan, median=np.nan, std=np.nan,
                    boot_ci_low=np.nan, boot_ci_high=np.nan)
    m   = float(np.mean(vals))
    med = float(np.median(vals))
    s   = float(np.std(vals, ddof=1)) if n > 1 else np.nan
    lo, hi = bootstrap_mean_ci(vals, rng)
    return dict(label=label, n=n, mean=m, median=med, std=s,
                boot_ci_low=lo, boot_ci_high=hi)

# ─── Part A: Goal behavioral summaries ───────────────────────────────────────

def part_a(audit: list[dict], rng: np.random.Generator) -> list[dict]:
    goals = sorted(set(r["goal_index"] for r in audit), key=int)
    rows_out = []
    for g in goals:
        grp = [r for r in audit if r["goal_index"] == g]
        think_elig = [r for r in grp if cb(r["usable_for_think_analysis"])]
        sr_suc  = [r for r in grp if cb(r["sr_success"])]
        sr_fail = [r for r in grp if not cb(r["sr_success"])]
        j_suc   = [r for r in grp if cb(r["judge_success"])]
        comb    = [r for r in grp if cb(r.get("combined_success", "False"))]
        rc      = [r for r in grp if cb(r["right_censored"])]
        ns      = [r for r in grp if r["thinking_segmentation_status"] == "not_separable"]

        n       = len(grp)
        n_sr    = len(sr_suc)
        rate    = n_sr / n if n > 0 else np.nan
        wi_lo, wi_hi = wilson_ci(n_sr, n)

        ptc  = np.array([cf(r["prompt_token_count"]) for r in grp])
        tkc  = np.array([cf(r["think_token_count"])  for r in think_elig])
        fnc  = np.array([cf(r["final_token_count"])  for r in grp])

        rows_out.append({
            "goal_index":                      int(g),
            "total_examples":                  n,
            "think_eligible_examples":         len(think_elig),
            "sr_success_count":                n_sr,
            "sr_failure_count":                len(sr_fail),
            "sr_success_rate":                 fmt(rate, 4),
            "sr_success_rate_wilson_ci_low":   fmt(wi_lo, 4),
            "sr_success_rate_wilson_ci_high":  fmt(wi_hi, 4),
            "judge_success_count":             len(j_suc),
            "combined_success_count":          len(comb),
            "prompt_token_count_mean":         fmt(np.mean(ptc)    if len(ptc) > 0 else np.nan),
            "prompt_token_count_median":       fmt(np.median(ptc)  if len(ptc) > 0 else np.nan),
            "think_token_count_mean":          fmt(np.mean(tkc)    if len(tkc) > 0 else np.nan),
            "think_token_count_median":        fmt(np.median(tkc)  if len(tkc) > 0 else np.nan),
            "think_token_count_std":           fmt(np.std(tkc, ddof=1) if len(tkc) > 1 else np.nan),
            "final_token_count_mean":          fmt(np.mean(fnc)    if len(fnc) > 0 else np.nan),
            "final_token_count_median":        fmt(np.median(fnc)  if len(fnc) > 0 else np.nan),
            "right_censored_count":            len(rc),
            "not_separable_count":             len(ns),
            "warning":                         EXPLORATORY_WARNING,
        })
    return rows_out

# ─── Part B: Goal projection summaries ───────────────────────────────────────

PROJ_FEATURES = [
    ("layer22_first500",      "L22 first 500 thinking tokens"),
    ("layer13_first500",      "L13 first 500 thinking tokens"),
    ("layer16_first500",      "L16 first 500 thinking tokens"),
    ("layer22_bin0",          "L22 normalized bin 0 (first 10%)"),
    ("layer22_bin9",          "L22 normalized bin 9 (last 10%)"),
    ("layer22_think_mean",    "L22 full think-phase mean"),
    ("layer22_final_mean",    "L22 final-phase mean"),
    ("layer22_trans_change",  "L22 think-to-final transition change"),
]

def part_b(audit: list[dict], fixed: list[dict], norm: list[dict],
           layer_sum: list[dict], rng: np.random.Generator) -> list[dict]:
    # Build lookup maps keyed by example_id → value
    feat_maps = {
        "layer22_first500":     fixed_vals(fixed, 22, 500),
        "layer13_first500":     fixed_vals(fixed, 13, 500),
        "layer16_first500":     fixed_vals(fixed, 16, 500),
        "layer22_bin0":         norm_vals(norm, 22, 0),
        "layer22_bin9":         norm_vals(norm, 22, 9),
        "layer22_think_mean":   layer_field(layer_sum, 22, "think_mean"),
        "layer22_final_mean":   layer_field(layer_sum, 22, "final_mean"),
        "layer22_trans_change": layer_field(layer_sum, 22, "transition_change"),
    }

    goals = sorted(set(r["goal_index"] for r in audit), key=int)
    rows_out = []

    for g in goals:
        grp     = [r for r in audit if r["goal_index"] == g]
        suc_ids = {r["example_id"] for r in grp if cb(r["sr_success"])}
        fai_ids = {r["example_id"] for r in grp if not cb(r["sr_success"])}

        for feat_key, feat_label in PROJ_FEATURES:
            fmap = feat_maps[feat_key]
            suc_vals = np.array([v for eid, v in fmap.items()
                                 if eid in suc_ids and not np.isnan(v)])
            fai_vals = np.array([v for eid, v in fmap.items()
                                 if eid in fai_ids and not np.isnan(v)])
            all_vals = np.concatenate([suc_vals, fai_vals])

            def row_stats(vals, outcome_label):
                gs = group_stats(vals, outcome_label, rng)
                return {
                    "goal_index":     int(g),
                    "feature":        feat_key,
                    "feature_label":  feat_label,
                    "outcome":        outcome_label,
                    "n":              gs["n"],
                    "mean":           fmt(gs["mean"]),
                    "median":         fmt(gs["median"]),
                    "std":            fmt(gs["std"]),
                    "boot_ci_low":    fmt(gs["boot_ci_low"]),
                    "boot_ci_high":   fmt(gs["boot_ci_high"]),
                    "diff_suc_minus_fai":  "",
                    "hedges_g":            "",
                    "diff_boot_ci_low":    "",
                    "diff_boot_ci_high":   "",
                    "warning": EXPLORATORY_WARNING,
                }

            r_suc = row_stats(suc_vals, "success")
            r_fai = row_stats(fai_vals, "failure")

            # Add difference stats to success row
            if len(suc_vals) >= 1 and len(fai_vals) >= 1:
                diff = np.mean(suc_vals) - np.mean(fai_vals)
                g_h  = hedges_g(suc_vals, fai_vals)
                lo, hi = bootstrap_ci(suc_vals, fai_vals, rng)
                r_suc["diff_suc_minus_fai"] = fmt(diff)
                r_suc["hedges_g"]           = fmt(g_h)
                r_suc["diff_boot_ci_low"]   = fmt(lo)
                r_suc["diff_boot_ci_high"]  = fmt(hi)

            rows_out.extend([r_suc, r_fai])

    return rows_out

# ─── Part C: Goal-specific normalized trajectories ────────────────────────────

def part_c(audit: list[dict], norm: list[dict],
           rng: np.random.Generator) -> list[dict]:
    goals = sorted(set(r["goal_index"] for r in audit), key=int)
    rows_out = []

    for layer in GOAL_NORM_LAYERS:
        for g in goals:
            grp     = [r for r in audit if r["goal_index"] == g]
            suc_ids = {r["example_id"] for r in grp if cb(r["sr_success"])}
            fai_ids = {r["example_id"] for r in grp if not cb(r["sr_success"])}

            for b in range(10):
                bin_rows = [r for r in norm
                            if int(r["layer"]) == layer
                            and int(r["progress_bin"]) == b]
                sv = np.array([cf(r["mean_projection"]) for r in bin_rows
                               if r["example_id"] in suc_ids and not np.isnan(cf(r["mean_projection"]))])
                fv = np.array([cf(r["mean_projection"]) for r in bin_rows
                               if r["example_id"] in fai_ids and not np.isnan(cf(r["mean_projection"]))])

                diff = float(np.mean(sv) - np.mean(fv)) if (len(sv) > 0 and len(fv) > 0) else np.nan
                g_h  = hedges_g(sv, fv)
                lo, hi = bootstrap_ci(sv, fv, rng) if (len(sv) > 0 and len(fv) > 0) else (np.nan, np.nan)

                rows_out.append({
                    "goal_index":      int(g),
                    "layer":           layer,
                    "normalized_bin":  b,
                    "n_success":       len(sv),
                    "n_failure":       len(fv),
                    "success_mean":    fmt(np.mean(sv) if len(sv) > 0 else np.nan),
                    "failure_mean":    fmt(np.mean(fv) if len(fv) > 0 else np.nan),
                    "mean_difference": fmt(diff),
                    "hedges_g":        fmt(g_h),
                    "bootstrap_ci_low":  fmt(lo),
                    "bootstrap_ci_high": fmt(hi),
                    "warning": EXPLORATORY_WARNING,
                })
    return rows_out

# ─── Part D: Attack-iteration analysis ───────────────────────────────────────

def iter_stats(rows: list[dict], fixed: list[dict], norm: list[dict],
               layer_sum: list[dict]) -> dict:
    """Compute projection/length stats for a list of audit rows."""
    n    = len(rows)
    eids = {r["example_id"] for r in rows}
    # sr_success
    n_sr = sum(1 for r in rows if cb(r["sr_success"]))
    # think length (think-eligible only)
    tkc  = np.array([cf(r["think_token_count"]) for r in rows
                     if cb(r["usable_for_think_analysis"])])
    ptc  = np.array([cf(r["prompt_token_count"]) for r in rows])
    # projections
    fw22 = np.array([cf(r["mean_projection"]) for r in fixed
                     if r["example_id"] in eids
                     and int(r["layer"]) == 22 and int(r["window_size"]) == 500])
    nb0  = np.array([cf(r["mean_projection"]) for r in norm
                     if r["example_id"] in eids
                     and int(r["layer"]) == 22 and int(r["progress_bin"]) == 0])
    # think_mean from layer_sum
    lf   = {r["example_id"]: cf(r["think_mean"]) for r in layer_sum
            if int(r["layer"]) == 22}
    tm   = np.array([v for eid, v in lf.items() if eid in eids and not np.isnan(v)])

    def mn(arr): return float(np.mean(arr)) if len(arr) > 0 else np.nan
    return {
        "example_count":           n,
        "sr_success_count":        n_sr,
        "sr_success_rate":         fmt(n_sr / n, 4) if n > 0 else "",
        "think_length_mean":       fmt(mn(tkc)),
        "prompt_length_mean":      fmt(mn(ptc)),
        "layer22_first500_mean":   fmt(mn(fw22)),
        "layer22_bin0_mean":       fmt(mn(nb0)),
        "layer22_full_think_mean": fmt(mn(tm)),
    }

def part_d(audit: list[dict], fixed: list[dict], norm: list[dict],
           layer_sum: list[dict]) -> list[dict]:
    rows_out = []
    iters = sorted(set(r["attack_iteration"] for r in audit), key=int)
    goals = sorted(set(r["goal_index"] for r in audit), key=int)

    # Overall by iteration
    for it in iters:
        grp = [r for r in audit if r["attack_iteration"] == it]
        stats = iter_stats(grp, fixed, norm, layer_sum)
        row = {"iteration": int(it), "goal_subset": "all", **stats}
        rows_out.append(row)

        # Stratified by outcome
        for outcome_label, outcome_fn in [("success", cb), ("failure", lambda v: not cb(v))]:
            sub = [r for r in grp if outcome_fn(r["sr_success"])]
            s = iter_stats(sub, fixed, norm, layer_sum)
            rows_out.append({"iteration": int(it), "goal_subset": f"all_{outcome_label}", **s})

    # Within goals that have both iterations
    both_iters_goals = [g for g in goals
                        if len(set(r["attack_iteration"]
                                   for r in audit if r["goal_index"] == g)) >= 2]
    for g in both_iters_goals:
        for it in iters:
            sub = [r for r in audit if r["goal_index"] == g and r["attack_iteration"] == it]
            if not sub:
                continue
            s = iter_stats(sub, fixed, norm, layer_sum)
            rows_out.append({"iteration": int(it), "goal_subset": f"goal_{g}", **s})

    return rows_out

# ─── Part E: Conversation-stream descriptives ─────────────────────────────────

def part_e(audit: list[dict], fixed: list[dict]) -> list[dict]:
    convs = sorted(set(r["conversation_id"] for r in audit), key=int)
    fw22  = {r["example_id"]: cf(r["mean_projection"]) for r in fixed
             if int(r["layer"]) == 22 and int(r["window_size"]) == 500}
    rows_out = []
    for c in convs:
        grp  = [r for r in audit if r["conversation_id"] == c]
        n    = len(grp)
        n_sr = sum(1 for r in grp if cb(r["sr_success"]))
        tkc  = np.array([cf(r["think_token_count"]) for r in grp
                         if cb(r["usable_for_think_analysis"])])
        pv   = np.array([fw22.get(r["example_id"], np.nan) for r in grp
                         if not np.isnan(fw22.get(r["example_id"], np.nan))])
        rows_out.append({
            "conversation_id":                  int(c),
            "example_count":                    n,
            "sr_success_count":                 n_sr,
            "sr_success_rate":                  fmt(n_sr / n, 4) if n > 0 else "",
            "mean_think_length":                fmt(np.mean(tkc) if len(tkc) > 0 else np.nan),
            "mean_layer22_first500_projection": fmt(np.mean(pv)  if len(pv)  > 0 else np.nan),
            "warning": "Conversation IDs represent attack streams; do not perform confirmatory inference.",
        })
    return rows_out

# ─── Part F: Trajectory-type heterogeneity ────────────────────────────────────

def part_f(audit: list[dict], fixed: list[dict], layer_sum: list[dict]) -> list[dict]:
    # Build per-example features from think-eligible examples only
    fw22   = {r["example_id"]: cf(r["mean_projection"]) for r in fixed
              if int(r["layer"]) == 22 and int(r["window_size"]) == 500}
    slope_ = {r["example_id"]: cf(r["full_generation_slope"]) for r in layer_sum
              if int(r["layer"]) == 22}
    trans_ = {r["example_id"]: cf(r["transition_change"])     for r in layer_sum
              if int(r["layer"]) == 22}
    think_ = {r["example_id"]: cf(r["think_token_count"])     for r in audit}

    # Compute medians on think-eligible rows only
    think_elig = [r for r in audit if cb(r["usable_for_think_analysis"])]
    eids_elig  = {r["example_id"] for r in think_elig}

    fw22_vals = np.array([v for eid, v in fw22.items() if eid in eids_elig and not np.isnan(v)])
    tk_vals   = np.array([v for eid, v in think_.items() if eid in eids_elig and not np.isnan(v)])
    med_fw22  = float(np.median(fw22_vals)) if len(fw22_vals) > 0 else np.nan
    med_tk    = float(np.median(tk_vals))   if len(tk_vals)  > 0 else np.nan

    def cat_early(eid):
        v = fw22.get(eid, np.nan)
        if np.isnan(v) or np.isnan(med_fw22): return "unavailable"
        return "early_high" if v >= med_fw22 else "early_low"

    def cat_slope(eid):
        v = slope_.get(eid, np.nan)
        if np.isnan(v): return "unavailable"
        return "increasing" if v > 0 else "decreasing"

    def cat_trans(eid):
        v = trans_.get(eid, np.nan)
        if np.isnan(v): return "unavailable"
        return "pos_transition" if v > 0 else "neg_transition"

    def cat_length(eid):
        v = think_.get(eid, np.nan)
        if np.isnan(v) or np.isnan(med_tk): return "unavailable"
        return "long_think" if v >= med_tk else "short_think"

    CATEGORIES = [
        ("early_projection",  cat_early,  ["early_high", "early_low"]),
        ("think_slope",       cat_slope,  ["increasing", "decreasing"]),
        ("transition_change", cat_trans,  ["pos_transition", "neg_transition"]),
        ("think_length",      cat_length, ["long_think", "short_think"]),
    ]

    rows_out = []
    for cat_name, cat_fn, cat_vals in CATEGORIES:
        for cv in cat_vals + ["unavailable"]:
            members = [r for r in think_elig if cat_fn(r["example_id"]) == cv]
            n       = len(members)
            n_sr    = sum(1 for r in members if cb(r["sr_success"]))
            rows_out.append({
                "category":        cat_name,
                "value":           cv,
                "n":               n,
                "sr_success_count":n_sr,
                "sr_success_rate": fmt(n_sr / n, 4) if n > 0 else "",
                "warning": "Predefined descriptive categories; not natural mechanistic clusters.",
            })
        # Also combinations: early × slope
    # Two-way cross: early_projection × think_slope
    for ev in ["early_high", "early_low"]:
        for sv in ["increasing", "decreasing"]:
            members = [r for r in think_elig
                       if cat_early(r["example_id"]) == ev
                       and cat_slope(r["example_id"]) == sv]
            n    = len(members)
            n_sr = sum(1 for r in members if cb(r["sr_success"]))
            rows_out.append({
                "category":         f"early_projection × think_slope",
                "value":            f"{ev} × {sv}",
                "n":                n,
                "sr_success_count": n_sr,
                "sr_success_rate":  fmt(n_sr / n, 4) if n > 0 else "",
                "warning": "Predefined descriptive categories; not natural mechanistic clusters.",
            })

    return rows_out, med_fw22, med_tk

# ─── Plotting helpers ─────────────────────────────────────────────────────────

def jitter(n, w=0.08, seed=42):
    rng = np.random.default_rng(seed)
    return rng.uniform(-w, w, size=n)

# ─── Plot 1: goal success rates ───────────────────────────────────────────────

def plot_goal_success_rates(goal_rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    goals = [r["goal_index"] for r in goal_rows]
    rates = [float(r["sr_success_rate"] or 0) for r in goal_rows]
    ci_lo = [float(r["sr_success_rate_wilson_ci_low"]  or 0) for r in goal_rows]
    ci_hi = [float(r["sr_success_rate_wilson_ci_high"] or 0) for r in goal_rows]
    ns    = [r["total_examples"] for r in goal_rows]
    x     = np.arange(len(goals))

    bars = ax.bar(x, rates, color=[GOAL_COLORS[g] for g in goals],
                  width=0.5, alpha=0.8, label="SR success rate")
    for xi, (lo, hi, n) in enumerate(zip(ci_lo, ci_hi, ns)):
        ax.errorbar(xi, (lo + hi) / 2,
                    yerr=[[(lo + hi) / 2 - lo], [hi - (lo + hi) / 2]],
                    fmt="none", color="black", lw=1.5, capsize=5)
        ax.text(xi, hi + 0.03, f"n={n}", ha="center", va="bottom", fontsize=9)

    ax.axhline(y=sum(r["sr_success_count"] for r in goal_rows) /
               sum(r["total_examples"] for r in goal_rows),
               color="grey", ls="--", lw=1, alpha=0.7, label="Overall rate")

    ax.set_xticks(x)
    ax.set_xticklabels([f"Goal {g}" for g in goals])
    ax.set_ylabel("SR success rate")
    ax.set_ylim(0, 1.1)
    ax.set_title(
        "SR success rate by goal — Wilson 95% CI (descriptive, small n)\n"
        "Projection onto provisional harmful-versus-harmless contrast direction",
        fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOT / "goal_success_rates.png", dpi=120)
    plt.close(fig)

# ─── Plot 2: think length by goal × outcome ───────────────────────────────────

def plot_think_length(audit: list[dict]) -> None:
    think_elig = [r for r in audit if cb(r["usable_for_think_analysis"])]
    goals = sorted(set(r["goal_index"] for r in audit), key=int)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    xpos = 0
    xticks, xlabels = [], []
    rng_j = np.random.default_rng(42)

    for gi, g in enumerate(goals):
        for outcome, col, lbl in [("True", COL_SUCCESS, "Success"),
                                   ("False", COL_FAILURE, "Failure")]:
            sub = [cf(r["think_token_count"])
                   for r in think_elig
                   if r["goal_index"] == g
                   and str(cb(r["sr_success"])).lower() == outcome.lower()]
            n   = len(sub)
            if n == 0:
                xpos += 1
                continue
            jit = rng_j.uniform(-0.15, 0.15, size=n)
            ax.scatter(np.full(n, xpos) + jit, sub, color=col, alpha=0.7, s=28, zorder=3)
            ax.plot([xpos - 0.3, xpos + 0.3], [np.mean(sub)] * 2, color=col, lw=2.5)
            xticks.append(xpos)
            xlabels.append(f"G{g}\n{lbl[0]}\nn={n}")
            xpos += 1
        xpos += 0.5

    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, fontsize=8)
    ax.set_ylabel("Think token count")
    ax.set_title("Think length by goal × SR outcome (horizontal bar = group mean)", fontsize=9)
    from matplotlib.lines import Line2D
    legend_els = [Line2D([0], [0], color=COL_SUCCESS, lw=2, label="Success"),
                  Line2D([0], [0], color=COL_FAILURE, lw=2, label="Failure")]
    ax.legend(handles=legend_els, fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOT / "goal_think_length_by_outcome.png", dpi=120)
    plt.close(fig)

# ─── Plot 3: layer-22 first-500 by goal × outcome ─────────────────────────────

def plot_goal_layer22_first500(audit: list[dict], fixed: list[dict]) -> None:
    fw22 = {r["example_id"]: cf(r["mean_projection"]) for r in fixed
            if int(r["layer"]) == 22 and int(r["window_size"]) == 500}
    goals = sorted(set(r["goal_index"] for r in audit), key=int)
    think_elig = {r["example_id"] for r in audit if cb(r["usable_for_think_analysis"])}

    fig, ax = plt.subplots(figsize=(9, 4.5))
    xpos = 0
    xticks, xlabels = [], []
    rng_j = np.random.default_rng(42)

    for g in goals:
        for outcome_str, col, lbl in [("True", COL_SUCCESS, "Success"),
                                       ("False", COL_FAILURE, "Failure")]:
            sub = [fw22[r["example_id"]]
                   for r in audit
                   if r["goal_index"] == g
                   and r["example_id"] in fw22
                   and r["example_id"] in think_elig
                   and str(cb(r["sr_success"])).lower() == outcome_str.lower()]
            sub = [v for v in sub if not np.isnan(v)]
            n   = len(sub)
            if n == 0:
                xpos += 1
                continue
            jit = rng_j.uniform(-0.15, 0.15, size=n)
            ax.scatter(np.full(n, xpos) + jit, sub, color=col, alpha=0.7, s=28, zorder=3)
            ax.plot([xpos - 0.3, xpos + 0.3], [np.mean(sub)] * 2, color=col, lw=2.5)
            xticks.append(xpos)
            xlabels.append(f"G{g}\n{lbl[0]}\nn={n}")
            xpos += 1
        xpos += 0.5

    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, fontsize=8)
    ax.set_ylabel("L22 first-500 projection (provisional direction)")
    ax.set_title(
        "Layer-22 first-500 projection by goal × SR outcome\n"
        "(horizontal bar = group mean; individual points shown)",
        fontsize=9)
    from matplotlib.lines import Line2D
    legend_els = [Line2D([0], [0], color=COL_SUCCESS, lw=2, label="Success"),
                  Line2D([0], [0], color=COL_FAILURE, lw=2, label="Failure")]
    ax.legend(handles=legend_els, fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOT / "goal_layer22_first500.png", dpi=120)
    plt.close(fig)

# ─── Plot 4: goal normalized L22 trajectories ─────────────────────────────────

def plot_goal_normalized(goal_norm_rows: list[dict]) -> None:
    goals = sorted(set(r["goal_index"] for r in goal_norm_rows), key=int)
    fig, axes = plt.subplots(1, len(goals), figsize=(4 * len(goals), 4.5), sharey=True)
    if len(goals) == 1:
        axes = [axes]

    for ax, g in zip(axes, goals):
        rows_g = [r for r in goal_norm_rows
                  if r["goal_index"] == g and r["layer"] == PRIMARY_LAYER]
        rows_g.sort(key=lambda r: r["normalized_bin"])
        bins  = [r["normalized_bin"] for r in rows_g]
        sm    = [cf(r["success_mean"])  for r in rows_g]
        fm    = [cf(r["failure_mean"])  for r in rows_g]
        ns    = [r["n_success"]   for r in rows_g]
        nf    = [r["n_failure"]   for r in rows_g]
        clo   = [cf(r["bootstrap_ci_low"])  for r in rows_g]
        chi   = [cf(r["bootstrap_ci_high"]) for r in rows_g]

        ax.plot(bins, sm, color=COL_SUCCESS, lw=2, marker="o", ms=5, label="Success")
        ax.plot(bins, fm, color=COL_FAILURE, lw=2, marker="s", ms=5, label="Failure")
        # Shade CI around the difference
        diffs = [s - f for s, f in zip(sm, fm)]
        ax.fill_between(bins,
                        [lo for lo in clo],
                        [hi for hi in chi],
                        alpha=0.15, color="#555555",
                        label="Diff 95% bootstrap CI")
        ax.set_title(f"Goal {g}\nL22, n_suc={ns[0] if ns else '?'}, n_fail={nf[0] if nf else '?'}",
                     fontsize=9)
        ax.set_xlabel("Normalized bin (0–9)")
        ax.set_xticks(range(10))
        ax.tick_params(axis="both", labelsize=8)
        if g == goals[0]:
            ax.set_ylabel("L22 mean projection (provisional dir.)")
        ax.legend(fontsize=7)

    fig.suptitle("Goal-specific normalized trajectories — Layer 22\n"
                 "(exploratory; small subgroups)", fontsize=9, y=1.02)
    fig.tight_layout()
    fig.savefig(PLOT / "goal_normalized_layer22.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

# ─── Plot 5: goal selected-layer effects ─────────────────────────────────────

def plot_goal_layer_effects(audit: list[dict], fixed: list[dict]) -> None:
    goals  = sorted(set(r["goal_index"] for r in audit), key=int)
    layers = REPORT_LAYERS
    think_elig = {r["example_id"] for r in audit if cb(r["usable_for_think_analysis"])}

    fig, axes = plt.subplots(1, len(goals), figsize=(4 * len(goals), 4.5), sharey=True)
    if len(goals) == 1:
        axes = [axes]

    for ax, g in zip(axes, goals):
        grp     = [r for r in audit if r["goal_index"] == g]
        suc_ids = {r["example_id"] for r in grp if cb(r["sr_success"])} & think_elig
        fai_ids = {r["example_id"] for r in grp if not cb(r["sr_success"])} & think_elig
        y_pos   = np.arange(len(layers))

        for yi, layer in enumerate(layers):
            fmap = {r["example_id"]: cf(r["mean_projection"]) for r in fixed
                    if int(r["layer"]) == layer and int(r["window_size"]) == 500}
            sv = np.array([v for eid, v in fmap.items() if eid in suc_ids and not np.isnan(v)])
            fv = np.array([v for eid, v in fmap.items() if eid in fai_ids and not np.isnan(v)])

            if len(sv) < 1 or len(fv) < 1:
                continue
            diff = float(np.mean(sv) - np.mean(fv))
            ns, nf = len(sv), len(fv)
            ax.barh(yi, diff,
                    color=LAYER_COLORS.get(layer, "#999999"),
                    alpha=0.8, height=0.5)
            ax.text(diff + (0.05 if diff >= 0 else -0.05), yi,
                    f"nS={ns}/nF={nf}", va="center",
                    ha="left" if diff >= 0 else "right", fontsize=7)

        ax.axvline(0, color="black", lw=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels([f"L{l}" for l in layers], fontsize=9)
        ax.set_title(f"Goal {g}", fontsize=9)
        ax.set_xlabel("Success−Failure mean diff", fontsize=8)

    from matplotlib.patches import Patch
    legend_els = [Patch(color=LAYER_COLORS[l], alpha=0.8, label=f"L{l}") for l in layers]
    axes[0].legend(handles=legend_els, fontsize=7, loc="lower right")
    fig.suptitle("Success-minus-failure L22/L16/L13 first-500 projection by goal\n"
                 "(exploratory; small subgroups)", fontsize=9, y=1.02)
    fig.tight_layout()
    fig.savefig(PLOT / "goal_selected_layer_effects.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

# ─── Plot 6: iteration behavior and projection ────────────────────────────────

def plot_iteration(iter_rows: list[dict]) -> None:
    overall = [r for r in iter_rows if r["goal_subset"] == "all"]
    iters   = sorted(r["iteration"] for r in overall)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    metrics = [
        ("sr_success_rate",         "SR success rate"),
        ("think_length_mean",       "Mean think length (tokens)"),
        ("layer22_first500_mean",   "L22 first-500 mean projection"),
    ]
    for ax, (field, label) in zip(axes, metrics):
        vals = [cf(r[field]) for r in overall]
        bars = ax.bar([f"Iter {i}" for i in iters], vals,
                      color=[COL_SUCCESS if i == 1 else COL_FAILURE for i in iters],
                      alpha=0.8)
        for bar, v in zip(bars, vals):
            if not np.isnan(v):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(vals) * 0.02,
                        f"{v:.3f}", ha="center", va="bottom", fontsize=9)
        ax.set_title(label, fontsize=9)
        ax.set_ylabel(label, fontsize=8)

    for r in overall:
        n = r["example_count"]
        axes[0].text(iters.index(r["iteration"]),
                     -0.07, f"n={n}", ha="center", va="top", fontsize=9,
                     transform=axes[0].get_xaxis_transform())

    fig.suptitle("Iteration 1 vs 2: SR success rate, think length, L22 first-500 projection\n"
                 "(exploratory; iteration 2 prompts may differ systematically)", fontsize=9)
    fig.tight_layout()
    fig.savefig(PLOT / "iteration_behavior_projection.png", dpi=120)
    plt.close(fig)

# ─── Plot 7: trajectory type outcomes ─────────────────────────────────────────

def plot_trajectory_types(traj_rows: list[dict]) -> None:
    CATS = ["early_projection", "think_slope", "transition_change", "think_length"]
    fig, axes = plt.subplots(1, len(CATS), figsize=(4.5 * len(CATS), 4))

    for ax, cat in zip(axes, CATS):
        sub = [r for r in traj_rows if r["category"] == cat and r["value"] != "unavailable"]
        labels = [r["value"] for r in sub]
        rates  = [cf(r["sr_success_rate"]) for r in sub]
        ns     = [r["n"] for r in sub]
        colors = [COL_SUCCESS if "high" in l or "increas" in l or "pos" in l or "long" in l
                  else COL_FAILURE for l in labels]

        bars = ax.bar(range(len(labels)), rates, color=colors, alpha=0.8)
        for bar, v, n in zip(bars, rates, ns):
            if not np.isnan(v):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.03,
                        f"n={n}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=8)
        ax.set_ylim(0, 1.15)
        ax.set_title(cat.replace("_", " "), fontsize=9)
        ax.set_ylabel("SR success rate" if ax is axes[0] else "")

    fig.suptitle("SR success rate by predefined trajectory categories\n"
                 "(descriptive only; not natural mechanistic clusters)", fontsize=9)
    fig.tight_layout()
    fig.savefig(PLOT / "trajectory_type_outcomes.png", dpi=120)
    plt.close(fig)

# ─── Validation ───────────────────────────────────────────────────────────────

def validate(audit: list[dict], goal_beh: list[dict],
             goal_proj: list[dict], iter_rows: list[dict]) -> bool:
    ok = True
    def chk(label, cond, note=""):
        nonlocal ok
        status = "OK" if cond else "FAIL"
        if not cond: ok = False
        print(f"  [{status}] {label}" + (f" — {note}" if note else ""))

    # Count checks against audit
    n_total     = len(audit)
    n_think_elig = sum(1 for r in audit if cb(r["usable_for_think_analysis"]))
    n_not_sep   = sum(1 for r in audit if r["thinking_segmentation_status"] == "not_separable")
    n_sr_true   = sum(1 for r in audit if cb(r["sr_success"]))
    n_judge_true= sum(1 for r in audit if cb(r["judge_success"]))

    chk("Total in behavioral summary = 42",
        sum(r["total_examples"] for r in goal_beh) == 42,
        f"got {sum(r['total_examples'] for r in goal_beh)}")
    chk("Think-eligible in behavioral summary = 41",
        sum(r["think_eligible_examples"] for r in goal_beh) == 41,
        f"got {sum(r['think_eligible_examples'] for r in goal_beh)}")
    chk("SR success total = 19",
        sum(r["sr_success_count"] for r in goal_beh) == 19,
        f"got {sum(r['sr_success_count'] for r in goal_beh)}")
    chk("judge_success total = 4",
        sum(r["judge_success_count"] for r in goal_beh) == 4,
        f"got {sum(r['judge_success_count'] for r in goal_beh)}")
    chk("Not-separable count = 1",
        sum(r["not_separable_count"] for r in goal_beh) == 1,
        f"got {sum(r['not_separable_count'] for r in goal_beh)}")

    # Projection features in Part B — check fixed L22 500 goal-all match Phase 2
    # Phase 2 ground truth: success mean across all goals = 4.664, failure = 3.119
    l22_suc_vals = [float(r["mean"]) for r in goal_proj
                    if r["feature"] == "layer22_first500" and r["outcome"] == "success"
                    and r["mean"] != ""]
    l22_fai_vals = [float(r["mean"]) for r in goal_proj
                    if r["feature"] == "layer22_first500" and r["outcome"] == "failure"
                    and r["mean"] != ""]
    chk("L22-first500 success group rows present for all 4 goals",
        len(l22_suc_vals) == 4,
        f"got {len(l22_suc_vals)}")
    chk("L22-first500 failure group rows present for all 4 goals",
        len(l22_fai_vals) == 4,
        f"got {len(l22_fai_vals)}")

    # No fabricated think features for not-separable
    # The not-sep example is goal_2 iter_1 conv_5
    # It should not appear in fixed_window (it's excluded — only 41 in fixed)
    # It should not appear in normalized_progress either
    # We check indirectly: think_eligible for goal_2 must be 11 (12-1)
    g2_elig = next((r for r in goal_beh if r["goal_index"] == 2), None)
    chk("Goal 2 think_eligible = 11 (not_separable excluded)",
        g2_elig is not None and g2_elig["think_eligible_examples"] == 11,
        f"got {g2_elig['think_eligible_examples'] if g2_elig else 'N/A'}")

    # Iteration counts
    it1_all = next((r for r in iter_rows if r["iteration"] == 1 and r["goal_subset"] == "all"), None)
    it2_all = next((r for r in iter_rows if r["iteration"] == 2 and r["goal_subset"] == "all"), None)
    chk("Iteration 1 count = 24", it1_all and it1_all["example_count"] == 24,
        f"got {it1_all['example_count'] if it1_all else 'N/A'}")
    chk("Iteration 2 count = 18", it2_all and it2_all["example_count"] == 18,
        f"got {it2_all['example_count'] if it2_all else 'N/A'}")

    return ok

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Phase 7: goal/iteration exploratory analysis")
    ap.add_argument("--n-bootstrap", type=int, default=N_BOOTSTRAP)
    ap.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    ensure_dir(ANA)
    ensure_dir(PLOT)

    print("[p7] Loading inputs...")
    audit     = load_audit()
    fixed     = load_fixed()
    norm      = load_norm()
    traj_sum  = load_traj_sum()
    layer_sum = load_layer_sum()
    print(f"     audit={len(audit)} fixed={len(fixed)} norm={len(norm)} "
          f"traj_sum={len(traj_sum)} layer_sum={len(layer_sum)}")

    # ── Part A ────────────────────────────────────────────────────────────────
    print("[p7] Part A: goal behavioral summaries...")
    goal_beh = part_a(audit, rng)
    FIELDS_A = [
        "goal_index","total_examples","think_eligible_examples",
        "sr_success_count","sr_failure_count","sr_success_rate",
        "sr_success_rate_wilson_ci_low","sr_success_rate_wilson_ci_high",
        "judge_success_count","combined_success_count",
        "prompt_token_count_mean","prompt_token_count_median",
        "think_token_count_mean","think_token_count_median","think_token_count_std",
        "final_token_count_mean","final_token_count_median",
        "right_censored_count","not_separable_count","warning",
    ]
    with open(OUT_GOAL_BEH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_A, extrasaction="ignore")
        w.writeheader(); w.writerows(goal_beh)
    print(f"     → {OUT_GOAL_BEH} ({len(goal_beh)} rows)")

    # ── Part B ────────────────────────────────────────────────────────────────
    print("[p7] Part B: goal projection summaries...")
    goal_proj = part_b(audit, fixed, norm, layer_sum, rng)
    FIELDS_B = [
        "goal_index","feature","feature_label","outcome",
        "n","mean","median","std","boot_ci_low","boot_ci_high",
        "diff_suc_minus_fai","hedges_g","diff_boot_ci_low","diff_boot_ci_high","warning",
    ]
    with open(OUT_GOAL_PROJ, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_B, extrasaction="ignore")
        w.writeheader(); w.writerows(goal_proj)
    print(f"     → {OUT_GOAL_PROJ} ({len(goal_proj)} rows)")

    # ── Part C ────────────────────────────────────────────────────────────────
    print("[p7] Part C: goal-specific normalized trajectories...")
    goal_norm = part_c(audit, norm, rng)
    FIELDS_C = [
        "goal_index","layer","normalized_bin","n_success","n_failure",
        "success_mean","failure_mean","mean_difference","hedges_g",
        "bootstrap_ci_low","bootstrap_ci_high","warning",
    ]
    with open(OUT_GOAL_NORM, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_C, extrasaction="ignore")
        w.writeheader(); w.writerows(goal_norm)
    print(f"     → {OUT_GOAL_NORM} ({len(goal_norm)} rows)")

    # ── Part D ────────────────────────────────────────────────────────────────
    print("[p7] Part D: attack-iteration analysis...")
    iter_rows = part_d(audit, fixed, norm, layer_sum)
    FIELDS_D = [
        "iteration","goal_subset","example_count","sr_success_count","sr_success_rate",
        "think_length_mean","prompt_length_mean",
        "layer22_first500_mean","layer22_bin0_mean","layer22_full_think_mean",
    ]
    with open(OUT_ITER, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_D, extrasaction="ignore")
        w.writeheader(); w.writerows(iter_rows)
    print(f"     → {OUT_ITER} ({len(iter_rows)} rows)")

    # ── Part E ────────────────────────────────────────────────────────────────
    print("[p7] Part E: conversation-stream descriptives...")
    conv_rows = part_e(audit, fixed)
    FIELDS_E = [
        "conversation_id","example_count","sr_success_count","sr_success_rate",
        "mean_think_length","mean_layer22_first500_projection","warning",
    ]
    with open(OUT_CONV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_E, extrasaction="ignore")
        w.writeheader(); w.writerows(conv_rows)
    print(f"     → {OUT_CONV} ({len(conv_rows)} rows)")

    # ── Part F ────────────────────────────────────────────────────────────────
    print("[p7] Part F: trajectory-type heterogeneity...")
    traj_rows, med_fw22, med_tk = part_f(audit, fixed, layer_sum)
    FIELDS_F = [
        "category","value","n","sr_success_count","sr_success_rate","warning",
    ]
    with open(OUT_TRAJ_TYPE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_F, extrasaction="ignore")
        w.writeheader(); w.writerows(traj_rows)
    print(f"     → {OUT_TRAJ_TYPE} ({len(traj_rows)} rows)")

    # ── Plots ─────────────────────────────────────────────────────────────────
    print("[p7] Generating plots...")
    plot_goal_success_rates(goal_beh)
    print("     goal_success_rates.png")
    plot_think_length(audit)
    print("     goal_think_length_by_outcome.png")
    plot_goal_layer22_first500(audit, fixed)
    print("     goal_layer22_first500.png")
    plot_goal_normalized(goal_norm)
    print("     goal_normalized_layer22.png")
    plot_goal_layer_effects(audit, fixed)
    print("     goal_selected_layer_effects.png")
    plot_iteration(iter_rows)
    print("     iteration_behavior_projection.png")
    plot_trajectory_types(traj_rows)
    print("     trajectory_type_outcomes.png")

    # ── Manifest ──────────────────────────────────────────────────────────────
    print("[p7] Writing manifest...")
    import matplotlib as mpl
    manifest = {
        "script_version":               SCRIPT_VERSION,
        "input_paths": {
            "analysis_dataset":             str(IN_AUDIT),
            "fixed_window_per_example":     str(IN_FIXED),
            "normalized_progress_per_example": str(IN_NORM),
            "per_prompt_trajectory_summary":str(IN_TRAJ_SUM),
            "per_prompt_layer_summary":     str(IN_LAYER),
        },
        "output_paths": {
            "goal_behavior_summary":        str(OUT_GOAL_BEH),
            "goal_projection_summary":      str(OUT_GOAL_PROJ),
            "goal_normalized_trajectories": str(OUT_GOAL_NORM),
            "iteration_summary":            str(OUT_ITER),
            "conversation_stream_summary":  str(OUT_CONV),
            "trajectory_type_summary":      str(OUT_TRAJ_TYPE),
        },
        "outcome_definitions": {
            "primary":   "sr_success = strongreject_score >= 0.5",
            "secondary": "judge_success = judge_score == 10",
        },
        "group_sizes": {
            "total_examples": 42,
            "think_eligible": 41,
            "not_separable":  1,
            "sr_success":     19,
            "sr_failure":     23,
            "judge_success":  4,
            "goal_0": 12, "goal_1": 12, "goal_2": 12, "goal_3": 6,
            "iteration_1": 24, "iteration_2": 18,
        },
        "features_analyzed":   [feat for feat, _ in PROJ_FEATURES],
        "report_layers":        REPORT_LAYERS,
        "primary_layer":        PRIMARY_LAYER,
        "bootstrap_n":          args.n_bootstrap,
        "random_seed":          args.seed,
        "confidence_intervals": {
            "method": "Wilson score (proportions) / nonparametric bootstrap (projections)",
            "alpha":  ALPHA,
        },
        "predefined_trajectory_categories": {
            "early_projection":  f"L22 first-500 >= median ({med_fw22:.3f}) → early_high; else early_low",
            "think_slope":       "L22 full-generation slope > 0 → increasing; else decreasing",
            "transition_change": "transition_post500 - transition_pre500 > 0 → pos; else neg",
            "think_length":      f"think_token_count >= median ({med_tk:.0f}) → long; else short",
        },
        "projection_direction_note": (
            "Projection is onto the provisional harmful-versus-harmless contrast direction. "
            "This direction is diagnostic only; Stage 4A2 found 0 causal survivors. "
            "No abrupt sign reversal was observed at the think-to-final boundary "
            "(Phase 6 observation); this does not rule out a commitment-related transition "
            "occurring before </think>, as a magnitude/slope change, in another layer, or "
            "requiring a multidimensional representation."
        ),
        "exploratory_analysis_warning": EXPLORATORY_WARNING,
        "python_version":  platform.python_version(),
        "numpy_version":   np.__version__,
        "matplotlib_version": mpl.__version__,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    with open(OUT_MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"     → {OUT_MANIFEST}")

    # ── Validation ────────────────────────────────────────────────────────────
    print("\n[p7] ── VALIDATION ──────────────────────────────────────────────────")
    ok = validate(audit, goal_beh, goal_proj, iter_rows)
    print(f"\n[p7] Overall validation: {'PASSED' if ok else 'FAILED'}")

    # ── Results summary ───────────────────────────────────────────────────────
    print("\n[p7] ══ RESULTS SUMMARY ══════════════════════════════════════════════")
    print("\n1. SR success rate and Wilson 95% CI by goal:")
    for r in goal_beh:
        print(f"   Goal {r['goal_index']}: "
              f"{float(r['sr_success_rate']):.3f} "
              f"[{float(r['sr_success_rate_wilson_ci_low']):.3f}, "
              f"{float(r['sr_success_rate_wilson_ci_high']):.3f}] "
              f"({r['sr_success_count']}/{r['total_examples']})")

    print("\n2. Think length (mean) by goal and outcome:")
    for g in sorted(set(r["goal_index"] for r in audit), key=int):
        think_elig = [r for r in audit if r["goal_index"] == g and cb(r["usable_for_think_analysis"])]
        suc_tk = np.array([cf(r["think_token_count"]) for r in think_elig if cb(r["sr_success"])])
        fai_tk = np.array([cf(r["think_token_count"]) for r in think_elig if not cb(r["sr_success"])])
        print(f"   Goal {g}: success {np.mean(suc_tk):.0f}±{np.std(suc_tk, ddof=1):.0f}"
              f" (n={len(suc_tk)})  |  failure {np.mean(fai_tk):.0f}±{np.std(fai_tk, ddof=1):.0f}"
              f" (n={len(fai_tk)})")

    print("\n3. L22 first-500 success−failure diff by goal:")
    fw22_map = {r["example_id"]: cf(r["mean_projection"]) for r in fixed
                if int(r["layer"]) == 22 and int(r["window_size"]) == 500}
    think_elig_ids = {r["example_id"] for r in audit if cb(r["usable_for_think_analysis"])}
    for g in sorted(set(r["goal_index"] for r in audit), key=int):
        grp = [r for r in audit if r["goal_index"] == g and r["example_id"] in think_elig_ids]
        sv  = np.array([fw22_map.get(r["example_id"], np.nan) for r in grp if cb(r["sr_success"])])
        fv  = np.array([fw22_map.get(r["example_id"], np.nan) for r in grp if not cb(r["sr_success"])])
        sv  = sv[~np.isnan(sv)]; fv = fv[~np.isnan(fv)]
        diff = float(np.mean(sv) - np.mean(fv)) if (len(sv) > 0 and len(fv) > 0) else np.nan
        g_h  = hedges_g(sv, fv)
        lo, hi = bootstrap_ci(sv, fv, rng) if len(sv) > 0 and len(fv) > 0 else (np.nan, np.nan)
        sign = "✓ positive" if diff > 0 else "✗ negative/zero"
        print(f"   Goal {g}: diff={diff:+.3f}  g={g_h:+.3f}  CI=[{lo:.3f},{hi:.3f}]  {sign}"
              f"  (nS={len(sv)}, nF={len(fv)})")

    print("\n4. Positive early-projection association by goal:")
    for g in sorted(set(r["goal_index"] for r in audit), key=int):
        # goal_norm stores goal_index as int; g is a string from audit — convert for comparison
        rows_g = [r for r in goal_norm if r["goal_index"] == int(g) and r["layer"] == PRIMARY_LAYER]
        pos_bins = sum(1 for r in rows_g if cf(r["mean_difference"]) > 0)
        print(f"   Goal {g}: {pos_bins}/10 bins have positive success−failure L22 diff")

    print("\n5. Leave-one-goal-out instability (Phase 4/5 reference):")
    print("   Goal 2 excluded → OR dropped from 4.00 to 1.90, CI includes 1.")
    print("   Phase 7 checks whether Goal 2 is qualitatively different.")
    g2_rows = [r for r in audit if r["goal_index"] == "2"]
    g2_sr   = sum(1 for r in g2_rows if cb(r["sr_success"]))
    g2_n    = len(g2_rows)
    g2_fw22 = [fw22_map.get(r["example_id"], np.nan) for r in g2_rows
               if r["example_id"] in think_elig_ids]
    g2_fw22 = [v for v in g2_fw22 if not np.isnan(v)]
    print(f"   Goal 2: SR={g2_sr}/{g2_n}={g2_sr/g2_n:.3f}  "
          f"L22-first500 mean={np.mean(g2_fw22):.3f} (n={len(g2_fw22)})")
    for g in [g for g in sorted(set(r["goal_index"] for r in audit), key=int) if g != "2"]:
        grp = [r for r in audit if r["goal_index"] == g and r["example_id"] in think_elig_ids]
        vs  = [fw22_map.get(r["example_id"], np.nan) for r in grp]
        vs  = [v for v in vs if not np.isnan(v)]
        sr  = sum(1 for r in grp if cb(r["sr_success"]))
        print(f"   Goal {g}: SR={sr}/{len(grp)}  L22-first500 mean={np.mean(vs):.3f} (n={len(vs)})")

    print("\n7. Iteration 1 vs 2:")
    it1 = next(r for r in iter_rows if r["iteration"] == 1 and r["goal_subset"] == "all")
    it2 = next(r for r in iter_rows if r["iteration"] == 2 and r["goal_subset"] == "all")
    for field in ["sr_success_rate", "think_length_mean", "layer22_first500_mean"]:
        print(f"   {field}: iter1={it1[field]}  iter2={it2[field]}")

    print("\n8. Conversation stream SR success rates:")
    for r in conv_rows:
        print(f"   Conv {r['conversation_id']}: "
              f"n={r['example_count']}  SR_rate={r['sr_success_rate']}  "
              f"L22={r['mean_layer22_first500_projection']}")

    print("\n9. Predefined trajectory type SR success rates:")
    for cat in ["early_projection", "think_slope", "transition_change", "think_length"]:
        sub = [r for r in traj_rows if r["category"] == cat and r["value"] != "unavailable"]
        line = "   " + cat + ": " + " | ".join(
            f"{r['value']}={r['sr_success_rate']} (n={r['n']})" for r in sub
        )
        print(line)

    print("\n10. Overall heterogeneity assessment (exploratory):")
    all_diffs = []
    for g in sorted(set(r["goal_index"] for r in audit), key=int):
        grp = [r for r in audit if r["goal_index"] == g and r["example_id"] in think_elig_ids]
        sv  = np.array([fw22_map.get(r["example_id"], np.nan) for r in grp if cb(r["sr_success"])])
        fv  = np.array([fw22_map.get(r["example_id"], np.nan) for r in grp if not cb(r["sr_success"])])
        sv  = sv[~np.isnan(sv)]; fv = fv[~np.isnan(fv)]
        if len(sv) > 0 and len(fv) > 0:
            all_diffs.append(float(np.mean(sv) - np.mean(fv)))
    if all_diffs:
        all_pos = all(d > 0 for d in all_diffs)
        print(f"   All-positive diffs across goals: {all_pos} (diffs: {[f'{d:+.3f}' for d in all_diffs]})")

    print("\n11. Small-sample warnings:")
    print("   - Goal 3: only 6 examples (1 attack iteration); all estimates highly uncertain.")
    print("   - All goal-level subgroups are too small for confirmatory inference.")
    print("   - Confidence intervals are descriptive; bootstrap CIs may be unstable at n<5.")
    print("   - Iteration 2 prompts come from an iterative refinement process and may differ")
    print("     systematically from iteration 1; iteration comparison is not causal.")
    print("   - Conversation IDs represent attack streams, not randomized conditions.")

    return ok


if __name__ == "__main__":
    main()
