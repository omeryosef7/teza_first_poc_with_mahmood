"""contextual_identity_probe.py -- fit and evaluate the Bombness probe.

Given activations at a (layer, position) and Bombness labels, fit a linear probe and
report validity metrics with the sprint's statistical contract (plan §5.1, §5.4, §16;
Appendix A2/A8/A9). Pure numpy + sklearn -- no torch, no model -- so it is fully
unit-testable offline with synthetic activations.

Estimators (manifest D3):
  - PRIMARY: sklearn LogisticRegression(penalty='l2', fit_intercept=True), C on dev.
  - SECONDARY: difference-of-means direction (no upstream equivalent; robustness).

What is DELIBERATELY different from upstream (Appendix A):
  - resampling unit is the EXAMPLE, never the token/row (A9.6): each example
    contributes one positive + one negative item, and the bootstrap resamples
    examples so the CI reflects the true ~n_examples, not inflated n_rows.
  - fp32 fit (A9.8); ROC-AUC + balanced accuracy + bootstrap CI (upstream reports
    only accuracy/log-loss with no CI).
  - the class space is fixed per experiment and never mixed (A9.7): here it is the
    binary Bombness {bound-to-harmful=1, bound-to-benign=0}.

Split discipline (manifest D4) is enforced upstream in probe_dataset; this module
additionally refuses to fit if train and eval groups overlap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, balanced_accuracy_score

DEFAULT_CS = (1e-4, 1e-3, 1e-2, 1e-1, 1e0, 1e1)


@dataclass
class FitResult:
    estimator: str
    C: Optional[float]
    coef: np.ndarray            # (hidden,) direction (unit-norm for diff-of-means)
    intercept: float
    # metrics on the eval set this was scored against
    auc: float
    balanced_acc: float
    auc_ci: tuple               # (lo, hi) bootstrap 95%, resampled by group
    n_eval_examples: int
    extra: dict = field(default_factory=dict)


def _as_xy(items_acts, items_labels):
    X = np.asarray(items_acts, dtype=np.float64)
    y = np.asarray(items_labels, dtype=int)
    if X.ndim != 2:
        raise ValueError(f"activations must be (n_items, hidden); got {X.shape}")
    if X.shape[0] != y.shape[0]:
        raise ValueError("activations and labels length mismatch")
    return X, y


def diff_of_means_direction(X, y):
    """Unit direction from class-0 mean to class-1 mean; threshold at the midpoint
    projection. Returns (unit_vector, bias) so that score = X@v + b, decision at 0."""
    X, y = _as_xy(X, y)
    mu1 = X[y == 1].mean(axis=0)
    mu0 = X[y == 0].mean(axis=0)
    v = mu1 - mu0
    nrm = np.linalg.norm(v)
    if nrm == 0:
        raise ValueError("degenerate diff-of-means (identical class means)")
    v = v / nrm
    mid = 0.5 * (mu1 + mu0)
    b = -float(mid @ v)
    return v, b


def _scores_logreg(clf, X):
    return clf.decision_function(X)


def _bootstrap_auc_ci(y, scores, groups, n_boot=2000, seed=0):
    """Bootstrap 95% CI for AUC, resampling GROUPS (examples), not rows. `groups` maps
    each item to its example id; resampling picks whole examples with replacement."""
    y = np.asarray(y)
    scores = np.asarray(scores, dtype=float)
    groups = np.asarray(groups)
    uniq = np.unique(groups)
    # index rows by group for fast reassembly
    by_g = {g: np.where(groups == g)[0] for g in uniq}
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([by_g[g] for g in pick])
        yb, sb = y[idx], scores[idx]
        if len(np.unique(yb)) < 2:
            continue
        aucs.append(roc_auc_score(yb, sb))
    if not aucs:
        return (float("nan"), float("nan"))
    lo, hi = np.percentile(aucs, [2.5, 97.5])
    return (float(lo), float(hi))


def fit_logreg(X_tr, y_tr, C):
    X_tr, y_tr = _as_xy(X_tr, y_tr)
    # L2 is the lbfgs default; naming penalty='l2' explicitly is deprecated in
    # sklearn >=1.8, so we rely on the default (still L2) and control it via C.
    clf = LogisticRegression(C=C, fit_intercept=True, max_iter=5000, solver="lbfgs")
    clf.fit(X_tr, y_tr)
    return clf


def select_C(X_tr, y_tr, X_dev, y_dev, groups_dev, Cs=DEFAULT_CS):
    """Pick C by dev AUC (plan §3.5 -- selection on dev only)."""
    best = None
    for C in Cs:
        clf = fit_logreg(X_tr, y_tr, C)
        auc = roc_auc_score(y_dev, _scores_logreg(clf, np.asarray(X_dev, float)))
        if best is None or auc > best[1]:
            best = (C, auc)
    return best[0], best[1]


def evaluate_direction(v, b, X, y, groups, n_boot=2000, seed=0):
    """Score a fixed linear direction (e.g. diff-of-means) on an eval set."""
    X, y = _as_xy(X, y)
    scores = X @ v + b
    auc = roc_auc_score(y, scores)
    bacc = balanced_accuracy_score(y, (scores > 0).astype(int))
    ci = _bootstrap_auc_ci(y, scores, groups, n_boot=n_boot, seed=seed)
    return auc, bacc, ci, scores


def fit_and_eval(X_tr, y_tr, groups_tr, X_ev, y_ev, groups_ev,
                 Cs=DEFAULT_CS, n_boot=2000, seed=0,
                 X_dev=None, y_dev=None, groups_dev=None):
    """Fit both estimators on train, select C on dev (falls back to eval-free CV-free
    default if no dev given -- only acceptable for unit tests), score on eval.

    Refuses to run if any train example id appears in the eval groups (leak guard)."""
    if groups_dev is None:
        groups_dev = groups_ev
        if X_dev is None:
            X_dev, y_dev = X_ev, y_ev
    leak = set(np.asarray(groups_tr)) & set(np.asarray(groups_ev))
    if leak:
        raise AssertionError(f"train/eval example leak: {sorted(map(str, leak))[:5]}")

    C, dev_auc = select_C(X_tr, y_tr, X_dev, y_dev, groups_dev, Cs=Cs)
    clf = fit_logreg(X_tr, y_tr, C)
    scores = _scores_logreg(clf, np.asarray(X_ev, float))
    auc = roc_auc_score(y_ev, scores)
    bacc = balanced_accuracy_score(y_ev, (scores > 0).astype(int))
    ci = _bootstrap_auc_ci(y_ev, scores, groups_ev, n_boot=n_boot, seed=seed)
    logreg = FitResult("logreg_l2", C, clf.coef_[0].copy(), float(clf.intercept_[0]),
                       auc, bacc, ci, len(np.unique(groups_ev)),
                       extra={"dev_auc": dev_auc})

    v, b = diff_of_means_direction(X_tr, y_tr)
    d_auc, d_bacc, d_ci, _ = evaluate_direction(v, b, X_ev, y_ev, groups_ev,
                                                n_boot=n_boot, seed=seed)
    dom = FitResult("diff_of_means", None, v, b, d_auc, d_bacc, d_ci,
                    len(np.unique(groups_ev)))
    return {"logreg": logreg, "diff_of_means": dom}


# --------------------------------------------------------------------------- #
# Gate-1 validity controls (plan §5.4). Each returns an AUC the headline must beat.
# --------------------------------------------------------------------------- #
def control_label_shuffle(X_tr, y_tr, X_ev, y_ev, groups_ev, C=1.0, seed=0):
    """Permute train labels -> probe should be at chance (AUC ~ 0.5)."""
    rng = np.random.default_rng(seed)
    y_perm = rng.permutation(np.asarray(y_tr))
    clf = fit_logreg(X_tr, y_perm, C)
    return float(roc_auc_score(y_ev, _scores_logreg(clf, np.asarray(X_ev, float))))


def control_random_direction(X_ev, y_ev, hidden=None, seed=0):
    """Norm-matched random direction -> AUC ~ 0.5."""
    X_ev, y_ev = _as_xy(X_ev, y_ev)
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(X_ev.shape[1])
    v /= np.linalg.norm(v)
    return float(roc_auc_score(y_ev, X_ev @ v))


def control_scalar_feature(feature_ev, y_ev):
    """A one-scalar baseline (position index, sequence length, or codeword-token-id).
    AUC of that scalar alone -- the probe must beat these (plan §5.4)."""
    f = np.asarray(feature_ev, float)
    y = np.asarray(y_ev, int)
    if len(np.unique(y)) < 2:
        return float("nan")
    auc = roc_auc_score(y, f)
    return float(max(auc, 1 - auc))  # a-priori-signless: either orientation counts


def cosine(u, v):
    u = np.asarray(u, float); v = np.asarray(v, float)
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu == 0 or nv == 0:
        return float("nan")
    return float((u @ v) / (nu * nv))
