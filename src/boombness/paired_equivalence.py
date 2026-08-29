"""Paired EQUIVALENCE test for a binary outcome. RBD sprint, 2026-08-29.

WHY THIS MODULE EXISTS
----------------------
`RBD-DR-001.2`: there is no equivalence test anywhere in `src/boombness/`. What the repo has is
`phase1_decomposition.py:206`, ``"equivalent_within_margin": gap <= MARGIN_ARM_VS_ARM`` -- a POINT
ESTIMATE compared to a margin, with no confidence interval on either side. That is not an
equivalence test, and "we failed to reject a difference" is not evidence of no difference. The
sprint's primary claim (H1) needs the positive form: *binding is PRESERVED*, i.e. the intervention's
effect on binding lies inside a preregistered margin.

The nearest existing thing, `margin_exposure.adversarial_bound`, disqualifies itself for this use in
its own note: an over-large window "is CONSERVATIVE here if the claim carries an effect and
ANTI-CONSERVATIVE if it is a null". "Binding survives" IS a null, so that bound is anti-conservative
in exactly our direction.

WHAT IT COMPUTES
----------------
The design is PAIRED and BINARY: the same family is scored under baseline and under the arm, and the
outcome is a mapped-win (1) or not (0). The estimand is delta = p_arm - p_base.

Three quantities, deliberately reported together:

1. `newcombe`  -- Newcombe's method-10 ("square-and-add") interval for a paired proportion
                  difference, built from two Wilson intervals and the tetrachoric-style
                  correlation between the two marginals. Closed form, no dependencies, well behaved
                  at the boundaries where the normal approximation is not (and this design lives at
                  the boundary: 45/48 and 48/48 are real observed cells).
2. `cluster`   -- a percentile bootstrap over CLUSTERS (domains), which is the only one of the three
                  that respects the domain clustering the sprint has repeatedly been bitten by.
                  Reported with its own n_clusters so a 5-cluster interval cannot masquerade as an
                  n=160 one.
3. `mcnemar_p` -- the exact conditional two-sided p for a DIFFERENCE. It is reported for context and
                  is explicitly NOT the equivalence verdict.

THE VERDICT USES THE MOST CONSERVATIVE LOWER BOUND of (1) and (2). Taking the friendlier of two
intervals is how a null claim gets manufactured.

CAPABILITY, BEFORE THE DATA
---------------------------
`can_establish_equivalence` answers: at this n, could ANY outcome have cleared the margin? The
best case is zero discordant pairs, so the field is computed by evaluating the interval at b=c=0
with the observed n. If that best case does not clear -m, the design is STRUCTURALLY INCAPABLE and
the result is `UNRESOLVABLE_AT_THIS_N` -- not "equivalent", and not "different".

This is the same discipline `clustered_stats.cluster_sign_test.can_reach_alpha` applies to the sign
test, and it exists because the prior phase quoted `pre10`'s k=5 cluster test as a negative when its
attainable floor (0.0625) was above alpha and no arrangement of the data could have cleared.
"""
from __future__ import annotations

import math
import random
from typing import Any, Callable, Dict, List, Optional, Sequence

SCHEMA = "PAIRED_EQUIVALENCE/1"


# --------------------------------------------------------------------------- #
# Normal quantile without scipy (the module must import on a bare compute node)
# --------------------------------------------------------------------------- #
def _z(alpha_two_sided: float) -> float:
    """z such that P(|Z| <= z) = 1 - alpha. Bisection on erf; exact to ~1e-12."""
    if not 0.0 < alpha_two_sided < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha_two_sided}")
    target = 1.0 - alpha_two_sided
    lo, hi = 0.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if math.erf(mid / math.sqrt(2.0)) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def wilson(x: int, n: int, alpha: float = 0.05) -> tuple:
    """Wilson score interval for a binomial proportion. Defined at x=0 and x=n."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= x <= n:
        raise ValueError(f"x={x} outside [0, {n}]")
    z = _z(alpha)
    z2 = z * z
    centre = (x + z2 / 2.0) / (n + z2)
    half = (z / (n + z2)) * math.sqrt(x * (n - x) / n + z2 / 4.0)
    return max(0.0, centre - half), min(1.0, centre + half)


# --------------------------------------------------------------------------- #
# Newcombe method 10 for a PAIRED difference of proportions
# --------------------------------------------------------------------------- #
def newcombe_paired_ci(n11: int, n10: int, n01: int, n00: int,
                       alpha: float = 0.05) -> Dict[str, Any]:
    """CI for delta = p_arm - p_base on paired binary data.

    Cell convention, both indexed (base, arm):
        n11 = base 1, arm 1     n10 = base 1, arm 0   (a LOSS under the arm)
        n01 = base 0, arm 1     n00 = base 0, arm 0   (a GAIN under the arm)

    so p_base = (n11 + n10)/n, p_arm = (n11 + n01)/n, delta = (n01 - n10)/n.
    """
    for v in (n11, n10, n01, n00):
        if v < 0:
            raise ValueError("counts must be non-negative")
    n = n11 + n10 + n01 + n00
    if n == 0:
        raise ValueError("no paired observations")

    x_base, x_arm = n11 + n10, n11 + n01
    p_base, p_arm = x_base / n, x_arm / n
    delta = p_arm - p_base

    l_base, u_base = wilson(x_base, n, alpha)
    l_arm, u_arm = wilson(x_arm, n, alpha)

    # phi: the 2x2 correlation between the two marginals. Undefined (0/0) when a margin is
    # degenerate -- e.g. every family wins under both arms, which is a REAL cell here (48/48).
    # Newcombe's own prescription is phi = 0 there, which widens the interval: the conservative
    # direction for a null claim.
    denom2 = (n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00)
    phi = 0.0 if denom2 <= 0 else (n11 * n00 - n10 * n01) / math.sqrt(denom2)
    phi = max(-1.0, min(1.0, phi))

    d1, d2 = p_arm - l_arm, u_base - p_base
    lo = delta - math.sqrt(max(0.0, d1 * d1 - 2.0 * phi * d1 * d2 + d2 * d2))
    e1, e2 = u_arm - p_arm, p_base - l_base
    hi = delta + math.sqrt(max(0.0, e1 * e1 - 2.0 * phi * e1 * e2 + e2 * e2))

    return {"delta": delta, "lo": max(-1.0, lo), "hi": min(1.0, hi),
            "p_base": p_base, "p_arm": p_arm, "n": n, "phi": phi,
            "n11": n11, "n10": n10, "n01": n01, "n00": n00, "alpha": alpha}


# --------------------------------------------------------------------------- #
# Exact conditional McNemar (a DIFFERENCE test -- reported, never the verdict)
# --------------------------------------------------------------------------- #
def mcnemar_exact(n10: int, n01: int) -> float:
    """Exact two-sided p for a paired difference, conditional on the discordant total."""
    m = n10 + n01
    if m == 0:
        return 1.0
    k = min(n10, n01)
    tail = sum(math.comb(m, i) for i in range(0, k + 1))
    return min(1.0, 2.0 * tail / (2.0 ** m))


# --------------------------------------------------------------------------- #
# Cluster bootstrap on delta
# --------------------------------------------------------------------------- #
def cluster_bootstrap_delta_ci(pairs: Sequence[Dict[str, Any]],
                               cluster_key: Callable[[Dict[str, Any]], Any],
                               alpha: float = 0.05, n_boot: int = 4000,
                               seed: int = 20260829) -> Dict[str, Any]:
    """Percentile bootstrap over whole clusters. `pairs` rows carry `base` and `arm` in {0,1}."""
    by: Dict[Any, List[Dict[str, Any]]] = {}
    for r in pairs:
        by.setdefault(cluster_key(r), []).append(r)
    keys = sorted(by, key=repr)
    if not keys:
        raise ValueError("no clusters")

    def delta_of(rows: Sequence[Dict[str, Any]]) -> float:
        n = len(rows)
        return sum(r["arm"] - r["base"] for r in rows) / n if n else float("nan")

    rng = random.Random(seed)
    draws: List[float] = []
    for _ in range(n_boot):
        picked: List[Dict[str, Any]] = []
        for _ in keys:
            picked.extend(by[keys[rng.randrange(len(keys))]])
        if picked:
            draws.append(delta_of(picked))
    draws.sort()
    if not draws:
        raise ValueError("bootstrap produced no draws")
    lo = draws[max(0, int(math.floor((alpha / 2.0) * len(draws))))]
    hi = draws[min(len(draws) - 1, int(math.ceil((1.0 - alpha / 2.0) * len(draws))) - 1)]
    return {"delta": delta_of(list(pairs)), "lo": lo, "hi": hi,
            "n_clusters": len(keys), "n_rows": len(pairs), "n_boot": n_boot,
            "cluster_sizes": {repr(k): len(by[k]) for k in keys}}


# --------------------------------------------------------------------------- #
# The verdict
# --------------------------------------------------------------------------- #
class EquivalenceVerdict(dict):
    def summary(self) -> str:
        return (f"{self['VERDICT']}: delta={self['delta']:+.4f} "
                f"[{self['binding_lo']:+.4f}, {self['binding_hi']:+.4f}] "
                f"vs margin -{self['margin']:.4f} "
                f"(binding={self['binding_interval']}, n={self['n']}, "
                f"k={self.get('n_clusters')}, capable={self['can_establish_equivalence']})")


def paired_equivalence(pairs: Sequence[Dict[str, Any]], margin: float,
                       cluster_key: Optional[Callable[[Dict[str, Any]], Any]] = None,
                       alpha: float = 0.05, n_boot: int = 4000,
                       seed: int = 20260829) -> EquivalenceVerdict:
    """Is the arm's binary outcome EQUIVALENT to baseline, within `margin`?

    `pairs`: rows with `base` and `arm` in {0, 1}, one row per paired unit (a family).
    `margin`: the preregistered maximum tolerable DROP, a positive number (T3 uses 0.10).

    PASSES iff the most conservative lower bound of the available intervals is strictly greater
    than -margin. A point estimate inside the margin whose interval crosses it does NOT pass.
    """
    if margin <= 0:
        raise ValueError("margin must be positive; it is a tolerable DROP")
    if not pairs:
        raise ValueError("no paired observations")
    for i, r in enumerate(pairs):
        for f in ("base", "arm"):
            if r.get(f) not in (0, 1):
                raise ValueError(f"row {i}: {f}={r.get(f)!r} is not 0 or 1")

    n11 = sum(1 for r in pairs if r["base"] == 1 and r["arm"] == 1)
    n10 = sum(1 for r in pairs if r["base"] == 1 and r["arm"] == 0)
    n01 = sum(1 for r in pairs if r["base"] == 0 and r["arm"] == 1)
    n00 = sum(1 for r in pairs if r["base"] == 0 and r["arm"] == 0)
    n = n11 + n10 + n01 + n00

    nc = newcombe_paired_ci(n11, n10, n01, n00, alpha)
    los = [("newcombe", nc["lo"], nc["hi"])]

    cl = None
    if cluster_key is not None:
        cl = cluster_bootstrap_delta_ci(pairs, cluster_key, alpha, n_boot, seed)
        los.append(("cluster_bootstrap", cl["lo"], cl["hi"]))

    binding_name, binding_lo, binding_hi = min(los, key=lambda t: t[1])

    # CAPABILITY: the best attainable case is zero discordance at this n and these marginals.
    best = newcombe_paired_ci(n11 + n10 + n01, 0, 0, n00, alpha)
    can = best["lo"] > -margin

    passes = binding_lo > -margin
    if not can:
        verdict = "UNRESOLVABLE_AT_THIS_N"
    elif passes:
        verdict = "EQUIVALENT"
    elif binding_hi < -margin:
        verdict = "WORSE_THAN_MARGIN"
    else:
        verdict = "NOT_ESTABLISHED"

    return EquivalenceVerdict({
        "schema": SCHEMA, "VERDICT": verdict,
        "delta": nc["delta"], "p_base": nc["p_base"], "p_arm": nc["p_arm"],
        "n": n, "n11": n11, "n10": n10, "n01": n01, "n00": n00,
        "margin": margin, "alpha": alpha,
        "binding_interval": binding_name, "binding_lo": binding_lo, "binding_hi": binding_hi,
        "newcombe": nc, "cluster_bootstrap": cl,
        "n_clusters": (cl or {}).get("n_clusters"),
        "mcnemar_p_two_sided": mcnemar_exact(n10, n01),
        "mcnemar_note": ("a DIFFERENCE test, reported for context. A large p here is NOT evidence "
                         "of equivalence -- that is the failure this module exists to prevent."),
        "can_establish_equivalence": can,
        "attainable_lo_at_zero_discordance": best["lo"],
        "capability_note": ("best case is zero discordant pairs at this n; if that lower bound "
                            "does not clear -margin, no outcome could have, and the verdict is "
                            "UNRESOLVABLE_AT_THIS_N rather than a finding"),
    })
