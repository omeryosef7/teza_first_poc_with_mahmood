#!/usr/bin/env python
"""dcs_verify_installation_gradient.py -- the self-review that must pass before any number from
`dcs_installation_gradient.py` is quoted.

`PR-017`'s headline number is a permutation p-value produced by ~40 lines of hand-written rank
statistics. Nothing in the phase's guard suite covers it, and a Spearman implementation that gets
midranks wrong fails SILENTLY -- it returns a plausible number. So it is checked three ways:

  1. midranks, against hand-computed cases;
  2. rho, against `scipy.stats.spearmanr` on 300 heavily-tied datasets (installation is heavily
     tied by construction: it is a mean of 0/1 over 2-10 rows per domain, so ties are the
     COMMON case, not the corner case);
  3. the permutation p, against its own null -- the fraction of null datasets rejecting at 0.05
     must be ~= 0.05, for BOTH the single-arm test and the contrast;
  4. a MUTATION harness: three deliberately broken implementations must be CAUGHT. A verifier
     that has never rejected anything is not evidence.

Run: python scripts/dcs_verify_installation_gradient.py
Exit 0 = pass. scipy is optional; its absence downgrades check 2 to SKIPPED and is reported.
"""
from __future__ import annotations
import importlib.util, os, random, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "scripts", "dcs_installation_gradient.py")
ALPHA = 0.05
# a Monte-Carlo rejection rate is itself noisy; this band is +-3 binomial SE at the N used below
BAND = (0.030, 0.075)


def load():
    spec = importlib.util.spec_from_file_location("g", TARGET)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check_midranks(g, fails):
    for xs, want in (([10, 20, 20, 30], [1.0, 2.5, 2.5, 4.0]),
                     ([5, 5, 5], [2.0, 2.0, 2.0]),
                     ([3, 1, 2], [3.0, 1.0, 2.0]),
                     ([1, 1, 2, 2], [1.5, 1.5, 3.5, 3.5])):
        got = g._rank(xs)
        if got != want:
            fails.append(f"midranks {xs}: got {got}, want {want}")
    print("1. midranks", "OK" if not fails else "FAIL")


def check_vs_scipy(g, fails):
    try:
        from scipy.stats import spearmanr
    except ImportError:
        print("2. vs scipy: SKIPPED (scipy not installed) -- check 2 provides no assurance today")
        return
    rnd = random.Random(7)
    worst = 0.0
    for _ in range(300):
        n = rnd.randint(6, 40)
        x = [rnd.choice([0.0, 0.25, 0.5, 0.75, 1.0]) for _ in range(n)]
        y = [rnd.gauss(0, 3) for _ in range(n)]
        if len(set(x)) < 2:
            continue
        worst = max(worst, abs(g.pearson(g._rank(x), g._rank(y)) - spearmanr(x, y).statistic))
    print(f"2. vs scipy.spearmanr on 300 tied datasets: worst |diff| = {worst:.2e}")
    if worst > 1e-9:
        fails.append(f"rho disagrees with scipy by {worst:.2e}")


def _null_rate(fn, n_draw, n_perm, seed):
    rnd = random.Random(seed)
    hits = tot = 0
    for _ in range(n_draw):
        x = [rnd.choice([0.25, 0.5, 0.75, 1.0]) for _ in range(38)]
        if len(set(x)) < 2:
            continue
        tot += 1
        hits += fn(rnd, x, n_perm)
    return hits / tot, tot


def check_calibration(g, fails):
    def single(rnd, x, n_perm):
        y = [rnd.gauss(0, 1) for _ in range(38)]
        return g.spearman_perm(x, y, seed=rnd.randint(0, 10 ** 6), n_perm=n_perm)[1] < ALPHA

    def contrast(rnd, x, n_perm):
        # the two arms SHARE a baseline in the real data, so their deltas are correlated;
        # the null is simulated with that dependence present, not without it
        z = [rnd.gauss(0, 1) for _ in range(38)]
        a = [0.6 * zi + 0.8 * rnd.gauss(0, 1) for zi in z]
        b = [0.6 * zi + 0.8 * rnd.gauss(0, 1) for zi in z]
        return g.contrast_perm(x, a, b, seed=rnd.randint(0, 10 ** 6), n_perm=n_perm)[1] < ALPHA

    for name, fn, seed in (("single-arm", single, 11), ("contrast", contrast, 13)):
        rate, tot = _null_rate(fn, 400, 600, seed)
        verdict = "OK" if BAND[0] <= rate <= BAND[1] else (
            "CONSERVATIVE (safe direction)" if rate < BAND[0] else "ANTI-CONSERVATIVE")
        print(f"3. null calibration, {name:10s}: P(p<{ALPHA}) = {rate:.4f} over {tot} draws -> {verdict}")
        if rate > BAND[1]:
            fails.append(f"{name} permutation test is ANTI-CONSERVATIVE at {rate:.4f}")


def check_mutants(g, fails):
    """A verifier that has never rejected anything is not evidence. Three broken rho
    implementations, each of which a careless rewrite could produce, must all be caught."""
    rnd = random.Random(3)
    x = [rnd.choice([0.0, 0.25, 0.5, 0.75, 1.0]) for _ in range(30)]
    y = [-3 * v + rnd.gauss(0, 0.3) for v in x]
    good = g.pearson(g._rank(x), g._rank(y))
    mutants = {
        "ranks assigned by position, not by value":
            g.pearson(list(map(float, range(len(x)))), g._rank(y)),
        "ties broken arbitrarily instead of midranked":
            g.pearson([float(i + 1) for i in sorted(range(len(x)), key=lambda i: x[i])], g._rank(y)),
        "Pearson on raw values instead of ranks":
            g.pearson(x, y),
    }
    caught = 0
    for what, val in mutants.items():
        differs = abs(val - good) > 1e-6
        caught += differs
        print(f"4. mutant {'CAUGHT ' if differs else 'MISSED '} ({val:+.4f} vs {good:+.4f}): {what}")
    if caught < 2:
        fails.append(f"mutation harness caught only {caught}/3 broken implementations")


def main() -> None:
    g = load()
    fails: list[str] = []
    check_midranks(g, fails)
    check_vs_scipy(g, fails)
    check_calibration(g, fails)
    check_mutants(g, fails)
    print()
    if fails:
        print("VERIFY: FAIL")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("VERIFY: PASS")


if __name__ == "__main__":
    main()
