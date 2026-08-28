"""clustered_stats.py — the rank statistics behind the Phase 7 gate decision, with their limits.

WHY THIS IS A MODULE AND NOT A HEREDOC. §12.23/§12.24 closed the Phase 7 gate on a partial
correlation with a cluster-bootstrap interval. Those numbers were first computed in inline scripts,
and one of them was WRONG in a way that supported the conclusion already written:

  ⛔ THE TIE BUG. A rank function using `argsort` positions assigns 1..n and breaks ties by
     arbitrary order. The outcome here is BINARY -- 226 zeros and 62 ones in 288 rows -- so almost
     every rank was arbitrary. It returned partial rho = +0.0942 where the correct value is +0.1924.
     It was caught only because a second computation of the same quantity disagreed.

Every function here is therefore pinned by tests, including a test that fails on exactly that bug.

TWO LIMITS THAT ARE PROPERTIES OF THE DESIGN, NOT OF THE CODE, both documented on the functions:

  * `cluster_permutation_p` is DEGENERATE for any variable balanced by construction within every
    cluster. Permuting outcomes between clusters preserves that variable's relationship to the
    outcome exactly, so it returns p ~ 1.0 regardless of the true association. This is why
    `n_examples` scored p=1.0000 in §12.23 -- an artifact, not a finding.
  * `cluster_bootstrap_ci` under-covers below roughly 30 clusters. This sprint's designs have 18,
    so intervals from it are optimistic and must be quoted that way.

Pure arithmetic. No model, no artifacts, no network.
"""
from __future__ import annotations

import random
from typing import Callable, Sequence


def ranks(values: Sequence[float]) -> list[float]:
    """Average ranks, ties shared.

    ⛔ Ties MUST be averaged. The `argsort`-position version of this function broke ties by
    arbitrary order and, on a binary outcome, silently randomised most of the ranks.
    """
    idx = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and values[idx[j + 1]] == values[idx[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            out[idx[k]] = avg
        i = j + 1
    return out


def _pearson(x: Sequence[float], y: Sequence[float]) -> float:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = sum((a - mx) ** 2 for a in x) ** 0.5
    dy = sum((b - my) ** 2 for b in y) ** 0.5
    return num / (dx * dy) if dx * dy else float("nan")


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) < 3:
        return float("nan")
    return _pearson(ranks(x), ranks(y))


def partial_spearman(x: Sequence[float], y: Sequence[float], z: Sequence[float]) -> float:
    """Partial rank correlation of x and y controlling one variable z.

    Kept alongside the multi-control version deliberately: the two agree on a single control, and
    that agreement is what exposed the tie bug. `test_the_two_partial_implementations_agree` pins it.
    """
    rxy, rxz, ryz = spearman(x, y), spearman(x, z), spearman(y, z)
    denom = ((1 - rxz ** 2) * (1 - ryz ** 2)) ** 0.5
    return (rxy - rxz * ryz) / denom if denom else float("nan")


def _residualise(target: list[float], controls: Sequence[Sequence[float]]) -> list[float]:
    """OLS residuals of `target` on ranked `controls`, via normal equations (no numpy needed)."""
    cols = [[1.0] * len(target)] + [ranks(c) for c in controls]
    p = len(cols)
    ata = [[sum(cols[a][i] * cols[b][i] for i in range(len(target))) for b in range(p)]
           for a in range(p)]
    atb = [sum(cols[a][i] * target[i] for i in range(len(target))) for a in range(p)]
    for c in range(p):                                   # Gaussian elimination w/ partial pivoting
        piv = max(range(c, p), key=lambda r: abs(ata[r][c]))
        if abs(ata[piv][c]) < 1e-12:
            continue
        ata[c], ata[piv] = ata[piv], ata[c]
        atb[c], atb[piv] = atb[piv], atb[c]
        for r in range(p):
            if r == c:
                continue
            f = ata[r][c] / ata[c][c]
            for k in range(c, p):
                ata[r][k] -= f * ata[c][k]
            atb[r] -= f * atb[c]
    beta = [atb[i] / ata[i][i] if abs(ata[i][i]) > 1e-12 else 0.0 for i in range(p)]
    return [target[i] - sum(beta[a] * cols[a][i] for a in range(p)) for i in range(len(target))]


def multi_partial_spearman(x: Sequence[float], y: Sequence[float],
                           controls: Sequence[Sequence[float]]) -> float:
    """Partial rank correlation of x and y controlling several variables at once."""
    if not controls:
        return spearman(x, y)
    ex = _residualise(ranks(x), controls)
    ey = _residualise(ranks(y), controls)
    return _pearson(ex, ey)


def cluster_bootstrap_ci(rows: Sequence[dict], cluster_key: Callable[[dict], object],
                         stat: Callable[[Sequence[dict]], float],
                         n_boot: int = 3000, seed: int = 0) -> tuple[float, float, float]:
    """Resample CLUSTERS with replacement. Returns (point, lo, hi) at 95%.

    ⛔ UNDER-COVERS BELOW ~30 CLUSTERS. This sprint's designs have 18, so the intervals are
    optimistic and every quote of one must say so.
    """
    groups: dict[object, list[dict]] = {}
    for r in rows:
        groups.setdefault(cluster_key(r), []).append(r)
    keys = sorted(groups, key=repr)
    rng = random.Random(seed)
    draws = []
    for _ in range(n_boot):
        sample = [x for k in (rng.choice(keys) for _ in keys) for x in groups[k]]
        v = stat(sample)
        if v == v:
            draws.append(v)
    draws.sort()
    return stat(rows), draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws))]


def cluster_permutation_p(rows: Sequence[dict], cluster_key: Callable[[dict], object],
                          stat: Callable[[Sequence[dict]], float],
                          n_perm: int = 20000, seed: int = 0) -> tuple[float, float]:
    """Permute whole clusters' outcomes against each other. Returns (|observed|, p).

    ⛔ DEGENERATE FOR ANY VARIABLE BALANCED BY CONSTRUCTION WITHIN EVERY CLUSTER. If each cluster
    carries an identical composition of that variable, swapping outcomes between clusters preserves
    its pairing with the outcome, and the null equals the observed value -- p ~ 1.0 no matter what
    the true association is. `n_examples` scored exactly 1.0000 this way in §12.23. Valid only for
    variables that VARY WITHIN a cluster.
    """
    groups: dict[object, list[dict]] = {}
    for r in rows:
        groups.setdefault(cluster_key(r), []).append(r)
    keys = sorted(groups, key=repr)
    obs = abs(stat(list(rows)))
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_perm):
        perm = keys[:]
        rng.shuffle(perm)
        swapped = []
        for a, b in zip(keys, perm):
            for ra, rb in zip(groups[a], groups[b]):
                q = dict(ra)
                q["__y"] = rb["__y"]
                swapped.append(q)
        if abs(stat(swapped)) >= obs:
            hits += 1
    return obs, (hits + 1) / (n_perm + 1)


def wild_cluster_bootstrap_p(rows: Sequence[dict], cluster_key: Callable[[dict], object],
                             x_key: str, y_key: str, control_keys: Sequence[str] = (),
                             n_boot: int = 4000, seed: int = 0,
                             return_draws: bool = False):
    """Null-imposed wild cluster bootstrap (Cameron-Gelbach-Miller) for "x has no partial effect".

    WHY THIS EXISTS ALONGSIDE `cluster_bootstrap_ci`. The pairs bootstrap in that function
    under-covers when the cluster count is small, and the usual guidance places cluster-robust
    inference in trouble below roughly 40-50 clusters rather than below 30. §12.27's primary test
    runs on the 32 UNSEEN domains — inside that marginal band — so a pairs interval there is not
    trustworthy on its own. The wild bootstrap with Rademacher weights is the standard remedy in
    exactly that range.

    Ranks everything first, residualises x and y on the controls, then tests the slope of
    ey ~ ex. The null b = 0 is IMPOSED: bootstrap outcomes are w_g * ey_i with one Rademacher draw
    w_g per CLUSTER, so the resampled data satisfy the null by construction and the reference
    distribution is the right one. Returns (observed t, two-sided p).
    """
    groups: dict[object, list[int]] = {}
    for i, r in enumerate(rows):
        groups.setdefault(cluster_key(r), []).append(i)
    keys = sorted(groups, key=repr)

    rx = ranks([r[x_key] for r in rows])
    ry = ranks([r[y_key] for r in rows])
    ctrls = [[r[c] for r in rows] for c in control_keys]
    ex = _residualise(rx, ctrls) if ctrls else [v - sum(rx) / len(rx) for v in rx]
    ey = _residualise(ry, ctrls) if ctrls else [v - sum(ry) / len(ry) for v in ry]

    def _t(y: Sequence[float]) -> float:
        sxx = sum(v * v for v in ex)
        if sxx <= 0:
            return float("nan")
        b = sum(a * c for a, c in zip(ex, y)) / sxx
        resid = [c - b * a for a, c in zip(ex, y)]
        # cluster-robust (CR0) variance of b
        meat = 0.0
        for k in keys:
            s = sum(ex[i] * resid[i] for i in groups[k])
            meat += s * s
        var = meat / (sxx * sxx)
        return b / (var ** 0.5) if var > 0 else float("nan")

    t_obs = _t(ey)
    if t_obs != t_obs:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    hits = 0
    draws = []
    for _ in range(n_boot):
        w = {k: (1.0 if rng.random() < 0.5 else -1.0) for k in keys}
        ystar = list(ey)
        for k in keys:
            wk = w[k]
            for i in groups[k]:
                ystar[i] = wk * ey[i]
        t_star = _t(ystar)
        if return_draws:
            draws.append(t_star)
        if t_star == t_star and abs(t_star) >= abs(t_obs):
            hits += 1
    p = (hits + 1) / (n_boot + 1)
    return (t_obs, p, draws) if return_draws else (t_obs, p)
