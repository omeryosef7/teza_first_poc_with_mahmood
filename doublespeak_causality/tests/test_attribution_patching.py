"""
GPU-free correctness gate for Attribution Patching (48_attribution_patching.py).

The load-bearing check: on a LINEAR toy stack the AtP first-order estimate
    AtP[L, pos] = grad_M(clean_act[L, pos]) . (corrupt_act[L, pos] - clean_act[L, pos])
must equal the TRUE metric delta from a real replace-patch EXACTLY (up to fp32), because
a linear network makes the metric affine in every intermediate activation, so the Taylor
expansion AtP relies on is not an approximation but an identity.

A second toy adds a nonlinearity so AtP is only approximate; we assert the AtP-vs-true
Pearson/Spearman correlation the script's validation gate reports is high there too, i.e.
the gate would (correctly) pass a mildly nonlinear stack.

No model, no GPU, fully deterministic.
Run:  python -m pytest doublespeak_causality/tests/test_attribution_patching.py -q
"""
import os
import sys
import importlib.util

import numpy as np
import torch
import torch.nn as nn

_HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_HERE, ".."))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, "..", filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


atp = _load("atp48", "48_attribution_patching.py")


# --------------------------------------------------------------------------- #
# Toy stacks (mirror tests/test_layerpatch_synthetic.py: .model.layers, tuple output)
# --------------------------------------------------------------------------- #
class LinearBlock(nn.Module):
    """Pointwise linear block: (x @ W + b, None). Makes the whole stack affine."""
    def __init__(self, hidden, seed):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        # near-identity + small mixing so downstream Jacobians are non-trivial but stable
        self.W = nn.Parameter(torch.eye(hidden) + 0.1 * torch.randn(hidden, hidden, generator=g))
        self.b = nn.Parameter(0.1 * torch.randn(hidden, generator=g))

    def forward(self, x):
        return (x @ self.W + self.b, None)


class TanhBlock(nn.Module):
    """Same but with a tanh nonlinearity, so AtP becomes a first-order APPROXIMATION."""
    def __init__(self, hidden, seed):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        self.W = nn.Parameter(torch.eye(hidden) + 0.1 * torch.randn(hidden, hidden, generator=g))
        self.b = nn.Parameter(0.1 * torch.randn(hidden, generator=g))

    def forward(self, x):
        return (torch.tanh(x @ self.W + self.b), None)


class ToyStack(nn.Module):
    def __init__(self, block_cls, n_layers=4, hidden=8):
        super().__init__()
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(block_cls(hidden, seed=i + 1) for i in range(n_layers))

    def forward(self, x):
        for blk in self.model.layers:
            x, _ = blk(x)
        return x


def _make_metric(readout_pos, w):
    """Linear readout M = <final[readout_pos], w> (scalar)."""
    def metric(out):
        return (out[0, readout_pos] * w).sum()
    return metric


def _capture_outputs(stack, x, layer_idxs):
    """Corrupt block outputs {L: Tensor[seq, hidden]} (no grad)."""
    cap = atp._ActGradCapture(stack, layer_idxs)
    with torch.no_grad():
        with cap:
            stack(x)
    return {L: cap.acts[L].detach()[0].float() for L in layer_idxs}


# --------------------------------------------------------------------------- #
# Correlation helpers
# --------------------------------------------------------------------------- #
def test_pearson_spearman_basics():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.1, 5.9, 8.2, 9.8]
    assert atp.pearson(x, y) > 0.998
    assert abs(atp.spearman(x, y) - 1.0) < 1e-9
    # perfect monotone-but-nonlinear => spearman 1, pearson < 1
    z = [1.0, 2.0, 4.0, 8.0, 16.0]
    assert abs(atp.spearman(x, z) - 1.0) < 1e-9
    assert atp.pearson(x, z) < 0.99
    # anti-correlation
    assert atp.pearson(x, [5, 4, 3, 2, 1]) < -0.999


# --------------------------------------------------------------------------- #
# THE load-bearing check: AtP == true patching, exactly, on a linear stack.
# --------------------------------------------------------------------------- #
def test_atp_equals_true_patching_on_linear_stack():
    torch.manual_seed(0)
    hidden, seq, n_layers = 8, 5, 4
    stack = ToyStack(LinearBlock, n_layers=n_layers, hidden=hidden)
    x_clean = torch.randn(1, seq, hidden)
    x_corrupt = torch.randn(1, seq, hidden)

    readout_pos = seq - 1
    w = torch.randn(hidden)
    metric = _make_metric(readout_pos, w)

    layer_idxs = list(range(n_layers - 1))       # below the readout layer
    positions = list(range(seq))

    corrupt = _capture_outputs(stack, x_corrupt, layer_idxs)

    def clean_forward():
        return stack(x_clean)

    est, m_clean = atp.atp_estimate(stack, clean_forward, metric,
                                    positions, corrupt, layer_idxs)

    # true patching for EVERY cell
    max_abs_err = 0.0
    n_nonzero = 0
    for L in layer_idxs:
        for pos in positions:
            vec = corrupt[L][pos]
            td = atp.true_patch_delta(stack, clean_forward, metric, L, pos, vec, m_clean)
            err = abs(est[(L, pos)] - td)
            max_abs_err = max(max_abs_err, err)
            if abs(td) > 1e-6:
                n_nonzero += 1
    assert n_nonzero > 0, "test is vacuous: no cell moved the metric"
    assert max_abs_err < 1e-3, f"AtP must equal true patching on a linear stack; " \
                               f"max |err|={max_abs_err:.2e}"


def test_atp_correlates_with_true_on_nonlinear_stack():
    """Nonlinear stack: AtP is approximate, but the gate's correlation must still be high
    for a SMALL clean/corrupt gap (linearization regime)."""
    torch.manual_seed(1)
    hidden, seq, n_layers = 8, 5, 4
    stack = ToyStack(TanhBlock, n_layers=n_layers, hidden=hidden)
    x_clean = torch.randn(1, seq, hidden) * 0.5
    x_corrupt = x_clean + 0.15 * torch.randn(1, seq, hidden)   # small perturbation

    readout_pos = seq - 1
    w = torch.randn(hidden)
    metric = _make_metric(readout_pos, w)
    layer_idxs = list(range(n_layers - 1))
    positions = list(range(seq))

    corrupt = _capture_outputs(stack, x_corrupt, layer_idxs)

    def clean_forward():
        return stack(x_clean)

    est, m_clean = atp.atp_estimate(stack, clean_forward, metric,
                                    positions, corrupt, layer_idxs)

    a_vals, t_vals = [], []
    for L in layer_idxs:
        for pos in positions:
            a_vals.append(est[(L, pos)])
            t_vals.append(atp.true_patch_delta(stack, clean_forward, metric, L, pos,
                                               corrupt[L][pos], m_clean))
    assert max(abs(t) for t in t_vals) > 1e-6, "vacuous: nothing moved"
    # This is exactly the quantity the script's validation gate reports.
    assert atp.pearson(a_vals, t_vals) > 0.9
    assert atp.spearman(a_vals, t_vals) > 0.9


def test_atp_direction_matches_sign_of_true_effect():
    """Sanity: on the linear stack, AtP and true deltas share sign cell-by-cell."""
    torch.manual_seed(2)
    hidden, seq, n_layers = 6, 4, 3
    stack = ToyStack(LinearBlock, n_layers=n_layers, hidden=hidden)
    x_clean = torch.randn(1, seq, hidden)
    x_corrupt = torch.randn(1, seq, hidden)
    metric = _make_metric(seq - 1, torch.randn(hidden))
    layer_idxs = list(range(n_layers - 1))
    positions = list(range(seq))
    corrupt = _capture_outputs(stack, x_corrupt, layer_idxs)

    def clean_forward():
        return stack(x_clean)

    est, m_clean = atp.atp_estimate(stack, clean_forward, metric, positions, corrupt, layer_idxs)
    for L in layer_idxs:
        for pos in positions:
            td = atp.true_patch_delta(stack, clean_forward, metric, L, pos, corrupt[L][pos], m_clean)
            if abs(td) > 1e-5:
                assert np.sign(est[(L, pos)]) == np.sign(td)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("ALL ATP TESTS PASSED")
