#!/usr/bin/env python
"""cds_power_domain.py -- `CDS-PR-001`'s capability calculation, at the TRUE independence unit.

WHY THIS EXISTS AND WHAT IT DOES NOT REPLACE.
`scripts/rah_power_trackb.py` answers the same question at the ROW level and corrects for
clustering with a design effect (`n_eff = k*m / (1 + (m-1)*ICC)`) applied to a row-level McNemar.
That is the repo's validated conservative bound and it is REUSED here unchanged -- this file does
not reimplement it and does not disagree with it.

What it adds is the capability of the test this sprint actually pre-registers as PRIMARY: an exact
paired SIGN TEST over DOMAIN-LEVEL attack counts, k domains, which is the estimator `PR-1` named as
the independence unit and the one `C-95` showed can be UNINFORMATIVE BY CONSTRUCTION when
`k_informative` is small (its attainable two-sided p-floor is `2 / 2**k_informative`). A design can
be capable at the row level and incapable at the domain level, and the reverse; both are reported
and NEITHER is allowed to override the other.

NOISE MODEL. Identical in shape to `paired_test_noise_sensitivity.simulate`: symmetric per-label
judge flips at rate `f` on BOTH arms, so a wipeout must beat the arm's own false-positive rate.
`f` is taken from `rah_power_trackb.flip_for_asr` -- the MEASURED curve, never an assumed constant.

CLUSTER MODEL. Each domain d draws its own attack probability `p_d ~ Beta(a, b)` with
`E[p_d] = p0` and `a + b = 1/ICC - 1`, which gives exactly the intraclass correlation `ICC` for
Bernoulli draws within a cluster. The intervention multiplies the domain's rate by `(1 - eff)`, so
`eff = 1.0` is a total wipeout -- the effect size C7 actually reports on Qwen3 (5/5, 7/7, 4/4).

READ THE `NONE`s THE SAME WAY `RAH3` DID: not detectable AT ALL, including a 100 % wipeout.
"""
from __future__ import annotations
import argparse, json, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from paired_test_noise_sensitivity import exact_two_sided_binomial  # noqa: E402
import rah_power_trackb as RP  # noqa: E402

SCHEMA = "CDS_POWER_DOMAIN/1"
ALPHA = 0.05
POWER_TARGET = 0.80


def _beta_ab(p0, icc):
    """Beta(a, b) with mean p0 and within-cluster ICC = 1/(a+b+1)."""
    s = 1.0 / icc - 1.0
    return p0 * s, (1.0 - p0) * s


def simulate_domain(k, m, p0, icc, eff, flip, reps=2000, seed=20260901, alpha=ALPHA):
    """Power of (i) the exact paired domain SIGN TEST and (ii) the row-level McNemar."""
    rng = random.Random(seed)
    a, b = _beta_ab(p0, icc)
    rej_sign = rej_mcn = 0
    kinf_tot = atk_tot = 0
    for _ in range(reps):
        up_d = dn_d = 0
        up_r = dn_r = 0
        atk = 0
        for _d in range(k):
            p_d = rng.betavariate(a, b)
            q_d = p_d * (1.0 - eff)
            db = 0
            for _i in range(m):
                at = rng.random() < p_d
                bt = rng.random() < q_d
                ao = (not at) if rng.random() < flip else at
                bo = (not bt) if rng.random() < flip else bt
                atk += int(ao)
                if ao and not bo:
                    dn_r += 1; db += 1
                elif bo and not ao:
                    up_r += 1; db -= 1
            if db > 0:
                dn_d += 1
            elif db < 0:
                up_d += 1
        kinf_tot += (up_d + dn_d)
        atk_tot += atk
        if up_d + dn_d > 0 and exact_two_sided_binomial(up_d, up_d + dn_d) <= alpha:
            rej_sign += 1
        if up_r + dn_r > 0 and exact_two_sided_binomial(up_r, up_r + dn_r) <= alpha:
            rej_mcn += 1
    return {"k": k, "m": m, "n": k * m, "p0": p0, "icc": icc, "eff": eff, "flip": flip,
            "reps": reps, "power_domain_sign": rej_sign / reps,
            "power_row_mcnemar": rej_mcn / reps,
            "mean_k_informative": kinf_tot / reps,
            "mean_baseline_attacks": atk_tot / reps,
            "p_floor_at_mean_kinf": 2.0 / (2 ** int(round(kinf_tot / reps)))
            if kinf_tot / reps >= 1 else 1.0}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--k", type=int, default=38)
    ap.add_argument("--m", default="4,10")
    ap.add_argument("--p0", default="0.05,0.075,0.10,0.1562,0.20")
    ap.add_argument("--icc", default="0.067,0.09,0.19,0.45")
    ap.add_argument("--eff", default="1.0,0.75")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--out", default="outputs/boombness/cds_power/cds_power_domain.json")
    a = ap.parse_args()
    ms = [int(x) for x in a.m.split(",")]
    p0s = [float(x) for x in a.p0.split(",")]
    iccs = [float(x) for x in a.icc.split(",")]
    effs = [float(x) for x in a.eff.split(",")]
    out = []
    print("%3s %3s %6s %7s %6s %5s %7s %10s %10s %8s %9s" %
          ("k", "m", "n", "p0", "icc", "eff", "flip", "pow_SIGN", "pow_ROW", "k_inf", "base_atk"))
    for m in ms:
        for p0 in p0s:
            f = RP.flip_for_asr(p0)
            for icc in iccs:
                for eff in effs:
                    r = simulate_domain(a.k, m, p0, icc, eff, f, reps=a.reps)
                    out.append(r)
                    print("%3d %3d %6d %7.4f %6.3f %5.2f %7.4f %10.3f %10.3f %8.1f %9.1f" %
                          (a.k, m, a.k * m, p0, icc, eff, f, r["power_domain_sign"],
                           r["power_row_mcnemar"], r["mean_k_informative"],
                           r["mean_baseline_attacks"]))
    p = os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump({"schema": SCHEMA, "alpha": ALPHA, "power_target": POWER_TARGET,
               "flip_source": "rah_power_trackb.flip_for_asr (MEASURED curve)",
               "grid": out}, open(p, "w"), indent=1)
    print("\nwrote", a.out)


if __name__ == "__main__":
    main()
