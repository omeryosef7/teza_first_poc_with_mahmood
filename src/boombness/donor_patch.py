"""§20 Q3: the primitive for a RESCUE experiment — per-position activation donation.

WHY A NEW CLASS. `ds_common.LayerPatch` writes ONE vector, shaped `[hidden]`, to every requested
position. A rescue asks a different question: *if we give the knocked-out run back exactly the
activations the clean run had at the demonstration positions, does the attack come back?* That needs
a **different vector per position** — a `[n_positions, hidden]` donor block — which `LayerPatch`
cannot express. Nothing here replaces or edits `LayerPatch`; it is a sibling.

*** THE BUG CLASS THIS FILE IS WRITTEN AGAINST ***
This repo has twice shipped a defect where a position computed on one example is reused as an
ABSOLUTE index on another. A donor patch is the ideal host for it: donor and recipient are two
different forward passes, and if their tokenisations differ by even one token the patch writes the
right activations to the wrong places and still produces a plausible number. So:

  * the donor carries the `input_ids` it was captured under, and `DonorPatch` REFUSES to apply
    unless the recipient's ids match **exactly** over the patched span (`strict_ids=True`);
  * position lists are stored per-donor, never recomputed at apply time;
  * the hook asserts the donor block's row count equals the position count, and that every position
    is inside the recipient's sequence.

A rescue that silently misaligns is worse than no rescue, because it produces a null that looks like
evidence the information was not there.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "doublespeak_causality"))
import ds_common as dc  # noqa: E402


@dataclass
class DonorBlock:
    """Activations captured from ONE forward pass at ONE layer, plus their identity."""
    layer_idx: int
    positions: List[int]
    acts: torch.Tensor                    # [n_positions, hidden]
    input_ids: List[int] = field(default_factory=list)

    def __post_init__(self):
        if self.acts.ndim != 2:
            raise ValueError(f"donor acts must be [n_positions, hidden], got {tuple(self.acts.shape)}")
        if self.acts.shape[0] != len(self.positions):
            raise ValueError(f"donor has {self.acts.shape[0]} rows for {len(self.positions)} positions")
        if len(set(self.positions)) != len(self.positions):
            raise ValueError("donor positions contain duplicates; the write order would be ambiguous")


class ActivationCapture:
    """Context manager: record `resid_post` at `layer_idx` for the positions requested."""

    def __init__(self, model, layer_idx: int, positions: Sequence[int]):
        self.layer = dc._get_layers(model)[layer_idx]
        self.layer_idx = layer_idx
        self.positions = list(positions)
        self.acts: Optional[torch.Tensor] = None
        self._h = None

    def _hook(self, module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        if hidden.shape[1] <= max(self.positions, default=-1):
            return output                      # decode step: nothing to capture
        idx = torch.tensor(self.positions, device=hidden.device)
        self.acts = hidden[0].index_select(0, idx).detach().clone()
        return output

    def __enter__(self):
        self._h = self.layer.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._h is not None:
            self._h.remove()
        return False


def assert_token_identity(donor: "DonorBlock", recipient_input_ids: Sequence[int],
                          strict_ids: bool = True) -> None:
    """The module docstring's guard, factored out so every patcher enforces the SAME check.

    Extracted verbatim from `DonorPatch.__init__` when `SubspaceDonorPatch` was added: two
    patchers with two hand-copied versions of a safety check is how one of them quietly loses it.
    """
    rid = list(recipient_input_ids)
    if not strict_ids:
        return
    if not donor.input_ids:
        raise ValueError("strict_ids=True but the donor carries no input_ids to check against")
    bad = [p for p in donor.positions
           if p >= len(rid) or p >= len(donor.input_ids) or rid[p] != donor.input_ids[p]]
    if bad:
        raise ValueError(
            f"REFUSING to patch: {len(bad)} of {len(donor.positions)} donor positions do not "
            f"carry the same token in the recipient (first offenders {bad[:5]}). Donor and "
            f"recipient must be token-identical over the patched span, or the rescue writes "
            f"the right activations to the wrong places.")


class DonorPatch:
    """Write a donor's per-position activations into the recipient's `resid_post` at one layer.

    `strict_ids` is ON by default and is the whole point: see the module docstring.
    """

    def __init__(self, model, donor: DonorBlock, recipient_input_ids: Sequence[int],
                 strict_ids: bool = True):
        self.layer = dc._get_layers(model)[donor.layer_idx]
        self.donor = donor
        self.n_applied = 0
        self.n_forward = 0
        self._h = None
        assert_token_identity(donor, recipient_input_ids, strict_ids)

    def _hook(self, module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        self.n_forward += 1
        # REVIEW m2: see SubspaceDonorPatch._hook -- `<=` alone lets a length-1 decode step through
        # when the only patched position is 0.
        if hidden.shape[1] <= max(self.donor.positions, default=-1) or hidden.shape[1] == 1:
            return output                      # decode step: positions already past
        idx = torch.tensor(self.donor.positions, device=hidden.device)
        src = self.donor.acts.to(hidden.dtype).to(hidden.device)
        hidden[0].index_copy_(0, idx, src)
        self.n_applied += len(self.donor.positions)
        return (hidden,) + tuple(output[1:]) if isinstance(output, tuple) else hidden

    def liveness(self):
        """A rescue that never fired is not a rescue. Report it, never infer it."""
        return {"n_positions_written": self.n_applied, "n_forward_calls": self.n_forward,
                "fired": self.n_applied > 0}

    def __enter__(self):
        self._h = self.layer.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._h is not None:
            self._h.remove()
        return False


def orthonormalise(basis: torch.Tensor, *, atol: float = 1e-4) -> torch.Tensor:
    """Return an orthonormal [r, hidden] basis for the row space of `basis`, in float64.

    A candidate exported from a ridge fit is a raw weight vector, not a unit vector, and a
    low-rank candidate's components are not orthogonal. Projecting with a non-orthonormal basis
    silently computes something that is not a projection, so the basis is normalised HERE, once,
    rather than trusted from whatever produced it.
    """
    B = basis.detach().to(torch.float64)
    if B.ndim == 1:
        B = B.unsqueeze(0)
    if B.ndim != 2:
        raise ValueError(f"basis must be [r, hidden] (or [hidden]), got {tuple(basis.shape)}")
    if torch.linalg.matrix_rank(B) < B.shape[0]:
        raise ValueError(f"basis rows are linearly dependent (rank {int(torch.linalg.matrix_rank(B))} "
                         f"< {B.shape[0]} rows); the projector would be ill-defined")
    Q, _ = torch.linalg.qr(B.T)                 # [hidden, r]
    Q = Q.T.contiguous()                        # [r, hidden]
    gram = Q @ Q.T
    if not torch.allclose(gram, torch.eye(Q.shape[0], dtype=Q.dtype), atol=atol):
        raise ValueError("orthonormalisation failed its own check")
    return Q


class SubspaceDonorPatch:
    """Restore (or remove) ONLY the component of the donor-minus-recipient difference that lies
    in a given subspace:

        h' = h + P_W (h_donor - h),        P_W = W^T W,  W orthonormal [r, hidden]

    WHY THIS IS THE EXPERIMENT. `DonorPatch` overwrites the whole residual state, which shows that
    the SITE matters but says nothing about WHICH variable at that site is doing the work. Setting
    W to a TRAIN-learned installation-predictive axis asks the sharper question: is the
    installation component itself the causal variable? Setting W to a random / shuffled-label /
    orthogonal subspace at matched norm gives the control distribution that question needs.

    BOTH DIRECTIONS FROM ONE PRIMITIVE. The formula is symmetric in which forward is the donor:
      * live = knocked-out, donor = clean  -> ADDS the clean installed component (sufficiency);
      * live = clean,       donor = ko     -> REMOVES it (necessity).
    So the necessity arm needs no new code, only a different donor -- which also guarantees the
    two directions cannot drift apart in implementation.

    NORM MATCHING. A random subspace of rank r captures only ~sqrt(r/hidden) of a delta's norm, so
    an unscaled random control injects a far smaller perturbation than the candidate and would
    "show specificity" for purely geometric reasons. When `norm_match_basis` is given, the written
    delta is rescaled per position to the norm the CANDIDATE subspace would have written on this
    same row -- the only matching that is honest at the row level.

    Arithmetic is done in float64 and cast once on write; a bf16 projection of a small delta loses
    a visible fraction of it.
    """

    def __init__(self, model, donor: DonorBlock, recipient_input_ids: Sequence[int],
                 basis: torch.Tensor, *, norm_match_basis: Optional[torch.Tensor] = None,
                 scale: float = 1.0, strict_ids: bool = True,
                 refuse_degenerate: bool = True):
        self.layer = dc._get_layers(model)[donor.layer_idx]
        self.donor = donor
        self.basis = orthonormalise(basis)
        self.norm_basis = orthonormalise(norm_match_basis) if norm_match_basis is not None else None
        if self.basis.shape[1] != donor.acts.shape[1]:
            raise ValueError(f"basis hidden dim {self.basis.shape[1]} != donor hidden dim "
                             f"{donor.acts.shape[1]}")
        if self.norm_basis is not None and self.norm_basis.shape[1] != self.basis.shape[1]:
            raise ValueError("norm_match_basis hidden dim differs from basis hidden dim")
        self.scale = float(scale)
        self.refuse_degenerate = bool(refuse_degenerate)
        self.n_applied = 0
        self.n_forward = 0
        self._h = None
        self._dose = None
        assert_token_identity(donor, recipient_input_ids, strict_ids)

    def _hook(self, module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        self.n_forward += 1
        # REVIEW m2. `<=` was wrong: with a single patched position 0, a decode step of length 1
        # satisfies 1 <= 0 == False and the hook would write into the decode step. The correct
        # test is whether the sequence is long enough to CONTAIN every patched position, which is
        # `shape[1] > max(positions)`; and a prefill is additionally the only forward where the
        # positions mean what they meant at capture time.
        if hidden.shape[1] <= max(self.donor.positions, default=-1) or hidden.shape[1] == 1:
            return output                      # decode step: positions already past
        idx = torch.tensor(self.donor.positions, device=hidden.device)
        cur = hidden[0].index_select(0, idx).to(torch.float64)          # [n_pos, hidden]
        don = self.donor.acts.to(hidden.device).to(torch.float64)       # [n_pos, hidden]
        delta = don - cur
        W = self.basis.to(hidden.device)
        proj = (delta @ W.T) @ W                                        # [n_pos, hidden]
        proj_norm = proj.norm(dim=1)
        dn_all = delta.norm(dim=1)
        n_degenerate = 0
        if self.norm_basis is not None:
            # NORM-MATCHED CONTROL. Target = the norm the CANDIDATE subspace would have written on
            # THIS row, so the match is per-position, not on average.
            Wc = self.norm_basis.to(hidden.device)
            target = ((delta @ Wc.T) @ Wc).norm(dim=1)
            # DEGENERACY. If this subspace carries essentially none of the difference, rescaling
            # its projection multiplies float noise by ~1e11 and writes a direction that is pure
            # rounding error. (The first version of this code did exactly that and a unit test
            # caught it writing 4e-6 where it should have written 0.143.) In that case inject
            # along a DETERMINISTIC unit vector of the subspace instead, and RECORD that we did --
            # a silently-degenerate control is a control that cannot fail.
            rel = proj_norm / dn_all.clamp_min(1e-12)
            degen = rel < 1e-6
            n_degenerate = int(degen.sum())
            if n_degenerate and self.refuse_degenerate:
                # REVIEW M5. The fallback direction W.sum(0) is an artifact of whichever QR gauge
                # `orthonormalise` happened to return -- for rank > 1 it is not even reproducible
                # across LAPACK versions -- so a control injecting along it is norm-matched but
                # scientifically meaningless. Counting it and continuing is the repo's own
                # "threshold published but never enforced" bug class; `assert_control_norm_matched`
                # SystemExits on the analogous condition and so does this.
                raise ValueError(
                    "REFUSING to patch: %d of %d positions are norm-match DEGENERATE (this "
                    "subspace carries < 1e-6 of the delta, so rescaling its projection would "
                    "amplify float noise). A control that writes an arbitrary QR-gauge direction "
                    "is not a control. Pass refuse_degenerate=False only for a test that means "
                    "to exercise this branch." % (n_degenerate, proj.shape[0]))
            unit = torch.where(degen.unsqueeze(1),
                               (W.sum(0) / W.sum(0).norm().clamp_min(1e-12)).expand_as(proj),
                               proj / proj_norm.clamp_min(1e-12).unsqueeze(1))
            proj = unit * target.unsqueeze(1)
            written_norm = proj.norm(dim=1)
        else:
            target = proj_norm
            written_norm = proj_norm
        if self.scale != 1.0:
            proj = proj * self.scale
            written_norm = written_norm * abs(self.scale)
        new = (cur + proj).to(hidden.dtype)
        hidden[0].index_copy_(0, idx, new)
        self.n_applied += len(self.donor.positions)
        dn = dn_all
        # DOSE, recorded not inferred: how big was the available difference, how much of it does
        # this subspace span, and how much did we actually write.
        self._dose = {
            "delta_norm_mean": float(dn.mean()),
            "proj_norm_mean": float(proj_norm.mean()),
            "written_norm_mean": float(written_norm.mean()),
            "norm_match_target_mean": float(target.mean()),
            "captured_energy_frac_mean": float((proj_norm / dn.clamp_min(1e-12)).mean()),
            "rank": int(self.basis.shape[0]),
            "n_positions": len(self.donor.positions),
            "norm_matched": self.norm_basis is not None,
            "n_positions_norm_match_degenerate": n_degenerate,
        }
        return (hidden,) + tuple(output[1:]) if isinstance(output, tuple) else hidden

    def liveness(self):
        """A subspace rescue that never fired is not a rescue, and one that wrote a zero-norm
        delta is indistinguishable from one that never fired -- so report the norm too."""
        d = dict(self._dose or {})
        d.update({"n_positions_written": self.n_applied, "n_forward_calls": self.n_forward,
                  "fired": self.n_applied > 0,
                  "wrote_nonzero": bool((self._dose or {}).get("written_norm_mean", 0.0) > 0)})
        return d

    def __enter__(self):
        self._h = self.layer.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._h is not None:
            self._h.remove()
        return False
