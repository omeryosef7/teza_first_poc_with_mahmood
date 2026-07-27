"""
09_attention_knockout.py — Stage 4 / RQ4 (plan §11): where does the hijacked meaning
come from? Block the final codeword's attention to the demonstrations and measure
whether the late-layer harmful semantics collapse.

Uses eager attention + a custom 4D additive mask (0 = allowed, large-negative =
blocked) so we can zero out attention from the final-codeword query position to
chosen key positions, at ALL layers, in one forward. Readout = the validated
repeat-prompt Patchscopes decoder at a late layer R (07's PatchscopeDecoder).

Knockouts (final-codeword query -> blocked keys):
  * prev_codewords : all EARLIER codeword occurrences (the substitution history)
  * demos_all      : every position before the final request line
Controls:
  * rand_before    : a random matched-size set of earlier NON-codeword positions
  * baseline       : no knockout
If blocking demos/prev-codewords drops patchscope P(harm) but the random control
does not, the harmful meaning is causally routed from the demonstrations via
attention to the codeword (RQ4).

Deterministic; numbers only (plan §5.12).

Run: python 09_attention_knockout.py --model meta-llama/Llama-3.1-8B-Instruct \
     --data data/seed_concepts_gpt4omini.json --only virus_muffin --templated
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


def build_mask(seq, device, dtype, q_pos, blocked_keys):
    """4D additive causal mask with (q_pos -> blocked_keys) additionally masked."""
    min_val = torch.finfo(dtype).min
    m = torch.full((seq, seq), min_val, device=device, dtype=dtype)
    m = torch.triu(m, diagonal=1)          # causal: allow k<=q (0), block k>q (min)
    for k in blocked_keys:
        if 0 <= k <= q_pos:
            m[q_pos, k] = min_val
    return m.view(1, 1, seq, seq)


@torch.no_grad()
def rep_under_mask(lm, input_ids, mask4d, pos, readout_layer):
    out = lm.model(input_ids=input_ids, attention_mask=mask4d,
                   output_hidden_states=True)
    return out.hidden_states[readout_layer + 1][0, pos, :]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(__file__), "data",
                                                   "seed_concepts_gpt4omini.json"))
    ap.add_argument("--templated", action="store_true")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--readout-layer", type=int, default=30)
    ap.add_argument("--only", default="virus_muffin")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "outputs", f"stage4_knockout_{args.model.split('/')[-1]}_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    # eager attention so the custom 4D mask is applied verbatim
    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype),
                       attn_implementation="eager")
    dec = PatchscopeDecoder(lm)
    R = args.readout_layer
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
        seq = len(ids)
        hit = dc.find_word_occurrences(lm.tokenizer, ids, it["codeword"])
        cw_last = hit.last_idx[-1]                    # final codeword (query)
        prev_cw = hit.last_idx[:-1]                   # earlier occurrences
        harm_id = token_id(lm.tokenizer, it["harmful_word"])
        code_id = token_id(lm.tokenizer, it["codeword"])
        final_start = hit.first_idx[-1]
        # F2 FIX (iter11): the OLD `demos_all = range(0, final_start)` blocked the ENTIRE request
        # (instruction prefix + verb phrase + substituted query up to the codeword), not just the
        # demonstrations → confounded "blocking demos eliminates the hijack" with "blocking the
        # request". Locate the REQUEST start (the instruction prefix, present only in the query, not
        # the demos) via char->token offsets, then block ONLY demo tokens (request intact), and add
        # the complementary REQUEST-ONLY control (block request phrasing, demos intact).
        req_prefix = "Do not reason, just"
        cpos = text.rfind(req_prefix)
        req_start_tok = final_start
        if cpos >= 0:
            try:
                enc = lm.tokenizer(text, return_offsets_mapping=True, add_special_tokens=True)
                offs = enc["offset_mapping"]
                req_start_tok = next((i for i, (s, e) in enumerate(offs) if s >= cpos and e > s), final_start)
            except Exception:
                req_start_tok = final_start
        demos_only = list(range(0, req_start_tok))                       # ONLY demo tokens
        request_only = [p for p in range(req_start_tok, seq) if p != cw_last]  # request, not demos
        gen = torch.Generator().manual_seed(args.seed)
        # random matched control: |prev_cw| random earlier non-codeword positions
        cw_set = set(hit.last_idx) | set(hit.first_idx)
        pool = [p for p in range(0, final_start) if p not in cw_set]
        k = min(len(prev_cw), len(pool))
        perm = torch.randperm(len(pool), generator=gen)[:k].tolist()
        rand_before = [pool[i] for i in perm]
        # count-matched random control for demos_only: |demos_only| random positions from [0,seq)
        # excluding the codeword (tests "block that many tokens" vs "block the demos specifically").
        pool2 = [p for p in range(0, seq) if p != cw_last]
        k2 = min(len(demos_only), len(pool2))
        perm2 = torch.randperm(len(pool2), generator=gen)[:k2].tolist()
        rand_demos_matched = [pool2[i] for i in perm2]

        dt = next(lm.model.parameters()).dtype
        dev = lm.model.device
        conds = {
            "baseline": [],
            "prev_codewords": prev_cw,
            "demos_only": demos_only,
            "request_only": request_only,
            "rand_before": rand_before,
            "rand_demos_matched": rand_demos_matched,
        }
        res = {"id": it["id"], "seq_len": seq, "cw_last": cw_last, "req_start_tok": req_start_tok,
               "n_prev_cw": len(prev_cw), "n_demos_tokens": len(demos_only),
               "n_request_tokens": len(request_only), "n_rand_ctrl": len(rand_before),
               "n_rand_demos_matched": len(rand_demos_matched), "conds": {}}
        for name, blocked in conds.items():
            m = build_mask(seq, dev, dt, cw_last, blocked)
            rep = rep_under_mask(lm, tok["input_ids"], m, cw_last, R)
            ph, pc = dec.decode(rep, R, harm_id, code_id)
            res["conds"][name] = {"p_harm": ph, "p_code": pc, "n_blocked": len(blocked)}
        report["items"].append(res)
        b = res["conds"]["baseline"]["p_harm"]
        print(f"[{it['id']}] baseline P_harm={b:.3f} | "
              f"demos_only={res['conds']['demos_only']['p_harm']:.3f} | "
              f"request_only={res['conds']['request_only']['p_harm']:.3f} | "
              f"rand_demos_matched={res['conds']['rand_demos_matched']['p_harm']:.3f}")

    report["status"] = "COMPLETE"
    with open(os.path.join(out_dir, "stage4_knockout_results.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"[stage4-knockout] -> {out_dir}")


if __name__ == "__main__":
    main()
