#!/usr/bin/env python3
"""§13 — PROSPECTIVE frozen-predictor attack-success prediction on v3.

The committed RP-01 (E4b) showed the decision-token refusal projection PREDICTS which items jailbreak
(AUC 0.874) on v1 — but pooled. §13 asks the prospective question: calibrate a threshold on TRAIN only,
FREEZE it, and evaluate on the untouched TEST split. Reports held-out AUC + frozen-threshold accuracy.

Pure CPU/scalar join (no GPU, no harmful text): per-item DOUBLESPEAK refusal projection (from a refproj run)
joined by item id with per-item ds_base jailbreak labels (MALICIOUS=1) from a committed behavioral run.
Predictor score = -projection (lower refusal projection => more jailbreak). Threshold frozen from train.

Usage: python scripts/phase13_prospective_predictor.py \
  --refproj outputs/refproj_clearharm_<...>/raw.jsonl \
  --labels outputs/refdecpatch_clearharm_20260807_221715_732560/raw.jsonl \
  --readout-layer 18
"""
from __future__ import annotations
import argparse, json, os
import numpy as np


def auc(scores, labels):
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    pos = s[y == 1]; neg = s[y == 0]
    if len(pos) == 0 or len(neg) == 0: return None
    # Mann-Whitney U / AUC
    order = np.argsort(s); ranks = np.empty_like(order, float); ranks[order] = np.arange(1, len(s) + 1)
    r_pos = ranks[y == 1].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refproj", required=True, help="refproj raw.jsonl (per-item DS projections)")
    ap.add_argument("--labels", required=True, help="behavioral raw.jsonl with ds_base_label per id")
    ap.add_argument("--readout-layer", type=int, default=18, help="decoder layer; projection read at hs[L+1]")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    hs = str(args.readout_layer + 1)

    proj = {}
    for l in open(args.refproj):
        r = json.loads(l)
        d = r.get("doublespeak", {})
        if hs in d: proj[r["id"]] = {"split": r.get("split"), "ds_proj": float(d[hs])}
    lab = {}
    for l in open(args.labels):
        r = json.loads(l)
        if "ds_base_label" in r: lab[r["id"]] = 1 if r["ds_base_label"] == "MALICIOUS" else 0

    rows = []
    for i, p in proj.items():
        if i in lab:
            rows.append({"id": i, "split": p["split"], "score": -p["ds_proj"], "y": lab[i]})
    tr = [r for r in rows if r["split"] == "train"]
    te = [r for r in rows if r["split"] == "test"]

    def rate(rs): return round(float(np.mean([r["y"] for r in rs])), 3) if rs else None
    res = {"n_joined": len(rows), "n_train": len(tr), "n_test": len(te),
           "readout_layer": args.readout_layer,
           "base_jailbreak_rate": {"train": rate(tr), "test": rate(te)}}

    if tr and te and rate(tr) not in (0.0, 1.0, None):
        # freeze threshold on TRAIN: choose the score cutoff maximizing Youden's J (tpr - fpr)
        tr_s = np.array([r["score"] for r in tr]); tr_y = np.array([r["y"] for r in tr])
        cands = np.unique(tr_s)
        best_j, best_thr = -1, None
        for t in cands:
            pred = (tr_s >= t).astype(int)
            tp = int(((pred == 1) & (tr_y == 1)).sum()); fn = int(((pred == 0) & (tr_y == 1)).sum())
            fp = int(((pred == 1) & (tr_y == 0)).sum()); tn = int(((pred == 0) & (tr_y == 0)).sum())
            tpr = tp / (tp + fn) if tp + fn else 0; fpr = fp / (fp + tn) if fp + tn else 0
            if tpr - fpr > best_j: best_j, best_thr = tpr - fpr, float(t)
        te_s = np.array([r["score"] for r in te]); te_y = np.array([r["y"] for r in te])
        te_pred = (te_s >= best_thr).astype(int)
        te_acc = float((te_pred == te_y).mean())
        res.update({
            "train_auc": round(auc([r["score"] for r in tr], [r["y"] for r in tr]) or float("nan"), 4),
            "frozen_threshold": round(best_thr, 4), "train_youden_J": round(best_j, 4),
            "test_auc_frozen_predictor": round(auc([r["score"] for r in te], [r["y"] for r in te]) or float("nan"), 4),
            "test_accuracy_frozen_threshold": round(te_acc, 4),
            "test_confusion": {
                "tp": int(((te_pred == 1) & (te_y == 1)).sum()), "fp": int(((te_pred == 1) & (te_y == 0)).sum()),
                "tn": int(((te_pred == 0) & (te_y == 0)).sum()), "fn": int(((te_pred == 0) & (te_y == 1)).sum())},
        })
    else:
        res["note"] = "test-split prospective eval requires both splits and a non-degenerate train jailbreak rate"

    out = args.out or os.path.join(os.path.dirname(args.refproj), "prospective_predictor_L%d.json" % args.readout_layer)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1)); print(f"[p13] -> {out}")


if __name__ == "__main__":
    main()
