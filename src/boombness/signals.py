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
import math
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
    """Diagnostic tokenization of a word's surface variants.

    DO NOT USE `all_first_ids` FOR SCORING — use `readout_ids` below. Kept only because the
    tokenization audit reports these variants, and because the bug it caused is worth being
    able to reproduce. See the docstring of `readout_ids`.
    """
    out: Dict[str, List[int]] = {}
    for name, s in (("bare", word), ("space", " " + word),
                    ("cap", word.capitalize()), ("space_cap", " " + word.capitalize())):
        out[name] = tokenizer(s, add_special_tokens=False)["input_ids"]
    out["primary"] = out["space"][:1]
    out["all_first_ids"] = sorted({v[0] for k, v in out.items()
                                   if k != "primary" and v})
    return out


def readout_ids(tokenizer, word: str) -> Dict[str, object]:
    """The token ids that may legitimately stand for `word` in a next-token / logit-lens score.

    WHY THIS EXISTS (bug found by the self-review, 2026-08-16, and it was corrupting results):
    the obvious construction — take the FIRST id of every surface variant — is wrong for any
    word that is multi-token in some variant. On Llama-3.1-8B:

        " carrot" -> [' carrot']              (1 token)
        "carrot"  -> ['car', 'rot']           first id is 'car'
        "Carrot"  -> ['Car', 'rot']           first id is 'Car'
        " Carrot" -> [' Car', 'rot']          first id is ' Car'

    so three of carrot's four "first ids" are the generic English word **car**, one of the most
    frequent tokens in the vocabulary. Meanwhile every variant of "bomb" is a single token that
    really does spell bomb. Scoring `logit(concept) - logit(codeword)` off those sets therefore
    inflated the codeword side with car-the-vehicle, and inflated it by a context-dependent
    amount — a systematic, ARM-ASYMMETRIC bias in exactly the quantity the sprint measures.

    The fix is to score only tokens that spell the whole word:
      primary_id     the leading-space single-token form, ' word'. This is the token that
                     actually appears in our prompts (the generator guarantees every occurrence
                     is preceded by a space) and the token the model must emit to answer with
                     the word. ONE id per word, so the two arms are exactly symmetric.
      full_word_ids  every variant that is a single token AND decodes (stripped, casefolded) to
                     the word. Recorded for a robustness check; note it is asymmetric in SIZE
                     between words (1 for carrot, 4 for bomb), and since the scorers aggregate
                     with max(), more variants can only raise a score — so it must not be the
                     default.

    Raises if the leading-space form is not a single token: that is a modelling decision
    (which subtoken represents the word?) that must be made explicitly, not defaulted.
    """
    variants: Dict[str, List[int]] = {}
    for name, s in (("bare", word), ("space", " " + word),
                    ("cap", word.capitalize()), ("space_cap", " " + word.capitalize())):
        variants[name] = tokenizer(s, add_special_tokens=False)["input_ids"]

    space_ids = variants["space"]
    if len(space_ids) != 1:
        raise ValueError(
            f"readout_ids({word!r}): ' {word}' tokenizes to {len(space_ids)} tokens "
            f"{[tokenizer.decode([i]) for i in space_ids]}, not 1. Decide explicitly how a "
            f"multi-token word should be scored before using a logit-lens readout on it.")

    full: List[int] = []
    for name, ids in variants.items():
        if len(ids) != 1:
            continue
        if tokenizer.decode(ids).strip().casefold() == word.casefold():
            full.append(ids[0])

    return {
        "word": word,
        "primary_id": space_ids[0],
        "primary_piece": tokenizer.decode(space_ids),
        "full_word_ids": sorted(set(full)),
        "full_word_pieces": [tokenizer.decode([i]) for i in sorted(set(full))],
        "variants": {k: v for k, v in variants.items()},
        "rejected_first_ids": sorted({v[0] for v in variants.values()
                                      if len(v) > 1}),
    }


def readout_id_pair(tokenizer, concept: str, codeword: str,
                    mode: str = "primary") -> Tuple[List[int], List[int], Dict[str, object]]:
    """Symmetric, validated id groups for (concept, codeword). Returns (c_ids, w_ids, meta).

    mode="primary"   one id each — the default, and the only fully symmetric option.
    mode="full_word" every single-token full-word variant; asymmetric in count, so it is a
                     robustness check rather than the headline metric.
    """
    rc = readout_ids(tokenizer, concept)
    rw = readout_ids(tokenizer, codeword)
    if mode == "primary":
        c_ids, w_ids = [rc["primary_id"]], [rw["primary_id"]]
    elif mode == "full_word":
        c_ids, w_ids = list(rc["full_word_ids"]), list(rw["full_word_ids"])
    else:
        raise ValueError(f"unknown readout id mode {mode!r}")
    if set(c_ids) & set(w_ids):
        raise ValueError(f"concept and codeword share readout ids {sorted(set(c_ids) & set(w_ids))} "
                         "— the score would be partly the same number on both sides")
    return c_ids, w_ids, {"mode": mode, "concept": rc, "codeword": rw,
                          "concept_ids": c_ids, "codeword_ids": w_ids}


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


@torch.no_grad()
def logit_lens_boombness_batch(lm, hidden: torch.Tensor, concept_ids: Sequence[int],
                               codeword_ids: Sequence[int],
                               apply_norm: bool = True) -> List[Dict[str, float]]:
    """Batched `logit_lens_boombness`: hidden is [N, H], returns N records.

    One `lm_head` matmul for the whole batch instead of N. Scoring the full bank touches
    ~100k (layer, position) pairs, and a per-vector call spends nearly all its time on
    host/device round-trips rather than on the 4096 x |V| matmul itself.
    """
    if hidden.dim() != 2:
        raise ValueError(f"expected [N, H], got {tuple(hidden.shape)}")
    logits = logit_lens(lm, hidden, apply_norm=apply_norm)      # [N, V] float32 cpu
    lp = torch.log_softmax(logits, dim=-1)
    ci = torch.tensor(sorted(set(concept_ids)), dtype=torch.long)
    wi = torch.tensor(sorted(set(codeword_ids)), dtype=torch.long)
    l_c = logits[:, ci].max(dim=1).values
    l_w = logits[:, wi].max(dim=1).values
    p_c = lp[:, ci].logsumexp(dim=1).exp()
    p_w = lp[:, wi].logsumexp(dim=1).exp()
    # COMPETITION rank of the best variant of each word: the number of tokens with a strictly
    # greater logit. Deliberately not the argsort position, which is arbitrary within a tie
    # block.
    #
    # CAVEAT, measured 2026-08-16 (smoke 1000604 vs 1001753): this rank is ILL-CONDITIONED
    # wherever it is large. The float32 logit distribution has a very flat tail, so tie and
    # near-tie blocks are hundreds of tokens wide, and a 1e-7 change in the logit (the ordinary
    # reduction-order difference between a batched and an unbatched matmul) moves the rank by
    # up to ~283 out of 128256. Every other metric here agreed to <= 3e-5 across that same
    # change. Treat rank as a coarse diagnostic that is meaningful only when SMALL (say < 100);
    # use `logit_lens_boombness` or the probability mass for anything quantitative.
    rank_c = (logits > l_c.unsqueeze(1)).sum(dim=1)
    rank_w = (logits > l_w.unsqueeze(1)).sum(dim=1)
    out = []
    for i in range(hidden.shape[0]):
        pc_, pw_ = float(p_c[i]), float(p_w[i])
        out.append({
            "logit_concept": float(l_c[i]), "logit_codeword": float(l_w[i]),
            "logit_lens_boombness": float(l_c[i] - l_w[i]),
            "p_concept": pc_, "p_codeword": pw_,
            "log_ratio": math.log(max(pc_, 1e-30) / max(pw_, 1e-30)),
            "rank_concept": int(rank_c[i]), "rank_codeword": int(rank_w[i]),
            "apply_norm": apply_norm,
        })
    return out


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


# The two controls must be INDEPENDENT draws. `pair_common.orthogonal_random` internally calls
# `norm_matched_random` with the SAME seed and then projects out the component along d — and in
# 4096 dimensions a random vector's component along any fixed direction is ~1/sqrt(4096) ≈ 0.016,
# so that projection changes ~0.02% of the vector. Passing the same seed to both therefore yields
# two near-identical vectors, and reporting "random and orthogonal both fail" would be one
# observation stated twice rather than two independent controls. (Found by the tick-16 audit: the
# two arms had agreed to 3 decimal places, which should have been the tell.)
ORTHOGONAL_SEED_OFFSET = 977_777


def orthogonal_control_direction(d: torch.Tensor, seed: int) -> torch.Tensor:
    """Norm-matched but orthogonal to d — separates 'any perturbation' from 'this axis'.

    Uses a seed offset from the random control so the two are independent draws.
    """
    pc = __import__("pair_common")
    return pc.orthogonal_random(d, 1, seed=seed + ORTHOGONAL_SEED_OFFSET)[0]


def in_subspace_control_direction(payload: dict, layer: int, d: torch.Tensor,
                                  seed: int, orthogonalize_against_arm: bool = False):
    """A VARIANCE-MATCHED control: random INSIDE the span of the 2x2 cell means, not in R^4096.

    WHY THIS EXISTS (review #5). Every "the matched random control is inert" statement in this sprint
    used `random_control_direction`, an isotropic draw in the full hidden space. Review #5 measured
    what that actually controls for: at L11 on Qwen3, projecting out `d_surface` removes 89.97% of
    the spread of the four cell means, while the isotropic control removes 0.018% -- about 5000x
    less -- and cos(d_surface, random) is 0.014, exactly the 1/sqrt(hidden) of an isotropic draw. So
    the control's inertness is a property of high-dimensional geometry, not an experimental result:
    a random rank-1 projection at the same depth was never going to do anything, whatever the model
    represents there.

    This control draws inside the span of the (mean-centred) cell means instead. That subspace is
    where the 2x2 design's variance lives and where `d_surface` itself lies, so a draw from it
    removes a COMPARABLE amount of real structure. The question it answers is the one that matters:
    is the behavioural effect about THIS axis, or about ablating any direction carrying the concept
    contrast?

    It is deliberately a STRONG control -- with four cells the centred span is at most 3-dimensional,
    so a draw has a substantial expected overlap with `d_surface`. That is the point: an isotropic
    control can only fail to falsify, while this one can. Its realised overlap and the spread it
    removes are recorded by the caller so the strength is measured rather than assumed.

    Falls back to `orthogonal_control_direction` (recorded, never silent) if the payload has no
    usable cell means at this layer.
    """
    cm = payload.get("cell_means")
    if not isinstance(cm, dict):
        return orthogonal_control_direction(d, seed), "fallback:no_cell_means"
    rows = []
    for cell in sorted(cm):
        v = cm[cell].get(layer) if isinstance(cm[cell], dict) else None
        if v is not None:
            rows.append(v.float().reshape(-1))
    if len(rows) < 2:
        return orthogonal_control_direction(d, seed), f"fallback:{len(rows)}_cell_means_at_L{layer}"
    M = torch.stack(rows)
    M = M - M.mean(dim=0, keepdim=True)          # centre: the SPREAD is the structure, not the mean
    # An orthonormal basis for the centred span; drop numerically-null directions so the draw cannot
    # be dominated by a component that carries no variance.
    U, S, Vh = torch.linalg.svd(M, full_matrices=False)
    keep = int((S > (S.max() * 1e-6)).sum())
    basis = Vh[:keep]
    if orthogonalize_against_arm:
        # Strictly the better control, and the one that answers the question cleanly: remove the
        # arm direction FROM THE BASIS, so the draw lives in the part of the concept subspace that
        # is not `d_surface`. Without this the draw shares variance with the arm (cos ran -0.48 to
        # +0.81 over layers on the Llama fit), so an effect from the control would be ambiguous
        # between "any concept-subspace axis works" and "the control partly IS the arm".
        u = (d.float().reshape(-1) / (d.float().norm() + 1e-8)).reshape(1, -1)
        proj = basis - (basis @ u.T) @ u
        # RANK MUST COME FROM THE SINGULAR VALUES, NOT THE ROW COUNT. The first version kept
        # `Vh[:proj.shape[0]]`, i.e. 3 rows for a 3-row matrix whose rank is now 2 -- and the third
        # Vh row is an arbitrary unit vector orthogonal to the other two, which is exactly the
        # direction just removed. The draw therefore still loaded on the arm (measured cos -0.73 at
        # L6) and the orthogonalisation was silently a no-op.
        # RANK THRESHOLD MUST BE LOOSE, AND THE RESULT RE-ORTHOGONALISED ANYWAY. A 1e-6 relative
        # cut looked right offline and then failed inside the real run: at several layers the
        # post-projection residual of the arm direction survives at ~1e-4 of the top singular
        # value, so rank came back 3 instead of 2, `Vh2[2]` was essentially that numerical residue,
        # and the draw loaded on the arm -- the run's own diagnostic reported
        # cos_with_arm_direction = -0.5709 at L8 where it must be ~0. Two independent guards now:
        # a 1e-3 relative cut, AND an explicit re-orthogonalisation of the drawn vector, which is
        # correct whatever the rank detection decides.
        # DETERMINISTIC BASIS. After removing the arm from an orthonormal rank-3 span the residual
        # has singular values ~[1, 1, 0] -- the top two are equal to ~2e-7 relative -- so SVD's
        # choice of basis inside that degenerate 2-D eigenspace is arbitrary and depends on the
        # LAPACK build. Review #6 found the four SLURM runs agreed byte-for-byte with each other
        # (same nodes, same environment) but NOT with an offline recomputation on the login node:
        # the L8 control differed by a rotation, so the run's control removed 5.1971% of the
        # cell-mean spread where the offline check said 5.35%. The draw is reproducible only within
        # one environment, which is not reproducible.
        #
        # Fixed by never relying on SVD's basis choice: project the arm out of the ORIGINAL basis
        # rows and Gram-Schmidt them in a fixed order. Rank still comes from the singular values,
        # but the basis vectors are now a deterministic function of (payload, layer) alone.
        U2, S2, Vh2 = torch.linalg.svd(proj, full_matrices=False)
        keep = int((S2 > (S2.max() * 1e-3)).sum()) if float(S2.max()) > 0 else 0
        if keep == 0:
            return orthogonal_control_direction(d, seed), "fallback:span_is_the_arm_alone"
        rows, basis_list = [], []
        for i in range(proj.shape[0]):
            w = proj[i].clone()
            for b in basis_list:
                w = w - torch.dot(w, b) * b
            n = w.norm()
            if float(n) > 1e-4 * float(proj.norm()):
                basis_list.append(w / n)
            if len(basis_list) == keep:
                break
        if not basis_list:
            return orthogonal_control_direction(d, seed), "fallback:gram_schmidt_collapsed"
        basis = torch.stack(basis_list)
        keep = basis.shape[0]
    pc = __import__("pair_common")
    v = pc.in_subspace_random(basis, d.float(), 1, seed=seed)[0].float()
    tag = "in_subspace"
    if orthogonalize_against_arm:
        u = d.float().reshape(-1) / (d.float().norm() + 1e-8)
        v = v - torch.dot(v, u) * u                      # second guard, independent of the rank cut
        n = v.norm()
        if float(n) < 1e-6:
            return orthogonal_control_direction(d, seed), "fallback:draw_collapsed_onto_the_arm"
        v = v / n * d.float().norm()
        tag = "in_subspace_orth"
    return v.to(d.dtype), f"{tag}:k={keep}"


def cell_span_basis_direction(payload: dict, layer: int, index: int):
    """The `index`-th orthonormal basis vector of the centred 2x2 cell-mean span.

    WHY THIS EXISTS -- it tests the one alternative explanation that would deflate the sprint's
    central result. Prediction rises with depth and causation falls with depth, giving
    Spearman -0.850. But a projection at L31 sits one layer before the unembedding with almost no
    computation left to amplify it, while an L8 edit propagates through twenty-three layers. So
    "causation falls with depth" might be a GENERIC property of late ablation rather than anything
    about `d_surface` -- two independent depth trends dressed up as a dissociation.

    The discriminating test is to ablate the ENTIRE 3-dimensional concept subspace, which is the
    largest edit that subspace admits, at both depths. If the full span moves ASR at L8 and does
    nothing at L31, the late null is architectural and the anti-alignment claim must be weakened.
    If the full span moves ASR at L31 too, then late ablation CAN act, and `d_surface`'s late null
    is a fact about that direction rather than about depth.

    Composing `cell_span0+cell_span1+cell_span2` at one layer projects out each in turn; because the
    vectors are orthonormal, sequential projection equals projecting out their span.

    Basis is the deterministic Gram-Schmidt of the centred cell means (same construction as
    `in_subspace_control_direction`), so the three indices are stable and jointly orthonormal.
    """
    cm = payload.get("cell_means")
    if not isinstance(cm, dict):
        raise SystemExit("cell_span requires `cell_means` in the fit payload")
    rows = [cm[c][layer].float().reshape(-1) for c in sorted(cm)
            if isinstance(cm.get(c), dict) and cm[c].get(layer) is not None]
    if len(rows) < 2:
        raise SystemExit(f"cell_span: only {len(rows)} cell means at L{layer}")
    M = torch.stack(rows)
    M = M - M.mean(dim=0, keepdim=True)
    basis = []
    for i in range(M.shape[0]):
        w = M[i].clone()
        for b in basis:
            w = w - torch.dot(w, b) * b
        n = w.norm()
        if float(n) > 1e-4 * float(M.norm()):
            basis.append(w / n)
    if index >= len(basis):
        raise SystemExit(f"cell_span{index}: span at L{layer} has rank {len(basis)}")
    return basis[index], f"cell_span:{index}/{len(basis)}"


def orthogonalize(d: torch.Tensor, against: torch.Tensor) -> torch.Tensor:
    """Remove the `against` component from d (used for Boombness ⟂ refusal, plan §10.4)."""
    a = _unit(against.float().reshape(-1))
    v = d.float().reshape(-1)
    return v - torch.dot(v, a) * a


# --------------------------------------------------------------------------- #
# Whole-answer forced-choice scoring (added 2026-08-18)
# --------------------------------------------------------------------------- #
ANSWER_CASES = ("{w}", "{W}")  # lower and Capitalized; applied identically to every option


def answer_variants(word: str, spaced: bool = True) -> List[str]:
    """The surface strings a forced answer may take, built IDENTICALLY for every option.

    WHY THIS REPLACES SINGLE-TOKEN SCORING. `readout_ids` picks ONE id per word, the leading-space
    form, precisely so the two arms are symmetric. Measured on the smoke (36 prompts, jobs
    764702/764703) that id is not what the model emits. With a forced "Answer:" prefix the argmax
    next token is:

        comprehension   ' Literal' (10/24)   ' Liter' (6/24)   ' Neither' (4/24)
        semantic        ' Car'     (8/12)    ' Neither' (3/12)  ' Bomb' (1/12)

    Two separate problems, both invisible to a single-id readout:
      1. THE MODEL CAPITALISES. ' literal' (24016) was scored; ' Literal' (50774) is what it wants.
      2. THE CAPITALISED CODEWORD IS MULTI-TOKEN. ' Car' is the FIRST SUBTOKEN of ' Carrot', and
         `readout_ids` rejects it by design because 'car' is the generic English word. So on
         Llama-3.1-8B `bomb` has four single-token variants (' bomb', 'bomb', ' Bomb', 'Bomb') and
         `carrot` has exactly one (' carrot'). No single-next-token readout can represent the
         model's preferred spelling of the codeword, so the concept side is structurally advantaged
         in every semantic_logodds ever computed -- including the one carrying G1's +68%-of-span
         headline. Adding variants does not fix it either: summing `full_word_ids` gives the concept
         four ids against the codeword's one, which is the same bias with a larger constant.

    The fix is to stop scoring a token and score the ANSWER. P(model answers "Carrot") is exactly
    P(' Car') * P('rot' | ' Car'); that is a joint probability, not a length artefact, so no length
    normalisation is wanted -- the quantity we need IS the probability of emitting the whole word.
    Every option gets the same number of surface forms built by the same rule, so symmetry is a
    property of the construction rather than an accident of the tokenizer.
    """
    stem = " " + word if spaced else word
    return [c.format(w=stem, W=stem[:1] + stem[1:2].upper() + stem[2:] if spaced
                     else stem[:1].upper() + stem[1:]) for c in ANSWER_CASES]


def string_option_readout(lm, context: str, options: Dict[str, Sequence[str]],
                          max_batch: int = 16) -> Dict[str, float]:
    """Teacher-forced log P(option | context), summed over each option's surface variants.

    One batched forward over `context + variant` per variant. Returns logp_/p_ per option plus
    `option_mass` (the total probability the forced answer is any of the options) and `top1_id`,
    the token the model actually wants next -- the field whose absence let a 1e-5 readout ship.
    """
    ctx_ids = lm.tokenizer(context, add_special_tokens=False)["input_ids"]
    flat: List[Tuple[str, List[int]]] = []
    for name, variants in options.items():
        for v in variants:
            vid = lm.tokenizer(v, add_special_tokens=False)["input_ids"]
            if vid:
                flat.append((name, vid))
    if not flat:
        raise ValueError("string_option_readout: no scorable variants")

    scores: Dict[str, List[float]] = {name: [] for name in options}
    top1 = None
    for s in range(0, len(flat), max_batch):
        chunk = flat[s:s + max_batch]
        seqs = [ctx_ids + vid for _, vid in chunk]
        width = max(len(x) for x in seqs)
        pad = lm.tokenizer.pad_token_id
        if pad is None:
            pad = lm.tokenizer.eos_token_id
        # LEFT padding would shift the context; pad on the RIGHT and read only real positions.
        inp = torch.full((len(seqs), width), pad, dtype=torch.long)
        att = torch.zeros((len(seqs), width), dtype=torch.long)
        for i, x in enumerate(seqs):
            inp[i, :len(x)] = torch.tensor(x, dtype=torch.long)
            att[i, :len(x)] = 1
        out = lm.model(input_ids=inp.to(lm.model.device),
                       attention_mask=att.to(lm.model.device), use_cache=False)
        lp = torch.log_softmax(out.logits.float(), dim=-1).cpu()
        if top1 is None:
            top1 = int(lp[0, len(ctx_ids) - 1, :].argmax())
        for i, (name, vid) in enumerate(chunk):
            tot = 0.0
            for j, tid in enumerate(vid):
                # position predicting token j of the variant is len(ctx)-1+j
                tot += float(lp[i, len(ctx_ids) - 1 + j, tid])
            scores[name].append(tot)

    res: Dict[str, float] = {}
    allv: List[float] = []
    for name, vals in scores.items():
        t = torch.tensor(vals)
        lse = float(t.logsumexp(0))
        res[f"logp_{name}"] = lse
        res[f"p_{name}"] = float(math.exp(lse))
        res[f"n_variants_{name}"] = len(vals)
        allv.extend(vals)
    res["option_mass"] = float(torch.tensor(allv).logsumexp(0).exp())
    res["top1_id"] = top1
    return res
