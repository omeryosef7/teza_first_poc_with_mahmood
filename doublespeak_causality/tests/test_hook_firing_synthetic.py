"""
GPU-free hook-FIRING and activation-DELTA assertions for the patching primitives (plan P4b-0.1).

WHY THIS FILE EXISTS. P4_READINESS.md:352 records that *"there is no activation-delta assertion
anywhere in this repo"*, and `phase5b_qkv.py:38-43` carries a live retraction for exactly the failure
this prevents: a Q/K/V patch whose hook silently did NOT fire produced a clean null that was read as a
scientific negative. The existing synthetic tests check that a hook, WHEN IT FIRES, edits the right
slice — they do not check that it fires at all, nor that the edit actually moves a downstream readout.
`selfswap_dev == 0.0` passes perfectly for a hook that never ran.

This file adds the two assertions every P4b cell must satisfy before its number is trusted:
  * FIRING   — the pre-hook is invoked exactly once per forward, and its edit reaches the module output.
  * DELTA    — a NON-self donor moves the o_proj output (donor_dist > 0); a SELF donor does not
               (donor_dist == 0.0 exactly). A null is only interpretable when the non-self donor
               demonstrably fired.

It reuses the ToyModel harness from tests/test_zhead_synthetic.py rather than building a second one.

Run:  python doublespeak_causality/tests/test_hook_firing_synthetic.py
      pytest doublespeak_causality/tests/test_hook_firing_synthetic.py -q
"""
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pair_common as pc                                   # noqa: E402
from tests.test_zhead_synthetic import ToyModel            # noqa: E402  (reuse, do not duplicate)


def _count_calls(module):
    """Attach a counting forward_pre_hook and return (handle, box) where box[0] is the call count.
    Independent of the primitive under test — it observes the SAME module the primitive hooks, so if
    the primitive's own hook is registered and fires, the module is exercised the expected number of
    times per forward."""
    box = [0]

    def _h(mod, args):
        box[0] += 1
        return None

    return module.register_forward_pre_hook(_h), box


def test_zheadpatch_hook_fires_once_per_forward():
    # head-2 slice is pushed far from the zero donor so the patch MUST move the output if it fired.
    torch.manual_seed(7)
    m = ToyModel(n_heads=4, head_dim=3)
    z = torch.randn(1, 6, 12) + 4.0
    o_proj = m.model.layers[0].self_attn.o_proj
    base = m.apply_o_proj(0, z)
    handle, box = _count_calls(o_proj)
    try:
        with pc.ZHeadPatch(m, 0, head=1, positions=[2, 4], corrupt_vec=torch.zeros(3)):
            out1 = m.apply_o_proj(0, z)
            m.apply_o_proj(0, z)
    finally:
        handle.remove()
    # (a) two forwards through the hooked module -> the observer counts exactly two invocations,
    assert box[0] == 2, f"expected 2 forwards through o_proj, counted {box[0]}"
    # (b) AND the patch actually changed the output. Counting alone is not enough: the observer hook
    #     fires whether or not ZHeadPatch's OWN hook did, so a dead ZHeadPatch would still count 2.
    #     Requiring an output delta is what makes this a firing test rather than a forward-count test.
    assert float((out1 - base).abs().max()) > 0.0, ("ZHeadPatch registered no effect on the output — "
                                                    "its hook did not fire (silent no-op)")


def test_nonself_donor_moves_output_self_donor_does_not():
    """The core anti-silent-no-op contract: a real donor MUST move the readout, a self donor must NOT.
    If the non-self case ever yields 0.0 the hook did not fire, and any 'null' built on it is void."""
    torch.manual_seed(3)
    m = ToyModel(n_heads=4, head_dim=3)
    z = torch.randn(1, 5, 12)
    base = m.apply_o_proj(0, z)

    # self donor: patch head 2 at pos 1 with ITS OWN current z -> exact no-op
    self_vec = z.view(1, 5, 4, 3)[0, 1, 2, :].clone()
    with pc.ZHeadPatch(m, 0, head=2, positions=[1], corrupt_vec=self_vec):
        out_self = m.apply_o_proj(0, z)
    donor_dist_self = float((out_self - base).abs().max())
    assert donor_dist_self == 0.0, f"self donor must be an exact no-op, got {donor_dist_self}"

    # non-self donor: a different vector MUST change the o_proj output
    other_vec = self_vec + 5.0
    with pc.ZHeadPatch(m, 0, head=2, positions=[1], corrupt_vec=other_vec):
        out_other = m.apply_o_proj(0, z)
    donor_dist = float((out_other - base).abs().max())
    assert donor_dist > 0.0, ("non-self donor did NOT move the output — the hook silently no-opped; "
                              "this is exactly the phase5b retraction failure mode")


def test_zero_donor_is_not_confused_with_a_dead_hook():
    """A ZERO donor is a legitimate intervention (ablate the head), and it MUST move a readout whose
    head slice was non-zero. Distinguishing 'zeroed a real signal' (delta>0) from 'hook never fired'
    (delta==0) is the whole point — they look identical if you only check the arm ran without error."""
    torch.manual_seed(4)
    m = ToyModel(n_heads=4, head_dim=3)
    z = torch.randn(1, 4, 12) + 3.0                        # ensure head-2 slice is far from zero
    base = m.apply_o_proj(0, z)
    with pc.ZHeadPatch(m, 0, head=2, positions=[0, 1, 2, 3], corrupt_vec=torch.zeros(3)):
        out_zero = m.apply_o_proj(0, z)
    delta = float((out_zero - base).abs().max())
    assert delta > 0.0, "zeroing a non-zero head slice must change the output; delta==0 means dead hook"


def test_out_of_range_position_is_a_true_noop_not_a_silent_failure():
    """Decode-step safety (seq==1, position out of range) is a DESIGNED no-op. Confirm it is a no-op
    for the RIGHT reason: the hook fired, examined the positions, and correctly skipped them —
    verified by pairing it with an in-range position that DOES move, in the same edit list."""
    torch.manual_seed(5)
    m = ToyModel(n_heads=4, head_dim=3)
    z = torch.randn(1, 3, 12)                               # seq == 3
    base = m.apply_o_proj(0, z)
    # position 99 is out of range and must be skipped; position 1 is in range and must apply.
    with pc.ZHeadPatch(m, 0, head=0, positions=[1, 99], corrupt_vec=torch.full((3,), 7.0)):
        out = m.apply_o_proj(0, z)
    # reconstruct: only position 1 changes
    zr = z.view(1, 3, 4, 3).clone()
    zr[0, 1, 0, :] = 7.0
    expected = m.model.layers[0].self_attn.o_proj(zr.view(1, 3, 12))
    assert torch.allclose(out, expected, atol=1e-6), "in-range edit must apply while out-of-range skips"
    assert float((out - base).abs().max()) > 0.0, "the in-range edit must still move the output"


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} hook-firing assertions passed")


if __name__ == "__main__":
    _run_all()
