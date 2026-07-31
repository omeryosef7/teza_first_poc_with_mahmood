"""
GPU-free synthetic tests for pair_common.AllPositionAdd / AllPositionAddMultiLayer (NEXT5 W5).
No model, no harmful text. Verifies the all-position/all-timestep additive refusal hook:

  (1) it ADDS alpha * d_hat at EVERY position (prefill),
  (2) it also adds on a SIMULATED DECODE STEP (a seq==1 forward) — the case
      LayerPatch(mode="add") SKIPS (its whole point vs the prefill-only add),
  (3) it normalizes the direction (alpha is absolute residual-space magnitude),
  (4) it composes with a LayerPatch add on the same layer in one ExitStack,
  (5) multi-layer adds at every targeted layer only; untargeted layers pass through,
  (6) hooks are removed on __exit__; bad index raises.

Run:  python doublespeak_causality/tests/test_alladd_hook_synthetic.py
      pytest doublespeak_causality/tests/test_alladd_hook_synthetic.py -q
"""
import os
import sys
from contextlib import ExitStack

import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pair_common as pc              # noqa: E402
from ds_common import LayerPatch      # noqa: E402


class ToyLayer(nn.Module):
    def forward(self, x):
        return (x, None)


class ToyStack(nn.Module):
    def __init__(self, n_layers=2, hidden=6):
        super().__init__()
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(ToyLayer() for _ in range(n_layers))

    def call_layer(self, li, x):
        return self.model.layers[li](x)[0]


def _comp(h, d):
    dn = d / d.norm()
    return (h * dn).sum(dim=-1)


def test_adds_at_all_positions_prefill():
    stack = ToyStack(n_layers=2, hidden=6)
    d = torch.tensor([1.0, 0, 0, 0, 0, 0])
    x = torch.zeros(1, 5, 6)
    with pc.AllPositionAdd(stack, 0, d, alpha=2.0):
        out = stack.call_layer(0, x)
    # every position gains alpha along d_hat (d already unit here)
    assert torch.allclose(_comp(out, d), torch.full((1, 5), 2.0), atol=1e-5), \
        "must add alpha*d_hat at EVERY prefill position"


def test_decode_step_added():
    """A seq==1 forward is the case LayerPatch(add) SKIPS; the hook must still fire."""
    stack = ToyStack(n_layers=1, hidden=4)
    d = torch.tensor([0.0, 1.0, 0.0, 0.0])
    x = torch.zeros(1, 1, 4)
    with pc.AllPositionAdd(stack, 0, d, alpha=3.0):
        out = stack.call_layer(0, x)
    assert torch.allclose(_comp(out, d), torch.full((1, 1), 3.0), atol=1e-5), \
        "add must fire on a decode step (seq==1)"


def test_direction_is_normalized():
    """alpha is absolute: a non-unit direction must be normalized before scaling."""
    stack = ToyStack(n_layers=1, hidden=4)
    d = torch.tensor([0.0, 10.0, 0.0, 0.0])            # norm 10, not unit
    x = torch.zeros(1, 2, 4)
    with pc.AllPositionAdd(stack, 0, d, alpha=1.0):
        out = stack.call_layer(0, x)
    # added vector must have norm == alpha == 1 (not 10)
    assert torch.allclose(out[0, 0].norm(), torch.tensor(1.0), atol=1e-5), \
        "direction must be unit-normalized so alpha is absolute"


def test_compose_with_layerpatch_add():
    stack = ToyStack(n_layers=1, hidden=4)
    dref = torch.tensor([1.0, 0.0, 0.0, 0.0])          # all-position refusal add axis
    add = torch.tensor([0.0, 5.0, 0.0, 0.0])           # position-specific concept install
    x = torch.zeros(1, 3, 4)
    with ExitStack() as s:
        s.enter_context(LayerPatch(stack, 0, positions=[1], vector=add, mode="add"))
        s.enter_context(pc.AllPositionAdd(stack, 0, dref, alpha=2.0))
        out = stack.call_layer(0, x)
    # all positions get +2 along dref; pos 1 additionally gets the concept add
    assert torch.allclose(_comp(out, dref), torch.full((1, 3), 2.0), atol=1e-5)
    assert torch.allclose(out[0, 1], torch.tensor([2.0, 5.0, 0.0, 0.0]), atol=1e-5)
    assert torch.allclose(out[0, 0], torch.tensor([2.0, 0.0, 0.0, 0.0]), atol=1e-5)


def test_hook_removed_after_context():
    stack = ToyStack(n_layers=1, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    x = torch.randn(1, 3, 4)
    with pc.AllPositionAdd(stack, 0, d, alpha=1.0):
        pass
    out = stack.call_layer(0, x)
    assert torch.allclose(out, x), "hook must be removed on __exit__ (no add)"


def test_multilayer_adds_every_layer():
    n = 4
    stack = ToyStack(n_layers=n, hidden=6)
    d = torch.tensor([0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
    with pc.AllPositionAddMultiLayer(stack, list(range(n)), d, alpha=1.5):
        for li in range(n):
            x = torch.zeros(1, 5, 6)
            out = stack.call_layer(li, x)
            assert torch.allclose(_comp(out, d), torch.full((1, 5), 1.5), atol=1e-5), \
                f"must add at every position of layer {li}"


def test_multilayer_subset_only_targets():
    stack = ToyStack(n_layers=3, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    x = torch.zeros(1, 3, 4)
    with pc.AllPositionAddMultiLayer(stack, [0, 2], d, alpha=1.0):
        out0 = stack.call_layer(0, x)
        out1 = stack.call_layer(1, x)
        out2 = stack.call_layer(2, x)
    assert torch.allclose(_comp(out0, d), torch.full((1, 3), 1.0), atol=1e-5)
    assert torch.allclose(_comp(out2, d), torch.full((1, 3), 1.0), atol=1e-5)
    assert torch.allclose(out1, x), "untargeted layer 1 must be unmodified"


def test_multilayer_hooks_removed_after_context():
    stack = ToyStack(n_layers=3, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    x = torch.randn(1, 3, 4)
    with pc.AllPositionAddMultiLayer(stack, [0, 1, 2], d, alpha=1.0):
        pass
    for li in range(3):
        assert torch.allclose(stack.call_layer(li, x), x), \
            f"all handles must be removed on __exit__ (layer {li})"


def test_multilayer_bad_index_raises():
    stack = ToyStack(n_layers=2, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    try:
        pc.AllPositionAddMultiLayer(stack, [0, 5], d)
    except IndexError:
        return
    raise AssertionError("out-of-range layer index must raise IndexError")


TESTS = [test_adds_at_all_positions_prefill, test_decode_step_added,
         test_direction_is_normalized, test_compose_with_layerpatch_add,
         test_hook_removed_after_context, test_multilayer_adds_every_layer,
         test_multilayer_subset_only_targets, test_multilayer_hooks_removed_after_context,
         test_multilayer_bad_index_raises]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS)-fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
