#!/usr/bin/env python3
"""Is `B1` predicted by the demonstration block's SURFACE TEXT? Successor plan section 5.

Plan section 5 requires that a proposed concept representation be interpreted against a MEASURED
nuisance floor, and is explicit: *"If surface text alone almost solves the classification problem,
DO NOT call a hidden-state classifier a concept probe."* `B1` is not a classifier, so the floor has
to be posed differently, and it is posed two ways here -- one that can only bound the between-domain
VARIATION, and one that can bound the MEAN.

  (1) VARIATION FLOOR. Regress per-domain `B1` on text-only features of the cell-C and cell-A
      demonstration blocks, with LEAVE-ONE-DOMAIN-OUT cross-validation. A high CV R^2 means the
      domains where `B1` is large are simply the domains with distinctive register, and `B1` is
      reporting register. A CV R^2 near zero does NOT clear `B1` -- it only says the VARIATION is
      not register. Stated here so the result cannot be over-read either way.

  (2) MEAN CONFOUND. The one surface asymmetry that could produce a positive mean rather than
      variance is LENGTH: cell C's harmful demonstrations are drawn from a different pool than cell
      A's benign ones, so if C's block is systematically longer, more context precedes the queried
      token in C than in A and the state differs for a reason that has nothing to do with the
      concept. This is measured directly -- the per-domain length delta, its correlation with `B1`,
      and `B1` recomputed on the length-balanced subset of domains.

REUSE. The feature set is IMPORTED from `scripts/dcs_ts_pr049_blockers.py`
(`register_features`, `register_features_lengthfree`, `hedge_counts`, `HEDGE_PATTERNS`) -- the same
five-family hedge definition the register work already uses, so this floor and the corpus's own
register numbers are the same instrument. Nothing about register is redefined here.

USAGE
  python scripts/dcs_succ_b1_surface_floor.py --layer 12 --codeword button
  python scripts/dcs_succ_b1_surface_floor.py --selftest
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

EXCLUDED_DOMAINS = ("restaurant_kitchen", "school_campus", "subway_station")


def pearson(x, y):
    n = len(x)
    if n < 3:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if sx == 0 or sy == 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def spearman(x, y):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(rank(x), rank(y))


def loo_ridge_r2(X, y, lam=1.0):
    """Leave-one-DOMAIN-out cross-validated R^2 of a ridge fit. Standardisation is refit inside
    each fold, so the held-out domain contributes nothing to the scaler either -- the same
    discipline the probe work uses, for the same reason."""
    import numpy as np
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n, p = X.shape
    preds = np.zeros(n)
    for i in range(n):
        tr = np.ones(n, dtype=bool)
        tr[i] = False
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Z = (Xtr - mu) / sd
        Z = np.hstack([np.ones((Z.shape[0], 1)), Z])
        A = Z.T @ Z + lam * np.eye(Z.shape[1])
        A[0, 0] -= lam                      # do not penalise the intercept
        w = np.linalg.solve(A, Z.T @ ytr)
        z = np.hstack([[1.0], (X[i] - mu) / sd])
        preds[i] = float(z @ w)
    ss_res = float(((y - preds) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return (1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan"), preds.tolist()


def selftest() -> int:
    import numpy as np
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("  %-52s %s" % (name, "PASS" if cond else "FAIL"))
        ok = ok and bool(cond)

    chk("pearson of a line is 1", abs(pearson([1, 2, 3, 4], [2, 4, 6, 8]) - 1.0) < 1e-12)
    chk("pearson of an anti-line is -1", abs(pearson([1, 2, 3], [3, 2, 1]) + 1.0) < 1e-12)
    chk("pearson of a constant is nan", math.isnan(pearson([1, 1, 1], [1, 2, 3])))
    chk("spearman is rank-based, not linear",
        abs(spearman([1, 2, 3, 4], [1, 2, 3, 100]) - 1.0) < 1e-12
        and abs(pearson([1, 2, 3, 4], [1, 2, 3, 100]) - 1.0) > 0.1)

    rng = np.random.default_rng(0)
    X = rng.normal(size=(60, 5))
    y_sig = X[:, 0] * 2.0 + rng.normal(scale=0.2, size=60)
    r2s, _ = loo_ridge_r2(X, y_sig)
    chk("LOO ridge recovers a planted signal (R2 > 0.8)", r2s > 0.8)
    y_noise = rng.normal(size=60)
    r2n, _ = loo_ridge_r2(X, y_noise)
    chk("LOO ridge on pure noise is NOT positive (R2 <= 0.05)", r2n <= 0.05)
    chk("LOO really holds out (in-sample would beat it)", r2n < r2s)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", default=os.path.join(
        REPO, "outputs/dcs_succ/bombness_candidates_train.json"))
    ap.add_argument("--bank", default=os.path.join(
        REPO, "data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl"))
    ap.add_argument("--codeword", default="button")
    ap.add_argument("--layer", type=int, default=12)
    ap.add_argument("--out", default=os.path.join(REPO, "outputs/dcs_succ/b1_surface_floor.json"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== selftest ===")
        return selftest()

    import numpy as np
    from dcs_ts_pr049_blockers import (register_features, register_features_lengthfree,
                                       hedge_counts, HEDGE_PATTERNS)

    art = json.load(open(a.artifact, encoding="utf-8"))
    per = art["by_codeword"][a.codeword].get("per_domain_B1_export")
    if not per:
        raise SystemExit("REFUSING: the artifact carries no per_domain_B1_export block. Re-run "
                         "dcs_succ_bombness_candidates.py with the per-domain export.")
    key = "B1|L%d|shift_bomb|ref_bomb" % a.layer
    if key not in per:
        raise SystemExit("REFUSING: %r absent; have %s" % (key, sorted(per)[:4]))
    b1 = per[key]

    # demonstration blocks, per domain, cells A and C -- averaged over the family slots so the
    # unit is the DOMAIN, matching B1's unit exactly.
    texts = {"A": {}, "C": {}}
    with open(a.bank, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if (r["query_kind"] != "semantic_one_word" or int(r["n_examples"]) != 4
                    or r["cell"] not in ("A", "C") or r["domain"] in EXCLUDED_DOMAINS):
                continue
            texts[r["cell"]].setdefault(r["domain"], []).append(r["demo_block"])

    doms = sorted(d for d in b1 if d in texts["A"] and d in texts["C"])
    if len(doms) < 20:
        raise SystemExit("REFUSING: only %d domains bind both B1 and both cells' text" % len(doms))

    def feats(cell, d, fn):
        return list(np.mean([fn(t) for t in texts[cell][d]], axis=0))

    rows_full, rows_lenfree, rows_delta, lens_c, lens_a = [], [], [], [], []
    for d in doms:
        fa, fc = feats("A", d, register_features), feats("C", d, register_features)
        rows_full.append(fc + fa)
        rows_delta.append([c - x for c, x in zip(fc, fa)])
        rows_lenfree.append(feats("C", d, register_features_lengthfree)
                            + feats("A", d, register_features_lengthfree))
        lens_c.append(float(np.mean([len(t) for t in texts["C"][d]])))
        lens_a.append(float(np.mean([len(t) for t in texts["A"][d]])))

    y = [b1[d] for d in doms]
    dlen = [c - x for c, x in zip(lens_c, lens_a)]

    res = {"_label": "SURFACE NUISANCE FLOOR for B1. EXPLORATORY, TRAIN ONLY.",
           "codeword": a.codeword, "layer": a.layer, "n_domains": len(doms),
           "feature_source": "scripts/dcs_ts_pr049_blockers.py (IMPORTED, not reimplemented)",
           "n_hedge_families": len(HEDGE_PATTERNS),
           "b1_mean": float(np.mean(y)), "b1_sd": float(np.std(y, ddof=1)),
           "variation_floor": {}, "mean_confound_length": {}}

    for name, X in (("register_full_C_and_A", rows_full),
                    ("register_lengthfree_C_and_A", rows_lenfree),
                    ("register_delta_C_minus_A", rows_delta)):
        r2, _ = loo_ridge_r2(X, y)
        res["variation_floor"][name] = {
            "loo_cv_r2": r2, "n_features": len(X[0]),
            "_reading": "leave-one-DOMAIN-out cross-validated R^2 of a ridge on text-only "
                        "features. High means B1's between-domain VARIATION is register."}

    r_len_p, r_len_s = pearson(dlen, y), spearman(dlen, y)
    med = float(np.median(np.abs(dlen)))
    bal = [i for i, v in enumerate(dlen) if abs(v) <= med]
    res["mean_confound_length"] = {
        "mean_char_len_C": float(np.mean(lens_c)), "mean_char_len_A": float(np.mean(lens_a)),
        "mean_delta_C_minus_A": float(np.mean(dlen)), "sd_delta": float(np.std(dlen, ddof=1)),
        "pearson_delta_vs_B1": r_len_p, "spearman_delta_vs_B1": r_len_s,
        "b1_mean_on_length_balanced_half": float(np.mean([y[i] for i in bal])),
        "n_length_balanced": len(bal),
        "_reading": "if C's demonstration block is systematically longer than A's, more context "
                    "precedes the queried token in C and the state differs for a reason that has "
                    "nothing to do with the concept. The balanced-half mean is B1 restricted to "
                    "the domains whose |length delta| is at or below the median."}

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
