#!/usr/bin/env python
"""tsc_show_one_prompt.py -- ONE prompt, complete, with every field that describes it.

FOR HANDING A SINGLE WORKED EXAMPLE TO A SUPERVISOR. `tsc_show_2x2_examples.py` shows the design;
this shows one row of it exhaustively -- the assembled prompt verbatim, the string the model is
actually fed after the chat template is applied, the exact character offsets of every target-word
occurrence, and the full bank record.

WHY THE TEMPLATED STRING IS INCLUDED. `full_prompt` is the bank's assembled text; it is NOT what the
model sees. `ds_common.apply_template` wraps it in the model's chat format, and every span the
analysis addresses -- the demonstration block, the query span, the token offsets the attention mask
edits -- is resolved against the TEMPLATED string, not the raw one. A worked example that shows only
`full_prompt` would misrepresent what the intervention operates on.

⛔ PROMPTS ONLY. Never opens `gens.jsonl`; no model output appears.
"""
from __future__ import annotations
import argparse, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELL_LETTER = {"benign_literal": "A", "direct_harmful": "B",
               "natural_doublespeak": "C", "concept_in_benign_ctx": "E"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=os.path.join(
        ROOT, "data/boombness_prompts/boombness_prompt_bank_cds38_button_bomb.jsonl"))
    ap.add_argument("--prompt-id", default="8539d5d09bb588be",
                    help="default: the natural_doublespeak (attack) row of the worked family")
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--no-template", action="store_true",
                    help="skip the chat-templated rendering (avoids loading a tokenizer)")
    ap.add_argument("--out", default=os.path.join(ROOT, "reports/TSC_ONE_PROMPT_FULL_EXAMPLE.md"))
    a = ap.parse_args()

    row = None
    for line in open(a.bank, encoding="utf-8"):
        r = json.loads(line)
        if r["prompt_id"] == a.prompt_id:
            row = r
            break
    if row is None:
        raise SystemExit(f"REFUSING: prompt_id {a.prompt_id} not in {a.bank}")

    templated = None
    if not a.no_template:
        import sys
        sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
        from transformers import AutoTokenizer
        from common import ds
        tok = AutoTokenizer.from_pretrained(a.model)
        templated = ds().apply_template(tok, row["full_prompt"], enable_thinking=None)

    cell = CELL_LETTER.get(row["condition"], row.get("cell"))
    L = []
    W = L.append
    W(f"# One complete prompt, verbatim\n")
    W(f"**Cell {cell} — `{row['condition']}`**, the attack condition."
      if row["condition"] == "natural_doublespeak" else
      f"**Cell {cell} — `{row['condition']}`**.")
    W(f"`prompt_id = {row['prompt_id']}`  ·  bank `{os.path.basename(a.bank)}`\n")
    W("**Prompt only — no model output appears in this document.**\n")
    W("---\n")

    W("## 1. What this row is\n")
    W("| field | value | what it means |")
    W("|---|---|---|")
    meaning = {
        "prompt_id": "sha256(family_id\\|condition)[:16] — stable across banks, so it is NOT proof of which bank a row came from",
        "prompt_sha16": "sha256 of the assembled `full_prompt` — this one IS text-specific",
        "family_id": "the 2×2 stem: all four conditions of this family share it",
        "cell": "position in the 2×2",
        "condition": "which of the four cells",
        "domain": "the narrative setting the demonstrations come from — **the independence unit of the analysis**",
        "split": "which disjoint half of the 40-sentence pool the demos were drawn from (**not** a train/test split)",
        "family_slot": "which non-overlapping slice of that half — slots 0/4/8/12/16 partition the 20 sentences",
        "n_examples": "demonstration dose",
        "demo_valence": "benign or harm — **2×2 factor 1**",
        "demo_surface": "which word the demonstrations use",
        "query_surface": "which word the final question uses — **2×2 factor 2**",
        "target_surface": "the word whose occurrences are counted",
        "target_semantic": "what that word is taken to mean here",
        "codeword": "the innocuous surface word",
        "concept": "the harmful referent the demonstrations map it onto",
        "n_target_occurrences": "occurrences of the target word — held EQUAL across the four cells so per-occurrence analyses compare like with like",
        "n_preamble_lines": "neutral filler lines prepended; they exist so a count-matched control has somewhere to draw from",
        "bank_block": "which generator block emitted the row",
        "query_kind": "which query template — `behavioral` is the one scored for ASR",
        "occurrence_analysis_safe": "whether per-occurrence analysis is valid for this row",
        "scores": "what this row is scored with",
        "n_chars": "length of `full_prompt`",
    }
    for k in ("prompt_id", "prompt_sha16", "family_id", "cell", "condition", "domain", "split",
              "family_slot", "n_examples", "demo_valence", "demo_surface", "query_surface",
              "target_surface", "target_semantic", "codeword", "concept", "n_target_occurrences",
              "n_preamble_lines", "bank_block", "query_kind", "occurrence_analysis_safe",
              "scores", "n_chars"):
        if k in row:
            # `family_id` is pipe-delimited, so an unescaped value SPLITS THE TABLE CELL and the
            # row renders as nine columns of garbage. Escape before emitting, not after noticing.
            val = str(row[k]).replace("|", "\\|")
            W(f"| `{k}` | `{val}` | {meaning.get(k,'')} |")
    W("")
    W(f"⚠ **Read the two factor rows together:** `demo_valence={row['demo_valence']}` with "
      f"`query_surface={row['query_surface']}` is what makes this cell {cell}. "
      + ("The demonstrations give the codeword a harmful character and the question then asks about "
         "the **codeword**, so the request contains no harmful word at all.\n"
         if row["condition"] == "natural_doublespeak" else "\n"))
    W("---\n")

    W("## 2. The prompt as assembled in the bank (`full_prompt`, verbatim)\n")
    W(f"{row['n_chars']} characters. This is the bank's text — **not yet** what the model receives.\n")
    W("```text")
    W(row["full_prompt"])
    W("```\n")

    W("### Its three parts, separately\n")
    if row.get("preamble"):
        W(f"**a) Preamble** — {row['n_preamble_lines']} neutral filler lines, byte-identical across "
          f"all four cells of this family. ⚠ This is the span the count-matched control arms draw "
          f"their masked positions from (measured: 98–99.8 % of drawn keys land here).\n")
        W("```text"); W(row["preamble"].rstrip()); W("```\n")
    W(f"**b) Demonstrations** — {row['n_demos_emitted']} sentences, valence `{row['demo_valence']}`, "
      f"surface `{row['demo_surface']}`, from pool `{row['demo_pool_domain']}|{row['demo_valence']}`, "
      f"split `{row['split']}`, slot {row['family_slot']}. ⚠ **This is the span the intervention "
      f"masks** (`--knockout-scope demo_processing_only`).\n")
    W("```text"); W(row["demo_block"].rstrip()); W("```\n")
    W(f"**c) Final query** — surface `{row['query_surface']}`. ⚠ Identical on all 380 rows of this "
      f"bank; the request never varies, which is why the 38 domains are 38 *demonstration pools* "
      f"and not 38 behaviours.\n")
    W("```text"); W(row["final_query_text"].rstrip()); W("```\n")

    occ = row.get("expected_target_occurrences") or []
    if occ:
        W(f"### Where the target word occurs\n")
        W(f"`{row['target_surface']}` occurs **{row['n_target_occurrences']}×** in `full_prompt`, at "
          f"these character spans — the positions the occurrence-alignment audit checks:\n")
        W("| # | span | text at that span |")
        W("|---|---|---|")
        for i, (lo, hi) in enumerate(occ, 1):
            W(f"| {i} | `[{lo}, {hi})` | `{row['full_prompt'][lo:hi]}` |")
        W("")
    W("---\n")

    if templated is not None:
        W("## 3. What the model is actually fed (after the chat template)\n")
        W(f"`{a.model}`, {len(templated)} characters. ⚠ **Every span the analysis addresses — the "
          f"demonstration block, the protected query span, the token offsets the attention mask "
          f"edits — is resolved against THIS string, not against `full_prompt`.**\n")
        W("```text")
        W(templated)
        W("```\n")
        W("---\n")

    W("## 4. How this row is used\n")
    W(f"* Scored with `--query-kinds behavioral --conditions {row['condition']} "
      f"--bank-blocks {row['bank_block']} --n-examples {row['n_examples']} --max-new 640`.")
    W(f"* Its arm's completion is judged by `openai/gpt-4o-mini` (pinned) for attack success, and by "
      f"a deterministic keyword detector for refusal.")
    W(f"* It contributes **one row** to domain `{row['domain']}`, which contributes **one cluster** "
      f"to the paired domain sign test that is the headline's primary statistic.")
    W(f"* In the intervention arms, the attention mask blocks the demonstration span above while the "
      f"model is processing it; the count-matched controls block the same NUMBER of positions drawn "
      f"from outside it.\n")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"[tsc] prompt_id={row['prompt_id']} cell={cell} condition={row['condition']}")
    print(f"[tsc] -> {a.out}  ({os.path.getsize(a.out)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
