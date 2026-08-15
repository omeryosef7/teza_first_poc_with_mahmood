"""GPU-free tests for the Phase-5 donor-shift energy decomposition (plan §9).

Uses synthetic activations with a PLANTED donor shift Δh = a·v_bomb + b·refusal +
c·w_perp of known magnitudes, so we can assert:
  * decompose() recovers the planted energy fractions (bomb / refusal / remainder);
  * the QR plane split is exact (frac_plane == frac_bomb+frac_refusal when the two
    named axes are orthogonal), and remainder = 1 - plane;
  * the index-alignment self-check returns cos≈1 exactly when v_bomb equals the
    normalized benign diff-of-means (the B9 guard's OK path), and drops otherwise.

Run:  python -m pytest doublespeak_causality/tests/test_phase5_decompose.py -q
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "..")
sys.path.insert(0, PKG)

from src.probes import phase5_decompose as p5  # noqa: E402


D = 64
LAYERS = [8, 9, 10, 11]
N = 60
POS = 1          # 2 positions; use index 0 in tests
NPOS = 2


def _basis():
    """orthonormal e0 (bomb), e1 (refusal), e2 (perp remainder) in R^D."""
    rng = np.random.default_rng(0)
    M = rng.standard_normal((D, 3))
    Q, _ = np.linalg.qr(M)
    return Q[:, 0], Q[:, 1], Q[:, 2]


def _build(a, b, c, vbomb_dir, refusal_dir, perp_dir):
    """Return (acts, triples, vbomb, refusal) with doublespeak-benign = Δh planted.

    Δh = a·vbomb + b·refusal + c·perp, identical across examples/layers (so the
    mean shift and per-example shift coincide and the planted fractions are exact).
    """
    dh = a * vbomb_dir + b * refusal_dir + c * perp_dir
    rng = np.random.default_rng(1)
    # 3 conditions × N examples; benign is a random base, doublespeak = benign+dh
    acts = np.zeros((3 * N, len(range(max(LAYERS) + 1)), NPOS, D), dtype=np.float32)
    # acts layer axis must cover indices up to max(LAYERS)
    triples = {}
    for i in range(N):
        base = rng.standard_normal((max(LAYERS) + 1, NPOS, D)).astype(np.float32)
        i_ds, i_be, i_ne = 3 * i, 3 * i + 1, 3 * i + 2
        acts[i_be] = base
        acts[i_ne] = base + rng.standard_normal(base.shape).astype(np.float32) * 0.1
        d_full = base.copy()
        for L in LAYERS:
            d_full[L, :, :] = base[L, :, :] + dh  # plant at every position
        acts[i_ds] = d_full
        triples[i] = {"doublespeak": i_ds, "benign": i_be, "neutral": i_ne}
    vbomb = {L: vbomb_dir.copy() for L in LAYERS}
    return acts, triples, vbomb, refusal_dir.copy()


def test_recovers_planted_energy_fractions():
    e0, e1, e2 = _basis()
    a, b, c = 3.0, 0.5, 4.0
    S = a * a + b * b + c * c
    acts, triples, vbomb, refusal = _build(a, b, c, e0, e1, e2)
    rows = p5.decompose(acts, triples, vbomb, refusal, pos_idx=0, donor="benign")
    for L in LAYERS:
        r = rows[L]
        assert r["n"] == N
        assert r["frac_bomb"] == pytest.approx(a * a / S, abs=1e-4)
        assert r["frac_refusal"] == pytest.approx(b * b / S, abs=1e-4)
        assert r["frac_remainder"] == pytest.approx(c * c / S, abs=1e-4)


def test_qr_plane_split_is_exact_and_consistent():
    e0, e1, e2 = _basis()
    a, b, c = 2.0, 1.0, 2.0
    S = a * a + b * b + c * c
    acts, triples, vbomb, refusal = _build(a, b, c, e0, e1, e2)
    rows = p5.decompose(acts, triples, vbomb, refusal, pos_idx=0, donor="benign")
    for L in LAYERS:
        r = rows[L]
        # orthogonal named axes → plane energy == bomb+refusal energy
        assert r["frac_bomb"] + r["frac_refusal"] == pytest.approx(
            1.0 - r["frac_remainder"], abs=1e-4)
        assert r["frac_remainder"] == pytest.approx(c * c / S, abs=1e-4)


def test_selfcheck_ok_when_vbomb_is_diffofmeans():
    e0, e1, e2 = _basis()
    # Δh purely along e0 → benign diff-of-means direction == e0 == v_bomb → cos≈1
    acts, triples, vbomb, refusal = _build(3.0, 0.0, 0.0, e0, e1, e2)
    chk = p5.alignment_selfcheck(acts, triples, vbomb, pos_idx=0, donor="benign")
    assert min(chk.values()) == pytest.approx(1.0, abs=1e-5)


def test_selfcheck_warns_when_axis_misaligned():
    e0, e1, e2 = _basis()
    # plant Δh along e0 but hand the checker a v_bomb along e1 → cos ≈ 0
    acts, triples, _vb, refusal = _build(3.0, 0.0, 0.0, e0, e1, e2)
    misaligned = {L: e1.copy() for L in LAYERS}
    chk = p5.alignment_selfcheck(acts, triples, misaligned, pos_idx=0, donor="benign")
    assert max(chk.values()) < 0.1
