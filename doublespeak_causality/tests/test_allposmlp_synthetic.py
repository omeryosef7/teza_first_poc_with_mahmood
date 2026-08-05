"""
GPU-free synthetic tests for pair_common.AllPositionMLPAblate (P10 item 1 / plan §0.9).
No model, no GPU, deterministic. Same toy-module pattern as
tests/test_componentoutswap_synthetic.py and tests/test_allposzheadablate_synthetic.py.

Asserts:
  (a) the hook fires on a PREFILL forward (seq > 1) AND on a DECODE-shaped forward (seq == 1) —
      the whole point of the primitive: the decode-step output must actually change;
  (b) only the requested layers are touched;
  (c) mode="zero" zeroes, "scale" scales, "project_out" removes exactly the given direction and
      leaves the orthogonal complement BIT-IDENTICAL (and "mean" keeps the prefill-only caveat
      that AllPositionZHeadAblate documents);
  (d) hooks are removed on __exit__ (a later forward is unaffected);
  (e) NEGATIVE CONTROL — the same ablation built with pair_common.ComponentOutSwap is a NO-OP on
      a decode-shaped input (its position guard drops every prompt position when seq == 1), while
      AllPositionMLPAblate is not. This pins the defect that makes the prefill-only BEHAV-WRITE
      behavioral null untested for the generation phase, i.e. WHY it must be re-run.

Run:  python doublespeak_causality/tests/test_allposmlp_synthetic.py
"""
import os
import sys
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import AllPositionMLPAblate, ComponentOutSwap  # noqa: E402


class ToyMLP(nn.Module):
    """Plain-tensor output, like a real HF mlp; deterministic and never zero."""
    def __init__(self, shift: float):
        super().__init__()
        self.shift = shift

    def forward(self, x):
        return 2.0 * x + self.shift


class ToyBlock(nn.Module):
    """resid_post = resid_pre + mlp(resid_pre); mlp is a hookable submodule."""
    def __init__(self, shift: float):
        super().__init__()
        self.mlp = ToyMLP(shift)

    def forward(self, x):
        return (x + self.mlp(x), None)


class ToyTupleMLP(nn.Module):
    """Returns a TUPLE, exercising the tuple-output branch of the hook."""
    def __init__(self, shift: float):
        super().__init__()
        self.shift = shift

    def forward(self, x):
        return (2.0 * x + self.shift, None)


class ToyTupleBlock(nn.Module):
    def __init__(self, shift: float):
        super().__init__()
        self.mlp = ToyTupleMLP(shift)

    def forward(self, x):
        return (x + self.mlp(x)[0], None)


class ToyStack(nn.Module):
    def __init__(self, n_layers=3, shifts=None, block=ToyBlock):
        super().__init__()
        shifts = shifts or [i + 1 for i in range(n_layers)]
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(block(s) for s in shifts)

    def forward(self, x):
        for blk in self.model.layers:
            x, _ = blk(x)
        return x


# --------------------------------------------------------------------------- #
# (a) fires on prefill AND on a KV-cached decode step
# --------------------------------------------------------------------------- #
def test_fires_on_prefill_and_on_decode_step():
    stack = ToyStack(n_layers=3)
    prefill = torch.arange(1 * 5 * 4, dtype=torch.float32).reshape(1, 5, 4)
    decode = torch.arange(1 * 1 * 4, dtype=torch.float32).reshape(1, 1, 4) + 100.0

    base_pre, base_dec = stack(prefill).clone(), stack(decode).clone()
    with AllPositionMLPAblate(stack, [1], mode="zero"):
        out_pre, out_dec = stack(prefill).clone(), stack(decode).clone()

    assert not torch.allclose(out_pre, base_pre), "must fire on a PREFILL forward (seq>1)"
    assert not torch.allclose(out_dec, base_dec), \
        "must fire on a DECODE-shaped forward (seq==1) — this is the whole point"
    # decode step: layer1's write is removed exactly -> resid_post == resid_pre at layer 1
    x1 = decode + stack.model.layers[0].mlp(decode)          # layer-0 output feeds layer 1
    expect_dec = x1 + stack.model.layers[2].mlp(x1)          # layer 1 contributes nothing
    assert torch.equal(out_dec, expect_dec), (out_dec, expect_dec)


def test_decode_step_mlp_output_is_exactly_zeroed():
    stack = ToyStack(n_layers=2)
    z = torch.ones(1, 1, 4)                                   # seq == 1 (cached decode step)
    with AllPositionMLPAblate(stack, [0], mode="zero"):
        out = stack.model.layers[0].mlp(z)
    assert torch.all(out == 0), out


def test_tuple_output_mlp_is_handled():
    stack = ToyStack(n_layers=2, block=ToyTupleBlock)
    z = torch.ones(1, 1, 4)
    with AllPositionMLPAblate(stack, [0], mode="zero"):
        out = stack.model.layers[0].mlp(z)
    assert isinstance(out, tuple) and out[1] is None, "tuple structure must be preserved"
    assert torch.all(out[0] == 0), out[0]


# --------------------------------------------------------------------------- #
# (b) only the requested layers are touched
# --------------------------------------------------------------------------- #
def test_only_requested_layers_touched():
    stack = ToyStack(n_layers=4)
    x = torch.randn(1, 3, 4)
    base = [stack.model.layers[i].mlp(x).clone() for i in range(4)]
    with AllPositionMLPAblate(stack, [1, 3], mode="zero"):
        got = [stack.model.layers[i].mlp(x).clone() for i in range(4)]
    assert torch.all(got[1] == 0) and torch.all(got[3] == 0), "layers 1,3 must be zeroed"
    assert torch.equal(got[0], base[0]), "layer 0 must be untouched"
    assert torch.equal(got[2], base[2]), "layer 2 must be untouched"


def test_layer_index_out_of_range_raises():
    stack = ToyStack(n_layers=2)
    try:
        AllPositionMLPAblate(stack, [0, 5], mode="zero")
    except IndexError:
        return
    raise AssertionError("out-of-range layer index must raise IndexError")


# --------------------------------------------------------------------------- #
# (c) modes
# --------------------------------------------------------------------------- #
def test_scale_mode_scales():
    stack = ToyStack(n_layers=1)
    x = torch.randn(1, 4, 4)
    base = stack.model.layers[0].mlp(x).clone()
    with AllPositionMLPAblate(stack, [0], mode="scale", alpha=0.25):
        out = stack.model.layers[0].mlp(x).clone()
    assert torch.allclose(out, 0.25 * base), (out, base)
    with AllPositionMLPAblate(stack, [0], mode="scale", alpha=0.0):
        out0 = stack.model.layers[0].mlp(torch.ones(1, 1, 4))
    assert torch.all(out0 == 0), "alpha=0 scale == zero, also on a decode step"


def test_project_out_removes_direction_and_leaves_complement_bit_identical():
    stack = ToyStack(n_layers=1)
    d = torch.tensor([3.0, 0.0, 0.0, 0.0])          # NOT unit norm; axis-aligned on coord 0
    for seq in (6, 1):                               # prefill AND decode-shaped
        x = torch.randn(1, seq, 4)
        base = stack.model.layers[0].mlp(x).clone()
        with AllPositionMLPAblate(stack, [0], mode="project_out", direction=d):
            out = stack.model.layers[0].mlp(x).clone()
        assert torch.allclose(out[..., 0], torch.zeros(1, seq), atol=1e-6), \
            f"seq={seq}: the direction component must be removed"
        assert torch.equal(out[..., 1:], base[..., 1:]), \
            f"seq={seq}: the orthogonal complement must be BIT-IDENTICAL"


def test_project_out_alpha_scales_the_removal():
    stack = ToyStack(n_layers=1)
    d = torch.tensor([0.0, 1.0, 0.0, 0.0])
    x = torch.randn(1, 3, 4)
    base = stack.model.layers[0].mlp(x).clone()
    with AllPositionMLPAblate(stack, [0], mode="project_out", direction=d, alpha=0.5):
        out = stack.model.layers[0].mlp(x).clone()
    assert torch.allclose(out[..., 1], 0.5 * base[..., 1]), (out[..., 1], base[..., 1])


def test_project_out_requires_direction():
    stack = ToyStack(n_layers=1)
    try:
        AllPositionMLPAblate(stack, [0], mode="project_out")
    except ValueError:
        return
    raise AssertionError("mode='project_out' without `direction` must raise ValueError")


def test_mean_mode_is_prefill_only_by_construction():
    """Same convention/caveat as AllPositionZHeadAblate: the seq-axis mean is an identity
    no-op on a decode step (seq == 1); it is documented as prefill-only."""
    stack = ToyStack(n_layers=1, shifts=[0.0])
    x = torch.tensor([[[1., 2.], [3., 6.]]])                  # mlp: 2x -> [[2,4],[6,12]]
    with AllPositionMLPAblate(stack, [0], mode="mean"):
        out = stack.model.layers[0].mlp(x)
        dec = stack.model.layers[0].mlp(torch.tensor([[[1., 2.]]]))
    assert torch.allclose(out, torch.tensor([[[4., 8.], [4., 8.]]])), out
    assert torch.equal(dec, torch.tensor([[[2., 4.]]])), "mean is a no-op on seq==1 (prefill-only)"


def test_unknown_mode_raises():
    stack = ToyStack(n_layers=1)
    try:
        AllPositionMLPAblate(stack, [0], mode="nope")
    except ValueError:
        return
    raise AssertionError("unknown mode must raise ValueError")


# --------------------------------------------------------------------------- #
# (d) cleanup
# --------------------------------------------------------------------------- #
def test_hooks_removed_after_context():
    stack = ToyStack(n_layers=3)
    x = torch.randn(1, 4, 4)
    base = stack(x).clone()
    with AllPositionMLPAblate(stack, [0, 2], mode="zero") as a:
        assert len(a._handles) == 2
    assert a._handles == [], "handles must be emptied on __exit__"
    assert torch.equal(stack(x), base), "a later forward must be unaffected"
    assert torch.equal(stack.model.layers[0].mlp(x), 2.0 * x + 1.0), "hook removed"


# --------------------------------------------------------------------------- #
# (e) NEGATIVE CONTROL — the defect that makes the old BEHAV-WRITE result prefill-only
# --------------------------------------------------------------------------- #
def test_componentoutswap_is_a_noop_on_a_decode_step_but_allposmlp_is_not():
    """pair_common.ComponentOutSwap:410 keeps only `0 <= p < seq`. On a KV-cached decode step
    seq == 1, so every prompt position is dropped and the ablation contributes NOTHING after
    prefill. AllPositionMLPAblate edits the whole tensor and still fires. This is why the
    BEHAV-WRITE behavioral null (measured with ComponentOutSwap) is untested for generation."""
    stack = ToyStack(n_layers=3)
    prompt_positions = [2, 3, 4]                              # a 5-token prompt
    hidden = 4
    zero_rows = {1: torch.zeros(len(prompt_positions), hidden)}   # "zero-ablate the L1 write"

    prefill = torch.randn(1, 5, hidden)
    decode = torch.randn(1, 1, hidden)                         # the cached decode step
    base_pre, base_dec = stack(prefill).clone(), stack(decode).clone()

    with ComponentOutSwap(stack, prompt_positions, zero_rows, component="mlp_out"):
        cos_pre, cos_dec = stack(prefill).clone(), stack(decode).clone()
    assert not torch.allclose(cos_pre, base_pre), "ComponentOutSwap does fire on PREFILL"
    assert torch.equal(cos_dec, base_dec), \
        "ComponentOutSwap must be an exact NO-OP on a decode step (the documented defect)"

    with AllPositionMLPAblate(stack, [1], mode="zero"):
        aps_dec = stack(decode).clone()
    assert not torch.allclose(aps_dec, base_dec), \
        "AllPositionMLPAblate must still ablate on the decode step"


def test_componentoutswap_writes_misaligned_rows_when_position_zero_survives():
    """Second failure shape of the same guard: if position 0 is among the targets it is the ONE
    position still 'in range' at seq == 1, so ComponentOutSwap writes the row meant for prompt
    position 0 onto the GENERATED token — a partial, misaligned ablation rather than a no-op."""
    stack = ToyStack(n_layers=1, shifts=[0.0])
    rows = {0: torch.stack([torch.full((4,), 7.0), torch.full((4,), 9.0)])}   # pos0 -> 7, pos3 -> 9
    decode = torch.zeros(1, 1, 4)
    with ComponentOutSwap(stack, [0, 3], rows, component="mlp_out"):
        out = stack(decode)
    assert torch.allclose(out[0, 0], torch.full((4,), 7.0)), \
        "only the pos-0 row survives the guard, and it lands on the generated token"


TESTS = [test_fires_on_prefill_and_on_decode_step,
         test_decode_step_mlp_output_is_exactly_zeroed,
         test_tuple_output_mlp_is_handled,
         test_only_requested_layers_touched,
         test_layer_index_out_of_range_raises,
         test_scale_mode_scales,
         test_project_out_removes_direction_and_leaves_complement_bit_identical,
         test_project_out_alpha_scales_the_removal,
         test_project_out_requires_direction,
         test_mean_mode_is_prefill_only_by_construction,
         test_unknown_mode_raises,
         test_hooks_removed_after_context,
         test_componentoutswap_is_a_noop_on_a_decode_step_but_allposmlp_is_not,
         test_componentoutswap_writes_misaligned_rows_when_position_zero_survives]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS) - fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
