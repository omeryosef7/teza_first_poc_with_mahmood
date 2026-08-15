"""Phase 10 (plan §14.1): build a SECOND doublespeak corpus from AdvBench.

Independent-replication corpus for behavioral power. Reuses the locked clearharm
pipeline verbatim (build_doublespeak_split.build_item / get_demos / codeword
lexicon / single-token filter / _llm_pick_concept) but swaps the SOURCE to the
public AdvBench harmful_behaviors.csv and produces a leakage-0 3-way split
(train/dev/test) that is BOTH concept-disjoint and codeword-disjoint. Not pooled
with ClearHarm; treated as a separate replication (§14.1).

The concept-extraction (a single-token harmful noun that appears verbatim in the
goal) is CACHED per instruction hash to _advbench_concept_cache.json, so the split
is reproducible. Records the AdvBench source sha256 in _meta.

Harmful text is handled here in the main process only (never delegated to a
subagent). Output: data/splits/advbench_doublespeak_v1.json.

    python scripts/build_advbench_doublespeak.py --no-api --smoke 4   # structural smoke
    python scripts/build_advbench_doublespeak.py --seed 7             # full build (OpenAI)
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
ROOT = os.path.dirname(DC)
sys.path.insert(0, HERE)
sys.path.insert(0, DC)

import ds_common  # noqa: E402
import build_doublespeak_split as B  # noqa: E402  (reuse the locked pipeline)

ADVBENCH_CSV = os.path.join(ROOT, "llm-attacks", "data", "advbench", "harmful_behaviors.csv")
CONCEPT_CACHE = os.path.join(DC, "data", "splits", "_advbench_concept_cache.json")
OUT = os.path.join(DC, "data", "splits", "advbench_doublespeak_v1.json")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_advbench_concepts(tok, client, model, use_api, limit):
    """Twin of build_doublespeak_split.extract_clearharm_concepts, reading AdvBench's
    `goal` column. Same swap contract: concept is single-token AND appears verbatim."""
    ccache = json.load(open(CONCEPT_CACHE)) if os.path.exists(CONCEPT_CACHE) else {}
    rows = list(csv.DictReader(open(ADVBENCH_CSV)))
    out, dirty = [], False
    for row in rows:
        instr = (row.get("goal") or "").strip()
        if not instr:
            continue
        concept = None
        if use_api:
            ckey = B.sha16(instr)
            if ckey in ccache:
                concept = ccache[ckey]
            else:
                concept = B._llm_pick_concept(client, model, instr)
                ccache[ckey] = concept
                dirty = True
        else:
            cands = sorted({w.strip(".,;:'\"()").lower() for w in instr.split() if w.isalpha()},
                           key=len, reverse=True)
            for w in cands:
                if len(w) >= 4 and B.is_single_token(tok, w) and w in instr.lower():
                    concept = w
                    break
        if not concept:
            continue
        # enforce the build_conditions swap contract: concept must appear verbatim
        if concept not in instr:
            low = instr.lower().find(concept.lower())
            if low < 0:
                continue
            concept = instr[low:low + len(concept)]
        if not B.is_single_token(tok, concept):
            continue
        aid = f"advbench_{B.sha16(instr)[:12]}"
        out.append({"clearharm_id": aid, "category": "advbench",
                    "intent_cluster": f"advbench::{concept.lower()}",
                    "instruction": instr, "concept": concept})
        if limit and len(out) >= limit:
            break
    if use_api and dirty:
        os.makedirs(os.path.dirname(CONCEPT_CACHE), exist_ok=True)
        json.dump(ccache, open(CONCEPT_CACHE, "w"), indent=1)
    return out


def assign_splits_leakage0(records, codewords, seed=7):
    """Leakage-0 3-way split: whole CONCEPT clusters go to exactly one split, and the
    codeword pool is partitioned into 3 DISJOINT sub-pools so a codeword seen in one
    split never appears in another (concept-disjoint AND codeword-disjoint). ~60/20/20
    over concept clusters, assigned deterministically by sorted concept hash."""
    concepts = sorted({r["target_concept"] for r in records})
    # deterministic shuffle by hash(concept, seed) so it is reproducible w/o RNG state
    def hkey(c):
        return hashlib.sha256(f"{seed}:{c}".encode()).hexdigest()
    concepts.sort(key=hkey)
    n = len(concepts)
    n_tr, n_dev = int(round(0.6 * n)), int(round(0.2 * n))
    split_of = {}
    for i, c in enumerate(concepts):
        split_of[c] = "train" if i < n_tr else ("dev" if i < n_tr + n_dev else "test")
    # disjoint codeword sub-pools per split
    cw = list(codewords)
    k = max(1, len(cw) // 5)
    pools = {"train": cw[:3 * k] or cw, "dev": cw[3 * k:4 * k] or cw, "test": cw[4 * k:] or cw}
    # assign one codeword per concept from its split's pool (round-robin)
    per_split_idx = {"train": 0, "dev": 0, "test": 0}
    concept_cw = {}
    for c in concepts:
        s = split_of[c]
        pool = pools[s]
        concept_cw[c] = pool[per_split_idx[s] % len(pool)]
        per_split_idx[s] += 1
    return split_of, concept_cw, pools


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-api", action="store_true")
    ap.add_argument("--smoke", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="max concepts to extract (0=all)")
    ap.add_argument("--num-demos", type=int, default=12)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--tokenizer", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    use_api = not args.no_api

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.tokenizer)
    client = None
    if use_api:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    demo_cache = json.load(open(B.DEMO_CACHE)) if os.path.exists(B.DEMO_CACHE) else {}
    cws = [w for w in B.CODEWORD_LEXICON if B.is_single_token(tok, w)]
    assert len(cws) >= 3, f"need >=3 single-token codewords, got {len(cws)}"

    items = extract_advbench_concepts(tok, client, args.model, use_api, args.limit or args.smoke)
    # one codeword per concept comes from the leakage-0 assignment; build a provisional
    # concept->split first (needs target_concept on the item), so stamp it now.
    for it in items:
        it["target_concept"] = it["concept"]
    split_of, concept_cw, pools = assign_splits_leakage0(items, cws, seed=args.seed)

    # index items by split so the shuffled/unrelated partner is a DIFFERENT concept in
    # the SAME split (fixes: (1) control-contamination if the CSV neighbor shares the
    # concept; (2) codeword leakage if the neighbor's codeword came from another split's
    # disjoint pool). A same-split partner guarantees wrong_cw is from split_of[c]'s pool.
    from collections import defaultdict
    idx_by_split = defaultdict(list)
    for j, jt in enumerate(items):
        idx_by_split[split_of[jt["concept"]]].append(j)

    records = []
    for i, it in enumerate(items):
        c = it["concept"]
        codeword = concept_cw[c]
        s = split_of[c]
        pool = idx_by_split[s]
        wrong = it  # degenerate fallback (single-concept split): build_item may assert-skip
        if len(pool) > 1:
            pos = pool.index(i)
            for step in range(1, len(pool)):
                cand = items[pool[(pos + step) % len(pool)]]
                if cand["concept"] != c:
                    wrong = cand
                    break
        wrong_cw = concept_cw.get(wrong["concept"], pools[s][0])
        if wrong_cw == codeword:
            # pick a different codeword from THIS split's pool only — never fall back to
            # the global lexicon (that reintroduces cross-split codeword leakage). If the
            # split's pool has a single codeword, reuse is unavoidable but stays in-split.
            p = pools[s]
            if len(p) > 1 and codeword in p:
                wrong_cw = p[(p.index(codeword) + 1) % len(p)]
            elif len(p) > 1:
                wrong_cw = p[0]
        ex_id = f"advbench_{i:04d}_{B.sha16(it['instruction'])[:8]}"
        try:
            rec = B.build_item(tok, "advbench", ex_id, it["clearharm_id"], "advbench",
                               it["intent_cluster"], it["instruction"], c, codeword,
                               wrong["concept"], wrong_cw, demo_cache, client, args.model,
                               args.num_demos, args.seed, use_api)
            rec["split"] = split_of[c]
            rec["normalized_concept"] = c          # cluster/split key (== target_concept,
            #                                        matching clearharm); required by
            #                                        probe_dataset.build_items
            rec["wrong_codeword"] = wrong_cw       # tracked for the leakage self-check
            rec["wrong_concept"] = wrong["concept"]
            records.append(rec)
        except AssertionError as e:
            print(f"  skip {ex_id}: {e}")

    if use_api:
        json.dump(demo_cache, open(B.DEMO_CACHE, "w"), indent=1)

    # leakage self-check: no concept and no codeword straddles two splits. Includes the
    # wrong_codeword embedded in each record's shuffled/unrelated demos (a cross-split
    # wrong_cw would leak a held-out codeword into a train example otherwise).
    concept_splits, cw_splits = defaultdict(set), defaultdict(set)
    for r in records:
        concept_splits[r["target_concept"]].add(r["split"])
        cw_splits[r["codeword"]].add(r["split"])
        cw_splits[r.get("wrong_codeword")].add(r["split"])
    cw_splits.pop(None, None)
    straddle_concept = [c for c, s in concept_splits.items() if len(s) > 1]
    straddle_cw = [c for c, s in cw_splits.items() if len(s) > 1]

    obj = {
        "_meta": {
            "dataset_revision": f"advbench@{sha256_file(ADVBENCH_CSV)[:16]}",
            "source": "llm-attacks/data/advbench/harmful_behaviors.csv",
            "source_sha256": sha256_file(ADVBENCH_CSV),
            "builder": "scripts/build_advbench_doublespeak.py",
            "reuses": "build_doublespeak_split (build_item/get_demos/codeword lexicon)",
            "git_commit": ds_common.git_commit(),
            "tokenizer": args.tokenizer,
            "generator": args.model if use_api else "placeholder",
            "openai_seed": args.seed, "num_demos": args.num_demos,
            "n_records": len(records),
            "split_counts": {s: sum(1 for r in records if r["split"] == s)
                             for s in ("train", "dev", "test")},
            "codeword_pools": pools,
            "leakage_check": {"concept_straddle": straddle_concept, "codeword_straddle": straddle_cw},
            "note": "STRUCTURAL SMOKE (placeholder demos)" if not use_api else "full build",
        },
        "examples": records,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(obj, open(args.out, "w"), indent=1)

    from collections import Counter
    print(f"wrote {args.out}: {len(records)} records "
          f"(concepts={len(concept_cw)}, straddle concept={len(straddle_concept)} cw={len(straddle_cw)})")
    for k in sorted(Counter(r["split"] for r in records).items()):
        print(f"  {k[0]}: {k[1]}")
    if straddle_concept or straddle_cw:
        print(f"  WARNING leakage: concept={straddle_concept[:3]} codeword={straddle_cw[:3]}")


if __name__ == "__main__":
    main()
