#!/usr/bin/env python3
"""P6 power for the H6a INTERSECTION-UNION rule (PREREG_P6_AMENDMENT_3): H6a passes only if the one-sided permutation
Spearman(probe, z_f) exceeds its alpha=0.05 critical value for ALL three z families f in {pooled, RAND-only, SHUF-only}.
Model (same as p6_power.py): latent s = rho*x + sqrt(1-rho^2)*e; observed y_f = sqrt(rel)*s + sqrt(1-rel)*n_f with
n_f = sqrt(c)*u + sqrt(1-c)*v_f — c = fraction of the outcome's measurement noise SHARED across the three families
(unknown a priori; the families share the candidate and overlap in controls, so c is plausibly high). c=1 reduces to
the single-test power. Seed 20261014b."""
import json, sys
import numpy as np
rng = np.random.default_rng(202610142)
NS = 20000


def spearman(a, b):
    ra = a.argsort(-1).argsort(-1).astype(float); rb = b.argsort(-1).argsort(-1).astype(float)
    ra -= ra.mean(-1, keepdims=True); rb -= rb.mean(-1, keepdims=True)
    return (ra * rb).sum(-1) / np.sqrt((ra ** 2).sum(-1) * (rb ** 2).sum(-1))


out = {"model": __doc__, "n_sim": NS, "rows": []}
for n in [12, 15]:
    x0 = np.tile(np.arange(n, dtype=float), (NS, 1)); crit = float(np.quantile(spearman(x0, rng.permuted(x0, axis=1)), 0.95))
    row = {"n": n, "crit_one_sided_0.05": round(crit, 3), "power": {}}
    for rho in [0.6, 0.7, 0.8]:
        for rel in [0.7]:
            for c in [1.0, 0.9, 0.7, 0.5]:
                x = rng.standard_normal((NS, n)); s = rho * x + np.sqrt(1 - rho ** 2) * rng.standard_normal((NS, n))
                u = rng.standard_normal((NS, n))
                ok = np.ones(NS, bool); single = None
                for f in range(3):
                    nf = np.sqrt(c) * u + np.sqrt(1 - c) * rng.standard_normal((NS, n))
                    y = np.sqrt(rel) * s + np.sqrt(1 - rel) * nf
                    hit = spearman(x, y) > crit
                    single = hit.mean() if single is None else single
                    ok &= hit
                row["power"][f"rho{rho}_rel{rel}_shared{c}"] = {"single_family": round(float(single), 3), "IUT_all_three": round(float(ok.mean()), 3)}
    out["rows"].append(row)
    print(n, {k: v for k, v in row["power"].items() if "rho0.7" in k or "rho0.8" in k}, flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
