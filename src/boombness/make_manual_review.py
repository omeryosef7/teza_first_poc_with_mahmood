"""make_manual_review.py — plan §4.2: `data/boombness_prompts/manual_review_50.md`.

A stratified 50-row sample of the bank, rendered for a human to read. Stratification is over
(bank_block, condition) so the sample cannot be all one arm, and each matched 2x2 family is
kept together so the exact-swap alignment is visible on the page rather than asserted in a log.

The file contains prompt TEXT, so it is a benchmark artifact, not stdout: written to the data
directory, never echoed. Generated in the MAIN loop, never a subagent.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, read_jsonl  # noqa: E402

BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")
OUT = os.path.join(DATA_DIR, "manual_review_50.md")

CORE = ("benign_literal", "direct_harmful", "natural_doublespeak", "concept_in_benign_ctx")
CELL_NOTE = {
    "A": "benign demos, codeword surface — the benign-literal baseline",
    "B": "harm demos, concept surface — the direct-harmful reference",
    "C": "harm demos, codeword surface — natural doublespeak (the attack)",
    "E": "benign demos, concept surface — hard negative: concept token, no harmful context",
    "D": "mapping STATED rather than demonstrated",
    "F": "benign remap control — structure and remapping present, meaning harmless",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=BANK)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260816)
    args = ap.parse_args()

    rows = read_jsonl(args.bank)
    rng = random.Random(args.seed)
    by_family = collections.defaultdict(dict)
    for r in rows:
        by_family[r["family_id"]][r["condition"]] = r

    # Prefer complete 2x2 families (4 rows each) so alignment is visible side by side.
    complete = [f for f, d in by_family.items() if set(CORE).issubset(d)]
    rng.shuffle(complete)
    picked, n = [], 0
    for f in complete:
        if n + 4 > args.n:
            break
        picked.append(("family", f))
        n += 4
    # Fill the remainder with single rows from the non-core blocks, one per (block, condition).
    others = [r for r in rows if r["bank_block"] != "core2x2"]
    seen = set()
    rng.shuffle(others)
    for r in others:
        k = (r["bank_block"], r["condition"], r["strength"], r["consistency"],
             r["example_position"], r["role_style"])
        if k in seen or n >= args.n:
            continue
        seen.add(k)
        picked.append(("single", r))
        n += 1

    meta = json.load(open(args.bank.replace(".jsonl", "_meta.json")))
    L = []
    L.append("# Boombness prompt bank — manual review sample\n")
    L.append(f"Plan §4.2. Stratified sample of {n} rows from `{os.path.relpath(args.bank)}` "
             f"({len(rows)} rows total), seed {args.seed}.\n")
    L.append(f"Pools sha16 `{meta['pools_sha16']}` · 2×2 families checked "
             f"{meta['stats']['n_2x2_families_checked']} · alignment violations "
             f"{meta['stats']['n_alignment_violations']}.\n")
    L.append("**What to check when reading this:** (1) within a family the four core cells "
             "differ *only* by the target word and the demo block's valence; (2) the final query "
             "sentence is identical across all four except for that word; (3) the demo sentences "
             "never start with the target word (single-token requirement, see progress log F4); "
             "(4) nothing here is operational content — the harm arm is topic-level only.\n")
    L.append("---\n")

    for kind, item in picked:
        if kind == "family":
            fam = by_family[item]
            head = fam[CORE[0]]
            L.append(f"\n## Family `{item}`\n")
            L.append(f"domain **{head['domain']}** · split **{head['split']}** · "
                     f"n_examples **{head['n_examples']}** · strength **{head['strength']}** · "
                     f"consistency **{head['consistency']}** · position **{head['example_position']}** · "
                     f"role **{head['role_style']}** · query **{head['query_kind']}**\n")
            for cond in CORE:
                r = fam[cond]
                L.append(f"\n### cell {r['cell']} — `{cond}`\n")
                L.append(f"*{CELL_NOTE[r['cell']]}* · target `{r['target_surface']}` · "
                         f"{r['n_target_occurrences']} occurrences · {r['n_chars']} chars\n")
                L.append("```text\n" + r["full_prompt"] + "\n```\n")
        else:
            r = item
            L.append(f"\n## Single row — block `{r['bank_block']}`, cell {r['cell']} "
                     f"(`{r['condition']}`)\n")
            L.append(f"domain **{r['domain']}** · n_examples **{r['n_examples']}** · "
                     f"strength **{r['strength']}** · consistency **{r['consistency']}** · "
                     f"position **{r['example_position']}** · role **{r['role_style']}** · "
                     f"query **{r['query_kind']}** · target `{r['target_surface']}` · "
                     f"{r['n_target_occurrences']} occurrences\n")
            L.append("```text\n" + r["full_prompt"] + "\n```\n")

    with open(args.out, "w") as f:
        f.write("\n".join(L))
    print(f"[manual_review] {n} rows ({len(picked)} entries) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
