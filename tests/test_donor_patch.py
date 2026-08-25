"""DonorPatch: the alignment guard, the shape contract, and that it actually writes.

A donor patch is the ideal host for this repo's absolute-position-index bug class, because donor and
recipient are two different forward passes. These tests exist so a misaligned rescue cannot produce a
plausible null.
"""
from __future__ import annotations

import os
import sys

import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
from donor_patch import DonorBlock  # noqa: E402


def test_shape_contract_rows_must_match_positions():
    with pytest.raises(ValueError, match="rows for"):
        DonorBlock(layer_idx=3, positions=[1, 2, 3], acts=torch.zeros(2, 8), input_ids=[0] * 5)


def test_acts_must_be_two_dimensional():
    with pytest.raises(ValueError, match=r"\[n_positions, hidden\]"):
        DonorBlock(layer_idx=3, positions=[1], acts=torch.zeros(8), input_ids=[0] * 5)


def test_duplicate_positions_are_refused():
    """Two rows targeting one position makes the written value depend on write order."""
    with pytest.raises(ValueError, match="duplicates"):
        DonorBlock(layer_idx=3, positions=[2, 2], acts=torch.zeros(2, 8), input_ids=[0] * 5)


def test_valid_block_constructs():
    b = DonorBlock(layer_idx=3, positions=[1, 2], acts=torch.zeros(2, 8), input_ids=[9, 9, 9, 9])
    assert b.acts.shape == (2, 8) and b.positions == [1, 2]


# --- the alignment guard, exercised through a fake model ------------------------------------ #

class _FakeLayer(torch.nn.Module):
    def forward(self, x):
        return x


class _FakeModel(torch.nn.Module):
    def __init__(self, n=4):
        super().__init__()
        self.layers = torch.nn.ModuleList([_FakeLayer() for _ in range(n)])


@pytest.fixture()
def patched_ds_common(monkeypatch):
    import donor_patch as dp
    monkeypatch.setattr(dp.dc, "_get_layers", lambda m: m.layers)
    return dp


def test_strict_ids_refuses_a_token_mismatch(patched_ds_common):
    dp = patched_ds_common
    donor = DonorBlock(0, [1, 2], torch.zeros(2, 4), input_ids=[10, 11, 12, 13])
    with pytest.raises(ValueError, match="REFUSING to patch"):
        dp.DonorPatch(_FakeModel(), donor, recipient_input_ids=[10, 11, 99, 13])


def test_strict_ids_accepts_identical_span(patched_ds_common):
    dp = patched_ds_common
    donor = DonorBlock(0, [1, 2], torch.zeros(2, 4), input_ids=[10, 11, 12, 13])
    dp.DonorPatch(_FakeModel(), donor, recipient_input_ids=[10, 11, 12, 77])  # pos 3 may differ


def test_strict_ids_refuses_when_donor_carries_no_ids(patched_ds_common):
    dp = patched_ds_common
    donor = DonorBlock(0, [1], torch.zeros(1, 4), input_ids=[])
    with pytest.raises(ValueError, match="no input_ids"):
        dp.DonorPatch(_FakeModel(), donor, recipient_input_ids=[1, 2, 3])


def test_a_short_recipient_is_refused_not_truncated(patched_ds_common):
    dp = patched_ds_common
    donor = DonorBlock(0, [5], torch.zeros(1, 4), input_ids=[0] * 6)
    with pytest.raises(ValueError, match="REFUSING to patch"):
        dp.DonorPatch(_FakeModel(), donor, recipient_input_ids=[0, 0])


def test_patch_actually_writes_and_reports_liveness(patched_ds_common):
    dp = patched_ds_common
    model = _FakeModel()
    src = torch.arange(8, dtype=torch.float32).reshape(2, 4)
    donor = DonorBlock(0, [1, 2], src, input_ids=[7, 7, 7, 7])
    h = torch.zeros(1, 4, 4)
    with dp.DonorPatch(model, donor, recipient_input_ids=[7, 7, 7, 7]) as P:
        out = model.layers[0](h)
    assert torch.equal(out[0, 1], src[0]) and torch.equal(out[0, 2], src[1])
    assert torch.equal(out[0, 0], torch.zeros(4)), "position 0 must be untouched"
    assert torch.equal(out[0, 3], torch.zeros(4)), "position 3 must be untouched"
    L = P.liveness()
    assert L["fired"] and L["n_positions_written"] == 2 and L["n_forward_calls"] == 1


def test_hook_is_removed_on_exit(patched_ds_common):
    dp = patched_ds_common
    model = _FakeModel()
    donor = DonorBlock(0, [1], torch.ones(1, 4), input_ids=[7, 7])
    with dp.DonorPatch(model, donor, recipient_input_ids=[7, 7]):
        pass
    out = model.layers[0](torch.zeros(1, 2, 4))
    assert torch.equal(out[0, 1], torch.zeros(4)), "patch still active after __exit__"


# --- ordering regression guard (a real bug, made and caught 2026-08-25) --------------------- #

def _score_behavior_src():
    return open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "src", "boombness", "score_behavior.py")).read()


def test_donor_capture_happens_after_ctxs_is_built():
    """`--rescue-donor self` captures under `ctxs`. If the capture sits ABOVE the line that builds
    `ctxs`, Python still resolves the name -- to the PREVIOUS loop iteration's value, because it is
    function-scoped. The donor would then be captured under the previous ROW's hooks: silent,
    plausible, and wrong. This exact mistake was made and caught during the deep review of
    2026-08-25; the guard is static because the failure is one of source order, not of behaviour on
    a single row."""
    src = _score_behavior_src()
    i_build = src.index("ctxs = make_intervention(")
    i_cap = src.index("_cap = ActivationCapture(")
    assert i_build < i_cap, (
        "donor capture appears BEFORE `ctxs = make_intervention(...)`; under --rescue-donor self "
        "this reads the previous row's hooks")


def test_rescue_is_inert_without_the_flag():
    """Every rescue statement must sit inside `if args.rescue_layer is not None:`."""
    src = _score_behavior_src()
    assert "if args.rescue_layer is not None:" in src
    guard = src.index("if args.rescue_layer is not None:")
    for token in ("_cap = ActivationCapture(", "DonorBlock(", "DonorPatch(lm.model"):
        assert src.index(token, guard) > guard, f"{token} is not under the rescue guard"


def test_identity_control_option_exists():
    """Without a `self` donor there is no end-to-end identity control, and a rescue instrument
    without one cannot show it writes what it read."""
    src = _score_behavior_src()
    assert 'choices=("clean", "self")' in src
    assert 'args.rescue_donor == "self"' in src


def test_rescue_liveness_is_recorded_on_the_row():
    """A rescue that never fired produces a null identical to "the information was not there".
    The two are only separable if the artifact says which happened, so DonorPatch.liveness() must
    reach the row. The first draft of this feature built liveness and never recorded it; the smoke
    completed cleanly and could not prove the patch had done anything."""
    src = _score_behavior_src()
    assert "_rescue_ctx.liveness()" in src, "DonorPatch.liveness() is never called"
    assert '"rescue_liveness": _rl' in src, "rescue liveness never reaches the emitted row"
    assert '"rescue_layer": args.rescue_layer' in src
