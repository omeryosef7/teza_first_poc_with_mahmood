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
        rid = list(recipient_input_ids)
        if strict_ids:
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

    def _hook(self, module, inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        self.n_forward += 1
        if hidden.shape[1] <= max(self.donor.positions, default=-1):
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
