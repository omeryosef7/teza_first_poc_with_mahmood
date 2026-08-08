#!/usr/bin/env python3
"""§28 addendum — DETERMINISTIC forward-pass equivalence of the two refusal-ablation implementations.

The full §28 run showed the house (pc.AllPositionProjectOutMultiLayer) and the from-scratch IndepProjectOut
reproduce the headline + ASR but diverge on ~43% of exact generations. This isolates whether that divergence
is a real implementation difference or bf16 reduction-order non-associativity amplified by greedy decoding.

For each item, on a SINGLE forward pass (no generation), compute the last-token residual at every layer under
(a) house ablation and (b) indep ablation, and report the max-abs and relative diff. If the diffs are at bf16
rounding scale (~1e-2 on an O(10-100) residual) the two implementations are numerically equivalent and the
generation divergence is greedy-decode bf16 non-associativity, not a logic discrepancy.

Usage: python scripts/phase28_forward_equiv.py --bench data/behavioral_v3/beh_clearharm.json \
  --refusal-pt outputs/stage_gcg_full/refusal_direction_llama_L18.pt --splits test --n 8
"""
from __future__ import annotations
import argparse, json, os, sys
from contextlib import ExitStack
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc
from phase28_framework_robustness import IndepProjectOut


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--refusal-pt", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--splits", default="test")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--enable-thinking", default="default")
    args = ap.parse_args()
    et = dc.parse_enable_thinking(args.enable_thinking)
    dc.set_seed(0)
    lm = dc.load_model(args.model); dev = lm.model.device; L = lm.num_layers
    v_ref = torch.load(args.refusal_pt).float().flatten()

    def house_ctx(): return pc.AllPositionProjectOutMultiLayer(lm.model, range(L), v_ref, args.alpha)
    def indep_ctx(): return IndepProjectOut(lm.model, v_ref, args.alpha)

    @torch.no_grad()
    def last_resid(text, ctx):
        tok = lm.tokenizer(text, return_tensors="pt", add_special_tokens=False).to(dev)
        with ExitStack() as st:
            st.enter_context(ctx)
            out = lm.model(**tok, output_hidden_states=True, return_dict=True)
        return torch.stack([hs[0, -1, :].float().cpu() for hs in out.hidden_states])  # [L+1, H]

    data = json.load(open(args.bench)); items = data["items"] if isinstance(data, dict) else data
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    diffs, rels = [], []
    for split in splits:
        cand = [it for it in items if it.get("split") == split][: args.n]
        for it in cand:
            hw, cw = it["harmful_word"], it["codeword"]
            instr = it["harmful_instruction"]
            if hw not in instr: instr = f"Give detailed step-by-step instructions to make a {hw}."
            demos = it["demos"] if isinstance(it["demos"], str) else "\n".join(it["demos"])
            conds = dc.build_conditions(instr, hw, cw, demos)
            t = dc.apply_template(lm.tokenizer, conds.doublespeak, add_generation_prompt=True, enable_thinking=et)
            rh = last_resid(t, house_ctx()); ri = last_resid(t, indep_ctx())
            d = float((rh - ri).abs().max()); scale = float(rh.abs().max())
            diffs.append(d); rels.append(d / (scale + 1e-8))
    diffs = np.array(diffs); rels = np.array(rels)
    print(f"[fwd-equiv] n={len(diffs)} house-vs-indep last-token residual (all layers):", flush=True)
    print(f"  max_abs_diff: median={np.median(diffs):.6f} max={diffs.max():.6f}", flush=True)
    print(f"  rel_diff:     median={np.median(rels):.2e} max={rels.max():.2e}", flush=True)
    # bf16 has ~3 decimal digits; a rel diff <~1e-2 across a 32-layer stack = rounding-order equivalent
    verdict = "EQUIVALENT (bf16 reduction-order only)" if rels.max() < 5e-2 else "DIFFERENT (real discrepancy)"
    print(f"  verdict: {verdict}", flush=True)


if __name__ == "__main__":
    main()
