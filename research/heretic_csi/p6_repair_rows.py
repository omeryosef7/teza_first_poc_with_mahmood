#!/usr/bin/env python3
"""P6 repair-touched rows (review #3 finding 9). Banks are generated in the same deterministic order (same pools,
seed, preset), so row i of every ts116m_<cw>_bomb bank is the same family/condition/slot. A row is REPAIR-TOUCHED if,
after swapping the codeword back to 'basket' (whole-word, case-preserving, incl. plural), its full_prompt differs from
basket's row i — the only remaining difference is then the codeword's own pool repair (<cw>=<repl>).
Self-check: codewords WITHOUT their own repair must give 0 touched rows. Writes per-codeword touched prompt_ids
(the 'unrepaired rows only' sensitivity population) and counts."""
import json, os, re, sys
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
D = os.path.join(REPO, "data/boombness_prompts")


def swap(text, cw):
    def rep(m):
        w = m.group(0); base = "basket" + ("s" if w.lower().endswith("s") and w.lower() != cw else "")
        if w.isupper():
            return base.upper()
        return base.capitalize() if w[0].isupper() else base
    return re.sub(r"\b%ss?\b" % re.escape(cw), rep, text, flags=re.IGNORECASE)


def main(cws, out):
    ref = [json.loads(l) for l in open(os.path.join(D, "boombness_prompt_bank_ts116m_basket_bomb.jsonl"))]
    res = {}
    for cw in cws:
        rows = [json.loads(l) for l in open(os.path.join(D, f"boombness_prompt_bank_ts116m_{cw}_bomb.jsonl"))]
        assert len(rows) == len(ref)
        misalign = sum(1 for a, b in zip(rows, ref) if (a["family_id"], a["condition"], a["cell"]) != (b["family_id"], b["condition"], b["cell"]))
        touched = [a["prompt_id"] for a, b in zip(rows, ref) if swap(a["full_prompt"], cw) != b["full_prompt"]]
        resc = [a["prompt_id"] for a, b in zip(rows, ref) if a["cell"] == "C" and a["query_kind"] == "semantic_one_word"
                and int(a["n_examples"]) == 4 and a["bank_block"] == "cds_n4_sow" and swap(a["full_prompt"], cw) != b["full_prompt"]]
        res[cw] = {"n_rows": len(rows), "misaligned_rows": misalign, "n_touched": len(touched),
                   "n_touched_rescue_pop": len(resc), "touched_prompt_ids": touched}
        print(cw, misalign, len(touched), len(resc), flush=True)
    json.dump({"schema": "hcsi_p6_repair_rows/1", "rows": res}, open(out, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[2].split(","), sys.argv[1])
