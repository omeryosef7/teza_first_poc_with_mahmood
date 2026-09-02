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
    ap.add_argument("--all-cells", action="store_true",
                    help="emit ALL FOUR core-2x2 rows of --prompt-id's family in one document, "
                         "in the fixed order A, B, C, E. The shared preamble and the shared "
                         "explanation are then written once and referenced, so what differs is "
                         "not buried under four repetitions of what does not.")
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

    ORDER = ("benign_literal", "direct_harmful", "natural_doublespeak", "concept_in_benign_ctx")
    rows_out = [row]
    if a.all_cells:
        fam = {}
        for line in open(a.bank, encoding="utf-8"):
            r = json.loads(line)
            if r.get("family_id") == row["family_id"] and r.get("condition") in ORDER:
                fam[r["condition"]] = r
        missing = [c for c in ORDER if c not in fam]
        if missing:
            raise SystemExit(f"REFUSING: family {row['family_id']} is missing {missing}. A partial "
                             f"2x2 would show a contrast that does not exist.")
        rows_out = [fam[c] for c in ORDER]

    render = None
    if not a.no_template:
        import sys
        sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
        from transformers import AutoTokenizer
        from common import ds
        tok, dc = AutoTokenizer.from_pretrained(a.model), ds()
        render = lambda r: dc.apply_template(tok, r["full_prompt"], enable_thinking=None)

    L = []
    W = L.append
    multi = len(rows_out) > 1
    if multi:
        W("# The four core-2x2 prompts, each written out in full\n")
        W(f"One matched family — **domain `{row['domain']}`, split `{row['split']}`, "
          f"slot {row['family_slot']}**, dose n={row['n_examples']} — shown in all four cells.")
        W(f"Bank `{os.path.basename(a.bank)}`. Mapping under test: **`{row['codeword']}` → "
          f"`{row['concept']}`**.\n")
        W("**Prompts only — no model output appears in this document.**\n")
        W("| | query names the **CODEWORD** (`%s`) | query names the **CONCEPT** (`%s`) |"
          % (row["codeword"], row["concept"]))
        W("|---|---|---|")
        W("| **demos BENIGN** | A `benign_literal` | E `concept_in_benign_ctx` |")
        W("| **demos HARMFUL** | **C `natural_doublespeak`** ⬅ ATTACK | B `direct_harmful` |")
        W("")
        W(f"⚠ All four share the same domain, slot, split and the same "
          f"{row.get('n_preamble_lines')}-line neutral preamble. **Only the two factors differ.** "
          f"Each section below is complete and self-contained.\n")
        W("---\n")

    for _n, row in enumerate(rows_out, 1):
        templated = render(row) if render else None
        cell = CELL_LETTER.get(row["condition"], row.get("cell"))
        W((f"# {'Cell ' + cell} — `{row['condition']}`\n") if multi
              else "# One complete prompt, verbatim\n")
        # In multi mode the H1 already names the cell and the header already carries the
        # prompts-only notice; restating both per section is noise, not emphasis.
        if not multi:
            W(f"**Cell {cell} — `{row['condition']}`**, the attack condition."
              if row["condition"] == "natural_doublespeak" else
              f"**Cell {cell} — `{row['condition']}`**.")
        elif row["condition"] == "natural_doublespeak":
            W("⬅ **This is the attack condition.**")
        W(f"`prompt_id = {row['prompt_id']}`  ·  bank `{os.path.basename(a.bank)}`\n")
        if not multi:
            W("**Prompt only — no model output appears in this document.**\n")
        W("---\n")

        W("## {c}1. What this row is\n".replace("{c}", (cell + ".") if multi else ""))
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

        W("## {c}2. The prompt as assembled in the bank (`full_prompt`, verbatim)\n".replace("{c}", (cell + ".") if multi else ""))
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
            W("## {c}3. What the model is actually fed (after the chat template)\n".replace("{c}", (cell + ".") if multi else ""))
            W(f"`{a.model}`, {len(templated)} characters. ⚠ **Every span the analysis addresses — the "
              f"demonstration block, the protected query span, the token offsets the attention mask "
              f"edits — is resolved against THIS string, not against `full_prompt`.**\n")
            W("```text")
            W(templated)
            W("```\n")
            W("---\n")

        W("## {c}4. How this row is used\n".replace("{c}", (cell + ".") if multi else ""))
        W(f"* Scored with `--query-kinds behavioral --conditions {row['condition']} "
          f"--bank-blocks {row['bank_block']} --n-examples {row['n_examples']} --max-new 640`.")
        W(f"* Its arm's completion is judged by `openai/gpt-4o-mini` (pinned) for attack success, and by "
          f"a deterministic keyword detector for refusal.")
        W(f"* It contributes **one row** to domain `{row['domain']}`, which contributes **one cluster** "
          f"to the paired domain sign test that is the headline's primary statistic.")
        W(f"* In the intervention arms, the attention mask blocks the demonstration span above while the "
          f"model is processing it; the count-matched controls block the same NUMBER of positions drawn "
          f"from outside it.\n")

        if multi and _n < len(rows_out):
            W("---\n")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print("[tsc] " + ("all four cells of family " + rows_out[0]["family_id"] if len(rows_out) > 1
                      else f"prompt_id={rows_out[0]['prompt_id']} condition={rows_out[0]['condition']}"))
    print(f"[tsc] -> {a.out}  ({os.path.getsize(a.out)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
