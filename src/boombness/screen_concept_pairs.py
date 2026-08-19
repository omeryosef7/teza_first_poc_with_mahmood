"""screen_concept_pairs.py — choose a second concept pair BEFORE generating a bank for it (E6).

WHY THIS EXISTS, AND WHAT IT SCREENS FOR. Every claim in this sprint is carrot↔bomb, and plan §2.4
makes a tokenization audit mandatory before any activation work. But `tokenization_audit.py` audits a
bank that already exists — by then the pair is chosen and a bad choice costs a full regeneration.
This screens candidate pairs first, on the four properties this sprint learned the hard way:

1. **Single-token bare form** (plan §2.4). A multi-token target makes "the codeword's position" a span,
   and every position-matched patch in §5 assumes a point.

2. **Single-token CAPITALISED form.** This is C-5, and it invalidated a readout. On Llama-3.1-8B the
   model *capitalises* its answer, and `' Carrot'` is TWO tokens (`' Car'` + `'rot'`) while `' Bomb'`
   is one — so a next-token forced choice was structurally biased toward the concept and could not
   represent the model's preferred spelling of the codeword. The whole-answer readout now handles
   this, but a pair that does not have the problem is strictly better than one that needs handling.

3. **The codeword's first subtoken must not be a common English word.** `' Car'` is why the capitalised
   variant could not simply be added to the option set: `readout_ids` rejects it by design, because a
   generic word would match text that has nothing to do with the codeword.

4. **Asymmetry in variant count.** `bomb` has four single-token variants and `carrot` one, so summing
   `full_word_ids` gives the concept four ids against the codeword's one — the same bias with a larger
   constant. A pair with matched variant counts needs no correction.

CPU-only: loads tokenizers, never a model. Reports every candidate with its failures named, and
prints the pairs that pass on both models so the choice is made from evidence rather than taste.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys

DEFAULT_MODELS = "meta-llama/Llama-3.1-8B-Instruct,Qwen/Qwen3-14B"
# Benign concrete nouns that can plausibly stand in for a harmful concept in a demonstration.
DEFAULT_CODEWORDS = ("carrot,apple,pencil,muffin,tulip,ladder,kettle,pebble,lantern,teapot,"
                     "basket,candle,pillow,button,marble")
DEFAULT_CONCEPTS = "bomb,virus,poison,weapon,toxin,gun,knife,drug,grenade,missile"
VARIANTS = ("{w}", " {w}", "{W}", " {W}")   # bare, leading-space, capitalised, space+capitalised


def screen(tok, word: str) -> dict:
    W = word.capitalize()
    ids = {v.format(w=word, W=W): tok(v.format(w=word, W=W), add_special_tokens=False)["input_ids"]
           for v in VARIANTS}
    single = {k: len(v) == 1 for k, v in ids.items()}
    first_sub = tok.decode(ids[f" {W}"][:1]).strip() if ids[f" {W}"] else ""
    return {
        "ids": ids,
        "n_single_token_variants": sum(single.values()),
        "bare_single": single[word],
        "space_single": single[f" {word}"],
        "cap_single": single[W],
        "space_cap_single": single[f" {W}"],
        "cap_first_subtoken": first_sub,
        # a first subtoken that is itself a short common word is the ' Car' problem
        "cap_first_subtoken_is_wordlike": (len(first_sub) >= 2 and first_sub.isalpha()
                                           and not single[f" {W}"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--models", default=DEFAULT_MODELS)
    ap.add_argument("--codewords", default=DEFAULT_CODEWORDS)
    ap.add_argument("--concepts", default=DEFAULT_CONCEPTS)
    ap.add_argument("--out", default="outputs/boombness/concept_pair_screen.json")
    a = ap.parse_args()

    from transformers import AutoTokenizer
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    words = sorted(set([w.strip() for w in a.codewords.split(",") if w.strip()]
                       + [w.strip() for w in a.concepts.split(",") if w.strip()]))
    per_model = {}
    for m in models:
        try:
            tok = AutoTokenizer.from_pretrained(m)
        except Exception as e:                       # noqa: BLE001 — reported, never silent
            print(f"[screen] SKIP {m}: {type(e).__name__}: {str(e)[:90]}")
            continue
        per_model[m] = {w: screen(tok, w) for w in words}
        print(f"[screen] {m}: screened {len(words)} words")

    if not per_model:
        raise SystemExit("[screen] no tokenizer could be loaded; nothing was screened")

    def clean_on_all(w):
        return all(per_model[m][w]["space_single"] and per_model[m][w]["space_cap_single"]
                   for m in per_model)

    codewords = [w.strip() for w in a.codewords.split(",") if w.strip()]
    concepts = [w.strip() for w in a.concepts.split(",") if w.strip()]
    print(f"\n{'word':<10}{'role':<9}" + "".join(f"{os.path.basename(m)[:14]:<16}" for m in per_model)
          + "  verdict")
    for w in codewords + concepts:
        role = "codeword" if w in codewords else "concept"
        cells = ""
        for m in per_model:
            s = per_model[m][w]
            cells += f"{('  ' + str(s['n_single_token_variants']) + '/4  ' + ('cap✓' if s['space_cap_single'] else 'cap✗')):<16}"
        print(f"{w:<10}{role:<9}{cells}  {'CLEAN' if clean_on_all(w) else 'has a multi-token variant'}")

    good_cw = [w for w in codewords if clean_on_all(w)]
    good_cc = [w for w in concepts if clean_on_all(w)]
    pairs = []
    for cw, cc in itertools.product(good_cw, good_cc):
        # variant-count symmetry: unequal counts reintroduce the bomb-4-vs-carrot-1 bias
        sym = all(per_model[m][cw]["n_single_token_variants"]
                  == per_model[m][cc]["n_single_token_variants"] for m in per_model)
        pairs.append({"codeword": cw, "concept": cc, "variant_counts_symmetric": sym})
    sym_pairs = [p for p in pairs if p["variant_counts_symmetric"]]

    print(f"\n[screen] codewords clean on every model: {good_cw}")
    print(f"[screen] concepts  clean on every model: {good_cc}")
    print(f"[screen] {len(pairs)} clean pairs, of which {len(sym_pairs)} also have symmetric "
          f"variant counts (no readout bias to correct):")
    for p in sym_pairs[:12]:
        print(f"     {p['codeword']:<10} <-> {p['concept']}")
    if not sym_pairs:
        print("     none — a pair with asymmetric variant counts needs the whole-answer readout, "
              "which exists, but is a worse starting point than one that does not.")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"models": list(per_model), "per_model": per_model,
                   "clean_codewords": good_cw, "clean_concepts": good_cc,
                   "clean_pairs": pairs, "symmetric_pairs": sym_pairs,
                   "current_pair": {"codeword": "carrot", "concept": "bomb"},
                   "provenance": {"argv": sys.argv, "python": sys.executable}}, f, indent=1)
    print(f"[screen] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
