"""Phase-17 (§21) defensive detector: SUCCESS-vs-FAILURE, not attacked-vs-clean.

Per §21.1 the defensive detector's target is changed from "attacked vs clean prompt" to
"successful attack vs failed attack" — exactly the C∪D success/failure split from the §9 dataset.
This script trains several detector families (§21.3) at several detection timings (§21.4) on the
§9 residual streams, using grouped leave-one-goal-out (the same anti-leakage protocol as Phase 6),
and reports the earliest position at which a jailbreak is detectable BEFORE harmful content appears.

Detector families (§21.3):
  - `fisher`   — difference-of-means direction threshold (the Phase-6 success direction; linear, 1-D).
  - `logistic` — StandardScaler + LogisticRegression (reuses `detector_groupkfold_audit.make_pipe`).
  - `mlp`      — StandardScaler + small MLP (one hidden layer).

Detection timings (§21.4): `prefill_last` (last input token — before ANY generation), `startofthink`,
`think_content_1/2/3` (first thinking tokens), `endofthink` (before the final answer). Post-answer
positions are reported but flagged (a detector that only fires after harmful content is defensively
useless — the §21.4 point).

Reuses the §9 loaders (`_load_goal`, `_rowkey_labels`, `_goal_shards`) and label plumbing
(`_labels_from_scores`) — no new data code. Grouped LOGO by goal_index matches Phase 6.

NOTE (carried caveat): the same prompt-length confound that qualified the Phase-6 predictor applies —
a defender does not need a *mechanism*, but the report must state the detector is partly length-driven.

Usage (CPU; torch import slow on login node → run via slurm_scripts/run_phase6_signal.slurm-style job):
  python scripts/phase17_detector.py --conditions C D \
    --layers 8 12 16 20 24 28 32 --out outputs/phase17_detect/detector_CvsD.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from poc_stage_ae.analyze_early_token_signals import _load_goal, _rowkey_labels, _goal_shards
from scripts.phase6_signal_search import _labels_from_scores
from scripts.detector_groupkfold_audit import make_pipe  # StandardScaler + LogisticRegression

PRE_ANSWER = ("prefill_last", "startofthink", "think_content_1", "think_content_2",
              "think_content_3", "endofthink")


def _mlp_pipe():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", MLPClassifier(hidden_layer_sizes=(64,), max_iter=500, early_stopping=True,
                              random_state=0)),
    ])


def _assemble(hidden_dir: Path, model: str, conditions: list[str], labels: dict[str, bool]):
    """Return position_names, n_layers, and per-(pos,layer) → (X[N,d], y[N], groups[N], finite[N])."""
    goals = sorted({g for c in conditions for g in _goal_shards(hidden_dir, model, c)})
    rows_t, rows_y, rows_g = [], [], []
    position_names, n_layers = None, None
    for g in goals:
        for c in conditions:
            if not (hidden_dir / f"{model}_{c}_goal{g}.pt").exists():
                continue
            meta, tensor = _load_goal(hidden_dir, model, c, g)
            if position_names is None:
                pos_order = meta.drop_duplicates("position_name").sort_values("position_offset")
                position_names = pos_order["position_name"].tolist()
                n_layers = int(meta["layer_count"].iloc[0])
            y = _rowkey_labels(meta, labels)
            t = tensor.to("cpu").float().numpy()  # [n_rows, n_pos, n_layers, d]
            for i, lab in enumerate(y):
                if lab is None:
                    continue
                rows_t.append(t[i]); rows_y.append(bool(lab)); rows_g.append(g)
    if not rows_t:
        return None, None, None
    T = np.stack(rows_t)          # [N, n_pos, n_layers, d]
    y = np.array(rows_y)
    groups = np.array(rows_g)
    return position_names, n_layers, (T, y, groups)


def _grouped_logo_oof(pipe_factory, X, y, groups, needs_min2=False):
    """Out-of-fold predictions via grouped leave-one-goal-out; returns (auc, acc, prec, rec, n).
    `needs_min2` skips folds with <2 of a class in train — required ONLY for the MLP (early_stopping
    makes an internal stratified split needing ≥2/class). Logistic/Fisher handle a 1-member class fine,
    so applying that skip to them would needlessly discard usable OOF predictions on thin splits."""
    oof_p, oof_y = [], []
    for g in np.unique(groups):
        tr, te = groups != g, groups == g
        if len(np.unique(y[tr])) < 2:
            continue
        # skip rows with any non-finite feature (NaN-position safety, mirrors phase6)
        fin_tr = np.isfinite(X[tr]).all(axis=1)
        ytr = y[tr][fin_tr]
        if len(np.unique(ytr)) < 2:
            continue
        if needs_min2 and min(np.bincount(ytr.astype(int))) < 2:
            continue  # MLP only
        fin_te = np.isfinite(X[te]).all(axis=1)
        if not fin_te.any():
            continue
        try:
            pipe = pipe_factory()
            pipe.fit(X[tr][fin_tr], ytr)
            p = pipe.predict_proba(X[te][fin_te])[:, 1]
        except ValueError:
            continue  # thin/degenerate fold → skip rather than crash the run (MLP fallback safety)
        oof_p.extend(p.tolist()); oof_y.extend(y[te][fin_te].astype(int).tolist())
    if len(np.unique(oof_y)) < 2:
        return None
    oof_p = np.array(oof_p); oof_y = np.array(oof_y)
    pred = (oof_p >= 0.5).astype(int)
    return {
        "auc": float(roc_auc_score(oof_y, oof_p)),
        "accuracy": float(accuracy_score(oof_y, pred)),
        "precision": float(precision_score(oof_y, pred, zero_division=0)),
        "recall": float(recall_score(oof_y, pred, zero_division=0)),
        "n": int(len(oof_y)),
    }


def _fisher_oof_auc(X, y, groups):
    """Difference-of-means (Fisher) direction threshold, grouped LOGO — the Phase-6 detector."""
    oof_s, oof_y = [], []
    for g in np.unique(groups):
        tr, te = groups != g, groups == g
        ytr = y[tr]
        if len(np.unique(ytr)) < 2:
            continue
        fin_tr = np.isfinite(X[tr]).all(axis=1)
        Xtr, ytr = X[tr][fin_tr], ytr[fin_tr]
        if len(np.unique(ytr)) < 2:
            continue
        d = Xtr[ytr].mean(0) - Xtr[~ytr].mean(0)
        nrm = np.linalg.norm(d)
        if nrm == 0 or not np.isfinite(nrm):
            continue
        d = d / nrm
        fin_te = np.isfinite(X[te]).all(axis=1)
        if not fin_te.any():
            continue
        oof_s.extend((X[te][fin_te] @ d).tolist()); oof_y.extend(y[te][fin_te].astype(int).tolist())
    if len(np.unique(oof_y)) < 2:
        return None
    return float(roc_auc_score(oof_y, oof_s))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="outputs/phase5_mechanistic/extraction")
    ap.add_argument("--model", default="qwen3")
    ap.add_argument("--conditions", nargs="+", default=["C", "D"])
    ap.add_argument("--scores", default="outputs/phase5_mechanistic/phase6_scores.jsonl")
    ap.add_argument("--layers", nargs="+", type=int, default=[8, 12, 16, 20, 24, 28, 32])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    hidden_dir = Path(args.run_dir) / "hidden_states" / "shards"
    labels = _labels_from_scores(Path(args.scores))
    position_names, n_layers, data = _assemble(hidden_dir, args.model, args.conditions, labels)
    if data is None:
        print("[phase17] no data for", args.conditions)
        return 1
    T, y, groups = data
    detectors = {"fisher": None, "logistic": make_pipe, "mlp": _mlp_pipe}
    recs = []
    for p, pos in enumerate(position_names):
        for l in args.layers:
            if l >= n_layers:
                continue
            if l == 0:
                # Layer 0 = raw embedding output: for input-token positions the residual is the
                # constant token embedding (zero within-fold variance) → Fisher returns None while
                # logistic/mlp emit a degenerate AUC≈0.5. Skip L0 uniformly so all 3 families share
                # an identical (position,layer) grid (avoids the fisher-has-6-fewer-cells asymmetry).
                continue
            X = T[:, p, l, :]
            if np.isfinite(X).all(axis=1).sum() < 4 or len(np.unique(y[np.isfinite(X).all(axis=1)])) < 2:
                continue  # non-applicable position (e.g. answer_content NaN) or single-class
            for name, fac in detectors.items():
                if name == "fisher":
                    auc = _fisher_oof_auc(X, y, groups)
                    m = {"auc": auc}
                else:
                    m = _grouped_logo_oof(fac, X, y, groups, needs_min2=(name == "mlp"))
                if m is None or m.get("auc") is None:
                    continue
                recs.append({"detector": name, "position_name": pos, "layer_index": l,
                             "pre_answer": pos in PRE_ANSWER, **m})

    df = pd.DataFrame.from_records(recs)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"[phase17] {len(df)} (detector,position,layer) cells → {args.out}")
    pre = df[df["pre_answer"]].sort_values("auc", ascending=False)
    print("[phase17] best PRE-ANSWER detectors (§21.4 — before harmful content):")
    for _, r in pre.head(10).iterrows():
        print(f"    {r['detector']:9} {r['position_name']:16} L{int(r['layer_index']):>2}  "
              f"AUC={r['auc']:.3f}" + (f" acc={r['accuracy']:.2f} prec={r['precision']:.2f} "
              f"rec={r['recall']:.2f}" if 'accuracy' in r and pd.notna(r.get('accuracy')) else ""))
    # best per detector family among pre-answer cells
    print("[phase17] best pre-answer AUC per detector family:")
    for name in ("fisher", "logistic", "mlp"):
        sub = pre[pre["detector"] == name]
        if not sub.empty:
            b = sub.iloc[0]
            print(f"    {name:9}: {b['position_name']} L{int(b['layer_index'])} AUC={b['auc']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
