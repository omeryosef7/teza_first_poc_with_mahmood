#!/usr/bin/env python
"""rah_power_trackb.py -- `RAH-PR-006`: the Track-B power/sensitivity analysis.

Answers, for a PAIRED behavioural design (same rows, baseline vs arm B, clustered by domain):

    given k domains x m rows/domain, baseline ASR p0, judge flip rate f and domain ICC,
    what is the minimum detectable ASR reduction at 80% power?

REUSE, NOT REWRITE. The simulator is `paired_test_noise_sensitivity.simulate()`, which already
models a paired McNemar test with per-label judge flips and is covered by 14 tests including a
positive control that asserts asymmetric noise DOES inflate type-I. This file adds only:
  (a) a bisection over `true_delta` to turn power into an MDE, and
  (b) a clustering correction, since `simulate` has no domain structure.

CLUSTERING. Rows in a domain share a stem, a demo pool and a target, so they are not independent.
The standard correction is the design effect `DEFF = 1 + (m-1)*ICC` on an equal-cluster-size design;
the simulation is run at the EFFECTIVE sample size `n_eff = k*m / DEFF`. This is a conservative,
first-order treatment -- it does not model the cluster sign test itself, which is reported
separately via its attainable exact p-floor `2/2^k_informative`.

CONSERVATIVE INPUTS ONLY (sprint plan section 20). The largest historical effect is NEVER used.
  * f -- NOT a constant. `RAH-C-004`: judge churn concentrates on rows near the 0.5 boundary
    (the repo's own FLIP_RATE_BY_CONFIDENCE: 7/11 flip at |score-0.5| < 0.05 against 5/289 at
    |score-0.5| >= 0.5), so the effective rate is a property of a population's score distribution,
    not of the judge alone. Measured with `effective_flip_rate` over each real population it runs
    0.0213 (ASR 0.0125) to 0.0851 (ASR 0.2708) -- i.e. it RISES with baseline ASR. The primary case
    interpolates the measured curve at each p0; flat 0.05 and a pessimistic 0.085 are also reported.
    The pooled corpus figure over the two PINNED byte-identical re-tests is 16/320 = 0.05, symmetric
    (8 up / 8 down, exact p = 1.0); this sprint's own fresh measurement agrees at 6/139 = 0.0432.
  * ICC = 0.09 -- the TOP of the range estimable from balanced, domain-structured populations
    (ab_base 0.030, 38dom 0.067, d10-Llama 0.090). The RBD baselines themselves cannot estimate ICC
    (every point estimate <= 0 at 4 rows/domain), so their apparent zero is NOT used. 0.19 (ab_C,
    a high-ASR arm) is reported as a pessimistic case.
  * up_bias = 0.0 -- the measured flips are symmetric. Asymmetry is reported as a stress case only.

Usage:
  python scripts/rah_power_trackb.py --out outputs/boombness/rah_power/rah_power_trackb.json
"""
from __future__ import annotations
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

SCHEMA = "RAH_POWER_TRACKB/1"

#: MEASURED effective flip rate vs that population's OWN baseline ASR, computed with
#: `paired_test_noise_sensitivity.effective_flip_rate` over each population's real score
#: distribution. `RAH-C-004`: a FLAT corpus-average flip rate is WRONG in both directions --
#: judge churn concentrates on rows near the 0.5 boundary (the repo's own
#: FLIP_RATE_BY_CONFIDENCE: 7/11 flip at |score-0.5|<0.05 vs 5/289 at |score-0.5|>=0.5), and a
#: HIGH-ASR population puts more rows there. So flip rate RISES with baseline ASR, and a design
#: does not buy free power by choosing a higher-headroom population: it buys more noise too.
MEASURED_FLIP_BY_ASR = (
    (0.0125, 0.0213),   # RBD Qwen3 x candle_missile,  n=80
    (0.0500, 0.0369),   # RBD Qwen3 x lantern_poison,  n=80
    (0.0625, 0.0289),   # RBD Llama x candle_missile,  n=80
    (0.0875, 0.0444),   # RBD Llama x lantern_poison,  n=80
    (0.1437, 0.0555),   # d10 Llama cap640,            n=160
    (0.1562, 0.0777),   # 38dom Llama cap640,          n=608
    (0.2708, 0.0851),   # carrot/bomb Llama cap640,    n=96
    (0.3125, 0.0658),   # basket_bomb Llama cap640,    n=96
)
#: Pessimistic fixed case = the largest effective rate ever measured here.
FLIP_PRIMARY, FLIP_STRESS = 0.05, 0.085


def flip_for_asr(p0):
    """Linear interpolation over MEASURED_FLIP_BY_ASR, clamped at the ends. Never extrapolated."""
    pts = MEASURED_FLIP_BY_ASR
    if p0 <= pts[0][0]:
        return pts[0][1]
    if p0 >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= p0 <= x1:
            return y0 + (y1 - y0) * (p0 - x0) / (x1 - x0)
    return pts[-1][1]


#: Estimable only on the larger balanced populations; RBD's own baselines cannot estimate it.
ICC_PRIMARY, ICC_PESSIMISTIC = 0.09, 0.19
ALPHA, REPS, POWER_TARGET = 0.05, 20000, 0.80
#: `RAH-C-006` / review F4. mde() used reps//5 internally while the artifact recorded REPS, so a
#: reader attributed sqrt(5)x more Monte-Carlo precision than existed. The simulation reps are now
#: a named constant and it is THIS value that is written to the artifact.
SIM_REPS = max(2000, REPS // 5)


def deff(m_per_domain, icc):
    """Design effect for equal cluster sizes."""
    return 1.0 + (m_per_domain - 1) * icc


def mde(sim, n_eff, p0, flip, up_bias=0.0, reps=SIM_REPS, seed=20260830):
    """Smallest |reduction| reaching POWER_TARGET, by bisection on true_delta (negative)."""
    n_eff = max(8, int(round(n_eff)))
    lo, hi = 0.0, p0                      # cannot reduce below zero
    if hi <= 0:
        return None
    # confirm the ceiling is even attainable
    top = sim(n=n_eff, base_rate=p0, true_delta=-hi, flip_a=flip, flip_b=flip,
              up_bias_b=up_bias, reps=reps, alpha=ALPHA, seed=seed)
    if top["rejection_rate"] < POWER_TARGET:
        return None                        # not even a total wipeout is detectable
    for _ in range(14):
        mid = (lo + hi) / 2.0
        r = sim(n=n_eff, base_rate=p0, true_delta=-mid, flip_a=flip, flip_b=flip,
                up_bias_b=up_bias, reps=reps, alpha=ALPHA, seed=seed)
        if r["rejection_rate"] < POWER_TARGET:
            lo = mid
        else:
            hi = mid
    return hi


def p_floor(k_informative):
    """Attainable exact two-sided p of the domain cluster sign test."""
    return 2.0 / (2 ** k_informative) if k_informative > 0 else 1.0


def main():
    import paired_test_noise_sensitivity as pn

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="outputs/boombness/rah_power/rah_power_trackb.json")
    a = ap.parse_args()
    sim = pn.simulate

    # Designs worth costing. k = domains, m = rows per domain. 20x4=80 is the RBD arm shape;
    # 20x8=160 is the RBD pooled shape; the larger ones are what a Track-B confirmation would buy.
    DESIGNS = [(20, 4), (20, 8), (20, 16), (30, 8), (38, 16)]
    # Baseline ASR values worth costing, spanning what this repo has actually measured.
    P0 = [0.05, 0.0875, 0.1375, 0.15, 0.20]

    grid, rows_out = [], []
    for k, m in DESIGNS:
        n = k * m
        for icc, icclab in ((ICC_PRIMARY, "primary"), (ICC_PESSIMISTIC, "pessimistic")):
            d = deff(m, icc)
            n_eff = n / d
            for p0 in P0:
                for flip, fl in ((flip_for_asr(p0), "measured"), (FLIP_PRIMARY, "flat0.05"),
                                 (FLIP_STRESS, "pessimistic")):
                    v = mde(sim, n_eff, p0, flip)
                    rec = {"k_domains": k, "rows_per_domain": m, "n_rows": n,
                           "icc": icc, "icc_case": icclab, "deff": d, "n_effective": n_eff,
                           "baseline_asr": p0, "flip_rate": flip, "flip_case": fl,
                           "mde_abs_reduction": v,
                           "mde_relative": (v / p0) if v is not None else None,
                           "mde_rows_of_n": (v * n) if v is not None else None,
                           "baseline_attacks_expected": p0 * n}
                    grid.append(rec)
                    if icclab == "primary" and fl == "measured":
                        rows_out.append(rec)

    print("PRIMARY CASE  (ICC=%.2f, judge flip = MEASURED per baseline ASR, symmetric, "
          "alpha=%.2f, power=%.2f)\n" % (ICC_PRIMARY, ALPHA, POWER_TARGET))
    print("%5s %4s %6s %8s %9s %11s %11s %10s" %
          ("k", "m", "n", "base_ASR", "exp_atks", "MDE_abs", "MDE_rel", "MDE_rows"))
    for r in rows_out:
        v = r["mde_abs_reduction"]
        print("%5d %4d %6d %8.4f %9.1f %11s %11s %10s" %
              (r["k_domains"], r["rows_per_domain"], r["n_rows"], r["baseline_asr"],
               r["baseline_attacks_expected"],
               "n/a" if v is None else "%.4f" % v,
               "n/a" if v is None else "%.2f" % (v / r["baseline_asr"]),
               "n/a" if v is None else "%.1f" % (v * r["n_rows"])))

    print("\nCLUSTER SIGN TEST attainable exact p-floor, 2/2^k_informative:")
    floors = {ki: p_floor(ki) for ki in (4, 5, 6, 7, 8, 10, 12, 20)}
    for ki, f in floors.items():
        print("   k_informative=%-3d floor=%.6f %s" % (ki, f, "" if f <= ALPHA else "  <-- ABOVE alpha"))

    out = {"schema": SCHEMA,
           "inputs": {"flip_rate_flat": FLIP_PRIMARY, "flip_rate_pessimistic": FLIP_STRESS,
                      "flip_rate_measured_by_asr": [list(t) for t in MEASURED_FLIP_BY_ASR],
                      "flip_symmetric": True, "icc_primary": ICC_PRIMARY,
                      "icc_pessimistic": ICC_PESSIMISTIC, "alpha": ALPHA,
                      "power_target": POWER_TARGET, "reps_per_simulation": SIM_REPS,
                      "reps_note": "each power evaluation uses reps_per_simulation; at power 0.80 the per-evaluation SE is sqrt(.8*.2/reps). MDE is reported to 4 dp for reproducibility, NOT because it is resolved to 4 dp.",
                      "mde_bisection_steps": 14, "mde_seed": 20260830,
                      "simulator": "paired_test_noise_sensitivity.simulate (reused, not reimplemented)",
                      "clustering": "design effect DEFF = 1 + (m-1)*ICC applied as n_eff = n/DEFF",
                      "provenance": {
                          "flip_rate": "16/320 pooled over the two PINNED byte-identical judge "
                                       "re-tests; symmetric 8 up / 8 down (exact p=1.0). This "
                                       "sprint's own fresh measurement agrees: 6/139 = 0.0432.",
                          "icc": "estimable only on balanced domain-structured populations: "
                                 "ab_base 0.0295, 38dom 0.0674, d10-Llama 0.0898. RBD's own "
                                 "baselines cannot estimate ICC (all point estimates <= 0 at 4 "
                                 "rows/domain) so their apparent zero is NOT used."}},
           "cluster_sign_test_p_floor": {str(k): v for k, v in floors.items()},
           "grid": grid}
    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)), exist_ok=True)
    with open(os.path.join(ROOT, a.out), "w") as f:
        json.dump(out, f, indent=1)
    print("\n-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
