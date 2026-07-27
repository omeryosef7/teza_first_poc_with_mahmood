"""
10_layerwise_knockout.py — Stage 4 / RQ4 depth localization (plan §11.2).

The global knockout (09) showed the hijacked meaning is routed from the demos to the
codeword via attention. This localizes WHERE IN DEPTH: block the final-codeword ->
demo-region attention at a chosen SET of layers only (per-layer forward_pre_hook on
LlamaAttention that edits the 4D attention_mask kwarg — interface confirmed in
logs/diag_attn_iface.log), and read patchscope P(harm) at late layer R.

Sweeps:
  * single-layer: block only at layer L (sweep L) -> which single layer matters most
  * cumulative [0..k]: block layers 0..k -> how deep must blocking go to kill it
Baseline = no hooks. Validated repeat-prompt Patchscopes decoder (07).

Deterministic; numbers only (plan §5.12).

Run: python 10_layerwise_knockout.py --model meta-llama/Llama-3.1-8B-Instruct \
     --only virus_muffin --templated
"""
import os
import sys
import json
import time
import argparse
from contextlib import ExitStack

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
from importlib import import_module
_ps = import_module("07_patchscope_readout")
PatchscopeDecoder = _ps.PatchscopeDecoder
token_id = _ps.token_id


def make_block_hook(cw_pos, demo_keys, min_val):
    dk = list(demo_keys)

    def preh(mod, args, kwargs):
        am = kwargs.get("attention_mask", None)
        if am is not None and am.dim() == 4 and cw_pos < am.shape[2]:
            am = am.clone()
            for k in dk:
                if k <= cw_pos:
                    am[0, 0, cw_pos, k] = min_val
            kwargs["attention_mask"] = am
        return (args, kwargs)
    return preh


@torch.no_grad()
def rep_with_layer_block(lm, tok, layers_to_block, cw_pos, demo_keys, readout_layer):
    """Forward with demos->cw attention blocked at `layers_to_block` only."""
    min_val = torch.finfo(next(lm.model.parameters()).dtype).min
    decoders = dc._get_layers(lm.model)
    with ExitStack() as stack:
        for L in layers_to_block:
            hook = make_block_hook(cw_pos, demo_keys, min_val)
            stack.enter_context(_hook_ctx(decoders[L].self_attn, hook))
        out = lm.model(**tok, output_hidden_states=True)
    return out.hidden_states[readout_layer + 1][0, cw_pos, :]


class _hook_ctx:
    def __init__(self, module, hook):
        self.module, self.hook, self.h = module, hook, None
    def __enter__(self):
        self.h = self.module.register_forward_pre_hook(self.hook, with_kwargs=True)
        return self
    def __exit__(self, *a):
        if self.h: self.h.remove()
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(__file__), "data",
                                                   "seed_concepts_gpt4omini.json"))
    ap.add_argument("--templated", action="store_true")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--readout-layer", type=int, default=30)
    ap.add_argument("--only", default="virus_muffin")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "outputs", f"stage4_layerko_{args.model.split('/')[-1]}_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype),
                       attn_implementation="eager")
    dec = PatchscopeDecoder(lm)
    R = args.readout_layer
    nL = lm.num_layers
    data = json.load(open(args.data))
    items = [it for it in data["items"]
             if (not args.only or it["id"] in set(args.only.split(",")))]

    report = {"model": args.model, "meta": lm.meta(), "readout_layer": R, "items": []}
    for it in items:
        demos = "\n".join(it["demos"]) if isinstance(it["demos"], list) else it["demos"]
        cond = dc.build_conditions(it["harmful_instruction"], it["harmful_word"],
                                   it["codeword"], demos)
        text = dc.apply_template(lm.tokenizer, cond.doublespeak) if args.templated \
            else cond.doublespeak
        tok = lm.tokenizer(text, return_tensors="pt").to(lm.model.device)
        ids = tok["input_ids"][0].tolist()
        hit = dc.find_word_occurrences(lm.tokenizer, ids, it["codeword"])
        cw_last = hit.last_idx[-1]
        demo_keys = list(range(0, hit.first_idx[-1]))
        harm_id = token_id(lm.tokenizer, it["harmful_word"])
        code_id = token_id(lm.tokenizer, it["codeword"])

        base_rep = rep_with_layer_block(lm, tok, [], cw_last, demo_keys, R)
        base_ph, base_pc = dec.decode(base_rep, R, harm_id, code_id)

        single = []
        for L in range(0, R + 1, 2):
            rep = rep_with_layer_block(lm, tok, [L], cw_last, demo_keys, R)
            ph, pc = dec.decode(rep, R, harm_id, code_id)
            single.append({"layer": L, "p_harm": ph, "p_code": pc})
        cumulative = []
        for k in range(2, R + 1, 3):
            rep = rep_with_layer_block(lm, tok, list(range(0, k + 1)), cw_last, demo_keys, R)
            ph, pc = dec.decode(rep, R, harm_id, code_id)
            cumulative.append({"through_layer": k, "p_harm": ph, "p_code": pc})

        report["items"].append({"id": it["id"], "cw_last": cw_last,
                                "n_demo_keys": len(demo_keys),
                                "baseline": {"p_harm": base_ph, "p_code": base_pc},
                                "single_layer": single, "cumulative": cumulative})
        # console: most-effective single layer + cumulative depth to reach ~0
        sl_best = min(single, key=lambda x: x["p_harm"])
        cum_kill = next((c["through_layer"] for c in cumulative
                         if c["p_harm"] < 0.5 * base_ph), None)
        print(f"[{it['id']}] baseline P_harm={base_ph:.3f} | best single-layer block "
              f"-> {sl_best['p_harm']:.3f}@L{sl_best['layer']} | cumulative<half by "
              f"through_layer={cum_kill}")

    report["status"] = "COMPLETE"
    with open(os.path.join(out_dir, "stage4_layerko_results.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[stage4-layerko] -> {out_dir}")


if __name__ == "__main__":
    main()
