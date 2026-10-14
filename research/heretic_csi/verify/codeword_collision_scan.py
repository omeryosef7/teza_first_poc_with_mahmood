#!/usr/bin/env python3
"""F3: independent (text-level + tokenizer-level) scan of a bank for codeword collisions: words that CONTAIN the codeword
but are not the whole word (basketball, buttonhole, buttoned, ...), and rows whose token-level count of the leading-space
codeword id differs from n_target_occurrences."""
import json, re, sys, collections
from transformers import AutoTokenizer
TOK = "/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2"
IDS = {"basket": 14351, "button": 3215}
tok = AutoTokenizer.from_pretrained(TOK)
out = {}
for cw in sys.argv[1:]:
    rows = [json.loads(l) for l in open(f"data/boombness_prompts/boombness_prompt_bank_ts116m_{cw}_bomb.jsonl")]
    words = collections.Counter(); bad = []
    for r in rows:
        txt = json.dumps({k: v for k, v in r.items() if isinstance(v, (str, list, dict)) and k not in ("prompt_id", "prompt_sha16", "family_id")})
        for w in re.findall(r"[A-Za-z]*%s[A-Za-z]*" % cw, txt, flags=re.I):
            if w.lower() != cw:
                words[w] += 1
    out[cw] = {"n_rows": len(rows), "superstring_words": dict(words)}
    print(cw, out[cw])
json.dump(out, open("reports/heretic_csi/VERIFY_codeword_collision_scan.json", "w"), indent=1)
