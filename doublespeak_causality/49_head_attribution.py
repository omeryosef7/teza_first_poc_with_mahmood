"""
49_head_attribution.py — NEXT5 W4 tier-B: per-HEAD attribution patching (layer x head) with a
true-patch validation gate, localizing which attention heads carry the Doublespeak context effect.

Extends 48_attribution_patching from layer x position (residual) to layer x head x position on the
per-head attention output z (o_proj input), reusing 48's alignment / metric / pair-selection and
stats verbatim. AtP[L,h,pos] = g_z[L,h,pos] . (z_corrupt[L,h,pos] - z_clean[L,h,pos]); validated
against a REAL per-head z-patch (pair_common.ZHeadPatch) on the top-k |AtP| cells (Pearson/Spearman
>= --min-corr => trustworthy). Metric = logit_diff (concept - codeword), clean = DOUBLESPEAK,
corrupt = matched NEUTRAL_CODEWORD (exactly as 48).

Scalars only (AtP values, correlations, top heads); no prompt text / completions persisted.

Run (GPU, L40S):
  python 49_head_attribution.py --bench data/pair_benchmark/pair_carrot_bomb.json \
      --readout forced_choice --split heldout --layers 10,12,14,16,18,20,22,24 --topk 40
"""
import os
import sys
import json
import time
import argparse
import importlib.util
from collections import defaultdict

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ds_common as dc
import pair_common as pc
import stats as st

# reuse 48's alignment / metric / selection / correlation verbatim
_spec = importlib.util.spec_from_file_location("atp48", os.path.join(HERE, "48_attribution_patching.py"))
atp48 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(atp48)


@torch.no_grad()
def capture_z(lm, text, layer_idxs):
    """{L: Tensor[seq, hidden] fp32 CPU} of per-head attention output z (o_proj input)."""
    tok = lm.tokenizer(text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
    cap = pc.ZHeadCapture(lm.model, layer_idxs)
    with cap:
        lm.model(**tok, return_dict=True)
    return {L: cap.acts[L].detach()[0].float().cpu() for L in layer_idxs}


def align_z(corrupt_z, clean_seq_len, mapping, layer_idxs):
    hidden = next(iter(corrupt_z.values())).shape[-1]
    out = {}
    for L in layer_idxs:
        buf = torch.zeros(clean_seq_len, hidden, dtype=torch.float32)
        src = corrupt_z[L]
        for cpos, npos in mapping.items():
            buf[cpos] = src[npos]
        out[L] = buf
    return out


def run(lm, bench, args):
    pair = bench["pair"]
    concept, codeword = pair["concept"], pair["codeword"]
    n_heads, head_dim = pc._attn_head_dims(lm.model)

    clean_row, corrupt_row = atp48._select_pair_rows(bench, args.readout, args.split)
    think = dc.parse_enable_thinking(getattr(args, "enable_thinking", "default"))
    clean_text = dc.apply_template(lm.tokenizer, clean_row["prompt"], enable_thinking=think)
    corrupt_text = dc.apply_template(lm.tokenizer, corrupt_row["prompt"], enable_thinking=think)

    n_layers = lm.num_layers
    layer_idxs = (dc.patch_layer_sweep(n_layers - 1) if args.layers == ""
                  else [int(x) for x in args.layers.split(",") if x.strip()])

    positions, mapping, diag = atp48.build_alignment(lm, clean_text, corrupt_text, codeword)
    if not positions:
        raise ValueError("no token-aligned positions between clean and corrupt prompts")
    metric = atp48.make_metric(lm, concept, codeword, args.metric)

    clean_seq_len = len(lm.tokenizer(clean_text, add_special_tokens=False)["input_ids"])
    corrupt_z = capture_z(lm, corrupt_text, layer_idxs)
    corrupt_al = align_z(corrupt_z, clean_seq_len, mapping, layer_idxs)   # {L: [seq, hidden]}
    corrupt_dev = {L: v.to(lm.model.device) for L, v in corrupt_al.items()}

    def clean_forward():
        tok = lm.tokenizer(clean_text, return_tensors="pt",
                           add_special_tokens=False).to(lm.model.device)
        return lm.model(**tok, return_dict=True)

    # ---- AtP on z: one backward, grad wrt every target layer's z ----
    cap = pc.ZHeadCapture(lm.model, layer_idxs)
    with torch.enable_grad():
        with cap:
            out = clean_forward()
            M = metric(out)
        if hasattr(lm.model, "zero_grad"):
            lm.model.zero_grad(set_to_none=True)
        M.backward()
    m_clean = float(M.detach())

    est = {}                                        # (L, h, pos) -> atp
    for L in layer_idxs:
        z = cap.acts[L]
        if z.grad is None:
            raise RuntimeError(f"no z-grad at layer {L}")
        g = z.grad[0].float().view(-1, n_heads, head_dim)          # [seq, H, hd]
        zc = z.detach()[0].float().view(-1, n_heads, head_dim)     # [seq, H, hd]
        cor = corrupt_dev[L].float().view(-1, n_heads, head_dim)   # [seq, H, hd]
        for pos in positions:
            delta = cor[pos] - zc[pos]                              # [H, hd]
            contrib = (g[pos] * delta).sum(dim=-1)                 # [H] per head
            for h in range(n_heads):
                est[(L, h, pos)] = float(contrib[h])

    # ---- validation gate: TRUE per-head z-patch on top-k |AtP| cells ----
    ranked = sorted(est.items(), key=lambda kv: abs(kv[1]), reverse=True)
    topk = ranked[: args.topk]
    val_atp, val_true = [], []
    val_cells = []
    for (L, h, pos), a in topk:
        vec = corrupt_dev[L].view(-1, n_heads, head_dim)[pos, h]   # corrupt z for this head/pos
        with torch.no_grad():
            with pc.ZHeadPatch(lm.model, L, h, [pos], vec):
                mp = float(metric(clean_forward()).detach())
        td = mp - m_clean
        val_atp.append(a); val_true.append(td)
        val_cells.append({"layer": L, "head": h, "pos": pos, "atp": round(a, 5),
                          "true_delta": round(td, 5)})

    pear = atp48.pearson(val_atp, val_true) if len(val_atp) >= 2 else None
    spear = atp48.spearman(val_atp, val_true) if len(val_atp) >= 2 else None
    trustworthy = bool(pear is not None and pear >= args.min_corr
                       and spear is not None and spear >= args.min_corr)

    # ---- reduce: per-head |AtP| summed over positions & layers; top heads ----
    by_head = defaultdict(float)         # (L,h) -> sum|atp| over positions
    by_layer = defaultdict(float)
    for (L, h, pos), a in est.items():
        by_head[(L, h)] += abs(a)
        by_layer[L] += abs(a)
    top_heads = sorted(by_head.items(), key=lambda kv: kv[1], reverse=True)[:20]

    return {
        "concept": concept, "codeword": codeword, "readout": args.readout, "split": args.split,
        "metric": args.metric, "n_layers": n_layers, "n_heads": n_heads, "head_dim": head_dim,
        "layers": layer_idxs, "alignment": diag, "n_cells": len(est),
        "m_clean": round(m_clean, 5),
        "validation": {"topk": args.topk, "pearson": pear, "spearman": spear,
                       "min_corr": args.min_corr, "trustworthy": trustworthy,
                       "cells": val_cells},
        "sum_abs_atp_by_layer": {str(L): round(v, 4) for L, v in sorted(by_layer.items())},
        "top_heads": [{"layer": L, "head": h, "sum_abs_atp": round(v, 4)} for (L, h), v in top_heads],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--readout", default="forced_choice")
    ap.add_argument("--split", default="heldout")
    ap.add_argument("--enable-thinking", default="default")
    ap.add_argument("--metric", default="logit_diff", choices=["logit_diff", "p_concept"])
    ap.add_argument("--layers", default="", help="comma ints; empty => valid sweep below readout")
    ap.add_argument("--topk", type=int, default=40)
    ap.add_argument("--min-corr", type=float, default=0.7)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model)          # default sdpa is fine (z hooks are on o_proj I/O)
    res = run(lm, bench, args)
    res["model"] = args.model
    res["meta"] = lm.meta()

    tag = args.model.split("/")[-1]
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"head_attr_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    json.dump(res, open(os.path.join(out_dir, "head_attribution.json"), "w"), indent=2)

    v = res["validation"]
    print(f"[head_attr] cells={res['n_cells']} m_clean={res['m_clean']} "
          f"pearson={v['pearson']} spearman={v['spearman']} trustworthy={v['trustworthy']}")
    print("  sum|AtP| by layer:", res["sum_abs_atp_by_layer"])
    print("  top heads:")
    for th in res["top_heads"][:10]:
        print(f"    L{th['layer']:>2} h{th['head']:>2}  sum|AtP|={th['sum_abs_atp']}")
    print(f"[head_attr] -> {out_dir}")


if __name__ == "__main__":
    main()
