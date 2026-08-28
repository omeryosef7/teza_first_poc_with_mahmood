"""The rank statistics that closed the Phase 7 gate, pinned — including the bug that nearly stood.

WHY THESE EXIST. §12.24's verdict rests on a partial correlation with a cluster-bootstrap interval.
The first version of that computation used an `argsort`-position rank function, which breaks ties by
arbitrary order. The outcome is BINARY (226 zeros, 62 ones in 288 rows), so nearly every rank was
randomised. It returned +0.0942 where the correct answer is +0.1924 — and it AGREED WITH THE
CONCLUSION ALREADY WRITTEN, which is the dangerous kind of wrong. It survived only until a second
implementation of the same quantity disagreed with it.

So two of these tests are structural rather than numerical: one fails on the tie bug specifically,
and one requires the two independent partial implementations to agree. The remaining two pin the
DESIGN limits — a permutation that is degenerate by construction, and a bootstrap that under-covers
— because both produced quotable numbers this sprint that meant nothing.
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import clustered_stats as cs  # noqa: E402


def test_ranks_average_ties_rather_than_breaking_them_arbitrarily():
    """⛔ THE BUG. argsort-position ranking would give [1,2,3,4,5] here."""
    assert cs.ranks([0, 0, 0, 1, 1]) == [2.0, 2.0, 2.0, 4.5, 4.5]


def test_ranks_of_a_binary_outcome_take_exactly_two_values():
    """The property the tie bug destroyed: a binary vector has two distinct ranks, not n."""
    y = [0.0] * 20 + [1.0] * 5
    assert len(set(cs.ranks(y))) == 2, "a binary outcome must not receive 25 distinct ranks"


def test_spearman_is_1_and_minus_1_on_monotone_data():
    assert abs(cs.spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1.0) < 1e-9
    assert abs(cs.spearman([1, 2, 3, 4], [40, 30, 20, 10]) + 1.0) < 1e-9


def test_spearman_is_rank_based_not_value_based():
    """A monotone but wildly non-linear transform must not change it."""
    x = [1, 2, 3, 4, 5]
    assert abs(cs.spearman(x, [v ** 7 for v in x]) - 1.0) < 1e-9


def test_the_two_partial_implementations_agree_on_a_single_control():
    """THE CROSS-CHECK THAT CAUGHT THE TIE BUG. Formula vs residualisation must coincide."""
    rng = random.Random(7)
    x = [rng.gauss(0, 1) for _ in range(200)]
    z = [xi * 0.8 + rng.gauss(0, 0.6) for xi in x]
    y = [1.0 if (xi * 0.5 + zi * 0.3 + rng.gauss(0, 1)) > 0 else 0.0 for xi, zi in zip(x, z)]
    a = cs.partial_spearman(x, y, z)
    b = cs.multi_partial_spearman(x, y, [z])
    assert abs(a - b) < 1e-6, f"single-control partial disagrees: {a} vs {b}"


def test_partial_removes_a_pure_confound():
    """If x only relates to y through z, the partial must collapse toward zero."""
    rng = random.Random(11)
    z = [rng.gauss(0, 1) for _ in range(400)]
    x = [zi + rng.gauss(0, 0.05) for zi in z]
    y = [zi + rng.gauss(0, 0.05) for zi in z]
    assert cs.spearman(x, y) > 0.9
    assert abs(cs.multi_partial_spearman(x, y, [z])) < 0.4


def test_multi_partial_with_no_controls_is_plain_spearman():
    x = [1, 5, 3, 9, 7]; y = [2, 4, 3, 8, 6]
    assert abs(cs.multi_partial_spearman(x, y, []) - cs.spearman(x, y)) < 1e-9


def _rows(n_clusters=8, per=6, seed=3):
    """Rows where `v` VARIES within a cluster and `balanced` is identical in every cluster."""
    rng = random.Random(seed)
    out = []
    for c in range(n_clusters):
        for i in range(per):
            out.append({"c": c, "v": rng.gauss(0, 1), "balanced": float(i),
                        "__y": 1.0 if rng.random() < 0.4 else 0.0})
    return out


def test_cluster_permutation_is_DEGENERATE_for_a_variable_balanced_by_construction():
    """⛔ The p=1.0000 artifact, pinned as a property rather than left to be re-quoted.

    Every cluster carries the same set of `balanced` values, so permuting outcomes between clusters
    preserves the balanced->outcome pairing and the null cannot move.
    """
    rows = _rows()
    _, p = cs.cluster_permutation_p(
        rows, lambda r: r["c"],
        lambda s: cs.spearman([r["balanced"] for r in s], [r["__y"] for r in s]),
        n_perm=400)
    assert p > 0.9, (
        f"expected a degenerate p near 1.0 for a construction-balanced variable, got {p} — if this "
        f"ever fails, the guarantee documented on cluster_permutation_p has changed")


def test_cluster_permutation_CAN_reject_for_a_variable_that_varies_within_cluster():
    """The complement: the test is not simply incapable of returning a small p."""
    rng = random.Random(5)
    rows = []
    for c in range(10):
        for _ in range(8):
            v = rng.gauss(0, 1)
            rows.append({"c": c, "v": v, "__y": 1.0 if v + rng.gauss(0, 0.3) > 0 else 0.0})
    _, p = cs.cluster_permutation_p(
        rows, lambda r: r["c"],
        lambda s: cs.spearman([r["v"] for r in s], [r["__y"] for r in s]), n_perm=400)
    assert p < 0.05, f"a strong within-cluster association should reject; got p={p}"


def test_cluster_bootstrap_returns_the_point_estimate_and_a_bracketing_interval():
    rows = _rows(n_clusters=12, per=8)
    pt, lo, hi = cs.cluster_bootstrap_ci(
        rows, lambda r: r["c"],
        lambda s: cs.spearman([r["v"] for r in s], [r["__y"] for r in s]), n_boot=300)
    assert lo <= pt <= hi, f"point estimate {pt} outside its own interval [{lo}, {hi}]"


def test_cluster_bootstrap_resamples_CLUSTERS_not_rows():
    """⛔ THIS TEST'S FIRST VERSION DID NOT CATCH THE MUTATION IT WAS WRITTEN FOR.

    It used Spearman between a cluster-constant x and an ALTERNATING y, whose bootstrap spread is
    wide under row-resampling too — so replacing cluster resampling with row resampling passed all
    eleven tests. The statistic has to be one whose variance actually differs between the two
    schemes.

    Here every cluster is internally constant and half are all-ones, so the mean of y has SE
    ~0.5/sqrt(12) = 0.144 under CLUSTER resampling and ~0.5/sqrt(96) = 0.051 under ROW resampling.
    The 95% widths are therefore ~0.57 against ~0.20, and the threshold sits between them.
    """
    rows = []
    for c in range(12):
        y = 1.0 if c < 6 else 0.0
        for _ in range(8):
            rows.append({"c": c, "v": float(c), "__y": y})
    pt, lo, hi = cs.cluster_bootstrap_ci(
        rows, lambda r: r["c"], lambda s: sum(r["__y"] for r in s) / len(s), n_boot=800)
    assert abs(pt - 0.5) < 1e-9
    assert hi - lo > 0.35, (
        f"width {hi - lo:.3f} is what ROW resampling produces (~0.20); cluster resampling of 12 "
        f"fully-clustered groups must give ~0.57. The bootstrap is not resampling clusters.")


def _clustered_null(n_clusters, per, rng):
    """x and y each strongly clustered but INDEPENDENT of one another: the true effect is zero."""
    rows = []
    for c in range(n_clusters):
        ax, ay = rng.gauss(0, 1), rng.gauss(0, 1)
        for _ in range(per):
            rows.append({"c": c, "x": ax + rng.gauss(0, 0.5), "y": ay + rng.gauss(0, 0.5)})
    return rows


def test_wild_cluster_bootstrap_has_correct_SIZE_under_a_clustered_null():
    """The property the whole function exists for.

    §12.27's primary statistic sits on 32 clusters, inside the 30-50 band where a pairs bootstrap
    is unreliable. This checks the wild version does not over-reject when x and y are each heavily
    clustered but unrelated — the exact structure of the boombness data, where the predictor's ICC
    is 0.82.
    """
    rng = random.Random(4)
    rejects = 0
    reps = 40
    for _ in range(reps):
        _, p = cs.wild_cluster_bootstrap_p(_clustered_null(32, 19, rng), lambda r: r["c"],
                                           "x", "y", n_boot=250)
        rejects += p < 0.05
    assert rejects / reps <= 0.20, (
        f"rejection rate {rejects / reps:.2f} at nominal 0.05 — the test over-rejects under a "
        f"clustered null, which is the failure it exists to prevent")


def test_treating_ROWS_as_clusters_over_rejects_badly_on_the_same_data():
    """The contrast that shows the clustering is doing real work: ~0.04 vs ~0.68 in simulation."""
    rng = random.Random(4)
    rejects = 0
    reps = 20
    for _ in range(reps):
        _, p = cs.wild_cluster_bootstrap_p(_clustered_null(32, 19, rng), lambda r: id(r),
                                           "x", "y", n_boot=250)
        rejects += p < 0.05
    assert rejects / reps >= 0.30, (
        "row-level 'clusters' should over-reject heavily here; if this passes the fixture no "
        "longer has the cluster structure the size test depends on")


def test_wild_cluster_bootstrap_detects_a_real_WITHIN_cluster_effect():
    rng = random.Random(9)
    rows = []
    for c in range(32):
        a = rng.gauss(0, 1)
        for _ in range(19):
            x = rng.gauss(0, 1)
            rows.append({"c": c, "x": x + a, "y": a + 1.2 * x + rng.gauss(0, 0.5)})
    _, p = cs.wild_cluster_bootstrap_p(rows, lambda r: r["c"], "x", "y", n_boot=500)
    assert p < 0.05, f"a strong within-cluster effect must be detected; got p={p}"


def test_rademacher_weights_are_drawn_PER_CLUSTER_not_per_row():
    """⛔ THE SECOND TEST OF MINE THAT FAILED ITS OWN MUTANT.

    The size test above did NOT catch "weights drawn per row": measured rejection rates were
    identical at 32 clusters (0.075 vs 0.075) and only separated below ~12 (0.117 vs 0.067 at
    k=8) — because the t statistic already carries a cluster-robust CR0 variance, so most of the
    clustering enters there rather than through the weights. A rejection-rate test is the wrong
    instrument for this property.

    The direct signature is deterministic and holds at any cluster count: one Rademacher draw per
    cluster means the bootstrap t can take at most 2**k distinct values. Per-row weights make the
    support effectively continuous.
    """
    rng = random.Random(2)
    rows = [{"c": c, "x": rng.gauss(0, 1), "y": rng.gauss(0, 1)}
            for c in range(4) for _ in range(25)]
    _, _, draws = cs.wild_cluster_bootstrap_p(rows, lambda r: r["c"], "x", "y",
                                              n_boot=600, return_draws=True)
    distinct = len({round(v, 9) for v in draws})
    assert distinct <= 2 ** 4, (
        f"{distinct} distinct bootstrap statistics from 4 clusters — with one weight per cluster "
        f"there can be at most 16. The weights are being drawn per ROW.")
    assert distinct >= 4, f"only {distinct} distinct values; the bootstrap is not varying at all"
