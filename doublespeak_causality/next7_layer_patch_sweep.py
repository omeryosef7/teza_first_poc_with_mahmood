"""
next7_layer_patch_sweep.py — N7-C: FORWARD-ONLY true-patch layer sweep (memory-safe circuit map).

Gradient AtP (49/51) needs a backward pass that OOMs for a 14B model on a 44GB L40S. This measures
the SAME per-layer contribution with true patching only (no backward), so it runs on any model size:
for each layer L and component c in {attn_out, mlp_out}, replace c[L] at the token-aligned positions
with the matched-NEUTRAL (corrupt) value and record the metric delta. Same contrast/alignment/metric
as 48/49/51: clean=DOUBLESPEAK, corrupt=matched NEUTRAL, metric=logit_diff(concept-codeword).

Also cross-validates the Llama AtP maps (true per-layer contribution vs AtP sum|.|). Scalars only.

Run (GPU, L40S; fits Qwen3-14B):
  python next7_layer_patch_sweep.py --bench data/pair_benchmark/pair_carrot_bomb.json \
      --model Qwen/Qwen3-14B --enable-thinking false --demo-cap 4 --out outputs/patchsweep_qwen3_bomb
"""
import os, sys, json, argparse, importlib.util
from collections import defaultdict
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ds_common as dc
import pair_common as pc

_spec = importlib.util.spec_from_file_location("atp48", os.path.join(HERE, "48_attribution_patching.py"))
atp48 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(atp48)

_TARGET = {"attn_out": "self_attn", "mlp_out": "mlp"}


class ComponentPatchMulti:
    """Replace layer.<sub> output at positions[i] with vecs[i] (forward-only, single forward)."""
    def __init__(self, model, layer_idx, component, positions, vecs):
        self.sub = getattr(dc._get_layers(model)[layer_idx], _TARGET[component])
        self.positions, self.vecs = list(positions), vecs
        self._h = None
    def _hook(self, mod, inp, out):
        is_t = isinstance(out, tuple); h = out[0] if is_t else out
        h = h.clone()
        for i, p in enumerate(self.positions):
            if 0 <= p < h.shape[1]:
                h[0, p, :] = self.vecs[i].to(h.dtype).to(h.device)
        return (h,) + tuple(out[1:]) if is_t else h
    def __enter__(self):
        self._h = self.sub.register_forward_hook(self._hook); return self
    def __exit__(self, *e):
        if self._h: self._h.remove(); self._h = None
        return False


@torch.no_grad()
def run(lm, bench, args):
    pair = bench["pair"]; concept, codeword = pair["concept"], pair["codeword"]
    cap = getattr(args, "demo_cap", 0)
    if cap:
        bench = {**bench, "semantic": [r for r in bench["semantic"] if r.get("n_demos", 99) <= cap]}
    clean_row, corrupt_row = atp48._select_pair_rows(bench, args.readout, args.split)
    think = dc.parse_enable_thinking(getattr(args, "enable_thinking", "default"))
    clean_text = dc.apply_template(lm.tokenizer, clean_row["prompt"], enable_thinking=think)
    corrupt_text = dc.apply_template(lm.tokenizer, corrupt_row["prompt"], enable_thinking=think)

    positions, mapping, diag = atp48.build_alignment(lm, clean_text, corrupt_text, codeword)
    if not positions:
        raise ValueError("no token-aligned positions")
    metric = atp48.make_metric(lm, concept, codeword, args.metric)
    n_layers = lm.num_layers
    comps = ["attn_out", "mlp_out"] if args.component == "both" else [args.component]

    # capture corrupt components at the corrupt positions that clean positions map to
    corr_positions = sorted(set(mapping[p] for p in positions))
    corr_tok = lm.tokenizer(corrupt_text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
    with pc.ComponentCapture(lm, comps, corr_positions) as ccap:
        lm.model(**corr_tok)
    stacked = ccap.stacked()                                 # {comp: [n_layers, n_corr_pos, hidden]}
    cpos_idx = {p: i for i, p in enumerate(corr_positions)}

    def clean_forward():
        tok = lm.tokenizer(clean_text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
        return lm.model(**tok, return_dict=True)
    m_clean = float(metric(clean_forward()).detach())

    by_layer = {c: {} for c in comps}
    for comp in comps:
        for L in range(n_layers):
            vecs = [stacked[comp][L, cpos_idx[mapping[p]]] for p in positions]
            with ComponentPatchMulti(lm.model, L, comp, positions, vecs):
                m = float(metric(clean_forward()).detach())
            by_layer[comp][L] = round(m - m_clean, 5)

    res = {"model": args.model, "meta": lm.meta(), "pair": pair, "readout": args.readout,
           "split": args.split, "metric": args.metric, "m_clean": round(m_clean, 5),
           "n_layers": n_layers, "n_positions": len(positions), "alignment": diag,
           "true_delta_by_layer": by_layer,
           "sum_abs_by_layer": {c: {str(L): abs(v) for L, v in by_layer[c].items()} for c in comps}}
    for comp in comps:
        vals = {L: abs(v) for L, v in by_layer[comp].items()}
        top = sorted(vals.items(), key=lambda kv: kv[1], reverse=True)[:6]
        res[f"top_layers_{comp}"] = [{"layer": L, "abs_delta": round(v, 4)} for L, v in top]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True); ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out", required=True)
    ap.add_argument("--component", default="both", choices=["attn_out", "mlp_out", "both"])
    ap.add_argument("--readout", default="forced_choice"); ap.add_argument("--split", default="heldout")
    ap.add_argument("--metric", default="logit_diff", choices=["logit_diff", "p_concept"])
    ap.add_argument("--enable-thinking", default="default"); ap.add_argument("--demo-cap", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    dc.set_seed(args.seed); os.makedirs(args.out, exist_ok=True)
    lm = dc.load_model(args.model)
    res = run(lm, json.load(open(args.bench)), args)
    json.dump(res, open(os.path.join(args.out, "patchsweep_results.json"), "w"), indent=2)
    print(f"[patchsweep] {res['pair']['codeword']}->{res['pair']['concept']} m_clean={res['m_clean']} "
          f"n_layers={res['n_layers']} n_pos={res['n_positions']}")
    for comp in (["attn_out", "mlp_out"] if args.component == "both" else [args.component]):
        peak = max(res["by_layer"] if False else res["true_delta_by_layer"][comp].items(),
                   key=lambda kv: abs(kv[1]))
        band = sum(abs(res["true_delta_by_layer"][comp][L]) for L in range(7, 15)
                   if L in res["true_delta_by_layer"][comp])
        tot = sum(abs(v) for v in res["true_delta_by_layer"][comp].values())
        print(f"  {comp}: peak L{peak[0]} ({peak[1]:+.3f}) | L7-14 share {band/tot:.0%}")
    print(f"[patchsweep] -> {args.out}")


if __name__ == "__main__":
    main()
