"""
GPU-free synthetic tests for pair_common.SubmodulePatch on its attn_out / mlp_out /
resid_post component paths (plan §P0 / §0.9 — untested hook primitives). Only the
resid_pre path was covered, by tests/test_submodule_resid_pre_synthetic.py; this file
covers the sub-block OUTPUT paths and the prefill-only defect.

No model, no GPU, deterministic. The toy block mimics the HF decoder-layer interface:
`self_attn` returns a TUPLE (exercises the tuple branch of `_hook`), `mlp` returns a plain
tensor, and the block itself returns a tuple.

Asserts:
  (a) SELF-PATCH — replacing a component's output with the value it already had is an
      EXACT no-op, on attn_out, mlp_out and resid_post;
  (b) replace / add / project_out behave as documented at the targeted position, and only
      at that position; alpha scales add and project_out; project_out(alpha=1) leaves a
      component orthogonal to the direction;
  (c) batch>1 raises NotImplementedError; unknown component / unknown mode raise; the
      handle is removed on __exit__;
  (d) *** PREFILL-ONLY DEFECT ***: on a decode-shaped forward (seq==1) every prompt
      position is out of range and `_edit` `continue`s, so the patch is a SILENT no-op —
      no error, output bit-identical to baseline. This is the defect that made the
      BEHAV-WRITE behavioural result prefill-only: under generate(), the patch applies to
      the prefill pass and then quietly stops applying for every generated token.

Run:  python -m pytest doublespeak_causality/tests/test_submodulepatch_components_synthetic.py -q
"""
import os
import sys

import pytest
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import SubmodulePatch  # noqa: E402

H = 6


# --------------------------------------------------------------------------- #
# Toy model
# --------------------------------------------------------------------------- #
class ToyAttn(nn.Module):
    """Returns a TUPLE (attn_out, weights) like a real HF self_attn."""

    def __init__(self, shift: float):
        super().__init__()
        self.shift = shift

    def forward(self, x):
        return (x + self.shift, None)


class ToyMLP(nn.Module):
    """Returns a plain tensor like a real HF mlp."""

    def __init__(self, scale: float):
        super().__init__()
        self.scale = scale

    def forward(self, x):
        return x * self.scale


class ToyBlock(nn.Module):
    """resid_post = (x + attn_out) + mlp(x + attn_out)."""

    def __init__(self, shift: float, scale: float):
        super().__init__()
        self.self_attn = ToyAttn(shift)
        self.mlp = ToyMLP(scale)

    def forward(self, x):
        mid = x + self.self_attn(x)[0]
        return (mid + self.mlp(mid), None)


class ToyStack(nn.Module):
    def __init__(self, n_layers=3, shifts=None, scales=None):
        super().__init__()
        shifts = shifts if shifts is not None else [i + 1.0 for i in range(n_layers)]
        scales = scales if scales is not None else [1.0] * n_layers
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(
            ToyBlock(sh, sc) for sh, sc in zip(shifts, scales))

    def forward(self, x):
        for blk in self.model.layers:
            x, _ = blk(x)
        return x


def _capture(stack, li, component, x):
    """Capture a component's output rows for one forward (reference for self-patch)."""
    mod = {"attn_out": stack.model.layers[li].self_attn,
           "mlp_out": stack.model.layers[li].mlp,
           "resid_post": stack.model.layers[li]}[component]
    store = {}

    def f(m, inp, out):
        store["h"] = (out[0] if isinstance(out, tuple) else out).clone()

    handle = mod.register_forward_hook(f)
    stack(x)
    handle.remove()
    return store["h"]


# --------------------------------------------------------------------------- #
# (a) self-patch is an exact no-op
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("component", ["attn_out", "mlp_out", "resid_post"])
def test_self_patch_is_exact_noop(component):
    torch.manual_seed(0)
    stack = ToyStack(n_layers=3, scales=[0.5, 0.25, 0.5])
    x = torch.randn(1, 5, H)
    base = stack(x).clone()
    p = 2
    cap = _capture(stack, 1, component, x)          # [1, seq, H]
    with SubmodulePatch(stack, 1, component, positions=[p], vector=cap[0, p],
                        mode="replace"):
        out = stack(x)
    assert torch.equal(out, base), f"{component}: self-patch must be EXACT"


# --------------------------------------------------------------------------- #
# (b) modes
# --------------------------------------------------------------------------- #
def test_attn_out_replace_writes_exact_value_and_propagates():
    # single layer, shift 0, scale 0 => resid_post = x + attn_out
    stack = ToyStack(n_layers=1, shifts=[0.0], scales=[0.0])
    x = torch.zeros(1, 4, H)
    v = torch.full((H,), 100.0)
    with SubmodulePatch(stack, 0, "attn_out", positions=[2], vector=v, mode="replace"):
        out = stack(x)
    assert torch.allclose(out[0, 2], v), out[0, 2]
    for p in (0, 1, 3):
        assert torch.allclose(out[0, p], torch.zeros(H)), f"pos {p} must be untouched"


def test_mlp_out_replace_writes_exact_value_and_propagates():
    # resid_post = mid + mlp_out, mid = x (shift 0 => attn_out = x, mid = 2x); use x=0
    stack = ToyStack(n_layers=1, shifts=[0.0], scales=[0.0])
    x = torch.zeros(1, 4, H)
    v = torch.full((H,), -7.0)
    with SubmodulePatch(stack, 0, "mlp_out", positions=[1, 3], vector=v, mode="replace"):
        out = stack(x)
    assert torch.allclose(out[0, 1], v) and torch.allclose(out[0, 3], v)
    assert torch.allclose(out[0, 0], torch.zeros(H))


def test_replace_writes_the_SAME_vector_to_every_position():
    """Documented contract difference vs ComponentOutSwap: SubmodulePatch broadcasts ONE
    shared vector to all `positions` (per-position rows need ComponentOutSwap)."""
    stack = ToyStack(n_layers=1, shifts=[0.0], scales=[0.0])
    x = torch.zeros(1, 3, H)
    v = torch.arange(H, dtype=torch.float32)
    with SubmodulePatch(stack, 0, "attn_out", positions=[0, 2], vector=v, mode="replace"):
        out = stack(x)
    assert torch.allclose(out[0, 0], v) and torch.allclose(out[0, 2], v)


@pytest.mark.parametrize("component", ["attn_out", "mlp_out"])
@pytest.mark.parametrize("alpha", [0.0, 1.0, 2.5])
def test_add_mode_scales_by_alpha(component, alpha):
    torch.manual_seed(1)
    stack = ToyStack(n_layers=2, scales=[0.5, 0.5])
    x = torch.randn(1, 4, H)
    base_comp = _capture(stack, 0, component, x)
    v = torch.randn(H)
    with SubmodulePatch(stack, 0, component, positions=[1], vector=v, mode="add",
                        alpha=alpha):
        got = _capture_under_patch(stack, 0, component, x)
    want = base_comp.clone()
    want[0, 1] = want[0, 1] + alpha * v
    assert torch.allclose(got, want, atol=1e-6)


def _capture_under_patch(stack, li, component, x):
    """Capture the component output while an outer SubmodulePatch context is active.

    The patch hook is registered FIRST, so this later-registered capture hook sees the
    already-edited output (PyTorch runs forward hooks in registration order and feeds each
    the previous hook's return value)."""
    return _capture(stack, li, component, x)


def test_add_alpha_zero_is_identity():
    torch.manual_seed(2)
    stack = ToyStack(n_layers=3, scales=[0.5, 0.5, 0.5])
    x = torch.randn(1, 4, H)
    base = stack(x).clone()
    with SubmodulePatch(stack, 1, "mlp_out", positions=[0, 1, 2, 3],
                        vector=torch.randn(H), mode="add", alpha=0.0):
        out = stack(x)
    assert torch.allclose(out, base, atol=1e-6)


@pytest.mark.parametrize("component", ["attn_out", "mlp_out"])
def test_project_out_removes_the_component_along_v(component):
    torch.manual_seed(3)
    stack = ToyStack(n_layers=2, scales=[0.5, 0.5])
    x = torch.randn(1, 4, H)
    v = torch.randn(H)
    d = v / v.norm()
    with SubmodulePatch(stack, 0, component, positions=[2], vector=v,
                        mode="project_out", alpha=1.0):
        got = _capture(stack, 0, component, x)
    assert abs(float(torch.dot(got[0, 2], d))) < 1e-5, "row must be orthogonal to v"
    # untouched rows keep their original projection
    base = _capture(stack, 0, component, x)
    for p in (0, 1, 3):
        assert torch.allclose(got[0, p], base[0, p], atol=1e-6)


def test_project_out_alpha_zero_is_identity():
    torch.manual_seed(4)
    stack = ToyStack(n_layers=2, scales=[0.5, 0.5])
    x = torch.randn(1, 4, H)
    base = stack(x).clone()
    with SubmodulePatch(stack, 0, "attn_out", positions=[1], vector=torch.randn(H),
                        mode="project_out", alpha=0.0):
        out = stack(x)
    assert torch.allclose(out, base, atol=1e-6)


def test_project_out_alpha_two_overshoots_by_construction():
    """alpha=2 flips the sign of the component along d (documents the linear form)."""
    torch.manual_seed(5)
    stack = ToyStack(n_layers=1, shifts=[0.0], scales=[0.0])
    x = torch.randn(1, 3, H)
    v = torch.randn(H)
    d = v / v.norm()
    base = _capture(stack, 0, "attn_out", x)
    before = float(torch.dot(base[0, 1], d))
    with SubmodulePatch(stack, 0, "attn_out", positions=[1], vector=v,
                        mode="project_out", alpha=2.0):
        got = _capture(stack, 0, "attn_out", x)
    after = float(torch.dot(got[0, 1], d))
    assert after == pytest.approx(-before, abs=1e-4), (before, after)


# --------------------------------------------------------------------------- #
# (c) validation / hygiene
# --------------------------------------------------------------------------- #
def test_unknown_component_raises():
    stack = ToyStack(n_layers=1)
    with pytest.raises(ValueError):
        SubmodulePatch(stack, 0, "bogus_out", positions=[0], vector=torch.zeros(H))


def test_unknown_mode_raises_at_forward_time():
    stack = ToyStack(n_layers=1)
    with pytest.raises(ValueError):
        with SubmodulePatch(stack, 0, "attn_out", positions=[0], vector=torch.zeros(H),
                            mode="bogus"):
            stack(torch.zeros(1, 3, H))


@pytest.mark.parametrize("component", ["attn_out", "mlp_out", "resid_post"])
def test_batch_gt_one_raises(component):
    stack = ToyStack(n_layers=1)
    with pytest.raises(NotImplementedError):
        with SubmodulePatch(stack, 0, component, positions=[0], vector=torch.zeros(H)):
            stack(torch.zeros(2, 3, H))


@pytest.mark.parametrize("component", ["attn_out", "mlp_out", "resid_post"])
def test_handle_removed_on_exit(component):
    stack = ToyStack(n_layers=2, scales=[0.5, 0.5])
    x = torch.randn(1, 3, H)
    base = stack(x).clone()
    with SubmodulePatch(stack, 0, component, positions=[0],
                        vector=torch.full((H,), 99.0)) as sp:
        pass
    assert sp._handle is None, "handle must be cleared on __exit__"
    assert torch.equal(stack(x), base), "hook must be gone"


def test_negative_positions_are_skipped_not_python_indexed():
    """p < 0 is skipped (NOT treated as a from-the-end index)."""
    stack = ToyStack(n_layers=1, shifts=[0.0], scales=[0.0])
    x = torch.zeros(1, 4, H)
    base = stack(x).clone()
    with SubmodulePatch(stack, 0, "attn_out", positions=[-1],
                        vector=torch.full((H,), 5.0), mode="replace"):
        out = stack(x)
    assert torch.equal(out, base), "-1 must be skipped, not mapped to the last position"


# --------------------------------------------------------------------------- #
# (d) THE PREFILL-ONLY DEFECT — silent no-op on decode-shaped forwards
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("component", ["attn_out", "mlp_out", "resid_post", "resid_pre"])
def test_decode_step_out_of_range_position_is_a_SILENT_noop(component):
    """*** THE BEHAV-WRITE DEFECT ***

    pair_common.py:322 -- `if p < 0 or p >= seq: continue`. On a KV-cached decode step the
    forward carries ONLY the new token (seq==1), so every prompt position is out of range
    and the patch does nothing, WITHOUT raising and WITHOUT any signal to the caller. Under
    generate(), the intervention therefore applies to the prefill pass only and silently
    stops for every generated token: any behavioural claim built on SubmodulePatch +
    generate() is a PREFILL-ONLY claim. Use an all-position hook (AllPositionProjectOut /
    AllPositionAdd / AllPositionZHeadAblate) for a generation-time intervention.
    """
    stack = ToyStack(n_layers=2, scales=[0.5, 0.5])
    x_decode = torch.randn(1, 1, H)                    # seq == 1, a decode step
    base = stack(x_decode).clone()
    huge = torch.full((H,), 1e4)
    with SubmodulePatch(stack, 0, component, positions=[7, 12], vector=huge,
                        mode="replace"):
        out = stack(x_decode)                          # must NOT raise
    assert torch.equal(out, base), (
        f"{component}: out-of-range positions on a seq==1 forward are a silent no-op")


def test_decode_step_position_zero_DOES_apply():
    """The no-op above is about out-of-range indices; position 0 is in range even at
    seq==1, which is why the defect is silent rather than obvious."""
    stack = ToyStack(n_layers=1, shifts=[0.0], scales=[0.0])
    x_decode = torch.zeros(1, 1, H)
    v = torch.full((H,), 3.0)
    with SubmodulePatch(stack, 0, "attn_out", positions=[0], vector=v, mode="replace"):
        out = stack(x_decode)
    assert torch.allclose(out[0, 0], v)


def test_mixed_in_and_out_of_range_applies_the_in_range_subset():
    """Partial application (no all-or-nothing guard): the in-range position IS patched
    while the out-of-range ones are dropped, so a multi-position write silently degrades
    to a subset rather than failing."""
    stack = ToyStack(n_layers=1, shifts=[0.0], scales=[0.0])
    x = torch.zeros(1, 2, H)
    v = torch.full((H,), 4.0)
    with SubmodulePatch(stack, 0, "attn_out", positions=[1, 50], vector=v,
                        mode="replace"):
        out = stack(x)
    assert torch.allclose(out[0, 1], v), "in-range position patched"
    assert torch.allclose(out[0, 0], torch.zeros(H)), "other position untouched"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
