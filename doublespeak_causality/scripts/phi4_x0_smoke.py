#!/usr/bin/env python3
"""Phase 5 STAGE X0 — Phi-4-mini-reasoning compatibility smoke (NEXT sprint 2026-08-09).

Validates the third-family model plumbing WITHOUT any scientific claim:
  - loads offline (HF_HUB_OFFLINE), reports num_layers / dtype / device
  - native chat template applies; reports whether reasoning/thinking tags appear
  - native EOS id resolves
  - codeword localization works AFTER templating (find_word_occurrences_in_text)
  - generation runs; reports gen length, stop reason, whether a </think>-style boundary
    and a final answer are present

Scalar/structure output ONLY — never prints harmful instruction or generation text.
Reuses ds_common (load_model, build_conditions, apply_template, localization).
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import ds_common as dc  # noqa: E402
import torch  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="microsoft/Phi-4-mini-reasoning")
    ap.add_argument("--bench", default=os.path.join(HERE, "data/behavioral_v3b/beh_clearharm.json"))
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--max-new", type=int, default=512)
    ap.add_argument("--enable-thinking", default="default")
    args = ap.parse_args()

    et = dc.parse_enable_thinking(args.enable_thinking)
    lm = dc.load_model(args.model)
    tok = lm.tokenizer
    dev = lm.model.device
    print(f"[x0] model={args.model} num_layers={lm.num_layers} device={dev} "
          f"dtype={next(lm.model.parameters()).dtype}")
    print(f"[x0] eos_token_id={tok.eos_token_id} pad={tok.pad_token_id} "
          f"chat_template_present={tok.chat_template is not None}")

    data = json.load(open(args.bench))
    items = data["items"] if isinstance(data, dict) else data
    items = items[:args.n]

    ok_localize = 0
    for i, it in enumerate(items):
        instr = it["harmful_instruction"]; hw = it["harmful_word"]
        cw = it["codeword"]; demos = it["demos"]
        conds = dc.build_conditions(instr, hw, cw, demos)
        templated = dc.apply_template(tok, conds.doublespeak, add_generation_prompt=True, enable_thinking=et)
        # localization AFTER templating
        hit = dc.find_word_occurrences_in_text(tok, templated, cw)
        n_occ = hit.n
        if n_occ and n_occ > 0:
            ok_localize += 1
        enc = tok(templated, return_tensors="pt").to(dev)
        with torch.no_grad():
            out = lm.model.generate(**enc, max_new_tokens=args.max_new, do_sample=False,
                                    pad_token_id=tok.eos_token_id)
        gen_ids = out[0][enc["input_ids"].shape[1]:]
        gen_len = int(gen_ids.shape[0])
        stopped_eos = bool(gen_ids[-1].item() == tok.eos_token_id) if gen_len else False
        text = tok.decode(gen_ids, skip_special_tokens=False)
        has_think_open = ("<think>" in text) or ("<|thinking|>" in text)
        has_think_close = ("</think>" in text) or ("<|/thinking|>" in text)
        # scalar-only structural flags (no content)
        print(f"[x0] item{i} tmpl_toks={enc['input_ids'].shape[1]} codeword_occ={n_occ} "
              f"gen_len={gen_len} stop_eos={stopped_eos} think_open={has_think_open} "
              f"think_close={has_think_close}")

    print(f"[x0] localization_ok {ok_localize}/{len(items)}")
    print(f"[x0] DONE — compatibility smoke only, no scientific claim")


if __name__ == "__main__":
    main()
