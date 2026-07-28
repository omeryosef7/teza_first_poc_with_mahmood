"""
24_codeword_selection.py — Phase 6 / Workstream F (plan §10.3 Stage 1: codeword selection).
The FEASIBLE Level-5 test: does OPTIMIZING the mechanistic temporal objective (pick the codeword with
MINIMUM early harmful alignment) improve the attack vs random codeword selection?

Reads the 6-codeword feature run (21 output: per-condition early_align + ds_malicious label). Aggregates
to (base, codeword): mean early_align + jailbreak rate. Per base with ≥K codewords, compares the
jailbreak rate of:
  - TEMPORAL-selected codeword (argmin early_align)   ← the objective
  - RANDOM codeword (expected = mean over the base's codewords)
  - ANTI (argmax early_align)                          ← the objective's opposite (sanity)
Aggregated across bases with a paired bootstrap CI (temporal − random). HELD-OUT by concept (the
codeword→early_align ranking is computed within-base, so no fitting leaks; the test is whether the
objective's ranking transfers to higher jailbreak rate).

Benign scalar analysis (reads features label data; no harmful text). Reuses stats.paired_bootstrap_ci.

Usage: python 24_codeword_selection.py --features outputs/features_cw6/features.json
"""
import os
import sys
import json
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--min-codewords", type=int, default=3)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    rows = json.load(open(args.features))["rows"]

    # aggregate to (base_id, codeword): mean early_align, jailbreak rate over context_lengths
    agg = defaultdict(lambda: {"early": [], "mal": [], "concept": None})
    for r in rows:
        base = r["key"][0]
        a = agg[(base, r["codeword"])]
        a["early"].append(r["feat"]["early_align"]); a["mal"].append(r["ds_malicious"])
        a["concept"] = r["concept"]
    cw = {k: {"early": sum(v["early"]) / len(v["early"]), "jb": sum(v["mal"]) / len(v["mal"]),
              "concept": v["concept"]} for k, v in agg.items()}

    by_base = defaultdict(list)
    for (base, w), v in cw.items():
        by_base[base].append((w, v["early"], v["jb"], v["concept"]))

    temporal, random_, anti, concepts = [], [], [], []
    for base, lst in by_base.items():
        if len(lst) < args.min_codewords:
            continue
        lst_sorted = sorted(lst, key=lambda x: x[1])        # by early_align ascending
        temporal.append(lst_sorted[0][2])                    # argmin early → jailbreak rate
        anti.append(lst_sorted[-1][2])                       # argmax early
        random_.append(sum(x[2] for x in lst) / len(lst))    # mean = expected random pick
        concepts.append(lst[0][3])

    n = len(temporal)
    print(f"[cw-select] bases with ≥{args.min_codewords} codewords: {n}")
    if n < 3:
        print("[cw-select] too few bases for a meaningful test"); return
    ci_tr = stats.paired_bootstrap_ci(temporal, random_, n_boot=10000, seed=0)
    ci_ta = stats.paired_bootstrap_ci(temporal, anti, n_boot=10000, seed=0)

    # --- MULTIVARIATE leave-one-concept-out selection (stronger predictor than early_align alone) ---
    mv = None
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline
        FEATS = ["early_align", "mid_align", "late_align", "early_to_late", "onset_layer",
                 "peak_align", "auc_align"]
        # condition-level design (per-condition features + label + concept + base + codeword)
        Xc = np.array([[r["feat"][f] for f in FEATS] for r in rows], float)
        yc = np.array([r["ds_malicious"] for r in rows])
        con = np.array([r["concept"] for r in rows]); base = np.array([r["key"][0] for r in rows])
        cwv = np.array([r["codeword"] for r in rows])
        prob = np.full(len(rows), np.nan)
        for c in set(con):                     # leave-one-concept-out: fit on others, predict on c
            tr = con != c
            if len(set(yc[tr])) < 2:
                continue
            clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
            clf.fit(Xc[tr], yc[tr])
            prob[con == c] = clf.predict_proba(Xc[con == c])[:, 1]
        # aggregate predicted prob + actual jailbreak to (base, codeword)
        bc_prob, bc_jb = defaultdict(list), defaultdict(list)
        for i in range(len(rows)):
            if np.isnan(prob[i]):
                continue
            bc_prob[(base[i], cwv[i])].append(prob[i]); bc_jb[(base[i], cwv[i])].append(yc[i])
        by_b = defaultdict(list)
        for k in bc_prob:
            by_b[k[0]].append((k[1], float(np.mean(bc_prob[k])), float(np.mean(bc_jb[k]))))
        mv_sel, mv_rand = [], []
        for b, lst in by_b.items():
            if len(lst) < args.min_codewords:
                continue
            best = max(lst, key=lambda x: x[1])          # argmax predicted jailbreak prob
            mv_sel.append(best[2]); mv_rand.append(sum(x[2] for x in lst) / len(lst))
        if len(mv_sel) >= 3:
            ci_mv = stats.paired_bootstrap_ci(mv_sel, mv_rand, n_boot=10000, seed=0)
            mv = {"n_bases": len(mv_sel),
                  "jailbreak_rate": {"multivariate_selected": round(sum(mv_sel) / len(mv_sel), 3),
                                     "random": round(sum(mv_rand) / len(mv_rand), 3)},
                  "multivariate_minus_random": {"mean": round(ci_mv["mean_diff"], 3),
                                                "lo": round(ci_mv["lo"], 3), "hi": round(ci_mv["hi"], 3),
                                                "ci_reliable": ci_mv["ci_reliable"]}}
            print(f"[cw-select] MULTIVARIATE (LOCO) selected={mv['jailbreak_rate']['multivariate_selected']} "
                  f"random={mv['jailbreak_rate']['random']} | Δ={mv['multivariate_minus_random']['mean']} "
                  f"[{mv['multivariate_minus_random']['lo']},{mv['multivariate_minus_random']['hi']}]")
    except Exception as e:
        print(f"[cw-select] multivariate selection skipped ({e!r})")
    result = {
        "n_bases": n,
        "mean_jailbreak_rate": {
            "temporal_selected": round(sum(temporal) / n, 3),
            "random": round(sum(random_) / n, 3),
            "anti_selected": round(sum(anti) / n, 3)},
        "temporal_minus_random": {"mean": round(ci_tr["mean_diff"], 3),
                                  "lo": round(ci_tr["lo"], 3), "hi": round(ci_tr["hi"], 3),
                                  "ci_reliable": ci_tr["ci_reliable"]},
        "temporal_minus_anti": {"mean": round(ci_ta["mean_diff"], 3),
                                "lo": round(ci_ta["lo"], 3), "hi": round(ci_ta["hi"], 3)},
        "multivariate_loco": mv,
    }
    print(f"[cw-select] jailbreak rate: temporal={result['mean_jailbreak_rate']['temporal_selected']} "
          f"random={result['mean_jailbreak_rate']['random']} anti={result['mean_jailbreak_rate']['anti_selected']}")
    print(f"[cw-select] TEMPORAL − RANDOM = {result['temporal_minus_random']['mean']} "
          f"[{result['temporal_minus_random']['lo']},{result['temporal_minus_random']['hi']}] "
          f"(reliable={result['temporal_minus_random']['ci_reliable']}) "
          f"<-- Level 5: objective improves attack if >0 and CI excludes 0")
    out = args.out or os.path.join(os.path.dirname(args.features), "codeword_selection.json")
    json.dump(result, open(out, "w"), indent=2)
    print(f"[cw-select] -> {out}")


if __name__ == "__main__":
    main()
