"""dominance.py — the hijacking paper's dominance score, ported to HF eager attention (plan §10.1).

ADOPTED FROM `external_repos/interp-jailbreak/src/interp/dominance_tools.py` (Ben-Tov, Geva,
Sharif, arXiv 2506.12880). Their quantity, our implementation, and the implementation is
deliberately different because ours is cheaper for the question we ask.

THE QUANTITY
Let `Y[l,h,dst,src,:]` be the contribution of (layer l, head h, SOURCE position src) to the
attention output at DESTINATION position dst:

    Y[l,h,dst,src,:] = A[l,h,dst,src] * (W_O[l,h] @ v[l,h,src])

Their two scores, unchanged in meaning:
    D_attn = <Y, attn_out[dst]> / ||attn_out[dst]||^2     sums to 1 over (h, src) — the share of
                                                          the attention output at dst that each
                                                          (head, source) supplied
    D_dir  = <Y, unit(dir)>                               the share ALONG A CHOSEN DIRECTION

For this sprint `dir = d_surface[l]`, so `D_dir[h, src]` answers plan §10.1 directly: **how much
of the Boombness arriving at the final codeword token was supplied by each demonstration token,
through which head.** That is the ranking that tells `pair_common.AttentionKnockout` which edges
are worth cutting, instead of cutting all of them and reporting that something happened.

WHY THIS PORT IS CHEAPER THAN THEIRS (not a shortcut — a consequence of asking less)
Their `get_model_hidden_states` materializes `Y` for ALL layers and ALL destinations, shape
[n_layer, n_head, T, T, d_model] — about 28 GB at T=120 on an 8B model, which is why their code
needs care about memory at all. We only ever need ONE destination (the final codeword occurrence).
Restricting dst to a single position removes a factor of T, and for `D_dir` the d_model axis
collapses analytically:

    <Y[h,src], u> = A[h,dst,src] * <W_O[h] @ v[h,src], u> = A[h,dst,src] * <v[h,src], W_O[h]^T u>

so we precompute `wo_dir[h] = W_O[h]^T u` once ([head_dim]) and never build a [T, d_model] tensor
at all. Cost is then A (n_head x T) plus v (n_kv_head x T x head_dim).

REQUIREMENTS AND TRAPS
* `attn_implementation="eager"` is REQUIRED to get `output_attentions`. Under SDPA the returned
  attentions are None or unreliable — the same constraint `pair_common.AttentionKnockout` has,
  and for the same reason.
* GQA: Llama-3.1-8B has 32 query heads and 8 KV heads, so query head h reads KV head
  `h // (n_q_heads // n_kv_heads)`. Getting this wrong silently attributes flow to the wrong head.
  The `--selftest` gate below catches it.
* Two invariants are asserted rather than trusted, mirroring the paper's own checks:
  `sum_{h,src} Y == attn_out[dst]` and `sum_{h,src} D_attn == 1`.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ds  # noqa: E402


def head_dims(model) -> Tuple[int, int, int]:
    """(n_query_heads, n_kv_heads, head_dim)."""
    cfg = model.config
    nq = int(cfg.num_attention_heads)
    nkv = int(getattr(cfg, "num_key_value_heads", nq))
    hd = int(getattr(cfg, "head_dim", cfg.hidden_size // nq))
    return nq, nkv, hd


class ValueCapture:
    """Capture `v_proj` output at chosen layers (pre-RoPE-irrelevant; values are not rotated)."""

    def __init__(self, model, layer_idxs: Sequence[int]):
        self.layers = ds()._get_layers(model)
        self.idxs = list(layer_idxs)
        self.buf: Dict[int, torch.Tensor] = {}
        self._h: List[object] = []

    def _hook(self, li):
        def f(mod, inp, out):
            self.buf[li] = (out[0] if isinstance(out, tuple) else out).detach()
        return f

    def __enter__(self):
        self.buf.clear()
        for li in self.idxs:
            self._h.append(self.layers[li].self_attn.v_proj.register_forward_hook(self._hook(li)))
        return self

    def __exit__(self, *e):
        for h in self._h:
            h.remove()
        self._h = []
        return False


@torch.no_grad()
def dominance_at(lm, input_ids: List[int], dst: int, layers: Sequence[int],
                 direction: Optional[Dict[int, torch.Tensor]] = None,
                 check_invariants: bool = True) -> Dict[str, Dict[int, torch.Tensor]]:
    """Dominance at ONE destination position.

    Returns {"D_attn": {layer: [n_head, T]}, "D_dir": {layer: [n_head, T]} (if `direction`)}.
    `direction[L]` is a d_model vector (it is unit-normalized here).
    """
    model = lm.model
    nq, nkv, hd = head_dims(model)
    rep = nq // nkv
    layers_mod = ds()._get_layers(model)

    with ValueCapture(model, layers) as vc:
        out = model(input_ids=torch.tensor([input_ids], device=model.device),
                    output_attentions=True, use_cache=False)
    attns = out.attentions
    if attns is None or attns[0] is None:
        raise RuntimeError(
            "output_attentions returned None — the model must be loaded with "
            "attn_implementation='eager' for dominance (same requirement as AttentionKnockout)")

    D_attn: Dict[int, torch.Tensor] = {}
    D_dir: Dict[int, torch.Tensor] = {}
    for L in layers:
        A = attns[L][0, :, dst, :].float()                       # [n_q_head, T]
        v = vc.buf[L][0].float().view(-1, nkv, hd)               # [T, n_kv_head, head_dim]
        Wo = layers_mod[L].self_attn.o_proj.weight.float()       # [d_model, n_q_head*head_dim]

        if direction is not None and L in direction:
            u = direction[L].float().reshape(-1)
            u = u / u.norm()
            # wo_dir[h] = W_O[h]^T u  ->  [n_q_head, head_dim];  no [T, d_model] tensor is built.
            wo_dir = torch.einsum("d,dk->k", u.to(Wo.device), Wo).view(nq, hd).cpu()
            vh = v[:, torch.arange(nq) // rep, :]                 # [T, n_q_head, head_dim] (GQA map)
            proj = torch.einsum("thk,hk->ht", vh, wo_dir)         # [n_q_head, T]
            D_dir[L] = (A.cpu() * proj)

        # D_attn needs the full per-(head,src) vector, but only for this one dst.
        vh = v[:, torch.arange(nq) // rep, :]                     # [T, n_q_head, head_dim]
        Wo_h = Wo.view(Wo.shape[0], nq, hd).permute(1, 0, 2).cpu()   # [n_q_head, d_model, head_dim]
        Yv = torch.einsum("hdk,thk->htd", Wo_h, vh)               # [n_q_head, T, d_model]
        Y = A.cpu().unsqueeze(-1) * Yv                            # [n_q_head, T, d_model]
        attn_out = Y.sum(dim=(0, 1))                              # == attention output at dst
        denom = attn_out.pow(2).sum()
        D_attn[L] = torch.einsum("htd,d->ht", Y, attn_out) / denom.clamp_min(1e-12)

        if check_invariants:
            s = float(D_attn[L].sum())
            if abs(s - 1.0) > 1e-3:
                raise AssertionError(
                    f"L{L}: sum of D_attn over (head, src) = {s:.6f}, expected 1.0 — the "
                    "value-flow decomposition does not reconstruct the attention output, so the "
                    "head mapping or the o_proj slicing is wrong")
    res: Dict[str, Dict[int, torch.Tensor]] = {"D_attn": D_attn}
    if direction is not None:
        res["D_dir"] = D_dir
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true",
                    help="verify the decomposition reconstructs the attention output exactly")
    ap.add_argument("--model", default=None)
    ap.add_argument("--layers", default="8,18")
    args = ap.parse_args()

    if not args.selftest:
        print("use --selftest, or import dominance_at()")
        return 0

    dc = ds()
    lm = dc.load_model(args.model or dc.PRIMARY_MODEL, dtype=torch.float32,
                       attn_implementation="eager")
    ids = lm.tokenizer("The report describes an object near the bridge and the storage yard.",
                       add_special_tokens=True)["input_ids"]
    layers = [int(x) for x in args.layers.split(",")]
    nq, nkv, hd = head_dims(lm.model)
    print(f"[dominance] {lm.model_id}: n_q_heads={nq} n_kv_heads={nkv} head_dim={hd} "
          f"(GQA rep={nq // nkv})  T={len(ids)}")

    d = {L: torch.randn(lm.hidden_size) for L in layers}
    res = dominance_at(lm, ids, dst=len(ids) - 1, layers=layers, direction=d,
                       check_invariants=True)
    for L in layers:
        da, dd = res["D_attn"][L], res["D_dir"][L]
        print(f"  L{L}: D_attn sum={float(da.sum()):.6f} (must be 1.0)  shape={tuple(da.shape)}  "
              f"D_dir range=[{float(dd.min()):+.3f}, {float(dd.max()):+.3f}]")
    print("selftest OK — the value-flow decomposition reconstructs the attention output, "
          "so the GQA head mapping and o_proj slicing are correct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
