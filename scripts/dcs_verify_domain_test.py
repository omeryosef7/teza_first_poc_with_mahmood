#!/usr/bin/env python
"""dcs_verify_domain_test.py -- audit of `scripts/cds_domain_test.py`, which computes
`DCS-PR-024a`'s PRIMARY: the exact paired domain sign test over 116 domains.

WRITTEN WHILE THE JUDGE WAS RUNNING (arm 1 of 5), so it is fixed before the numbers it will validate
exist. The script it audits came from the CDS sprint and had never been checked here, despite being
the thing that decides whether `B-009` resolves.

⚠ CHECK 4 CARRIES A LESSON. On first writing, the ICC check FAILED at every true value -- and the
estimator was fine. My simulator called `betavariate()` INSIDE the row comprehension, giving every
ROW its own cluster probability, which is ICC = 0 data by construction. The estimator was correctly
reporting ~0. That is the third audit in this phase to fail on its own instrument (`A-005`'s regex,
`C-036`'s collision rule, this) -- so the simulator draws ONE p_d per DOMAIN, and the fixed version
is kept here precisely so the trap is visible rather than silently corrected.

Stdlib + optional scipy.
"""
from __future__ import annotations
import importlib.util, os, random, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    spec = importlib.util.spec_from_file_location(
        "c", os.path.join(ROOT, "scripts", "cds_domain_test.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sim_clustered(icc, k=116, m=10, p0=0.4):
    """ONE Beta draw per DOMAIN -- that draw IS the cluster. Drawing per row destroys the
    clustering and yields ICC 0, which is the bug this docstring exists to prevent."""
    a, b = p0 * (1 / icc - 1), (1 - p0) * (1 / icc - 1)
    out = {}
    for i in range(k):
        p = random.betavariate(a, b)
        out[f"d{i}"] = [1 if random.random() < p else 0 for _ in range(m)]
    return out


def main() -> None:
    c = load()
    fails: list[str] = []

    try:
        from scipy.stats import binomtest
        worst = max(abs(c._binom_cdf_two_sided(x, n) - binomtest(x, n, 0.5).pvalue)
                    for n in range(1, 60) for x in range(0, n + 1))
        print(f"1. exact two-sided binomial vs scipy, all (x, n<=59): worst |diff| = {worst:.2e}")
        if worst > 1e-12:
            fails.append(f"binomial disagrees with scipy by {worst:.2e}")
    except ImportError:
        print("1. vs scipy: SKIPPED (scipy not installed)")

    bad = [k for k in range(1, 40)
           if abs(c.p_floor(k) - c._binom_cdf_two_sided(0, k)) > 1e-15]
    print(f"2. p_floor equals p(unanimous split) for k=1..39: {'OK' if not bad else 'FAIL'}")
    if bad:
        fails.append("p_floor is not the attainable minimum")

    hi, lo = c.p_floor(116), c.p_floor(4)
    print(f"3. CAPABLE flag: k=116 floor={hi:.3e} -> {hi <= c.ALPHA}; "
          f"k=4 floor={lo:.3f} -> {lo <= c.ALPHA}")
    if not (hi <= c.ALPHA and lo > c.ALPHA):
        fails.append("CAPABLE misclassifies a known-capable or known-incapable design")

    print("4. ICC recovery (simulator clusters per DOMAIN -- see the docstring):")
    for true in (0.05, 0.16, 0.40, 0.60):
        random.seed(7)
        est = st.mean([c.icc_anova(sim_clustered(true)) for _ in range(40)])
        ok = abs(est - true) < 0.05
        print(f"     true={true:.2f} -> estimated={est:.3f}  {'OK' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"ICC off at true={true}: got {est:.3f}")

    doms = {"a": [10, 3, 1], "b": [10, 2, 2], "c": [10, 1, 3]}
    dn = sum(1 for d in doms.values() if d[1] > d[2])
    up = sum(1 for d in doms.values() if d[2] > d[1])
    print(f"5. a TIED domain is not informative: k_informative={dn + up} (must be 2)")
    if dn + up != 2:
        fails.append("a tied domain is counted as informative")

    print()
    if fails:
        print("VERIFY: FAIL")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("VERIFY: PASS")


if __name__ == "__main__":
    main()
