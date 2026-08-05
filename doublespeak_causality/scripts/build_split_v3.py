#!/usr/bin/env python3
"""P1b: build the ClearHarm v3 Doublespeak split (CAUSAL_CONTINUATION_MASTER_PLAN §5 P1b).

v1 (data/splits/clearharm_doublespeak_v1.json) is leaky in the two channels that actually carry
signal, and its "zero intent_cluster overlap" check was VACUOUS because intent_cluster was a
per-instruction hash (build_doublespeak_split.py:272 -> f"clearharm::{cat}::{sha16(instr)[:8]}"),
so every one of the 86 rows was its own cluster. Measured on v1 (see reports/P1B_V3_SPLIT.md):
14/43 concepts and 17/21 codewords straddle train/test, affecting 55 (concept) / 77 (codeword) rows.

v3 fixes exactly that:
  - intent_cluster = NORMALIZED TARGET CONCEPT (lowercased, singular/plural collapsed), which is the
    dominant leakage channel in ClearHarm; the surface-paraphrase channel the v1 hash was guarding
    is weak (max pairwise instruction TF-IDF cosine 0.690 over all 179 rows, 3 pairs > 0.5, and 0
    CROSS-SPLIT pairs > 0.5 in the resulting v3 split -- max 0.489).
  - concept-level greedy bin-pack ~50/25/25 over WHOLE clusters => zero straddling concepts.
  - ONE codeword per concept, drawn from a dictionary-intersect-vocabulary pool (not the hardcoded
    42-item CODEWORD_LEXICON, of which only 21 are single-token and two -- 'lantern2','pebble2' --
    are junk), each codeword used exactly once => codeword sets are DISJOINT per split, which is
    what an "unseen codeword" generalization claim needs.
  - the shuffled/unrelated controls draw their wrong_concept / wrong_codeword from WITHIN the same
    split, so a test prompt never contains train material.

Reuse (nothing is reimplemented here):
  scripts/recover_clearharm_concepts.py : load_lexicon / replay / bin_pack  (86 -> 138 examples,
                                          45 concepts, via the cached extractions + lexicon fallback)
  scripts/build_doublespeak_split.py    : build_item (which itself calls prepare_demos.substitute and
                                          ds_common.build_conditions) + is_single_token + sha16
  data/splits/_concept_cache.json       : the cached gpt-4o-mini concept extractions
  data/splits/_demo_cache.json          : the cached gpt-4o-mini 12-demo sets

CPU only, ZERO OpenAI calls: demos come from the on-disk cache; the cache is opened READ-ONLY and a
copy is handed to build_item so placeholder fills can never be written back. All 45 concepts and 21
of the 45 codewords have cached gpt-4o-mini demos; the other 24 codewords fall back to the
deterministic template demos and are marked codeword_demos='template_placeholder' per row.

Usage (offline tokenizer required):
  HF_HOME=<repo>/.cache/huggingface HF_HUB_OFFLINE=1 \
    python scripts/build_split_v3.py
  python scripts/build_split_v3.py --out /tmp/v3.json --dry-run
"""
from __future__ import annotations
import argparse, copy, csv, json, os, random, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)                        # doublespeak_causality/
ROOT = os.path.dirname(DC)                        # repo root
sys.path.insert(0, HERE)
sys.path.insert(0, DC)

import ds_common                                   # noqa: E402
import recover_clearharm_concepts as R             # noqa: E402
import build_doublespeak_split as B                # noqa: E402

CLEARHARM_CSV = os.path.join(ROOT, "data", "clearharm", "clearharm_179.csv")
DEMO_CACHE = os.path.join(DC, "data", "splits", "_demo_cache.json")
V1_SPLIT = os.path.join(DC, "data", "splits", "clearharm_doublespeak_v1.json")
OUT = os.path.join(DC, "data", "splits", "clearharm_doublespeak_v3.json")
DICTIONARY = "/usr/share/dict/american-english"

SPLIT_NAMES = ("train", "dev", "test")
FRACS = (0.50, 0.25, 0.25)
MIN_CODEWORD_LEN = 4          # same floor the concept lexicon uses
COHORT = "clearharm"          # ClearHarm-primary: v3 has no curated cohort


# ------------------------------------------------------------------ intent clusters
def normalize_concept(word: str, vocab) -> str:
    """intent_cluster key: lowercase + collapse a plural onto its singular when BOTH are concepts.

    Same rule as recover_clearharm_concepts.main's `lemma`, promoted to a named function so the
    split and the audit agree by construction. Collapses e.g. weapons->weapon, toxins->toxin.
    """
    w = word.strip().lower()
    if w.endswith("s") and not w.endswith("ss") and w[:-1] in vocab:
        return w[:-1]
    return w


# ------------------------------------------------------------------ codeword pool
# A codeword is substituted into the query ("...how to build a {codeword}..."), so it has to be a
# BENIGN COUNT NOUN. Raw dictionary-intersect-vocabulary admits verbs/adjectives ('coaching',
# 'hinted', 'loud') and harm-adjacent nouns ('massacre'), so the pool is filtered morphologically.
_BAD_SUFFIX = ("ing", "ed", "ly", "est", "ness", "ous", "ive", "able", "ible", "ic", "ize", "ise",
               "ate", "ify", "ism", "ist", "ity", "ment", "tion", "sion", "ance", "ence", "ship",
               "hood")
_HARM_STEM = ("bomb", "gun", "kill", "weap", "viol", "attack", "war", "drug", "poison", "toxic",
              "hack", "fraud", "steal", "theft", "murder", "abus", "assault", "terror", "explo",
              "massacr", "slaughter", "onslaught", "demoli", "victim", "corpse", "death", "dead",
              "wound", "crime", "crimin", "illeg", "harm", "danger", "threat", "shoot", "stab",
              "burn", "arson", "riot", "rape", "hostage", "ammo", "arms", "blade", "knife", "sword",
              "venom", "virus", "malw", "phish", "exploit", "ransom", "smuggl", "traffick", "cartel",
              "gang", "militia", "sniper", "grenad", "missil", "warhead", "anthrax", "cyanide",
              "narcot", "opioid", "overdose", "scam", "swindl", "forger", "launder", "bribe",
              "extort", "hazard", "lethal", "fatal", "injur", "disease", "patho", "radiat",
              "nuclear", "uranium", "plutoni", "bullet", "ammun", "muniti", "cartridg", "pistol",
              "rifle", "firearm", "shotgun", "shrapnel", "detonat", "incendiar", "combat", "calib")
# function words that survive the morphology test ('these' -> 'theses' is a dictionary word)
_STOPWORDS = {"these", "those", "this", "that", "than", "then", "thus", "thou", "thee", "thine",
              "when", "what", "which", "while", "where", "whom", "whose", "with", "from", "into",
              "onto", "upon", "over", "under", "they", "them", "their", "there", "here", "such",
              "some", "each", "both", "many", "much", "most", "more", "less", "very", "just",
              "only", "even", "also", "ever", "none", "once", "twice", "hence", "shall", "will",
              "would", "could", "should", "must", "been", "were", "have", "does", "same", "other",
              "first", "second", "next", "last"}


def _inflections(w):
    """Surface verb/adverb inflections of w; presence in the dictionary => w is not a pure noun."""
    out = {w + "ed", w + "ing", w + "ly", w + w[-1] + "ed", w + w[-1] + "ing"}
    if w.endswith("e"):
        out |= {w + "d", w[:-1] + "ing"}
    if w.endswith("y"):
        out |= {w[:-1] + "ied", w + "ing"}
    return out


def _noun_like(w, words):
    """Pure benign count noun: pluralizable, no verb/adverb inflection, no harm stem."""
    if w in _STOPWORDS or any(h in w for h in _HARM_STEM):
        return False
    if w.endswith(_BAD_SUFFIX):
        return False
    if w.endswith("s") and w[:-1] in words:          # already a plural
        return False
    if not (w + "s" in words or w + "es" in words):  # not pluralizable
        return False
    return not (_inflections(w) & words)


def load_codeword_pool(tok, banned, whitelist=()):
    """Single-token benign-noun codeword pool = dictionary INTERSECT tokenizer vocabulary.

    Replaces build_doublespeak_split.CODEWORD_LEXICON (42 hand-listed words, only 21 single-token,
    'lantern2'/'pebble2' not words at all). `banned` removes every concept lexicon word, every v3
    target concept, and every word occurring in ANY ClearHarm instruction -- the last one so a
    codeword can never already be present in the query before the concept->codeword swap.
    `whitelist` re-admits the paper's established codewords (blanket/canoe/cushion/... -- the ones
    that already have cached gpt-4o-mini demos); the morphological filter rejects them only because
    English also verbs them ('blanketed', 'saddled'), not because they are bad codewords.
    """
    words = set()
    with open(DICTIONARY, encoding="latin-1") as fh:
        for line in fh:
            w = line.strip()
            if w.isalpha() and w.islower():
                words.add(w)
    cands = {w for w in words if len(w) >= MIN_CODEWORD_LEN}
    single = {w for w in cands if B.is_single_token(tok, w)}
    nouns = {w for w in single if _noun_like(w, words)} | (set(whitelist) & single)
    return sorted(nouns - set(banned)), {"dictionary": DICTIONARY,
                                         "n_dictionary_candidates": len(cands),
                                         "n_single_token": len(single),
                                         "n_noun_like": len(nouns),
                                         "n_banned": len(set(banned) & nouns),
                                         "n_available": len(nouns - set(banned))}


def instruction_vocabulary():
    """Every lowercase word token occurring in any ClearHarm instruction (banned as a codeword)."""
    vocab = set()
    for row in csv.DictReader(open(CLEARHARM_CSV)):
        instr = row.get("instruction") or row.get("content") or ""
        vocab.update(re.findall(r"[a-z]+", instr.lower()))
    return vocab


def assign_codewords(concepts_by_split, pool, cached_words, seed):
    """One codeword per concept, each used exactly once => split codeword sets are DISJOINT.

    Words that already have cached gpt-4o-mini demos are consumed FIRST but handed out round-robin
    across splits, so no split gets a systematically better benign condition than another.
    """
    rng = random.Random(seed)
    have = [w for w in pool if w in cached_words]
    rest = [w for w in pool if w not in cached_words]
    rng.shuffle(rest)
    ordered_pool = have + rest

    # interleave the splits so the `have` prefix is shared out proportionally
    order = []
    for i in range(max(len(v) for v in concepts_by_split.values())):
        for s in SPLIT_NAMES:
            if i < len(concepts_by_split[s]):
                order.append(concepts_by_split[s][i])
    assert len(ordered_pool) >= len(order), f"pool {len(ordered_pool)} < concepts {len(order)}"
    return {c: ordered_pool[i] for i, c in enumerate(order)}


# ------------------------------------------------------------------ build
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--num-demos", type=int, default=12)
    ap.add_argument("--openai-seed", type=int, default=7, help="seed of the CACHED demo generation")
    ap.add_argument("--codeword-seed", type=int, default=1234, help="codeword-pool shuffle seed")
    ap.add_argument("--min-per-split", type=int, default=20)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--dry-run", action="store_true", help="print stats, do not write the split")
    args = ap.parse_args()

    os.environ.setdefault("HF_HOME", os.path.join(ROOT, ".cache", "huggingface"))
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.tokenizer)

    # ---- 1. recover the ClearHarm rows (REUSED wholesale, no API)
    lex, _ = R.load_lexicon(tok)
    rows = R.replay(tok, lex)
    kept = [r for r in rows if r.get("concept")]
    v1_status = Counter(r["v1_status"] for r in rows)
    print(f"[1] recovered {len(kept)}/{len(rows)} ClearHarm rows "
          f"(v1 kept {v1_status['kept']})  lexicon={len(lex)} concepts")

    # ---- 2. intent_cluster = normalized target concept
    concept_vocab = {r["concept"].lower() for r in kept}
    for r in kept:
        r["cluster"] = normalize_concept(r["concept"], concept_vocab)
    cluster_sizes = Counter(r["cluster"] for r in kept)
    print(f"[2] intent_cluster = normalized concept: {len(concept_vocab)} raw concepts -> "
          f"{len(cluster_sizes)} clusters (largest={cluster_sizes.most_common(1)[0][1]})")

    # ---- 3. concept-level bin-pack (REUSED), whole clusters only
    cl_split, load = R.bin_pack(cluster_sizes, FRACS, SPLIT_NAMES)
    for r in kept:
        r["split"] = cl_split[r["cluster"]]
    assert all(v >= args.min_per_split for v in load.values()), load
    print(f"[3] bin-pack {dict(load)}  clusters/split={dict(Counter(cl_split.values()))}  "
          f"all >= {args.min_per_split}")

    # ---- 4. codewords: pooled, one per concept, disjoint per split
    banned = set(lex) | concept_vocab | instruction_vocabulary()
    demo_cache = json.load(open(DEMO_CACHE))                      # READ-ONLY
    cached_words = {k.rsplit("|", 2)[0] for k in demo_cache
                    if k.endswith(f"|{args.num_demos}|{args.openai_seed}")}
    pool, pool_meta = load_codeword_pool(tok, banned, whitelist=cached_words)
    concept_split = {}
    for r in kept:
        concept_split[r["concept"].lower()] = r["split"]
    concepts_by_split = {s: sorted(c for c, sp in concept_split.items() if sp == s)
                         for s in SPLIT_NAMES}
    cw_map = assign_codewords(concepts_by_split, pool, cached_words, args.codeword_seed)
    pool_meta["n_with_cached_demos"] = sum(1 for c in cw_map if cw_map[c] in cached_words)
    assert len(set(cw_map.values())) == len(cw_map), "codeword reused across concepts"
    for s in SPLIT_NAMES:
        for t in SPLIT_NAMES:
            if s < t:
                ov = {cw_map[c] for c in concepts_by_split[s]} & {cw_map[c] for c in concepts_by_split[t]}
                assert not ov, f"codeword overlap {s}/{t}: {sorted(ov)}"
    print(f"[4] codeword pool {pool_meta['n_available']} available "
          f"(dict {pool_meta['n_dictionary_candidates']} -> single-token {pool_meta['n_single_token']}"
          f" - {pool_meta['n_banned']} banned); assigned {len(cw_map)}, "
          f"{pool_meta['n_with_cached_demos']} with cached gpt-4o-mini demos; split sets disjoint")

    # ---- 5. wrong_concept / wrong_codeword controls, WITHIN split
    wrong = {}
    for s in SPLIT_NAMES:
        cs = concepts_by_split[s]
        assert len(cs) >= 2, f"split {s} needs >=2 concepts for the shuffled/unrelated controls"
        for i, c in enumerate(cs):
            wrong[c] = cs[(i + 1) % len(cs)]

    # ---- 6. emit all 6 conditions per example via the v1 item builder (REUSED)
    cache = copy.deepcopy(demo_cache)   # placeholder fills stay in memory, never written back
    records = []
    for i, r in enumerate(sorted(kept, key=lambda x: x["clearharm_id"])):
        concept = r["concept"]
        key = concept.lower()
        cw, wc = cw_map[key], wrong[key]
        ex_id = f"{COHORT}_{i:04d}_{r['clearharm_id'].split('_')[-1][:8]}"
        instr = _instruction_for(r["clearharm_id"])
        rec = B.build_item(tok, COHORT, ex_id, r["clearharm_id"], r["category"], r["cluster"],
                           instr, concept, cw, wc, cw_map[wc], cache, None, None,
                           args.num_demos, args.openai_seed, False)
        rec["split"] = r["split"]
        rec["normalized_concept"] = r["cluster"]
        rec["provenance"] = {
            "concept_extraction": ("lexicon_fallback" if r.get("provenance") == "lexicon_fallback"
                                   else "llm_extracted"),
            "v1_status": r["v1_status"],
            "lexicon_word": r.get("lexicon_word"),
            "lexicon_sources": r.get("lexicon_sources"),
            "match_char_start": r.get("match_char_start"),
            "concept_demos": _demo_src(concept, cached_words),
            "codeword_demos": _demo_src(cw, cached_words),
            "wrong_concept_demos": _demo_src(wc, cached_words),
            "generator": "gpt-4o-mini (cached)",
            "openai_seed": args.openai_seed,
            "num_demos": args.num_demos,
        }
        rec["wrong_concept"] = wc
        rec["wrong_codeword"] = cw_map[wc]
        records.append(rec)
    assert json.load(open(DEMO_CACHE)) == demo_cache, "demo cache mutated on disk"
    print(f"[6] built {len(records)} records x 6 conditions = {len(records) * 6} prompt rows")

    # ---- 7. leakage accounting, v1 vs v3
    lk = {"v1": _leakage(json.load(open(V1_SPLIT))["examples"], COHORT),
          "v3": _leakage(records, COHORT)}
    for k, v in lk.items():
        print(f"[7] {k}: concepts_straddling={v['concepts_straddling']}/{v['n_concepts']} "
              f"codewords_straddling={v['codewords_straddling']}/{v['n_codewords']} "
              f"rows_concept_leak={v['rows_concept_leak']} rows_codeword_leak={v['rows_codeword_leak']} "
              f"n_clusters={v['n_clusters']}/{v['n_rows']}")
    assert lk["v3"]["concepts_straddling"] == 0 and lk["v3"]["codewords_straddling"] == 0

    obj = {
        "_meta": {
            "dataset_revision": B.DATASET_REVISION,
            "builder": "scripts/build_split_v3.py",
            "reused": ["scripts/recover_clearharm_concepts.py:load_lexicon/replay/bin_pack",
                       "scripts/build_doublespeak_split.py:build_item/is_single_token",
                       "prepare_demos.substitute", "ds_common.build_conditions"],
            "git_commit": ds_common.git_commit(),
            "git_dirty": ds_common.git_dirty(),
            "tokenizer": args.tokenizer,
            "generator": "gpt-4o-mini (demos read from data/splits/_demo_cache.json; 0 API calls)",
            "concept_source": "data/splits/_concept_cache.json (gpt-4o-mini) + lexicon fallback",
            "seeds": {"openai_seed": args.openai_seed, "num_demos": args.num_demos,
                      "codeword_pool_seed": args.codeword_seed},
            "cohorts": {COHORT: len(records)},
            "n_records": len(records),
            "n_conditions": 6,
            "conditions": ["doublespeak", "neutral", "direct", "benign", "shuffled", "unrelated"],
            "n_raw_concepts": len(concept_vocab),
            "n_intent_clusters": len(cluster_sizes),
            "intent_cluster_definition": "normalized target concept (lowercased, plural collapsed "
                                         "onto singular when both are concepts)",
            "split_sizes": dict(Counter(r["split"] for r in records)),
            "clusters_per_split": dict(Counter(cl_split.values())),
            "concepts_per_split": {s: len(concepts_by_split[s]) for s in SPLIT_NAMES},
            "codewords_per_split": {s: sorted(cw_map[c] for c in concepts_by_split[s])
                                    for s in SPLIT_NAMES},
            "codeword_pool": pool_meta,
            "provenance_counts": dict(Counter(r["provenance"]["concept_extraction"]
                                              for r in records)),
            "demo_provenance_counts": {
                f: dict(Counter(r["provenance"][f] for r in records))
                for f in ("concept_demos", "codeword_demos", "wrong_concept_demos")},
            "v1_status_counts": dict(v1_status),
            "leakage": lk,
            "note": "ClearHarm-primary v3; concept-level split, disjoint codewords, 0 API calls",
        },
        "examples": records,
    }
    if args.dry_run:
        print("[dry-run] not writing")
        return
    assert os.path.abspath(args.out) != os.path.abspath(V1_SPLIT), "refusing to overwrite v1"
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(obj, open(args.out, "w"), indent=1)
    print(f"wrote {args.out}: {len(records)} records  {dict(Counter(r['split'] for r in records))}")


_INSTR = None


def _instruction_for(clearharm_id):
    """instruction text keyed by the same sha16-derived id replay() builds (never printed)."""
    global _INSTR
    if _INSTR is None:
        _INSTR = {}
        for row in csv.DictReader(open(CLEARHARM_CSV)):
            s = row.get("instruction") or row.get("content") or ""
            _INSTR[f"clearharm_{B.sha16(s)[:12]}"] = s
    return _INSTR[clearharm_id]


def _demo_src(word, cached_words):
    return "gpt-4o-mini_cached" if word in cached_words else "template_placeholder"


def _leakage(examples, cohort):
    """Concept / codeword straddling between the train-like and test-like halves of a split file.

    train-like = train+dev, test-like = test+heldout -- the same folding validate_data_integrity.py
    uses, so these numbers are directly comparable to its FATAL checks.
    """
    ex = [e for e in examples if e.get("cohort") == cohort]
    tr = [e for e in ex if e["split"] in ("train", "dev")]
    te = [e for e in ex if e["split"] in ("test", "heldout")]
    cs = {e["target_concept"].lower() for e in tr} & {e["target_concept"].lower() for e in te}
    ws = {e["codeword"] for e in tr} & {e["codeword"] for e in te}
    ks = {e["intent_cluster"] for e in tr} & {e["intent_cluster"] for e in te}
    return {
        "n_rows": len(ex),
        "n_concepts": len({e["target_concept"].lower() for e in ex}),
        "n_codewords": len({e["codeword"] for e in ex}),
        "n_clusters": len({e["intent_cluster"] for e in ex}),
        "concepts_straddling": len(cs),
        "codewords_straddling": len(ws),
        "clusters_straddling": len(ks),
        "rows_concept_leak": sum(1 for e in ex if e["target_concept"].lower() in cs),
        "rows_codeword_leak": sum(1 for e in ex if e["codeword"] in ws),
        "rows_any_leak": sum(1 for e in ex
                             if e["target_concept"].lower() in cs or e["codeword"] in ws),
    }


if __name__ == "__main__":
    main()
