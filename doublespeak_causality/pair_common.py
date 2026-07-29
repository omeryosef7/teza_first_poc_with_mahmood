"""
pair_common.py — shared primitives for the fixed-pair causal core (CAUSAL_CORE_PLAN
Phases B–D). Thin layer over ds_common; holds NO experiment logic.

Adds the three things the plan needs that ds_common does not already provide:

  1. COMPONENT capture (§4): besides the post-block residual that ds_common exposes via
     output_hidden_states, we need the pre-attention residual (block input), the attention
     output, and the MLP output. Implemented with forward / forward-pre hooks on
     `layer`, `layer.self_attn`, `layer.mlp`.

  2. POSITION resolution (§4): {codeword, following, final_prompt, first_generated,
     answer}. Resolved on the ALREADY-TEMPLATED string with add_special_tokens=False so
     indices line up with generation (ds_common.capture_target_reps uses
     add_special_tokens=True and would double the BOS — see PAPER_REPRODUCTION_NOTES).

  3. A forward-only SEMANTIC SCORE (§3, §7): the next-token probability mass on the
     concept vs the codeword. One forward pass instead of a generation, which is what
     makes the exhaustive layer x alpha x control sweeps affordable.

House conventions preserved:
  * 0-indexed block L <-> hidden_states[L+1]; hidden_states[0] is the embedding.
  * Native list-valued EOS is never overwritten.
  * Nothing harmful is printed; callers persist scalars.
"""
from __future__ import annotations

import re
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Any

import torch

import ds_common as dc

COMPONENTS = ("resid_pre", "attn_out", "mlp_out", "resid_post")
POSITIONS = ("codeword_last", "following", "final_prompt", "first_generated")


# --------------------------------------------------------------------------- #
# Positions
# --------------------------------------------------------------------------- #
@dataclass
class PairPositions:
    codeword_all: List[int]
    codeword_last: int
    following: Optional[int]
    final_prompt: int
    seq_len: int

    def get(self, name: str) -> Optional[int]:
        if name == "first_generated":
            # the token generated right after the prompt is produced FROM final_prompt
            return self.final_prompt
        return getattr(self, name, None)

    def as_dict(self) -> Dict[str, Any]:
        return {"codeword_all": self.codeword_all, "codeword_last": self.codeword_last,
                "following": self.following, "final_prompt": self.final_prompt,
                "seq_len": self.seq_len}


def resolve_positions(lm, templated_text: str, probe_word: str) -> PairPositions:
    """Locate probe-word / following / final-prompt positions in a TEMPLATED string.

    Tokenizes with add_special_tokens=False because apply_template already emitted BOS.
    """
    ids = lm.tokenizer(templated_text, add_special_tokens=False)["input_ids"]
    hit = dc.find_word_occurrences(lm.tokenizer, ids, probe_word)
    last = hit.last_idx[-1]
    n = len(ids)
    return PairPositions(
        codeword_all=list(hit.last_idx), codeword_last=last,
        following=(last + 1 if last + 1 < n else None),
        final_prompt=n - 1, seq_len=n,
    )


# --------------------------------------------------------------------------- #
# Component capture
# --------------------------------------------------------------------------- #
class ComponentCapture:
    """Capture per-layer {resid_pre, attn_out, mlp_out, resid_post} at given positions.

    Usage:
        with ComponentCapture(lm, components, positions) as cap:
            lm.model(**tok)
        cap.stacked()  -> {component: Tensor[n_layers, n_positions, hidden] (float32 CPU)}

    resid_post is taken from the block's own output rather than output_hidden_states so
    that all four components come from one uniform hook path.
    """

    def __init__(self, lm, components: Sequence[str] = COMPONENTS,
                 positions: Sequence[int] = ()):
        bad = set(components) - set(COMPONENTS)
        if bad:
            raise ValueError(f"unknown components {sorted(bad)}")
        self.lm = lm
        self.components = list(components)
        self.positions = list(positions)
        self.layers = dc._get_layers(lm.model)
        self.n_layers = len(self.layers)
        self._buf: Dict[str, Dict[int, torch.Tensor]] = {c: {} for c in self.components}
        self._handles: List[Any] = []

    def _grab(self, comp, li, hidden):
        if hidden.dim() == 3:
            hidden = hidden[0]
        idx = torch.tensor([p for p in self.positions if 0 <= p < hidden.shape[0]],
                           device=hidden.device)
        if idx.numel() != len(self.positions):
            raise IndexError(f"position out of range for seq_len={hidden.shape[0]}")
        self._buf[comp][li] = hidden.index_select(0, idx).float().cpu()

    def __enter__(self):
        def out_hook(comp, li):
            def f(mod, inp, out):
                h = out[0] if isinstance(out, tuple) else out
                self._grab(comp, li, h)
            return f

        def pre_hook(li):
            def f(mod, args, kwargs=None):
                h = args[0] if args else kwargs.get("hidden_states")
                self._grab("resid_pre", li, h)
            return f

        for li, layer in enumerate(self.layers):
            if "resid_pre" in self.components:
                self._handles.append(
                    layer.register_forward_pre_hook(pre_hook(li), with_kwargs=True))
            if "resid_post" in self.components:
                self._handles.append(
                    layer.register_forward_hook(out_hook("resid_post", li)))
            if "attn_out" in self.components:
                self._handles.append(
                    layer.self_attn.register_forward_hook(out_hook("attn_out", li)))
            if "mlp_out" in self.components:
                self._handles.append(
                    layer.mlp.register_forward_hook(out_hook("mlp_out", li)))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False

    def stacked(self) -> Dict[str, torch.Tensor]:
        out = {}
        for c in self.components:
            got = self._buf[c]
            missing = [l for l in range(self.n_layers) if l not in got]
            if missing:
                raise RuntimeError(f"component {c}: no capture for layers {missing[:5]}")
            out[c] = torch.stack([got[l] for l in range(self.n_layers)], dim=0)
        return out


@torch.no_grad()
def capture_components(lm, templated_text: str, probe_word: str,
                       components: Sequence[str] = COMPONENTS,
                       position_names: Sequence[str] = POSITIONS):
    """One forward pass -> {component: Tensor[n_layers, n_positions, hidden]} + positions.

    Positions that do not exist for this prompt (e.g. `following` when the probe word is
    the last token) are dropped, and the surviving names are returned alongside.
    """
    pos = resolve_positions(lm, templated_text, probe_word)
    names, idxs = [], []
    for n in position_names:
        p = pos.get(n)
        if p is not None:
            names.append(n)
            idxs.append(p)
    tok = lm.tokenizer(templated_text, return_tensors="pt",
                       add_special_tokens=False).to(lm.model.device)
    with ComponentCapture(lm, components, idxs) as cap:
        out = lm.model(**tok, return_dict=True)
    return {"reps": cap.stacked(), "position_names": names,
            "positions": pos.as_dict(), "logits_last": out.logits[0, -1, :].float().cpu()}


# --------------------------------------------------------------------------- #
# Forward-only semantic score (the cheap outcome used by the big sweeps)
# --------------------------------------------------------------------------- #
def word_first_ids(tokenizer, word: str) -> List[int]:
    """First-token ids of every surface form the model might emit for `word`."""
    ids = set()
    for surface in (f" {word}", word, f" {word.capitalize()}", word.capitalize()):
        enc = tokenizer.encode(surface, add_special_tokens=False)
        if enc:
            ids.add(int(enc[0]))
    return sorted(ids)


@torch.no_grad()
def semantic_score(lm, templated_text: str, id_groups: Dict[str, List[int]],
                   patches: Sequence = ()) -> Dict[str, float]:
    """Next-token probability mass per id group, optionally under LayerPatch hooks.

    `patches` is a list of (layer_idx, positions, vector, mode, alpha) tuples applied
    SIMULTANEOUSLY (multi-layer windows), matching 18_run_behavioral_necessity's
    patched_generate contract but with an explicit alpha.
    """
    tok = lm.tokenizer(templated_text, return_tensors="pt",
                       add_special_tokens=False).to(lm.model.device)
    with ExitStack() as stack:
        for (li, positions, vec, mode, alpha) in patches:
            stack.enter_context(dc.LayerPatch(lm.model, li, positions, vec, mode, alpha))
        out = lm.model(**tok, return_dict=True)
    probs = torch.softmax(out.logits[0, -1, :].float(), dim=-1)
    return {name: float(probs[ids].sum()) for name, ids in id_groups.items()}


@torch.no_grad()
def patched_generate(lm, templated_text: str, patches: Sequence = (),
                     max_new_tokens: int = 8) -> str:
    """Greedy generation under the same patch contract (used for label readouts)."""
    tok = lm.tokenizer(templated_text, return_tensors="pt",
                       add_special_tokens=False).to(lm.model.device)
    in_len = tok["input_ids"].shape[1]
    with ExitStack() as stack:
        for (li, positions, vec, mode, alpha) in patches:
            stack.enter_context(dc.LayerPatch(lm.model, li, positions, vec, mode, alpha))
        out = lm.model.generate(**tok, max_new_tokens=max_new_tokens, do_sample=False,
                                eos_token_id=lm.eos_token_ids,
                                pad_token_id=lm.tokenizer.pad_token_id)
    return lm.tokenizer.decode(out[0][in_len:], skip_special_tokens=True)


# --------------------------------------------------------------------------- #
# Control vectors (plan §5) — the matched-perturbation distribution
# --------------------------------------------------------------------------- #
def norm_matched_random(direction: torch.Tensor, n: int, seed: int = 0) -> torch.Tensor:
    """n random vectors with the SAME norm as `direction`. Returns [n, hidden]."""
    g = torch.Generator().manual_seed(seed)
    v = torch.randn(n, direction.numel(), generator=g, dtype=torch.float32)
    v = v / v.norm(dim=1, keepdim=True) * direction.float().norm()
    return v


def orthogonal_random(direction: torch.Tensor, n: int, seed: int = 0) -> torch.Tensor:
    """Norm-matched random vectors ORTHOGONAL to `direction`. Returns [n, hidden]."""
    d = direction.float().flatten()
    d = d / (d.norm() + 1e-8)
    v = norm_matched_random(direction, n, seed)
    v = v - (v @ d).unsqueeze(1) * d.unsqueeze(0)
    return v / v.norm(dim=1, keepdim=True) * direction.float().norm()


def in_subspace_random(basis: torch.Tensor, direction: torch.Tensor, n: int,
                       seed: int = 0) -> torch.Tensor:
    """Norm-matched random vectors inside the span of `basis` [k, hidden]."""
    g = torch.Generator().manual_seed(seed)
    k = basis.shape[0]
    c = torch.randn(n, k, generator=g, dtype=torch.float32)
    v = c @ basis.float()
    return v / (v.norm(dim=1, keepdim=True) + 1e-8) * direction.float().norm()
