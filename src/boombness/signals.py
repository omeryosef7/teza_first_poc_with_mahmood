"""signals.py — the Boombness metrics (plan §6) and the 2x2 direction estimator.

Three metrics, deliberately kept independent so §6.4 can compare them:

  A. LOGIT LENS       — decode a mid-layer residual through the model's own final norm +
                        unembedding and read logit(concept) - logit(codeword).
  B. DIRECTION        — project onto a diff-of-means direction. This module estimates the
                        direction from the 2x2 (see below), not from the plan's naive
                        B - A, which is confounded (progress log F1).
  C. PROBE            — a trained linear probe; lives in probes.py, scored through the
                        same `BoombnessScorer` interface so §6.4 is a fair comparison.

THE 2x2 ESTIMATOR
-----------------
With cells A=benign_literal, B=direct_harmful, C=natural_doublespeak, E=concept_in_benign_ctx
(see prompt_families.py), at a fixed layer and token role:

    d_surface = 1/2[(B - C) + (E - A)]    identified surface-word effect, context matched
    d_context = 1/2[(C - A) + (B - E)]    context/valence effect, surface matched
    d_inter   = (B - C) - (E - A)         interaction: is the surface effect itself
                                          context-dependent? (nonzero => the codeword is
                                          being read differently in doublespeak context)
    d_naive   = B - A                     what the plan §6.2 asks for = d_surface + d_context

`Boombness(h) := <h_unit, d_surface_unit>` unless a caller explicitly asks for another basis.
Every scorer records WHICH direction it used, because reporting a number without that is
how the confound got in last time.

LAYER CONVENTION (repo-wide, do not re-litigate): 0-indexed block L corresponds to
`hidden_states[L+1]`; `hidden_states[0]` is the embedding. Functions here take and return
BLOCK indices and convert internally; every returned record carries `layer_convention`.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ds  # noqa: E402

LAYER_CONVENTION = "block_L == hidden_states[L+1]; hidden_states[0] == embeddings"

CELL_TO_CONDITION = {
    "A": "benign_literal",
    "B": "direct_harmful",
    "C": "natural_doublespeak",
    "E": "concept_in_benign_ctx",
}


# --------------------------------------------------------------------------- #
# A. Logit lens
# --------------------------------------------------------------------------- #
def _final_norm_and_head(model):
    """Locate the model's final norm and unembedding, across the HF layouts we use."""
    base = getattr(model, "model", model)
    norm = getattr(base, "norm", None) or getattr(base, "final_layernorm", None) \
        or getattr(getattr(base, "transformer", base), "ln_f", None)
    head = getattr(model, "lm_head", None)
    if head is None or norm is None:
        raise RuntimeError(
            f"cannot locate final norm / lm_head on {type(model).__name__}; "
            "logit lens needs both — add the layout rather than guessing")
    return norm, head


@torch.no_grad()
def logit_lens(lm, hidden: torch.Tensor, apply_norm: bool = True) -> torch.Tensor:
    """Decode residual-stream vectors to vocabulary logits.

    hidden: [..., H] on any device/dtype. Returns [..., V] float32 on CPU.
    apply_norm=True runs the model's own final norm first, which is what makes this the
    *logit lens* rather than a raw unembedding dot product; the flag exists so §6.4 can
    report both, since the choice measurably changes early-layer scores.
    """
    norm, head = _final_norm_and_head(lm.model)
    p = next(head.parameters())
    h = hidden.to(device=p.device, dtype=p.dtype)
    if apply_norm:
        h = norm(h)
    return head(h).float().cpu()


def word_token_ids(tokenizer, word: str) -> Dict[str, List[int]]:
    """Token ids for the surface variants that matter, with the leading-space form first.

    Multi-token words are NOT collapsed: the caller is handed the full id list and the
    aggregation choice is explicit (plan §6.1 "handle spans carefully and document the
    aggregation"). `primary` is the id used for scalar scores: the FIRST id of the
    leading-space form, which is the id the model must emit to start writing the word.
    """
    out: Dict[str, List[int]] = {}
    for name, s in (("bare", word), ("space", " " + word),
                    ("cap", word.capitalize()), ("space_cap", " " + word.capitalize())):
        out[name] = tokenizer(s, add_special_tokens=False)["input_ids"]
    out["primary"] = out["space"][:1]
    out["all_first_ids"] = sorted({v[0] for k, v in out.items()
                                   if k != "primary" and v})
    return out


@torch.no_grad()
def logit_lens_boombness(lm, hidden: torch.Tensor, concept_ids: Sequence[int],
                         codeword_ids: Sequence[int], apply_norm: bool = True) -> Dict[str, float]:
    """logit(concept) - logit(codeword) plus the probability/rank diagnostics of plan §6.1."""
    logits = logit_lens(lm, hidden, apply_norm=apply_norm)
    if logits.dim() > 1:
        logits = logits.reshape(-1, logits.shape[-1]).mean(0)
    lp = torch.log_softmax(logits, dim=-1)
    ci = torch.tensor(list(concept_ids), dtype=torch.long)
    wi = torch.tensor(list(codeword_ids), dtype=torch.long)
    # Aggregation over a multi-id word: max over the alternative surface forms, because the
    # model only has to pick ONE of them; mean would penalize a word with many rare variants.
    l_c = logits[ci].max().item()
    l_w = logits[wi].max().item()
    p_c = lp[ci].logsumexp(0).exp().item()
    p_w = lp[wi].logsumexp(0).exp().item()
    order = torch.argsort(logits, descending=True)
    rank = {int(t): int((order == t).nonzero()[0, 0]) for t in torch.cat([ci, wi]).tolist()}
    return {
        "logit_concept": l_c, "logit_codeword": l_w,
        "logit_lens_boombness": l_c - l_w,
        "p_concept": p_c, "p_codeword": p_w,
        "log_ratio": float(torch.log(torch.tensor(max(p_c, 1e-30) / max(p_w, 1e-30)))),
        "rank_concept": min(rank[int(t)] for t in ci.tolist()),
        "rank_codeword": min(rank[int(t)] for t in wi.tolist()),
        "apply_norm": apply_norm,
    }


# --------------------------------------------------------------------------- #
# B. Directions from the 2x2
# --------------------------------------------------------------------------- #
@dataclass
class DirectionSet:
    """Per-layer directions estimated from matched 2x2 cell means.

    All tensors are float32 CPU, indexed by BLOCK layer. `raw` keeps the un-normalized
    difference so a caller can use the natural dose unit ||d|| (the house `gap`) instead of
    inventing an alpha scale.
    """
    layers: List[int]
    d_surface: Dict[int, torch.Tensor] = field(default_factory=dict)
    d_context: Dict[int, torch.Tensor] = field(default_factory=dict)
    d_inter: Dict[int, torch.Tensor] = field(default_factory=dict)
    d_naive: Dict[int, torch.Tensor] = field(default_factory=dict)
    gap: Dict[str, Dict[int, float]] = field(default_factory=dict)
    n_per_cell: Dict[str, int] = field(default_factory=dict)
    meta: Dict[str, object] = field(default_factory=dict)

    def get(self, name: str, layer: int) -> torch.Tensor:
        return getattr(self, name)[layer]

    def as_payload(self) -> Dict[str, object]:
        return {"layers": self.layers, "layer_convention": LAYER_CONVENTION,
                "d_surface": self.d_surface, "d_context": self.d_context,
                "d_inter": self.d_inter, "d_naive": self.d_naive,
                "gap": self.gap, "n_per_cell": self.n_per_cell, "meta": self.meta}


def _unit(v: torch.Tensor) -> torch.Tensor:
    n = v.norm()
    if not torch.isfinite(n) or n < 1e-12:
        raise ValueError("cannot normalize a zero/non-finite direction")
    return v / n


def estimate_directions(cell_means: Dict[str, Dict[int, torch.Tensor]],
                        n_per_cell: Optional[Dict[str, int]] = None,
                        meta: Optional[Dict[str, object]] = None) -> DirectionSet:
    """Build d_surface / d_context / d_inter / d_naive from per-layer 2x2 cell means.

    cell_means: {"A"|"B"|"C"|"E": {block_layer: Tensor[H]}}. Every cell must cover the same
    layers — a missing cell is an error, not a silently-dropped layer (plan §2.2).
    """
    missing = {c for c in "ABCE"} - set(cell_means)
    if missing:
        raise ValueError(f"estimate_directions needs all four 2x2 cells; missing {sorted(missing)}")
    layer_sets = [set(cell_means[c]) for c in "ABCE"]
    layers = sorted(set.intersection(*layer_sets))
    dropped = sorted(set.union(*layer_sets) - set(layers))
    if dropped:
        raise ValueError(f"cells do not cover the same layers; layers missing from some cell: {dropped}")

    out = DirectionSet(layers=layers, n_per_cell=dict(n_per_cell or {}),
                       meta={"layer_convention": LAYER_CONVENTION, **(meta or {})})
    out.gap = {k: {} for k in ("d_surface", "d_context", "d_inter", "d_naive")}
    for L in layers:
        A, B, C, E = (cell_means[c][L].float() for c in "ABCE")
        raw = {
            "d_surface": 0.5 * ((B - C) + (E - A)),
            "d_context": 0.5 * ((C - A) + (B - E)),
            "d_inter": (B - C) - (E - A),
            "d_naive": B - A,
        }
        for name, v in raw.items():
            out.gap[name][L] = float(v.norm())
            getattr(out, name)[L] = _unit(v) if out.gap[name][L] > 1e-12 else v
    return out


def direction_boombness(h: torch.Tensor, d: torch.Tensor) -> Dict[str, float]:
    """Both projections plan §6.2 asks for: cosine (normalized) and raw dot (unnormalized)."""
    h = h.float().reshape(-1)
    d = d.float().reshape(-1)
    hn, dn = h.norm(), d.norm()
    dot = float(torch.dot(h, d))
    return {
        "dot": dot,
        "cosine": float(dot / (hn * dn)) if hn > 1e-12 and dn > 1e-12 else 0.0,
        "projection": float(dot / dn) if dn > 1e-12 else 0.0,   # component along d, in h's units
        "h_norm": float(hn),
    }


# --------------------------------------------------------------------------- #
# Controls (plan §2.5)
# --------------------------------------------------------------------------- #
def random_control_direction(d: torch.Tensor, seed: int) -> torch.Tensor:
    """Norm-matched Gaussian control. Delegates to the house helper so the control is the
    SAME construction used by every previous result in this repo."""
    pc = __import__("pair_common")
    return pc.norm_matched_random(d, 1, seed=seed)[0]


def orthogonal_control_direction(d: torch.Tensor, seed: int) -> torch.Tensor:
    """Norm-matched but orthogonal to d — separates 'any perturbation' from 'this axis'."""
    pc = __import__("pair_common")
    return pc.orthogonal_random(d, 1, seed=seed)[0]


def orthogonalize(d: torch.Tensor, against: torch.Tensor) -> torch.Tensor:
    """Remove the `against` component from d (used for Boombness ⟂ refusal, plan §10.4)."""
    a = _unit(against.float().reshape(-1))
    v = d.float().reshape(-1)
    return v - torch.dot(v, a) * a
