#!/usr/bin/env python3
"""P6 power v2 (review #3 finding 10): H6a ONE-sided, H6b TWO-sided, Holm over {H6a, H6b}.
Holm with 2 tests: the smaller p must be <= 0.025, the larger <= 0.05. A test's power is therefore bracketed by
  conservative = rejection at alpha/2 = 0.025 (guaranteed regardless of the other test) and
  optimistic    = rejection at 0.05 (only if the other test rejects first).
Exact-null permutation critical values (20000 perms per n); outcome reliability rel (signal var/total var);
same generative model as p6_power.py; seed 20261014."""
import json, sys
import numpy as np
rng = np.random.default_rng(20261014)
NS = 20000


def spearman(a, b):
    ra = a.argsort(-1).argsort(-1).astype(float); rb = b.argsort(-1).argsort(-1).astype(float)
    ra -= ra.mean(-1, keepdims=True); rb -= rb.mean(-1, keepdims=True)
    return (ra * rb).sum(-1) / np.sqrt((ra ** 2).sum(-1) * (rb ** 2).sum(-1))


out = {"model": "y = rho*x + sqrt(1-rho^2)*e, then reliability rel", "n_sim": NS, "holm_over": ["H6a", "H6b"], "rows": []}
for n in [6, 8, 10, 12, 13, 14, 15, 16, 17, 18, 20]:
    x0 = np.tile(np.arange(n, dtype=float), (NS, 1)); null = spearman(x0, rng.permuted(x0, axis=1))
    c = {"one_0.05": np.quantile(null, 0.95), "one_0.025": np.quantile(null, 0.975),
         "two_0.05": np.quantile(np.abs(null), 0.95), "two_0.025": np.quantile(np.abs(null), 0.975)}
    row = {"n": n, "crit": {k: round(float(v), 3) for k, v in c.items()}, "power": {}}
    for rho in [0.5, 0.6, 0.7, 0.8]:
        for rel in [1.0, 0.7]:
            x = rng.standard_normal((NS, n)); y = rho * x + np.sqrt(1 - rho ** 2) * rng.standard_normal((NS, n))
            y = np.sqrt(rel) * y + np.sqrt(1 - rel) * rng.standard_normal((NS, n))
            r = spearman(x, y)
            k = "rho%.1f_rel%.1f" % (rho, rel)
            row["power"][k] = {"H6a_one_sided_conservative_0.025": round(float((r > c["one_0.025"]).mean()), 3),
                               "H6a_one_sided_optimistic_0.05": round(float((r > c["one_0.05"]).mean()), 3),
                               "H6b_two_sided_conservative_0.025": round(float((np.abs(r) > c["two_0.025"]).mean()), 3),
                               "H6b_two_sided_optimistic_0.05": round(float((np.abs(r) > c["two_0.05"]).mean()), 3)}
    out["rows"].append(row)
    p = row["power"]["rho0.8_rel0.7"]; q = row["power"]["rho0.7_rel0.7"]
    print(n, "rho0.8/rel0.7 H6b cons", p["H6b_two_sided_conservative_0.025"], "H6a cons", p["H6a_one_sided_conservative_0.025"],
          "| rho0.7 H6b cons", q["H6b_two_sided_conservative_0.025"], "H6a cons", q["H6a_one_sided_conservative_0.025"], flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
