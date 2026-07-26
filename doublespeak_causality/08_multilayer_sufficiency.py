"""
08_multilayer_sufficiency.py — RQ2 completion (plan §9.2 / §10.1): is DISTRIBUTED
(multi-layer) injection sufficient to induce the harmful meaning, given that a
single-layer injection is not (C2 robust null)?

For a neutral prompt, inject the Direct codeword representation at the codeword
position across a WINDOW of consecutive layers simultaneously (stacked LayerPatch
hooks), then read Patchscopes P(harm) at a fixed late readout layer R.

Windows tested:
  * cumulative [0..k] for increasing k  -> is there a threshold depth?
  * fixed-width sliding windows (early / mid / late)  -> does WHERE you inject
    matter (a semantic-level timing signal, complementary to §10.3 behavioral)?
Controls: single-layer (=07, null), random-vector across the same window, baseline.

Reuses 07's PatchscopeDecoder. Deterministic; numbers only (plan §5.12).

Run: python 08_multilayer_sufficiency.py --model meta-llama/Llama-3.1-8B-Instruct \
     --data data/seed_concepts_gpt4omini.json --templated --only virus_muffin
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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from importlib import import_module
_ps = import_module("07_patchscope_readout")
PatchscopeDecoder = _ps.PatchscopeDecoder
token_id = _ps.token_id


@torch.no_grad()
def multilayer_patched_rep(lm, text, layers, pos, vecs, readout_layer, mode="replace"):
    """Patch `vecs[L]` at (layer L, pos) for every L in `layers` simultaneously
    (stacked hooks), return the codeword rep at readout_layer."""
    tok = lm.tokenizer(text, return_tensors="pt").to(lm.model.device)
    with ExitStack() as stack:
        for L in layers:
            stack.enter_context(dc.LayerPatch(lm.model, L, [pos], vector=vecs[L],
                                              mode=mode))
        out = lm.model(**tok, output_hidden_states=True)
    return out.hidden_states[readout_layer + 1][0, pos, :]


def run_item(lm, dec, it, templated, R, seed, width):
    demos = "\n".join(it["demos"]) if isinstance(it["demos"], list) else it["demos"]
    cond = dc.build_conditions(it["harmful_instruction"], it["harmful_word"],
                               it["codeword"], demos)
    render = lambda n: (dc.apply_template(lm.tokenizer, getattr(cond, n))
                        if templated else getattr(cond, n))
    neu_text, dir_text = render("neutral"), render("direct")
    harm_id = token_id(lm.tokenizer, it["harmful_word"])
    code_id = token_id(lm.tokenizer, it["codeword"])

    neu_cap = dc.capture_target_reps(lm, neu_text, it["codeword"])
    dir_cap = dc.capture_target_reps(lm, dir_text, it["harmful_word"])
    neu_pos = neu_cap["positions"]["codeword_last"]

    # per-layer Direct injection vectors (on device)
    dir_vecs = {L: dir_cap["reps"]["codeword_last"][L + 1].to(lm.model.device)
                for L in range(R + 1)}
    gen = torch.Generator().manual_seed(seed)
    rand_vecs = {}
    for L in range(R + 1):
        r = torch.randn(lm.hidden_size, generator=gen)
        r = r * (float(dir_vecs[L].float().norm()) / float(r.norm()))
        rand_vecs[L] = r.to(lm.model.device)

    # baselines
    neu_repR = neu_cap["reps"]["codeword_last"][R + 1].to(lm.model.device)
    base_ph, base_pc = dec.decode(neu_repR, R, harm_id, code_id)

    res = {"id": it["id"], "readout_layer": R, "width": width,
           "baseline_neutral": {"p_harm": base_ph, "p_code": base_pc},
           "cumulative": [], "sliding": [], "sliding_random": []}

    # cumulative windows [0..k]
    for k in range(2, R + 1, 3):
        layers = list(range(0, k + 1))
        rep = multilayer_patched_rep(lm, neu_text, layers, neu_pos, dir_vecs, R)
        ph, pc = dec.decode(rep, R, harm_id, code_id)
        res["cumulative"].append({"k": k, "n_layers": len(layers),
                                  "p_harm": ph, "p_code": pc})

    # fixed-width sliding windows across the range
    for start in range(0, R - width + 2, 3):
        layers = list(range(start, min(start + width, R + 1)))
        rep = multilayer_patched_rep(lm, neu_text, layers, neu_pos, dir_vecs, R)
        ph, pc = dec.decode(rep, R, harm_id, code_id)
        res["sliding"].append({"start": start, "end": layers[-1],
                               "p_harm": ph, "p_code": pc})
        # random-vector control across the same window
        repr_ = multilayer_patched_rep(lm, neu_text, layers, neu_pos, rand_vecs, R)
        phr, pcr = dec.decode(repr_, R, harm_id, code_id)
        res["sliding_random"].append({"start": start, "end": layers[-1],
                                      "p_harm": phr, "p_code": pcr})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(__file__), "data",
                                                   "seed_concepts_gpt4omini.json"))
    ap.add_argument("--templated", action="store_true")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--readout-layer", type=int, default=None)
    ap.add_argument("--width", type=int, default=8)
    ap.add_argument("--only", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "outputs", f"stage2c_multilayer_{args.model.split('/')[-1]}_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))
    dec = PatchscopeDecoder(lm)
    R = args.readout_layer if args.readout_layer is not None else lm.num_layers - 4
    data = json.load(open(args.data))
    items = data["items"]
    if args.only:
        keep = set(args.only.split(","))
        items = [it for it in items if it["id"] in keep]

    report = {"model": args.model, "meta": lm.meta(), "templated": args.templated,
              "readout_layer": R, "width": args.width, "items": []}
    for it in items:
        r = run_item(lm, dec, it, args.templated, R, args.seed, args.width)
        report["items"].append(r)
        cum_max = max((x["p_harm"] for x in r["cumulative"]), default=0)
        sld = r["sliding"]; rnd = r["sliding_random"]
        best = max(sld, key=lambda x: x["p_harm"]) if sld else {"p_harm": 0, "start": -1}
        rnd_max = max((x["p_harm"] for x in rnd), default=0)
        print(f"[{r['id']}] baseNeu={r['baseline_neutral']['p_harm']:.3f} | "
              f"cumulative max P_harm={cum_max:.3f} | sliding(w{args.width}) best "
              f"P_harm={best['p_harm']:.3f}@start{best['start']} | random-window max={rnd_max:.3f}")

    report["status"] = "COMPLETE"
    with open(os.path.join(out_dir, "stage2c_results.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[stage2c-multilayer] -> {out_dir}")


if __name__ == "__main__":
    main()
