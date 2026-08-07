#!/usr/bin/env python
"""P6 behavioral-prediction arm: does the per-item REFUSAL Jacobian predict which
Doublespeak items jailbreak, while the CONCEPT Jacobian is behaviorally inert?

Joins the P6 jacobian raw (doublespeak condition, final_prompt position) with the
behav_refusal ds_base StrongREJECT label, on item_key == id (exact, no hashing loss).
Reports AUC (oriented so >=0.5) with a seeded percentile-bootstrap 95% CI, per split
and pooled, for the refusal-target vs concept-target features, plus the paired
refusal-minus-concept ||J|| AUC difference. No new GPU work.

Usage:
  python scripts/analyze_jacobian_predicts_behavior.py \
    --jac outputs/jacobian_clearharm_20260807_132150_732004 \
    --beh outputs/behav_refusal_clearharm_a1.0_20260804_133355_708038 \
    --concept-peak 16 --refusal-peak 12 --out outputs/p6_predicts_behavior.json
"""
import argparse, json, os
import numpy as np


def _auc(x, y):
    x = np.asarray(x, float); y = np.asarray(y, int)
    pos, neg = x[y == 1], x[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    gt = sum((p > neg).sum() for p in pos)
    eq = sum((p == neg).sum() for p in pos)
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def _boot(x, y, n=5000, seed=0, orient=None):
    x = np.asarray(x, float); y = np.asarray(y, int)
    a0 = _auc(x, y)
    if orient is None:
        orient = a0 >= 0.5
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y)); out = []
    for _ in range(n):
        s = rng.choice(idx, len(idx), replace=True)
        if y[s].sum() in (0, len(s)):
            continue
        a = _auc(x[s], y[s]); out.append(a if orient else 1 - a)
    lo, hi = np.percentile(out, [2.5, 97.5])
    return (a0 if orient else 1 - a0), float(lo), float(hi), bool(orient)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jac", required=True, help="jacobian run dir (with raw.jsonl)")
    ap.add_argument("--beh", required=True, help="behav_refusal run dir (with raw.jsonl)")
    ap.add_argument("--concept-peak", type=int, default=16, help="layer for concept ||J|| feature")
    ap.add_argument("--refusal-peak", type=int, default=12, help="layer for refusal ||J|| feature")
    ap.add_argument("--position", default="final_prompt")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    lab = {}
    for l in open(os.path.join(a.beh, "raw.jsonl")):
        r = json.loads(l)
        lab[r["id"]] = (r["split"], int(r["ds_base_label"] == "MALICIOUS"))

    feat = {}
    for l in open(os.path.join(a.jac, "raw.jsonl")):
        r = json.loads(l)
        if r["condition"] != "doublespeak":
            continue
        bp = r["by_pos"][a.position]
        d = feat.setdefault(r["item_key"], {}); t = r["target"]
        peak = a.concept_peak if t == "concept" else a.refusal_peak
        d[f"{t}_scalar"] = r["scalar"]
        d[f"{t}_gradnorm_peak"] = bp[peak]["grad_norm"]
        d[f"{t}_jacproj_peak"] = abs(bp[peak]["jac_proj"])

    items = [k for k in feat if k in lab]
    res = {"n": len(items), "concept_peak_layer": a.concept_peak,
           "refusal_peak_layer": a.refusal_peak, "features": {}}
    feats = ["refusal_scalar", "refusal_gradnorm_peak", "refusal_jacproj_peak",
             "concept_scalar", "concept_gradnorm_peak", "concept_jacproj_peak"]
    for fn in feats:
        cell = {}
        orient = None
        for sp in ["pooled", "train", "test"]:
            ks = [k for k in items if (sp == "pooled" or lab[k][0] == sp) and fn in feat[k]]
            x = [feat[k][fn] for k in ks]; y = [lab[k][1] for k in ks]
            auc, lo, hi, orient = _boot(x, y, orient=orient)
            cell[sp] = {"auc": round(auc, 4), "ci95": [round(lo, 4), round(hi, 4)],
                        "n": len(ks), "n_mal": int(sum(y))}
        cell["orientation"] = "lower_scalar_more_jailbreak" if not orient else "higher_more_jailbreak"
        res["features"][fn] = cell

    # paired refusal||J|| - concept||J|| AUC difference (both oriented to >=0.5)
    xr = np.array([feat[k]["refusal_gradnorm_peak"] for k in items])
    xc = np.array([feat[k]["concept_gradnorm_peak"] for k in items])
    y = np.array([lab[k][1] for k in items])
    def o(x, y):
        v = _auc(x, y); return max(v, 1 - v)
    rng = np.random.default_rng(0); diffs = []
    for _ in range(5000):
        s = rng.choice(np.arange(len(y)), len(y), replace=True)
        if y[s].sum() in (0, len(s)):
            continue
        diffs.append(o(xr[s], y[s]) - o(xc[s], y[s]))
    res["refusal_minus_concept_gradnorm_auc_diff"] = {
        "point": round(o(xr, y) - o(xc, y), 4),
        "ci95": [round(float(np.percentile(diffs, 2.5)), 4),
                 round(float(np.percentile(diffs, 97.5)), 4)]}

    print(json.dumps(res, indent=2))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=2)
        print("wrote", a.out)


if __name__ == "__main__":
    main()
