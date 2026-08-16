"""diagnose_knockout.py — is `pair_common.AttentionKnockout` still firing on transformers 5.12?

WHY THIS EXISTS. The §10 positive control blocked EVERY pre-query key in EVERY head at two layers
(7392 edges), leaving the final token attending only to itself, and the readout moved by 0.086
log-odds. That is not a small effect — it is physically impossible if the mask edit reached the
attention computation. So the null in every knockout arm is a statement about the hook, not the
model.

`AttentionKnockout` edits `kwargs["attention_mask"]` in a forward-pre hook on `layer.self_attn`
and raises if the mask is not 4-D — and it did NOT raise, so a 4-D mask was present and was
modified. The question is whether the module still *uses* that kwarg. transformers 5.x moved to a
pluggable attention interface, and a mask supplied per-layer may be recomputed or ignored.

This measures it directly and unambiguously: capture the ATTENTION WEIGHTS with and without a
total knockout at one layer. If the weights are unchanged, the hook is not reaching the
computation, and that is a defect affecting every knockout result in this repository under this
transformers version — not only this sprint.
"""
from __future__ import annotations

import argparse
import os
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ds, pair  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=None)
    ap.add_argument("--layer", type=int, default=8)
    args = ap.parse_args()

    dc, pc = ds(), pair()
    lm = dc.load_model(args.model or dc.PRIMARY_MODEL, dtype=torch.float32,
                       attn_implementation="eager")
    import transformers
    print(f"[diag] transformers {transformers.__version__}  attn_impl="
          f"{getattr(lm.model.config, '_attn_implementation', '?')}")

    text = "The report describes an object near the bridge and the storage yard today."
    ids = lm.tokenizer(text, add_special_tokens=True)["input_ids"]
    T = len(ids)
    dst = T - 1
    t = torch.tensor([ids], device=lm.model.device)

    with torch.no_grad():
        clean = lm.model(input_ids=t, output_attentions=True, use_cache=False)
    A0 = clean.attentions[args.layer][0, :, dst, :].float().cpu()
    lg0 = clean.logits[0, -1, :].float().cpu()

    # Total knockout: block every key before dst, all heads, at this layer.
    with torch.no_grad():
        with pc.AttentionKnockout(lm.model, [args.layer], query_positions=[dst],
                                  blocked_keys=list(range(dst)), heads=None):
            ko = lm.model(input_ids=t, output_attentions=True, use_cache=False)
    A1 = ko.attentions[args.layer][0, :, dst, :].float().cpu()
    lg1 = ko.logits[0, -1, :].float().cpu()

    print(f"\n[diag] layer {args.layer}, destination = last token ({dst}), blocked keys = 0..{dst-1}")
    print(f"  attention row, clean : mass on keys<dst = {float(A0[:, :dst].sum(dim=1).mean()):.6f} "
          f"(per head, mean); mass on self = {float(A0[:, dst].mean()):.6f}")
    print(f"  attention row, knocked: mass on keys<dst = {float(A1[:, :dst].sum(dim=1).mean()):.6f} "
          f"(per head, mean); mass on self = {float(A1[:, dst].mean()):.6f}")
    d_attn = float((A0 - A1).abs().max())
    d_log = float((lg0 - lg1).abs().max())
    print(f"\n  max |Δ attention weight| = {d_attn:.6e}")
    print(f"  max |Δ final logit|      = {d_log:.6e}")

    if d_attn < 1e-6:
        print("\n  VERDICT: THE KNOCKOUT IS NOT FIRING. The attention weights are unchanged after a "
              "total mask-out, so kwargs['attention_mask'] is not what this transformers version "
              "uses for the eager attention computation. Every AttentionKnockout result under this "
              "version is void, in this sprint AND in any prior work that used it here.")
        return 1
    print("\n  VERDICT: the knockout fires; the attention weights changed as required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
