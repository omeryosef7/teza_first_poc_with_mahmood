#!/usr/bin/env python3
"""P1b step 1: audit + recover the ClearHarm rows the v1 concept extractor silently dropped.

The locked v1 split (data/splits/clearharm_doublespeak_v1.json) keeps 86 of the 179 ClearHarm
instructions. The 93 losses are NOT a property of the data, they are two bugs in
scripts/build_doublespeak_split.py:
  (a) _llm_pick_concept (~L286-292) wraps the gpt-4o-mini call in `except Exception: return None`,
      so an API error is indistinguishable from a genuine "no harmful noun here" -> row dropped;
  (b) a returned concept that is a perfectly good WORD but tokenizes to 2-4 tokens under
      Llama-3.1 is dropped outright (~L263-270) instead of falling back to another word.

This script REPLAYS the extractor over all 179 rows from the on-disk concept cache (NO OpenAI
calls, CPU only), reproduces the 86/62/31/0 decomposition, and then applies a LEXICON FALLBACK:
for every row whose cached answer was None or multi-token, pick from a union single-token concept
lexicon (v1 split concepts + data/expanded_concepts_v2.json + data/curated_concepts.json) the
LONGEST word that appears verbatim (word-boundary) in the instruction. Recovered rows carry
provenance='lexicon_fallback' so they stay distinguishable from LLM-extracted ones forever.

It does NOT rebuild the split -- it is an audit + a reusable recovery function for a future v3
builder. Every emitted field is a count, a concept word, or a char offset; instruction text is
never printed.

Usage:
  python scripts/recover_clearharm_concepts.py
  python scripts/recover_clearharm_concepts.py --out data/splits/_p1b_recovered.json
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)                        # doublespeak_causality/
ROOT = os.path.dirname(DC)                        # repo root

CLEARHARM_CSV = os.path.join(ROOT, "data", "clearharm", "clearharm_179.csv")
CONCEPT_CACHE = os.path.join(DC, "data", "splits", "_concept_cache.json")
V1_SPLIT = os.path.join(DC, "data", "splits", "clearharm_doublespeak_v1.json")
EXPANDED_V2 = os.path.join(DC, "data", "expanded_concepts_v2.json")
CURATED = os.path.join(DC, "data", "curated_concepts.json")

MIN_CONCEPT_LEN = 4          # same floor the --no-api heuristic uses in the v1 builder


def sha16(s: str) -> str:
    """Identical to build_doublespeak_split.sha16 so clearharm_ids line up with v1."""
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def is_single_token(tok, word: str) -> bool:
    """Single-token under the primary tokenizer in the ' word' (space-prefixed) form."""
    return len(tok.encode(" " + word, add_special_tokens=False)) == 1


# ------------------------------------------------------------------ union concept lexicon
def load_lexicon(tok):
    """Union single-token concept lexicon + where each word came from.

    Sources (all already in-repo, no new curation):
      v1_split   : target_concept of every example in clearharm_doublespeak_v1.json
      expanded_v2: harmful_word of every item in expanded_concepts_v2.json
      curated    : concept of every item in curated_concepts.json
    """
    src = defaultdict(set)
    if os.path.exists(V1_SPLIT):
        for ex in json.load(open(V1_SPLIT))["examples"]:
            w = (ex.get("target_concept") or "").strip().lower()
            if w:
                src[w].add("v1_split")
    if os.path.exists(EXPANDED_V2):
        for it in json.load(open(EXPANDED_V2))["items"]:
            w = (it.get("harmful_word") or "").strip().lower()
            if w:
                src[w].add("expanded_v2")
    if os.path.exists(CURATED):
        for it in json.load(open(CURATED))["items"]:
            w = (it.get("concept") or "").strip().lower()
            if w:
                src[w].add("curated")

    lex, dropped = {}, []
    for w in sorted(src):
        if not w.isalpha() or len(w) < MIN_CONCEPT_LEN:
            dropped.append((w, "too_short_or_nonalpha"))
        elif not is_single_token(tok, w):
            dropped.append((w, "multi_token"))
        else:
            lex[w] = sorted(src[w])
    return lex, dropped


def lexicon_match(instr, lex, tok):
    """Longest lexicon word appearing VERBATIM (word-boundary) in instr.

    Returns (word_as_it_appears, lexicon_key, char_start, n_occurrences, sources) or None.
    The as-it-appears casing is what a v3 builder must substitute, so it -- not the lowercase
    lexicon key -- is what gets the single-token check.
    """
    low = instr.lower()
    for w in sorted(lex, key=lambda x: (-len(x), x)):
        hits = [m.start() for m in re.finditer(r"\b" + re.escape(w) + r"\b", low)]
        if not hits:
            continue
        start = hits[0]
        actual = instr[start:start + len(w)]
        if not is_single_token(tok, actual):
            continue
        return actual, w, start, len(hits), lex[w]
    return None


# ------------------------------------------------------------------ replay of the v1 extractor
def replay(tok, lex):
    """Re-run the v1 accept/reject decision for all 179 rows from the CACHE (no API).

    Mirrors extract_clearharm_concepts() exactly: cache hit -> verbatim check (case-insensitive
    relocate) -> single-token check. Rows that the v1 builder dropped then get the fallback.
    """
    ccache = json.load(open(CONCEPT_CACHE))
    rows = list(csv.DictReader(open(CLEARHARM_CSV)))
    out = []
    for row in rows:
        instr = row.get("instruction") or row.get("content") or ""
        cat = row.get("category") or "other"
        rec = {
            "clearharm_id": f"clearharm_{sha16(instr)[:12]}",
            "category": cat,
            "intent_cluster": f"clearharm::{cat}::{sha16(instr)[:8]}",
            "instr_len": len(instr),
            "cached_concept": ccache.get(sha16(instr), "__MISSING__"),
        }
        concept = rec["cached_concept"]
        if concept == "__MISSING__":
            rec.update(v1_status="cache_miss", concept=None)
        elif not concept:
            rec.update(v1_status="llm_none", concept=None)
        else:
            # verbatim contract (build_conditions swaps concept -> codeword by string replace)
            if concept not in instr:
                pos = instr.lower().find(concept.lower())
                concept = instr[pos:pos + len(concept)] if pos >= 0 else None
            if concept is None:
                rec.update(v1_status="not_verbatim", concept=None)
            elif not is_single_token(tok, concept):
                rec.update(v1_status="multi_token", concept=None,
                           rejected_concept_ntok=len(tok.encode(" " + concept,
                                                               add_special_tokens=False)))
            else:
                rec.update(v1_status="kept", concept=concept, provenance="llm_gpt4omini")

        # ---- lexicon fallback for everything v1 threw away
        if rec["v1_status"] != "kept":
            hit = lexicon_match(instr, lex, tok)
            if hit:
                actual, key, start, n_occ, sources = hit
                rec.update(recovered=True, concept=actual, provenance="lexicon_fallback",
                           lexicon_word=key, match_char_start=start, match_n_occurrences=n_occ,
                           lexicon_sources=sources,
                           match_word_index=len(instr[:start].split()))
            else:
                rec.update(recovered=False)
        out.append(rec)
    return out


# ------------------------------------------------------------------ v3 leakage / bin-pack
def bin_pack(concept_sizes, fracs=(0.50, 0.25, 0.25), names=("train", "val", "test")):
    """Greedy largest-first concept-level bin-pack: whole concepts only => zero straddling."""
    total = sum(concept_sizes.values())
    targets = {n: f * total for n, f in zip(names, fracs)}
    assign, load = {}, {n: 0 for n in names}
    for c, k in sorted(concept_sizes.items(), key=lambda kv: (-kv[1], kv[0])):
        pick = max(names, key=lambda n: (targets[n] - load[n], -names.index(n)))
        assign[c] = pick
        load[pick] += k
    return assign, load


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--out", default=None, help="optional JSON dump of the 179-row audit")
    ap.add_argument("--min-per-split", type=int, default=20)
    args = ap.parse_args()

    os.environ.setdefault("HF_HOME", os.path.join(ROOT, ".cache", "huggingface"))
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.tokenizer)

    lex, lex_dropped = load_lexicon(tok)
    print(f"[lexicon] {len(lex)} single-token concepts "
          f"({len(lex_dropped)} candidates dropped: "
          f"{Counter(r for _, r in lex_dropped)})")

    recs = replay(tok, lex)
    st = Counter(r["v1_status"] for r in recs)
    print(f"\n[1] v1 replay over {len(recs)} ClearHarm rows (from cache, no API)")
    for k in ("kept", "llm_none", "multi_token", "not_verbatim", "cache_miss"):
        print(f"    {k:<13} {st.get(k, 0)}")
    assert sum(st.values()) == 179, st

    print(f"\n[2] lexicon fallback on the {179 - st['kept']} dropped rows")
    rec_by_bucket = Counter(r["v1_status"] for r in recs if r.get("recovered"))
    n_rec = sum(rec_by_bucket.values())
    for k in ("llm_none", "multi_token", "not_verbatim", "cache_miss"):
        if st.get(k):
            print(f"    {k:<13} {rec_by_bucket.get(k, 0)}/{st[k]} recovered")
    kept = [r for r in recs if r.get("concept")]
    concepts = sorted({r["concept"].lower() for r in kept})
    print(f"    recovered total {n_rec}  ->  {len(kept)} examples / {len(concepts)} concepts "
          f"(v1 was {st['kept']} / "
          f"{len({r['concept'].lower() for r in recs if r['v1_status'] == 'kept'})})")

    print("\n[3] recovered-row evidence (concept | lexicon source | char offset | #occ)")
    for r in recs:
        if r.get("recovered"):
            print(f"    {r['clearharm_id']}  {r['concept']:<14} "
                  f"{','.join(r['lexicon_sources']):<24} @char{r['match_char_start']:<4} "
                  f"x{r['match_n_occurrences']}  [{r['v1_status']}]")

    print("\n[4] real-tokenizer single-token verification of every kept concept")
    bad = [(r["clearharm_id"], r["concept"]) for r in kept if not is_single_token(tok, r["concept"])]
    print(f"    tokenizer={args.tokenizer}  offline={os.environ['HF_HUB_OFFLINE']}")
    print(f"    NOT single-token: {len(bad)} {bad if bad else ''}")

    print("\n[5] concept-level leakage structure for a v3 split")
    sizes = Counter(r["concept"].lower() for r in kept)
    print(f"    n_examples={len(kept)}  n_concepts={len(sizes)}  "
          f"largest_concept_cluster={max(sizes.values())} "
          f"({sizes.most_common(1)[0][0]})")
    print(f"    concept size histogram: {dict(sorted(Counter(sizes.values()).items()))}")
    print(f"    singleton concepts: {sum(1 for v in sizes.values() if v == 1)}")
    assign, load = bin_pack(sizes)
    straddle = sum(1 for c in sizes if len({assign[c]}) != 1)   # 0 by construction
    ok = all(v >= args.min_per_split for v in load.values())
    print(f"    50/25/25 concept-level bin-pack -> {dict(load)}  "
          f"straddling_concepts={straddle}  all>= {args.min_per_split}: {ok}")
    print(f"    concepts per split: "
          f"{dict(Counter(assign.values()))}")

    # singular/plural pairs ("weapon"/"weapons") are the SAME intent: if they land in different
    # splits that is concept leakage the raw string-keyed pack would not catch. Re-pack on the
    # lemma to show the split survives the stricter definition.
    def lemma(w):
        w = w.lower()
        return w[:-1] if (w.endswith("s") and not w.endswith("ss") and w[:-1] in sizes) else w
    lsizes = Counter(lemma(c) for c in sizes.elements())
    lassign, lload = bin_pack(lsizes)
    lok = all(v >= args.min_per_split for v in lload.values())
    print(f"    [strict] lemma-collapsed: n_concepts={len(lsizes)} "
          f"largest={max(lsizes.values())} ({lsizes.most_common(1)[0][0]})  "
          f"bin-pack {dict(lload)}  straddling=0  all>= {args.min_per_split}: {lok}")
    print(f"    [strict] collapsed pairs: "
          f"{sorted({(c, lemma(c)) for c in sizes if lemma(c) != c})}")

    if args.out:
        json.dump({"_meta": {"script": "scripts/recover_clearharm_concepts.py",
                             "tokenizer": args.tokenizer, "n_rows": len(recs),
                             "v1_status_counts": dict(st), "n_recovered": n_rec,
                             "n_kept_total": len(kept), "n_concepts": len(sizes),
                             "lexicon_size": len(lex)},
                   "rows": recs,
                   "v3_bin_pack": {"assign": assign, "load": load}},
                  open(args.out, "w"), indent=1)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
