#!/usr/bin/env python3
"""S-007 / plan §6: the Phase-2 NECESSITY arm (`--rescue-donor ko`) and the contract it needs.

THE DEFECT THIS CLOSES. Everything scored so far tests SUFFICIENCY: under a live knockout, add the
clean state's component back along the installation axis (`h' = h_ko + P_w(h_clean - h_ko)`, D12,
+3.9%). NECESSITY is the other direction -- start from a CLEAN, high-installation forward and
REMOVE the installed component (`h' = h_clean - P_w(h_clean - h_ko)`) -- and it could not be
expressed by any flag: the donor was captured under the knockout only for `--rescue-donor self`,
and the patch was always composed ON TOP of the live knockout.

*** THE DANGER THE ARM INTRODUCES, WHICH IS WHAT MOST OF THIS FILE IS ABOUT. ***
Every other knockout arm is trustworthy because the knockout is verified LIVE on the forward that
produced the number. On this arm it is deliberately NOT live there. Two failure modes follow, and
both produce a plausible number rather than a crash:

  * the ordinary liveness gate is SILENTLY SATISFIED BY THE WRONG FORWARD. The hook's stats dict
    is shared across a row, and the donor capture increments it, so an unchanged gate would read
    "prefill edits > 0 on every row" and be describing the donor capture while the reader takes it
    for the readout;
  * the gate is skipped for this arm, leaving an arm with no liveness evidence at all -- the
    "check that cannot fail" shape of reviews R3-B1 and S-074a.

So the tests below assert BOTH halves of every claim: the arm does the right thing, AND it refuses
when any leg of its contract is untrue.

  1. the COMPOSITION is the necessity one, numerically: patch-without-the-knockout reproduces
     `h_clean - P_w(h_clean - h_ko)`, and it is NOT the sufficiency composition;
  2. the built-in POSITIVE CONTROL works: whole-state removal writes the ENTIRE ko state, so the
     readout state at those positions IS the ko state (plan §15's "if this does not move,
     the instrument is broken and any subspace null is CANNOT ANSWER");
  3. the donor is captured UNDER the knockout while the readout forward is knockout-FREE --
     measured from the knockout's own counters, not asserted;
  4. LEG 4's measurement depends on hook REGISTRATION ORDER (the clean capture must be entered
     ahead of the patch to see the pre-patch state); that dependence is pinned here, because if it
     inverted the measured difference would be 0 and every row would be refused;
  5. the four-leg gate REFUSES each way the arm can be broken: a dead donor knockout, a knockout
     that leaked into the readout, a patch that never fired, and a KO state that does not differ
     from the clean one (nothing to remove);
  6. the run-level gate refuses an empty block, ZERO rows, and any failing row -- a gate that
     never ran is not a pass;
  7. the R2-M3 cross-layer basis guard still refuses under the new donor mode;
  8. main() is actually wired this way: the donor capture enters the arm's hooks for `ko`, the
     readout drops them BY IDENTITY, and the three preconditions are refusals and not warnings.

Run: python -m pytest tests/test_necessity_arm.py -q
"""
import ast
import contextlib
import importlib.util
import os
import sys
import types

import pytest
import torch
import torch.nn as nn

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
from donor_patch import (ActivationCapture, DonorBlock, DonorPatch,  # noqa: E402
                         SubspaceDonorPatch, orthonormalise)

SB_PATH = os.path.join(REPO, "src", "boombness", "score_behavior.py")
SCOPE = "target_surface_row_only"          # the scope every Phase-1 arm ran under

H = 16
L = 3
IDS = [5, 9, 3, 11, 2, 8, 4]
POS = [2, 3, 4]
LAYER = 1
torch.manual_seed(20260917)


# --------------------------------------------------------------------------- a real hook harness
class _Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.lin = nn.Linear(H, H)

    def forward(self, x):
        return (self.lin(torch.tanh(x)),)


class _Inner(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.ModuleList([_Block() for _ in range(L)])


class _Model(nn.Module):
    """Minimal stand-in exposing `model.model.layers`, which is what `dc._get_layers` looks for."""

    def __init__(self):
        super().__init__()
        self.model = _Inner()
        self.emb = nn.Embedding(50, H)

    def forward(self, input_ids=None):
        x = self.emb(input_ids)
        for blk in self.model.layers:
            x = blk(x)[0]
        return x


class _FakeKnockout:
    """A stand-in for the attention knockout: it CHANGES the forward and COUNTS what it did.

    It is not the real hook -- the real one edits an attention mask and needs a real model -- but
    it is the two properties the necessity contract actually reads: it perturbs the state the donor
    is captured from, and it writes `pair_common`-shaped counters into a stats dict that the SAME
    `knockout_counter_delta` / `readout_liveness_violations` the run uses can be pointed at. That
    is what makes "the donor was captured under it and the readout was not" a measurement here
    rather than a comment.
    """

    def __init__(self, model, layer_idx, stats, delta=0.7):
        self.layer = model.model.layers[layer_idx]
        self.stats = stats
        # A PER-POSITION perturbation, not a constant one, and fixed across forwards. A constant
        # offset makes `h_clean - h_ko` the SAME vector at every position, i.e. exactly rank 1 --
        # under which a rank-1 subspace removal is indistinguishable from the whole-state one and
        # the positive-control test below would compare two identical numbers and still pass.
        g = torch.Generator().manual_seed(4242)
        self.noise = torch.randn(1, 64, H, generator=g) * float(delta)
        self._h = None

    def _hook(self, module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        self.stats["n_forward"] = self.stats.get("n_forward", 0) + 1
        self.stats["n_prefill_forward"] = self.stats.get("n_prefill_forward", 0) + 1
        self.stats["n_edits"] = self.stats.get("n_edits", 0) + hidden.shape[1]
        self.stats["n_prefill_edits"] = self.stats.get("n_prefill_edits", 0) + hidden.shape[1]
        self.stats.setdefault("n_decode_edits", 0)
        self.stats.setdefault("n_decode_forward", 0)
        hidden = hidden + self.noise[:, :hidden.shape[1], :].to(hidden.dtype).to(hidden.device)
        return (hidden,) + tuple(output[1:]) if isinstance(output, tuple) else hidden

    def __enter__(self):
        self._h = self.layer.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._h is not None:
            self._h.remove()
        return False


def _load_sb():
    """score_behavior.py by path. It is a script, not a package module."""
    spec = importlib.util.spec_from_file_location("score_behavior_necessity", SB_PATH)
    m = importlib.util.module_from_spec(spec)
    sys.modules["score_behavior_necessity"] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def sb():
    return _load_sb()


@pytest.fixture(scope="module")
def harness():
    """One model, and the three states the arm is defined in terms of: clean, ko, and the axis."""
    model = _Model().eval()

    def run(ctxs=()):
        with contextlib.ExitStack() as st:
            for c in ctxs:
                st.enter_context(c)
            with torch.no_grad():
                return model(input_ids=torch.tensor([IDS]))

    def capture(ctxs=(), after=None):
        """Capture at LAYER/POS. `after` contexts are entered AFTER the capture registers."""
        cap = ActivationCapture(model, LAYER, POS)
        with contextlib.ExitStack() as st:
            for c in ctxs:
                st.enter_context(c)
            st.enter_context(cap)
            for c in (after or ()):
                st.enter_context(c)
            with torch.no_grad():
                model(input_ids=torch.tensor([IDS]))
        return cap.acts

    h_clean = capture()
    ko_stats = {}
    h_ko = capture(ctxs=[_FakeKnockout(model, LAYER, ko_stats)])
    assert float((h_ko - h_clean).norm()) > 1e-3, "the fake knockout must move the state"
    # A rank-1 'installation axis': a genuine direction of the clean-vs-ko difference, so the
    # projection is neither everything nor nothing.
    w = orthonormalise((h_clean - h_ko)[0])
    return types.SimpleNamespace(model=model, run=run, capture=capture,
                                 h_clean=h_clean, h_ko=h_ko, w=w, ko_stats=ko_stats)


def _donor_block(acts):
    return DonorBlock(layer_idx=LAYER, positions=list(POS), acts=acts, input_ids=list(IDS))


# =============================================================== 1. THE COMPOSITION IS NECESSITY
def test_ko_donor_under_a_clean_live_forward_is_the_removal_the_plan_asks_for(harness):
    """`h' = h_clean - P_w(h_clean - h_ko)`, to float tolerance, and NOT the sufficiency form.

    Both halves matter. If the arithmetic were right but the arm still composed the patch on top
    of the live knockout, the number would be the OLD arm's with a new label -- so the second
    assertion (the two compositions differ) is the one that would catch that, and it is not
    implied by the first.
    """
    h = harness
    W = h.w.to(torch.float64)
    expected = (h.h_clean.to(torch.float64)
                + ((h.h_ko.to(torch.float64) - h.h_clean.to(torch.float64)) @ W.T) @ W)

    patch = SubspaceDonorPatch(h.model, _donor_block(h.h_ko), IDS, basis=h.w)
    got = h.capture(after=[patch])                       # capture registers BEFORE -> see below
    got_after = h.capture(ctxs=[patch])                  # patch registers first -> post-patch
    assert torch.allclose(got_after.to(torch.float64), expected, atol=1e-8), \
        "necessity composition is not h_clean - P_w(h_clean - h_ko)"
    # ...and the pre-patch read is the clean state, which is what leg 4 measures against.
    assert torch.allclose(got.to(torch.float64), h.h_clean.to(torch.float64), atol=1e-12)

    # THE OTHER DIRECTION, for contrast: same primitive, donor swapped, knockout LIVE.
    suff = SubspaceDonorPatch(h.model, _donor_block(h.h_clean), IDS, basis=h.w)
    suff_state = h.capture(ctxs=[_FakeKnockout(h.model, LAYER, {}), suff])
    assert not torch.allclose(suff_state.to(torch.float64), expected, atol=1e-4), \
        "sufficiency and necessity must not be the same intervention"


def test_the_removal_moves_the_state_and_the_axis_component_is_what_moved(harness):
    """A removal that changes nothing would be indistinguishable from a null, so assert it moves.

    And assert WHERE it moved: the component along `w` must land on the ko state's, while the
    orthogonal complement must be untouched. That is the difference between "this site matters"
    and "this variable at this site matters", and a patch that quietly wrote the whole state would
    pass the first assertion and fail the second.
    """
    h = harness
    patch = SubspaceDonorPatch(h.model, _donor_block(h.h_ko), IDS, basis=h.w)
    got = h.capture(ctxs=[patch]).to(torch.float64)
    W = h.w.to(torch.float64)
    assert not torch.allclose(got, h.h_clean.to(torch.float64), atol=1e-6)
    along = lambda x: (x @ W.T)                                              # noqa: E731
    assert torch.allclose(along(got), along(h.h_ko.to(torch.float64)), atol=1e-8), \
        "the axis component did not become the ko state's"
    perp = lambda x: x - ((x @ W.T) @ W)                                     # noqa: E731
    assert torch.allclose(perp(got), perp(h.h_clean.to(torch.float64)), atol=1e-8), \
        "the orthogonal complement was disturbed; this is not a subspace intervention"


# ======================================================= 2. THE FREE POSITIVE CONTROL (plan §15)
def test_whole_state_ko_donor_writes_the_entire_ko_state_the_arms_positive_control(harness):
    """`--rescue-donor ko` with NO --rescue-basis is the necessity direction's positive control.

    It writes the whole ko state into the clean forward, so the state at those positions IS the ko
    state -- which is why the arm's installation should land near the KO arm's. Asserted here at
    the mechanism level: if this equality does not hold, the arm cannot serve as a positive
    control and a subspace null under it is CANNOT ANSWER rather than a negative.
    """
    h = harness
    patch = DonorPatch(h.model, _donor_block(h.h_ko), IDS)
    got = h.capture(ctxs=[patch])
    assert torch.allclose(got, h.h_ko, atol=1e-6), \
        "whole-state removal did not reproduce the ko state at the patched positions"
    # And it is a strictly larger intervention than the rank-1 one, so the subspace arm is bounded
    # by it rather than being a differently-constructed comparison.
    sub = SubspaceDonorPatch(h.model, _donor_block(h.h_ko), IDS, basis=h.w)
    got_sub = h.capture(ctxs=[sub])
    d_full = float((got - h.h_clean).norm())
    d_sub = float((got_sub - h.h_clean).norm())
    assert 0 < d_sub < d_full, f"rank-1 removal {d_sub} not strictly inside whole-state {d_full}"


# ============================ 3. DONOR UNDER THE KNOCKOUT, READOUT WITHOUT IT -- MEASURED
def test_the_donor_is_captured_under_the_knockout_and_the_readout_is_knockout_free(sb, harness):
    """The two halves of (a), read off the knockout's OWN counters rather than asserted.

    This is the composition main() performs: enter the arm's hooks for the donor capture, then
    drop them and enter only the patch for the readout. The counters must show prefill edits on
    the donor forward and a ZERO delta across the readout -- and `knockout_counter_delta` is used
    here because the hook's counters are cumulative over a row, which is exactly the trap that
    would let the ordinary gate pass on donor-forward evidence.
    """
    h = harness
    stats = {}
    ko = _FakeKnockout(h.model, LAYER, stats)

    donor_acts = h.capture(ctxs=[ko])                     # DONOR: under the knockout
    donor_ks = sb.knockout_row_stats(dict(stats))
    assert donor_ks["n_prefill_edits"] > 0
    assert sb.readout_liveness_violations(SCOPE, donor_ks) == [], \
        "the donor capture must satisfy the SAME reduced contract every other readout arm does"

    before = sb.knockout_row_stats(dict(stats))
    patch = DonorPatch(h.model, _donor_block(donor_acts), IDS)
    with patch:
        h.run()                                           # READOUT: patch only, no knockout
    delta = sb.knockout_counter_delta(before, stats)
    assert all(v == 0 for v in delta.values()), f"knockout was live on the readout: {delta}"
    assert patch.liveness()["n_positions_written"] > 0

    assert sb.necessity_readout_violations(
        SCOPE, donor_ks, delta, patch.liveness(),
        donor_delta_norm=float((donor_acts - h.h_clean).norm(dim=1).mean())) == []


def test_the_gate_catches_it_when_the_knockout_is_left_live_on_the_readout(sb, harness):
    """The refusing half of the same test: compose it the OLD way and the arm must be refused.

    This is the silent-bypass failure. Entering the knockout for the readout as well turns the arm
    back into the sufficiency composition, with a donor that happens to be the ko state -- an
    inert identity patch. Nothing crashes, the number is plausible, and only leg 2 separates them.
    """
    h = harness
    stats = {}
    ko = _FakeKnockout(h.model, LAYER, stats)
    donor_acts = h.capture(ctxs=[ko])
    donor_ks = sb.knockout_row_stats(dict(stats))
    before = sb.knockout_row_stats(dict(stats))
    patch = DonorPatch(h.model, _donor_block(donor_acts), IDS)
    with ko:                                              # <- the defect: still live
        with patch:
            h.run()
    delta = sb.knockout_counter_delta(before, stats)
    bad = sb.necessity_readout_violations(SCOPE, donor_ks, delta, patch.liveness(),
                                          donor_delta_norm=0.5)
    assert bad, "a knockout live on the readout was accepted"
    assert any("readout_forward" in b and "n_prefill_edits" in b for b in bad), bad


# ================================================= 4. LEG 4'S MEASUREMENT DEPENDS ON HOOK ORDER
def test_the_clean_capture_must_be_registered_ahead_of_the_patch_to_read_h_live(harness):
    """Pins the ordering main() relies on for ||h_donor - h_live||.

    `ActivationCapture` and the patch both register a forward hook on the SAME layer module, and
    PyTorch fires them in registration order. main() enters the capture first, so it reads the
    layer's output BEFORE the patch rewrites it. If that ever inverted, the capture would read the
    patched state, the measured difference would be ~0 and EVERY row would be refused -- a loud
    failure rather than a plausible number, which is the right direction to fail in, but the
    dependence is real and is asserted here rather than left to a comment.
    """
    h = harness
    patch = DonorPatch(h.model, _donor_block(h.h_ko), IDS)
    cap_first = ActivationCapture(h.model, LAYER, POS)
    cap_last = ActivationCapture(h.model, LAYER, POS)
    with contextlib.ExitStack() as st:
        st.enter_context(cap_first)                       # registered BEFORE the patch
        st.enter_context(patch)
        st.enter_context(cap_last)                        # registered AFTER the patch
        h.run()
    assert torch.allclose(cap_first.acts, h.h_clean, atol=1e-12), \
        "a capture entered before the patch must read the pre-patch (live) state"
    assert torch.allclose(cap_last.acts, h.h_ko, atol=1e-6), \
        "a capture entered after the patch must read the patched state"
    assert float((cap_first.acts - h.h_ko).norm(dim=1).mean()) > 0, \
        "the KO-vs-CLEAN difference leg 4 measures must be non-zero in this harness"


# ================================================================= 5. EACH LEG REFUSES ON ITS OWN
def _ok_inputs(sb):
    donor = {"n_forward": 1, "n_prefill_forward": 1, "n_decode_forward": 0,
             "n_edits": 12, "n_prefill_edits": 12, "n_decode_edits": 0}
    return (donor, {k: 0 for k in sb.KNOCKOUT_COUNTERS},
            {"n_positions_written": 24, "n_forward_calls": 3, "fired": True}, 0.31)


def test_a_correctly_composed_row_passes_the_four_leg_gate(sb):
    donor, delta, patch, dn = _ok_inputs(sb)
    assert sb.necessity_readout_violations(SCOPE, donor, delta, patch, dn) == []


@pytest.mark.parametrize("leg,mutate,needle", [
    # LEG 1: the donor was captured under a mask that never fired -> nothing was knocked out.
    ("donor dead", lambda d: (dict(d[0], n_edits=0, n_prefill_edits=0), d[1], d[2], d[3]),
     "donor_capture"),
    # LEG 1: no counters at all -> "captured under the knockout" is an assumption.
    ("donor unobserved", lambda d: ({}, d[1], d[2], d[3]), "never observed"),
    # LEG 2: the knockout leaked into the forward that produced the number.
    ("readout leaked", lambda d: (d[0], dict(d[1], n_prefill_edits=4), d[2], d[3]),
     "knockout-FREE"),
    # LEG 2: the delta was never taken -> the central claim is unobserved.
    ("readout unmeasured", lambda d: (d[0], None, d[2], d[3]), "assumption rather than an "
     "observation"),
    # LEG 3: legs 1 and 2 are both satisfied by doing nothing; this is what makes them non-vacuous.
    ("patch dead", lambda d: (d[0], d[1], {"n_positions_written": 0, "fired": False}, d[3]),
     "UNINTERVENED"),
    ("patch unrecorded", lambda d: (d[0], d[1], None, d[3]), "ENTIRE"),
    # LEG 4: the ko and clean states coincide -> the removal writes back what was there.
    ("nothing to remove", lambda d: (d[0], d[1], d[2], 0.0), "CANNOT lower installation"),
    ("delta unmeasured", lambda d: (d[0], d[1], d[2], None), "was not measured"),
])
def test_every_leg_refuses_on_its_own(sb, leg, mutate, needle):
    """Each way the arm can be broken must be caught by the leg that exists for it.

    Parameterised deliberately: a single "a broken arm is refused" test passes as soon as ONE leg
    works, and would have let the other three rot. That is the same shape as review R3-B1's
    finding -- a check whose passing case is not the case it was written for.
    """
    args = mutate(_ok_inputs(sb))
    bad = sb.necessity_readout_violations(SCOPE, args[0], args[1], args[2],
                                          donor_delta_norm=args[3])
    assert bad, f"{leg}: accepted a broken necessity row"
    assert any(needle in b for b in bad), f"{leg}: refused for the wrong reason: {bad}"


# =========================================================== 6. THE RUN-LEVEL GATE, BOTH HALVES
def _run_summary(sb, n_ok=3, n_bad=0):
    live = sb.new_necessity_live()
    donor, delta, patch, dn = _ok_inputs(sb)
    for _ in range(n_ok):
        sb.record_necessity_row(live, SCOPE, donor, delta, patch, donor_delta_norm=dn)
    for _ in range(n_bad):
        sb.record_necessity_row(live, SCOPE, donor, dict(delta, n_prefill_edits=7), patch,
                                donor_delta_norm=dn)
    return live, sb.necessity_summary(live, SCOPE, "ko", layer=20, basis_key="cand_rank1")


def test_a_clean_run_passes_and_records_which_forward_it_measured(sb):
    live, s = _run_summary(sb, n_ok=5)
    assert sb.assert_necessity_live(s) is True
    assert s["n_rows"] == 5 and s["frac_rows_ok"] == 1.0
    assert s["max_readout_knockout_edits"] == 0
    assert s["min_patch_positions_written"] == 24
    assert s["min_donor_delta_norm"] == pytest.approx(0.31)
    # The artifact must say which forward the knockout counters describe. Without this the run's
    # `knockout_liveness` block reads as a claim about the readout, which on this arm is false.
    assert s["knockout_live_on"] == "donor_capture_forward"
    assert s["rescue_layer"] == 20 and s["rescue_basis_key"] == "cand_rank1"


def test_the_run_level_gate_refuses_zero_rows_an_empty_block_and_a_single_bad_row(sb):
    """A gate that never ran is not a pass -- the three ways this repo has shipped a vacuous one."""
    with pytest.raises(SystemExit) as e:
        sb.assert_necessity_live({})
    assert "no necessity block" in str(e.value)

    empty = sb.necessity_summary(sb.new_necessity_live(), SCOPE, "ko")
    with pytest.raises(SystemExit) as e:
        sb.assert_necessity_live(empty)
    assert "ZERO rows" in str(e.value)

    with pytest.raises(SystemExit) as e:
        sb.assert_necessity_live(dict(empty, n_rows=4, frac_rows_ok=None))
    assert "never computed" in str(e.value)

    _, mixed = _run_summary(sb, n_ok=9, n_bad=1)
    assert mixed["frac_rows_ok"] < 1.0
    with pytest.raises(SystemExit) as e:
        sb.assert_necessity_live(mixed)
    assert "not reportable" in str(e.value)


def test_the_run_level_gate_re_asserts_each_leg_from_a_different_statistic(sb):
    """A bug that loses the per-row verdict must not also silence the run-level one.

    So the summary is hand-forged with frac_rows_ok == 1.0 (i.e. the per-row verdict claims every
    row was clean) and one leg broken in the aggregates. Each must still be refused.
    """
    _, good = _run_summary(sb, n_ok=3)
    for field, value, needle in (("max_readout_knockout_edits", 5, "READOUT forward"),
                                 ("min_patch_positions_written", 0, "0 patch positions"),
                                 ("min_donor_prefill_edits", 0, "ZERO knockout prefill edits"),
                                 ("min_donor_delta_norm", 0.0, "coincide"),
                                 ("min_donor_delta_norm", None, "coincide")):
        with pytest.raises(SystemExit) as e:
            sb.assert_necessity_live(dict(good, **{field: value}))
        assert needle in str(e.value), (field, str(e.value))
    with pytest.raises(SystemExit) as e:
        sb.assert_necessity_live(dict(good, schema="SOMETHING/9"))
    assert "does not know what it is reading" in str(e.value)


def test_the_accumulator_the_gate_reads_is_the_one_the_run_fills(sb):
    """`record_necessity_row` must both return the verdict and count it -- not one or the other."""
    live = sb.new_necessity_live()
    donor, delta, patch, dn = _ok_inputs(sb)
    assert sb.record_necessity_row(live, SCOPE, donor, delta, patch, donor_delta_norm=dn) == []
    bad = sb.record_necessity_row(live, SCOPE, donor, delta,
                                  {"n_positions_written": 0}, donor_delta_norm=dn)
    assert bad and live["n_rows"] == 2 and live["n_rows_ok"] == 1
    assert sum(live["violations"].values()) == len(bad)


# ============================================ 7. THE CROSS-LAYER BASIS GUARD STILL BITES (R2-M3)
def _axis_file(tmp_path, selected_layer):
    p = tmp_path / "axis.pt"
    torch.save({"bases": {"cand_rank1": torch.randn(1, H),
                          "ctrl_orth": torch.randn(1, H)},
                "meta": {"selected_layer": selected_layer, "codeword": "button",
                         "fit_prompt": "cw_query", "site": "resid_post",
                         "fit_population": {"split": "train", "n_domains": 67},
                         "bases": {"cand_rank1": {"sha16": "deadbeefdeadbeef"}}}}, p)
    return str(p)


def _args(**kw):
    base = dict(rescue_basis="", rescue_basis_key="", rescue_norm_match_key="",
                rescue_layer=20, rescue_donor="ko", bank="banks/ts116m_button_bomb.jsonl")
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_a_basis_fit_at_another_layer_is_still_refused_under_the_new_donor_mode(sb, tmp_path):
    """R2-M3 must not have a hole at `--rescue-donor ko`: same loader, same refusal.

    A necessity arm that writes an L18-fit axis at L20 is a different experiment wearing the arm's
    label, exactly as the sufficiency arm would be -- and this is the guard that used to be a
    print-only warning.
    """
    ax = _axis_file(tmp_path, selected_layer=18)
    loader = sb.make_rescue_basis_loader(
        _args(rescue_basis=ax, rescue_basis_key="cand_rank1", rescue_layer=20))
    with pytest.raises(SystemExit) as e:
        loader()
    assert "was fit at layer L18" in str(e.value)

    # ...and the matching layer still LOADS, so the guard is not simply refusing everything.
    ok = sb.make_rescue_basis_loader(
        _args(rescue_basis=ax, rescue_basis_key="cand_rank1", rescue_layer=18))
    B, NB = ok()
    assert tuple(B.shape) == (1, H) and NB is None
    assert ok.meta()["selected_layer"] == 18

    # An unknown key is still a refusal and not a default, under this donor mode too.
    with pytest.raises(SystemExit) as e:
        sb.make_rescue_basis_loader(
            _args(rescue_basis=ax, rescue_basis_key="cand_rank9", rescue_layer=18))()
    assert "not in" in str(e.value)


# ================================================================== 8. main() IS WIRED THIS WAY
def _sb_src():
    return open(SB_PATH).read()


def test_the_donor_capture_enters_the_arms_hooks_for_ko_by_the_same_line_self_uses():
    """`self` and `ko` must share ONE capture line, or the identity control and the necessity arm
    can drift apart in how the donor is obtained -- and then the control stops controlling it."""
    src = _sb_src()
    assert 'if args.rescue_donor in ("self", "ko"):' in src, \
        "the donor capture does not enter the arm's hooks for donor mode 'ko'"
    assert 'if args.rescue_donor == "self":\n                            for _c in ctxs:' not in src


def test_the_readout_drops_the_arms_hooks_by_identity_and_only_for_ko():
    """The one line that makes this the necessity direction, plus the guarantee that no other arm
    is affected: every other donor mode must still compose the patch ON TOP of `ctxs`."""
    src = _sb_src()
    assert "_arm_ctxs = list(ctxs)" in src, "the arm's own hooks are never identified"
    assert "_arm_ids = {id(_c) for _c in _arm_ctxs}" in src, \
        "the hooks are not dropped by identity (a class-name filter silently keeps a renamed hook)"
    assert "[_c for _c in ctxs if id(_c) not in _arm_ids]" in src
    assert "ctxs = list(ctxs) + [_rescue_ctx]" in src, \
        "the sufficiency composition was removed; every other arm depends on it"


def test_the_three_preconditions_are_refusals_not_warnings():
    """Each precondition turns the arm into something that still produces a number, so each must
    raise. Read off the AST rather than the text, so reformatting cannot silently empty it."""
    tree = ast.parse(_sb_src())
    guards = [n for n in ast.walk(tree)
              if isinstance(n, ast.If) and "rescue_donor" in ast.dump(n.test)
              and "'ko'" in ast.dump(n.test) and isinstance(n.test, ast.Compare)]
    assert guards, "no `if args.rescue_donor == \"ko\"` guard in main()"
    blob = "\n".join(ast.dump(g) for g in guards)
    raisers = [n for g in guards for n in ast.walk(g)
               if isinstance(n, ast.Raise) and "SystemExit" in ast.dump(n)]
    assert len(raisers) >= 3, f"expected 3 refusals, found {len(raisers)}"
    for needle in ("rescue_layer", "_wants_knockout", "_readout_only"):
        assert needle in blob, f"the {needle} precondition is not guarded under donor 'ko'"


def test_the_run_level_necessity_gate_is_actually_called_and_the_summary_is_written():
    """A gate that exists and is never invoked is the defect, not the fix."""
    src = _sb_src()
    assert "assert_necessity_live(nec_summary or {})" in src, "the necessity gate is never called"
    assert '"necessity_arm": nec_summary,' in src, "the necessity block never reaches summary.json"
    assert 'nec_live = new_necessity_live() if args.rescue_donor == "ko" else None' in src
    # On this arm the ordinary block describes a DIFFERENT forward, and the artifact must say so.
    assert '"counters_measured_on": "donor_capture_forward (--rescue-donor ko)"' in src


def test_rescue_donor_ko_is_a_real_choice_and_the_row_records_it():
    src = _sb_src()
    assert 'choices=("clean", "self", "ko")' in src
    # `rescue_donor` already travels on every rescue row through the one builder, so "ko" is
    # persisted by construction -- asserted so a future refactor cannot quietly drop it.
    assert '"rescue_donor": args.rescue_donor,' in src
    assert '"necessity_violations": _bad,' in src


def test_the_row_builder_raises_rather_than_defaulting_a_missing_donor_record():
    """plan §14: a load-bearing field that is missing RAISES; it never becomes null."""
    src = _sb_src()
    i = src.index("def _necessity_row_fields(")
    body = src[i:i + 3000]
    assert 'if not nec or nec.get("donor_ks") is None' in body
    assert "raise SystemExit(" in body.split('if not nec or nec.get("donor_ks") is None')[1][:400]
