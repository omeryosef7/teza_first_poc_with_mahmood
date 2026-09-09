#!/usr/bin/env python3
"""CPU preflight for the C -> A aggressive patch (successor plan sections 13, 14).

Mandate discipline: PROVE THE ARM IS CONSTRUCTIBLE BEFORE SPENDING GPU. This checks, on the real
tokenizer and the real bank, every precondition `aggressive_patching.run_pair` will check per row
under `align_mode="end_relative"`, over the WHOLE population rather than a sample -- so "how many
families can this arm actually bind" is a number and not a hope.

WHAT IT CHECKS, one line per failure mode, because each one failing produces a DIFFERENT wrong
answer rather than a shared "misaligned":
  P1  donor (cell C) and recipient (cell A) exist for the same family_id
  P2  both are at least END_RELATIVE_SHARED_SUFFIX tokens long
  P3  the last END_RELATIVE_SHARED_SUFFIX token ids are IDENTICAL on both sides
  P4  the final target occurrence sits at the SAME end-relative offset on both sides
  P5  that offset lies inside the verified suffix
  P6  the token at the patch position is the SAME TOKEN ID on both sides (the lexical control that
      makes this a counterfactual about context and not about which word is there)
  P7  the target occurrence is ONE subtoken on both sides
  P8  donor and recipient differ ONLY in the demonstration block -- preamble and final_query_text
      byte-identical -- so the transplant is not carrying a different question

It also reports the token-length delta distribution, which is the reason the historical
`absolute` alignment cannot be used for this pair.

USAGE
  python scripts/dcs_succ_pr068_preflight.py --split train
  python scripts/dcs_succ_pr068_preflight.py --split train --limit 40
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in ("scripts", os.path.join("src", "boombness"), "doublespeak_causality"):
    _f = os.path.join(REPO, _p)
    if _f not in sys.path:
        sys.path.insert(0, _f)

EXCLUDED_DOMAINS = ("restaurant_kitchen", "school_campus", "subway_station")
SPLIT_MANIFEST = os.path.join(REPO, "data/boombness_prompts/dcs_ts116_domain_split.json")
DONOR_CELL, RECIP_CELL = "C", "A"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", default=os.path.join(
        REPO, "data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl"))
    ap.add_argument("--query-kind", default="semantic_one_word")
    ap.add_argument("--n-examples", type=int, default=4)
    ap.add_argument("--split", default="train")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--revision", default="0e9e39f249a16976918f6564b8830bc894c89659")
    ap.add_argument("--out", default=os.path.join(REPO, "outputs/dcs_succ/pr068_preflight.json"))
    a = ap.parse_args()

    from transformers import AutoTokenizer
    import ds_common as dc
    import aggressive_patching as AP

    S = AP.END_RELATIVE_SHARED_SUFFIX
    tok = AutoTokenizer.from_pretrained(a.model, revision=a.revision)

    assign = json.load(open(SPLIT_MANIFEST, encoding="utf-8"))["assign"]
    keep = {d for d, s in assign.items() if s == a.split} - set(EXCLUDED_DOMAINS)
    if not keep:
        print("REFUSING: split %r selects no domain" % a.split, file=sys.stderr)
        return 2

    by_family = collections.defaultdict(dict)
    with open(a.bank, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if (r["query_kind"] != a.query_kind or int(r["n_examples"]) != a.n_examples
                    or r["domain"] not in keep or r["cell"] not in (DONOR_CELL, RECIP_CELL)):
                continue
            by_family[r["family_id"]][r["cell"]] = r

    fams = sorted(f for f, d in by_family.items() if DONOR_CELL in d and RECIP_CELL in d)
    if a.limit:
        fams = fams[:a.limit]
    if not fams:
        print("REFUSING: no family binds both cells -- an empty preflight is not a passed "
              "preflight", file=sys.stderr)
        return 2

    fails = collections.Counter()
    deltas, rels, domains_ok = [], collections.Counter(), set()
    n_ok = 0
    for f in fams:
        d_row, r_row = by_family[f][DONOR_CELL], by_family[f][RECIP_CELL]
        try:
            d_text, d_ids, d_last, _, d_nsub = AP.resolve_occurrences(dc, tok, d_row)
            r_text, r_ids, r_last, _, r_nsub = AP.resolve_occurrences(dc, tok, r_row)
        except Exception as e:                        # noqa: BLE001
            fails["P1_resolve:%s" % type(e).__name__] += 1
            continue
        deltas.append(len(d_ids) - len(r_ids))
        ok = True
        if len(d_ids) < S or len(r_ids) < S:
            fails["P2_shorter_than_suffix"] += 1; ok = False
        elif list(d_ids[-S:]) != list(r_ids[-S:]):
            fails["P3_suffix_differs"] += 1; ok = False
        if ok:
            d_rel, r_rel = d_last[-1] - len(d_ids), r_last[-1] - len(r_ids)
            if d_rel != r_rel:
                fails["P4_rel_end_differs"] += 1; ok = False
            elif r_rel < -S:
                fails["P5_outside_verified_suffix"] += 1; ok = False
            else:
                rels[r_rel] += 1
                if d_ids[d_last[-1]] != r_ids[r_last[-1]]:
                    fails["P6_patch_token_identity_differs"] += 1; ok = False
        if any(n != 1 for n in d_nsub + r_nsub):
            fails["P7_multi_subtoken_target"] += 1; ok = False
        if d_row["preamble"] != r_row["preamble"]:
            fails["P8_preamble_differs"] += 1; ok = False
        if d_row["final_query_text"] != r_row["final_query_text"]:
            fails["P8_final_query_differs"] += 1; ok = False
        if d_row["demo_block"] == r_row["demo_block"]:
            # If the demonstration blocks were EQUAL the pair would not be a manipulation at all.
            fails["P8_demo_block_IDENTICAL_no_manipulation"] += 1; ok = False
        if ok:
            n_ok += 1
            domains_ok.add(r_row["domain"])

    res = {"_label": "CPU PREFLIGHT for the C->A end-relative patch. No GPU, no model weights.",
           "bank": os.path.relpath(a.bank, REPO), "split": a.split,
           "query_kind": a.query_kind, "n_examples": a.n_examples,
           "shared_suffix_required": S, "constructible_scopes": list(AP.END_RELATIVE_SCOPES),
           "n_families_examined": len(fams), "n_families_constructible": n_ok,
           "n_domains_constructible": len(domains_ok),
           "failures": dict(fails),
           "token_length_delta_donor_minus_recipient": {
               "n": len(deltas), "mean": round(statistics.mean(deltas), 3) if deltas else None,
               "median": statistics.median(deltas) if deltas else None,
               "min": min(deltas) if deltas else None, "max": max(deltas) if deltas else None,
               "frac_equal": round(sum(1 for x in deltas if x == 0) / len(deltas), 4)
               if deltas else None,
               "_why_this_matters": "the historical `absolute` alignment asserts this is 0. It is "
                                    "not, which is exactly why this pair needs end-relative "
                                    "correspondence and why running it under the old assertion "
                                    "would have ledgered every row as a length mismatch."},
           "patch_position_rel_end_histogram": {str(k): v for k, v in sorted(rels.items())}}

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))
    return 0 if n_ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
