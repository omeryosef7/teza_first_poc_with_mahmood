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
    try:
        hit = dc.find_word_occurrences(lm.tokenizer, ids, probe_word)
        last_idxs = list(hit.last_idx)
    except ValueError:
        # Strict id-matching can miss a word whose in-context tokenization differs from its
        # standalone variants (e.g. 'pumpkin' in some ClearHarm prompts). Fall back to the
        # offset-based finder, which reads token spans off character offsets (audit-preferred,
        # "more complete"). add_special_tokens=False keeps indices aligned with `ids`. This
        # branch only runs where the strict finder ALREADY raised => no regression for callers
        # whose words resolve strictly.
        hit = dc.find_word_occurrences_in_text(
            lm.tokenizer, templated_text, probe_word, add_special_tokens=False)
        last_idxs = list(hit.last_idx)
    last = last_idxs[-1]
    n = len(ids)
    return PairPositions(
        codeword_all=last_idxs, codeword_last=last,
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
        # dtype=long is required: torch.tensor([]) defaults to float32, which makes
        # index_select raise for an empty position list (reachable from
        # capture_components when every requested position resolves to None).
        idx = torch.tensor([p for p in self.positions if 0 <= p < hidden.shape[0]],
                           device=hidden.device, dtype=torch.long)
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
# Demonstration K/V mediation (S3, NEXT_CAUSAL_SPRINT) — resid_pre write-hook
# --------------------------------------------------------------------------- #
class DemoStateSwap:
    """S3 (NEXT_CAUSAL_SPRINT): overwrite the pre-attention residual (resid_pre) at a
    FIXED set of positions with per-layer SOURCE rows, via forward-PRE hooks.

    K and V are projected from the block INPUT (resid_pre), so overwriting the resid_pre
    of the demonstration tokens swaps the K/V that the query attends to WITHOUT touching
    sequence length (no insertion/deletion) and without needing a past_key_values cache.
    This is the demo-K/V analogue of ds_common.LayerPatch (which edits the block OUTPUT).

    Args:
        model:      the HF model (layers found via ds_common._get_layers).
        positions:  token indices to overwrite at EVERY hooked layer (shared across
                    layers; length n_pos).
        source:     dict {layer_idx: Tensor[n_pos, hidden]} — the rows written at that
                    layer, aligned to `positions` order. The KEYS of this dict define the
                    set of layers that get a hook.
        batch_index: batch row to edit (default 0; the pipeline runs batch size 1).

    Invariants (unit-tested in tests/test_demostateswap_synthetic.py):
      (a) SELF-SWAP — if `source[L]` equals the receiver's OWN captured resid_pre at
          `positions` for every hooked layer L, the forward reproduces the no-hook
          baseline EXACTLY (bf16<->fp32 round-trips are lossless, so the write is a
          numerical no-op).
      (b) LOCALITY — only `positions` (and their causal downstream) change; earlier
          positions are never modified.
      (c) CLEANUP — all hook handles are removed on __exit__.

    The pre-hook signature MIRRORS ComponentCapture's (`args[0] if args else
    kwargs['hidden_states']`) so it works whether the decoder layer is called with the
    hidden state positionally or by keyword; it returns the modified (args, kwargs).
    """

    def __init__(self, model, positions: Sequence[int],
                 source: Dict[int, torch.Tensor], batch_index: int = 0):
        self.layers = dc._get_layers(model)
        self.positions = list(positions)
        self.source = source
        self.bi = batch_index
        self._handles: List[Any] = []

    def _pre_hook(self, li: int):
        rows = self.source[li]
        pos = self.positions

        def f(mod, args, kwargs=None):
            kwargs = {} if kwargs is None else kwargs
            h = args[0] if args else kwargs.get("hidden_states")
            h = h.clone()                                    # never edit in place
            seq = h.shape[1]
            # Length-preserving: write existing positions only. Keep source rows aligned
            # to `positions` order; drop any position that is out of range (KV-cached
            # decode steps hold only the new token) rather than raising.
            keep = [k for k, p in enumerate(pos) if 0 <= p < seq]
            if keep:
                idx = torch.tensor([pos[k] for k in keep], device=h.device)
                r = rows.to(h.dtype).to(h.device)
                sel = torch.tensor(keep, device=r.device)
                h[self.bi, idx, :] = r.index_select(0, sel)
            if args:
                return (h,) + tuple(args[1:]), kwargs
            kwargs["hidden_states"] = h
            return args, kwargs

        return f

    def __enter__(self):
        for li in self.source:
            self._handles.append(
                self.layers[li].register_forward_pre_hook(self._pre_hook(li),
                                                          with_kwargs=True))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


# --------------------------------------------------------------------------- #
# Component-level patching (§6: "attention-output vs MLP-output patching")
# --------------------------------------------------------------------------- #
class SubmodulePatch:
    """LayerPatch generalised to the attention / MLP sub-blocks.

    ds_common.LayerPatch edits the residual stream at the block OUTPUT, which cannot
    distinguish "the attention head wrote the mapping" from "the MLP consolidated it".
    This edits `layer.self_attn` or `layer.mlp` (or the block, for parity) with the same
    replace / add / project_out semantics and the same generation-safety guard.
    """

    # component -> submodule attr. None => the block itself. "resid_pre" is special:
    # it edits the INPUT to the block via a forward_pre_hook (== resid_post of L-1, but
    # enumerated as its own Phase-3 cell). The other three edit sub-block / block OUTPUT.
    _TARGETS = {"attn_out": "self_attn", "mlp_out": "mlp",
                "resid_post": None, "resid_pre": None}

    def __init__(self, model, layer_idx: int, component: str,
                 positions: Sequence[int], vector: Optional[torch.Tensor] = None,
                 mode: str = "replace", alpha: float = 1.0):
        if component not in self._TARGETS:
            raise ValueError(f"component must be one of {sorted(self._TARGETS)}")
        layer = dc._get_layers(model)[layer_idx]
        attr = self._TARGETS[component]
        self.component = component
        self.is_pre = (component == "resid_pre")
        self.module = layer if (attr is None) else getattr(layer, attr)
        self.positions = list(positions)
        self.vector = vector
        self.mode = mode
        self.alpha = alpha
        self._handle = None

    def _edit(self, hidden):
        """Apply replace/add/project_out at the requested positions (in-place on a clone)."""
        if hidden.shape[0] != 1:      # edits row 0 only; fail loud on batch>1 (audit finding 5)
            raise NotImplementedError("SubmodulePatch supports batch size 1 only")
        hidden = hidden.clone()
        v = None if self.vector is None else self.vector.to(hidden.dtype).to(hidden.device)
        seq = hidden.shape[1]
        for p in self.positions:
            if p < 0 or p >= seq:      # KV-cached decode steps: already in the cache
                continue
            if self.mode == "replace":
                hidden[0, p, :] = v
            elif self.mode == "add":
                hidden[0, p, :] = hidden[0, p, :] + self.alpha * v
            elif self.mode == "project_out":
                d = v / (v.norm() + 1e-8)
                comp = torch.dot(hidden[0, p, :].float(), d.float()).to(hidden.dtype)
                hidden[0, p, :] = hidden[0, p, :] - self.alpha * comp * d.to(hidden.dtype)
            else:
                raise ValueError(f"unknown mode {self.mode}")
        return hidden

    def _pre_hook(self, module, args, kwargs):
        """Edit the block INPUT hidden_states (resid_pre). Decoder layers receive
        hidden_states as args[0] (or kwargs['hidden_states'])."""
        if len(args) > 0 and torch.is_tensor(args[0]):
            new = self._edit(args[0])
            return (new,) + tuple(args[1:]), kwargs
        if "hidden_states" in kwargs and torch.is_tensor(kwargs["hidden_states"]):
            kwargs = dict(kwargs)
            kwargs["hidden_states"] = self._edit(kwargs["hidden_states"])
            return args, kwargs
        raise RuntimeError("resid_pre: could not locate hidden_states in block inputs")

    def _hook(self, module, inputs, output):
        is_tuple = isinstance(output, tuple)
        hidden = self._edit(output[0] if is_tuple else output)
        return (hidden,) + tuple(output[1:]) if is_tuple else hidden

    def __enter__(self):
        if self.is_pre:
            self._handle = self.module.register_forward_pre_hook(
                self._pre_hook, with_kwargs=True)
        else:
            self._handle = self.module.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None
        return False


# --------------------------------------------------------------------------- #
# Sub-block OUTPUT swap (Phase 6 causal MLP write) — per-position rows
# --------------------------------------------------------------------------- #
class ComponentOutSwap:
    """Overwrite the OUTPUT of a sub-block (`mlp` / `self_attn`) or the block itself at a
    FIXED set of positions with per-position SOURCE rows, per layer. This is the mlp/attn
    OUTPUT analogue of DemoStateSwap (which writes the block INPUT resid_pre) and of
    SubmodulePatch (which writes ONE shared vector to every position; this writes a distinct
    row per position, needed for a faithful donor->receiver swap).

    Args mirror DemoStateSwap:
        source: {layer_idx: Tensor[n_pos, hidden]} aligned to `positions`; its KEYS define
                which layers get a hook.
    Invariants (tests/test_componentoutswap_synthetic.py):
      (a) SELF-SWAP — source == receiver's OWN captured output at `positions` -> exact no-op.
      (b) LOCALITY — only `positions` (and causal downstream) change.
      (c) CLEANUP — handles removed on __exit__.
    """
    _ATTR = {"mlp_out": "mlp", "attn_out": "self_attn", "resid_post": None}

    def __init__(self, model, positions: Sequence[int], source: Dict[int, torch.Tensor],
                 component: str = "mlp_out", batch_index: int = 0):
        if component not in self._ATTR:
            raise ValueError(f"component must be one of {sorted(self._ATTR)}")
        self.layers = dc._get_layers(model)
        self.attr = self._ATTR[component]
        self.positions = list(positions)
        self.source = source
        self.bi = batch_index
        self._handles: List[Any] = []

    def _hook(self, li: int):
        rows = self.source[li]
        pos = self.positions

        def f(mod, inp, out):
            is_tuple = isinstance(out, tuple)
            h = (out[0] if is_tuple else out).clone()          # never edit in place
            seq = h.shape[1]
            keep = [k for k, p in enumerate(pos) if 0 <= p < seq]
            if keep:
                idx = torch.tensor([pos[k] for k in keep], device=h.device)
                r = rows.to(h.dtype).to(h.device)
                sel = torch.tensor(keep, device=r.device)
                h[self.bi, idx, :] = r.index_select(0, sel)
            return (h,) + tuple(out[1:]) if is_tuple else h

        return f

    def __enter__(self):
        for li in self.source:
            mod = self.layers[li] if self.attr is None else getattr(self.layers[li], self.attr)
            self._handles.append(mod.register_forward_hook(self._hook(li)))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


# --------------------------------------------------------------------------- #
# Attention knockout (§6) — per-layer AND per-head
# --------------------------------------------------------------------------- #
class AttentionKnockout:
    """Block attention from `query_positions` to `blocked_keys`, per layer and per head.

    REQUIRES the model to be loaded with attn_implementation="eager": under SDPA/flash a
    custom additive 4-D mask is not applied verbatim and the knockout silently becomes a
    no-op. This is the single biggest footgun in the existing knockout scripts.

    `heads=None` blocks every head (the existing all-head behaviour, whose mask has head
    dim 1). A head list expands the mask over the QUERY-head axis — note GQA: the
    attention-weight tensor is over `num_attention_heads`, not `num_key_value_heads`.
    """

    def __init__(self, model, layer_idxs: Sequence[int], query_positions: Sequence[int],
                 blocked_keys: Sequence[int], heads: Optional[Sequence[int]] = None):
        self.layers = [dc._get_layers(model)[i] for i in layer_idxs]
        self.q = list(query_positions)
        self.k = list(blocked_keys)
        self.heads = None if heads is None else list(heads)
        self.n_heads = int(model.config.num_attention_heads)
        self._handles = []

    def _pre(self, mod, args, kwargs):
        am = kwargs.get("attention_mask")
        if am is None or am.dim() != 4:
            raise RuntimeError("expected a 4-D additive attention mask; is the model "
                               "loaded with attn_implementation='eager'?")
        if am.shape[0] != 1:          # edits row 0 only; fail loud on batch>1 (audit finding 5)
            raise NotImplementedError("AttentionKnockout supports batch size 1 only")
        am = am.clone()
        if self.heads is not None and am.shape[1] == 1:
            am = am.expand(-1, self.n_heads, -1, -1).clone()
        min_val = torch.finfo(am.dtype).min
        hs = range(am.shape[1]) if self.heads is None else self.heads
        for qp in self.q:
            if qp >= am.shape[2]:
                continue
            for kp in self.k:
                if 0 <= kp <= qp and kp < am.shape[3]:
                    for h in hs:
                        am[0, h, qp, kp] = min_val
        kwargs["attention_mask"] = am
        return args, kwargs

    def __enter__(self):
        for layer in self.layers:
            self._handles.append(
                layer.self_attn.register_forward_pre_hook(self._pre, with_kwargs=True))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


# --------------------------------------------------------------------------- #
# Attention knockout that SURVIVES GENERATION (Phase 2 of the d_surface next phase)
# --------------------------------------------------------------------------- #
class AllQueryAttentionKnockout:
    """Block attention onto `blocked_keys` from EVERY query row, at prefill AND at decode.

    WHY THIS EXISTS, AND WHY `AttentionKnockout` COULD NOT BE REUSED.
    `AttentionKnockout` addresses query rows by ABSOLUTE prompt position. Under KV-cached
    autoregressive decoding the additive mask has shape [1, H, 1, kv_len]: there is exactly ONE
    query row, so `am.shape[2] == 1`, and its guard

        if qp >= am.shape[2]: continue

    skips every absolute query position on every decode step. The knockout therefore applies
    during prefill and silently switches itself off for the whole generation. Its own test
    asserts this as intended behaviour (tests/test_attnknockout_synthetic.py:185-192, "a query
    index past the current seq (e.g. a decode step) is skipped, not an error") -- correct for the
    teacher-forced readout it was built for, fatal for a behavioural experiment.

    A second, independent break in the same method: the causality guard `0 <= kp <= qp` compares
    an ABSOLUTE key index against a CACHE-LOCAL query index (0 on a decode step), so even a query
    row that survived the first guard would reject every demonstration key.

    The consequence if this had gone unnoticed is the reason the class is written rather than the
    guard patched: the run still emits rows, still reports `n_edges_cut`, still exits 0, and
    yields "full demonstration-block knockout does not change jailbreak ASR" -- a statement about
    a hook that turned itself off after the first generated token. That is this repo's documented
    absolute-position-index bug class (feedback_absolute_position_index_bug), which has already
    landed twice.

    THE INDEX ALGEBRA. KV-cache columns are ABSOLUTE positions, so `kp` indexes `am[..., kp]`
    directly at every step. Query row `r` of the current chunk is absolute position
    `past + r` where `past = am.shape[3] - am.shape[2]`. Causality permits row `r` to see key
    `kp` iff `past + r >= kp`, i.e. `r >= kp - past`. So the first blockable row is
    `lo = max(0, kp - past)` and every row from `lo` onward is blocked. At prefill `past == 0`
    and this reduces to the lower triangle; at decode `am.shape[2] == 1` and `lo == 0` whenever
    `kp <= past`, which is exactly the case that matters.

    `AttentionKnockout` IS DELIBERATELY LEFT UNTOUCHED. surgical_knockout.py and the G1/G3
    artifacts depend on its skip semantics; changing it would silently re-score published results.

    LIVENESS INSTRUMENTATION IS NOT OPTIONAL. `stats` counts decode-step forwards and decode-step
    edits so a caller can PROVE the mask fired during generation instead of assuming it. A run
    whose `n_decode_edits` is 0 is void, and the caller is expected to refuse to report it.
    """

    def __init__(self, model, layer_idxs, blocked_keys,
                 heads=None, stats=None):
        self.layers = [dc._get_layers(model)[i] for i in layer_idxs]
        self.k = sorted(set(int(x) for x in blocked_keys))
        self.heads = None if heads is None else list(heads)
        self.n_heads = int(model.config.num_attention_heads)
        self._handles = []
        self.stats = stats if stats is not None else {}
        for key in ("n_forward", "n_decode_forward", "n_edits", "n_decode_edits", "n_prefill_forward"):
            self.stats.setdefault(key, 0)

    def _pre(self, mod, args, kwargs):
        am = kwargs.get("attention_mask")
        if am is None or am.dim() != 4:
            raise RuntimeError("expected a 4-D additive attention mask; is the model loaded with "
                               "attn_implementation='eager'? Under SDPA/flash the mask edit is "
                               "discarded and the knockout is a silent no-op.")
        if am.shape[0] != 1:
            raise NotImplementedError("AllQueryAttentionKnockout supports batch size 1 only")
        am = am.clone()
        if self.heads is not None and am.shape[1] == 1:
            am = am.expand(-1, self.n_heads, -1, -1).clone()
        min_val = torch.finfo(am.dtype).min
        hs = range(am.shape[1]) if self.heads is None else self.heads
        n_q, kv_len = am.shape[2], am.shape[3]
        past = kv_len - n_q                     # absolute position of query row 0
        is_decode = (n_q == 1)
        n_edits = 0
        for kp in self.k:
            if kp >= kv_len:
                continue                        # key not in the cache yet
            lo = max(0, kp - past)              # first query row that may causally see kp
            if lo >= n_q:
                continue
            for h in hs:
                am[0, h, lo:, kp] = min_val
            n_edits += (n_q - lo) * (len(list(hs)) if self.heads is not None else am.shape[1])
        kwargs["attention_mask"] = am
        self.stats["n_forward"] += 1
        self.stats["n_decode_forward"] += int(is_decode)
        self.stats["n_prefill_forward"] += int(not is_decode)
        self.stats["n_edits"] += n_edits
        if is_decode:
            self.stats["n_decode_edits"] += n_edits
        return args, kwargs

    def __enter__(self):
        for layer in self.layers:
            self._handles.append(
                layer.self_attn.register_forward_pre_hook(self._pre, with_kwargs=True))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


# --------------------------------------------------------------------------- #
# SCOPED attention knockout — the WHICH-QUERY-ROWS decomposition of the above
# --------------------------------------------------------------------------- #
# `AllQueryAttentionKnockout` answers one question: "does the model need the demonstration
# keys AT ALL?" It blocks them from EVERY query row, so a positive result cannot say WHERE
# the dependence lives — the demo tokens' own self-processing, the final-query rows at
# prefill, or the generated rows at decode are all cut at once. These five modes split that
# single edit into its addressable pieces WITHOUT touching either existing class: the
# `legacy_all_query` mode is asserted byte-identical to `AllQueryAttentionKnockout`, which is
# the bridge from every committed knockout artifact to the scoped ones.
#
# TWO MODES LEGITIMATELY MAKE ZERO DECODE EDITS, so the single global "n_decode_edits > 0 or
# the run is void" gate that guards the all-query hook would reject them as dead when they
# are working exactly as specified. That gate must therefore be per-mode, and it must read
# the SAME table the hook is written against — hence `LIVENESS_REQUIREMENT` /
# `LIVENESS_MUST_BE_ZERO` live here, next to the hook, and the consumer imports them rather
# than restating them at the call site where they can drift.
SCOPED_KNOCKOUT_MODES = (
    "legacy_all_query",       # every query row, prefill AND decode == AllQueryAttentionKnockout
    "query_prefill_only",     # prefill only, only the final-query span rows
    "decode_only",            # decode only; prefill left completely alone
    "response_query_only",    # final-query rows at prefill + every generated row at decode
    "demo_processing_only",   # prefill only, only the rows INSIDE the demonstration block
    # ADDED 2026-09-02 (DCS phase, plan section 1.8 KO-1/KO-2). The most SURGICAL scope in the
    # ladder: prefill only, and only the rows of ONE token occurrence in the query -- the final
    # occurrence of the prompt's `target_surface`.
    #
    # WHY ONE MODE COVERS BOTH KO-1 AND KO-2. `target_surface` is a bank field that already holds
    # the CODEWORD in cells A/C and the explicit CONCEPT in cells B/E. So "block the final
    # target-surface row from seeing the demonstrations" is literally KO-1 in the Doublespeak cell
    # and its own matched specificity control KO-2 in the direct-harmful cell, with ONE code path
    # and ONE dose. Two modes would have been two chances to make them differ by something other
    # than the cell, which is the comparison the whole experiment rests on.
    #
    # Distinct from `query_prefill_only`, which blocks the WHOLE query span: if the narrow scope is
    # null and the wide one is not, the mapping is built during demonstration processing rather
    # than retrieved at the final surface token. Collapsing them would erase that answer.
    "target_surface_row_only",
    # ADDED 2026-09-03 (DCS phase, DCS-C-010 / open question 1). `query_prefill_only` cuts the WHOLE
    # query span and therefore cannot say WHICH position retrieves the mapping -- the ~10 intervening
    # query tokens, or the final row where the forced-choice answer is actually scored. This scope
    # isolates the LAST row of the query span.
    #
    # It needs no new plumbing: the last query position is `max(query_span)`, derived from the span
    # the consumer already resolves. Deliberately NOT a second `surface_span`-style argument -- a
    # scope computable from an existing argument should be, or the two can disagree.
    #
    # Together with `target_surface_row_only` the ladder becomes separable: codeword row / last row /
    # whole query span. If the last row alone reproduces `query_prefill_only`, retrieval happens AT
    # THE READOUT; if it does not, retrieval is distributed across the span.
    "prompt_last_row_only",
    # ADDED 2026-09-03 (DCS-B-010). The ladder so far has TWO 1-row nulls and ONE 32-row collapse,
    # which a "retrieval is distributed" account and a "row-count threshold" account explain
    # equally well. Separating them needs intermediate row counts, so this scope takes an
    # ARBITRARY caller-supplied row set through the same `surface_span` plumbing
    # `target_surface_row_only` already uses -- the consumer passes the last K rows of the query
    # span, and K is swept.
    #
    # One mode rather than one mode per K, because a family of near-identical named modes is a
    # family of places for them to drift apart.
    "query_last_k_rows",
)

# mode -> counters that MUST be > 0 for the run to be reportable (PROOF OF LIFE)
LIVENESS_REQUIREMENT: Dict[str, tuple] = {
    "legacy_all_query":     ("n_prefill_edits", "n_decode_edits"),
    "query_prefill_only":   ("n_prefill_edits",),
    "decode_only":          ("n_decode_edits",),
    "response_query_only":  ("n_prefill_edits", "n_decode_edits"),
    "demo_processing_only": ("n_prefill_edits",),
    "target_surface_row_only": ("n_prefill_edits",),
    "prompt_last_row_only": ("n_prefill_edits",),
    "query_last_k_rows": ("n_prefill_edits",),
}

# mode -> counters that MUST be exactly 0; a non-zero one means the scoping leaked and the
# mode is secretly a different (larger) intervention than the one being reported.
LIVENESS_MUST_BE_ZERO: Dict[str, tuple] = {
    "legacy_all_query":     (),
    "query_prefill_only":   ("n_decode_edits",),
    "decode_only":          ("n_prefill_edits",),
    "response_query_only":  (),
    "demo_processing_only": ("n_decode_edits",),
    "target_surface_row_only": ("n_decode_edits",),
    "prompt_last_row_only": ("n_decode_edits",),
    "query_last_k_rows": ("n_decode_edits",),
}


def resolve_scoped_query_rows(mode: str, is_decode: bool,
                              query_span: Optional[frozenset],
                              demo_span: Optional[frozenset],
                              surface_span: Optional[frozenset] = None):
    """Which ABSOLUTE query positions `mode` may edit on THIS forward pass.

    Returns None for "every row of this chunk" (no per-row filter), otherwise a set of
    absolute positions — possibly EMPTY, which means "edit nothing on this forward".
    None and empty are deliberately different: None is the legacy all-rows behaviour, empty
    is a scoped mode that is switched off for this half of the computation.

    Split out as a module-level function so the tests can mutate/probe the span algebra
    directly instead of restating it, and so the hook and any consumer share one definition.
    """
    if mode == "legacy_all_query":
        return None
    if mode == "decode_only":
        return None if is_decode else frozenset()
    if mode == "response_query_only":
        return None if is_decode else (query_span or frozenset())
    if mode == "query_prefill_only":
        return frozenset() if is_decode else (query_span or frozenset())
    if mode == "demo_processing_only":
        return frozenset() if is_decode else (demo_span or frozenset())
    if mode == "prompt_last_row_only":
        # Prefill only, and only the LAST row of the query span. Derived from `query_span` rather
        # than taken as its own argument, so it cannot drift from the span the consumer resolved.
        if is_decode:
            return frozenset()
        return frozenset({max(query_span)}) if query_span else frozenset()
    if mode == "query_last_k_rows":
        # Prefill only; the row set is supplied verbatim by the consumer via `surface_span`, which
        # is the same channel `target_surface_row_only` uses. The consumer, not this resolver, owns
        # the definition of "last K" so that K appears in exactly one place.
        return frozenset() if is_decode else (surface_span or frozenset())
    if mode == "target_surface_row_only":
        # Prefill only, and only the ONE occurrence's rows. `surface_span` is deliberately a
        # separate argument rather than a narrowed `query_span`: the query span is still needed
        # by the twin-check in the consumer, and overloading one argument with two meanings is how
        # a scope silently becomes a different intervention than the one being reported.
        return frozenset() if is_decode else (surface_span or frozenset())
    raise ValueError(f"unknown scoped knockout mode {mode!r}; known: {SCOPED_KNOCKOUT_MODES}")


#: DCS-C-134 (ADDITIVE, 2026-09-09). The counters of `ScopedAttentionKnockout` that DESCRIBE A
#: WRITE, as opposed to the ones that describe the code path having run. A knockout wrapped in a
#: `DisabledHookBridge` runs its `_pre` in full and its mask edit is thrown away, so EVERY counter
#: in this tuple must be exactly 0 on such a record and its `_would_have` twin carries the number.
#:
#: WHY THIS EXISTS. Until 2026-09-09 `_pre` wrote these counters unconditionally, including under
#: the bridge -- and `n_cells_edited_realised` is READ BACK OUT OF THE CLONE the hook edits, a
#: clone the bridge then discards. The bridged arm therefore persisted a per-row record that was
#: NUMERICALLY IDENTICAL to a live knockout's (PHASE 11 job 870913: hook_fired_count=8280,
#: n_cells_edited_realised=13061664 -- the same 13,061,664 the live arm reported on the same 230
#: rows) while the model's attention mask was never touched. The mask discard was correct; the
#: BOOKKEEPING was the defect, and only a downstream analyzer gate caught it.
KNOCKOUT_WRITE_COUNTERS: tuple = (
    "n_edits", "n_prefill_edits", "n_decode_edits", "n_query_rows_edited", "n_keys_masked",
    "n_cells_edited_realised", "hook_fired_count",
)

#: The `_would_have` twin of every write counter. Seeded by `DisabledHookBridge.__init__` -- i.e.
#: on a BRIDGED record only, and strictly before the first forward -- for the reason the D-4 block
#: below gives: a record that GROWS keys cannot tell "this hook never fired" from "this consumer
#: read a key the producer never wrote". They are deliberately NOT seeded on a live arm's record:
#: see the note in `ScopedAttentionKnockout.__init__`.
KNOCKOUT_WOULD_HAVE_COUNTERS: tuple = tuple(k + "_would_have" for k in KNOCKOUT_WRITE_COUNTERS)


def bridged_scoped_liveness_violations(mode: str, stats: Dict[str, Any]) -> List[str]:
    """[] iff `stats` is the record of a knockout that RAN IN FULL and WROTE NOTHING.

    The bridged contract is not the live one with a relaxation; it is the live one with its two
    halves separated. A live arm proves itself by writing. A BRIDGE has to prove two opposite
    things at once and BOTH are required here:

      * it RESOLVED destinations -- the mode's required counters are > 0 in their `_would_have`
        twins, so a bridge over a knockout that cut nothing is refused rather than passing as a
        perfect identity (that is a false negative wearing a null's name);
      * it WROTE NOTHING -- every counter in `KNOCKOUT_WRITE_COUNTERS` is exactly 0, so a
        bridge that quietly ran live can no longer produce a record indistinguishable from the
        live arm's. THE PRODUCER CONVICTS ITSELF; before this, only the analyzer's downstream
        cell-count gate could.

    `n_forward` and the two forward counters are NOT write counters and stay live: the hook did
    run those forwards, and that is precisely what the bridge exists to demonstrate.
    """
    if mode not in LIVENESS_REQUIREMENT:
        raise ValueError(f"unknown scoped knockout mode {mode!r}; known: {SCOPED_KNOCKOUT_MODES}")
    bad: List[str] = []
    if int(stats.get("n_forward", 0)) <= 0:
        bad.append("bridged_knockout_never_ran:n_forward==0 -- the wrapped hook was registered "
                   "and never called, so this bridge exercised nothing")
    for key in LIVENESS_REQUIREMENT[mode]:
        _tw = key + "_would_have"
        if _tw not in stats:
            bad.append(f"{_tw}_NOT_RECORDED (the bridged producer wrote no would-have twin for "
                       f"{key}, so 'the inner hook was alive' cannot be evaluated at all)")
        elif int(stats.get(_tw, 0)) <= 0:
            bad.append(f"{_tw}==0 (mode {mode} requires it > 0: a bridge over a knockout that "
                       f"resolved nothing certifies nothing)")
    for key in LIVENESS_MUST_BE_ZERO[mode]:
        _tw = key + "_would_have"
        if int(stats.get(_tw, 0)) != 0:
            bad.append(f"{_tw}=={int(stats.get(_tw, 0))} (mode {mode} requires it == 0; the "
                       f"scoping leaked in the bridged run exactly as it would have live)")
    for key in KNOCKOUT_WRITE_COUNTERS:
        _v = int(stats.get(key, 0))
        if _v != 0:
            bad.append(f"bridged_knockout_reports_a_REALISED_{key}=={_v}: the write was supposed "
                       f"to be DISCARDED, so a non-zero realised counter on a bridged record is "
                       f"either a live arm wearing the null's name or a producer counting a "
                       f"write it threw away. Both are refusals.")
    return bad


def scoped_liveness_violations(mode: str, stats: Dict[str, Any]) -> List[str]:
    """[] iff `stats` satisfies this mode's proof-of-life contract. The gate, in one place.

    Callers do `if scoped_liveness_violations(mode, stats): refuse to report`. Do NOT restate
    the ">0 / ==0" rules at the call site: two modes make zero decode edits by design and a
    hand-written gate has already been the failure mode this whole class exists to avoid.

    DCS-C-134 (ADDITIVE). A record that `DisabledHookBridge` has stamped `bridged_and_discarded`
    is judged by `bridged_scoped_liveness_violations` instead. The branch is reached ONLY on a
    stats dict carrying that key, which nothing but the bridge writes, so every live arm --
    every PHASE 9 and PHASE 10 arm included -- takes the identical path it always did.
    """
    if mode not in LIVENESS_REQUIREMENT:
        raise ValueError(f"unknown scoped knockout mode {mode!r}; known: {SCOPED_KNOCKOUT_MODES}")
    if stats.get("bridged_and_discarded"):
        return bridged_scoped_liveness_violations(mode, stats)
    bad: List[str] = []
    for key in LIVENESS_REQUIREMENT[mode]:
        if int(stats.get(key, 0)) <= 0:
            bad.append(f"{key}==0 (mode {mode} requires it > 0)")
    for key in LIVENESS_MUST_BE_ZERO[mode]:
        if int(stats.get(key, 0)) != 0:
            bad.append(f"{key}=={int(stats.get(key, 0))} (mode {mode} requires it == 0)")
    return bad


class ScopedAttentionKnockout:
    """`AllQueryAttentionKnockout` restricted to a chosen set of QUERY ROWS (see the modes above).

    Keys are addressed exactly as in `AllQueryAttentionKnockout`: `blocked_keys` are ABSOLUTE
    token positions and KV-cache columns are absolute, so `kp` indexes `am[..., kp]` at every
    step. Query row `r` of the current chunk is absolute position `past + r` with
    `past = am.shape[3] - am.shape[2]`, and the first causally-blockable row is
    `lo = max(0, kp - past)`. The ONLY thing this class adds is a per-row filter applied on top
    of `lo`, expressed in ABSOLUTE positions — mixing that filter up with the cache-local row
    index `r` is this repo's documented absolute-position-index bug class and is tested for.

    `query_span` / `demo_span` are ABSOLUTE token positions, supplied the way score_behavior
    already computes them: `query_span` is `query_span_positions(...)` (the harmful request plus
    the generation header — already a set there), `demo_span` is `demo_key_positions(...)[0]`
    (the demonstration block — the same list that becomes `blocked_keys` for the demo_all arm,
    passed separately because a CONTROL arm's keys are not the demo block).

    A mode that needs a span and is not given one RAISES: an empty span would silently degrade
    to a no-op knockout that scores as a clean null, which is the exact failure this file's
    other two classes are written to prevent.
    """

    def __init__(self, model, layer_idxs, blocked_keys, mode: str = "legacy_all_query",
                 query_span=None, demo_span=None, heads=None, stats=None, surface_span=None):
        if mode not in SCOPED_KNOCKOUT_MODES:
            raise ValueError(f"unknown scoped knockout mode {mode!r}; "
                             f"known: {SCOPED_KNOCKOUT_MODES}")
        self.mode = mode
        self.layers = [dc._get_layers(model)[i] for i in layer_idxs]
        self.k = sorted(set(int(x) for x in blocked_keys))
        self.query_span = None if query_span is None else frozenset(int(x) for x in query_span)
        self.demo_span = None if demo_span is None else frozenset(int(x) for x in demo_span)
        self.surface_span = (None if surface_span is None
                             else frozenset(int(x) for x in surface_span))
        if mode in ("query_prefill_only", "response_query_only") and not self.query_span:
            raise ValueError(f"mode {mode!r} needs a non-empty query_span (absolute positions of "
                             f"the final-query span); an empty one is a no-op knockout")
        if mode == "demo_processing_only" and not self.demo_span:
            raise ValueError(f"mode {mode!r} needs a non-empty demo_span (absolute positions of "
                             f"the demonstration block); an empty one is a no-op knockout")
        if mode == "query_last_k_rows" and not self.surface_span:
            raise ValueError(f"mode {mode!r} needs a non-empty surface_span (the last K query rows); "
                             f"an empty one is a no-op knockout that would score as a clean null")
        if mode == "target_surface_row_only" and not self.surface_span:
            raise ValueError(f"mode {mode!r} needs a non-empty surface_span (absolute positions of "
                             f"the FINAL target_surface occurrence in the query); an empty one is a "
                             f"no-op knockout that would score as a clean null")
        # SURGICAL SCOPES MUST NOT SILENTLY WIDEN. This scope's whole claim is that it edits ONE
        # occurrence's rows, so a span that has leaked outside the query span is a different
        # experiment wearing this one's name. Checked here, at construction, because by the time
        # the counters are read the forward pass has already happened.
        if (mode == "target_surface_row_only" and self.query_span
                and not self.surface_span <= self.query_span):
            raise ValueError(
                f"mode {mode!r}: surface_span is not contained in query_span "
                f"(surface={sorted(self.surface_span)[:8]}..., "
                f"query bounds=[{min(self.query_span)},{max(self.query_span)}]). The final "
                f"target-surface occurrence must lie inside the query, or the positions were "
                f"resolved against a different tokenization than the one being run.")
        self.heads = None if heads is None else list(heads)
        self.n_heads = int(model.config.num_attention_heads)
        self._handles = []
        self.stats = stats if stats is not None else {}
        for key in ("n_forward", "n_decode_forward", "n_prefill_forward",
                    "n_edits", "n_decode_edits", "n_prefill_edits",
                    "n_query_rows_edited", "n_keys_masked"):
            self.stats.setdefault(key, 0)
        # DCS-PR-059 D-4 (ADDITIVE). The three counters the PR-057 project-out schema carries and
        # this class never wrote. They are seeded HERE, at construction, for the same reason
        # `hook_stats_dict` seeds every key at once: a record that GROWS keys as the hook runs
        # cannot distinguish "this hook never fired" from "this consumer read a key the producer
        # never wrote". Nothing that existed before this line reads them.
        for key in ("hook_fired_count", "n_forward_with_destinations",
                    "n_cells_edited_expected", "n_cells_edited_realised"):
            self.stats.setdefault(key, 0)
        # DCS-C-134 (ADDITIVE, 2026-09-09). THE BRIDGE SWITCH and the `_would_have` twins.
        #
        # `bridged_discard` is set to True by `DisabledHookBridge` when it wraps this object. It
        # changes NOTHING about what `_pre` computes -- the clone, the head expansion, the row
        # resolution, the min_val writes and the read-back all still happen, which is the whole
        # point of the bridge -- it changes only WHERE the WRITE-DESCRIBING counters land. Under
        # the bridge the mask edit is thrown away, so `n_cells_edited_realised` and its six
        # siblings describe a write into a discarded clone, and reporting them in the live fields
        # made a bridged row byte-for-byte indistinguishable from a live knockout's row.
        #
        # THE TWINS ARE SEEDED BY THE BRIDGE, NOT HERE, and that is deliberate on both counts.
        # They must exist before the first forward -- "not measured" and "measured and zero" are
        # opposite verdicts (the D-4 rule above) -- and `DisabledHookBridge.__init__` seeds all
        # seven the moment it wraps this object, which is strictly before `__enter__`. Seeding
        # them here instead would add seven keys to the stats dict of EVERY live knockout,
        # including the `legacy_all_query` arm whose stats-key set is pinned byte-for-byte
        # against `AllQueryAttentionKnockout` (doublespeak_causality/tests/
        # test_scoped_attnknockout.py::test_legacy_mode_is_byte_identical_to_...). An artifact
        # schema that grows keys nobody decided to add is the drift that test exists to stop, and
        # a bridged-arm repair has no business changing what a live arm records.
        self.bridged_discard = False
        # RESOLVED SPANS GO IN THE ARTIFACT, not only in a log line: a null is uninterpretable
        # without knowing which rows the mode actually had to work with.
        self.stats["mode"] = mode
        self.stats["n_blocked_keys"] = len(self.k)
        self.stats["n_query_span_positions"] = (0 if self.query_span is None
                                                else len(self.query_span))
        self.stats["n_demo_span_positions"] = (0 if self.demo_span is None
                                               else len(self.demo_span))
        self.stats["n_surface_span_positions"] = (0 if self.surface_span is None
                                                  else len(self.surface_span))
        self.stats["query_span_bounds"] = (None if not self.query_span
                                           else [min(self.query_span), max(self.query_span)])
        self.stats["demo_span_bounds"] = (None if not self.demo_span
                                          else [min(self.demo_span), max(self.demo_span)])
        # The surgical scope's positions go in the artifact IN FULL, not as bounds: a two-token
        # span is small enough to record exactly, and "which rows did you actually cut" is the
        # first question anyone will ask of a null at this scope.
        self.stats["surface_span_positions"] = (None if not self.surface_span
                                                else sorted(self.surface_span))
        self.stats["liveness_required"] = list(LIVENESS_REQUIREMENT[mode])
        self.stats["liveness_must_be_zero"] = list(LIVENESS_MUST_BE_ZERO[mode])

    def _pre(self, mod, args, kwargs):
        am = kwargs.get("attention_mask")
        if am is None or am.dim() != 4:
            raise RuntimeError("expected a 4-D additive attention mask; is the model loaded with "
                               "attn_implementation='eager'? Under SDPA/flash the mask edit is "
                               "discarded and the knockout is a silent no-op.")
        if am.shape[0] != 1:
            raise NotImplementedError("ScopedAttentionKnockout supports batch size 1 only")
        am = am.clone()
        if self.heads is not None and am.shape[1] == 1:
            am = am.expand(-1, self.n_heads, -1, -1).clone()
        min_val = torch.finfo(am.dtype).min
        hs = range(am.shape[1]) if self.heads is None else self.heads
        n_heads_edited = am.shape[1] if self.heads is None else len(self.heads)
        n_q, kv_len = am.shape[2], am.shape[3]
        past = kv_len - n_q                     # absolute position of query row 0
        is_decode = (n_q == 1)
        allowed = resolve_scoped_query_rows(self.mode, is_decode, self.query_span, self.demo_span,
                                            self.surface_span)
        n_edits = 0
        n_keys_masked = 0
        rows_touched = set()
        # DCS-PR-059 D-4 (ADDITIVE). `expected` is counted from the rows this forward RESOLVED,
        # BEFORE the mask is written. `realised` is READ BACK OUT of the mask that was actually
        # written, at exactly the coordinates the write targeted. They are measured on OPPOSITE
        # SIDES of the write on purpose: counting both from the same source would make
        # "realised == expected" a tautology, and `0 == 0` on a dead hook is precisely the
        # clean-looking null this file exists to make impossible. realised <= expected always, and
        # a write that did not land shows up as a strict inequality rather than as silence.
        n_cells_expected = 0
        n_cells_realised = 0
        _hsel = (None if self.heads is None
                 else torch.tensor(list(self.heads), device=am.device, dtype=torch.long))

        def _readback(_kp, rowsel):
            sub = am[0] if _hsel is None else am[0].index_select(0, _hsel)
            return int((sub[:, rowsel, _kp] == min_val).sum().item())

        if allowed is None or allowed:          # an empty set means: edit nothing this forward
            for kp in self.k:
                if kp >= kv_len:
                    continue                    # key not in the cache yet
                lo = max(0, kp - past)          # first query row that may causally see kp
                if lo >= n_q:
                    continue
                if allowed is None:
                    # LEGACY PATH, kept as a contiguous slice so the produced mask (and n_edits)
                    # are identical to AllQueryAttentionKnockout's.
                    n_rows = n_q - lo
                    n_cells_expected += n_rows * n_heads_edited          # BEFORE the write
                    for h in hs:
                        am[0, h, lo:, kp] = min_val
                    n_cells_realised += _readback(kp, slice(lo, n_q))    # FROM what was written
                    rows_touched.update(range(lo, n_q))
                else:
                    rows = [r for r in range(lo, n_q) if (past + r) in allowed]
                    if not rows:
                        continue
                    ridx = torch.tensor(rows, device=am.device, dtype=torch.long)
                    n_rows = len(rows)
                    n_cells_expected += n_rows * n_heads_edited          # BEFORE the write
                    for h in hs:
                        am[0, h, ridx, kp] = min_val
                    n_cells_realised += _readback(kp, ridx)              # FROM what was written
                    rows_touched.update(rows)
                n_edits += n_rows * n_heads_edited
                n_keys_masked += 1
        kwargs["attention_mask"] = am
        # ---- DCS-C-134 (ADDITIVE): WHICH FIELD EACH COUNTER LANDS IN ------------------------
        # `_sfx` is "" for a live arm -- byte-identical to every run before 2026-09-09 -- and
        # "_would_have" when this hook is wrapped in a `DisabledHookBridge`, whose shim hands the
        # ORIGINAL (args, kwargs) back to the model and throws `am` away. Under the bridge the
        # numbers below are a description of a write into a discarded clone, and a record that
        # files them as realised is a control reporting itself as the thing it controls for.
        #
        # The forward counters and `n_cells_edited_expected` are NOT suffixed: the forwards
        # really happened and the destinations were really resolved. Only the WRITE moves.
        _sfx = "_would_have" if getattr(self, "bridged_discard", False) else ""
        self.stats["n_cells_edited_expected"] += n_cells_expected
        self.stats["n_cells_edited_realised" + _sfx] += n_cells_realised
        self.stats["n_forward_with_destinations"] += int(n_cells_expected > 0)
        # A forward that resolved destinations and wrote them is a forward on which the hook
        # FIRED. Zero over a whole row is "the hook never fired" and is VOID, not a null.
        self.stats["hook_fired_count" + _sfx] += int(n_cells_realised > 0)
        self.stats["n_forward"] += 1
        self.stats["n_decode_forward"] += int(is_decode)
        self.stats["n_prefill_forward"] += int(not is_decode)
        self.stats["n_edits" + _sfx] += n_edits
        self.stats["n_decode_edits" + _sfx] += n_edits if is_decode else 0
        self.stats["n_prefill_edits" + _sfx] += 0 if is_decode else n_edits
        self.stats["n_query_rows_edited" + _sfx] += len(rows_touched)
        self.stats["n_keys_masked" + _sfx] += n_keys_masked
        return args, kwargs

    def liveness_violations(self) -> List[str]:
        """[] iff this hook's own stats satisfy its mode's contract (same table as the gate)."""
        return scoped_liveness_violations(self.mode, self.stats)

    def __enter__(self):
        for layer in self.layers:
            self._handles.append(
                layer.self_attn.register_forward_pre_hook(self._pre, with_kwargs=True))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


# --------------------------------------------------------------------------- #
# Per-head z capture / patch (NEXT5 W4 tier-B — attention-head circuit)
# --------------------------------------------------------------------------- #
# The attention OUTPUT before o_proj is the concatenation of per-QUERY-head outputs z:
# o_proj input has shape [batch, seq, n_heads * head_dim]. (GQA shrinks the K/V heads, NOT
# this tensor — it is over num_attention_heads.) These hook o_proj to capture z (for AtP) or
# replace a single head's z at chosen positions (for true head-output patching / validation).
# Nothing else in the stack touches the head axis for OUTPUT/patching (AttentionKnockout only
# masks attention weights); this is the single new primitive tier-B needs.
def _attn_head_dims(model):
    cfg = model.config
    n_heads = int(cfg.num_attention_heads)
    hidden = int(getattr(cfg, "hidden_size", None) or cfg.n_embd)
    head_dim = int(getattr(cfg, "head_dim", 0) or (hidden // n_heads))
    return n_heads, head_dim


class ZHeadPatch:
    """Replace the per-head attention output z[head] at `positions` with `corrupt_vec`.

    Registers a forward_pre_hook on `layers[layer_idx].self_attn.o_proj` that reshapes the
    o_proj INPUT to [batch, seq, n_heads, head_dim], overwrites head `head` at each position
    in `positions`, and flattens back. Generation-safe: a decode step (seq==1) whose position
    index is out of range is skipped, mirroring ds_common.LayerPatch. `corrupt_vec` is a
    [head_dim] tensor (the corrupt counterpart of this head's z at that position).
    """

    def __init__(self, model, layer_idx: int, head: int, positions: Sequence[int],
                 corrupt_vec: torch.Tensor):
        self.o_proj = dc._get_layers(model)[layer_idx].self_attn.o_proj
        self.n_heads, self.head_dim = _attn_head_dims(model)
        if not (0 <= head < self.n_heads):
            raise IndexError(f"head {head} out of range for {self.n_heads} heads")
        self.head = head
        self.positions = list(positions)
        self.vec = corrupt_vec.detach().float()
        self._handle = None

    def _pre(self, module, args):
        z = args[0]
        b, seq, hh = z.shape
        if b != 1:                    # edits row 0 only; fail loud on batch>1 (audit finding 5)
            raise NotImplementedError("ZHeadPatch supports batch size 1 only")
        zr = z.view(b, seq, self.n_heads, self.head_dim).clone()
        v = self.vec.to(device=z.device, dtype=z.dtype)
        for p in self.positions:
            if 0 <= p < seq:                       # skip out-of-range (decode-step safe)
                zr[0, p, self.head, :] = v
        return (zr.view(b, seq, hh),) + tuple(args[1:])

    def __enter__(self):
        self._handle = self.o_proj.register_forward_pre_hook(self._pre)
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None
        return False


class AllPositionZHeadAblate:
    """Ablate a set of attention heads' output z at EVERY position, on EVERY forward (prefill AND
    each KV-cached decode step) — the generation-time, all-position analogue of ZHeadPatch. Used
    for behavioral necessity: does removing the carry heads' contribution throughout generation
    reduce harmful behavior? `heads_by_layer` = {layer_idx: [head, ...]}; mode "zero" sets those
    head slices to 0, "mean" sets them to their per-head mean over the current positions. NOTE (audit): mean over
    the seq axis is an identity no-op on KV-cached decode steps (seq==1) — mean mode is PREFILL-ONLY;
    use mode="zero" (decode-safe) for any generation-time necessity test.

    Registers a forward_pre_hook on each layer's o_proj (the head-concat = o_proj input). Unlike
    ZHeadPatch (fixed prompt positions), this edits ALL rows of the current forward, so ablation
    persists through generated tokens.
    """

    def __init__(self, model, heads_by_layer: Dict[int, Sequence[int]], mode: str = "zero"):
        self.layers = dc._get_layers(model)
        self.n_heads, self.head_dim = _attn_head_dims(model)
        self.heads_by_layer = {int(l): list(hs) for l, hs in heads_by_layer.items()}
        self.mode = mode
        self._handles: List[Any] = []

    def _pre(self, heads):
        def f(module, args):
            z = args[0]
            b, seq, hh = z.shape
            zr = z.view(b, seq, self.n_heads, self.head_dim).clone()
            for h in heads:
                if self.mode == "zero":
                    zr[:, :, h, :] = 0.0
                elif self.mode == "mean":
                    zr[:, :, h, :] = zr[:, :, h, :].mean(dim=1, keepdim=True)
                else:
                    raise ValueError(f"unknown mode {self.mode}")
            return (zr.view(b, seq, hh),) + tuple(args[1:])
        return f

    def __enter__(self):
        for li, hs in self.heads_by_layer.items():
            self._handles.append(self.layers[li].self_attn.o_proj.register_forward_pre_hook(self._pre(hs)))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


class ZHeadCapture:
    """Capture the per-head attention output z (o_proj input) at target layers, retaining its
    grad — the per-head analogue of 48's _ActGradCapture (which captures the residual). After a
    backward, `grads[L]` / `acts[L]` are [seq, n_heads*head_dim]; reshape to [seq, n_heads,
    head_dim] for a per-(layer, head, pos) AtP: g_z . (z_corrupt - z_clean)."""

    def __init__(self, model, layer_idxs: Sequence[int]):
        self.o_projs = {li: dc._get_layers(model)[li].self_attn.o_proj for li in layer_idxs}
        self.n_heads, self.head_dim = _attn_head_dims(model)
        self.acts: Dict[int, torch.Tensor] = {}
        self._handles: List[Any] = []

    def _pre(self, li):
        def f(module, args):
            z = args[0]
            if z.requires_grad:
                z.retain_grad()
            self.acts[li] = z                       # keep graph node (do NOT detach/clone)
            return None
        return f

    def __enter__(self):
        for li, op in self.o_projs.items():
            self._handles.append(op.register_forward_pre_hook(self._pre(li)))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


# --------------------------------------------------------------------------- #
# HOOK LIVENESS INSTRUMENTATION (DCS-PR-057 / blocker Q12, C-13)
#
# WHY THIS BLOCK EXISTS. `make_project_out_hook`, `AllPositionProjectOut` and
# `SinglePositionProjectOut` wrote NO statistics of any kind. A hook on the wrong layer
# object, a hook holding a zero direction, a hook whose handle was removed before the
# forward, and a hook that only ever sees KV-cached decode steps all produce EXACTLY the
# artifact that a live intervention with no effect produces. A DEAD HOOK SCORES AS A CLEAN
# NULL, and there was nothing in this file that could tell the two apart.
#
# Everything here is ADDITIVE and DEFAULT-OFF: `stats=None` (the default) leaves the hook
# body byte-identical to what every committed artifact was produced with. Pass a dict from
# `hook_stats_dict()` and the hook records, per (layer, position-set):
#
#   fired count, forward calls (prefill/decode split), destination rows, cells edited,
#   pre/post activation norm, norm ratio, projection magnitude removed, cosine before/after,
#   max |delta|, layer, rel_end / resolved absolute token index, occurrence index.
#
# `project_out_liveness_violations()` turns those into refusals, and it refuses the DISABLED
# case separately: a bridge (`DisabledHookBridge`) that never ran, or that wrapped a hook
# which would not have changed anything anyway, bridges nothing and is REFUSED rather than
# tolerated.
# --------------------------------------------------------------------------- #
#: Keys every instrumented residual-stream edit hook writes. Named here so a consumer can
#: refuse a stats dict that is missing one rather than reading `None` as "no effect".
HOOK_STATS_KEYS = (
    "mode", "enabled", "layer", "alpha", "direction_norm",
    "n_forward_calls", "n_prefill_forward", "n_decode_forward",
    "n_forward_with_destinations",
    "hook_fired_count", "n_destination_rows",
    "n_cells_edited_realised", "n_cells_edited_expected",
    "activation_norm_pre", "activation_norm_post", "norm_ratio",
    "projection_removed_l2", "sum_projection_removed_l2", "min_projection_removed_l2",
    "orthogonal_residual_delta_l2",
    "cos_pre_post", "max_abs_delta",
    "positions", "rel_end", "occurrence_index", "resolved_absolute_index",
    "seq_len_last", "seq_len_at_resolution",
    "would_have_changed_max_abs", "would_have_changed_l2", "bridged_and_discarded",
    # ---- the ADDITIVE arm's DOSE (control C4, 2026-09-07). Present on every record and
    # gated only for `add*` modes, the same way the `would_have_changed_*` pair is present
    # everywhere and gated only for a bridge.
    "alpha_gap_units", "gap_norm", "dose_units", "realised_dose_l2_per_cell",
)
# ONE SCHEMA, AND THE PRODUCER OWNS THE MEASUREMENTS (C-117 / review F2, 2026-09-07).
#
# `scripts/dcs_ts_pr057_causal.py` carries a second liveness schema (`LivenessStats`) whose
# `liveness_gate()` / `orthogonal_residual_gate()` read `n_cells_edited_expected` and
# `orthogonal_residual_delta_l2` -- two fields THIS file never wrote. Both consumers read them
# with a defaulting `.get`, so a MISSING field became a measured `0` / `NaN` and every healthy
# arm gated VOID with a substantive scientific verdict ("the orthogonal component was NOT
# preserved") whose real content was "nobody measured it". The two schemas are reconciled here
# rather than in the gate, and the split of ownership is deliberate:
#
#   n_cells_edited_expected      -> PRODUCER. Only the hook sees the tensor it was HANDED, so
#                                   only the hook can say how many cells it was supposed to
#                                   edit. It is counted at the TOP of the forward, from the
#                                   input shape and the declared scope, BEFORE the write;
#                                   `n_cells_edited_realised` is counted from the slice actually
#                                   written. `realised == expected` is then a real bind instead
#                                   of the vacuous `0 == 0` the consumer was getting.
#   orthogonal_residual_delta_l2 -> PRODUCER. Only the hook holds `h_pre`, `h_post` and `d`.
#                                   For `project_out` the edit is `alpha*(h.d)d`, i.e. exactly
#                                   along `d`, so the component of the change ORTHOGONAL to `d`
#                                   must be 0 to float error; measuring it costs one projection
#                                   and turns I-N7 from an assertion into a number.
#   n_forward_with_destinations  -> PRODUCER. Review F6: the gated scalars are overwritten every
#                                   forward, so they certify the LAST decode step, not the run.
#                                   This counts the forwards that HAD cells to edit; a hook that
#                                   fired on some of them and not others is then caught by an
#                                   exact identity, with no numeric threshold.
#   min_projection_removed_l2    -> PRODUCER, same reason: the minimum over forwards, so a
#                                   forward that was handed cells and removed exactly nothing
#                                   cannot hide behind a healthy last forward.
#   seq_len_at_resolution        -> PRODUCER, supplied by the caller (review F3). See
#                                   `SinglePositionProjectOut.__init__`.
#   alpha_gap_units / gap_norm   -> PRODUCER, DECLARED BY THE CALLER, and the identity between
#   dose_units                      them and the absolute `alpha` the hook was actually handed
#   realised_dose_l2_per_cell       is CHECKED (control C4, 2026-09-07). `make_add_hook`
#                                   normalises its direction, so `alpha` is an ABSOLUTE
#                                   residual-space magnitude, while every non-`refusalness`
#                                   caller doses in GAP UNITS and must pass `alpha * gap`. A
#                                   bare `alpha` at that call site injects an absolute magnitude
#                                   under a gap-unit label -- the RETRACTION F-3 arithmetic, a
#                                   14.65x overdose from an identical-looking flag, which this
#                                   repository has hit at this second call site twice. The
#                                   caller therefore declares BOTH the gap-unit alpha and the
#                                   gap, the hook asserts `alpha == alpha_gap_units * gap_norm`
#                                   at construction, and `realised_dose_l2_per_cell` -- the L2
#                                   of the change actually written to a cell -- is MEASURED and
#                                   compared with `alpha`, so the record alone can convict a
#                                   hook whose body disagrees with its own manifest.
#
# `hook_stats_dict` initialises the two MEASURED floats to None, not to 0.0. A missing or
# unmeasured quantity must never be indistinguishable from a measured zero -- that is the same
# defect one level down, and it is what `project_out_liveness_violations` and the analyzer's
# gates now refuse on separately from a genuine zero.


def _resolve_layer(model, layer_idx: int):
    """The decoder layer to hook.

    A real model resolves through the house helper `ds_common._get_layers`, unchanged. Anything
    `_get_layers` cannot resolve but which IS itself hookable is treated AS the layer -- which is
    what lets the hooks in this file be unit-tested on CPU against the REAL hook functions
    instead of against a re-implementation of them. Testing a copy of a hook proves nothing
    about the hook, and C-13 is a defect that lived precisely in the gap between the two.

    The order matters and is not cosmetic: an HF model is itself an nn.Module and therefore has
    `register_forward_hook`, so a `hasattr` check FIRST would hook the whole model instead of
    block L and edit the final hidden state -- a different intervention, silently, on the real
    path.
    """
    try:
        layers = dc._get_layers(model)
    except Exception:
        layers = None
    if layers is not None:
        return layers[layer_idx]
    if hasattr(model, "register_forward_hook"):
        return model
    raise TypeError(f"cannot resolve a decoder layer from {type(model).__name__}")


def hook_stats_dict(mode: str = "", layer: int = -1, enabled: bool = True,
                    rel_end: Optional[int] = None,
                    occurrence_index: Optional[int] = None,
                    seq_len_at_resolution: Optional[int] = None) -> Dict[str, Any]:
    """A fresh, fully-populated liveness record. Every key exists from the start.

    A record that GROWS keys as the hook runs cannot distinguish "this hook never fired" from
    "this consumer read a key the producer never wrote" -- that is the shape of the check that
    reads the producer's own null field and asserts None == None.
    """
    return {
        "mode": str(mode), "enabled": bool(enabled), "layer": int(layer),
        "alpha": None, "direction_norm": None,
        "n_forward_calls": 0, "n_prefill_forward": 0, "n_decode_forward": 0,
        "n_forward_with_destinations": 0,
        "hook_fired_count": 0, "n_destination_rows": 0,
        "n_cells_edited_realised": 0, "n_cells_edited_expected": 0,
        "activation_norm_pre": None, "activation_norm_post": None, "norm_ratio": None,
        "projection_removed_l2": 0.0, "sum_projection_removed_l2": 0.0,
        # None, NOT 0.0: "never measured" and "measured and it was zero" are opposite verdicts
        # for both of these, and the consumer is entitled to tell them apart.
        "min_projection_removed_l2": None, "orthogonal_residual_delta_l2": None,
        "cos_pre_post": None, "max_abs_delta": 0.0,
        "positions": None, "rel_end": (None if rel_end is None else int(rel_end)),
        "occurrence_index": (None if occurrence_index is None else int(occurrence_index)),
        "resolved_absolute_index": None,
        "seq_len_last": None,
        "seq_len_at_resolution": (None if seq_len_at_resolution is None
                                  else int(seq_len_at_resolution)),
        "would_have_changed_max_abs": 0.0, "would_have_changed_l2": 0.0,
        "bridged_and_discarded": False,
        # None, NOT 0.0 / "" (C4): an undeclared dose and a declared dose of zero are opposite
        # verdicts, and `realised_dose_l2_per_cell == 0.0` IS the dead-additive-hook signature.
        "alpha_gap_units": None, "gap_norm": None, "dose_units": None,
        "realised_dose_l2_per_cell": None,
    }


def _record_edit(stats: Dict[str, Any], pre: torch.Tensor, post: torch.Tensor,
                 removed: torch.Tensor, n_dest: int, seq_len: int,
                 abs_index: Optional[Sequence[int]] = None,
                 direction: Optional[torch.Tensor] = None) -> None:
    """Fold one forward's edit into `stats`. `pre`/`post`/`removed` are [n_cells, hidden].

    `direction` is the (already normalised) axis the edit is supposed to lie along. Given it,
    the ORTHOGONAL residual of the change is measured -- `||(I - dd^T)(h_pre - h_post)||`, which
    for `project_out` must be zero to float error because the edit IS `alpha*(h.d)d`. Passing it
    is what turns `orthogonal_residual_delta_l2` from a field the analyzer invented into a
    number this file produced (C-117).
    """
    pre_f = pre.detach().float().reshape(-1, pre.shape[-1])
    post_f = post.detach().float().reshape(-1, post.shape[-1])
    rem_f = removed.detach().float().reshape(-1, removed.shape[-1])
    npre, npost, nrem = float(pre_f.norm()), float(post_f.norm()), float(rem_f.norm())
    stats["hook_fired_count"] += 1
    stats["n_cells_edited_realised"] += int(pre_f.shape[0])
    stats["n_destination_rows"] += int(n_dest)
    stats["activation_norm_pre"] = npre
    stats["activation_norm_post"] = npost
    stats["norm_ratio"] = (npost / npre) if npre else None
    stats["projection_removed_l2"] = nrem
    stats["sum_projection_removed_l2"] = float(stats["sum_projection_removed_l2"]) + nrem
    stats["cos_pre_post"] = (float((pre_f * post_f).sum() / (npre * npost))
                             if npre > 0 and npost > 0 else None)
    stats["max_abs_delta"] = max(float(stats["max_abs_delta"]),
                                 float((pre_f - post_f).abs().max()))
    # MINIMUM over forwards, not the last one (review F6). `projection_removed_l2` above is
    # overwritten every call, so on its own it certifies the final decode step and a hook that
    # was dead on some other forward passes.
    _prev_min = stats.get("min_projection_removed_l2")
    stats["min_projection_removed_l2"] = (nrem if _prev_min is None
                                          else min(float(_prev_min), nrem))
    if direction is not None:
        d_f = direction.detach().float().reshape(-1)
        _dn = float(d_f.norm())
        if _dn > 0.0:
            d_f = d_f / _dn
            delta = pre_f - post_f
            along = (delta @ d_f.reshape(-1, 1)) * d_f.reshape(1, -1)
            _orth = float((delta - along).norm())
            _prev = stats.get("orthogonal_residual_delta_l2")
            stats["orthogonal_residual_delta_l2"] = (_orth if _prev is None
                                                     else max(float(_prev), _orth))
    stats["seq_len_last"] = int(seq_len)
    if abs_index is not None:
        stats["resolved_absolute_index"] = [int(i) for i in abs_index]


def project_out_liveness_violations(stats: Optional[Dict[str, Any]],
                                    rel_tol: float = 1.19e-7) -> List[str]:
    """Names of every way this hook's record fails to prove it did what it claims.

    An EMPTY list is the only clean state. The two branches are deliberately asymmetric:

      enabled=True  -- must have RUN, must have EDITED, and must have CHANGED THE STATE.
                       A deliberately disabled hook presented as a live arm fails here on
                       `hook_fired_count==0`, which is the unit-tested case.
      enabled=False -- the C5 disabled-hook bridge. It must have RUN, must have edited
                       NOTHING, and the hook it wrapped must have been one that WOULD have
                       changed the state. A bridge over a dead hook bridges nothing and is
                       refused rather than passed as a clean identity.
    """
    if stats is None:
        return ["no_stats_recorded"]
    missing = [k for k in HOOK_STATS_KEYS if k not in stats]
    if missing:
        return ["stats_missing_keys:" + ",".join(missing)]
    bad: List[str] = []
    if int(stats.get("n_forward_calls") or 0) == 0:
        bad.append("hook_never_ran:n_forward_calls==0")
    dn = stats.get("direction_norm")
    if dn is not None and float(dn) == 0.0:
        bad.append("zero_norm_direction")
    if stats.get("enabled", True):
        if int(stats.get("hook_fired_count") or 0) == 0:
            bad.append("hook_fired_count==0")
        if int(stats.get("n_cells_edited_realised") or 0) == 0:
            bad.append("zero_cells_edited")
        if not (float(stats.get("projection_removed_l2") or 0.0) > 0.0):
            bad.append("zero_projection_removed")
        if not (float(stats.get("max_abs_delta") or 0.0) > 0.0):
            bad.append("state_unchanged:max_abs_delta==0")
        # SCALE-FREE, AND NOT A RESTATEMENT OF THE TWO ABOVE. An edit whose magnitude is below
        # float32 resolution relative to the state is numerically indistinguishable from no edit
        # even though `max_abs_delta > 0` -- an under-dosed arm that would score as a clean null.
        # The bar is `rel_tol`, the float32 epsilon by default, NOT a scientific threshold.
        _npre = float(stats.get("activation_norm_pre") or 0.0)
        if _npre > 0.0:
            _rel = float(stats.get("projection_removed_l2") or 0.0) / _npre
            if _rel < rel_tol:
                bad.append("edit_below_float32_resolution:rel=%.3e" % _rel)
        # The COSINE is required to be RECORDED (mandate 10.3 lists it among the persisted
        # quantities). It is not gated on `== 1.0`: at float32 a genuine small edit rounds the
        # cosine to 1.0000001, so gating on it would refuse live hooks. `max_abs_delta` and the
        # relative-magnitude rule above answer "did the state change" without that false alarm.
        if stats.get("cos_pre_post") is None:
            bad.append("cosine_not_recorded")
        # ---- C-117: REALISED vs EXPECTED, and it must not be vacuous ----------------------
        # `n_cells_edited_expected` is counted at the top of every forward from the tensor the
        # hook was handed; `n_cells_edited_realised` from the slice it wrote. The frozen config's
        # `void_if` names "realised != expected cell count", and a comparison of 0 with 0 does
        # not implement it -- a check that binds zero is not a check.
        _exp = stats.get("n_cells_edited_expected")
        if _exp is None:
            bad.append("n_cells_edited_expected_NOT_MEASURED")
        elif int(_exp) == 0:
            bad.append("n_cells_edited_expected==0:the hook was handed no destinations, so "
                       "'realised == expected' is vacuously true")
        elif int(stats.get("n_cells_edited_realised") or 0) != int(_exp):
            bad.append("realised_!=_expected:%d!=%d"
                       % (int(stats.get("n_cells_edited_realised") or 0), int(_exp)))
        # ---- review F6: EVERY forward that had destinations must have fired ---------------
        # The gated scalars above are overwritten on each call, so on their own they certify the
        # LAST forward. This is an exact identity over all of them, with no threshold: a hook
        # dead on prefill but live on the final decode step no longer passes.
        _nfd = int(stats.get("n_forward_with_destinations") or 0)
        if _nfd and int(stats.get("hook_fired_count") or 0) != _nfd:
            bad.append("partially_dead_hook:fired %d of %d forwards that had destinations"
                       % (int(stats.get("hook_fired_count") or 0), _nfd))
        _minp = stats.get("min_projection_removed_l2")
        if _minp is None:
            bad.append("min_projection_removed_l2_NOT_MEASURED")
        elif not (float(_minp) > 0.0):
            bad.append("some forward removed EXACTLY ZERO projection "
                       "(min_projection_removed_l2==0) even though the hook reports firing")
        # ---- C-117: the orthogonal residual is MEASURED, never defaulted ------------------
        # `orthogonal_residual_gate` in the analyzer used to read this field with a NaN default
        # and then assert "the orthogonal component was NOT preserved; H2b is VOID" when the
        # truth was that nobody had measured it. It is measured here; its absence is a
        # NOT-MEASURED refusal, which is a different thing from a violation.
        if stats.get("orthogonal_residual_delta_l2") is None:
            bad.append("orthogonal_residual_delta_l2_NOT_MEASURED")
        # ---- C4: the ADDITIVE arm's DOSE, declared AND measured ---------------------------
        # `pc.AllPositionAdd` normalises its direction, so the `alpha` it is handed is an
        # ABSOLUTE residual-space magnitude. Every non-`refusalness` caller doses in GAP UNITS
        # and must therefore hand it `alpha * gap`. A bare `alpha` there injects an absolute
        # magnitude under a gap-unit label -- at L18 a 14.65x overdose from an identical-looking
        # flag (RETRACTION F-3), and this repository has written that bug at this exact second
        # call site before. Two independent binds, neither of which is a threshold on a
        # scientific quantity:
        #   1. the caller DECLARES `alpha_gap_units` and `gap_norm`; the absolute `alpha` the
        #      hook actually holds must be their product. This catches the flag arithmetic.
        #   2. `realised_dose_l2_per_cell` -- the L2 of the change actually WRITTEN to a cell --
        #      is MEASURED in the hook and must equal `alpha`. This catches a hook body that
        #      disagrees with its own manifest, which (1) alone cannot see.
        if str(stats.get("mode") or "").startswith("add"):
            _al = stats.get("alpha")
            _du = stats.get("dose_units")
            _agu, _gn = stats.get("alpha_gap_units"), stats.get("gap_norm")
            if _al is None:
                bad.append("add_alpha_NOT_RECORDED")
            if _du is None:
                bad.append("add_dose_units_NOT_DECLARED:an additive arm whose caller did not say "
                           "whether alpha is in GAP UNITS or ABSOLUTE residual magnitude cannot "
                           "be audited for the F-3 overdose")
            elif str(_du) == "gap":
                if _agu is None or _gn is None:
                    bad.append("add_declared_gap_units_but_%s_NOT_RECORDED"
                               % ("alpha_gap_units" if _agu is None else "gap_norm"))
                elif _al is not None:
                    _want = float(_agu) * float(_gn)
                    if abs(float(_al) - _want) > 1e-6 * max(1.0, abs(_want)):
                        bad.append(
                            "add_dosed_in_ABSOLUTE_units:the hook holds alpha=%.6g but the "
                            "caller declared %.6g GAP UNITS x gap_norm %.6g = %.6g. A bare alpha "
                            "at this call site injects an absolute magnitude under a gap-unit "
                            "label (RETRACTION F-3)." % (float(_al), float(_agu), float(_gn),
                                                         _want))
            elif str(_du) != "absolute":
                bad.append("add_dose_units_UNKNOWN:%r (expected 'gap' or 'absolute')" % (_du,))
            _rd = stats.get("realised_dose_l2_per_cell")
            if _rd is None:
                bad.append("realised_dose_l2_per_cell_NOT_MEASURED")
            elif not (float(_rd) > 0.0):
                bad.append("realised_dose_l2_per_cell==0:the additive hook reports firing but "
                           "wrote a change of ZERO magnitude to every cell")
            elif _al is not None and abs(float(_al)) > 0.0:
                # 5% RELATIVE, and it is a NUMERICAL bar, not a scientific one: the add is
                # computed in the model's dtype (bf16 on the L40S nodes), whose ~3 decimal digits
                # put a genuine cell's realised magnitude within ~1e-2 of the requested one. The
                # error it exists to catch is a GAP FACTOR -- 1.6x to 2.6x at these layers, i.e.
                # 60-160% -- so the bar has two orders of magnitude of headroom over the noise
                # and none over the defect.
                _relerr = abs(float(_rd) - abs(float(_al))) / abs(float(_al))
                if _relerr > 5e-2:
                    bad.append(
                        "add_realised_dose_!=_declared:the hook WROTE %.6g per cell but reports "
                        "alpha=%.6g (relative error %.3g). The magnitude injected is not the "
                        "magnitude the manifest claims." % (float(_rd), float(_al), _relerr))
        # ---- an ALL-POSITION edit MUST NOT carry a single edit site (2026-09-08) -----------
        # `occurrence_index` is a property of the PROMPT and is populated on every mode (see
        # `occurrence_annotation`). `rel_end` and `resolved_absolute_index` are properties of the
        # EDIT SITE, and an all-position edit has none: there is no single site. A record that
        # carries one is not a more complete record, it is a FABRICATED one -- it says the edit
        # was scoped to a token when the edit touched every token -- and it would pass the
        # end-relative audit below while describing an intervention nobody ran. Refused here, in
        # the producer's own gate, so it cannot reach an artifact.
        if str(stats.get("mode") or "").endswith("_all"):
            for _k in ("rel_end", "resolved_absolute_index", "positions"):
                if stats.get(_k) is not None:
                    bad.append(
                        "all_position_edit_claims_a_single_site:%s=%r on mode %r. An "
                        "all-position edit has no edit site; inventing one is worse than "
                        "leaving it null." % (_k, stats.get(_k), stats.get("mode")))
        # ---- review F3: the persisted site must satisfy its own documented invariant -------
        _rel, _slr = stats.get("rel_end"), stats.get("seq_len_at_resolution")
        _abs = stats.get("resolved_absolute_index")
        if _abs is not None and (_rel is None or _slr is None):
            bad.append("site_not_auditable:resolved_absolute_index is persisted but %s is not, "
                       "so `resolved_absolute_index == seq_len + rel_end` cannot be checked"
                       % ("rel_end" if _rel is None else "seq_len_at_resolution"))
        elif _abs is not None:
            _idx = list(_abs) if isinstance(_abs, (list, tuple)) else [_abs]
            for _a in _idx:
                if int(_slr) + int(_rel) != int(_a):
                    bad.append("absolute_index_is_not_end_relative:%d != %d%+d"
                               % (int(_a), int(_slr), int(_rel)))
    else:
        if int(stats.get("n_cells_edited_realised") or 0) != 0:
            bad.append("disabled_hook_edited_cells")
        if not (float(stats.get("would_have_changed_max_abs") or 0.0) > 0.0):
            bad.append("bridge_over_a_dead_hook:would_have_changed_max_abs==0")
    return bad


def bridge_mask_liveness_violations(stats: Optional[Dict[str, Any]]) -> List[str]:
    """DCS-PR-059 D-6 / L-N1. The contract for a `DisabledHookBridge` over the ATTENTION-MASK
    family. [] is the only clean state.

    It is NOT `project_out_liveness_violations` with a widened branch, because the two bridges
    witness different things. The project-out bridge's evidence that its inner hook was alive is
    a HIDDEN-STATE delta; this one's is a MASK delta, whose magnitude is always |finfo.min| and
    therefore carries no information at all -- the informative quantity is HOW MANY mask cells
    would have been blocked. Reusing the other function would have let a bridge whose inner hook
    resolved ZERO rows pass on a magnitude that is constant by construction.
    """
    if stats is None:
        return ["no_stats_recorded"]
    bad: List[str] = []
    if stats.get("enabled", False):
        bad.append("bridge_stats_marked_enabled:a bridge that reports itself as a live arm is "
                   "not a bridge")
    if int(stats.get("n_forward_calls") or 0) == 0:
        bad.append("hook_never_ran:n_forward_calls==0")
    if int(stats.get("n_prefill_forward") or 0) == 0:
        bad.append("bridge_never_saw_a_prefill_forward:this family is PREFILL-ONLY, so a bridge "
                   "that only ran on decode steps exercised nothing the live arm does")
    if int(stats.get("n_cells_edited_realised") or 0) != 0:
        bad.append("disabled_hook_edited_cells")
    # A bridge over a DEAD hook bridges nothing and is refused rather than passed as a perfect
    # identity. Both witnesses are required: the count proves rows resolved, the magnitude proves
    # the write reached the tensor.
    if int(stats.get("n_mask_cells_would_have_edited") or 0) == 0:
        bad.append("bridge_over_a_dead_hook:n_mask_cells_would_have_edited==0 -- the wrapped "
                   "knockout resolved no rows, so this bridge certifies nothing")
    if not (float(stats.get("would_have_changed_max_abs") or 0.0) > 0.0):
        bad.append("bridge_over_a_dead_hook:would_have_changed_max_abs==0")
    # ---- DCS-C-134 (ADDITIVE): THE DISCARD, AS A MEASUREMENT ---------------------------------
    # Everything above this line witnesses that the inner hook was ALIVE. Nothing above it
    # witnesses that its write was DISCARDED -- that was left to a comment about cloning and to
    # a downstream analyzer's cell count. `_shim_pre` now snapshots the mask it was handed and
    # compares it after the inner hook has run, so the bridge can convict itself.
    if stats.get("n_live_mask_forwards_checked") is None:
        bad.append("discard_NOT_MEASURED:this bridge recorded no live-mask comparison at all, so "
                   "'the write was discarded' is an assertion and not an observation")
    elif int(stats.get("n_live_mask_forwards_checked") or 0) == 0:
        bad.append("discard_measured_on_ZERO_forwards:a check that binds nothing is not a check")
    if int(stats.get("n_cells_written_to_live_mask") or 0) != 0:
        bad.append("bridge_WROTE_%d_cells_into_the_LIVE_mask:the inner hook wrote through the "
                   "tensor the model handed it. This arm is a LIVE knockout wearing the null's "
                   "name." % int(stats.get("n_cells_written_to_live_mask") or 0))
    if stats.get("bridge_returned_a_different_mask_object"):
        bad.append("bridge_returned_a_different_mask_object:the kwargs handed back to the model "
                   "no longer carry the tensor the model supplied")
    return bad


def occurrence_annotation(stats: Optional[Dict[str, Any]],
                          codeword_last_indices: Optional[Sequence[int]]) -> Dict[str, Any]:
    """Resolve "occurrence index of the codeword" for ONE hook record, on EVERY edit mode.

    The frozen `persist_per_row_and_per_arm` list requires this field of every arm. It is a
    property of the PROMPT -- where the codeword occurs in this row -- NOT a property of the
    edit, so it is well defined whether the edit touched one position or all of them. Until
    2026-09-08 it was derived only from `resolved_absolute_index`, so the FIRST all-position
    (S2) arm ever run persisted `null` for it and was refused at artifact verification after a
    clean 230-row GPU run.

    `codeword_last_indices` is `last_idx_per_occurrence` from `extract_boombness.resolve_
    occurrences` -- one absolute index per occurrence of the codeword in this prompt. It is the
    SAME resolution the single-position path uses; nothing about occurrence resolution is
    re-implemented here.

      single-position modes  the ordinal of the occurrence the hook EDITED, or `None` for an
                             edited position that is not at a codeword_last site (the honest
                             value: it says "this edit was not at a codeword site" rather than
                             defaulting to 0 and implying it was the first occurrence).
      all-position modes     the ordinal of the codeword_last occurrence of this prompt -- the
                             LAST one, which is the site the single-position arms edit and
                             therefore the same value an S1 record carries for the same row.
                             It is labelled `occurrence_index_is_prompt_property = True` and
                             `occurrence_index_per_edit` stays `None`, so no reader can take it
                             for a claim that the edit was scoped to that occurrence. `rel_end`
                             and `resolved_absolute_index` STAY NULL for the same reason and
                             `project_out_liveness_violations` refuses a record that fills them.

    Returns the sibling fields the writer persists alongside the record; mutates
    `stats["occurrence_index"]` in place.
    """
    last = [int(x) for x in (codeword_last_indices or [])]
    if stats is None:
        return {"occurrence_index_per_edit": None,
                "occurrence_index_is_prompt_property": None,
                "occurrence_index_source": "no hook record"}
    if not last:
        # NOT 0, and not a guess. A prompt in which no codeword occurrence could be resolved has
        # no occurrence index, and a live arm carrying `None` here is REFUSED downstream by the
        # frozen persist contract -- which is the correct outcome, not a defect to paper over.
        stats["occurrence_index"] = None
        return {"occurrence_index_per_edit": None,
                "occurrence_index_is_prompt_property": None,
                "occurrence_index_source": "NO codeword occurrence resolved for this prompt"}
    _ri = stats.get("resolved_absolute_index")
    if _ri:
        _idx = list(_ri) if isinstance(_ri, (list, tuple)) else [_ri]
        occ = [(last.index(int(a)) if int(a) in last else None) for a in _idx]
        stats["occurrence_index"] = (occ[0] if len(occ) == 1 else occ)
        return {"occurrence_index_per_edit": occ,
                "occurrence_index_is_prompt_property": False,
                "occurrence_index_source": ("the ordinal, among this prompt's %d codeword "
                                            "occurrence(s), of the position this hook EDITED"
                                            % len(last))}
    stats["occurrence_index"] = len(last) - 1
    return {"occurrence_index_per_edit": None,
            "occurrence_index_is_prompt_property": True,
            "occurrence_index_source": (
                "codeword_last: the ordinal of the LAST of this prompt's %d codeword "
                "occurrence(s) (last_idx_per_occurrence[-1] = %d), which is the site the "
                "single-position arms edit. THIS record (mode %r) carries no single edit site "
                "-- an all-position edit has none, and a disabled-hook bridge discarded its "
                "write -- so `occurrence_index_per_edit`, `rel_end` and "
                "`resolved_absolute_index` are null, and this field is an audit property of the "
                "PROMPT, never a claim that the edit was scoped to this occurrence."
                % (len(last), last[-1], str(stats.get("mode") or "")))}


class DisabledHookBridge:
    """C5, the DISABLED-HOOK BRIDGE, as a real code path rather than a simulated one.

    Wraps an already-constructed pair_common edit context manager (`AllPositionProjectOut`,
    `AllPositionProjectOutMultiLayer`, `SinglePositionProjectOut`, `AllPositionAdd`, ...),
    registers on the SAME layer objects, RUNS THE INNER HOOK IN FULL, measures what its edit
    would have been, and then RETURNS THE UNMODIFIED OUTPUT.

    That is the distinction the bridge exists to make. "Comment out the hook" proves nothing:
    it does not run the resolution, the direction load, the dtype/device cast or the
    projection, so it cannot show that the machinery around the edit is inert. This runs all
    of it and discards only the write, and it RECORDS `would_have_changed_max_abs`, so a
    bridge whose inner hook was itself dead is detectable (`project_out_liveness_violations`
    refuses it) instead of scoring as a perfect identity.
    """

    #: The two hook FAMILIES this bridge knows how to run-and-discard. They differ in WHAT the
    #: discarded write is, so they cannot share a shim (DCS-PR-059 D-6).
    #:   "forward_output"     -- a `register_forward_hook` whose RETURN VALUE is the edited block
    #:                           output. Discarding = return the original output.
    #:   "attn_pre_kwargs"    -- a `register_forward_pre_hook(..., with_kwargs=True)` on
    #:                           `layer.self_attn` whose edit is written into the additive
    #:                           `attention_mask` it hands back. Discarding = return the ORIGINAL
    #:                           (args, kwargs), i.e. the unedited mask.
    BRIDGE_FAMILIES = ("forward_output", "attn_pre_kwargs")

    def __init__(self, inner, stats: Optional[Dict[str, Any]] = None):
        kind = "forward_output"
        if hasattr(inner, "_hooks") and hasattr(inner, "layers"):
            pairs = list(zip(list(inner.layers), list(inner._hooks)))
            idxs = list(getattr(inner, "layer_idxs", [-1] * len(pairs)))
        elif hasattr(inner, "_hook") and hasattr(inner, "layer"):
            pairs = [(inner.layer, inner._hook)]
            idxs = [int(getattr(inner, "layer_idx", -1))]
        elif hasattr(inner, "_pre") and getattr(inner, "layers", None):
            # DCS-PR-059 D-6 (ADDITIVE -- reached ONLY by objects the two branches above already
            # refused with a TypeError). The ATTENTION-KNOCKOUT family (`ScopedAttentionKnockout`,
            # `AllQueryAttentionKnockout`) edits the additive attention mask in a forward PRE hook
            # on `layer.self_attn` and exposes `_pre` / `layers` / `_handles` rather than a
            # `_hook`. Its edit is therefore not a return value to be swapped, and the bridge for
            # it must discard a different thing -- the mask -- which is why this is a separate
            # family rather than a widened `hasattr` on the branch above.
            #
            # It is a REAL bridge and not a simulated one for exactly the reason the class
            # docstring gives: `_pre` runs IN FULL -- the eager-mask assertion, the batch check,
            # the head expansion, `resolve_scoped_query_rows`, the per-key causal `lo`, the
            # min_val writes into the clone and every counter -- and only the WRITE is dropped.
            # "Comment out the knockout" proves none of that machinery is inert.
            kind = "attn_pre_kwargs"
            pairs = [(l, inner._pre) for l in list(inner.layers)]
            idxs = list(getattr(inner, "layer_idxs", [-1] * len(pairs)))
        else:
            raise TypeError(
                f"DisabledHookBridge cannot bridge {type(inner).__name__}: it exposes none of "
                "(_hook, layer), (_hooks, layers) or (_pre, layers). Refusing rather than "
                "registering nothing -- a bridge that binds no hook is exactly the clean-looking "
                "null this class exists to make impossible.")
        if not pairs:
            raise ValueError("DisabledHookBridge bound ZERO hooks; a bridge over nothing is not "
                             "a control.")
        self.kind = kind
        self.inner = inner
        self.layer_idxs = idxs
        self._pairs = pairs
        self.stats = stats if stats is not None else hook_stats_dict(
            mode=f"bridge:{type(inner).__name__}", layer=idxs[0], enabled=False)
        self.stats["enabled"] = False
        self.stats["mode"] = f"bridge:{type(inner).__name__}"
        # If the inner object carried its own live-arm record, mark it so it can never be read
        # as evidence that a live edit happened. Its write was discarded.
        _is = getattr(inner, "stats", None)
        if isinstance(_is, dict):
            _is["enabled"] = False
            _is["bridged_and_discarded"] = True
        # ---- DCS-C-134 (ADDITIVE, 2026-09-09) ------------------------------------------------
        # THE INNER HOOK IS TOLD IT IS BRIDGED. `enabled=False` on the record was never enough:
        # the inner hook went on incrementing its WRITE counters, and PHASE 11 job 870913
        # persisted a bridged row carrying hook_fired_count=8280 and
        # n_cells_edited_realised=13061664 -- the live arm's own numbers, from a write into a
        # clone this shim throws away. `bridged_discard` moves those counters into their
        # `_would_have` twins at source, so the record says FIRED-AND-DISCARDED rather than
        # FIRED-AND-WROTE, and `bridged_scoped_liveness_violations` refuses it if it does not.
        try:
            inner.bridged_discard = True
        except Exception:                                    # noqa: BLE001  (slots / frozen)
            pass
        if isinstance(_is, dict):
            for _k in KNOCKOUT_WOULD_HAVE_COUNTERS:
                _is.setdefault(_k, 0)
        self._handles: List[Any] = []
        if kind == "attn_pre_kwargs":
            # THE DISCARD IS MEASURED, NOT ASSERTED IN A COMMENT. Seeded so that "the bridge
            # never checked" and "the bridge checked and found zero" are different states.
            self.stats.setdefault("n_cells_written_to_live_mask", 0)
            self.stats.setdefault("n_live_mask_forwards_checked", 0)
            self.stats.setdefault("bridge_returned_a_different_mask_object", False)

    def _shim(self, fn):
        st = self.stats

        def f(module, inputs, output):
            st["n_forward_calls"] += 1
            h_in = output[0] if isinstance(output, tuple) else output
            if hasattr(h_in, "shape") and len(h_in.shape) >= 2:
                if int(h_in.shape[1]) <= 1:
                    st["n_decode_forward"] += 1
                else:
                    st["n_prefill_forward"] += 1
                st["seq_len_last"] = int(h_in.shape[1])
            edited = fn(module, inputs, output)          # the REAL hook runs, in full
            h_out = edited[0] if isinstance(edited, tuple) else edited
            if h_out is not h_in and hasattr(h_out, "shape"):
                d = (h_out.detach().float() - h_in.detach().float())
                st["would_have_changed_max_abs"] = max(
                    float(st["would_have_changed_max_abs"]), float(d.abs().max()))
                st["would_have_changed_l2"] = max(
                    float(st["would_have_changed_l2"]), float(d.norm()))
            return output                                 # ...and its edit is DISCARDED
        return f

    def _shim_pre(self, fn):
        """DCS-PR-059 D-6. The `attn_pre_kwargs` shim: run the real pre-hook IN FULL, measure the
        mask edit it WOULD have installed, and hand back the ORIGINAL (args, kwargs).

        `fn` is handed a COPY of the kwargs dict because `ScopedAttentionKnockout._pre` rebinds
        `kwargs["attention_mask"]` in place. It clones the tensor before writing, so the original
        mask is never touched -- the copy is belt-and-braces against a future hook that writes
        through, which would turn this bridge into a live arm silently.
        """
        st = self.stats

        def f(module, args, kwargs):
            st["n_forward_calls"] += 1
            am_in = kwargs.get("attention_mask")
            if am_in is not None and hasattr(am_in, "shape") and len(am_in.shape) >= 3:
                n_q = int(am_in.shape[-2])
                if n_q <= 1:
                    st["n_decode_forward"] += 1
                else:
                    st["n_prefill_forward"] += 1
                st["seq_len_last"] = n_q
            # DCS-C-134. THE WITNESS OF THE DISCARD, taken BEFORE the inner hook runs. A comment
            # saying "it clones, so the caller's tensor is safe" is not evidence; this is. If any
            # future hook in this family writes THROUGH into the mask it was handed, the bridge
            # is a live arm, and the only thing that would notice is this snapshot.
            _snap = (am_in.detach().clone()
                     if (am_in is not None and hasattr(am_in, "detach")) else None)
            # THE REAL HOOK RUNS, IN FULL -- including its eager-mask assertion and its refusal
            # of a non-4-D mask. A bridge that skipped them would not be exercising the code path.
            _a, _kw = fn(module, args, dict(kwargs))
            if _snap is not None:
                st["n_cells_written_to_live_mask"] = int(
                    st.get("n_cells_written_to_live_mask", 0)
                    + int((am_in.detach() != _snap).sum()))
                st["n_live_mask_forwards_checked"] = int(
                    st.get("n_live_mask_forwards_checked", 0)) + 1
            if kwargs.get("attention_mask") is not am_in:
                # The dict handed back to the model no longer holds the tensor the model gave us.
                # Whatever it holds, this is no longer a bridge.
                st["bridge_returned_a_different_mask_object"] = True
            am_out = _kw.get("attention_mask")
            if (am_in is not None and am_out is not None and am_out is not am_in
                    and hasattr(am_out, "shape")):
                d = (am_out.detach().float() - am_in.detach().float())
                st["would_have_changed_max_abs"] = max(
                    float(st["would_have_changed_max_abs"] or 0.0), float(d.abs().max()))
                st["would_have_changed_l2"] = max(
                    float(st["would_have_changed_l2"] or 0.0), float(d.norm()))
                # The count is the informative number for a MASK edit: the magnitude is always
                # |finfo.min| and says nothing, while "how many cells would have been blocked"
                # is what a reader needs to know the bridged hook was not itself dead.
                st["n_mask_cells_would_have_edited"] = int(
                    st.get("n_mask_cells_would_have_edited", 0) + int((d != 0).sum()))
            return args, kwargs                           # ...and the edit is DISCARDED

        return f

    def __enter__(self):
        for layer, fn in self._pairs:
            if self.kind == "attn_pre_kwargs":
                self._handles.append(layer.self_attn.register_forward_pre_hook(
                    self._shim_pre(fn), with_kwargs=True))
            else:
                self._handles.append(layer.register_forward_hook(self._shim(fn)))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False

    def liveness_violations(self) -> List[str]:
        if self.kind == "attn_pre_kwargs":
            return bridge_mask_liveness_violations(self.stats)
        return project_out_liveness_violations(self.stats)


# --------------------------------------------------------------------------- #
# All-position / all-timestep directional ablation (S4 — TOCTOU factorial)
# --------------------------------------------------------------------------- #
def make_project_out_hook(direction: torch.Tensor, alpha: float = 1.0,
                          stats: Optional[Dict[str, Any]] = None):
    """S4: forward hook that projects `direction` out of the block output at EVERY
    position and on EVERY forward call (prefill AND each KV-cached decode step).

    Lifted from poc_stage4/run_reasoning_intervention_experiments.py:175-191 into the
    ds_common/pair_common stack. UNLIKE ds_common.LayerPatch(mode="project_out"), which
    edits only a FIXED set of prompt positions and skips decode steps (seq==1 rows are
    out of range), this operates on the whole `hidden` tensor, so it also ablates the
    direction from GENERATED tokens — required to keep a refusal axis suppressed through
    the answer, not just on the prompt. The hook is registered on the decoder-LAYER
    output (register_forward_hook), so `direction` lives in the post-block-L residual
    == hidden_states[L+1]. `direction` need not be unit-norm; it is normalized here.
    """
    d_raw = direction.detach().float().cpu()
    d_cpu = d_raw / (d_raw.norm() + 1e-8)
    if stats is not None:
        stats["direction_norm"] = float(d_raw.norm())
        stats["alpha"] = float(alpha)
        if not stats.get("mode"):
            stats["mode"] = "project_out_all"

    def hook(module, inputs, output):
        is_tuple = isinstance(output, tuple)
        h = output[0] if is_tuple else output
        d = d_cpu.to(device=h.device, dtype=h.dtype)
        proj = (h * d).sum(dim=-1, keepdim=True)          # [.., 1] over hidden
        h_post = h - alpha * proj * d                     # broadcast over all positions
        # LIVENESS (default-off). With `stats is None` this branch is not entered and the
        # arithmetic above is byte-identical to the pre-2026-09-07 hook.
        if stats is not None:
            stats["n_forward_calls"] += 1
            if int(h.shape[1]) <= 1:
                stats["n_decode_forward"] += 1
            else:
                stats["n_prefill_forward"] += 1
            # EXPECTED, counted from the tensor this forward was HANDED and BEFORE the write.
            # An all-position edit's destination set is every cell of the block output, so the
            # count is batch x seq. Counting it here rather than deriving it from what was
            # written is the whole point: `realised == expected` must be able to be FALSE.
            stats["n_forward_with_destinations"] += 1
            stats["n_cells_edited_expected"] += int(h.shape[0]) * int(h.shape[1])
            _pre = h.reshape(-1, h.shape[-1])
            _post = h_post.reshape(-1, h_post.shape[-1])
            _record_edit(stats, _pre, _post, _pre - _post,
                         n_dest=int(h.shape[0]) * int(h.shape[1]), seq_len=int(h.shape[1]),
                         direction=d)
        h = h_post
        return (h,) + tuple(output[1:]) if is_tuple else h

    return hook


class AllPositionProjectOut:
    """Context manager wrapping `make_project_out_hook` on a single decoder layer.

    Registers the all-position/all-timestep projection hook on `layers[layer_idx]` and
    removes it on exit. Composes freely with ds_common.LayerPatch (concept install) in a
    shared ExitStack — the two hooks live on different mechanisms (this on the whole block
    output, LayerPatch on specific positions) and both fire per forward call. LayerPatch
    is left untouched (plan S4 §b/§g).
    """

    def __init__(self, model, layer_idx: int, direction: torch.Tensor,
                 alpha: float = 1.0, stats: Optional[Dict[str, Any]] = None,
                 rel_end: Optional[int] = None, occurrence_index: Optional[int] = None):
        self.layer = _resolve_layer(model, layer_idx)
        self.layer_idx = layer_idx
        # ADDITIVE, DEFAULT-OFF (Q12/C-13). `stats=None` -> no record, unchanged hook body.
        self.stats = stats
        if stats is not None:
            stats.update({"mode": "project_out_all", "layer": int(layer_idx),
                          "enabled": True, "positions": None})
            if rel_end is not None:
                stats["rel_end"] = int(rel_end)
            if occurrence_index is not None:
                stats["occurrence_index"] = int(occurrence_index)
        self._hook = make_project_out_hook(direction, alpha, stats=stats)
        self._handle = None

    def __enter__(self):
        self._handle = self.layer.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None
        return False


class AllPositionProjectOutMultiLayer:
    """S4: the multi-layer ablation of Arditi et al. — project the SAME single direction
    out of the block output at EVERY position/timestep on EVERY layer in `layer_idxs`.

    Single-layer AllPositionProjectOut projects a refusal axis out at one layer only
    (e.g. L14: refusal 1.0 -> 0.933), which barely dents refusal because the axis is
    re-written by later layers. The standard "directional ablation" removes ONE refusal
    direction from the residual stream at every layer during generation, which strongly
    suppresses refusal. This registers an independent all-position project-out hook (via
    the same `make_project_out_hook`) on each layer in `layer_idxs` and removes ALL handles
    on exit. `direction` is a single vector (the diff-of-means from the validated layer);
    the same vector is projected out at all layers — this is the standard ablation and
    what the paper does, even though the axis was fit at one layer. `direction` need not be
    unit-norm; each hook normalizes its own copy.

    Composes freely with ds_common.LayerPatch (concept install) in a shared ExitStack, the
    same as the single-layer class.

    Note (risk): the residual basis drifts across depth, so a mid-layer refusal axis is
    only an approximate refusal direction at very early / very late layers; projecting it
    everywhere is nonetheless the established recipe and empirically the strong ablation.
    """

    def __init__(self, model, layer_idxs: Sequence[int], direction: torch.Tensor,
                 alpha: float = 1.0,
                 stats_by_layer: Optional[Dict[int, Dict[str, Any]]] = None):
        all_layers = dc._get_layers(model)
        self.layer_idxs = list(layer_idxs)
        bad = [i for i in self.layer_idxs if i < 0 or i >= len(all_layers)]
        if bad:
            raise IndexError(f"layer index out of range for {len(all_layers)} layers: {bad}")
        self.layers = [all_layers[i] for i in self.layer_idxs]
        # LIVENESS: one INDEPENDENT record per layer (additive, default-off). A single shared
        # dict would let a hook that fired at one layer mask a hook that never fired at another
        # -- a PARTIALLY dead band, which one aggregate counter cannot see.
        self.stats_by_layer: Dict[int, Dict[str, Any]] = {}
        if stats_by_layer is not None:
            for i in self.layer_idxs:
                st = stats_by_layer.setdefault(
                    i, hook_stats_dict(mode="project_out_all", layer=i, enabled=True))
                st.update({"mode": "project_out_all", "layer": int(i), "enabled": True,
                           "positions": None})
                self.stats_by_layer[i] = st
        # one hook instance per layer (each holds its own normalized copy of `direction`)
        self._hooks = [make_project_out_hook(direction, alpha,
                                             stats=self.stats_by_layer.get(i))
                       for i in self.layer_idxs]
        self._handles: List[Any] = []

    def __enter__(self):
        for layer, hook in zip(self.layers, self._hooks):
            self._handles.append(layer.register_forward_hook(hook))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


# --------------------------------------------------------------------------- #
# Single-position / single-layer ablation — the D3 SCOPE-MATCHED control
# --------------------------------------------------------------------------- #
def make_single_position_project_out_hook(direction: torch.Tensor, alpha: float = 1.0,
                                          pos: int = -1,
                                          stats: Optional[Dict[str, Any]] = None):
    """Project `direction` out of the block output at ONE position (default the last
    prompt token = the `decision` position) and ONLY during PREFILL (a multi-token
    forward). This is the intervention-scope-matched analogue of a token attack, which
    perturbs the input at fixed positions and then lets the model generate normally:
    here we perturb the L18 residual at the single decision position during prefill; the
    change propagates through that position's KV and the generated answer follows, but no
    all-position/all-timestep suppression is applied. Contrast AllPositionProjectOut(Multi
    Layer), which ablates at every position and every decode step (the R3/D3 scope
    confound, ASYMMETRY_GAP_MATRIX §D3). On KV-cached decode steps (seq==1) the hook is a
    no-op — there is no decision position to touch. `direction` is normalized here.
    """
    d_raw = direction.detach().float().cpu()
    d_cpu = d_raw / (d_raw.norm() + 1e-8)
    if stats is not None:
        stats["direction_norm"] = float(d_raw.norm())
        stats["alpha"] = float(alpha)
        if not stats.get("mode"):
            stats["mode"] = "project_out_single"

    def hook(module, inputs, output):
        is_tuple = isinstance(output, tuple)
        h = output[0] if is_tuple else output
        if stats is not None:
            stats["n_forward_calls"] += 1
            if int(h.shape[1]) <= 1:
                stats["n_decode_forward"] += 1
            else:
                stats["n_prefill_forward"] += 1
        if h.shape[1] <= 1:                       # decode step (cached) → no-op
            return output
        d = d_cpu.to(device=h.device, dtype=h.dtype)
        h = h.clone()
        hp = h[:, pos, :]                          # [batch, hidden] at decision position
        proj = (hp * d).sum(dim=-1, keepdim=True)  # [batch, 1]
        h_new = hp - alpha * proj * d
        # `hp` is a VIEW into the cloned `h`, so the assignment below overwrites it. The
        # pre-edit state must be COPIED before the write or the liveness record compares the
        # post-edit state with itself and reports `projection_removed_l2 = 0` on a hook that
        # fired correctly -- i.e. the instrument would manufacture the exact dead-hook signature
        # it exists to detect. Caught by the self-test on its first run.
        hp_pre = hp.clone() if stats is not None else None
        h[:, pos, :] = h_new
        # LIVENESS (default-off). This branch also RESOLVES the (possibly negative) position
        # against the REALISED sequence length and records it, so `resolved_absolute_index ==
        # seq_len + rel_end` is auditable per row. A position computed once and reused as an
        # absolute index across examples is this repository's twice-recorded bug class, and its
        # signature -- a SINGLE distinct absolute index across prompts of different lengths --
        # is only visible if the index is written down.
        if stats is not None:
            _abs = pos if pos >= 0 else int(h.shape[1]) + int(pos)
            stats["n_forward_with_destinations"] += 1
            stats["n_cells_edited_expected"] += int(h.shape[0])
            _record_edit(stats, hp_pre, h_new, hp_pre - h_new,
                         n_dest=int(h.shape[0]), seq_len=int(h.shape[1]),
                         abs_index=[_abs], direction=d)
        return (h,) + tuple(output[1:]) if is_tuple else h

    return hook


class SinglePositionProjectOut:
    """Context manager: single-layer, single-position (decision) project-out — the
    pre-registered D3 scope-matched activation control (gap-matrix §D3, execution-log
    E-D3 deferral). Same medium as AllPositionProjectOut but scope-matched to the token
    attack's one-position/one-layer budget, so medium and scope are separable."""

    def __init__(self, model, layer_idx: int, direction: torch.Tensor,
                 alpha: float = 1.0, pos: int = -1,
                 stats: Optional[Dict[str, Any]] = None,
                 rel_end: Optional[int] = None, occurrence_index: Optional[int] = None,
                 seq_len_at_resolution: Optional[int] = None):
        """`pos` is the RESOLVED ABSOLUTE index inside the prompt; `rel_end` is the END-RELATIVE
        offset that produced it, and `seq_len_at_resolution` is the length it was resolved
        against (`len(input_ids)` of THIS row).

        WHY THREE ARGUMENTS FOR ONE SITE (review F3, 2026-09-07). The caller used to pass the
        already-resolved absolute index as BOTH `pos` and `rel_end`, so `rel_end` was recorded as
        7 on a 10-token row and 14 on a 17-token row: the frozen config's mandated end-relative
        persistence never happened, the documented invariant
        `resolved_absolute_index == seq_len + rel_end` was FALSE on every row while liveness
        reported clean, and a reader inspecting a VARYING `rel_end` would read it as evidence of
        exactly the absolute-index bug class the field exists to detect.

        The absolute index is what the hook must use -- the site is defined relative to the
        PROMPT, and this hook also fires on the readout's variant forwards, whose realised
        lengths differ; re-resolving `-10` against each of those would move the edit. So the
        absolute index is the input and the offset is the record, which is what
        `_absolute_index_is_persisted_only_as_a_witness` says. The identity between them is
        asserted HERE, at construction, per row -- the earliest point at which it can be
        checked -- and again in `project_out_liveness_violations` over the persisted record.
        """
        self.layer = _resolve_layer(model, layer_idx)
        self.layer_idx = layer_idx
        self.pos = int(pos)
        if rel_end is not None and int(rel_end) >= 0:
            raise ValueError(
                "SinglePositionProjectOut got rel_end=%r, which is NON-NEGATIVE. An end-relative "
                "offset is negative by construction; a non-negative one is an absolute index "
                "wearing the wrong name, and recording it as `rel_end` is how the persisted site "
                "stopped being auditable (review F3)." % (rel_end,))
        if rel_end is not None and seq_len_at_resolution is not None:
            _want = int(seq_len_at_resolution) + int(rel_end)
            if _want != int(pos):
                raise ValueError(
                    "SinglePositionProjectOut: pos=%d but seq_len_at_resolution(%d) + "
                    "rel_end(%d) = %d. The edit site and the site RECORDED for the audit are not "
                    "the same token. Refusing rather than editing one position and persisting "
                    "another." % (int(pos), int(seq_len_at_resolution), int(rel_end), _want))
        # ADDITIVE, DEFAULT-OFF (Q12/C-13).
        self.stats = stats
        if stats is not None:
            stats.update({"mode": "project_out_single", "layer": int(layer_idx),
                          "enabled": True, "positions": [int(pos)]})
            if rel_end is not None:
                stats["rel_end"] = int(rel_end)
            if seq_len_at_resolution is not None:
                stats["seq_len_at_resolution"] = int(seq_len_at_resolution)
            if occurrence_index is not None:
                stats["occurrence_index"] = int(occurrence_index)
        self._hook = make_single_position_project_out_hook(direction, alpha, pos, stats=stats)
        self._handle = None

    def __enter__(self):
        self._handle = self.layer.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None
        return False


# --------------------------------------------------------------------------- #
# All-position / all-timestep MLP-OUTPUT ablation (P10 §0.9 — decode-safe BEHAV-WRITE)
# --------------------------------------------------------------------------- #
class AllPositionMLPAblate:
    """Ablate the MLP sub-block OUTPUT of every layer in `layer_idxs` at EVERY position and on
    EVERY forward call (prefill AND each KV-cached decode step) — the generation-time analogue
    of ComponentOutSwap(component="mlp_out") and the MLP counterpart of AllPositionZHeadAblate.

    WHY (plan §0.9 / P10 item 1): ComponentOutSwap writes a FIXED set of positions behind the
    guard `keep = [k for k, p in enumerate(pos) if 0 <= p < seq]` (:410). On a KV-cached decode
    step `seq == 1`, so every prompt position is out of range and the swap contributes NOTHING
    after prefill. The BEHAV-WRITE behavioral null was measured with it and is therefore a
    PREFILL-ONLY (prompt-side) ablation, not the "ablate the L8-11 write throughout generation"
    it is reported as. This class edits the WHOLE output tensor, so the ablation persists into
    generated tokens; it is what the decode-safe re-test must use.

    Modes (`alpha` sets the strength, as in `make_project_out_hook`):
      "zero"         h <- 0                                    (decode-safe)
      "scale"        h <- alpha * h                            (decode-safe; alpha=0 == "zero")
      "project_out"  h <- h - alpha * (h . d_hat) d_hat        (decode-safe; needs `direction`)
      "mean"         h <- h.mean(seq, keepdim=True)            (PREFILL-ONLY — see NOTE)
    NOTE (same convention/caveat as AllPositionZHeadAblate): the mean is over the seq axis of
    the CURRENT forward, so on a decode step (seq == 1) it is an identity no-op — "mean" is
    prefill-only; use "zero"/"scale"/"project_out" for any generation-time necessity test.

    `direction` lives in MLP-output space (== residual space, the MLP writes into resid) and
    need not be unit-norm; it is normalized here. One forward hook per layer on `layer.mlp`
    (tensor- and tuple-valued outputs both handled); all handles removed on __exit__.

    Invariants (tests/test_allposmlp_synthetic.py): fires on prefill AND on seq==1 decode ·
    only `layer_idxs` touched · project_out leaves the orthogonal complement bit-identical ·
    cleanup on exit · ComponentOutSwap negative control is a no-op on the decode-shaped input.
    """
    _MODES = ("zero", "scale", "project_out", "mean")

    def __init__(self, model, layer_idxs: Sequence[int], mode: str = "zero",
                 direction: Optional[torch.Tensor] = None, alpha: float = 1.0):
        if mode not in self._MODES:
            raise ValueError(f"mode must be one of {list(self._MODES)}")
        if mode == "project_out" and direction is None:
            raise ValueError("mode='project_out' requires `direction`")
        all_layers = dc._get_layers(model)
        self.layer_idxs = [int(i) for i in layer_idxs]
        bad = [i for i in self.layer_idxs if i < 0 or i >= len(all_layers)]
        if bad:
            raise IndexError(f"layer index out of range for {len(all_layers)} layers: {bad}")
        self.layers = [all_layers[i] for i in self.layer_idxs]
        self.mode = mode
        self.alpha = float(alpha)
        self._d = None
        if direction is not None:
            d = direction.detach().float().cpu().flatten()
            self._d = d / (d.norm() + 1e-8)
        self._handles: List[Any] = []

    def _edit(self, h: torch.Tensor) -> torch.Tensor:
        if self.mode == "zero":
            return torch.zeros_like(h)
        if self.mode == "scale":
            return self.alpha * h
        if self.mode == "mean":                       # prefill-only by construction (see NOTE)
            return h.mean(dim=1, keepdim=True).expand_as(h).clone()
        d = self._d.to(device=h.device, dtype=h.dtype)
        proj = (h * d).sum(dim=-1, keepdim=True)      # [.., 1] over hidden
        return h - self.alpha * proj * d              # broadcast over ALL positions/timesteps

    def _hook(self, module, inputs, output):
        is_tuple = isinstance(output, tuple)
        h = self._edit(output[0] if is_tuple else output)
        return (h,) + tuple(output[1:]) if is_tuple else h

    def __enter__(self):
        for layer in self.layers:
            self._handles.append(layer.mlp.register_forward_hook(self._hook))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


# --------------------------------------------------------------------------- #
# All-position / all-timestep directional ADD (NEXT5 W5 — mechanism-derived defense)
# --------------------------------------------------------------------------- #
def _declare_add_dose(stats: Optional[Dict[str, Any]], alpha: float,
                      alpha_gap_units: Optional[float], gap_norm: Optional[float],
                      where: str) -> None:
    """Record the additive dose in BOTH units, and refuse a caller that contradicts itself.

    C4, 2026-09-07. `alpha` here is the ABSOLUTE residual-space magnitude the hook will inject,
    because the direction is normalised. Every non-`refusalness` caller in this repository doses
    additively in GAP UNITS -- `alpha_gap_units * gap` -- and passing a bare `alpha` there is a
    14.65x overdose at L18 from a flag that looks identical (RETRACTION F-3). So the caller
    declares BOTH numbers and the identity is asserted HERE, at construction, which is the
    earliest point it can be checked; `project_out_liveness_violations` asserts it again over the
    persisted record, so an arm cannot be analysed as gap-dosed without the check having run.
    """
    if stats is None:
        return
    stats["alpha"] = float(alpha)
    if alpha_gap_units is None and gap_norm is None:
        stats["dose_units"] = "absolute"
        stats["alpha_gap_units"] = None
        stats["gap_norm"] = None
        return
    if alpha_gap_units is None or gap_norm is None:
        raise ValueError(
            "%s: an additive dose declared in GAP UNITS needs BOTH alpha_gap_units and gap_norm "
            "(got %r and %r). Half a declaration cannot be audited." % (where, alpha_gap_units,
                                                                        gap_norm))
    want = float(alpha_gap_units) * float(gap_norm)
    if abs(float(alpha) - want) > 1e-6 * max(1.0, abs(want)):
        raise ValueError(
            "%s: the hook was handed alpha=%.6g but the caller declares %.6g GAP UNITS x "
            "gap_norm %.6g = %.6g. A bare alpha at this call site injects an ABSOLUTE magnitude "
            "under a gap-unit label -- the RETRACTION F-3 arithmetic. Refusing to build the "
            "hook." % (where, float(alpha), float(alpha_gap_units), float(gap_norm), want))
    stats["dose_units"] = "gap"
    stats["alpha_gap_units"] = float(alpha_gap_units)
    stats["gap_norm"] = float(gap_norm)


def _record_add_dose(stats: Dict[str, Any], pre: torch.Tensor, post: torch.Tensor) -> None:
    """MEASURE the per-cell magnitude actually written. `pre`/`post` are [n_cells, hidden].

    `_declare_add_dose` checks the caller's arithmetic; this checks the HOOK's. An additive edit
    writes `alpha * d_hat` to every destination cell, so the L2 of the change at a cell IS
    `alpha`. Recording it means the persisted record alone can convict a hook whose body does
    not inject what its manifest says -- including a hook that fired and wrote nothing, which is
    the C-13 signature this whole subsystem exists to make visible.
    """
    _per_cell = (pre.detach().float().reshape(-1, pre.shape[-1])
                 - post.detach().float().reshape(-1, post.shape[-1])).norm(dim=-1)
    if _per_cell.numel() == 0:
        return
    _mx = float(_per_cell.abs().max())
    _prev = stats.get("realised_dose_l2_per_cell")
    stats["realised_dose_l2_per_cell"] = _mx if _prev is None else max(float(_prev), _mx)


def make_add_hook(direction: torch.Tensor, alpha: float = 1.0,
                  stats: Optional[Dict[str, Any]] = None):
    """NEXT5 W5: forward hook that ADDS `alpha * d_hat` to the block output at EVERY
    position and on EVERY forward call (prefill AND each KV-cached decode step).

    The additive counterpart of `make_project_out_hook`. It exists because BOTH existing
    add paths are prefill-only — `ds_common.LayerPatch(mode="add")` edits a FIXED set of
    prompt positions and SKIPS decode steps (seq==1 rows are out of range). To keep a
    refusal axis PRESENT throughout generation (so late-emerging compliance keeps hitting
    the refusal direction on every generated token), the add must fire on the whole
    `hidden` tensor, including generated tokens. Registered on the decoder-LAYER output, so
    `direction` lives in the post-block-L residual == hidden_states[L+1]. `direction` is
    normalized to unit norm here, so `alpha` is an absolute residual-space magnitude,
    directly comparable across layers.

    LIVENESS (C4, 2026-09-07). `stats=None` (the default) leaves the hook body byte-identical
    to what every committed artifact was produced with. Passed a dict from `hook_stats_dict()`
    this records the same liveness quantities `make_project_out_hook` does -- fired count,
    forward split, expected vs realised cells, pre/post norms, the orthogonal residual, the
    minimum magnitude over forwards -- plus the additive DOSE. Until today `pc.AllPositionAdd`
    took no `stats` at all, so control C4 -- the equal-magnitude orthogonal edit, the arm whose
    whole job is to separate "this DIRECTION matters" from "this much PERTURBATION at this site
    matters" -- was the ONE remaining place in the intervention stack where a dead hook produced
    exactly the "the control did not move the readout" record a positive H2a wants to see.
    """
    d_raw = direction.detach().float().cpu()
    d_cpu = d_raw / (d_raw.norm() + 1e-8)
    if stats is not None:
        stats["direction_norm"] = float(d_raw.norm())
        if stats.get("alpha") is None:
            stats["alpha"] = float(alpha)
        if not stats.get("mode"):
            stats["mode"] = "add_all"

    def hook(module, inputs, output):
        is_tuple = isinstance(output, tuple)
        h = output[0] if is_tuple else output
        d = d_cpu.to(device=h.device, dtype=h.dtype)
        h_post = h + alpha * d                            # broadcast over ALL positions/timesteps
        # LIVENESS (default-off). With `stats is None` this branch is not entered and the
        # arithmetic above is byte-identical to the pre-2026-09-07 hook.
        if stats is not None:
            stats["n_forward_calls"] += 1
            if int(h.shape[1]) <= 1:
                stats["n_decode_forward"] += 1
            else:
                stats["n_prefill_forward"] += 1
            # EXPECTED, counted from the tensor this forward was HANDED and BEFORE the write,
            # exactly as the project-out hook counts it: an all-position edit's destination set
            # is every cell of the block output, so the count is batch x seq.
            stats["n_forward_with_destinations"] += 1
            stats["n_cells_edited_expected"] += int(h.shape[0]) * int(h.shape[1])
            _pre = h.reshape(-1, h.shape[-1])
            _post = h_post.reshape(-1, h_post.shape[-1])
            _record_edit(stats, _pre, _post, _pre - _post,
                         n_dest=int(h.shape[0]) * int(h.shape[1]), seq_len=int(h.shape[1]),
                         direction=d)
            _record_add_dose(stats, _pre, _post)
        h = h_post
        return (h,) + tuple(output[1:]) if is_tuple else h

    return hook


def make_single_position_add_hook(direction: torch.Tensor, alpha: float, pos: int,
                                  stats: Optional[Dict[str, Any]] = None):
    """The SINGLE-SITE additive edit: `alpha * d_hat` added at ONE absolute prompt position.

    C4 x S1, 2026-09-07. `edit_positions` used to be implemented for `project_out` only, so the
    single-site orthogonal control could not be built at all -- and building it out of
    `AllPositionAdd` would have been an ALL-POSITION edit reported under a single-site label,
    which is the silent-larger-intervention shape this phase refuses everywhere else. This is
    the additive mirror of `make_single_position_project_out_hook`, including its two
    load-bearing details: the pre-edit slice is COPIED before the write (`hp` is a view into the
    clone, so measuring after the write would compare the post-edit state with itself and
    manufacture the dead-hook signature), and on a KV-cached decode step (seq==1) there is no
    prompt site to touch, so the hook is a no-op there.
    """
    d_raw = direction.detach().float().cpu()
    d_cpu = d_raw / (d_raw.norm() + 1e-8)
    if stats is not None:
        stats["direction_norm"] = float(d_raw.norm())
        if stats.get("alpha") is None:
            stats["alpha"] = float(alpha)
        if not stats.get("mode"):
            stats["mode"] = "add_single"

    def hook(module, inputs, output):
        is_tuple = isinstance(output, tuple)
        h = output[0] if is_tuple else output
        if stats is not None:
            stats["n_forward_calls"] += 1
            if int(h.shape[1]) <= 1:
                stats["n_decode_forward"] += 1
            else:
                stats["n_prefill_forward"] += 1
        if h.shape[1] <= 1:                       # decode step (cached) -> no-op
            return output
        d = d_cpu.to(device=h.device, dtype=h.dtype)
        h = h.clone()
        hp = h[:, pos, :]
        h_new = hp + alpha * d
        hp_pre = hp.clone() if stats is not None else None
        h[:, pos, :] = h_new
        if stats is not None:
            _abs = pos if pos >= 0 else int(h.shape[1]) + int(pos)
            stats["n_forward_with_destinations"] += 1
            stats["n_cells_edited_expected"] += int(h.shape[0])
            _record_edit(stats, hp_pre, h_new, hp_pre - h_new,
                         n_dest=int(h.shape[0]), seq_len=int(h.shape[1]),
                         abs_index=[_abs], direction=d)
            _record_add_dose(stats, hp_pre, h_new)
        return (h,) + tuple(output[1:]) if is_tuple else h

    return hook


class AllPositionAdd:
    """Context manager wrapping `make_add_hook` on a single decoder layer (W5 defense).

    `stats`, `alpha_gap_units` and `gap_norm` are ADDITIVE and DEFAULT-OFF (C4). With all three
    omitted this is the class every committed W5 artifact was produced with: `dc._get_layers`
    resolves the layer, no record is written and the hook body is unchanged. `_resolve_layer`
    replaces the direct `_get_layers` index for one reason only -- it tries `_get_layers` FIRST
    and falls back to a hookable object only when that cannot resolve, which is what lets this
    hook be unit-tested on CPU against the REAL hook function rather than a re-implementation of
    it. Testing a copy of a hook proves nothing about the hook, and C-13 lived in exactly that
    gap.
    """

    def __init__(self, model, layer_idx: int, direction: torch.Tensor, alpha: float = 1.0,
                 stats: Optional[Dict[str, Any]] = None,
                 alpha_gap_units: Optional[float] = None,
                 gap_norm: Optional[float] = None):
        self.layer = _resolve_layer(model, layer_idx)
        self.layer_idx = layer_idx
        self.stats = stats
        if stats is not None:
            stats.update({"mode": "add_all", "layer": int(layer_idx),
                          "enabled": True, "positions": None})
            _declare_add_dose(stats, alpha, alpha_gap_units, gap_norm, "AllPositionAdd")
        self._hook = make_add_hook(direction, alpha, stats=stats)
        self._handle = None

    def __enter__(self):
        self._handle = self.layer.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None
        return False


class SinglePositionAdd:
    """C4 x S1: the equal-magnitude edit at ONE absolute prompt position, on one layer.

    The additive mirror of `SinglePositionProjectOut`, and it carries the same three-argument
    site contract for the same reason (review F3): `pos` is the RESOLVED ABSOLUTE index inside
    the prompt, `rel_end` is the END-RELATIVE offset that produced it, and
    `seq_len_at_resolution` is the length it was resolved against. The absolute index is what
    the hook must use -- this hook also fires on the readout's variant forwards, whose realised
    lengths differ, so re-resolving the offset inside the hook would MOVE the edit -- and the
    identity `seq_len_at_resolution + rel_end == pos` is asserted here, at construction, per row.
    """

    def __init__(self, model, layer_idx: int, direction: torch.Tensor,
                 alpha: float = 1.0, pos: int = -1,
                 stats: Optional[Dict[str, Any]] = None,
                 rel_end: Optional[int] = None, occurrence_index: Optional[int] = None,
                 seq_len_at_resolution: Optional[int] = None,
                 alpha_gap_units: Optional[float] = None,
                 gap_norm: Optional[float] = None):
        self.layer = _resolve_layer(model, layer_idx)
        self.layer_idx = layer_idx
        self.pos = int(pos)
        if rel_end is not None and int(rel_end) >= 0:
            raise ValueError(
                "SinglePositionAdd got rel_end=%r, which is NON-NEGATIVE. An end-relative offset "
                "is negative by construction; a non-negative one is an absolute index wearing "
                "the wrong name, and recording it as `rel_end` is how the persisted site stopped "
                "being auditable (review F3)." % (rel_end,))
        if rel_end is not None and seq_len_at_resolution is not None:
            _want = int(seq_len_at_resolution) + int(rel_end)
            if _want != int(pos):
                raise ValueError(
                    "SinglePositionAdd: pos=%d but seq_len_at_resolution(%d) + rel_end(%d) = %d. "
                    "The edit site and the site RECORDED for the audit are not the same token."
                    % (int(pos), int(seq_len_at_resolution), int(rel_end), _want))
        self.stats = stats
        if stats is not None:
            stats.update({"mode": "add_single", "layer": int(layer_idx),
                          "enabled": True, "positions": [int(pos)]})
            if rel_end is not None:
                stats["rel_end"] = int(rel_end)
            if seq_len_at_resolution is not None:
                stats["seq_len_at_resolution"] = int(seq_len_at_resolution)
            if occurrence_index is not None:
                stats["occurrence_index"] = int(occurrence_index)
            _declare_add_dose(stats, alpha, alpha_gap_units, gap_norm, "SinglePositionAdd")
        self._hook = make_single_position_add_hook(direction, alpha, int(pos), stats=stats)
        self._handle = None

    def __enter__(self):
        self._handle = self.layer.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None
        return False


class AllPositionAddMultiLayer:
    """NEXT5 W5: ADD the SAME single direction (e.g. the validated refusal axis) to the block
    output at EVERY position/timestep on EVERY layer in `layer_idxs`, throughout generation.

    The additive mirror of `AllPositionProjectOutMultiLayer`. The mechanism-derived defense:
    harmful semantics in Doublespeak emerge at a LATE/use depth while the refusal check acts
    earlier — so re-installing `+alpha * refusal_dir` at the late (use) layers on every
    generated token should re-engage refusal against the late-emerging compliance. Each layer
    gets its own hook holding a normalized copy of `direction`; all handles are removed on
    exit. Composes freely with ds_common.LayerPatch / the Doublespeak prompt in an ExitStack.
    """

    def __init__(self, model, layer_idxs: Sequence[int], direction: torch.Tensor,
                 alpha: float = 1.0):
        all_layers = dc._get_layers(model)
        self.layer_idxs = list(layer_idxs)
        bad = [i for i in self.layer_idxs if i < 0 or i >= len(all_layers)]
        if bad:
            raise IndexError(f"layer index out of range for {len(all_layers)} layers: {bad}")
        self.layers = [all_layers[i] for i in self.layer_idxs]
        self._hooks = [make_add_hook(direction, alpha) for _ in self.layers]
        self._handles: List[Any] = []

    def __enter__(self):
        for layer, hook in zip(self.layers, self._hooks):
            self._handles.append(layer.register_forward_hook(hook))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


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
