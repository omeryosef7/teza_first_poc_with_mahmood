#!/usr/bin/env python3
"""Unit tests for SubspaceDonorPatch (Phase 1 primitive) and the refactor it forced.

Run: python tests/test_subspace_donor_patch.py

The point of these tests is not coverage, it is the specific ways this intervention can be wrong
while still producing a plausible number:
  * a projection with a non-orthonormal basis is not a projection;
  * a full-rank subspace must reproduce the existing whole-state rescue EXACTLY -- if it does not,
    the subspace arm and its own positive control are not on the same scale and no recovery
    fraction between them means anything;
  * a subspace orthogonal to the difference must write nothing -- that is the null the controls
    are supposed to sit at;
  * add-then-remove must return to the starting state, because Phase 2's necessity arm is the
    same primitive with the donor swapped;
  * a norm-matched control must actually be norm-matched, per position, not on average;
  * the token-identity guard must still refuse, for BOTH patchers, after being factored out.
"""
import os
import sys

import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
from donor_patch import (ActivationCapture, DonorBlock, DonorPatch,  # noqa: E402
                         SubspaceDonorPatch, assert_token_identity, orthonormalise)

H = 16          # hidden size
L = 3           # layers
T = 7           # sequence length
torch.manual_seed(20260915)


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


def _run(model, ids):
    with torch.no_grad():
        return model(input_ids=torch.tensor([ids]))


def _capture(model, layer, positions, ids, ctxs=()):
    import contextlib
    cap = ActivationCapture(model, layer, positions)
    with contextlib.ExitStack() as st:
        for c in ctxs:
            st.enter_context(c)
        st.enter_context(cap)
        _run(model, ids)
    return cap.acts


def _rerun(model, donor, ids, basis, norm_basis):
    with SubspaceDonorPatch(model, donor, ids, basis=basis, norm_match_basis=norm_basis):
        return _run(model, ids)


FAILS = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (("   " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)


def main():
    model = _Model().eval()
    ids = [5, 9, 3, 11, 2, 8, 4]
    ids_other = [5, 9, 3, 42, 2, 8, 4]         # differs at position 3, INSIDE the patched span
    ids_outside = [5, 9, 3, 11, 2, 8, 42]      # differs at position 6, OUTSIDE the span
    pos = [2, 3, 4]
    layer = 1

    # A "donor" forward that genuinely differs from the recipient: perturb the embedding table.
    donor_model = _Model().eval()
    donor_model.load_state_dict(model.state_dict())
    with torch.no_grad():
        donor_model.emb.weight.add_(torch.randn_like(donor_model.emb.weight) * 0.5)

    donor_acts = _capture(donor_model, layer, pos, ids)
    donor = DonorBlock(layer_idx=layer, positions=list(pos), acts=donor_acts, input_ids=list(ids))
    base_out = _run(model, ids)
    recipient_acts = _capture(model, layer, pos, ids)
    delta = (donor_acts - recipient_acts).to(torch.float64)
    check("donor and recipient genuinely differ", float(delta.norm()) > 1e-3,
          "||delta||=%.4f" % float(delta.norm()))

    print("\n[orthonormalise]")
    v = torch.randn(H)
    Q = orthonormalise(v)
    check("1-D vector -> [1, hidden] unit row", Q.shape == (1, H) and abs(float(Q.norm()) - 1) < 1e-9)
    M = torch.randn(3, H)
    Q3 = orthonormalise(M)
    check("rank-3 -> orthonormal 3xH",
          Q3.shape == (3, H) and torch.allclose(Q3 @ Q3.T, torch.eye(3, dtype=Q3.dtype), atol=1e-9))
    check("row space preserved",
          torch.linalg.matrix_rank(torch.cat([M.to(torch.float64), Q3], 0)) == 3)
    dep = torch.cat([M[:1], M[:1] * 2.0], 0)
    try:
        orthonormalise(dep); ok = False
    except ValueError:
        ok = True
    check("linearly dependent rows REFUSED", ok)

    print("\n[full-rank subspace == whole-state DonorPatch]")
    full_basis = torch.eye(H)
    with DonorPatch(model, donor, ids) as _:
        out_full = _run(model, ids)
    with SubspaceDonorPatch(model, donor, ids, basis=full_basis) as _:
        out_sub = _run(model, ids)
    check("full-rank subspace reproduces DonorPatch",
          torch.allclose(out_full, out_sub, atol=1e-5),
          "max|diff|=%.2e" % float((out_full - out_sub).abs().max()))
    check("both differ from the unpatched forward",
          not torch.allclose(out_full, base_out, atol=1e-6))

    print("\n[orthogonal subspace writes nothing]")
    # Build a basis orthogonal to every row of delta.
    U, S, Vh = torch.linalg.svd(delta, full_matrices=True)
    orth_basis = Vh[len(pos):len(pos) + 2]                 # rows orthogonal to delta's row space
    sp = SubspaceDonorPatch(model, donor, ids, basis=orth_basis)
    with sp:
        out_orth = _run(model, ids)
    lv = sp.liveness()
    check("orthogonal subspace: forward unchanged",
          torch.allclose(out_orth, base_out, atol=1e-6),
          "max|diff|=%.2e" % float((out_orth - base_out).abs().max()))
    check("orthogonal subspace: fired but wrote ~0 norm",
          lv["fired"] and lv["written_norm_mean"] < 1e-8,
          "written_norm_mean=%.2e" % lv["written_norm_mean"])

    print("\n[rank-1 subspace: partial, bounded by full]")
    w = delta[0] / delta[0].norm()
    sp1 = SubspaceDonorPatch(model, donor, ids, basis=w.to(torch.float32))
    with sp1:
        out_r1 = _run(model, ids)
    d1 = sp1.liveness()
    check("rank-1 writes a nonzero but sub-total delta",
          0 < d1["written_norm_mean"] < d1["delta_norm_mean"],
          "written=%.4f  available=%.4f  frac=%.3f"
          % (d1["written_norm_mean"], d1["delta_norm_mean"], d1["captured_energy_frac_mean"]))
    check("rank-1 output differs from both unpatched and full",
          (not torch.allclose(out_r1, base_out, atol=1e-6))
          and (not torch.allclose(out_r1, out_full, atol=1e-6)))
    check("captured energy fraction in (0,1]", 0 < d1["captured_energy_frac_mean"] <= 1.0 + 1e-9)

    print("\n[add then remove returns to start  (Phase 2 necessity uses the same primitive)]")
    # *** THIS TEST WAS VACUOUS AND AN ADVERSARIAL REVIEW PROVED IT. ***
    # The first version ran the two patches in SEPARATE forward passes. In the second pass the
    # live forward is clean, so the "remove" patch's donor (the clean recipient activations) EQUALS
    # the live state, delta is identically zero, and nothing is written. The assertion passed
    # because the forward was never modified -- it still passed with the write path disabled
    # (scale=0.0), which is the definition of a test that cannot fail.
    #
    # The real test composes both patches in ONE forward, which is also what an add-then-remove
    # intervention actually is. Hooks on the same layer fire in registration order on the same
    # tensor, so with P idempotent:
    #     h'  = h + P(d - h)
    #     h'' = h' + P(h - h') = h + P(d-h) - P(P(d-h)) = h
    # and this holds at ANY rank, not just full rank -- which is the property Phase 2's necessity
    # arm depends on.
    back = DonorBlock(layer_idx=layer, positions=list(pos), acts=recipient_acts, input_ids=list(ids))
    for rank_name, B in (("full-rank", full_basis), ("rank-1", w.to(torch.float32))):
        sp_fwd = SubspaceDonorPatch(model, donor, ids, basis=B)
        sp_bwd = SubspaceDonorPatch(model, back, ids, basis=B)
        with sp_fwd, sp_bwd:                       # BOTH hooks live in ONE forward
            out_back = _run(model, ids)
        check("add-then-remove in one forward is identity (%s)" % rank_name,
              torch.allclose(out_back, base_out, atol=1e-5),
              "max|diff|=%.2e  fwd_wrote=%d bwd_wrote=%d"
              % (float((out_back - base_out).abs().max()),
                 sp_fwd.liveness()["n_positions_written"],
                 sp_bwd.liveness()["n_positions_written"]))
        check("  ...and both patches actually fired (%s)" % rank_name,
              sp_fwd.liveness()["fired"] and sp_bwd.liveness()["fired"])
    # THE ANTI-VACUITY CHECK the first version lacked: with the write path disabled the identity
    # must still hold trivially, but the FORWARD patch must be shown to change the output when it
    # is the only hook -- otherwise "returns to start" proves nothing.
    sp_only = SubspaceDonorPatch(model, donor, ids, basis=full_basis)
    with sp_only:
        out_fwd_only = _run(model, ids)
    check("the forward patch alone DOES change the output (anti-vacuity)",
          not torch.allclose(out_fwd_only, base_out, atol=1e-6),
          "max|diff|=%.2e" % float((out_fwd_only - base_out).abs().max()))

    print("\n[norm matching]")
    # The candidate here must look like a LEARNED axis, i.e. a generic direction that is not
    # parallel to any single row of delta. Using delta[0] (as a first draft did) makes position 0
    # exactly parallel to the candidate, so a control orthogonal to the candidate is exactly
    # orthogonal to that row's delta and is CORRECTLY flagged degenerate -- the flag fired and the
    # test, not the code, was wrong. A learned installation axis is never one row's delta.
    g0 = torch.Generator().manual_seed(11)
    cand = orthonormalise(torch.randn(H, generator=g0))
    cand_p = SubspaceDonorPatch(model, donor, ids, basis=cand)
    with cand_p:
        _run(model, ids)
    c = cand_p.liveness()

    # (a) the REALISTIC control: a random direction orthogonal to the CANDIDATE (not to delta).
    g = torch.Generator().manual_seed(7)
    r = torch.randn(H, generator=g).to(torch.float64)
    r = r - (r @ cand[0]) * cand[0]
    ctrl_dir = orthonormalise(r)
    check("realistic control is orthogonal to the candidate",
          abs(float(ctrl_dir[0] @ cand[0])) < 1e-9)
    ctrl_raw = SubspaceDonorPatch(model, donor, ids, basis=ctrl_dir)
    with ctrl_raw:
        _run(model, ids)
    ctrl_matched = SubspaceDonorPatch(model, donor, ids, basis=ctrl_dir, norm_match_basis=cand)
    with ctrl_matched:
        _run(model, ids)
    a, b = ctrl_raw.liveness(), ctrl_matched.liveness()
    check("unmatched control writes a different norm than the candidate",
          abs(a["written_norm_mean"] - c["written_norm_mean"]) > 1e-4,
          "ctrl=%.4f candidate=%.4f" % (a["written_norm_mean"], c["written_norm_mean"]))
    check("norm-matched control writes the candidate's norm exactly",
          abs(b["written_norm_mean"] - c["written_norm_mean"]) < 1e-9,
          "matched=%.6f candidate=%.6f" % (b["written_norm_mean"], c["written_norm_mean"]))
    check("realistic control is NOT flagged degenerate",
          b["n_positions_norm_match_degenerate"] == 0)
    check("norm-matched control still moves the forward",
          not torch.allclose(_rerun(model, donor, ids, ctrl_dir, cand), base_out, atol=1e-6))

    # (b) the DEGENERATE case: a subspace orthogonal to DELTA itself. Rescaling its projection
    # would amplify float noise; the implementation must inject a deterministic unit vector
    # instead AND say so.
    # The degenerate branch now REFUSES by default (review M5). Confirm the refusal fires...
    try:
        with SubspaceDonorPatch(model, donor, ids, basis=orth_basis[:1], norm_match_basis=cand):
            _run(model, ids)
        ok = False
    except ValueError as e:
        ok = "DEGENERATE" in str(e)
    check("degenerate norm-match REFUSES by default", ok)
    # ...then opt in, to check the fallback still writes the matched norm and flags every position.
    deg = SubspaceDonorPatch(model, donor, ids, basis=orth_basis[:1], norm_match_basis=cand,
                             refuse_degenerate=False)
    with deg:
        _run(model, ids)
    d = deg.liveness()
    check("degenerate control still writes the candidate's norm",
          abs(d["written_norm_mean"] - c["written_norm_mean"]) < 1e-9,
          "degenerate=%.6f candidate=%.6f" % (d["written_norm_mean"], c["written_norm_mean"]))
    check("degenerate control is FLAGGED on every position",
          d["n_positions_norm_match_degenerate"] == len(pos),
          "flagged=%d of %d" % (d["n_positions_norm_match_degenerate"], len(pos)))

    print("\n[token identity guard, both patchers]")
    for cls, kw in ((DonorPatch, {}), (SubspaceDonorPatch, {"basis": full_basis})):
        try:
            cls(model, donor, ids_other, **kw); ok = False
        except ValueError as e:
            ok = "REFUSING to patch" in str(e)
        check("%s refuses a token-mismatched recipient" % cls.__name__, ok)
    try:
        assert_token_identity(DonorBlock(layer_idx=layer, positions=list(pos), acts=donor_acts,
                                         input_ids=[]), ids, True)
        ok = False
    except ValueError:
        ok = True
    check("empty donor input_ids refused under strict_ids", ok)
    # The guard is POSITION-SCOPED on purpose: a token that differs OUTSIDE the patched span
    # cannot misplace the written activations, so it must NOT refuse. (The first version of this
    # test asserted the opposite and "failed" against correct behaviour.)
    try:
        DonorPatch(model, donor, ids_outside); ok = True
    except ValueError:
        ok = False
    check("mismatch OUTSIDE the patched span is allowed", ok)

    print("\n[decode-step guard]")
    sp_dec = SubspaceDonorPatch(model, donor, ids, basis=full_basis)
    with sp_dec:
        with torch.no_grad():
            model(input_ids=torch.tensor([[ids[0]]]))     # seq_len 1: nothing to patch
    check("single-token forward writes nothing",
          sp_dec.liveness()["n_positions_written"] == 0 and sp_dec.liveness()["n_forward_calls"] == 1)

    print("\n[decode guard when the only patched position is 0  (review m2)]")
    d0 = DonorBlock(layer_idx=layer, positions=[0], acts=donor_acts[:1], input_ids=list(ids))
    for cls, kw in ((DonorPatch, {}), (SubspaceDonorPatch, {"basis": full_basis})):
        pc = cls(model, d0, ids, **kw)
        with pc:
            with torch.no_grad():
                model(input_ids=torch.tensor([[ids[0]]]))     # a length-1 decode step
        check("%s does not write on a length-1 decode step at position 0" % cls.__name__,
              pc.liveness()["n_positions_written"] == 0,
              "wrote=%d" % pc.liveness()["n_positions_written"])

    print("\n[basis shape validation]")
    try:
        SubspaceDonorPatch(model, donor, ids, basis=torch.randn(2, H + 1)); ok = False
    except ValueError:
        ok = True
    check("hidden-dim mismatch refused", ok)

    print("\n%s  (%d failure(s))" % ("ALL TESTS PASSED" if not FAILS else "FAILURES: " + ", ".join(FAILS),
                                     len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
