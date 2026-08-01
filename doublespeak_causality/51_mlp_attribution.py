"""51_mlp_attribution.py — per-LAYER MLP Attribution Patching (N7-A).

Direct follow-up to NEXT6 D4: the Doublespeak concept-readout effect is mediated,
not written, by mid-band attention heads (large TOTAL true-patch, DIRECT~=0; head->head
edges do not reconstruct the total) => the mediation must run through MLP sublayers.
This LOCALIZES it: AtP[L,pos] = g_mlp . (mlp_corrupt - mlp_clean) on each layer.mlp
OUTPUT, validated by a TRUE SubmodulePatch(mlp) on the top-k cells. Same contrast /
alignment / metric / stats as 48; clean=DOUBLESPEAK, corrupt=matched NEUTRAL_CODEWORD.

Scalars only (plan §5.12); no prompt text / completions persisted. GPU script.
AtP<->true equivalence math is unit-tested GPU-free in tests/test_mlp_attribution.py.

Run (L40S):
  python 51_mlp_attribution.py --bench data/pair_benchmark/pair_carrot_bomb.json \
      --topk 40 --out outputs/mlp_atp_carrot_bomb
"""
import os, sys, json, argparse
from collections import defaultdict
import importlib.util
import numpy as np, torch

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ds_common as dc
import pair_common as pc

# reuse 48's selection / alignment / metric / correlation / align_corrupt verbatim
_spec = importlib.util.spec_from_file_location("atp48", os.path.join(HERE, "48_attribution_patching.py"))
atp48 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(atp48)


class _MLPActGradCapture:
    """Hook each target layer.mlp OUTPUT, retain its grad for the backward.
    Sibling of atp48._ActGradCapture but on layer.mlp (== SubmodulePatch 'mlp_out'
    target), so AtP and the true patch operate on the identical tensor."""
    def __init__(self, model, layer_idxs):
        self.layers = dc._get_layers(model); self.layer_idxs = list(layer_idxs)
        self.acts, self._handles = {}, []
    def _hook(self, li):
        def f(mod, inp, out):
            h = out[0] if isinstance(out, tuple) else out
            if h.requires_grad: h.retain_grad()
            self.acts[li] = h                       # keep graph node; do NOT detach
        return f
    def __enter__(self):
        for li in self.layer_idxs:
            self._handles.append(self.layers[li].mlp.register_forward_hook(self._hook(li)))
        return self
    def __exit__(self, *e):
        for h in self._handles: h.remove()
        self._handles = []; return False


@torch.no_grad()
def capture_mlp_outputs(lm, text, layer_idxs):
    tok = lm.tokenizer(text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
    cap = _MLPActGradCapture(lm.model, layer_idxs)
    with cap: lm.model(**tok, return_dict=True)
    return {L: cap.acts[L].detach()[0].float().cpu() for L in layer_idxs}


def run(lm, bench, args):
    pair = bench["pair"]; concept, codeword = pair["concept"], pair["codeword"]
    cap = getattr(args, "demo_cap", 0)
    if cap:                                    # shorten prompt (fewer demos) to fit big-model backward
        bench = {**bench, "semantic": [r for r in bench["semantic"] if r.get("n_demos", 99) <= cap]}
    clean_row, corrupt_row = atp48._select_pair_rows(bench, args.readout, args.split)
    think = dc.parse_enable_thinking(getattr(args, "enable_thinking", "default"))
    clean_text = dc.apply_template(lm.tokenizer, clean_row["prompt"], enable_thinking=think)
    corrupt_text = dc.apply_template(lm.tokenizer, corrupt_row["prompt"], enable_thinking=think)

    n_layers = lm.num_layers
    if args.layers:
        layer_idxs = [int(x) for x in args.layers.split(",") if x.strip()]
    else:
        layer_idxs = dc.patch_layer_sweep(n_layers - 1)
        if args.include_last_mlp and (n_layers - 1) not in layer_idxs:
            layer_idxs = layer_idxs + [n_layers - 1]   # last MLP IS upstream of final norm

    positions, mapping, diag = atp48.build_alignment(lm, clean_text, corrupt_text, codeword)
    if not positions: raise ValueError("no token-aligned positions")
    metric = atp48.make_metric(lm, concept, codeword, args.metric)

    clean_seq_len = len(lm.tokenizer(clean_text, add_special_tokens=False)["input_ids"])
    corrupt_out = capture_mlp_outputs(lm, corrupt_text, layer_idxs)
    corrupt_al = atp48.align_corrupt(corrupt_out, clean_seq_len, mapping, layer_idxs)  # reuse
    corrupt_dev = {L: v.to(lm.model.device) for L, v in corrupt_al.items()}

    def clean_forward():
        tok = lm.tokenizer(clean_text, return_tensors="pt",
                           add_special_tokens=False).to(lm.model.device)
        return lm.model(**tok, return_dict=True)

    # ---- AtP: one backward, grad wrt every target layer.mlp output ----
    cap = _MLPActGradCapture(lm.model, layer_idxs)
    with torch.enable_grad():
        with cap:
            out = clean_forward(); M = metric(out)
        if hasattr(lm.model, "zero_grad"): lm.model.zero_grad(set_to_none=True)
        M.backward()
    m_clean = float(M.detach())

    est = {}
    for L in layer_idxs:
        a = cap.acts[L]
        if a.grad is None: raise RuntimeError(f"no mlp-grad at layer {L}")
        ac = a.detach()[0].float(); g = a.grad[0].float(); cor = corrupt_dev[L].float()
        for pos in positions:
            est[(L, pos)] = float((g[pos] * (cor[pos] - ac[pos])).sum())

    # ---- validation gate: TRUE MLP replace-patch on top-k |AtP| cells ----
    ranked = sorted(est.items(), key=lambda kv: abs(kv[1]), reverse=True)
    topk = ranked[: args.topk]; val_atp, val_true, val_cells = [], [], []
    for (L, pos), aval in topk:
        vec = corrupt_dev[L][pos]
        with torch.no_grad():
            with pc.SubmodulePatch(lm.model, L, "mlp_out", [pos], vector=vec, mode="replace"):
                mp = float(metric(clean_forward()).detach())
        td = mp - m_clean
        val_atp.append(aval); val_true.append(td)
        val_cells.append({"layer": L, "pos": int(pos), "atp": round(aval, 5),
                          "true_delta": round(td, 5)})

    pear = atp48.pearson(val_atp, val_true) if len(val_atp) >= 2 else float("nan")
    spear = atp48.spearman(val_atp, val_true) if len(val_atp) >= 2 else float("nan")
    trustworthy = bool(np.isfinite(pear) and np.isfinite(spear)
                       and min(pear, spear) >= args.min_corr)

    # ---- reducer: sum|AtP| by layer + top MLP layers ----
    by_layer = defaultdict(float)
    for (L, pos), a in est.items(): by_layer[L] += abs(a)
    top_layers = sorted(by_layer.items(), key=lambda kv: kv[1], reverse=True)[:8]

    return {
        "model": args.model, "meta": lm.meta(), "pair": pair,
        "readout": args.readout, "split": args.split, "metric": args.metric,
        "m_clean": m_clean, "layers": layer_idxs, "alignment": diag,
        "clean_sid": clean_row["sid"], "corrupt_sid": corrupt_row["sid"],
        "topk": args.topk, "min_corr": args.min_corr,
        "pearson_atp_vs_true": pear, "spearman_atp_vs_true": spear,
        "trustworthy": trustworthy, "validation_cells": val_cells,
        "sum_abs_atp_by_layer": {str(L): round(v, 4) for L, v in sorted(by_layer.items())},
        "top_mlp_layers": [{"layer": L, "sum_abs_atp": round(v, 4)} for L, v in top_layers],
        "atp_map": [{"layer": L, "pos": int(pos), "atp": a} for (L, pos), a in ranked],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bench", required=True); ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out", required=True)
    ap.add_argument("--readout", default="one_word"); ap.add_argument("--split", default="dev")
    ap.add_argument("--enable-thinking", default="default")
    ap.add_argument("--demo-cap", type=int, default=0)
    ap.add_argument("--metric", default="logit_diff", choices=["logit_diff", "p_concept"])
    ap.add_argument("--layers", default="", help="comma ints; empty => sweep below readout")
    ap.add_argument("--include-last-mlp", action="store_true")
    ap.add_argument("--topk", type=int, default=40); ap.add_argument("--min-corr", type=float, default=0.7)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16","float16","float32"])
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    dc.set_seed(args.seed); os.makedirs(args.out, exist_ok=True)
    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))
    bench = json.load(open(args.bench)); res = run(lm, bench, args)
    json.dump(res, open(os.path.join(args.out, "mlp_atp_results.json"), "w"), indent=2)
    print(f"[mlp_atp] {res['pair']['codeword']}->{res['pair']['concept']} "
          f"m_clean={res['m_clean']:.3f} pearson={res['pearson_atp_vs_true']:.3f} "
          f"spearman={res['spearman_atp_vs_true']:.3f} trustworthy={res['trustworthy']}")
    print("  sum|AtP| by layer:", res["sum_abs_atp_by_layer"])
    print(f"[mlp_atp] -> {args.out}")


if __name__ == "__main__":
    main()


