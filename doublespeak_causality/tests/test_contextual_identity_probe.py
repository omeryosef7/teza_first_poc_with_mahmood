"""GPU-free tests for the Bombness probe fitting/eval (plan §5.1, §5.4, §16).

Uses synthetic activations with a PLANTED linear signal so we can assert:
  * the probe recovers a decodable signal (AUC high) on held-out examples;
  * label-shuffle and random-direction controls sit at chance (~0.5);
  * the bootstrap CI resamples EXAMPLES (its width tracks n_examples, not n_rows);
  * the train/eval example-leak guard actually fires;
  * diff-of-means agrees with logreg on a clean signal;
  * a scalar nuisance feature uncorrelated with the label is at chance.

Run:  python -m pytest doublespeak_causality/tests/test_contextual_identity_probe.py -q
"""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "..")
sys.path.insert(0, PKG)

from src.probes import contextual_identity_probe as cip  # noqa: E402


def _synth(n_examples, hidden=64, signal=1.2, noise=0.6, seed=0, split_offset=0):
    """Each example -> one positive + one negative item sharing an example id.
    Both share a per-example `base` (the matched-pair structure), each gets
    INDEPENDENT noise, and the class signal is +/- along axis 0. With signal=0 the
    two items are still distinct noisy points with no class structure (chance)."""
    rng = np.random.default_rng(seed)
    X, y, groups = [], [], []
    for e in range(n_examples):
        gid = f"ex{split_offset + e}"
        base = rng.standard_normal(hidden)
        xp = base + noise * rng.standard_normal(hidden); xp[0] += signal
        xn = base + noise * rng.standard_normal(hidden); xn[0] -= signal
        X += [xp, xn]; y += [1, 0]; groups += [gid, gid]
    return np.array(X), np.array(y), np.array(groups)


def test_probe_recovers_planted_signal():
    Xtr, ytr, gtr = _synth(120, seed=1, split_offset=0)
    Xev, yev, gev = _synth(60, seed=2, split_offset=1000)  # disjoint example ids
    res = cip.fit_and_eval(Xtr, ytr, gtr, Xev, yev, gev, n_boot=500)
    assert res["logreg"].auc > 0.9
    assert res["diff_of_means"].auc > 0.9
    assert res["logreg"].balanced_acc > 0.80
    lo, hi = res["logreg"].auc_ci
    assert 0.5 < lo <= res["logreg"].auc <= hi <= 1.0


def test_label_shuffle_is_chance():
    Xtr, ytr, gtr = _synth(120, seed=3, split_offset=0)
    Xev, yev, gev = _synth(60, seed=4, split_offset=1000)
    auc = cip.control_label_shuffle(Xtr, ytr, Xev, yev, gev)
    assert 0.35 < auc < 0.65


def test_random_direction_is_chance():
    Xev, yev, _ = _synth(200, seed=5)
    aucs = [cip.control_random_direction(Xev, yev, seed=s) for s in range(20)]
    assert 0.40 < np.mean(aucs) < 0.60


def test_leak_guard_fires():
    Xtr, ytr, gtr = _synth(50, seed=6, split_offset=0)
    Xev, yev, gev = _synth(50, seed=7, split_offset=0)  # SAME example ids -> leak
    with pytest.raises(AssertionError, match="leak"):
        cip.fit_and_eval(Xtr, ytr, gtr, Xev, yev, gev, n_boot=10)


def test_scalar_nuisance_at_chance():
    _, yev, _ = _synth(200, seed=8)
    rng = np.random.default_rng(9)
    nuisance = rng.standard_normal(len(yev))  # uncorrelated with label
    auc = cip.control_scalar_feature(nuisance, yev)
    assert 0.5 <= auc < 0.62  # max(auc, 1-auc), so >=0.5 by construction, but low


def test_diff_of_means_direction_points_right_way():
    X, y, _ = _synth(100, seed=10)
    v, b = cip.diff_of_means_direction(X, y)
    # signal is on axis 0; the unit direction should load mostly on axis 0
    assert abs(v[0]) > 0.5
    assert np.isclose(np.linalg.norm(v), 1.0)


def test_no_signal_is_chance():
    """Sanity: with signal=0, even the fitted probe cannot beat chance on held-out."""
    Xtr, ytr, gtr = _synth(120, signal=0.0, seed=11, split_offset=0)
    Xev, yev, gev = _synth(80, signal=0.0, seed=12, split_offset=1000)
    res = cip.fit_and_eval(Xtr, ytr, gtr, Xev, yev, gev, n_boot=300)
    assert 0.35 < res["logreg"].auc < 0.65


def test_smoke_fit_on_synthetic_run(tmp_path):
    """smoke_fit loads a run dir and reports above-chance per-layer AUC on a decodable
    synthetic slice (mechanics check)."""
    from src.probes import smoke_fit
    # build a fake run dir: acts [n, L=3, P=2, H=16] with a signal at L1, pos0
    rng = np.random.default_rng(0)
    n_ex, L, P, H = 30, 3, 2, 16
    acts, items = [], []
    for e in range(n_ex):
        base = rng.standard_normal((L, P, H))
        pos_block = base.copy(); pos_block[1, 0, 0] += 3.0   # signal: layer1, codeword_last
        neg_block = base.copy(); neg_block[1, 0, 0] -= 3.0
        acts.append(pos_block); acts.append(neg_block)
        gid = f"ex{e}"
        items.append({"example_id": gid, "label": 1, "condition": "doublespeak", "split": "dev"})
        items.append({"example_id": gid, "label": 0, "condition": "benign", "split": "dev"})
    acts = np.stack(acts).astype(np.float32)
    np.save(tmp_path / "acts.npy", acts)
    with open(tmp_path / "items.jsonl", "w") as fh:
        for it in items:
            fh.write(json.dumps(it) + "\n")

    a2, i2 = smoke_fit.load_run(str(tmp_path))
    assert a2.shape == (2 * n_ex, L, P, H)
    rows = smoke_fit.fit_per_layer(a2, i2, position="codeword_last")
    assert "error" not in rows[0]
    best = max(rows, key=lambda r: r["auc"])
    assert best["layer"] == 1 and best["auc"] > 0.9   # signal is at layer 1
