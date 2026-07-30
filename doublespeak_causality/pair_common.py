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

    _TARGETS = {"attn_out": "self_attn", "mlp_out": "mlp", "resid_post": None}

    def __init__(self, model, layer_idx: int, component: str,
                 positions: Sequence[int], vector: Optional[torch.Tensor] = None,
                 mode: str = "replace", alpha: float = 1.0):
        if component not in self._TARGETS:
            raise ValueError(f"component must be one of {sorted(self._TARGETS)}")
        layer = dc._get_layers(model)[layer_idx]
        attr = self._TARGETS[component]
        self.module = layer if attr is None else getattr(layer, attr)
        self.positions = list(positions)
        self.vector = vector
        self.mode = mode
        self.alpha = alpha
        self._handle = None

    def _hook(self, module, inputs, output):
        is_tuple = isinstance(output, tuple)
        hidden = (output[0] if is_tuple else output).clone()
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
        return (hidden,) + tuple(output[1:]) if is_tuple else hidden

    def __enter__(self):
        self._handle = self.module.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None
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
# All-position / all-timestep directional ablation (S4 — TOCTOU factorial)
# --------------------------------------------------------------------------- #
def make_project_out_hook(direction: torch.Tensor, alpha: float = 1.0):
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
    d_cpu = direction.detach().float().cpu()
    d_cpu = d_cpu / (d_cpu.norm() + 1e-8)

    def hook(module, inputs, output):
        is_tuple = isinstance(output, tuple)
        h = output[0] if is_tuple else output
        d = d_cpu.to(device=h.device, dtype=h.dtype)
        proj = (h * d).sum(dim=-1, keepdim=True)          # [.., 1] over hidden
        h = h - alpha * proj * d                          # broadcast over all positions
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
                 alpha: float = 1.0):
        self.layer = dc._get_layers(model)[layer_idx]
        self.layer_idx = layer_idx
        self._hook = make_project_out_hook(direction, alpha)
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
                 alpha: float = 1.0):
        all_layers = dc._get_layers(model)
        self.layer_idxs = list(layer_idxs)
        bad = [i for i in self.layer_idxs if i < 0 or i >= len(all_layers)]
        if bad:
            raise IndexError(f"layer index out of range for {len(all_layers)} layers: {bad}")
        self.layers = [all_layers[i] for i in self.layer_idxs]
        # one hook instance per layer (each holds its own normalized copy of `direction`)
        self._hooks = [make_project_out_hook(direction, alpha) for _ in self.layers]
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
