# P1b step 1 — the free dataset recovery (plan §5 P1b)

**Date** 2026-08-05 · **Compute** CPU only, **zero OpenAI calls** (replay is from the on-disk concept cache)
**Script** `doublespeak_causality/scripts/recover_clearharm_concepts.py`
**Command**
```
/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python \
    doublespeak_causality/scripts/recover_clearharm_concepts.py
```
Nothing was rebuilt or overwritten. `clearharm_doublespeak_v1.json`, `_concept_cache.json` and
`_demo_cache.json` are untouched; this is an audit plus a reusable recovery function for a future
v3 builder.

---

## Headline

| | examples | concepts |
|---|---|---|
| v1 locked split (clearharm cohort) | 86 | 43 |
| **+ lexicon fallback (this work)** | **138** | **45** |
| delta | **+52 (+60.5%)** | +2 |

The plan estimated **+33 → 119 / 45 concepts**. The concept count lands exactly on the estimate;
the example count is **higher** (138), because the fallback also fires on the 31 multi-token
rejects (+8) and because the union lexicon covers ClearHarm's weapons/CBRN vocabulary more densely
than the estimate assumed. See *Sensitivity* below — 44/62 is stable across every reasonable
variant of the matching rule; no variant reproduces 33.

---

## 1. Replay of the v1 extractor (from cache, no API) — reproduces the decomposition exactly

```
[1] v1 replay over 179 ClearHarm rows (from cache, no API)
    kept          86
    llm_none      62
    multi_token   31
    not_verbatim  0
    cache_miss    0
```

Matches the briefed 86 / 62 / 31 / 0 on the nose. The cache has 179/179 entries (0 cache misses),
so the replay is a faithful re-execution of the accept/reject decision in
`build_doublespeak_split.py::extract_clearharm_concepts`.

Both loss buckets are code defects, not properties of the data:

* **62 `llm_none`** — `_llm_pick_concept` (L286-292) is
  `try: ...openai... except Exception: return None`. A genuine "no harmful noun" and a transport /
  rate-limit / parse failure produce the identical `None`, and `if not concept: continue` drops the
  row. The cache stores the swallowed `None`, so the loss is *frozen into the locked split*.
* **31 `multi_token`** — the returned word is a legitimate verbatim concept but is rejected by
  `if not is_single_token(tok, concept): continue` (L263-270) with no second attempt. Rejected
  token-length histogram: `{2: 25, 3: 3, 4: 3}` — i.e. 25 of the 31 missed by a single token.

`not_verbatim = 0` and `cache_miss = 0`: the verbatim-swap contract never once caused a drop.

## 2. Lexicon fallback

**Lexicon** = union of `target_concept` over all 137 v1 split examples ∪ `harmful_word` over
`data/expanded_concepts_v2.json` ∪ `concept` over `data/curated_concepts.json`, lowercased,
alphabetic, ≥4 chars, and verified single-token under Llama-3.1.
→ **85 usable words** (29 candidates dropped: 21 multi-token, 8 too-short/non-alpha).

**Rule** — for a dropped row, take the **longest** lexicon word matching the instruction with a
regex **word boundary** (`\bword\b`, case-insensitive), then re-cased to the instruction's actual
casing, then re-checked single-token in that exact casing. Word boundaries (not raw substring) are
required: a substring hit inside a longer word would corrupt `build_conditions`' concept→codeword
string swap.

```
[2] lexicon fallback on the 93 dropped rows
    llm_none      44/62 recovered
    multi_token    8/31 recovered
    recovered total 52  ->  138 examples / 45 concepts (v1 was 86 / 43)
```

41 rows remain unrecovered (18 of the `llm_none` bucket, 23 of the `multi_token` bucket): no
lexicon word occurs verbatim in them. Category breakdown — recovered:
`{other_uncategorized: 36, weapons_explosives_mass_casualty: 14, cyber_hacking_malware: 2}`;
unrecovered: `{other_uncategorized: 37, cyber_hacking_malware: 2, drugs_controlled_substances: 1,
weapons_explosives_mass_casualty: 1}`. Recovery is therefore not category-neutral: it is strongly
biased toward the weapons/CBRN slice, which is where the union lexicon has coverage.

### Sensitivity of the 44/62 figure

| variant (applied to the 62 `llm_none` rows) | recovered |
|---|---|
| union lexicon, word-boundary (**used**) | **44** |
| union lexicon, raw substring (no boundary) | 49 |
| union lexicon, case-**sensitive** match | 44 |
| lexicon = v1-split concepts only | 44 |
| lexicon = expanded_v2 + curated only (no v1 concepts) | 0 |
| lexicon = curated only | 3 |
| min word length 5 / 6 / 7 | 43 / 41 / 24 |

44 is robust: it does not depend on casing, and the v1-split concepts carry the entire signal (the
external files contribute 0 rows on their own). The plan's 33 is not reproduced by any variant and
appears to have been a conservative estimate.

## 3. Evidence per recovered row

`provenance='lexicon_fallback'` is stamped on every recovered row (LLM-extracted rows keep
`provenance='llm_gpt4omini'`), so the two populations stay separable forever and any downstream
result can be re-run on the LLM-only subset. Per row the script emits
`lexicon_word`, `lexicon_sources`, `match_char_start`, `match_word_index`, `match_n_occurrences`,
and the originating `v1_status`. Full 52-row table is printed by section `[3]` of the script (not
reproduced here to keep instruction text out of the report). Distribution of the recovered concept:

```
chemical 13 · device 8 · explosive 5 · weapons 4 · weapon 4 · agents 4 · agent 3 ·
casualties 2 · fuel 2 · chlorine, attacks, material, mortar, bacteria, virus, bomb 1 each
```

All 52 matched at exactly **one** occurrence in their instruction (`x1` everywhere), so the
concept→codeword swap is unambiguous for every recovered row. Lexicon provenance: 49 rows matched
a word sourced from the v1 split only; 3 matched a word also present in `curated_concepts.json`
(`chlorine`, `mortar`, `bomb`).

## 4. Single-token verification with the real tokenizer

```
[4] real-tokenizer single-token verification of every kept concept
    tokenizer=meta-llama/Llama-3.1-8B-Instruct  offline=1
    NOT single-token: 0
```

Loaded from `HF_HOME=<repo>/.cache/huggingface` with `HF_HUB_OFFLINE=1` (the script sets both
defaults itself). The check is on `len(tok.encode(" " + concept)) == 1` in the **as-it-appears
casing**, identical to the v1 builder's contract. **Zero** of the 138 kept concepts — recovered or
original — is multi-token.

## 5. Concept-level leakage structure implied for v3

```
[5] n_examples=138  n_concepts=45  largest_concept_cluster=14 (chemical)
    concept size histogram: {1:24, 2:5, 3:3, 4:5, 5:1, 6:1, 7:1, 9:1, 10:1, 11:1, 13:1, 14:1}
    singleton concepts: 24
    50/25/25 concept-level bin-pack -> {'train': 69, 'val': 35, 'test': 34}
        straddling_concepts=0   all >= 20: True   concepts/split {'train':17,'val':14,'test':14}
    [strict] lemma-collapsed: n_concepts=40  largest=20 (weapon)
        bin-pack {'train': 69, 'val': 35, 'test': 34}  straddling=0  all >= 20: True
```

* **Yes** — a 50/25/25 concept-level bin-pack of the 138 clears ≥20 per split with **zero
  straddling concepts** (whole concepts are assigned as units by construction; greedy
  largest-first on the remaining deficit). Actual 69/35/34 = 50.0 / 25.4 / 24.6 %.
* It also survives the **stricter** definition where singular/plural pairs are one concept
  (`weapon`/`weapons`, `agent`/`agents`, `attack`/`attacks`, `explosive`/`explosives`,
  `toxin`/`toxins` collapse; 45 → 40 concepts, largest cluster 14 → 20). Still 69/35/34, still
  zero straddling. This matters because in v1 those pairs are distinct strings and *could* have
  been split across train/test.
* For contrast, the v1 86-example set bin-packs to 43/22/21 — feasible but with only ~1 example of
  slack over the ≥20 floor in val/test. The recovery buys real margin.

### Caveat that must be carried into the paper

The +52 rows add almost **no concept diversity**: only 2 of the 45 concepts are new
(`chlorine`, `mortar`); the other 50 recovered rows densify the 43 concepts v1 already had. So:

* for **item-level** statistics (per-example AUC, per-item rep→behavior link) this is a genuine
  +60% in N;
* for **concept-level generalization** (LOGO, cross-concept transfer) the effective N goes 43 → 45,
  i.e. essentially unchanged. Do not report the +60% as if it strengthened concept-level claims.

The recovered concepts also skew generic (`chemical`, `device`, `material`, `agent`). Whether
swapping such a low-specificity noun actually neutralizes the request — the core Doublespeak
assumption that harm is concentrated in one swappable noun — is *not* established for these rows
and should be gated on a neutral-prompt harmfulness check before the v3 split is locked.

## Recommended next step (not executed — plan gate)

1. Patch `_llm_pick_concept` to distinguish an API exception from a real `NONE` (re-raise / retry,
   and cache a sentinel like `"__ERROR__"` rather than `None`).
2. Add the multi-token second chance: on rejection, fall back to `lexicon_match` before dropping.
3. Rebuild as **v3** at a new path (`clearharm_doublespeak_v3.json`) — never in place — carrying
   `provenance` per example, and gate on the neutral-prompt harmfulness check above.

`recover_clearharm_concepts.py --out <path>` dumps the full 179-row audit plus the v3 bin-pack
assignment as JSON for step 2 to consume (off by default; writes nothing unless asked).
