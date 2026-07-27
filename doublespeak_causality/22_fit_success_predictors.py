"""
22_fit_success_predictors.py — Phase 5 / Workstream E (plan §9.2). Test whether the mechanistic
temporal features (from 21) PREDICT behavioral jailbreak success (DS_MALICIOUS). Benign CPU-only
analysis (reads scalar features, fits logistic regression). No harmful text.

Reports:
  - univariate AUC per feature (which signal predicts best);
  - cross-validated (stratified k-fold) multivariate logistic-regression AUC;
  - HELD-OUT-CONCEPT AUC (train on some concepts, test on unseen concepts) — the real generalization test;
  - the "temporal objective" (late_align − λ·early_align) univariate AUC, the candidate attack objective.

A feature is a useful attack objective ONLY if it predicts held-out behavioral success (plan §9.2),
not merely differs between groups.

Run: python 22_fit_success_predictors.py --features outputs/features_llama8b/features.json
"""
import os
import sys
import json
import argparse
import numpy as np

FEATS = ["early_align", "mid_align", "late_align", "early_to_late", "onset_layer",
         "peak_align", "auc_align"]


def _auc(y, s):
    """ROC AUC. Prefer sklearn (tie-correct; onset_layer is integer with ties); fallback to a
    rank statistic. A feature and its negation are symmetric — report max(auc, 1-auc) so a
    strongly *negative* predictor isn't reported as ~0 (direction is set by the sign of the coef)."""
    y = np.asarray(y); s = np.asarray(s, float)
    if len(set(y.tolist())) < 2:
        return float("nan")
    try:
        from sklearn.metrics import roc_auc_score
        a = float(roc_auc_score(y, s))
    except Exception:
        pos, neg = s[y == 1], s[y == 0]
        order = np.argsort(s, kind="mergesort")
        ranks = np.empty(len(s), float); ranks[order] = np.arange(1, len(s) + 1)
        a = float((ranks[y == 1].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))
    return max(a, 1.0 - a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--lam", type=float, default=1.0, help="λ for temporal objective late−λ·early")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = json.load(open(args.features))
    rows = d["rows"]
    y = np.array([r["ds_malicious"] for r in rows])
    X = np.array([[r["feat"][f] for f in FEATS] for r in rows], float)
    concepts = np.array([r["concept"] for r in rows])
    print(f"[predict] n={len(rows)} pos(DS_MALICIOUS)={int(y.sum())} concepts={len(set(concepts))}")

    # 1) univariate AUCs
    print("[predict] univariate AUC (predicting DS_MALICIOUS):")
    uni = {}
    for j, f in enumerate(FEATS):
        a = _auc(y, X[:, j]); uni[f] = round(a, 3)
        print(f"  {f:14s} AUC={a:.3f}")
    # candidate temporal objective: late_align − λ·early_align
    to = X[:, FEATS.index("late_align")] - args.lam * X[:, FEATS.index("early_align")]
    auc_to = _auc(y, to); print(f"  {'TEMPORAL late−λ·early':22s} AUC={auc_to:.3f}")

    result = {"n": len(rows), "n_pos": int(y.sum()), "univariate_auc": uni,
              "temporal_objective_auc": round(auc_to, 3), "lam": args.lam}

    # 2) multivariate CV + held-out-concept — needs sklearn
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline
        from sklearn.model_selection import StratifiedKFold, GroupKFold
        from sklearn.metrics import roc_auc_score

        def cv_auc(splitter, groups=None):
            aucs = []
            for tr, te in (splitter.split(X, y, groups) if groups is not None else splitter.split(X, y)):
                if len(set(y[tr])) < 2 or len(set(y[te])) < 2:
                    continue
                clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, C=1.0))
                clf.fit(X[tr], y[tr])
                aucs.append(roc_auc_score(y[te], clf.predict_proba(X[te])[:, 1]))
            return (float(np.mean(aucs)), float(np.std(aucs)), len(aucs)) if aucs else (float("nan"), 0.0, 0)

        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
        m, s, k = cv_auc(skf)
        print(f"[predict] multivariate 5-fold CV AUC = {m:.3f} ± {s:.3f} (k={k})")
        result["cv5_auc_mean"], result["cv5_auc_std"] = round(m, 3), round(s, 3)

        ncon = len(set(concepts))
        if ncon >= 3:
            gkf = GroupKFold(n_splits=min(5, ncon))
            mg, sg, kg = cv_auc(gkf, groups=concepts)
            print(f"[predict] HELD-OUT-CONCEPT AUC = {mg:.3f} ± {sg:.3f} (k={kg}) <-- generalization test")
            result["heldout_concept_auc_mean"], result["heldout_concept_auc_std"] = round(mg, 3), round(sg, 3)
    except Exception as e:
        print(f"[predict] sklearn unavailable ({e!r}); univariate AUCs only")

    out = args.out or os.path.join(os.path.dirname(args.features), "success_predictors.json")
    json.dump(result, open(out, "w"), indent=2)
    print(f"[predict] -> {out}")


if __name__ == "__main__":
    main()
