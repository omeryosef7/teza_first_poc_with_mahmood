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
    """RAW directional ROC AUC (sklearn, tie-correct; rank-statistic fallback). Directional: <0.5
    means the feature predicts the POSITIVE class *negatively* (e.g. low early_align → DS-malicious).
    NOTE: report this raw value, NOT max(auc,1-auc) — the symmetric fold is biased upward for
    genuinely null features (sampling noise pushes |auc-0.5| away from 0), which would make a
    no-signal feature look predictive. Absolute predictive power = |auc-0.5| is reported separately."""
    y = np.asarray(y); s = np.asarray(s, float)
    if len(set(y.tolist())) < 2:
        return float("nan")
    try:
        from sklearn.metrics import roc_auc_score
        a = float(roc_auc_score(y, s))
    except Exception:
        pos, neg = s[y == 1], s[y == 0]
        # tie-corrected midranks (average rank within ties) so the fallback matches sklearn on
        # tied scores (e.g. integer-valued onset_layer); plain argsort ranks would diverge.
        order = np.argsort(s, kind="mergesort")
        ranks = np.empty(len(s), float); ranks[order] = np.arange(1, len(s) + 1)
        su = np.sort(s)
        i = 0
        while i < len(su):
            j = i
            while j + 1 < len(su) and su[j + 1] == su[i]:
                j += 1
            if j > i:  # tie group [i..j] → assign the average of their ranks
                avg = (i + 1 + j + 1) / 2.0
                ranks[np.isin(s, su[i])] = avg
            i = j + 1
        a = float((ranks[y == 1].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))
    return a


def _align_matrix(ds_move_sub, dvec):
    """C9 FIX (NEXT_CAUSAL_SPRINT S0): cos( DS−Neutral movement, fold-specific harmful axis dvec ) per
    (row, layer), matching 21's _cos = dot / (|a||b| + 1e-8). ds_move_sub: [m, L, H]; dvec: [L, H]."""
    num = np.einsum("mlh,lh->ml", ds_move_sub, dvec)
    dsn = np.linalg.norm(ds_move_sub, axis=2)
    dvn = np.linalg.norm(dvec, axis=1)
    return num / (dsn * dvn[None, :] + 1e-8)


def _feats_from_align(align, bands, onset_thresh):
    """C9 FIX (NEXT_CAUSAL_SPRINT S0): rebuild the FEATS vector from an alignment trajectory [m, L] in
    the EXACT column order of FEATS (21's feature definitions), for leakage-free per-fold scoring."""
    e = align[:, bands["early"]].mean(1)
    mi = align[:, bands["mid"]].mean(1)
    la = align[:, bands["late"]].mean(1)
    mask = align >= onset_thresh
    onset = np.where(mask.any(1), mask.argmax(1), -1).astype(float)
    # order matches FEATS: early, mid, late, early_to_late, onset_layer, peak_align, auc_align
    return np.column_stack([e, mi, la, la - e, onset, align.max(1), align.mean(1)])


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

    # C9 FIX (NEXT_CAUSAL_SPRINT S0): load raw movement vectors (if 21 wrote them) so the held-out-
    # concept AUC re-fits the harmful axis per fold using ONLY the fold's training concepts (no leak).
    ds_move = dir_move = None
    raw_path = os.path.join(os.path.dirname(os.path.abspath(args.features)), d.get("raw_npz", "features_raw.npz"))
    if os.path.exists(raw_path):
        with np.load(raw_path) as z:
            ds_move, dir_move = z["ds_move"], z["dir_move"]
    bands = d.get("bands")
    onset_thresh = float(d.get("onset_thresh", 0.1))

    # 1) univariate AUCs (raw directional; abs power = |auc-0.5| reported alongside)
    print("[predict] univariate AUC (predicting DS_MALICIOUS; <0.5 = negative predictor):")
    uni, uni_abs = {}, {}
    for j, f in enumerate(FEATS):
        a = _auc(y, X[:, j]); uni[f] = round(a, 3); uni_abs[f] = round(abs(a - 0.5), 3)
        print(f"  {f:14s} AUC={a:.3f}  |power|={abs(a - 0.5):.3f}")
    # candidate temporal objective: late_align − λ·early_align
    to = X[:, FEATS.index("late_align")] - args.lam * X[:, FEATS.index("early_align")]
    auc_to = _auc(y, to); print(f"  {'TEMPORAL late−λ·early':22s} AUC={auc_to:.3f}  |power|={abs(auc_to - 0.5):.3f}")

    result = {"n": len(rows), "n_pos": int(y.sum()), "univariate_auc": uni,
              "univariate_abs_power": uni_abs,
              "temporal_objective_auc": round(auc_to, 3),
              "temporal_objective_abs_power": round(abs(auc_to - 0.5), 3), "lam": args.lam}

    # 2) multivariate CV + held-out-concept — needs sklearn
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline
        from sklearn.model_selection import StratifiedKFold, GroupKFold
        from sklearn.metrics import roc_auc_score
    except ImportError as e:
        print(f"[predict] sklearn unavailable ({e!r}); univariate AUCs only")
    else:

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
            nsplits = min(5, ncon)
            leakfree = ds_move is not None and bands is not None
            if leakfree:
                # C9 FIX (NEXT_CAUSAL_SPRINT S0): per-fold harmful axis. For each GroupKFold split we
                # rebuild dvec from the TRAINING concepts' Direct−Neutral movement only, recompute the
                # alignment features for BOTH train and held-out rows on that fold-specific axis, then
                # score — so a held-out concept never contributes to the axis it is evaluated against.
                gkf = GroupKFold(n_splits=nsplits)
                aucs = []
                for tr, te in gkf.split(ds_move, y, concepts):
                    if len(set(y[tr])) < 2 or len(set(y[te])) < 2:
                        continue
                    dvec = dir_move[tr].mean(0)
                    dvec = dvec / (np.linalg.norm(dvec, axis=1, keepdims=True) + 1e-8)
                    Xtr = _feats_from_align(_align_matrix(ds_move[tr], dvec), bands, onset_thresh)
                    Xte = _feats_from_align(_align_matrix(ds_move[te], dvec), bands, onset_thresh)
                    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, C=1.0))
                    clf.fit(Xtr, y[tr])
                    aucs.append(roc_auc_score(y[te], clf.predict_proba(Xte)[:, 1]))
                mg, sg, kg = (float(np.mean(aucs)), float(np.std(aucs)), len(aucs)) if aucs else (float("nan"), 0.0, 0)
                print(f"[predict] HELD-OUT-CONCEPT AUC = {mg:.3f} ± {sg:.3f} (k={kg}) <-- generalization test (leakage-free per-fold axis)")
            else:
                # C9 FIX (NEXT_CAUSAL_SPRINT S0): raw vectors absent (pre-fix features.json) — fall back
                # to global-axis features and flag that this number still carries axis leakage.
                gkf = GroupKFold(n_splits=nsplits)
                mg, sg, kg = cv_auc(gkf, groups=concepts)
                print(f"[predict] HELD-OUT-CONCEPT AUC = {mg:.3f} ± {sg:.3f} (k={kg}) <-- generalization test (WARNING: global axis; leakage — rerun 21 for per-fold axis)")
            result["heldout_concept_auc_mean"], result["heldout_concept_auc_std"] = round(mg, 3), round(sg, 3)
            result["heldout_axis_per_fold"] = bool(leakfree)  # C9 FIX (NEXT_CAUSAL_SPRINT S0)

    out = args.out or os.path.join(os.path.dirname(args.features), "success_predictors.json")
    json.dump(result, open(out, "w"), indent=2)
    print(f"[predict] -> {out}")


if __name__ == "__main__":
    main()
