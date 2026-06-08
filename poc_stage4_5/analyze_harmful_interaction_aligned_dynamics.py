"""
Stage 4.5 — Phase 3: Event-Aligned Projection Analysis.

Loads Stage 4 per-example projection artifacts and aligns them to the
manually annotated harmful-interaction-start token, then computes per-example
features, group statistics, and Firth logistic regression models.

Outputs (all under <run-dir>/):
  analysis/harmful_interaction_annotation_audit.json
  analysis/evaluator_agreement_summary.csv / .json
  analysis/event_aligned_per_example.csv
  analysis/event_aligned_group_summary.csv
  analysis/event_aligned_firth_coefficients.csv
  analysis/event_aligned_analysis.json
  analysis/leave_one_goal_out.csv
  analysis/stream_sensitivity.csv
  manifests/run_manifest.json

Graceful degradation: if fewer than MIN_ANNOTATIONS annotated examples are
available, writes the per-example CSV with whatever is ready and exits 0 with
a warning (does not fit models).

Cautious terminology: the projection direction is
"provisional harmful-versus-harmless contrast direction" only.
No causal claims are made.

Usage:
  python -m poc_stage4_5.analyze_harmful_interaction_aligned_dynamics \\
      --run-dir outputs/stage4_5/harmful_interaction_alignment/run_20260608_120000 \\
      --review-dir review/ [options]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats as scipy_stats

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common
from poc_stage4.fit_confound_models import (
    firth_fit,
    build_design_matrix,
    loo_predict,
    compute_metrics,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_ANNOTATIONS = 5          # minimum annotated examples to run models
PRE_WINDOW = 500             # tokens before event
POST_EARLY_END = 250         # post-event early window: [0, 250)
POST_LATE_END = 1000         # post-event late window: [250, 1000)
RANDOM_SEED = 42
N_BOOTSTRAP = 2_000
N_PERMUTATIONS = 10_000

PRIMARY_LAYER = common.PRIMARY_LAYER           # 22
SELECTED_LAYERS = common.SELECTED_LAYERS       # [13, 16, 22, 26, 30, 38, 39]
EXPLORATORY_LAYERS = common.EXPLORATORY_LAYERS # {13, 16, 38}

_ALPHA = 0.05

# ---------------------------------------------------------------------------
# CSV field schemas
# ---------------------------------------------------------------------------

PER_EXAMPLE_FIELDS: list[str] = [
    "example_id", "goal_index", "attack_iteration", "conversation_id",
    "target_model", "strongreject_score", "sr_success", "judge_success",
    "think_token_count", "generation_token_count", "right_censored",
    "harmful_interaction_start_token", "interaction_phase",
    "relative_onset_position", "annotation_confidence",
    "annotation_status", "is_primary_analysis",
    "layer",
    "pre_event_n_tokens", "post_event_early_n_tokens", "post_event_late_n_tokens",
    "pre_event_mean_projection", "post_event_early_mean", "post_event_late_mean",
    "event_delta_early", "event_delta_late",
    "pre_event_slope", "post_event_early_slope", "post_event_late_slope",
    "slope_change_at_event",
    "pre_event_std", "post_event_std",
    "normalized_auc_pre", "normalized_auc_post",
    "projection_at_event",
    "minimum_after_event", "maximum_after_event",
    "tokens_until_local_extremum",
    "is_exploratory_layer",
]

GROUP_SUMMARY_FIELDS: list[str] = [
    "layer", "feature", "subset", "is_exploratory_layer",
    "n_success", "n_failure",
    "success_mean", "failure_mean", "success_std", "failure_std",
    "mean_difference", "hedges_g", "rank_biserial",
    "mann_whitney_u", "mann_whitney_p", "permutation_p",
    "bootstrap_ci_low", "bootstrap_ci_high",
    "bh_adjusted_p",
]

FIRTH_COEF_FIELDS: list[str] = [
    "model_name", "outcome", "subset", "predictor",
    "coefficient", "standard_error", "odds_ratio",
    "ci_low", "ci_high", "wald_z", "p_value_wald",
    "converged", "warning", "is_exploratory",
]

LOGO_FIELDS: list[str] = [
    "excluded_goal", "layer", "feature", "outcome", "subset",
    "n_success", "n_failure", "hedges_g", "mann_whitney_p",
    "or_post_event_proj", "or_ci_low", "or_ci_high",
]

STREAM_FIELDS: list[str] = [
    "excluded_stream", "layer", "feature", "outcome",
    "n_success", "n_failure", "hedges_g", "mann_whitney_p",
]

# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------

def compute_event_aligned_features(
    token_level_data: list[dict],
    harmful_start_idx: int,
    layer: int,
    pre_window: int = PRE_WINDOW,
    post_early_end: int = POST_EARLY_END,
    post_late_end: int = POST_LATE_END,
) -> dict[str, Any]:
    """
    Compute event-aligned projection features for one example and one layer.

    All think tokens are used.  If interaction_phase is 'final', final tokens
    are included (flagged separately for sensitivity analysis).

    Returns a dict of features; pre-event features are NaN if empty window.
    """
    think_toks = [t for t in token_level_data if t.get("role_or_part") == "think"]
    key = str(layer)

    pre: list[float] = []
    post_early: list[float] = []
    post_late: list[float] = []
    proj_at_event: float = float("nan")

    for t in think_toks:
        rel = t["generated_token_index"] - harmful_start_idx
        v = t["layer_projections"].get(key)
        if v is None or not math.isfinite(v):
            continue
        if rel == 0:
            proj_at_event = float(v)
        if -pre_window <= rel < 0:
            pre.append(v)
        if 0 <= rel < post_early_end:
            post_early.append(v)
        if post_early_end <= rel < post_late_end:
            post_late.append(v)

    pre_arr = np.array(pre, dtype=np.float64)
    early_arr = np.array(post_early, dtype=np.float64)
    late_arr = np.array(post_late, dtype=np.float64)

    def _mean(a: np.ndarray) -> float:
        return float(np.mean(a)) if len(a) > 0 else float("nan")

    def _std(a: np.ndarray) -> float:
        return float(np.std(a, ddof=1)) if len(a) > 1 else float("nan")

    def _slope(a: np.ndarray, toks: list[dict]) -> float:
        """Linear slope of projections vs. generated_token_index."""
        if len(a) < 2:
            return float("nan")
        xs = np.array([t["generated_token_index"] for t in toks if
                        t["layer_projections"].get(key) is not None and
                        math.isfinite(t["layer_projections"][key])], dtype=np.float64)
        if len(xs) < 2 or len(xs) != len(a):
            return float("nan")
        slope, _, _, _, _ = scipy_stats.linregress(xs, a)
        return float(slope)

    def _norm_auc(a: np.ndarray) -> float:
        if len(a) == 0:
            return float("nan")
        return float(np.trapz(a, np.linspace(0, 1, len(a))))

    def _extremum_dist(a: np.ndarray) -> int:
        if len(a) == 0:
            return -1
        peak_idx = int(np.argmax(np.abs(a)))
        return peak_idx

    pre_mean = _mean(pre_arr)
    early_mean = _mean(early_arr)
    late_mean = _mean(late_arr)

    delta_early = (early_mean - pre_mean
                   if not (math.isnan(pre_mean) or math.isnan(early_mean))
                   else float("nan"))
    delta_late = (late_mean - pre_mean
                  if not (math.isnan(pre_mean) or math.isnan(late_mean))
                  else float("nan"))

    # Slopes using tokens in each window
    pre_toks = [t for t in think_toks if -pre_window <= (t["generated_token_index"] - harmful_start_idx) < 0
                and math.isfinite(t["layer_projections"].get(key, float("nan")))]
    early_toks = [t for t in think_toks if 0 <= (t["generated_token_index"] - harmful_start_idx) < post_early_end
                  and math.isfinite(t["layer_projections"].get(key, float("nan")))]
    late_toks = [t for t in think_toks if post_early_end <= (t["generated_token_index"] - harmful_start_idx) < post_late_end
                 and math.isfinite(t["layer_projections"].get(key, float("nan")))]

    pre_slope = _slope(pre_arr, pre_toks)
    early_slope = _slope(early_arr, early_toks)
    late_slope = _slope(late_arr, late_toks)

    slope_change = (early_slope - pre_slope
                    if not (math.isnan(pre_slope) or math.isnan(early_slope))
                    else float("nan"))

    post_all = np.concatenate([early_arr, late_arr]) if (len(early_arr) + len(late_arr)) > 0 else np.array([])

    return {
        "pre_event_n_tokens": len(pre_arr),
        "post_event_early_n_tokens": len(early_arr),
        "post_event_late_n_tokens": len(late_arr),
        "pre_event_mean_projection": pre_mean,
        "post_event_early_mean": early_mean,
        "post_event_late_mean": late_mean,
        "event_delta_early": delta_early,
        "event_delta_late": delta_late,
        "pre_event_slope": pre_slope,
        "post_event_early_slope": early_slope,
        "post_event_late_slope": late_slope,
        "slope_change_at_event": slope_change,
        "pre_event_std": _std(pre_arr),
        "post_event_std": _std(post_all),
        "normalized_auc_pre": _norm_auc(pre_arr),
        "normalized_auc_post": _norm_auc(early_arr),
        "projection_at_event": proj_at_event,
        "minimum_after_event": float(np.min(post_all)) if len(post_all) > 0 else float("nan"),
        "maximum_after_event": float(np.max(post_all)) if len(post_all) > 0 else float("nan"),
        "tokens_until_local_extremum": _extremum_dist(post_all),
    }


# ---------------------------------------------------------------------------
# Dataset construction
# ---------------------------------------------------------------------------

def build_per_example_dataset(
    annotations: dict[str, dict],
    dataset_meta: list[dict],
    layers: list[int] = SELECTED_LAYERS,
) -> list[dict]:
    """
    For every annotated example and layer, compute event-aligned features.

    Primary analysis: interaction_phase == 'think'.
    Sensitivity: interaction_phase == 'final' (flagged is_primary_analysis=False).
    """
    meta_map = {r["example_id"]: r for r in dataset_meta}
    rows: list[dict] = []

    for eid, ann in annotations.items():
        status = ann.get("annotation_status", "")
        if status not in ("annotated",):
            continue

        try:
            start_tok = int(ann["harmful_interaction_start_token"])
        except (KeyError, ValueError, TypeError):
            continue

        if start_tok < 0:
            continue

        phase = ann.get("interaction_phase", "unknown")
        is_primary = phase == "think"

        meta = meta_map.get(eid, {})
        think_tc = int(meta.get("think_token_count", 0) or 0)
        gen_tc = int(meta.get("generation_token_count", 0) or 0)
        relative_onset = (start_tok / think_tc) if think_tc > 0 else float("nan")

        try:
            artifact = common.load_stage4_per_example(eid)
        except FileNotFoundError:
            warnings.warn(f"Stage 4 artifact missing for {eid!r}; skipping.")
            continue

        tld = artifact.get("token_level_data", [])
        if not tld:
            warnings.warn(f"Empty token_level_data for {eid!r}; skipping.")
            continue

        for layer in layers:
            feats = compute_event_aligned_features(tld, start_tok, layer)
            rows.append({
                "example_id": eid,
                "goal_index": meta.get("goal_index", ""),
                "attack_iteration": meta.get("attack_iteration", ""),
                "conversation_id": meta.get("conversation_id", ""),
                "target_model": meta.get("target_model", ""),
                "strongreject_score": meta.get("strongreject_score", ""),
                "sr_success": meta.get("sr_success", ""),
                "judge_success": meta.get("judge_success", ""),
                "think_token_count": think_tc,
                "generation_token_count": gen_tc,
                "right_censored": meta.get("right_censored", ""),
                "harmful_interaction_start_token": start_tok,
                "interaction_phase": phase,
                "relative_onset_position": relative_onset,
                "annotation_confidence": ann.get("annotation_confidence", ""),
                "annotation_status": status,
                "is_primary_analysis": is_primary,
                "layer": layer,
                "is_exploratory_layer": layer in EXPLORATORY_LAYERS,
                **feats,
            })

    return rows


# ---------------------------------------------------------------------------
# Annotation audit
# ---------------------------------------------------------------------------

def audit_annotations(
    annotations: dict[str, dict],
    dataset_meta: list[dict],
) -> dict[str, Any]:
    """Validate annotations; return audit report dict."""
    meta_map = {r["example_id"]: r for r in dataset_meta}
    errors: list[str] = []
    warnings_list: list[str] = []
    counts: dict[str, int] = {}

    seen_ids: set[str] = set()
    for eid, ann in annotations.items():
        status = ann.get("annotation_status", "missing")
        counts[status] = counts.get(status, 0) + 1

        if eid in seen_ids:
            errors.append(f"Duplicate example_id: {eid!r}")
        seen_ids.add(eid)

        meta = meta_map.get(eid)
        if meta is None:
            errors.append(f"Annotation for unknown example_id: {eid!r}")
            continue

        gen_tc = int(meta.get("generation_token_count", 0) or 0)
        start_raw = ann.get("harmful_interaction_start_token", "")
        if start_raw not in ("", "-1", None):
            try:
                start_tok = int(start_raw)
            except ValueError:
                errors.append(f"{eid!r}: harmful_interaction_start_token is not integer: {start_raw!r}")
                continue
            if gen_tc > 0 and not (0 <= start_tok < gen_tc):
                errors.append(
                    f"{eid!r}: harmful_interaction_start_token={start_tok} "
                    f"out of range [0, {gen_tc})"
                )

    unannotated = [r["example_id"] for r in dataset_meta
                   if r["example_id"] not in seen_ids]

    return {
        "n_total_examples": len(dataset_meta),
        "n_annotated": len(annotations),
        "n_unannotated": len(unannotated),
        "counts_by_status": counts,
        "errors": errors,
        "warnings": warnings_list,
        "has_errors": len(errors) > 0,
    }


# ---------------------------------------------------------------------------
# Evaluator agreement summary
# ---------------------------------------------------------------------------

def build_evaluator_agreement_summary(dataset_meta: list[dict]) -> list[dict]:
    """Compute evaluator agreement categories for all 42 examples."""
    rows = []
    for r in dataset_meta:
        sr = r.get("sr_success", False)
        judge = r.get("judge_success", False)
        if sr and judge:
            agreement = "both_positive"
        elif sr and not judge:
            agreement = "sr_positive_judge_negative"
        elif not sr and judge:
            agreement = "sr_negative_judge_positive"
        else:
            agreement = "both_negative"
        rows.append({
            "example_id": r["example_id"],
            "goal_index": r["goal_index"],
            "attack_iteration": r["attack_iteration"],
            "conversation_id": r["conversation_id"],
            "strongreject_score": r["strongreject_score"],
            "sr_success": r["sr_success"],
            "judge_score": r.get("judge_score", ""),
            "judge_success": r["judge_success"],
            "evaluator_agreement_type": agreement,
        })
    return rows


# ---------------------------------------------------------------------------
# BH correction
# ---------------------------------------------------------------------------

def bh_correct(pvals: list[float], alpha: float = _ALPHA) -> list[float]:
    """Benjamini-Hochberg correction. Returns adjusted p-values."""
    n = len(pvals)
    if n == 0:
        return []
    ranked = sorted(range(n), key=lambda i: pvals[i])
    adj = [1.0] * n
    for rank, orig_idx in enumerate(ranked):
        adj[orig_idx] = min(1.0, pvals[orig_idx] * n / (rank + 1))
    # Enforce monotonicity (adjusted p-values must be non-decreasing)
    cummin = 1.0
    for orig_idx in reversed(ranked):
        adj[orig_idx] = min(adj[orig_idx], cummin)
        cummin = adj[orig_idx]
    return adj


# ---------------------------------------------------------------------------
# Group statistics
# ---------------------------------------------------------------------------

def compute_group_summary(
    per_example_rows: list[dict],
    rng: np.random.Generator,
    n_bootstrap: int = N_BOOTSTRAP,
    n_permutations: int = N_PERMUTATIONS,
    outcome_col: str = "sr_success",
) -> list[dict]:
    """
    Compute group statistics per layer × feature × subset.

    Subsets:
      primary      — only think-phase events (is_primary_analysis=True)
      primary_hc   — think-phase + high_confidence only
      all_phases   — include final-phase events (sensitivity)
    """
    features_to_test = [
        "pre_event_mean_projection",
        "post_event_early_mean",
        "post_event_late_mean",
        "event_delta_early",
        "relative_onset_position",
    ]

    subsets = {
        "primary": lambda r: r.get("is_primary_analysis") is True,
        "primary_hc": lambda r: r.get("is_primary_analysis") is True
                                and r.get("annotation_confidence") == "high",
        "all_phases": lambda r: True,
    }

    all_rows_out: list[dict] = []
    pvals_for_bh: list[tuple[int, str, str, str, float]] = []  # (row_idx, ...)

    for layer in SELECTED_LAYERS:
        layer_rows = [r for r in per_example_rows if int(r.get("layer", -1)) == layer]
        is_expl = layer in EXPLORATORY_LAYERS

        for feat in features_to_test:
            for subset_name, subset_fn in subsets.items():
                eligible = [r for r in layer_rows if subset_fn(r)]

                sr_success_vals = np.array(
                    [float(r[feat]) for r in eligible
                     if str(r.get(outcome_col, "")) == "True"
                     and not math.isnan(float(r[feat]) if r[feat] not in ("", None) else float("nan"))],
                    dtype=np.float64,
                )
                sr_failure_vals = np.array(
                    [float(r[feat]) for r in eligible
                     if str(r.get(outcome_col, "")) == "False"
                     and not math.isnan(float(r[feat]) if r[feat] not in ("", None) else float("nan"))],
                    dtype=np.float64,
                )

                n_s, n_f = len(sr_success_vals), len(sr_failure_vals)

                if n_s == 0 or n_f == 0:
                    row_out = {
                        "layer": layer, "feature": feat, "subset": subset_name,
                        "is_exploratory_layer": is_expl,
                        "n_success": n_s, "n_failure": n_f,
                        **{k: float("nan") for k in [
                            "success_mean", "failure_mean", "success_std", "failure_std",
                            "mean_difference", "hedges_g", "rank_biserial",
                            "mann_whitney_u", "mann_whitney_p", "permutation_p",
                            "bootstrap_ci_low", "bootstrap_ci_high", "bh_adjusted_p",
                        ]},
                    }
                else:
                    stats = common.compute_group_stats(
                        sr_success_vals, sr_failure_vals, n_bootstrap, n_permutations, rng
                    )
                    rb = common.rank_biserial(
                        sr_success_vals, sr_failure_vals, stats["mann_whitney_u"]
                    )
                    row_out = {
                        "layer": layer, "feature": feat, "subset": subset_name,
                        "is_exploratory_layer": is_expl,
                        "n_success": n_s, "n_failure": n_f,
                        "success_mean": stats["success_mean"],
                        "failure_mean": stats["failure_mean"],
                        "success_std": stats["success_std"],
                        "failure_std": stats["failure_std"],
                        "mean_difference": stats["mean_difference"],
                        "hedges_g": stats["hedges_g"],
                        "rank_biserial": rb,
                        "mann_whitney_u": stats["mann_whitney_u"],
                        "mann_whitney_p": stats["mann_whitney_p"],
                        "permutation_p": stats["permutation_p"],
                        "bootstrap_ci_low": stats["bootstrap_ci_low"],
                        "bootstrap_ci_high": stats["bootstrap_ci_high"],
                        "bh_adjusted_p": float("nan"),  # filled later
                    }
                    pvals_for_bh.append(
                        (len(all_rows_out), layer, feat, subset_name,
                         stats["mann_whitney_p"])
                    )

                all_rows_out.append(row_out)

    # Apply BH correction across all non-NaN p-values
    if pvals_for_bh:
        pv = [t[4] for t in pvals_for_bh]
        adj = bh_correct(pv)
        for (row_idx, *_), adj_p in zip(pvals_for_bh, adj):
            all_rows_out[row_idx]["bh_adjusted_p"] = adj_p

    return all_rows_out


# ---------------------------------------------------------------------------
# Firth models
# ---------------------------------------------------------------------------

def _build_raw(
    rows_layer22: list[dict],
    projection_feature: str,
    outcome_col: str = "sr_success",
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Build raw input dict for fit_model / build_design_matrix."""
    proj = np.array([float(r[projection_feature])
                     for r in rows_layer22], dtype=np.float64)
    log_think = np.array([math.log1p(int(r["think_token_count"]))
                           for r in rows_layer22], dtype=np.float64)
    prompt = np.array([int(r.get("prompt_token_count") or 0)
                        for r in rows_layer22], dtype=np.float64)
    goal = np.array([int(r["goal_index"]) for r in rows_layer22], dtype=np.float64)
    attack_iter = np.array([int(r["attack_iteration"])
                             for r in rows_layer22], dtype=np.float64)
    y = np.array([1.0 if str(r.get(outcome_col)) == "True" else 0.0
                   for r in rows_layer22], dtype=np.float64)

    raw = {
        "projection": proj,
        "log_think": log_think,
        "prompt": prompt,
        "goal": goal,
        "attack_iter": attack_iter,
    }
    return raw, y


def _fit_single_model(
    raw: dict[str, np.ndarray],
    y: np.ndarray,
    features: list[str],
    model_name: str,
    outcome: str,
    subset: str,
    is_exploratory: bool,
) -> tuple[list[dict], dict]:
    """Fit one Firth model; return (coefficient_rows, summary_dict)."""
    from poc_stage4.fit_confound_models import firth_fit, build_design_matrix, loo_predict
    from scipy.special import expit
    from scipy import stats as scipy_stats

    X, col_names, std_p = build_design_matrix(
        raw["projection"], raw["log_think"], raw["prompt"],
        raw["goal"], raw["attack_iter"],
        features, compute_std=True,
    )
    result = firth_fit(X, y)

    z_vals = result["coef"] / np.where(result["se"] > 1e-15, result["se"], np.nan)
    wald_p = 2.0 * (1.0 - scipy_stats.norm.cdf(np.abs(z_vals)))
    ci_low = result["coef"] - 1.96 * result["se"]
    ci_high = result["coef"] + 1.96 * result["se"]
    or_val = np.exp(np.clip(result["coef"], -500, 500))

    coef_rows = []
    for i, col in enumerate(col_names):
        coef_rows.append({
            "model_name": model_name,
            "outcome": outcome,
            "subset": subset,
            "predictor": col,
            "coefficient": float(result["coef"][i]),
            "standard_error": float(result["se"][i]),
            "odds_ratio": float(or_val[i]),
            "ci_low": float(np.exp(np.clip(ci_low[i], -500, 500))),
            "ci_high": float(np.exp(np.clip(ci_high[i], -500, 500))),
            "wald_z": float(z_vals[i]),
            "p_value_wald": float(wald_p[i]),
            "converged": result.get("converged", False),
            "warning": result.get("warning", ""),
            "is_exploratory": is_exploratory,
        })

    train_metrics = {
        "log_loss": float(-np.mean(y * np.log(np.clip(result["fitted"], 1e-12, 1 - 1e-12)) +
                                   (1 - y) * np.log(np.clip(1 - result["fitted"], 1e-12, 1 - 1e-12)))),
    }

    summary = {
        "model_name": model_name,
        "n": int(len(y)),
        "n_events": int(np.sum(y)),
        "converged": result.get("converged", False),
        "features": features,
        "col_names": col_names,
    }
    return coef_rows, summary


def fit_all_firth_models(
    per_example_rows: list[dict],
    layer: int = PRIMARY_LAYER,
    outcome: str = "sr_success",
) -> tuple[list[dict], list[dict]]:
    """
    Fit the pre-specified model suite at the given layer and outcome.

    Returns (coef_rows, model_summaries).
    """
    # Filter to primary-analysis examples at the given layer
    eligible = [r for r in per_example_rows
                if int(r.get("layer", -1)) == layer
                and r.get("is_primary_analysis") is True]

    # Drop rows with NaN in key features
    eligible_with_pre = [r for r in eligible
                          if not math.isnan(float(r.get("pre_event_mean_projection") or "nan"))
                          and not math.isnan(float(r.get("event_delta_early") or "nan"))]
    eligible_post_only = [r for r in eligible
                           if not math.isnan(float(r.get("post_event_early_mean") or "nan"))]

    all_coef_rows: list[dict] = []
    all_summaries: list[dict] = []

    model_specs = [
        # (name, eligible_subset, features, is_expl)
        ("M0_covariates",
         eligible_post_only,
         ["intercept", "log_think", "prompt_z", "goal_1", "goal_2", "goal_3", "attack_iter"],
         False),
        ("M2_post_event_only",
         eligible_post_only,
         ["intercept", "projection_z"],
         False),
        ("M3_post_event_adjusted",
         eligible_post_only,
         ["intercept", "projection_z", "log_think", "prompt_z",
          "goal_1", "goal_2", "goal_3", "attack_iter"],
         False),
        ("M1_pre_event_only",
         eligible_with_pre,
         ["intercept", "projection_z"],
         False),
        ("M4_delta_only",
         eligible_with_pre,
         ["intercept", "projection_z"],
         False),
    ]

    for model_name, subset_rows, features, is_expl in model_specs:
        if len(subset_rows) < MIN_ANNOTATIONS:
            all_summaries.append({
                "model_name": model_name,
                "skipped": True,
                "reason": f"n={len(subset_rows)} < MIN_ANNOTATIONS={MIN_ANNOTATIONS}",
            })
            continue

        # Choose projection feature based on model name
        if "pre_event" in model_name or model_name == "M4_delta_only":
            proj_feat = "pre_event_mean_projection" if "pre_event" in model_name else "event_delta_early"
        else:
            proj_feat = "post_event_early_mean"

        # Re-filter for non-NaN in chosen feature
        final_rows = [r for r in subset_rows
                       if not math.isnan(float(r.get(proj_feat) or "nan"))]
        if len(final_rows) < MIN_ANNOTATIONS:
            all_summaries.append({
                "model_name": model_name,
                "skipped": True,
                "reason": f"After NaN filter, n={len(final_rows)} < {MIN_ANNOTATIONS}",
            })
            continue

        try:
            raw, y = _build_raw(final_rows, proj_feat)
            coef_rows, summary = _fit_single_model(
                raw, y, features, model_name, outcome, "primary", is_expl
            )
            all_coef_rows.extend(coef_rows)
            all_summaries.append(summary)
        except Exception as e:
            all_summaries.append({
                "model_name": model_name,
                "skipped": True,
                "reason": f"Exception: {e}",
            })

    return all_coef_rows, all_summaries


# ---------------------------------------------------------------------------
# Leave-one-goal-out analysis
# ---------------------------------------------------------------------------

def run_logo_analysis(
    per_example_rows: list[dict],
    layer: int = PRIMARY_LAYER,
    rng: np.random.Generator | None = None,
    n_bootstrap: int = N_BOOTSTRAP,
    n_permutations: int = N_PERMUTATIONS,
    outcome_col: str = "sr_success",
) -> list[dict]:
    """Leave-one-goal-out sensitivity for post_event_early_mean at primary layer."""
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)
    eligible = [r for r in per_example_rows
                if int(r.get("layer", -1)) == layer
                and r.get("is_primary_analysis") is True
                and not math.isnan(float(r.get("post_event_early_mean") or "nan"))]

    goals = sorted({int(r["goal_index"]) for r in eligible})
    rows_out: list[dict] = []

    for excl_goal in goals:
        subset = [r for r in eligible if int(r["goal_index"]) != excl_goal]
        s_vals = np.array([float(r["post_event_early_mean"]) for r in subset
                            if str(r.get(outcome_col)) == "True"], dtype=np.float64)
        f_vals = np.array([float(r["post_event_early_mean"]) for r in subset
                            if str(r.get(outcome_col)) == "False"], dtype=np.float64)
        if len(s_vals) == 0 or len(f_vals) == 0:
            rows_out.append({"excluded_goal": excl_goal, "layer": layer,
                              "feature": "post_event_early_mean",
                              "outcome": outcome_col, "subset": f"excl_goal_{excl_goal}",
                              "n_success": len(s_vals), "n_failure": len(f_vals),
                              "hedges_g": float("nan"), "mann_whitney_p": float("nan"),
                              "or_post_event_proj": float("nan"),
                              "or_ci_low": float("nan"), "or_ci_high": float("nan")})
            continue
        stats = common.compute_group_stats(s_vals, f_vals, n_bootstrap, n_permutations, rng)
        rows_out.append({
            "excluded_goal": excl_goal,
            "layer": layer,
            "feature": "post_event_early_mean",
            "outcome": "sr_success",
            "subset": f"excl_goal_{excl_goal}",
            "n_success": len(s_vals),
            "n_failure": len(f_vals),
            "hedges_g": stats["hedges_g"],
            "mann_whitney_p": stats["mann_whitney_p"],
            "or_post_event_proj": float("nan"),
            "or_ci_low": float("nan"),
            "or_ci_high": float("nan"),
        })
    return rows_out


# ---------------------------------------------------------------------------
# Stream sensitivity analysis
# ---------------------------------------------------------------------------

def run_stream_sensitivity(
    per_example_rows: list[dict],
    layer: int = PRIMARY_LAYER,
    rng: np.random.Generator | None = None,
    n_bootstrap: int = N_BOOTSTRAP,
    n_permutations: int = N_PERMUTATIONS,
    outcome_col: str = "sr_success",
) -> list[dict]:
    """Leave-one-stream-out sensitivity for post_event_early_mean."""
    if rng is None:
        rng = np.random.default_rng(RANDOM_SEED)
    eligible = [r for r in per_example_rows
                if int(r.get("layer", -1)) == layer
                and r.get("is_primary_analysis") is True
                and not math.isnan(float(r.get("post_event_early_mean") or "nan"))]

    convs = sorted({int(r["conversation_id"]) for r in eligible})
    rows_out: list[dict] = []

    for excl_conv in convs:
        subset = [r for r in eligible if int(r["conversation_id"]) != excl_conv]
        s_vals = np.array([float(r["post_event_early_mean"]) for r in subset
                            if str(r.get(outcome_col)) == "True"], dtype=np.float64)
        f_vals = np.array([float(r["post_event_early_mean"]) for r in subset
                            if str(r.get(outcome_col)) == "False"], dtype=np.float64)
        if len(s_vals) == 0 or len(f_vals) == 0:
            rows_out.append({"excluded_stream": excl_conv, "layer": layer,
                              "feature": "post_event_early_mean",
                              "outcome": outcome_col,
                              "n_success": len(s_vals), "n_failure": len(f_vals),
                              "hedges_g": float("nan"), "mann_whitney_p": float("nan")})
            continue
        stats = common.compute_group_stats(s_vals, f_vals, n_bootstrap, n_permutations, rng)
        rows_out.append({
            "excluded_stream": excl_conv,
            "layer": layer,
            "feature": "post_event_early_mean",
            "outcome": outcome_col,
            "n_success": len(s_vals),
            "n_failure": len(f_vals),
            "hedges_g": stats["hedges_g"],
            "mann_whitney_p": stats["mann_whitney_p"],
        })
    return rows_out


# ---------------------------------------------------------------------------
# Run directory setup
# ---------------------------------------------------------------------------

def make_run_dir(base_dir: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"run_{ts}"
    for sub in ("analysis", "plots/aggregate", "plots/per_example",
                "manifests", "logs"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    return run_dir


# ---------------------------------------------------------------------------
# Prompt-token-count lookup (not in analysis_dataset.csv; read from Stage 4)
# ---------------------------------------------------------------------------

def _get_prompt_token_counts(dataset_meta: list[dict]) -> dict[str, int]:
    """Read prompt_token_count from Stage 4 per-example JSONs."""
    result: dict[str, int] = {}
    for r in dataset_meta:
        eid = r["example_id"]
        # First try from analysis_dataset itself (field added in audit)
        v = r.get("prompt_token_count")
        if v:
            try:
                result[eid] = int(v)
                continue
            except (ValueError, TypeError):
                pass
        # Fallback: load per-example artifact
        try:
            artifact = common.load_stage4_per_example(eid)
            result[eid] = int(artifact.get("prompt_token_count", 0))
        except FileNotFoundError:
            result[eid] = 0
    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_analysis(
    run_dir: Path,
    review_dir: Path,
    seed: int = RANDOM_SEED,
    n_bootstrap: int = N_BOOTSTRAP,
    n_permutations: int = N_PERMUTATIONS,
    layers: list[int] = SELECTED_LAYERS,
    example_ids: set[str] | None = None,
    pilot_mode: bool = False,
) -> int:
    """Execute full event-aligned analysis. Returns exit code."""
    rng = np.random.default_rng(seed)

    # Load inputs
    dataset_meta = common.load_analysis_dataset()
    if example_ids is not None:
        dataset_meta = [r for r in dataset_meta if r["example_id"] in example_ids]
        print(f"Filtered to {len(dataset_meta)} examples from --example-ids-file.")
    annotations_path = review_dir / "harmful_interaction_annotations.csv"

    annotations: dict[str, dict] = {}
    if annotations_path.exists():
        for r in common.read_csv_as_list(annotations_path):
            eid = r.get("example_id")
            if eid:
                annotations[eid] = r
    else:
        print(f"WARNING: Annotations file not found: {annotations_path}", file=sys.stderr)

    # Annotation audit
    audit = audit_annotations(annotations, dataset_meta)
    common.atomic_write_json(run_dir / "analysis" / "harmful_interaction_annotation_audit.json",
                              common.make_json_safe(audit))
    if audit["has_errors"]:
        for err in audit["errors"]:
            print(f"ANNOTATION ERROR: {err}", file=sys.stderr)
        print("Annotation errors found; fix before proceeding.", file=sys.stderr)
        return 1

    n_annotated = audit["counts_by_status"].get("annotated", 0)
    print(f"Annotations: {n_annotated} annotated, {audit['n_unannotated']} unannotated")

    # Evaluator agreement summary
    eval_summary = build_evaluator_agreement_summary(dataset_meta)
    EVAL_FIELDS = ["example_id", "goal_index", "attack_iteration", "conversation_id",
                   "strongreject_score", "sr_success", "judge_score", "judge_success",
                   "evaluator_agreement_type"]
    common.write_csv(run_dir / "analysis" / "evaluator_agreement_summary.csv",
                      eval_summary, EVAL_FIELDS)
    counts_eval = {}
    for r in eval_summary:
        k = r["evaluator_agreement_type"]
        counts_eval[k] = counts_eval.get(k, 0) + 1
    common.atomic_write_json(run_dir / "analysis" / "evaluator_agreement_summary.json",
                              counts_eval)
    print(f"Evaluator agreement: {counts_eval}")

    if n_annotated < MIN_ANNOTATIONS:
        print(
            f"WARNING: Only {n_annotated} annotated examples (minimum is {MIN_ANNOTATIONS}). "
            "Writing partial outputs and exiting without model fitting.",
            file=sys.stderr,
        )
        # Write empty per-example CSV if no data
        common.write_csv(run_dir / "analysis" / "event_aligned_per_example.csv",
                          [], PER_EXAMPLE_FIELDS)
        if pilot_mode:
            _write_pilot_results(
                run_dir=run_dir,
                review_dir=review_dir,
                example_ids=example_ids,
                n_annotated=n_annotated,
            )
        _write_run_manifest(run_dir, review_dir, annotations_path, n_annotated,
                             n_bootstrap, n_permutations, seed)
        return 0

    # Build per-example feature dataset
    per_example_rows = build_per_example_dataset(annotations, dataset_meta, layers)
    print(f"Per-example features: {len(per_example_rows)} rows "
          f"({len(per_example_rows) // max(1, len(layers))} examples × {len(layers)} layers)")

    # Add prompt_token_count to rows (for Firth models)
    ptc_map = _get_prompt_token_counts(dataset_meta)
    for r in per_example_rows:
        r["prompt_token_count"] = ptc_map.get(r["example_id"], 0)

    common.write_csv(run_dir / "analysis" / "event_aligned_per_example.csv",
                      per_example_rows, PER_EXAMPLE_FIELDS)
    print(f"Written: event_aligned_per_example.csv")

    # Group statistics
    group_summary = compute_group_summary(per_example_rows, rng, n_bootstrap, n_permutations)
    common.write_csv(run_dir / "analysis" / "event_aligned_group_summary.csv",
                      group_summary, GROUP_SUMMARY_FIELDS)
    print(f"Written: event_aligned_group_summary.csv ({len(group_summary)} rows)")

    # Firth models (only if enough data)
    coef_rows: list[dict] = []
    model_summaries: list[dict] = []
    n_primary = sum(1 for r in per_example_rows
                     if int(r.get("layer", -1)) == PRIMARY_LAYER
                     and r.get("is_primary_analysis") is True)
    if n_primary >= MIN_ANNOTATIONS:
        coef_rows, model_summaries = fit_all_firth_models(per_example_rows)
        common.write_csv(run_dir / "analysis" / "event_aligned_firth_coefficients.csv",
                          coef_rows, FIRTH_COEF_FIELDS)
        print(f"Written: event_aligned_firth_coefficients.csv ({len(coef_rows)} rows)")
    else:
        print(f"WARNING: Only {n_primary} primary-analysis examples at layer {PRIMARY_LAYER}; "
              "skipping Firth models.", file=sys.stderr)

    # LOGO analysis
    logo_rows = run_logo_analysis(per_example_rows, PRIMARY_LAYER, rng, n_bootstrap, n_permutations)
    common.write_csv(run_dir / "analysis" / "leave_one_goal_out.csv", logo_rows, LOGO_FIELDS)
    print(f"Written: leave_one_goal_out.csv ({len(logo_rows)} rows)")

    # Stream sensitivity
    stream_rows = run_stream_sensitivity(per_example_rows, PRIMARY_LAYER, rng, n_bootstrap, n_permutations)
    common.write_csv(run_dir / "analysis" / "stream_sensitivity.csv", stream_rows, STREAM_FIELDS)
    print(f"Written: stream_sensitivity.csv ({len(stream_rows)} rows)")

    # Gemini sensitivity (pilot mode only)
    if pilot_mode and per_example_rows:
        gemini_summary = compute_group_summary(
            per_example_rows, rng, n_bootstrap, n_permutations,
            outcome_col="judge_success",
        )
        common.write_csv(
            run_dir / "analysis" / "event_aligned_group_summary_gemini_sensitivity.csv",
            gemini_summary, GROUP_SUMMARY_FIELDS,
        )
        print(f"Written: event_aligned_group_summary_gemini_sensitivity.csv "
              f"({len(gemini_summary)} rows)")

    # Full analysis JSON
    analysis_json = {
        "stage": "stage4_5",
        "artifact_version": "stage4_5_event_aligned_v1",
        "created_utc": common.utc_now(),
        "n_examples_total": 42,
        "n_annotated": n_annotated,
        "n_primary_analysis": n_primary,
        "primary_layer": PRIMARY_LAYER,
        "layers_analyzed": layers,
        "exploratory_layers": sorted(EXPLORATORY_LAYERS),
        "annotation_audit": audit,
        "evaluator_agreement_counts": counts_eval,
        "model_summaries": [common.make_json_safe(s) for s in model_summaries],
        "random_seed": seed,
        "n_bootstrap": n_bootstrap,
        "n_permutations": n_permutations,
    }
    if pilot_mode:
        analysis_json["analysis_scope"] = "pilot_exploratory_not_full_human_ground_truth"
        if example_ids is not None:
            analysis_json["n_pilot"] = len(example_ids)
    common.atomic_write_json(run_dir / "analysis" / "event_aligned_analysis.json",
                              common.make_json_safe(analysis_json))
    print(f"Written: event_aligned_analysis.json")

    # Pilot results document
    if pilot_mode:
        _write_pilot_results(
            run_dir=run_dir,
            review_dir=review_dir,
            example_ids=example_ids,
            n_annotated=n_annotated,
        )

    _write_run_manifest(run_dir, review_dir, annotations_path, n_annotated,
                         n_bootstrap, n_permutations, seed)
    print(f"\nAnalysis complete. Outputs in: {run_dir}")
    return 0


def _write_pilot_results(
    run_dir: Path,
    review_dir: Path,
    example_ids: set[str] | None,
    n_annotated: int,
) -> None:
    """Write pilot_results.json with required disclosures."""
    # Count completed human reviews
    progress_path = review_dir / "manual_adjudication_progress.csv"
    n_manual = 0
    if progress_path.exists():
        rows = common.read_csv_as_list(progress_path)
        pilot_ids = example_ids or set()
        n_manual = sum(
            1 for r in rows
            if r.get("review_status") == "completed"
            and (not pilot_ids or r.get("example_id") in pilot_ids)
        )

    # Load n_disagreements_included from selection manifest if available
    manifest_path = review_dir / "pilot_selection_manifest.json"
    n_disagree: int | str = "unknown"
    selection_rules_ref = str(manifest_path)
    if manifest_path.exists():
        import json as _json
        with open(manifest_path, encoding="utf-8") as f:
            m = _json.load(f)
        n_disagree = m.get("n_disagreements_included", "unknown")

    pilot_results = {
        "analysis_scope": "pilot_exploratory_not_full_human_ground_truth",
        "pilot_size": len(example_ids) if example_ids is not None else "all",
        "selection_rules_manifest": selection_rules_ref,
        "n_disagreements_included": n_disagree,
        "n_manual_labels_completed": n_manual,
        "n_event_annotations_completed": n_annotated,
        "primary_outcome": "sr_success",
        "sensitivity_outcome": "judge_success",
        "human_labels_used_as_outcome": False,
        "exploratory_disclaimer": (
            "Results are exploratory. Pilot size is N="
            + str(len(example_ids) if example_ids is not None else "?")
            + ". Cannot replace the full 42-example analysis with complete human ground truth. "
            "No causal claims are made. StrongREJECT is the primary outcome; "
            "Gemini judge is used as a sensitivity outcome only."
        ),
    }
    common.atomic_write_json(
        run_dir / "analysis" / "pilot_results.json",
        common.make_json_safe(pilot_results),
    )
    print(f"Written: analysis/pilot_results.json")


def _write_run_manifest(
    run_dir: Path,
    review_dir: Path,
    annotations_path: Path,
    n_annotated: int,
    n_bootstrap: int,
    n_permutations: int,
    seed: int,
) -> None:
    import subprocess
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=common.REPO_ROOT,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        git_commit = "unknown"

    manifest = {
        "stage": "stage4_5",
        "artifact_version": "stage4_5_run_manifest_v1",
        "created_utc": common.utc_now(),
        "run_dir": str(run_dir),
        "inputs": {
            "analysis_dataset_path": str(common.ANALYSIS_DATASET_PATH),
            "stage4_per_example_dir": str(common.STAGE4_PER_EXAMPLE_DIR),
            "stage6_traces_dir": str(common.STAGE6_TRACES_DIR),
            "review_dir": str(review_dir),
            "annotations_csv_path": str(annotations_path),
        },
        "outputs": {
            "analysis_dir": str(run_dir / "analysis"),
            "plots_dir": str(run_dir / "plots"),
        },
        "n_annotated": n_annotated,
        "random_seed": seed,
        "n_bootstrap": n_bootstrap,
        "n_permutations": n_permutations,
        "git_commit": git_commit,
        "contains_raw_text": False,
    }
    common.atomic_write_json(run_dir / "manifests" / "run_manifest.json", manifest)
    print(f"Written: manifests/run_manifest.json")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stage 4.5 event-aligned projection analysis.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Output run directory (default: auto-created with timestamp under "
             "outputs/stage4_5/harmful_interaction_alignment/).",
    )
    p.add_argument(
        "--review-dir",
        type=Path,
        default=common.DEFAULT_REVIEW_DIR,
    )
    p.add_argument("--seed", type=int, default=RANDOM_SEED)
    p.add_argument("--n-bootstrap", type=int, default=N_BOOTSTRAP)
    p.add_argument("--n-permutations", type=int, default=N_PERMUTATIONS)
    p.add_argument(
        "--layers",
        type=int,
        nargs="+",
        default=SELECTED_LAYERS,
        help="Layers to analyze.",
    )
    p.add_argument(
        "--example-ids-file",
        type=Path,
        default=None,
        help="CSV with example_id column; restrict analysis to these examples "
             "(e.g. review/pilot_example_queue.csv).",
    )
    p.add_argument(
        "--pilot-mode",
        action="store_true",
        default=False,
        help="Label outputs as pilot_exploratory_not_full_human_ground_truth and "
             "add Gemini sensitivity analysis.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.run_dir is None:
        run_dir = make_run_dir(common.DEFAULT_OUTPUT_BASE)
    else:
        run_dir = args.run_dir
        for sub in ("analysis", "plots/aggregate", "plots/per_example",
                    "manifests", "logs"):
            (run_dir / sub).mkdir(parents=True, exist_ok=True)

    # Resolve example IDs from file if provided
    example_ids: set[str] | None = None
    if args.example_ids_file is not None:
        rows = common.read_csv_as_list(args.example_ids_file)
        example_ids = {r["example_id"] for r in rows if r.get("example_id")}
        print(f"Loaded {len(example_ids)} example IDs from {args.example_ids_file}")

    print(f"Run directory: {run_dir}")
    return run_analysis(
        run_dir=run_dir,
        review_dir=args.review_dir,
        seed=args.seed,
        n_bootstrap=args.n_bootstrap,
        n_permutations=args.n_permutations,
        layers=args.layers,
        example_ids=example_ids,
        pilot_mode=args.pilot_mode,
    )


if __name__ == "__main__":
    sys.exit(main())
