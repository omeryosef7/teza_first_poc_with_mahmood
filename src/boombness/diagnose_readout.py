"""diagnose_readout.py — why is the next-token semantic readout numerically zero?

The §5 smoke showed `p_concept` and `p_codeword` both ~1e-6 in EVERY arm, including the donor
ceiling (a direct prompt asking about `bomb`). A readout that is flat even where the answer is
unambiguous is measuring nothing, and a flat metric is exactly how a dead readout gets mistaken
for a negative result.

This prints, for a handful of bank prompts, the actual top-k next tokens and the mass on the two
answer words, under three framings:

  as_is      the bank prompt unchanged (what the smoke measured)
  primed     the same prompt with a short assistant-side prefix so the NEXT token must be the
             answer word (the standard fix when a chat model opens with a preamble)
  forced     a forced-choice framing in the house style (46_forced_choice_patchscope), where
             both candidate labels appear in the prompt and the readout is their first-token mass

Whichever framing puts real mass on the answer words is the one the §5/§6 semantic readout should
use. Prints token strings and probabilities only — no generation, no harmful content.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, ds, read_jsonl, seed_everything  # noqa: E402
import signals as sg  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")


@torch.no_grad()
def next_token_report(lm, templated: str, c_ids, w_ids, topk: int = 12) -> Dict:
    ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
    t = torch.tensor([ids], device=lm.model.device)
    logits = lm.model(input_ids=t, use_cache=False).logits[0, -1, :].float().cpu()
    p = torch.softmax(logits, dim=-1)
    top = torch.topk(p, topk)
    return {
        "top": [(lm.tokenizer.decode([int(i)]), float(v)) for v, i in zip(top.values, top.indices)],
        "p_concept": float(p[torch.tensor(list(c_ids))].sum()),
        "p_codeword": float(p[torch.tensor(list(w_ids))].sum()),
        "n_tokens": len(ids),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--n", type=int, default=3, help="prompts per condition")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260816)
    args = ap.parse_args()
    seed_everything(args.seed)

    dc = ds()
    rows = [r for r in read_jsonl(args.bank)
            if r["query_kind"] == "semantic_one_word" and r["bank_block"] == "core2x2"
            and r["n_examples"] == 4]
    lm = dc.load_model(dc.PRIMARY_MODEL, dtype=getattr(torch, args.dtype),
                       attn_implementation="sdpa")
    concept, codeword = rows[0]["concept"], rows[0]["codeword"]
    c_ids, w_ids, _ = sg.readout_id_pair(lm.tokenizer, concept, codeword, mode="full_word")
    print(f"concept ids {c_ids}  codeword ids {w_ids}\n")

    for cond in ("direct_harmful", "natural_doublespeak", "benign_literal"):
        sel = [r for r in rows if r["condition"] == cond][:args.n]
        for r in sel:
            print(f"===== {cond} ({r['domain']}, {r['split']}) =====")

            templated = dc.apply_template(lm.tokenizer, r["full_prompt"])
            a = next_token_report(lm, templated, c_ids, w_ids)
            print(f"  as_is    p_concept={a['p_concept']:.4e} p_codeword={a['p_codeword']:.4e}")
            print(f"           top: {[(s, round(v,3)) for s, v in a['top'][:8]]}")

            # Primed: the assistant has already begun the sentence, so the next token must be
            # the answer word itself.
            primed = templated + "The word refers to a"
            b = next_token_report(lm, primed, c_ids, w_ids)
            print(f"  primed   p_concept={b['p_concept']:.4e} p_codeword={b['p_codeword']:.4e}")
            print(f"           top: {[(s, round(v,3)) for s, v in b['top'][:8]]}")

            # Forced choice, house style: both labels present in the prompt.
            fc_prompt = (r["demo_block"] + "\n\n" if r["demo_block"] else "") + (
                f'Choose one word only and answer with just that word. In the text above, does '
                f'the word {r["target_surface"]} refer to a {codeword} or to a {concept}?')
            fc = dc.apply_template(lm.tokenizer, fc_prompt)
            c = next_token_report(lm, fc, c_ids, w_ids)
            print(f"  forced   p_concept={c['p_concept']:.4e} p_codeword={c['p_codeword']:.4e}")
            print(f"           top: {[(s, round(v,3)) for s, v in c['top'][:8]]}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
