#!/usr/bin/env python3
"""HERETIC-CSI P6 power (mandate §20): across-codeword Spearman between a predeclared covariate
(Zipf frequency or held-out probe rho) and a per-codeword outcome (rank-1 rescue specificity z).
Unit = codeword. Test = one-sided permutation Spearman at alpha=0.05 (critical value from 20000
exact-null permutations per n). Outcome measured with reliability `rel` (signal var / total var)."""
import json, sys
import numpy as np
rng = np.random.default_rng(20261013)
def spearman(a, b):
    ra = a.argsort(-1).argsort(-1); rb = b.argsort(-1).argsort(-1)
    ra = ra - ra.mean(-1, keepdims=True); rb = rb - rb.mean(-1, keepdims=True)
    return (ra * rb).sum(-1) / np.sqrt((ra ** 2).sum(-1) * (rb ** 2).sum(-1))
out = {"alpha": 0.05, "sided": "one (predeclared direction)", "n_sim": 20000, "rows": []}
for n in [2, 4, 6, 8, 10, 12, 15, 17, 21, 23]:
    x0 = np.tile(np.arange(n, dtype=float), (20000, 1)); y0 = rng.permuted(x0, axis=1)
    null = spearman(x0, y0); crit = np.quantile(null, 0.95)
    import math
    minp = 1 / math.factorial(n)
    row = {"n_codewords": n, "min_attainable_p": minp, "crit_rho": round(float(crit), 3),
           "CANNOT_ANSWER": bool(minp > 0.05), "power": {}}
    for rho in [0.4, 0.5, 0.6, 0.7, 0.8]:
        for rel in [1.0, 0.7, 0.5]:
            x = rng.standard_normal((20000, n)); e = rng.standard_normal((20000, n))
            y = rho * x + np.sqrt(1 - rho ** 2) * e
            y = np.sqrt(rel) * y + np.sqrt(1 - rel) * rng.standard_normal((20000, n))
            row["power"]["rho%.1f_rel%.1f" % (rho, rel)] = round(float((spearman(x, y) > crit).mean()), 3)
    out["rows"].append(row)
    print(n, row["crit_rho"], row["CANNOT_ANSWER"], {k: v for k, v in row["power"].items() if k.endswith("rel0.7")})
json.dump(out, open(sys.argv[1], "w"), indent=1)
