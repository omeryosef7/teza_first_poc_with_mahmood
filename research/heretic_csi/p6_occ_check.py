#!/usr/bin/env python3
"""P6 FULL occurrence-count check (review #3 finding 4): run the EXACT pre-flight gate the extractor and
score_behavior use — extract_boombness.resolve_occurrences(ds_common, tokenizer, row) — over EVERY row of a bank.
A row fails if the tokenizer-level occurrence count != the generator's recorded n_target_occurrences (e.g. 'bottled'
matched at token level but not counted by the generator's whole-word regex), or any other ValueError it raises.
Output: per bank, counts by failure reason, split by population (all / extractor pop = behavioral n4 train+val /
rescue pop = C semantic_one_word n4 cds_n4_sow, by split), and the failing prompt_ids.
"""
from __future__ import annotations
import argparse, collections, json, os, sys
from multiprocessing import Pool

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "src", "boombness")); sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))
TOK = "/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2"
SPLIT = json.load(open(os.path.join(REPO, "data/boombness_prompts/dcs_ts116_domain_split.json")))

_tok = _dc = _res = None


def _init():
    global _tok, _dc, _res
    from transformers import AutoTokenizer
    import ds_common
    from extract_boombness import resolve_occurrences
    _tok = AutoTokenizer.from_pretrained(TOK); _dc = ds_common; _res = resolve_occurrences


def dom_split(d):
    a = SPLIT.get("assign") or {}
    if isinstance(a, dict) and d in a:
        return a[d]
    for k in ("train", "validation", "test"):
        if d in (SPLIT.get(k) or SPLIT.get("splits", {}).get(k, [])):
            return k
    return "excluded"


def check(path):
    cw = os.path.basename(path).split("_ts116m_")[1].rsplit("_bomb", 1)[0]
    by = collections.Counter(); fails = []
    n = 0
    for l in open(path):
        r = json.loads(l); n += 1
        try:
            _res(_dc, _tok, r, enable_thinking=None)
        except ValueError as e:
            reason = str(e).split(":")[0]
            ext = r["query_kind"] == "behavioral" and int(r["n_examples"]) == 4 and dom_split(r["domain"]) in ("train", "validation") and r["cell"] == "C"
            res = (r["cell"] == "C" and r["query_kind"] == "semantic_one_word" and int(r["n_examples"]) == 4
                   and r["bank_block"] == "cds_n4_sow")
            sp = dom_split(r["domain"])
            by[reason] += 1
            fails.append({"prompt_id": r["prompt_id"], "reason": str(e)[:120], "cell": r["cell"], "query_kind": r["query_kind"],
                          "n_examples": r["n_examples"], "block": r["bank_block"], "domain": r["domain"], "split": sp,
                          "extractor_pop": ext, "rescue_pop": res})
    return {"codeword": cw, "n_rows": n, "n_fail": len(fails), "by_reason": dict(by),
            "n_fail_extractor_pop": sum(f["extractor_pop"] for f in fails),
            "n_fail_rescue_pop": sum(f["rescue_pop"] for f in fails),
            "n_fail_rescue_pop_by_split": dict(collections.Counter(f["split"] for f in fails if f["rescue_pop"])),
            "fails": fails}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--banks", nargs="+", required=True)
    ap.add_argument("--procs", type=int, default=16)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with Pool(a.procs, initializer=_init) as p:
        res = p.map(check, a.banks, chunksize=1)
    for r in res:
        print(json.dumps({k: r[k] for k in r if k != "fails"}), flush=True)
    json.dump({"schema": "hcsi_p6_occ_check/1", "gate": "extract_boombness.resolve_occurrences (pre-flight of extractor + score_behavior)",
               "rows": res}, open(a.out, "w"), indent=1)
    print("DONE_MARKER p6_occ_check n_banks=%d" % len(res))


if __name__ == "__main__":
    main()
