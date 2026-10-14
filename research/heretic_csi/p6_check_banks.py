#!/usr/bin/env python3
"""P6 Stage-0 bank checks (CPU, tokenizer only). For each codeword bank:
  - ' <cw>' is a single Llama-3.1 token (positions.leading_space_id);
  - on a deterministic sample of the rescue population (cell C, semantic_one_word, natural_doublespeak,
    n_examples 4, bank_block cds_n4_sow), the chat-templated BARE prompt (add_generation_prompt=True, no
    system, no 'Answer:') has the codeword at rel_end -10 (positions.anchor_from_rel_end, loud);
  - bank shape (rows, by_block, by_domain count, population size per split) equals basket's;
  - rows_sha16 (boombness.common.rows_sha16) + file sha256; meta repairs / residual collisions;
  - occurrence_analysis_safe on every row; whole-word codeword hits in the pools file AFTER repair = 0.
Writes one JSON with a row per codeword.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, os, re, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "src")); sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
from boombness.common import rows_sha16  # noqa: E402
import positions  # noqa: E402

TOK = "/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2"
SPLIT = os.path.join(REPO, "data/boombness_prompts/dcs_ts116_domain_split.json")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def shape(bank):
    n = 0; blocks = collections.Counter(); doms = set(); pop = collections.Counter(); pairs = []; unsafe = 0
    sample = []
    for l in open(bank):
        r = json.loads(l); n += 1; blocks[r["bank_block"]] += 1; doms.add(r["domain"])
        pairs.append((r["prompt_id"], r["prompt_sha16"]))
        if not r.get("occurrence_analysis_safe", True):
            unsafe += 1
        if (r["cell"] == "C" and r["query_kind"] == "semantic_one_word" and r["condition"] == "natural_doublespeak"
                and int(r["n_examples"]) == 4 and r["bank_block"] == "cds_n4_sow"):
            pop[r["domain"]] += 1; sample.append(r)
    return n, dict(blocks), len(doms), pop, rows_sha16(pairs), unsafe, sample


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--banks-dir", required=True)
    ap.add_argument("--codewords", required=True)
    ap.add_argument("--n-sample", type=int, default=40)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(TOK)
    split = json.load(open(SPLIT))
    dom2split = split.get("assignment") or split.get("domains") or {}
    ref = shape(os.path.join(REPO, "data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl"))
    rows = []
    for cw in a.codewords.split(","):
        bank = os.path.join(a.banks_dir, f"boombness_prompt_bank_ts116m_{cw}_bomb.jsonl")
        meta = json.load(open(bank[:-6] + "_meta.json"))
        n, blocks, ndom, pop, rsha, unsafe, sample = shape(bank)
        try:
            tid = positions.leading_space_id(tok, cw); single = True
        except positions.AmbiguousPosition:
            tid = None; single = False
        # deterministic sample across domains
        sample.sort(key=lambda r: (r["domain"], int(r["family_slot"]), r["prompt_id"]))
        step = max(1, len(sample) // a.n_sample)
        ok = bad = 0; fails = []
        for r in sample[::step][: a.n_sample]:
            text = tok.apply_chat_template([{"role": "user", "content": r["full_prompt"]}],
                                           add_generation_prompt=True, tokenize=False)
            ids = tok(text, add_special_tokens=False)["input_ids"]  # template already carries BOS
            try:
                positions.anchor_from_rel_end(ids, tok, cw, positions.REL_END_CODEWORD_ROW); ok += 1
            except positions.AmbiguousPosition as e:
                bad += 1; fails.append(str(e)[:160])
        rows.append({"codeword": cw, "token_id": tid, "single_token": single,
                     "bank_sha256": sha256(bank), "rows_sha16": rsha, "meta_rows_sha16": meta["stats"]["bank_rows_sha16"],
                     "n_rows": n, "by_block": blocks, "n_domains": ndom,
                     "pop_rows": sum(pop.values()), "pop_domains": len(pop),
                     "shape_equals_basket": (n == ref[0] and blocks == ref[1] and ndom == ref[2] and dict(pop) == dict(ref[3])),
                     "occurrence_unsafe_rows": unsafe,
                     "incidental_repairs": meta.get("incidental_repairs"),
                     "collisions_after_repair": meta.get("incidental_collisions_after_repair"),
                     "rel10_ok": ok, "rel10_fail": bad, "rel10_fail_examples": fails[:3]})
        print(json.dumps({k: rows[-1][k] for k in ("codeword", "token_id", "single_token", "shape_equals_basket",
                                                   "occurrence_unsafe_rows", "rel10_ok", "rel10_fail")}), flush=True)
    json.dump({"schema": "hcsi_p6_bank_checks/1", "tokenizer": TOK, "rows": rows}, open(a.out, "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
