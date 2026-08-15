"""GPU-free tests for the Phase-5 per-example patch-vector construction (plan §9).

Plants a per-example donor shift Δhᵢ = aᵢ·v_bomb + bᵢ·refusal + cᵢ·perp with
per-example random coefficients, and asserts:
  * additivity: bomb_i + refusal_i + remainder_i == full_i (exact);
  * each component lies along its intended axis (bomb ∥ v_bomb, refusal ∥ r);
  * the remainder is orthogonal to BOTH named axes;
  * the norm-matched random arm matches ‖bomb_i‖ per example;
  * vectors are per-example (differ across examples), not a shared mean.

Run:  python -m pytest doublespeak_causality/tests/test_build_phase5_perexample.py -q
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from src.probes import build_phase5_perexample as bpx  # noqa: E402

D = 48
LAYERS = [8, 9, 10, 11]
N = 40


def _basis():
    rng = np.random.default_rng(0)
    Q, _ = np.linalg.qr(rng.standard_normal((D, 3)))
    return Q[:, 0], Q[:, 1], Q[:, 2]


def _synth():
    e0, e1, e2 = _basis()
    rng = np.random.default_rng(3)
    coef = rng.standard_normal((N, 3)) * np.array([3.0, 1.0, 2.0]) + 3.0  # per-example
    acts = np.zeros((3 * N, max(LAYERS) + 1, 2, D), dtype=np.float32)
    triples = {}
    for i in range(N):
        base = rng.standard_normal((max(LAYERS) + 1, 2, D)).astype(np.float32)
        i_ds, i_be, i_ne = 3 * i, 3 * i + 1, 3 * i + 2
        a, b, c = coef[i]
        dh = a * e0 + b * e1 + c * e2
        ds = base.copy()
        for L in LAYERS:
            ds[L, 0, :] = base[L, 0, :] + dh    # plant at codeword pos (idx 0)
        acts[i_be], acts[i_ne], acts[i_ds] = base, base, ds
        triples[i] = {"doublespeak": i_ds, "benign": i_be, "neutral": i_ne}
    vbomb = {L: e0.copy() for L in LAYERS}
    return acts, triples, vbomb, e1, e0, e1, e2, coef


def test_additivity_and_axes():
    acts, triples, vbomb, refusal, e0, e1, e2, coef = _synth()
    arms, eids, diag = bpx.build_perexample(acts, triples, vbomb, refusal,
                                            LAYERS, pos_idx=0, donor="benign")
    for L in LAYERS:
        full = arms["full"][L]; bomb = arms["bomb"][L]
        refv = arms["refusal"][L]; rem = arms["remainder"][L]
        # additivity (exact, since v_bomb ⟂ refusal here)
        assert np.allclose(bomb + refv + rem, full, atol=1e-4)
        # components lie along intended axes
        assert np.allclose(bomb, np.outer(bomb @ e0, e0), atol=1e-4)
        assert np.allclose(refv, np.outer(refv @ e1, e1), atol=1e-4)
        # remainder orthogonal to both named axes
        assert np.allclose(rem @ e0, 0.0, atol=1e-4)
        assert np.allclose(rem @ e1, 0.0, atol=1e-4)
        # reconstruction diagnostic reports ~0 error
        assert diag[L]["recon_rel_err"] < 1e-5


def test_random_arm_norm_matched_and_per_example():
    acts, triples, vbomb, refusal, e0, e1, e2, coef = _synth()
    arms, eids, diag = bpx.build_perexample(acts, triples, vbomb, refusal,
                                            LAYERS, pos_idx=0, donor="benign")
    for L in LAYERS:
        bomb = arms["bomb"][L]; rand = arms["random"][L]
        # random arm norm-matched to bomb per example
        assert np.allclose(np.linalg.norm(rand, axis=1),
                           np.linalg.norm(bomb, axis=1), atol=1e-4)
        # vectors are per-example, not a shared mean (rows differ)
        assert not np.allclose(arms["full"][L][0], arms["full"][L][1], atol=1e-2)


def test_additivity_holds_when_bomb_and_refusal_NOT_orthogonal():
    """Regression: on real data v_bomb ⟂ refusal only ~cos 0.09. A raw dual
    projection would double-count the overlap and break additivity (~6% err seen
    in the E39/E40 build). With refusal orthogonalised against v_bomb the arms
    must remain EXACTLY additive even for a deliberately non-orthogonal refusal."""
    acts, triples, vbomb, _refusal, e0, e1, e2, coef = _synth()
    # refusal deliberately shares ~0.3 cosine with v_bomb (=e0)
    refusal = bpx._unit(e1 + 0.3 * e0)
    arms, eids, diag = bpx.build_perexample(acts, triples, vbomb, refusal,
                                            LAYERS, pos_idx=0, donor="benign")
    for L in LAYERS:
        assert np.allclose(arms["bomb"][L] + arms["refusal"][L] + arms["remainder"][L],
                           arms["full"][L], atol=1e-4)
        assert diag[L]["recon_rel_err"] < 1e-6
        # refusal arm is orthogonal to v_bomb (its bomb-aligned part was removed)
        assert np.allclose(arms["refusal"][L] @ e0, 0.0, atol=1e-4)


def test_planted_bomb_coefficient_recovered():
    acts, triples, vbomb, refusal, e0, e1, e2, coef = _synth()
    arms, eids, diag = bpx.build_perexample(acts, triples, vbomb, refusal,
                                            LAYERS, pos_idx=0, donor="benign")
    # bomb_i · e0 should equal the planted a_i (coef col 0), example-ordered by eid
    order = sorted(triples.keys())
    a_planted = coef[np.array(order)][:, 0]
    for L in LAYERS:
        a_rec = arms["bomb"][L] @ e0
        assert np.allclose(a_rec, a_planted, atol=1e-3)
