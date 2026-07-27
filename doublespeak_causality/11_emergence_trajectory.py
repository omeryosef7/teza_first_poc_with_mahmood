"""
11_emergence_trajectory.py — headline artifact (plan §8.3): per-layer Patchscopes
decoding of the codeword rep for Direct / Neutral / Doublespeak, showing the
early-vs-late emergence contrast (the time-of-check/time-of-use signature).

Uses the VALIDATED repeat-prompt Patchscopes decoder (07). For each condition,
extract the codeword rep at each layer L and decode P(harm) by injecting at layer L.
Writes a JSON of {condition: [P_harm per layer]} for plotting.

Run: python 11_emergence_trajectory.py --model meta-llama/Llama-3.1-8B-Instruct \
     --only virus_muffin --templated
"""
import os
import sys
import json
import time
import argparse

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
from importlib import import_module
_ps = import_module("07_patchscope_readout")
PatchscopeDecoder = _ps.PatchscopeDecoder
token_id = _ps.token_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(__file__), "data",
                                                   "seed_concepts_gpt4omini.json"))
    ap.add_argument("--templated", action="store_true")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--only", default="virus_muffin")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "outputs", f"emergence_{args.model.split('/')[-1]}_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))
    dec = PatchscopeDecoder(lm)
    data = json.load(open(args.data))
    items = [it for it in data["items"]
             if (not args.only or it["id"] in set(args.only.split(",")))]
    nL = lm.num_layers

    report = {"model": args.model, "meta": lm.meta(), "num_layers": nL, "items": []}
    for it in items:
        demos = "\n".join(it["demos"]) if isinstance(it["demos"], list) else it["demos"]
        cond = dc.build_conditions(it["harmful_instruction"], it["harmful_word"],
                                   it["codeword"], demos)
        render = lambda n: (dc.apply_template(lm.tokenizer, getattr(cond, n))
                            if args.templated else getattr(cond, n))
        harm_id = token_id(lm.tokenizer, it["harmful_word"])
        code_id = token_id(lm.tokenizer, it["codeword"])
        traj = {}
        for cname, word in [("direct", it["harmful_word"]),
                            ("neutral", it["codeword"]),
                            ("doublespeak", it["codeword"])]:
            reps = dc.capture_target_reps(lm, render(cname), word)["reps"]["codeword_last"]
            ph = []
            for L in range(nL):
                p, _ = dec.decode(reps[L + 1].to(lm.model.device), L, harm_id, code_id)
                ph.append(p)
            traj[cname] = ph
        report["items"].append({"id": it["id"], "harm": it["harmful_word"],
                                "code": it["codeword"], "p_harm_by_layer": traj})
        # console: argmax layer per condition
        for c, v in traj.items():
            am = max(range(len(v)), key=lambda i: v[i])
            print(f"[{it['id']}] {c:12s} peak P_harm={v[am]:.3f} @L{am}")

    report["status"] = "COMPLETE"
    with open(os.path.join(out_dir, "emergence_results.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[emergence] -> {out_dir}")


if __name__ == "__main__":
    main()
