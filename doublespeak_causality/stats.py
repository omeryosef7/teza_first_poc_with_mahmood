"""Pure-Python statistics module for paired-sample analysis.

Generic numerical infrastructure for a research analysis pipeline. Contains no
domain-specific logic -- only math on numbers / arrays.

Dependencies: numpy, plus math/typing from the standard library. No scipy.
All randomized procedures accept a seed or numpy Generator and are deterministic
given that seed.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Union

import numpy as np

ArrayLike = Union[Sequence[float], np.ndarray]
SeedLike = Union[int, np.random.Generator, None]


def _as_rng(seed: SeedLike) -> np.random.Generator:
    """Coerce an int / Generator / None into a numpy Generator."""
    if isinstance(seed, np.random.Generator):
        return seed
    return np.random.default_rng(seed)


def _as_1d(a: ArrayLike, name: str) -> np.ndarray:
    """Return a contiguous 1-D float64 array or raise on bad shape."""
    arr = np.asarray(a, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be 1-dimensional, got shape {arr.shape}")
    return arr


def _paired_diffs(x: ArrayLike, y: ArrayLike) -> np.ndarray:
    """Validate two equal-length paired arrays and return their differences."""
    xa = _as_1d(x, "x")
    ya = _as_1d(y, "y")
    if xa.shape[0] != ya.shape[0]:
        raise ValueError(f"x and y must have equal length, got {xa.shape[0]} and {ya.shape[0]}")
    if xa.shape[0] == 0:
        raise ValueError("x and y must be non-empty")
    return xa - ya


def paired_bootstrap_ci(
    x: ArrayLike,
    y: ArrayLike,
    n_boot: int = 10000,
    alpha: float = 0.05,
    seed: SeedLike = 0,
) -> Dict[str, float]:
    """Bootstrap confidence interval of the paired mean difference.

    Resamples the paired differences ``d = x - y`` with replacement ``n_boot``
    times and takes percentile bounds of the resampled means.

    Args:
        x: First paired sample, 1-D and same length as ``y``.
        y: Second paired sample, 1-D and same length as ``x``.
        n_boot: Number of bootstrap resamples.
        alpha: Two-sided significance level; the CI covers ``1 - alpha``.
        seed: Int seed or numpy Generator for reproducibility.

    Returns:
        dict with keys ``'mean_diff'`` (observed mean of ``d``), ``'lo'`` and
        ``'hi'`` (the ``alpha/2`` and ``1 - alpha/2`` percentile bounds).
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    if n_boot < 1:
        raise ValueError("n_boot must be >= 1")
    d = _paired_diffs(x, y)
    n = d.shape[0]
    rng = _as_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boot_means = d[idx].mean(axis=1)
    lo = float(np.percentile(boot_means, 100.0 * (alpha / 2.0)))
    hi = float(np.percentile(boot_means, 100.0 * (1.0 - alpha / 2.0)))
    return {"mean_diff": float(d.mean()), "lo": lo, "hi": hi}


def _binom_pmf(k: int, n: int, p: float) -> float:
    """Binomial probability mass P(X = k) for X ~ Binomial(n, p)."""
    return math.comb(n, k) * (p ** k) * ((1.0 - p) ** (n - k))


def mcnemar_test(b: int, c: int) -> Dict[str, float]:
    """McNemar's test for paired binary outcomes from discordant counts.

    ``b`` and ``c`` are the two off-diagonal (discordant) cell counts of the
    2x2 paired contingency table. For small ``b + c`` (<= 25) an exact
    two-sided binomial p-value is used; otherwise the chi-square statistic with
    continuity correction is used against a chi-square(1) reference.

    Args:
        b: Count of pairs discordant in one direction.
        c: Count of pairs discordant in the other direction.

    Returns:
        dict with keys ``'stat'`` (test statistic; the chi-square value, or the
        smaller discordant count in the exact branch) and ``'p'`` (two-sided
        p-value).
    """
    b = int(b)
    c = int(c)
    if b < 0 or c < 0:
        raise ValueError("b and c must be non-negative")
    n = b + c
    if n == 0:
        # No discordant pairs: no evidence of difference.
        return {"stat": 0.0, "p": 1.0}

    if n <= 25:
        # Exact two-sided binomial test at p = 0.5.
        k = min(b, c)
        tail = sum(_binom_pmf(i, n, 0.5) for i in range(0, k + 1))
        p = min(1.0, 2.0 * tail)
        return {"stat": float(k), "p": float(p)}

    # Chi-square with continuity correction; survival function of chi-square(1)
    # is available in closed form via the error function.
    stat = (abs(b - c) - 1.0) ** 2 / float(n)
    # P(chi2_1 > stat) = erfc(sqrt(stat / 2))
    p = math.erfc(math.sqrt(stat / 2.0))
    return {"stat": float(stat), "p": float(p)}


def permutation_test_paired(
    x: ArrayLike,
    y: ArrayLike,
    n_perm: int = 10000,
    seed: SeedLike = 0,
    alternative: str = "two-sided",
) -> Dict[str, float]:
    """Sign-flip permutation test on paired differences.

    Under the null of exchangeable signs, each paired difference's sign is
    randomly flipped; the observed statistic is the mean difference. The
    p-value is computed with a ``+1`` add-one correction in numerator and
    denominator (never returns exactly 0).

    Args:
        x: First paired sample.
        y: Second paired sample.
        n_perm: Number of random sign-flip permutations.
        seed: Int seed or numpy Generator.
        alternative: ``'two-sided'``, ``'greater'`` (mean diff > 0), or
            ``'less'`` (mean diff < 0).

    Returns:
        dict with keys ``'observed'`` (mean of ``x - y``) and ``'p'``.
    """
    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError("alternative must be 'two-sided', 'greater', or 'less'")
    if n_perm < 1:
        raise ValueError("n_perm must be >= 1")
    d = _paired_diffs(x, y)
    n = d.shape[0]
    observed = float(d.mean())
    rng = _as_rng(seed)
    signs = rng.integers(0, 2, size=(n_perm, n)) * 2 - 1  # values in {-1, +1}
    perm_stats = (signs * d).mean(axis=1)

    if alternative == "greater":
        count = int(np.sum(perm_stats >= observed))
    elif alternative == "less":
        count = int(np.sum(perm_stats <= observed))
    else:
        count = int(np.sum(np.abs(perm_stats) >= abs(observed)))

    p = (count + 1) / (n_perm + 1)
    return {"observed": observed, "p": float(p)}


def paired_cohens_d(x: ArrayLike, y: ArrayLike) -> float:
    """Cohen's d for paired samples: mean(d) / std(d), with d = x - y.

    Uses the sample standard deviation (ddof=1) of the differences. Returns a
    float; ``nan`` if the differences have zero variance and non-zero mean is
    represented as +/- inf, while an all-zero difference yields ``nan``.

    Args:
        x: First paired sample.
        y: Second paired sample.

    Returns:
        The paired Cohen's d effect size.
    """
    d = _paired_diffs(x, y)
    if d.shape[0] < 2:
        raise ValueError("paired Cohen's d requires at least 2 pairs")
    sd = float(np.std(d, ddof=1))
    mean = float(d.mean())
    if sd == 0.0:
        if mean == 0.0:
            return float("nan")
        return math.inf if mean > 0 else -math.inf
    return mean / sd


def holm_bonferroni(pvals: ArrayLike) -> List[float]:
    """Holm-Bonferroni step-down adjustment of p-values.

    Returns adjusted p-values in the same order as the input. Adjusted values
    are enforced monotone non-decreasing along the sorted order and clipped to
    ``[0, 1]``.

    Args:
        pvals: Sequence of raw p-values in ``[0, 1]``.

    Returns:
        List of adjusted p-values aligned to the input order.
    """
    p = _as_1d(pvals, "pvals")
    m = p.shape[0]
    if m == 0:
        return []
    if np.any(p < 0.0) or np.any(p > 1.0):
        raise ValueError("p-values must lie in [0, 1]")

    order = np.argsort(p, kind="stable")
    sorted_p = p[order]
    adj_sorted = np.empty(m, dtype=np.float64)
    running_max = 0.0
    for i in range(m):
        val = (m - i) * sorted_p[i]
        val = min(val, 1.0)
        running_max = max(running_max, val)
        adj_sorted[i] = running_max

    adjusted = np.empty(m, dtype=np.float64)
    adjusted[order] = adj_sorted
    return [float(v) for v in adjusted]


def rank_biserial_paired(x: ArrayLike, y: ArrayLike) -> float:
    """Matched-pairs rank-biserial correlation effect size.

    Computes the Wilcoxon signed-rank based effect size
    ``r = (W+ - W-) / sum(ranks)``, where non-zero absolute differences are
    rank-averaged for ties and zero differences are dropped. Ranges in
    ``[-1, 1]``; positive means ``x > y`` predominates.

    Args:
        x: First paired sample.
        y: Second paired sample.

    Returns:
        The matched-pairs rank-biserial correlation. Returns ``0.0`` if all
        differences are zero.
    """
    d = _paired_diffs(x, y)
    nz = d[d != 0.0]
    if nz.shape[0] == 0:
        return 0.0
    abs_d = np.abs(nz)
    ranks = _average_ranks(abs_d)
    total = float(ranks.sum())
    if total == 0.0:
        return 0.0
    w_plus = float(ranks[nz > 0.0].sum())
    w_minus = float(ranks[nz < 0.0].sum())
    return (w_plus - w_minus) / total


def _average_ranks(a: np.ndarray) -> np.ndarray:
    """Return 1-based ranks of ``a`` with ties assigned their average rank."""
    n = a.shape[0]
    order = np.argsort(a, kind="stable")
    sorted_a = a[order]
    ranks_sorted = np.empty(n, dtype=np.float64)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        # positions i..j (0-based) share value -> average of 1-based ranks
        avg = (i + j) / 2.0 + 1.0
        ranks_sorted[i : j + 1] = avg
        i = j + 1
    ranks = np.empty(n, dtype=np.float64)
    ranks[order] = ranks_sorted
    return ranks


if __name__ == "__main__":
    # ------------------------------------------------------------------
    # Self-test: tiny hardcoded arrays, deterministic seeds, sanity asserts.
    # ------------------------------------------------------------------
    xa = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    ya = [4.0, 6.0, 5.0, 9.0, 7.0, 8.0]  # x - y = [1, 0, 2, -1, 2, 2]

    # 1. paired_bootstrap_ci
    ci = paired_bootstrap_ci(xa, ya, n_boot=2000, seed=0)
    assert set(ci) == {"mean_diff", "lo", "hi"}
    assert ci["lo"] <= ci["mean_diff"] <= ci["hi"]
    assert abs(ci["mean_diff"] - 1.0) < 1e-9
    # determinism
    ci2 = paired_bootstrap_ci(xa, ya, n_boot=2000, seed=0)
    assert ci == ci2
    print(f"PASS paired_bootstrap_ci: mean_diff={ci['mean_diff']:.4f} "
          f"CI=[{ci['lo']:.4f}, {ci['hi']:.4f}]")

    # 2. mcnemar_test -- exact branch and chi-square branch
    m_exact = mcnemar_test(1, 9)
    assert 0.0 <= m_exact["p"] <= 1.0
    # exact two-sided binomial for (b=1,c=9): 2 * P(X<=1), X~Bin(10,0.5)
    expected = min(1.0, 2.0 * (_binom_pmf(0, 10, 0.5) + _binom_pmf(1, 10, 0.5)))
    assert abs(m_exact["p"] - expected) < 1e-12
    m_chi = mcnemar_test(10, 30)  # n=40 > 25 -> chi-square branch
    assert 0.0 <= m_chi["p"] <= 1.0
    m_zero = mcnemar_test(0, 0)
    assert m_zero["p"] == 1.0
    print(f"PASS mcnemar_test: exact p={m_exact['p']:.6f} "
          f"chi2 stat={m_chi['stat']:.4f} p={m_chi['p']:.6f}")

    # 3. permutation_test_paired
    for alt in ("two-sided", "greater", "less"):
        pt = permutation_test_paired(xa, ya, n_perm=3000, seed=1, alternative=alt)
        assert 0.0 <= pt["p"] <= 1.0, f"p out of range for {alt}"
        assert abs(pt["observed"] - 1.0) < 1e-9
    pt2 = permutation_test_paired(xa, ya, n_perm=3000, seed=1)
    assert permutation_test_paired(xa, ya, n_perm=3000, seed=1) == pt2  # deterministic
    print(f"PASS permutation_test_paired: observed={pt2['observed']:.4f} "
          f"p={pt2['p']:.6f}")

    # 4. paired_cohens_d
    dval = paired_cohens_d(xa, ya)
    assert math.isfinite(dval)
    manual = np.mean(np.array(xa) - np.array(ya)) / np.std(
        np.array(xa) - np.array(ya), ddof=1)
    assert abs(dval - manual) < 1e-12
    print(f"PASS paired_cohens_d: d={dval:.4f}")

    # 5. holm_bonferroni
    raw = [0.01, 0.04, 0.03, 0.005]
    adj = holm_bonferroni(raw)
    assert len(adj) == len(raw)
    assert all(0.0 <= v <= 1.0 for v in adj)
    # monotonic along sorted-by-raw order
    srt = sorted(zip(raw, adj))
    adj_in_order = [a for _, a in srt]
    assert all(adj_in_order[i] <= adj_in_order[i + 1] + 1e-12
               for i in range(len(adj_in_order) - 1)), "holm not monotonic"
    # each adjusted >= its raw
    assert all(a >= r - 1e-12 for r, a in zip(raw, adj))
    print(f"PASS holm_bonferroni: adjusted={[round(v, 4) for v in adj]}")

    # 6. rank_biserial_paired
    rb = rank_biserial_paired(xa, ya)
    assert -1.0 <= rb <= 1.0
    # more positive than negative diffs -> positive effect
    assert rb > 0.0
    assert rank_biserial_paired([1.0, 2.0], [1.0, 2.0]) == 0.0  # all-zero diffs
    print(f"PASS rank_biserial_paired: r={rb:.4f}")

    print("ALL PASS")
