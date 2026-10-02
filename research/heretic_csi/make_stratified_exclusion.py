#!/usr/bin/env python3
"""Make a domain-stratified exclusion file that keeps only K rows per domain for the cell-C
semantic_one_word rescue population — a DECLARED power/feasibility trade-off for the remaining ranks
(~517s/arm at the full 10 rows/domain is too heavy for a 6-rank x 2-codeword sweep).

It reuses score_behavior's `--exclude-prompt-ids` mechanism (no bank edit): the output = the base SOW
exclusion UNION {population prompt_ids beyond the first K per domain}. "First K" is a DETERMINISTIC
sort by (split, family_slot, prompt_id) so the kept subset is reproducible and balanced across the
dev/heldout sub-splits. The domain split (train/val/test) is still applied downstream by the analyzer;
this only thins rows WITHIN each domain, so every domain remains represented.

Usage:
  python make_stratified_exclusion.py --codeword basket --keep-per-domain 4 \
    --out runargs/heretic_csi/exclude_basket_K4.txt
"""
from __future__ import annotations
import argparse, json, os
from collections import defaultdict

ROOT = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--keep-per-domain", type=int, required=True)
    ap.add_argument("--bank", default=None)
    ap.add_argument("--base-exclusion", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bank = a.bank or f"{ROOT}/data/boombness_prompts/boombness_prompt_bank_ts116m_{a.codeword}_bomb.jsonl"
    base = a.base_exclusion or f"{ROOT}/runargs/dcs_cont/exclude_{a.codeword}_bomb_sow_train.txt"

    base_ids = []
    for l in open(base):
        s = l.strip()
        if s and not s.startswith("#"):
            base_ids.append(s)
    base_set = set(base_ids)

    # population rows (same filter score_behavior applies), not already excluded
    by_dom = defaultdict(list)
    for l in open(bank):
        r = json.loads(l)
        if (r.get("cell") == "C" and r.get("query_kind") == "semantic_one_word"
                and r.get("condition") == "natural_doublespeak" and r.get("n_examples") == 4
                and r.get("prompt_id") not in base_set):
            by_dom[r["domain"]].append(r)

    extra_excl = []
    kept = 0
    for dom, rows in by_dom.items():
        rows.sort(key=lambda r: (str(r.get("split")), int(r.get("family_slot", 0)), r.get("prompt_id")))
        keep = rows[:a.keep_per_domain]
        drop = rows[a.keep_per_domain:]
        kept += len(keep)
        extra_excl += [r["prompt_id"] for r in drop]

    all_excl = base_ids + extra_excl
    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)) if not os.path.isabs(a.out) else os.path.dirname(a.out), exist_ok=True)
    outp = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    with open(outp, "w") as fh:
        fh.write(f"# HERETIC-CSI domain-stratified exclusion: base SOW exclusion + rows beyond K={a.keep_per_domain}/domain\n")
        fh.write(f"# base: {base}\n# bank: {bank}\n")
        fh.write(f"# kept {kept} rows across {len(by_dom)} domains (~{a.keep_per_domain}/domain); "
                 f"base_excl={len(base_ids)} extra_excl={len(extra_excl)} total_excl={len(all_excl)}\n")
        fh.write("# DECLARED power trade-off: fewer rows/domain => noisier domain means; domain remains the unit.\n")
        for pid in all_excl:
            fh.write(pid + "\n")
    print(f"codeword={a.codeword} K={a.keep_per_domain} kept={kept} domains={len(by_dom)} "
          f"extra_excl={len(extra_excl)} total_excl={len(all_excl)} -> {outp}")


if __name__ == "__main__":
    main()
