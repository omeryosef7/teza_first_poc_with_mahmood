#!/usr/bin/env python3
"""
Phase 4 / 5: Confound-Controlled Modeling and Robustness Analysis

Tests whether the Layer-22 / first-500-token provisional projection remains
associated with sr_success after accounting for measured covariates:
  log1p(think_token_count), prompt_token_count (z-scored),
  goal_index (dummy coded, goal-0 reference), attack_iteration.

Fitting method: Firth (1993) penalized-likelihood logistic regression
(implemented in pure NumPy/SciPy; no external modeling packages required).
With n=41 and ~8 parameters, standard MLE risks infinite estimates due to
monotone likelihood; Firth's Jeffreys-prior penalty shrinks estimates toward
zero and guarantees finite estimates.

Statistical unit: the example (not individual tokens).
Primary binary outcome: sr_success = strongreject_score >= 0.5.
Primary projection feature: Layer-22 mean over the first 500 thinking tokens
(pre-specified in Phase 2; avoids post-hoc selection from Phase 3's 400 cells).

Outputs
-------
  analysis/confound_model_dataset.csv
  analysis/confound_model_coefficients.csv
  analysis/confound_model_metrics.csv
  analysis/confound_models.json
  analysis/confound_model_manifest.json
  plots_analysis_v2/confound_projection_adjusted_odds_ratio.png
  plots_analysis_v2/confound_model_comparison.png
  plots_analysis_v2/confound_projection_vs_think_length.png
  plots_analysis_v2/confound_partial_effect_projection.png
  plots_analysis_v2/confound_leave_one_goal_out.png

Usage
-----
  python -m poc_stage4.fit_confound_models \\
      --stage4-run-dir outputs/stage4/token_dynamics/full_20260604_101929 \\
      --analysis-dataset outputs/stage4/token_dynamics/full_20260604_101929/analysis/analysis_dataset.csv \\
      --fixed-window-csv  outputs/stage4/token_dynamics/full_20260604_101929/analysis/fixed_window_per_example.csv \\
      --normalized-csv    outputs/stage4/token_dynamics/full_20260604_101929/analysis/normalized_progress_per_example.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import scipy
from scipy.special import expit, logit
from scipy import stats as scipy_stats

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROVISIONAL_LAYER   = 22
WINDOW_500          = 500
ALPHA               = 0.05
RANDOM_SEED         = 42
N_BOOTSTRAP         = 2_000
N_PERMUTATIONS      = 10_000
GOAL_REF            = 0           # reference goal for dummy coding
SELECTED_SENS_LAYERS = [13, 16]   # exploratory alternative layers

COLOR_SUCCESS = "#0072B2"
COLOR_FAILURE = "#D55E00"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="python -m poc_stage4.fit_confound_models",
        description="Phase 4/5: Confound-Controlled Modeling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--stage4-run-dir", required=True)
    ap.add_argument("--analysis-dataset", required=True)
    ap.add_argument("--fixed-window-csv", required=True)
    ap.add_argument("--normalized-csv", required=True)
    ap.add_argument("--output-dir", default=None)
    ap.add_argument("--plots-dir", default=None)
    ap.add_argument("--seed", type=int, default=RANDOM_SEED)
    ap.add_argument("--n-bootstrap", type=int, default=N_BOOTSTRAP)
    ap.add_argument("--n-permutations", type=int, default=N_PERMUTATIONS)
    return ap.parse_args()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _bval(s: str) -> bool:
    return s == "True"


def load_analysis_dataset(path: str) -> list[dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["sr_success"]             = _bval(r["sr_success"])
        r["judge_success"]          = _bval(r["judge_success"])
        r["right_censored"]         = _bval(r["right_censored"])
        r["usable_for_think_analysis"] = _bval(r["usable_for_think_analysis"])
        r["strongreject_score"]     = float(r["strongreject_score"])
        r["think_token_count"]      = int(r["think_token_count"])
        r["prompt_token_count"]     = int(r["prompt_token_count"])
        r["goal_index"]             = int(r["goal_index"])
        r["attack_iteration"]       = int(r["attack_iteration"])
    return rows


def load_fixed_window_projections(
    path: str,
    window_size: int,
    layers: list[int],
) -> dict[str, dict[int, float]]:
    """Return {example_id: {layer: mean_projection}} for given window × layers."""
    proj: dict[str, dict[int, float]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if int(r["window_size"]) != window_size:
                continue
            li = int(r["layer"])
            if li not in layers:
                continue
            eid = r["example_id"]
            proj.setdefault(eid, {})[li] = float(r["mean_projection"])
    return proj


def load_normalized_bin0_projection(path: str, layer: int) -> dict[str, float]:
    """Return {example_id: mean_projection} for bin 0 at given layer."""
    proj: dict[str, float] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if int(r["progress_bin"]) != 0 or int(r["layer"]) != layer:
                continue
            proj[r["example_id"]] = float(r["mean_projection"])
    return proj


# ---------------------------------------------------------------------------
# Firth (1993) penalized-likelihood logistic regression
# ---------------------------------------------------------------------------
#
# Maximises L*(β) = L(β) + (1/2) log|X^T W X|  (Jeffreys-prior penalty)
# via penalised Newton–Raphson.
#
# Firth-adjusted score (Heinze & Schemper 2002, eq. 3):
#   U*(β) = X^T (y − μ) + X^T W h (0.5 − μ)
# where h = diag(H), H = W^{1/2} X (X^T W X)^{-1} X^T W^{1/2} is the hat
# matrix and μ = expit(X β).
#
# Update: β ← β + (X^T W X)^{-1} U*(β).
# Standard errors from observed Fisher information X^T W X at converged β.

def firth_fit(
    X: np.ndarray,
    y: np.ndarray,
    max_iter: int = 200,
    tol: float = 1e-9,
    ridge: float = 1e-8,
) -> dict[str, Any]:
    """
    Firth logistic regression.  X must include an intercept column.
    Returns dict: coef, se, fitted, log_lik, log_lik_penalized,
                  converged, n_iter, warning.
    """
    n, p = X.shape
    y = y.astype(np.float64)
    beta = np.zeros(p)
    converged = False
    warn = ""

    for it in range(max_iter):
        eta = X @ beta
        mu = expit(eta)
        mu_c = np.clip(mu, 1e-12, 1 - 1e-12)
        W = mu_c * (1.0 - mu_c)

        XW = X * W[:, None]                     # n × p
        I_mat = X.T @ XW + ridge * np.eye(p)   # Fisher information + tiny ridge
        try:
            I_inv = np.linalg.inv(I_mat)
        except np.linalg.LinAlgError:
            warn = "singular_information_matrix"
            break

        # Hat-matrix diagonal  h_i = W_i · x_i^T I^{-1} x_i
        temp = X @ I_inv          # n × p
        h = W * np.einsum("ij,ij->i", temp, X)  # n
        h = np.clip(h, 0.0, 1.0)

        # Firth score and Newton step
        score = X.T @ (y - mu_c + W * h * (0.5 - mu_c))
        delta = I_inv @ score
        beta = beta + delta

        if np.max(np.abs(delta)) < tol:
            converged = True
            break

    # Final quantities at converged beta
    mu_f = expit(X @ beta)
    mu_fc = np.clip(mu_f, 1e-12, 1 - 1e-12)
    W_f = mu_fc * (1.0 - mu_fc)
    I_f = X.T @ (X * W_f[:, None]) + ridge * np.eye(p)
    try:
        var_f = np.diag(np.linalg.inv(I_f))
        se = np.sqrt(np.maximum(var_f, 0.0))
    except np.linalg.LinAlgError:
        se = np.full(p, np.nan)
        warn = warn or "se_computation_failed"

    ll = float(np.sum(y * np.log(mu_fc) + (1.0 - y) * np.log(1.0 - mu_fc)))
    try:
        sign, logdet = np.linalg.slogdet(I_f)
        ll_pen = ll + 0.5 * (logdet if sign > 0 else 0.0)
    except Exception:
        ll_pen = ll

    if not converged and not warn:
        warn = f"max_iter_reached (n_iter={max_iter})"

    return {
        "coef":              beta,
        "se":                se,
        "fitted":            mu_f,
        "log_lik":           ll,
        "log_lik_penalized": ll_pen,
        "converged":         converged,
        "n_iter":            it + 1,
        "warning":           warn,
    }


# ---------------------------------------------------------------------------
# Design-matrix helpers
# ---------------------------------------------------------------------------

def _standardize_col(train_vals: np.ndarray, apply_vals: np.ndarray | None = None):
    """Return (z-scored train_vals, [z-scored apply_vals,] params_dict)."""
    m = float(np.mean(train_vals))
    s = float(np.std(train_vals, ddof=1))
    if s < 1e-12:
        s = 1.0
    z_train = (train_vals - m) / s
    if apply_vals is not None:
        z_apply = (apply_vals - m) / s
        return z_train, z_apply, {"mean": m, "std": s}
    return z_train, {"mean": m, "std": s}


def build_design_matrix(
    projection: np.ndarray,
    log_think: np.ndarray,
    prompt: np.ndarray,
    goal: np.ndarray,
    attack_iter: np.ndarray,
    features: list[str],
    std_params: dict[str, dict] | None = None,
    compute_std: bool = True,
) -> tuple[np.ndarray, list[str], dict[str, dict]]:
    """
    Build design matrix from raw feature vectors.

    features must be a subset of:
      ['intercept', 'projection_z', 'log_think', 'prompt_z',
       'goal_1', 'goal_2', 'goal_3', 'attack_iter']

    Returns (X, col_names, std_params_out).
    If compute_std=True, computes and returns standardization params.
    If compute_std=False, uses supplied std_params to apply existing params.
    """
    if std_params is None:
        std_params = {}
    std_out = dict(std_params)

    arrays: list[np.ndarray] = []
    col_names: list[str] = []

    for feat in features:
        if feat == "intercept":
            arrays.append(np.ones(len(projection)))
            col_names.append("intercept")
        elif feat == "projection_z":
            if compute_std:
                z, params = _standardize_col(projection)
                std_out["projection"] = params
            else:
                params = std_params["projection"]
                z = (projection - params["mean"]) / params["std"]
            arrays.append(z)
            col_names.append("projection_z")
        elif feat == "log_think":
            arrays.append(log_think.astype(np.float64))
            col_names.append("log_think")
        elif feat == "prompt_z":
            if compute_std:
                z, params = _standardize_col(prompt.astype(np.float64))
                std_out["prompt"] = params
            else:
                params = std_params["prompt"]
                z = (prompt.astype(np.float64) - params["mean"]) / params["std"]
            arrays.append(z)
            col_names.append("prompt_z")
        elif feat.startswith("goal_"):
            g = int(feat.split("_")[1])
            col = (goal == g).astype(np.float64)
            # Drop if all zeros (no examples from this goal in current subset)
            if col.sum() > 0 or not compute_std:
                arrays.append(col)
                col_names.append(feat)
        elif feat == "attack_iter":
            arrays.append(attack_iter.astype(np.float64))
            col_names.append("attack_iter")
        else:
            raise ValueError(f"Unknown feature: {feat!r}")

    return np.column_stack(arrays), col_names, std_out


MODEL_FEATURES = {
    "model0_covariates": [
        "intercept", "log_think", "prompt_z", "goal_1", "goal_2", "goal_3", "attack_iter"
    ],
    "model1_projection_only": [
        "intercept", "projection_z"
    ],
    "model2_primary": [
        "intercept", "projection_z", "log_think", "prompt_z",
        "goal_1", "goal_2", "goal_3", "attack_iter"
    ],
}


# ---------------------------------------------------------------------------
# Classification metrics
# ---------------------------------------------------------------------------

def _clip_prob(p: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    return np.clip(p, eps, 1.0 - eps)


def log_loss_fn(y: np.ndarray, p: np.ndarray) -> float:
    pc = _clip_prob(p)
    return float(-np.mean(y * np.log(pc) + (1.0 - y) * np.log(1.0 - pc)))


def brier_score_fn(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((y - p) ** 2))


def roc_auc_fn(y: np.ndarray, p: np.ndarray) -> float:
    """Area under ROC via Mann–Whitney U statistic."""
    pos = p[y == 1]
    neg = p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    diff = pos[:, None] - neg[None, :]      # n_pos × n_neg
    return float((np.sum(diff > 0) + 0.5 * np.sum(diff == 0)) / diff.size)


def balanced_accuracy_fn(y: np.ndarray, p: np.ndarray, thr: float = 0.5) -> float:
    yp = (p >= thr).astype(int)
    tp = np.sum((yp == 1) & (y == 1))
    tn = np.sum((yp == 0) & (y == 0))
    fp = np.sum((yp == 1) & (y == 0))
    fn = np.sum((yp == 0) & (y == 1))
    sens = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    return float((sens + spec) / 2.0)


def compute_metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    return {
        "log_loss":          log_loss_fn(y, p),
        "brier_score":       brier_score_fn(y, p),
        "roc_auc":           roc_auc_fn(y, p),
        "balanced_accuracy": balanced_accuracy_fn(y, p),
    }


# ---------------------------------------------------------------------------
# Leave-one-out evaluation
# ---------------------------------------------------------------------------

def loo_predict(
    raw: dict[str, np.ndarray],
    y: np.ndarray,
    features: list[str],
) -> np.ndarray:
    """
    Leave-one-out predicted probabilities.  Standardization parameters are
    re-estimated on each training fold (n−1 examples).

    Critical: the test design matrix uses the actual column names produced by
    the training build (some goal dummies may be dropped when a goal has no
    training examples in the current subset).  This ensures matching dimensions.
    """
    n = len(y)
    loo_probs = np.zeros(n)

    proj_raw  = raw["projection"]
    log_think = raw["log_think"]
    prompt    = raw["prompt"]
    goal      = raw["goal"]
    attack    = raw["attack_iter"]

    for i in range(n):
        tr = np.ones(n, dtype=bool)
        tr[i] = False

        X_tr, col_names_tr, std_p = build_design_matrix(
            proj_raw[tr], log_think[tr], prompt[tr], goal[tr], attack[tr],
            features, compute_std=True,
        )
        # Use col_names_tr (not the original features list) so that any goal
        # dummies that were dropped from training are also absent from the test
        # matrix, keeping dimensions consistent.
        X_te, _, _ = build_design_matrix(
            proj_raw[[i]], log_think[[i]], prompt[[i]], goal[[i]], attack[[i]],
            col_names_tr, std_params=std_p, compute_std=False,
        )

        res = firth_fit(X_tr, y[tr])
        p = float(expit(X_te @ res["coef"])[0])
        loo_probs[i] = p

    return loo_probs


# ---------------------------------------------------------------------------
# Spearman bootstrap CI
# ---------------------------------------------------------------------------

def spearman_bootstrap_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_boot: int,
    rng: np.random.Generator,
) -> tuple[float, float, float, float]:
    """Spearman rho with bootstrap 95% CI. Returns (rho, p, ci_low, ci_high)."""
    result = scipy_stats.spearmanr(x, y)
    rho = float(result.statistic)
    p_val = float(result.pvalue)
    n = len(x)
    boot_rhos: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        r = float(scipy_stats.spearmanr(x[idx], y[idx]).statistic)
        boot_rhos.append(r)
    boot_arr = np.array(boot_rhos)
    ci_lo = float(np.percentile(boot_arr, 100 * ALPHA / 2))
    ci_hi = float(np.percentile(boot_arr, 100 * (1 - ALPHA / 2)))
    return rho, p_val, ci_lo, ci_hi


# ---------------------------------------------------------------------------
# Within-goal permutation test
# ---------------------------------------------------------------------------

def within_goal_permute(
    y: np.ndarray,
    goal: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Permute sr_success within each goal group, preserving per-goal counts."""
    y_perm = np.empty_like(y)
    for g in np.unique(goal):
        mask = goal == g
        block = y[mask].copy()
        rng.shuffle(block)
        y_perm[mask] = block
    return y_perm


def permutation_test_projection(
    raw: dict[str, np.ndarray],
    y: np.ndarray,
    features: list[str],
    n_perm: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """
    Within-goal permutation test.  Test statistic: |projection_z coefficient|
    from Model 2 fitted on the full dataset.
    Returns observed coefficient, empirical p-value, null distribution.
    """
    # Fit observed
    X_obs, col_names, std_p = build_design_matrix(
        raw["projection"], raw["log_think"], raw["prompt"],
        raw["goal"], raw["attack_iter"],
        features, compute_std=True,
    )
    res_obs = firth_fit(X_obs, y)
    # Find projection_z column index
    if "projection_z" not in col_names:
        return {"error": "projection_z not in model features"}
    proj_idx = col_names.index("projection_z")
    obs_coef = float(res_obs["coef"][proj_idx])

    null_coefs: list[float] = []
    for _ in range(n_perm):
        y_perm = within_goal_permute(y, raw["goal"], rng)
        X_p, _, _ = build_design_matrix(
            raw["projection"], raw["log_think"], raw["prompt"],
            raw["goal"], raw["attack_iter"],
            features, std_params=std_p, compute_std=False,
        )
        res_p = firth_fit(X_p, y_perm)
        null_coefs.append(float(res_p["coef"][proj_idx]))

    null_arr = np.array(null_coefs)
    p_emp = float((np.sum(np.abs(null_arr) >= abs(obs_coef)) + 1) / (n_perm + 1))

    return {
        "observed_coef":  obs_coef,
        "p_empirical":    p_emp,
        "null_mean":      float(np.mean(null_arr)),
        "null_std":       float(np.std(null_arr, ddof=1)),
        "null_p025":      float(np.percentile(null_arr, 2.5)),
        "null_p975":      float(np.percentile(null_arr, 97.5)),
        "n_permutations": n_perm,
        "statistic":      "absolute_projection_z_coefficient",
    }


# ---------------------------------------------------------------------------
# Single-model fitting wrapper
# ---------------------------------------------------------------------------

def fit_model(
    raw: dict[str, np.ndarray],
    y: np.ndarray,
    features: list[str],
    col_labels: list[str] | None = None,
) -> dict[str, Any]:
    """
    Fit Firth logistic regression for one model specification.
    Returns full result dict including LOO predictions.
    """
    X, col_names, std_p = build_design_matrix(
        raw["projection"], raw["log_think"], raw["prompt"],
        raw["goal"], raw["attack_iter"],
        features, compute_std=True,
    )
    result = firth_fit(X, y)

    # Wald z-tests and p-values
    z_vals = result["coef"] / np.where(result["se"] > 1e-15, result["se"], np.nan)
    wald_p = 2.0 * (1.0 - scipy_stats.norm.cdf(np.abs(z_vals)))

    # 95% Wald CI on coefficient
    ci_low  = result["coef"] - 1.96 * result["se"]
    ci_high = result["coef"] + 1.96 * result["se"]

    # Exponentiated (clip large coefficients to avoid inf in OR; report as-is in JSON)
    _clip = lambda x: np.where(np.isfinite(x), np.exp(np.clip(x, -500, 500)), np.nan)

    # Training metrics
    train_metrics = compute_metrics(y, result["fitted"])

    # LOO
    loo_probs = loo_predict(raw, y, features)
    loo_metrics = compute_metrics(y, loo_probs)

    return {
        "coef":        result["coef"],
        "se":          result["se"],
        "wald_z":      z_vals,
        "wald_p":      wald_p,
        "ci_low":      ci_low,
        "ci_high":     ci_high,
        "or":          _clip(result["coef"]),
        "or_ci_low":   _clip(ci_low),
        "or_ci_high":  _clip(ci_high),
        "log_lik":     result["log_lik"],
        "log_lik_pen": result["log_lik_penalized"],
        "converged":   result["converged"],
        "n_iter":      result["n_iter"],
        "warning":     result["warning"],
        "col_names":   col_names,
        "std_params":  std_p,
        "train":       train_metrics,
        "loo":         loo_metrics,
        "loo_probs":   loo_probs,
        "n":           int(len(y)),
        "n_success":   int(y.sum()),
        "n_failure":   int((1 - y).sum()),
    }


# ---------------------------------------------------------------------------
# Build raw-feature dict from data frame rows
# ---------------------------------------------------------------------------

def build_raw_features(
    rows: list[dict[str, Any]],
    fw_proj: dict[str, dict[int, float]],
    b0_proj: dict[str, float],
    projection_layer: int = PROVISIONAL_LAYER,
    projection_window: int = WINDOW_500,
) -> dict[str, np.ndarray]:
    """Build per-column numpy arrays from the joined dataset rows."""
    # Validate that all rows have the required projection
    proj_vals, log_think_vals, prompt_vals = [], [], []
    proj_l13_vals, proj_l16_vals, proj_b0_vals = [], [], []
    goal_vals, attack_vals, sr_vals, sr_cont_vals = [], [], [], []
    right_censored_vals, example_ids = [], []

    for r in rows:
        eid = r["example_id"]
        fw = fw_proj.get(eid, {})
        proj_vals.append(fw.get(projection_layer, np.nan))
        proj_l13_vals.append(fw.get(13, np.nan))
        proj_l16_vals.append(fw.get(16, np.nan))
        proj_b0_vals.append(b0_proj.get(eid, np.nan))
        log_think_vals.append(math.log1p(r["think_token_count"]))
        prompt_vals.append(r["prompt_token_count"])
        goal_vals.append(r["goal_index"])
        attack_vals.append(r["attack_iteration"])
        sr_vals.append(int(r["sr_success"]))
        sr_cont_vals.append(r["strongreject_score"])
        right_censored_vals.append(int(r["right_censored"]))
        example_ids.append(eid)

    return {
        "projection":       np.array(proj_vals, dtype=np.float64),
        "projection_l13":   np.array(proj_l13_vals, dtype=np.float64),
        "projection_l16":   np.array(proj_l16_vals, dtype=np.float64),
        "projection_b0":    np.array(proj_b0_vals, dtype=np.float64),
        "log_think":        np.array(log_think_vals, dtype=np.float64),
        "prompt":           np.array(prompt_vals, dtype=np.float64),
        "goal":             np.array(goal_vals, dtype=np.int32),
        "attack_iter":      np.array(attack_vals, dtype=np.float64),
        "sr_success":       np.array(sr_vals, dtype=np.float64),
        "sr_score":         np.array(sr_cont_vals, dtype=np.float64),
        "right_censored":   np.array(right_censored_vals, dtype=np.int32),
        "example_id":       example_ids,
    }


def subset_raw(raw: dict[str, np.ndarray], mask: np.ndarray) -> dict[str, np.ndarray]:
    """Apply boolean mask to all arrays in raw."""
    out: dict[str, np.ndarray] = {}
    for k, v in raw.items():
        if isinstance(v, np.ndarray):
            out[k] = v[mask]
        elif isinstance(v, list):
            out[k] = [v[i] for i, m in enumerate(mask) if m]
        else:
            out[k] = v
    return out


# ---------------------------------------------------------------------------
# Coefficient table builder (for CSV output)
# ---------------------------------------------------------------------------

def _safe_exp(x: float) -> float:
    """Exponentiate, returning nan for non-finite input and inf for large values."""
    if math.isnan(x):
        return float("nan")
    return float(np.exp(min(x, 700.0)))


def coef_rows(
    model_name: str,
    subset: str,
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for j, col in enumerate(result["col_names"]):
        coef = float(result["coef"][j])
        se   = float(result["se"][j])
        rows.append({
            "model_name":         model_name,
            "subset":             subset,
            "predictor":          col,
            "coefficient":        coef,
            "standard_error":     se,
            "odds_ratio":         _safe_exp(coef),
            "ci_low":             _safe_exp(float(result["ci_low"][j])),
            "ci_high":            _safe_exp(float(result["ci_high"][j])),
            "wald_z":             float(result["wald_z"][j]),
            "p_value_wald":       float(result["wald_p"][j]),
            "convergence_status": result["converged"],
            "warning":            result["warning"] or "",
        })
    return rows


def metrics_rows(
    model_name: str,
    subset: str,
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    n, ns, nf = result["n"], result["n_success"], result["n_failure"]
    rows = []
    for split, met in [("train", result["train"]), ("loo", result["loo"])]:
        rows.append({
            "model_name":        model_name,
            "subset":            subset,
            "split":             split,
            "n_samples":         n,
            "n_events":          ns,
            "n_nonevents":       nf,
            "log_loss":          met["log_loss"],
            "brier_score":       met["brier_score"],
            "roc_auc":           met["roc_auc"],
            "balanced_accuracy": met["balanced_accuracy"],
        })
    return rows


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_odds_ratio_forest(
    models_for_plot: list[tuple[str, dict[str, Any]]],
    output_path: str,
) -> None:
    """
    Forest plot of projection-feature odds ratios and 95% Wald CIs
    for all model variants.
    """
    labels, ors, ci_los, ci_his = [], [], [], []
    for label, res in models_for_plot:
        cols = res["col_names"]
        if "projection_z" not in cols:
            continue
        j = cols.index("projection_z")
        labels.append(label)
        ors.append(float(np.exp(res["coef"][j])))
        ci_los.append(float(np.exp(res["ci_low"][j])))
        ci_his.append(float(np.exp(res["ci_high"][j])))

    n = len(labels)
    y_pos = np.arange(n)

    fig, ax = plt.subplots(figsize=(9, max(4, 0.55 * n + 1.5)))
    for i in range(n):
        ax.plot([ci_los[i], ci_his[i]], [i, i], color="#555555", linewidth=1.2, zorder=2)
        ax.scatter([ors[i]], [i], color=COLOR_SUCCESS, s=70, zorder=3)
    ax.axvline(1.0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Odds ratio for projection feature (per 1 SD; 95% Wald CI)")
    ax.set_title(
        "Projection-Feature Odds Ratios Across Model Variants\n"
        "(primary outcome: sr_success; projection = Layer-22 first-500 tokens unless noted)"
    )
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


def plot_model_comparison(
    model_results: list[tuple[str, dict[str, Any]]],
    output_path: str,
) -> None:
    """
    Compare Model 0, 1, 2 by LOO log loss, Brier score, AUC.
    Shows both train (lighter) and LOO (darker) values side-by-side.
    """
    metrics_list = ["log_loss", "brier_score", "roc_auc"]
    metric_labels = ["Log Loss", "Brier Score", "ROC AUC"]
    ncols = 3
    fig, axes = plt.subplots(1, ncols, figsize=(12, 4.5))

    model_labels = [label for label, _ in model_results]
    colors = ["#56B4E9", "#E69F00", "#CC79A7"]

    for ax, met, met_label in zip(axes, metrics_list, metric_labels):
        x = np.arange(len(model_results))
        width = 0.35
        for k, (label, res) in enumerate(model_results):
            t_val = res["train"].get(met, np.nan)
            l_val = res["loo"].get(met, np.nan)
            col = colors[k % len(colors)]
            ax.bar(k - width / 2, t_val, width, color=col, alpha=0.5, label=f"{label} (train)")
            ax.bar(k + width / 2, l_val, width, color=col, alpha=1.0, label=f"{label} (LOO)")

        ax.set_xticks(x)
        ax.set_xticklabels([f"M{i}" for i in range(len(model_results))], fontsize=9)
        ax.set_title(met_label, fontsize=10)
        ax.set_ylabel(met_label, fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    axes[0].legend(
        [mpatches.Patch(color=c, alpha=a) for c, a in zip(colors, [0.5] * 3 + [1.0] * 3)],
        [f"{label} train" for label, _ in model_results] +
        [f"{label} LOO"   for label, _ in model_results],
        fontsize=7, ncol=2,
    )
    fig.suptitle(
        "Model Comparison: Training vs. Leave-One-Out Metrics\n"
        "(M0=covariates only; M1=projection only; M2=primary adjusted; "
        "all subsets='all')",
        fontsize=9,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


def plot_projection_vs_think_length(
    raw: dict[str, np.ndarray],
    output_path: str,
) -> None:
    """Scatter: layer-22 first-500 projection vs log think-token count."""
    marker_map = {0: "o", 1: "s", 2: "^", 3: "D"}
    goal_labels = {0: "Goal 0", 1: "Goal 1", 2: "Goal 2", 3: "Goal 3"}
    success = raw["sr_success"].astype(bool)
    goals = raw["goal"]
    proj  = raw["projection"]
    lt    = raw["log_think"]

    fig, ax = plt.subplots(figsize=(8, 6))
    for g, marker in marker_map.items():
        for suc, color, label in [
            (True,  COLOR_SUCCESS, f"Success / {goal_labels[g]}"),
            (False, COLOR_FAILURE, f"Failure / {goal_labels[g]}"),
        ]:
            mask = success == suc & (goals == g)
            if mask.sum() == 0:
                continue
            ax.scatter(
                lt[mask], proj[mask],
                c=color, marker=marker, s=55, alpha=0.75,
                label=label if g == 0 else "_",
            )

    # Goal-unmarked legend
    ax.scatter([], [], c=COLOR_SUCCESS, marker="o", s=50, label="Success (any goal)")
    ax.scatter([], [], c=COLOR_FAILURE, marker="o", s=50, label="Failure (any goal)")
    for g, marker in marker_map.items():
        ax.scatter([], [], c="gray", marker=marker, s=50, label=goal_labels[g])

    # Regression lines per outcome
    for suc, color in [(True, COLOR_SUCCESS), (False, COLOR_FAILURE)]:
        mask = success == suc
        if mask.sum() >= 3:
            coefs = np.polyfit(lt[mask], proj[mask], 1)
            xr = np.linspace(lt[mask].min(), lt[mask].max(), 100)
            ax.plot(xr, np.polyval(coefs, xr), color=color, linewidth=1.2,
                    linestyle="--", alpha=0.7)

    # Pearson r annotation
    if len(proj) >= 3:
        r_s, p_s = scipy_stats.pearsonr(lt, proj)
        rsp, psp = scipy_stats.spearmanr(lt, proj)
        ax.text(0.03, 0.97,
                f"Pearson r={r_s:.2f} (p={p_s:.3f})\n"
                f"Spearman ρ={rsp:.2f} (p={psp:.3f})\n"
                f"n={len(proj)}",
                transform=ax.transAxes, fontsize=8, va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    ax.set_xlabel("log(1 + think_token_count)")
    ax.set_ylabel("Layer-22 first-500 mean projection")
    ax.set_title(
        "Projection Feature vs. Log Thinking Length\n"
        "(color=sr_success; marker=goal; dashed=within-outcome regression)"
    )
    ax.legend(fontsize=8, ncol=2, loc="upper right")
    ax.axhline(0, color="black", linewidth=0.4, alpha=0.4, linestyle=":")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


def plot_partial_effect(
    result: dict[str, Any],
    raw: dict[str, np.ndarray],
    output_path: str,
) -> None:
    """
    Predicted P(sr_success) vs standardized projection (Model 2, primary).
    All other covariates held at documented reference values.
    """
    col_names = result["col_names"]
    coefs = result["coef"]
    std_p = result["std_params"]

    # Compute reference values
    lt_ref = float(np.median(raw["log_think"]))      # median log think
    prompt_ref = 0.0                                  # mean (since prompt_z is standardized)
    attack_ref = 1.0                                  # attack_iteration = 1

    # Range for projection_z from observed data
    proj_std_mean = std_p["projection"]["mean"]
    proj_std_std  = std_p["projection"]["std"]
    proj_raw_min  = float(np.min(raw["projection"]))
    proj_raw_max  = float(np.max(raw["projection"]))
    proj_z_range  = np.linspace(
        (proj_raw_min - proj_std_mean) / proj_std_std - 0.5,
        (proj_raw_max - proj_std_mean) / proj_std_std + 0.5,
        200
    )

    # Build linear predictor at reference values
    def lp_at_ref(proj_z_val: float) -> float:
        lp = 0.0
        for j, col in enumerate(col_names):
            if col == "intercept":
                lp += coefs[j] * 1.0
            elif col == "projection_z":
                lp += coefs[j] * proj_z_val
            elif col == "log_think":
                lp += coefs[j] * lt_ref
            elif col == "prompt_z":
                lp += coefs[j] * prompt_ref
            elif col.startswith("goal_"):
                lp += coefs[j] * 0.0  # goal 0 reference
            elif col == "attack_iter":
                lp += coefs[j] * attack_ref
        return lp

    pred_p = np.array([float(expit(lp_at_ref(z))) for z in proj_z_range])

    # Compute confidence band via delta method (Wald)
    # d(prob)/d(beta_j) = prob(1-prob) * x_j
    # var(linear predictor) = x^T V x  where V = I^{-1}
    X_ref = np.zeros((len(proj_z_range), len(col_names)))
    for j, col in enumerate(col_names):
        if col == "intercept":
            X_ref[:, j] = 1.0
        elif col == "projection_z":
            X_ref[:, j] = proj_z_range
        elif col == "log_think":
            X_ref[:, j] = lt_ref
        elif col == "attack_iter":
            X_ref[:, j] = attack_ref
        # goal dummies stay 0 (reference group)

    # Var(eta) = X V X^T diagonal
    se_vals = result["se"]
    V = np.diag(se_vals ** 2)
    var_eta = np.einsum("ij,jk,ik->i", X_ref, V, X_ref)
    se_eta  = np.sqrt(np.maximum(var_eta, 0))
    pred_lo = expit(proj_z_range * coefs[col_names.index("projection_z")]
                    + sum(
                        coefs[j] * (1.0 if col == "intercept" else
                                    lt_ref if col == "log_think" else
                                    attack_ref if col == "attack_iter" else 0.0)
                        for j, col in enumerate(col_names)
                        if col != "projection_z"
                    )  # simplified, same as lp_at_ref but -1.96*se_eta
    )
    # Cleaner: use X_ref @ coef ± 1.96*se_eta
    lp_vec = X_ref @ coefs
    pred_lo_ci = expit(lp_vec - 1.96 * se_eta)
    pred_hi_ci = expit(lp_vec + 1.96 * se_eta)

    # Actual observations (coloured by outcome)
    proj_z_obs = (raw["projection"] - proj_std_mean) / proj_std_std
    success_mask = raw["sr_success"].astype(bool)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.fill_between(proj_z_range, pred_lo_ci, pred_hi_ci,
                    alpha=0.2, color="#888888", label="95% Wald CI (delta method)")
    ax.plot(proj_z_range, pred_p, color="#333333", linewidth=2,
            label="Fitted P(sr_success)")

    ax.scatter(proj_z_obs[success_mask], raw["sr_success"][success_mask],
               color=COLOR_SUCCESS, s=40, alpha=0.7, zorder=3, label="Success")
    ax.scatter(proj_z_obs[~success_mask], raw["sr_success"][~success_mask],
               color=COLOR_FAILURE, s=40, alpha=0.7, zorder=3, label="Failure")

    ax.axhline(0.5, color="gray", linewidth=0.5, linestyle=":", alpha=0.6)
    ax.axvline(0, color="gray", linewidth=0.5, linestyle=":", alpha=0.6)
    ax.set_xlabel("Projection feature (standardized, z-score)")
    ax.set_ylabel("Predicted P(sr_success)")
    ax.set_ylim(-0.05, 1.10)
    ax.set_title(
        "Partial Effect: Predicted Probability vs. Standardized Projection\n"
        "(Model 2 primary; all other covariates at reference values:\n"
        f"log_think=median={lt_ref:.2f}, prompt_z=0, goal=0, attack_iter=1)\n"
        "ASSOCIATIVE RELATIONSHIP — NOT CAUSAL",
        fontsize=9,
    )
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


def plot_leave_one_goal_out(
    logo_results: dict[int, dict[str, Any]],
    primary_result: dict[str, Any],
    output_path: str,
) -> None:
    """
    Forest plot: projection OR when each goal is excluded.
    Primary model (all goals) shown at top for reference.
    """
    labels, ors, ci_los, ci_his = [], [], [], []

    # Primary model
    cols = primary_result["col_names"]
    if "projection_z" in cols:
        j = cols.index("projection_z")
        labels.append("All goals (primary)")
        ors.append(float(np.exp(primary_result["coef"][j])))
        ci_los.append(float(np.exp(primary_result["ci_low"][j])))
        ci_his.append(float(np.exp(primary_result["ci_high"][j])))

    # LOO per goal
    for g in sorted(logo_results.keys()):
        res = logo_results[g]
        if "error" in res or "col_names" not in res:
            labels.append(f"Excl. goal {g} (failed)")
            ors.append(1.0)
            ci_los.append(float("nan"))
            ci_his.append(float("nan"))
            continue
        gcols = res["col_names"]
        if "projection_z" not in gcols:
            continue
        j = gcols.index("projection_z")
        labels.append(f"Excl. goal {g}")
        ors.append(float(np.exp(res["coef"][j])))
        ci_los.append(float(np.exp(res["ci_low"][j])))
        ci_his.append(float(np.exp(res["ci_high"][j])))

    n = len(labels)
    y_pos = np.arange(n)

    fig, ax = plt.subplots(figsize=(9, max(4, 0.6 * n + 1.5)))
    for i in range(n):
        if math.isnan(ci_los[i]):
            continue
        ax.plot([ci_los[i], ci_his[i]], [i, i], color="#555555", linewidth=1.5, zorder=2)
        color = COLOR_SUCCESS if i == 0 else "#888888"
        size  = 80 if i == 0 else 55
        ax.scatter([ors[i]], [i], color=color, s=size, zorder=3)

    ax.axvline(1.0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Projection OR per 1 SD (95% Wald CI)")
    ax.set_title(
        "Leave-One-Goal-Out Stability of Projection Effect\n"
        "(primary outcome: sr_success; primary model = Model 2)"
    )
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    rng  = np.random.default_rng(args.seed)

    s4_run    = Path(args.stage4_run_dir)
    out_dir   = Path(args.output_dir   or s4_run / "analysis")
    plots_dir = Path(args.plots_dir    or s4_run / "plots_analysis_v2")
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load inputs
    # ------------------------------------------------------------------
    print("[cm] Loading analysis dataset ...")
    dataset    = load_analysis_dataset(args.analysis_dataset)
    eligible   = [r for r in dataset if r["usable_for_think_analysis"]]
    print(f"[cm] Eligible for think analysis: {len(eligible)}")

    print("[cm] Loading fixed-window projections (layers 13, 16, 22 / window 500) ...")
    fw_proj = load_fixed_window_projections(
        args.fixed_window_csv, WINDOW_500, [13, 16, PROVISIONAL_LAYER]
    )

    print("[cm] Loading normalized-progress bin-0 projection (layer 22) ...")
    b0_proj = load_normalized_bin0_projection(args.normalized_csv, PROVISIONAL_LAYER)

    # ------------------------------------------------------------------
    # Build raw feature arrays
    # ------------------------------------------------------------------
    print("[cm] Building raw feature arrays ...")
    raw_all = build_raw_features(eligible, fw_proj, b0_proj)

    # Validate no NaN in primary projection or key features
    proj_nan = np.isnan(raw_all["projection"])
    if proj_nan.any():
        bad = [raw_all["example_id"][i] for i in np.where(proj_nan)[0]]
        print(f"[cm] WARNING: {proj_nan.sum()} examples missing layer-22/500 projection: {bad}",
              file=sys.stderr)

    y_all = raw_all["sr_success"]
    print(f"[cm] n={len(y_all)}  n_success={int(y_all.sum())}  n_failure={int((1-y_all).sum())}")

    # excl_censored subset
    not_censored = raw_all["right_censored"] == 0
    raw_excl = subset_raw(raw_all, not_censored)
    y_excl   = raw_excl["sr_success"]

    # ------------------------------------------------------------------
    # Correlation / covariate analysis
    # ------------------------------------------------------------------
    print("\n[cm] --- Covariate analysis ---")
    cont_features = {
        "projection_l22_500":       raw_all["projection"],
        "log1p_think_token_count":  raw_all["log_think"],
        "prompt_token_count":       raw_all["prompt"],
        "attack_iteration":         raw_all["attack_iter"],
    }
    feat_names = list(cont_features.keys())
    feat_vecs  = [cont_features[k] for k in feat_names]
    print("  Spearman correlation matrix:")
    print(f"  {'':30s} " + "  ".join(f"{n:14s}" for n in feat_names))
    for i, ni in enumerate(feat_names):
        row_str = f"  {ni:30s}"
        for j, nj in enumerate(feat_names):
            r, _ = scipy_stats.spearmanr(feat_vecs[i], feat_vecs[j])
            row_str += f"  {r:+.3f}         "
        print(row_str)

    # Projection vs think length
    r_proj_lt, p_proj_lt = scipy_stats.spearmanr(
        raw_all["projection"], raw_all["log_think"]
    )
    print(f"\n  Projection vs log_think: Spearman ρ={r_proj_lt:.3f} (p={p_proj_lt:.4f})")
    print(f"  Projection vs prompt:    Spearman ρ="
          f"{scipy_stats.spearmanr(raw_all['projection'], raw_all['prompt']).statistic:.3f}")
    print(f"  Projection vs attack:    Spearman ρ="
          f"{scipy_stats.spearmanr(raw_all['projection'], raw_all['attack_iter']).statistic:.3f}")

    # Goal-stratified projection stats
    print("\n  Layer-22/500 projection by goal (mean ± SD, n, n_success):")
    for g in sorted(np.unique(raw_all["goal"])):
        gm = raw_all["goal"] == g
        ps = raw_all["projection"][gm]
        ns = int(y_all[gm].sum())
        print(f"    Goal {g}: mean={np.mean(ps):+.3f}  SD={np.std(ps, ddof=1):.3f}"
              f"  n={int(gm.sum())}  n_success={ns}")

    # ------------------------------------------------------------------
    # Fit primary models (all subset)
    # ------------------------------------------------------------------
    print("\n[cm] --- Fitting primary models (subset='all') ---")
    results: dict[str, dict[str, Any]] = {}

    for mname, feats in MODEL_FEATURES.items():
        print(f"  Fitting {mname} ...")
        results[mname] = fit_model(raw_all, y_all, feats)
        r = results[mname]
        print(f"    converged={r['converged']}  n_iter={r['n_iter']}"
              f"  warning={r['warning']!r}")
        print(f"    LOO: log_loss={r['loo']['log_loss']:.4f}  "
              f"brier={r['loo']['brier_score']:.4f}  "
              f"auc={r['loo']['roc_auc']:.4f}")
        if "projection_z" in r["col_names"]:
            j = r["col_names"].index("projection_z")
            print(f"    projection_z: coef={r['coef'][j]:+.4f}  "
                  f"OR={np.exp(r['coef'][j]):.3f}  "
                  f"[{np.exp(r['ci_low'][j]):.3f}, {np.exp(r['ci_high'][j]):.3f}]  "
                  f"p={r['wald_p'][j]:.4f}")

    # ------------------------------------------------------------------
    # Sensitivity A: excl_censored
    # ------------------------------------------------------------------
    print("\n[cm] --- Sensitivity A: exclude right-censored (n="
          f"{int(not_censored.sum())}) ---")
    results_excl: dict[str, dict[str, Any]] = {}
    for mname, feats in MODEL_FEATURES.items():
        print(f"  Fitting {mname} [excl_censored] ...")
        results_excl[mname] = fit_model(raw_excl, y_excl, feats)
        r = results_excl[mname]
        print(f"    converged={r['converged']}  warning={r['warning']!r}")
        if "projection_z" in r["col_names"]:
            j = r["col_names"].index("projection_z")
            print(f"    projection_z: coef={r['coef'][j]:+.4f}  "
                  f"OR={np.exp(r['coef'][j]):.3f}  "
                  f"[{np.exp(r['ci_low'][j]):.3f}, {np.exp(r['ci_high'][j]):.3f}]")

    # ------------------------------------------------------------------
    # Sensitivity B: normalized bin-0 feature
    # ------------------------------------------------------------------
    print("\n[cm] --- Sensitivity B: bin-0 projection feature ---")
    raw_b0 = dict(raw_all)
    raw_b0 = {**raw_all, "projection": raw_all["projection_b0"]}
    feats_b0 = MODEL_FEATURES["model2_primary"]
    results["model2_bin0"] = fit_model(raw_b0, y_all, feats_b0)
    r = results["model2_bin0"]
    print(f"  converged={r['converged']}  warning={r['warning']!r}")
    if "projection_z" in r["col_names"]:
        j = r["col_names"].index("projection_z")
        print(f"  projection_z (bin-0): coef={r['coef'][j]:+.4f}  "
              f"OR={np.exp(r['coef'][j]):.3f}  "
              f"[{np.exp(r['ci_low'][j]):.3f}, {np.exp(r['ci_high'][j]):.3f}]")

    # ------------------------------------------------------------------
    # Sensitivity C: exploratory layers 13 and 16
    # ------------------------------------------------------------------
    print("\n[cm] --- Sensitivity C: exploratory layers ---")
    feats_adj = MODEL_FEATURES["model2_primary"]
    for sens_layer, proj_key in [(13, "projection_l13"), (16, "projection_l16")]:
        raw_l = {**raw_all, "projection": raw_all[proj_key]}
        key = f"model2_layer{sens_layer}"
        print(f"  Fitting {key} ...")
        results[key] = fit_model(raw_l, y_all, feats_adj)
        r = results[key]
        print(f"  converged={r['converged']}  warning={r['warning']!r}")
        if "projection_z" in r["col_names"]:
            j = r["col_names"].index("projection_z")
            print(f"  projection_z (layer {sens_layer}): coef={r['coef'][j]:+.4f}  "
                  f"OR={np.exp(r['coef'][j]):.3f}  "
                  f"[{np.exp(r['ci_low'][j]):.3f}, {np.exp(r['ci_high'][j]):.3f}]")

    # ------------------------------------------------------------------
    # Sensitivity D: leave-one-goal-out
    # ------------------------------------------------------------------
    print("\n[cm] --- Sensitivity D: leave-one-goal-out ---")
    logo_results: dict[int, dict[str, Any]] = {}
    goal_vals = raw_all["goal"]
    feats_m2  = MODEL_FEATURES["model2_primary"]
    for g in sorted(np.unique(goal_vals)):
        keep = goal_vals != g
        raw_g = subset_raw(raw_all, keep)
        y_g   = raw_g["sr_success"]
        if int(y_g.sum()) == 0 or int((1 - y_g).sum()) == 0:
            logo_results[int(g)] = {"error": "no variation in outcome after goal removal"}
            print(f"  Goal {g}: skipped (no variation)")
            continue
        print(f"  Excluding goal {g} (n={int(keep.sum())}, "
              f"n_success={int(y_g.sum())}) ...")
        logo_results[int(g)] = fit_model(raw_g, y_g, feats_m2)
        r = logo_results[int(g)]
        print(f"    converged={r['converged']}  warning={r['warning']!r}")
        if "projection_z" in r["col_names"]:
            j = r["col_names"].index("projection_z")
            print(f"    projection_z: coef={r['coef'][j]:+.4f}  "
                  f"OR={np.exp(r['coef'][j]):.3f}  "
                  f"[{np.exp(r['ci_low'][j]):.3f}, {np.exp(r['ci_high'][j]):.3f}]")

    # ------------------------------------------------------------------
    # Sensitivity E: within-goal permutation test
    # ------------------------------------------------------------------
    print(f"\n[cm] --- Sensitivity E: within-goal permutation "
          f"(n_perm={args.n_permutations}) ---")
    perm_result = permutation_test_projection(
        raw_all, y_all, feats_m2, args.n_permutations, rng
    )
    print(f"  Observed |coef|: {abs(perm_result['observed_coef']):.4f}")
    print(f"  Empirical p-value: {perm_result['p_empirical']:.4f}")
    print(f"  Null 2.5%–97.5%: [{perm_result['null_p025']:.4f}, {perm_result['null_p975']:.4f}]")

    # ------------------------------------------------------------------
    # Spearman correlation with continuous StrongREJECT score
    # ------------------------------------------------------------------
    print("\n[cm] --- Continuous StrongREJECT analysis ---")
    proj_z_all, std_p_all = _standardize_col(raw_all["projection"])
    rho_s, p_s, ci_lo_s, ci_hi_s = spearman_bootstrap_ci(
        proj_z_all, raw_all["sr_score"], args.n_bootstrap, rng
    )
    print(f"  Spearman ρ (projection_z vs SR score): {rho_s:.3f} "
          f"(p={p_s:.4f})  95% bootstrap CI: [{ci_lo_s:.3f}, {ci_hi_s:.3f}]")
    print(f"  Note: SR scores are highly discrete (many tied); "
          f"interpret cautiously.")

    # Partial Spearman (residualize both on covariates)
    X_cov_all, _, _ = build_design_matrix(
        raw_all["projection"], raw_all["log_think"], raw_all["prompt"],
        raw_all["goal"], raw_all["attack_iter"],
        ["intercept", "log_think", "prompt_z", "goal_1", "goal_2", "goal_3", "attack_iter"],
        compute_std=True,
    )
    # OLS residuals
    coef_ols_proj, _, _, _ = np.linalg.lstsq(X_cov_all, proj_z_all, rcond=None)
    resid_proj = proj_z_all - X_cov_all @ coef_ols_proj
    coef_ols_sr, _, _, _ = np.linalg.lstsq(X_cov_all, raw_all["sr_score"], rcond=None)
    resid_sr   = raw_all["sr_score"] - X_cov_all @ coef_ols_sr
    rho_partial, p_partial = scipy_stats.spearmanr(resid_proj, resid_sr)
    print(f"  Partial Spearman ρ (after OLS residualisation on covariates): "
          f"{rho_partial:.3f} (p={p_partial:.4f})")

    # ------------------------------------------------------------------
    # Build confound_model_dataset.csv
    # ------------------------------------------------------------------
    print("\n[cm] Writing confound_model_dataset.csv ...")
    X_m2_all, col_m2, std_m2 = build_design_matrix(
        raw_all["projection"], raw_all["log_think"], raw_all["prompt"],
        raw_all["goal"], raw_all["attack_iter"],
        MODEL_FEATURES["model2_primary"], compute_std=True,
    )
    dataset_rows = []
    for i, eid in enumerate(raw_all["example_id"]):
        row: dict[str, Any] = {
            "example_id":                    eid,
            "sr_success":                    int(raw_all["sr_success"][i]),
            "strongreject_score":            raw_all["sr_score"][i],
            "judge_success":                 eligible[i]["judge_success"],
            "right_censored":                int(raw_all["right_censored"][i]),
            "goal_index":                    int(raw_all["goal"][i]),
            "attack_iteration":              int(raw_all["attack_iter"][i]),
            "think_token_count":             eligible[i]["think_token_count"],
            "prompt_token_count":            int(raw_all["prompt"][i]),
            "layer22_first500_projection":   raw_all["projection"][i],
            "layer13_first500_projection":   raw_all["projection_l13"][i],
            "layer16_first500_projection":   raw_all["projection_l16"][i],
            "layer22_bin0_projection":       raw_all["projection_b0"][i],
            "log_think":                     raw_all["log_think"][i],
            "projection_z":                  (raw_all["projection"][i] - std_m2["projection"]["mean"])
                                              / std_m2["projection"]["std"],
            "prompt_z":                      (raw_all["prompt"][i] - std_m2["prompt"]["mean"])
                                              / std_m2["prompt"]["std"],
            "m2_loo_predicted_prob":         results["model2_primary"]["loo_probs"][i],
            "m0_loo_predicted_prob":         results["model0_covariates"]["loo_probs"][i],
        }
        dataset_rows.append(row)

    ds_path = out_dir / "confound_model_dataset.csv"
    with open(ds_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(dataset_rows[0].keys()))
        w.writeheader()
        w.writerows(dataset_rows)
    print(f"[cm] Wrote {ds_path}  ({len(dataset_rows)} rows)")

    # Validate: layer-22/500 values match fixed_window_per_example.csv
    mismatch = 0
    for r in dataset_rows:
        eid  = r["example_id"]
        expected = fw_proj.get(eid, {}).get(PROVISIONAL_LAYER)
        if expected is not None and abs(r["layer22_first500_projection"] - expected) > 1e-8:
            mismatch += 1
    if mismatch:
        print(f"[cm] WARNING: {mismatch} layer-22/500 projection mismatches!", file=sys.stderr)
    else:
        print(f"[cm] Validation: layer-22/500 projection matches fixed_window_per_example.csv ✓")

    # ------------------------------------------------------------------
    # Write confound_model_coefficients.csv
    # ------------------------------------------------------------------
    print("[cm] Writing confound_model_coefficients.csv ...")
    coef_list: list[dict[str, Any]] = []

    for mname, feats in MODEL_FEATURES.items():
        coef_list.extend(coef_rows(mname,           "all",           results[mname]))
        coef_list.extend(coef_rows(mname + "_excl", "excl_censored", results_excl[mname]))

    coef_list.extend(coef_rows("model2_bin0",     "all", results["model2_bin0"]))
    coef_list.extend(coef_rows("model2_layer13",  "all", results["model2_layer13"]))
    coef_list.extend(coef_rows("model2_layer16",  "all", results["model2_layer16"]))
    for g, res_g in logo_results.items():
        if "col_names" in res_g:
            coef_list.extend(coef_rows(f"model2_excl_goal{g}", f"excl_goal{g}", res_g))

    coef_path = out_dir / "confound_model_coefficients.csv"
    with open(coef_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(coef_list[0].keys()))
        w.writeheader()
        w.writerows(coef_list)
    print(f"[cm] Wrote {coef_path}  ({len(coef_list)} rows)")

    # ------------------------------------------------------------------
    # Write confound_model_metrics.csv
    # ------------------------------------------------------------------
    print("[cm] Writing confound_model_metrics.csv ...")
    met_list: list[dict[str, Any]] = []
    for mname in MODEL_FEATURES:
        met_list.extend(metrics_rows(mname,           "all",           results[mname]))
        met_list.extend(metrics_rows(mname + "_excl", "excl_censored", results_excl[mname]))
    met_list.extend(metrics_rows("model2_bin0",    "all", results["model2_bin0"]))
    met_list.extend(metrics_rows("model2_layer13", "all", results["model2_layer13"]))
    met_list.extend(metrics_rows("model2_layer16", "all", results["model2_layer16"]))

    met_path = out_dir / "confound_model_metrics.csv"
    with open(met_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(met_list[0].keys()))
        w.writeheader()
        w.writerows(met_list)
    print(f"[cm] Wrote {met_path}  ({len(met_list)} rows)")

    # ------------------------------------------------------------------
    # Build confound_models.json
    # ------------------------------------------------------------------

    def _serialise(x: Any) -> Any:
        if isinstance(x, np.ndarray):
            return [round(float(v), 6) for v in x]
        if isinstance(x, np.bool_):
            return bool(x)
        if isinstance(x, (np.integer,)):
            return int(x)
        if isinstance(x, (np.floating,)):
            return None if math.isnan(float(x)) else round(float(x), 6)
        if isinstance(x, dict):
            return {k: _serialise(v) for k, v in x.items()}
        if isinstance(x, list):
            return [_serialise(v) for v in x]
        return x

    def _coef_summary(res: dict, label: str) -> dict:
        out: dict[str, Any] = {
            "label":       label,
            "n":           res["n"],
            "n_success":   res["n_success"],
            "n_failure":   res["n_failure"],
            "converged":   res["converged"],
            "n_iter":      res["n_iter"],
            "warning":     res["warning"],
            "log_lik":     round(res["log_lik"], 4),
            "log_lik_pen": round(res["log_lik_pen"], 4),
            "train":       {k: round(v, 4) for k, v in res["train"].items()},
            "loo":         {k: round(v, 4) for k, v in res["loo"].items()},
            "coefficients": {},
        }
        for j, col in enumerate(res["col_names"]):
            out["coefficients"][col] = {
                "coef":       round(float(res["coef"][j]), 4),
                "se":         round(float(res["se"][j]), 4),
                "OR":         round(_safe_exp(float(res["coef"][j])), 4),
                "or_ci_low":  round(_safe_exp(float(res["ci_low"][j])), 4),
                "or_ci_high": round(_safe_exp(float(res["ci_high"][j])), 4),
                "wald_p":     round(float(res["wald_p"][j]), 4),
            }
        return out

    models_json: dict[str, Any] = {
        "artifact_version": "confound_models_v1",
        "fitting_method": (
            "Firth (1993) penalized-likelihood logistic regression "
            "(pure NumPy/SciPy implementation; Jeffreys-prior penalty; "
            "standard errors from observed Fisher information at converged estimate; "
            "CIs are Wald 95%; p-values are two-sided Wald z-tests)"
        ),
        "primary_predictor": (
            f"layer-{PROVISIONAL_LAYER} mean projection over first {WINDOW_500} thinking tokens "
            "(standardized to z-score within each fitted subset)"
        ),
        "standardization": {
            "projection": std_m2.get("projection"),
            "prompt":     std_m2.get("prompt"),
        },
        "models": {
            mname: _coef_summary(results[mname], mname)
            for mname in list(MODEL_FEATURES.keys()) + ["model2_bin0", "model2_layer13", "model2_layer16"]
        },
        "sensitivity_a_excl_censored": {
            mname: _coef_summary(results_excl[mname], mname + "_excl_censored")
            for mname in MODEL_FEATURES
        },
        "sensitivity_d_leave_one_goal_out": {
            str(g): _coef_summary(res, f"excl_goal_{g}") if "col_names" in res else res
            for g, res in logo_results.items()
        },
        "sensitivity_e_permutation_test": perm_result,
        "spearman_continuous": {
            "projection_z_vs_sr_score": {
                "rho":    round(rho_s, 3),
                "p":      round(p_s, 4),
                "ci_low": round(ci_lo_s, 3),
                "ci_high":round(ci_hi_s, 3),
                "note":   "SR scores are highly discrete; bootstrap CI uses percentile method",
            },
            "partial_spearman_after_ols_residualization": {
                "rho": round(float(rho_partial), 3),
                "p":   round(float(p_partial), 4),
            },
        },
        "model_comparison_loo": {
            mname: {
                "log_loss":    round(results[mname]["loo"]["log_loss"], 4),
                "brier_score": round(results[mname]["loo"]["brier_score"], 4),
                "roc_auc":     round(results[mname]["loo"]["roc_auc"], 4),
            }
            for mname in MODEL_FEATURES
        },
        "warnings": [
            "With n=41 and up to 8 parameters, events-per-variable is ~2.4; "
            "Firth penalty mitigates but does not eliminate estimation uncertainty.",
            "All LOO metrics with n≈41 must be treated as exploratory.",
            "CIs are asymptotic Wald; profile-likelihood CIs would be more accurate for small n.",
            "The provisional direction is diagnostic only; causal claims are not supported.",
        ],
        "interpretation_note": (
            "If Model-2 projection coefficient is large and stable across sensitivities: "
            "supports early representational divergence associated with outcome. "
            "If strongly attenuated after covariates: indicates confounding. "
            "Cannot establish causation, refusal-signal validity, or gradual dilution mechanism."
        ),
    }
    cm_json_path = out_dir / "confound_models.json"
    with open(cm_json_path, "w", encoding="utf-8") as f:
        json.dump(_serialise(models_json), f, indent=2)
    print(f"[cm] Wrote {cm_json_path}")

    # ------------------------------------------------------------------
    # Manifest
    # ------------------------------------------------------------------
    manifest = {
        "artifact_version": "confound_model_manifest_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "stage4_run_directory": str(s4_run),
        "inputs": {
            "analysis_dataset":    str(args.analysis_dataset),
            "fixed_window_csv":    str(args.fixed_window_csv),
            "normalized_csv":      str(args.normalized_csv),
        },
        "primary_predictor": f"layer-{PROVISIONAL_LAYER}, window={WINDOW_500}, mean_projection",
        "primary_outcome":   "sr_success = strongreject_score >= 0.5",
        "fitting_method":    "Firth (1993) penalized logistic regression",
        "n_bootstrap":       args.n_bootstrap,
        "n_permutations":    args.n_permutations,
        "random_seed":       args.seed,
        "package_versions": {
            "python":     sys.version.split()[0],
            "numpy":      np.__version__,
            "scipy":      scipy.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "outputs": {
            "confound_model_dataset_csv":    str(ds_path),
            "confound_model_coefficients_csv": str(coef_path),
            "confound_model_metrics_csv":    str(met_path),
            "confound_models_json":          str(cm_json_path),
        },
    }
    mf_path = out_dir / "confound_model_manifest.json"
    with open(mf_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[cm] Wrote {mf_path}")

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    print("\n[cm] Generating plots ...")

    # Plot 1: Forest plot of ORs
    forest_models = [
        ("Model 2 (primary, all)",            results["model2_primary"]),
        ("Model 2 (excl. censored)",           results_excl["model2_primary"]),
        ("Sens. B: normalized bin-0",          results["model2_bin0"]),
        ("Sens. C: layer 13 (exploratory)",    results["model2_layer13"]),
        ("Sens. C: layer 16 (exploratory)",    results["model2_layer16"]),
    ]
    for g in sorted(logo_results.keys()):
        if "col_names" in logo_results[g]:
            forest_models.append(
                (f"LOO goal {g} (Sens. D)", logo_results[g])
            )
    plot_odds_ratio_forest(
        forest_models,
        str(plots_dir / "confound_projection_adjusted_odds_ratio.png"),
    )

    # Plot 2: Model comparison
    plot_model_comparison(
        [
            ("M0 covariates", results["model0_covariates"]),
            ("M1 projection", results["model1_projection_only"]),
            ("M2 primary",    results["model2_primary"]),
        ],
        str(plots_dir / "confound_model_comparison.png"),
    )

    # Plot 3: Projection vs think length
    plot_projection_vs_think_length(
        raw_all,
        str(plots_dir / "confound_projection_vs_think_length.png"),
    )

    # Plot 4: Partial effect
    plot_partial_effect(
        results["model2_primary"],
        raw_all,
        str(plots_dir / "confound_partial_effect_projection.png"),
    )

    # Plot 5: Leave-one-goal-out
    plot_leave_one_goal_out(
        logo_results,
        results["model2_primary"],
        str(plots_dir / "confound_leave_one_goal_out.png"),
    )

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------
    print()
    print("=" * 72)
    print("  CONFOUND-MODEL ANALYSIS SUMMARY")
    print("=" * 72)
    print(f"  Fitting method: Firth penalized logistic regression (NumPy/SciPy)")
    print(f"  Primary predictor: Layer-{PROVISIONAL_LAYER} / first-{WINDOW_500} tokens / z-scored")
    print()

    # Primary model coefficients summary
    r2 = results["model2_primary"]
    cols2 = r2["col_names"]
    print("  Model 2 (primary adjusted, subset='all'):")
    print(f"    n={r2['n']}  n_success={r2['n_success']}  n_failure={r2['n_failure']}")
    print(f"    converged={r2['converged']}  n_iter={r2['n_iter']}  warning={r2['warning']!r}")
    for j, col in enumerate(cols2):
        coef = float(r2["coef"][j])
        se   = float(r2["se"][j])
        OR   = float(np.exp(coef))
        ci_lo = float(np.exp(r2["ci_low"][j]))
        ci_hi = float(np.exp(r2["ci_high"][j]))
        pw    = float(r2["wald_p"][j])
        mark  = " *" if pw < ALPHA and col == "projection_z" else ""
        print(f"    {col:20s}: coef={coef:+.4f}  SE={se:.4f}  "
              f"OR={OR:.3f} [{ci_lo:.3f}, {ci_hi:.3f}]  p={pw:.4f}{mark}")
    print()

    # Model comparison
    print("  LOO metric comparison (exploratory with n=41):")
    for mname in MODEL_FEATURES:
        r = results[mname]
        lo = r["loo"]
        print(f"    {mname:35s}: "
              f"log_loss={lo['log_loss']:.4f}  "
              f"brier={lo['brier_score']:.4f}  "
              f"AUC={lo['roc_auc']:.4f}")
    print()

    # LOO difference
    ll_m0 = results["model0_covariates"]["loo"]["log_loss"]
    ll_m2 = results["model2_primary"]["loo"]["log_loss"]
    bs_m0 = results["model0_covariates"]["loo"]["brier_score"]
    bs_m2 = results["model2_primary"]["loo"]["brier_score"]
    au_m0 = results["model0_covariates"]["loo"]["roc_auc"]
    au_m2 = results["model2_primary"]["loo"]["roc_auc"]
    print(f"  Model 0 → Model 2 LOO changes:")
    print(f"    Δ log_loss  = {ll_m2 - ll_m0:+.4f} (negative = improvement)")
    print(f"    Δ brier     = {bs_m2 - bs_m0:+.4f} (negative = improvement)")
    print(f"    Δ AUC       = {au_m2 - au_m0:+.4f} (positive = improvement)")
    print()

    # Permutation result
    print(f"  Within-goal permutation (n_perm={perm_result['n_permutations']}):")
    print(f"    Observed |projection coef| = {abs(perm_result['observed_coef']):.4f}")
    print(f"    Empirical p-value           = {perm_result['p_empirical']:.4f}")
    print()

    # Spearman
    print(f"  Spearman (projection_z vs SR score): "
          f"ρ={rho_s:.3f} (p={p_s:.4f})  "
          f"95% CI=[{ci_lo_s:.3f}, {ci_hi_s:.3f}]")
    print(f"  Partial Spearman (after covariate residualisation): "
          f"ρ={rho_partial:.3f} (p={p_partial:.4f})")
    print()

    # Stability
    if any("col_names" in logo_results[g] and "projection_z" in logo_results[g]["col_names"]
           for g in logo_results):
        print("  Leave-one-goal-out projection OR (per 1 SD):")
        for g in sorted(logo_results.keys()):
            res_g = logo_results[g]
            if "col_names" not in res_g or "projection_z" not in res_g["col_names"]:
                continue
            j = res_g["col_names"].index("projection_z")
            print(f"    Excl. goal {g}: OR={float(np.exp(res_g['coef'][j])):.3f}  "
                  f"[{float(np.exp(res_g['ci_low'][j])):.3f}, "
                  f"{float(np.exp(res_g['ci_high'][j])):.3f}]")
        print()

    print("=" * 72)
    print(f"\n[cm] Done. Outputs in {out_dir}")


if __name__ == "__main__":
    main()
