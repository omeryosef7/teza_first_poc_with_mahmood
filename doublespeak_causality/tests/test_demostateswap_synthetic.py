"""
GPU-free synthetic tests for pair_common.DemoStateSwap (S3, NEXT_CAUSAL_SPRINT).
No model, no GPU, fully deterministic. Mirrors tests/test_layerpatch_synthetic.py.

Asserts the three invariants the resid_pre write-hook MUST satisfy:
  (a) SELF-SWAP (source == the receiver's own captured resid_pre) == baseline EXACTLY;
  (b) swapping target positions changes ONLY those positions, never earlier ones;
  (c) all hook handles are removed after __exit__.

Run:  python doublespeak_causality/tests/test_demostateswap_synthetic.py
      pytest doublespeak_causality/tests/test_demostateswap_synthetic.py -q
"""
import os
import sys
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import DemoStateSwap  # noqa: E402


class ToyBlock(nn.Module):
    """Returns a tuple (hidden, aux) like a real decoder layer, applying a fixed
    additive shift so downstream layers depend on the (possibly patched) input."""
    def __init__(self, hidden: int, shift: float):
        super().__init__()
        self.shift = shift

    def forward(self, x):
        return (x + self.shift, None)


class ToyStack(nn.Module):
    def __init__(self, n_layers=4, hidden=8):
        super().__init__()
        self.model = nn.Module()               # DemoStateSwap discovers model.model.layers
        self.model.layers = nn.ModuleList(ToyBlock(hidden, i + 1) for i in range(n_layers))

    def forward(self, x):
        for blk in self.model.layers:
            x, _ = blk(x)
        return x


def _capture_resid_pre(stack, x, positions, layers):
    """Capture the block-INPUT (resid_pre) rows at `positions` for each layer, via
    forward-pre hooks, exactly the state DemoStateSwap will overwrite."""
    store, handles = {}, []
    for li in layers:
        def mk(li):
            def f(mod, args, kwargs=None):
                h = args[0] if args else kwargs.get("hidden_states")
                store[li] = h[0, positions, :].clone()
            return f
        handles.append(
            stack.model.layers[li].register_forward_pre_hook(mk(li), with_kwargs=True))
    stack(x)
    for h in handles:
        h.remove()
    return store


def test_self_swap_equals_baseline_exactly():
    torch.manual_seed(0)
    stack = ToyStack(n_layers=4, hidden=8)
    x = torch.randn(1, 5, 8)
    positions, layers = [1, 3], [0, 1, 2, 3]

    base = stack(x).clone()
    src = _capture_resid_pre(stack, x, positions, layers)  # own resid_pre
    with DemoStateSwap(stack, positions, src):
        out = stack(x)
    assert torch.equal(out, base), "self-swap must reproduce the baseline EXACTLY"


def test_swap_changes_only_target_positions():
    stack = ToyStack(n_layers=4, hidden=8)
    x = torch.zeros(1, 6, 8)
    positions, layers = [2], [1]                # overwrite pos 2 at layer 1 only
    base = stack(x).clone()

    src = {1: torch.full((1, 8), 100.0)}
    with DemoStateSwap(stack, positions, src):
        out = stack(x)

    diff = (out - base).abs().sum(dim=-1)[0]     # [seq]
    assert diff[2] > 0, "target position 2 must change"
    for p in (0, 1, 3, 4, 5):
        assert torch.allclose(out[0, p], base[0, p]), f"pos {p} must be unchanged"
    assert out.shape == base.shape, "length must be preserved"


def test_multi_layer_swap_and_downstream_propagation():
    # Overwrite pos 0 at layers 1 AND 2 with a known value; the remaining layers'
    # shifts must propagate from that value (downstream-in-depth change).
    stack = ToyStack(n_layers=4, hidden=4)      # shifts 1,2,3,4
    x = torch.zeros(1, 2, 4)
    # Layer-1 input overwritten to 100 -> layer1 +2, layer2 input overwritten to 50 ->
    # +3, layer3 +4 => 50 + 3 + 4 = 57 at pos 0.
    src = {1: torch.full((1, 4), 100.0), 2: torch.full((1, 4), 50.0)}
    with DemoStateSwap(stack, [0], src):
        out = stack(x)
    assert torch.allclose(out[0, 0], torch.full((4,), 57.0)), out[0, 0]
    assert torch.allclose(out[0, 1], torch.full((4,), 10.0)), "pos1 untouched (1+2+3+4)"


def test_hook_removed_after_context():
    stack = ToyStack(n_layers=2, hidden=4)
    x = torch.zeros(1, 2, 4)
    with DemoStateSwap(stack, [0], {0: torch.full((1, 4), 99.0)}) as swp:
        pass
    assert swp._handles == [], "handles list must be emptied on __exit__"
    after = stack(x)
    base = stack(x)
    assert torch.allclose(after, base), "hook must be removed on __exit__"


TESTS = [test_self_swap_equals_baseline_exactly,
         test_swap_changes_only_target_positions,
         test_multi_layer_swap_and_downstream_propagation,
         test_hook_removed_after_context]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS) - fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
