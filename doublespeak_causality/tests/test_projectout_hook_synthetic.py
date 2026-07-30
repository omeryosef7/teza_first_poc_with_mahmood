"""
GPU-free synthetic tests for pair_common.AllPositionProjectOut (STAGE4 §b/§4). No model,
no harmful text. Verifies the all-position/all-timestep refusal-ablation hook:

  (1) it zeroes the component along `direction` at EVERY position (unlike LayerPatch
      project_out, which only edits fixed prompt positions),
  (2) it also zeroes the component on a SIMULATED DECODE STEP (a seq==1 forward), which is
      exactly the case LayerPatch skips,
  (3) it composes with a LayerPatch add on the same layer in one ExitStack,
  (4) hooks are removed on __exit__.

Run:  python doublespeak_causality/tests/test_projectout_hook_synthetic.py
      pytest doublespeak_causality/tests/test_projectout_hook_synthetic.py -q
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
    """Decoder-layer stand-in: returns a tuple (hidden, aux) like a real block."""
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
    """Signed magnitude of h's component along unit-normalized d, per position: [.., ]."""
    dn = d / d.norm()
    return (h * dn).sum(dim=-1)


def test_all_positions_zeroed_prefill():
    stack = ToyStack(n_layers=2, hidden=6)
    d = torch.tensor([1.0, 0, 0, 0, 0, 0])
    x = torch.randn(1, 5, 6) + d                       # every position has a d-component
    assert (_comp(x, d).abs() > 1e-3).all()
    with pc.AllPositionProjectOut(stack, 0, d):
        out = stack.call_layer(0, x)
    assert torch.allclose(_comp(out, d), torch.zeros(1, 5), atol=1e-5), \
        "d-component must be ~0 at EVERY prefill position"


def test_decode_step_zeroed():
    """A seq==1 forward is the case LayerPatch(project_out) skips; the hook must still fire."""
    stack = ToyStack(n_layers=1, hidden=4)
    d = torch.tensor([0.0, 1.0, 0.0, 0.0])
    x = torch.randn(1, 1, 4) + 3.0 * d
    with pc.AllPositionProjectOut(stack, 0, d):
        out = stack.call_layer(0, x)
    assert torch.allclose(_comp(out, d), torch.zeros(1, 1), atol=1e-5)


def test_compose_with_layerpatch_add():
    """LayerPatch add (position-specific) + all-position project-out, one ExitStack."""
    stack = ToyStack(n_layers=1, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])             # ablated axis
    add = torch.tensor([0.0, 5.0, 0.0, 0.0])           # orthogonal to d, added at pos 1
    x = torch.zeros(1, 3, 4) + d                        # d-component everywhere
    with ExitStack() as s:
        s.enter_context(LayerPatch(stack, 0, positions=[1], vector=add, mode="add"))
        s.enter_context(pc.AllPositionProjectOut(stack, 0, d))
        out = stack.call_layer(0, x)
    # d-component removed at all positions...
    assert torch.allclose(_comp(out, d), torch.zeros(1, 3), atol=1e-5)
    # ...and the orthogonal add survives at pos 1 only.
    assert torch.allclose(out[0, 1], torch.tensor([0.0, 5.0, 0.0, 0.0]), atol=1e-5)
    assert torch.allclose(out[0, 0], torch.zeros(4), atol=1e-5)


def test_alpha_partial_projection():
    stack = ToyStack(n_layers=1, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    x = torch.zeros(1, 2, 4) + 2.0 * d                 # component magnitude 2
    with pc.AllPositionProjectOut(stack, 0, d, alpha=0.5):
        out = stack.call_layer(0, x)
    assert torch.allclose(_comp(out, d), torch.full((1, 2), 1.0), atol=1e-5)  # 2 - 0.5*2 = 1


def test_hook_removed_after_context():
    stack = ToyStack(n_layers=1, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    x = torch.randn(1, 3, 4) + d
    with pc.AllPositionProjectOut(stack, 0, d):
        pass
    out = stack.call_layer(0, x)
    assert torch.allclose(out, x), "hook must be removed on __exit__ (no projection)"


def test_multilayer_zeroes_every_layer():
    """AllPositionProjectOutMultiLayer over [0..n) zeroes the SAME direction at EVERY
    layer's output (the standard Arditi et al. all-layer ablation)."""
    n = 4
    stack = ToyStack(n_layers=n, hidden=6)
    d = torch.tensor([0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
    with pc.AllPositionProjectOutMultiLayer(stack, list(range(n)), d):
        for li in range(n):
            x = torch.randn(1, 5, 6) + 2.0 * d      # d-component present at this layer
            assert (_comp(x, d).abs() > 1e-3).all()
            out = stack.call_layer(li, x)
            assert torch.allclose(_comp(out, d), torch.zeros(1, 5), atol=1e-5), \
                f"d-component must be ~0 at every position of layer {li}"


def test_multilayer_subset_only_targets():
    """Only the layers in `layer_idxs` project out; untargeted layers pass through."""
    stack = ToyStack(n_layers=3, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    x = torch.randn(1, 3, 4) + 2.0 * d
    with pc.AllPositionProjectOutMultiLayer(stack, [0, 2], d):
        out0 = stack.call_layer(0, x)
        out1 = stack.call_layer(1, x)
        out2 = stack.call_layer(2, x)
    assert torch.allclose(_comp(out0, d), torch.zeros(1, 3), atol=1e-5)
    assert torch.allclose(_comp(out2, d), torch.zeros(1, 3), atol=1e-5)
    assert torch.allclose(out1, x), "untargeted layer 1 must be unmodified"


def test_multilayer_hooks_removed_after_context():
    stack = ToyStack(n_layers=3, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    x = torch.randn(1, 3, 4) + d
    with pc.AllPositionProjectOutMultiLayer(stack, [0, 1, 2], d):
        pass
    for li in range(3):
        assert torch.allclose(stack.call_layer(li, x), x), \
            f"all handles must be removed on __exit__ (layer {li})"


def test_multilayer_bad_index_raises():
    stack = ToyStack(n_layers=2, hidden=4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    try:
        pc.AllPositionProjectOutMultiLayer(stack, [0, 5], d)
    except IndexError:
        return
    raise AssertionError("out-of-range layer index must raise IndexError")


TESTS = [test_all_positions_zeroed_prefill, test_decode_step_zeroed,
         test_compose_with_layerpatch_add, test_alpha_partial_projection,
         test_hook_removed_after_context,
         test_multilayer_zeroes_every_layer, test_multilayer_subset_only_targets,
         test_multilayer_hooks_removed_after_context, test_multilayer_bad_index_raises]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS)-fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
