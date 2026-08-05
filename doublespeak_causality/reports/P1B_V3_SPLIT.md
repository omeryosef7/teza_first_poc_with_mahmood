# P1b — ClearHarm Doublespeak split **v3**

Plan: `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md` §5 P1b (motivated by §0.4 concept-level leakage
and §0.5 power).
Builder: `scripts/build_split_v3.py` · Output: `data/splits/clearharm_doublespeak_v3.json`
Built 2026-08-05, CPU only, **0 OpenAI calls**, git commit `a9f04ae3af36a8d854f9840b03374a597ed60cca`.

---

## 1. Why v3 exists — the v1 leakage audit

v1 passes `validate_data_integrity.py` with **12 ok / 0 warn / 0 FATAL**, including
`ok no intent_cluster overlap across train/test`. That check was **vacuous**: v1 set

```
intent_cluster = f"clearharm::{cat}::{sha16(instr)[:8]}"     # build_doublespeak_split.py:272
```

i.e. a per-*instruction* hash, so all 86 ClearHarm rows were 86 distinct clusters and no two rows
could ever share one. The channels that actually carry signal — the **target concept** and the
**codeword** — were never constrained and straddle the split badly. Paraphrase leakage, which the
hash *was* meant to guard against, is not the binding constraint: over all 179 ClearHarm
instructions the max pairwise TF-IDF cosine is **0.690** with only **3** pairs above 0.5
(the plan's §5 P1b claim of "zero pairs exceed 0.5" is slightly optimistic but the conclusion holds).

### v1 vs v3 leakage table

Computed by `build_split_v3._leakage()` (train-like = train+dev, test-like = test+heldout — the same
folding `validate_data_integrity.py` uses), stored verbatim in `_meta.leakage`:

| metric | **v1** (clearharm cohort) | **v3** |
|---|---|---|
| examples | 86 | **138** |
| raw target concepts | 43 | 45 |
| distinct codewords | 21 | **45** |
| intent clusters | 86 (= 1 per row, vacuous) | **40** (normalized concept) |
| **concepts straddling train/test** | **14 / 43** | **0 / 45** |
| **codewords straddling train/test** | **17 / 21** | **0 / 45** |
| clusters straddling train/test | 0 *(vacuously)* | 0 *(by construction)* |
| rows whose concept straddles | **55 / 86** | **0 / 138** |
| rows whose codeword straddles | **77 / 86** | **0 / 138** |
| rows with either leak | **77 / 86 (90 %)** | **0 / 138** |

Consequence for the paper: **v1 supports no "unseen concept" and no "unseen codeword"
generalization claim** — 17 of its 21 codewords appear on both sides, so a test-set effect can be
memorized binding rather than a transferable mechanism. v3 is the split those claims need.
v1 remains untouched and frozen; the numbers above are its documented limitation.

---

## 2. What v3 is

ClearHarm-primary (single cohort `clearharm`, no curated replication arm), **6 conditions per
example**: `doublespeak`, `neutral`, `direct`, `benign`, `shuffled`, `unrelated`.

| quantity | value |
|---|---|
| examples (N) | **138** |
| prompt rows (N × 6 conditions) | **828** |
| raw target concepts | **45** (all single-token) |
| intent clusters (= normalized concept) | **40** |
| split sizes (examples) | **train 69 / dev 35 / test 34** |
| clusters per split | 14 / 13 / 13 |
| concepts per split | 17 / 14 / 14 |
| codewords per split | 17 / 14 / 14, **pairwise disjoint** |
| min examples per split | 34 ≥ 20 ✅ |
| codeword occurrences in templated DS prompt | min 7, median 13, max 13 (≥ 1 demo + 1 query) |

### Composition (from 179 ClearHarm rows)

Replayed from `data/splits/_concept_cache.json` by the reused
`recover_clearharm_concepts.replay()` — **no API**:

| v1 extractor outcome | rows | recovered by lexicon fallback |
|---|---|---|
| `kept` (gpt-4o-mini concept, single-token, verbatim) | 86 | — (kept as `llm_extracted`) |
| `llm_none` (silent `except Exception: return None`) | 62 | **44** |
| `multi_token` (good word, 2–4 Llama tokens) | 31 | **8** |
| `not_verbatim` / `cache_miss` | 0 | — |
| **total kept in v3** | | **138** (86 `llm_extracted` + 52 `lexicon_fallback`) |

The 41 still-dropped rows (18 `llm_none`, 23 `multi_token`) need OpenAI to recover
(re-run + paraphrase), which is out of scope for this CPU-only task — see §6.

---

## 3. Design decisions

**intent_cluster = normalized target concept.** Lowercased, with a plural collapsed onto its
singular when both are concepts (`normalize_concept`, identical rule to the audit script's `lemma`).
Collapses 5 pairs: agents→agent, attacks→attack, explosives→explosive, toxins→toxin,
weapons→weapon. 45 raw concepts → **40 clusters**, largest cluster 20 examples.
Concept identity is the dominant leakage channel in ClearHarm; the surface-paraphrase channel is
weak (§1) and the resulting v3 split has a max **cross-split** instruction TF-IDF cosine of
**0.489**, i.e. 0 pairs above the plan's 0.7 threshold and 0 above 0.5 (v1: 0.423).

**Concept-level bin-pack.** `recover_clearharm_concepts.bin_pack` (greedy largest-first over
*whole* clusters, target 50/25/25) → 69/35/34, i.e. 50.0 % / 25.4 % / 24.6 %. Whole clusters only,
so straddling is impossible by construction; asserted, and re-verified pairwise for
train/dev, train/test **and** dev/test (0 / 0 / 0 for concepts, codewords and clusters).

**Single-token, verified with the real tokenizer.** `meta-llama/Llama-3.1-8B-Instruct`, offline
(`HF_HOME=<repo>/.cache/huggingface`, `HF_HUB_OFFLINE=1`), space-prefixed form
`len(tok.encode(" "+w)) == 1`, for every concept **and** every codeword. Independently re-checked by
`validate_data_integrity.py` → `ok all primary codewords/concepts are single-token`.

**Codeword pool (replaces `CODEWORD_LEXICON`).** The hardcoded 42-item list yields only 21
single-token entries and contains two non-words (`lantern2`, `pebble2`). v3 draws from
`/usr/share/dict/american-english` ∩ Llama-3.1 vocabulary:

| stage | count |
|---|---|
| dictionary words, lowercase alpha, ≥ 4 chars | 63,072 |
| … single-token under Llama-3.1 | **16,113** |
| … benign count nouns (morphological filter, see below) | 2,192 |
| … minus banned (concept lexicon ∪ v3 concepts ∪ every word in any ClearHarm instruction) | **2,098 available** |
| assigned (one per concept, each used once) | **45** |

The morphological filter keeps only pluralizable words with no `-ed/-ing/-ly` inflection in the
dictionary, drops derivational suffixes (`-ing/-ed/-ly/-tion/-ment/…`), a function-word stoplist,
and any word containing a harm stem — a raw pool admits verbs/adjectives (`coaching`, `hinted`,
`loud`) and harm words (`massacre`, `bullet`), which would make the substituted query
("…how to build a *hinted*…") ungrammatical or unsafe. The 21 words that already have cached
gpt-4o-mini demos are whitelisted back in (English also verbs them: *blanketed*, *saddled*).

**Codewords are pairwise disjoint per split** (each of the 45 is used exactly once; asserted for all
three split pairs). Cached-demo words are handed out round-robin so no split gets a systematically
better `benign` condition (7 cached codewords each).

| split | codewords |
|---|---|
| train (17) | beacon caller canoe centerpiece consultant cushion debtor fighter kettle marble odor pumpkin refugee stranger survival tang trumpet |
| dev (14) | artisan blanket carrot dinosaur ferry highway ingress lantern legend pillow quilt rainbow scooter violet |
| test (14) | altitude cabbage cider circus civilian comer harbor hunter mango potato prank saddle teen walnut |

**Controls stay inside the split.** `shuffled` (wrong concept → same codeword) and `unrelated`
(same concept → wrong codeword) pick `wrong_concept` / `wrong_codeword` by cyclic rotation
**within the example's own split**, so a test prompt never contains train material. v1 rotated over
the global item list and did leak this way. Verified: 0 cross-split `wrong_concept`, 0 cross-split
`wrong_codeword`.

---

## 4. Reuse and provenance

Nothing was reimplemented:

- `recover_clearharm_concepts.load_lexicon / replay / bin_pack` — 86 → 138 examples / 45 concepts.
- `build_doublespeak_split.build_item` — emits all 6 conditions, which internally calls
  `ds_common.build_conditions`, `prepare_demos.substitute`, `ds_common.apply_template` and
  `ds_common.find_word_occurrences_in_text`. Also `is_single_token`, `sha16`, `DATASET_REVISION`.
- Caches: `data/splits/_concept_cache.json` (concepts), `data/splits/_demo_cache.json` (demos).

**Zero API calls.** The demo cache is read-only; `build_item` receives a `deepcopy`, and the script
asserts the on-disk cache is byte-identical afterwards. Demo coverage:

| demo set | gpt-4o-mini (cached) | template placeholder |
|---|---|---|
| concept demos (attack / `doublespeak`) | 138 / 138 | 0 |
| wrong-concept demos (`shuffled`) | 138 / 138 | 0 |
| codeword demos (`benign` only) | 79 / 138 | 59 |

So every *attack* condition uses real gpt-4o-mini demos; only the `benign` control falls back for the
24 new codewords, recorded per row as `provenance.codeword_demos = "template_placeholder"`.

`_meta` records: `dataset_revision` (`clearharm@79464fb6…`), `builder`, `reused`, `git_commit`,
`git_dirty`, `tokenizer`, `generator`, `concept_source`, `seeds`
(`openai_seed=7`, `num_demos=12`, `codeword_pool_seed=1234`), split/cluster/concept/codeword
inventories, `codeword_pool` stats, `provenance_counts`, `demo_provenance_counts`,
`v1_status_counts`, and the full `leakage` block for **both v1 and v3**.
Per row: `provenance.concept_extraction ∈ {llm_extracted, lexicon_fallback}` (86 / 52), plus
`v1_status`, `lexicon_word`, `lexicon_sources`, `match_char_start`, and the three demo-source fields.

---

## 5. Verification

```
$ cd doublespeak_causality
$ HF_HOME=$PWD/../.cache/huggingface HF_HUB_OFFLINE=1 python scripts/build_split_v3.py
[1] recovered 138/179 ClearHarm rows (v1 kept 86)  lexicon=85 concepts
[2] intent_cluster = normalized concept: 45 raw concepts -> 40 clusters (largest=20)
[3] bin-pack {'train': 69, 'dev': 35, 'test': 34}  clusters/split={'train': 14, 'dev': 13, 'test': 13}  all >= 20
[4] codeword pool 2098 available (dict 63072 -> single-token 16113 - 94 banned); assigned 45, 21 with cached gpt-4o-mini demos; split sets disjoint
[6] built 138 records x 6 conditions = 828 prompt rows
[7] v1: concepts_straddling=14/43 codewords_straddling=17/21 rows_concept_leak=55 rows_codeword_leak=77 n_clusters=86/86
[7] v3: concepts_straddling=0/45 codewords_straddling=0/45 rows_concept_leak=0 rows_codeword_leak=0 n_clusters=40/138
wrote .../data/splits/clearharm_doublespeak_v3.json: 138 records  {'train': 69, 'dev': 35, 'test': 34}
```

```
$ HF_HOME=$PWD/../.cache/huggingface HF_HUB_OFFLINE=1 python scripts/validate_data_integrity.py \
      --split data/splits/clearharm_doublespeak_v3.json --tokenizer meta-llama/Llama-3.1-8B-Instruct
== split integrity: data/splits/clearharm_doublespeak_v3.json ==
  ok    loaded 138 examples from data/splits/clearharm_doublespeak_v3.json
  ok    train/dev has 104 unique examples (>= 20)
  ok    test/heldout has 34 unique examples (>= 20)
  ok    cohort 'clearharm' train has 104 unique examples (>= 20)
  ok    cohort 'clearharm' test has 34 unique examples (>= 20)
  ok    no train/test example_id overlap
  ok    no intent_cluster overlap across train/test
  ok    no duplicate prompts across train/test
  ok    dataset_revision = clearharm@79464fb6b3c2a8ee925184f394f9636600349f88
  ok    all primary codewords/concepts are single-token

10 ok / 0 warn / 0 FATAL
```

Additional independent checks (not covered by the validator, which only folds dev into train):

```
all 6 conditions non-empty in all rows: True => rows 828
  train/dev:  concepts=0 codewords=0 clusters=0
  train/test: concepts=0 codewords=0 clusters=0
  dev/test:   concepts=0 codewords=0 clusters=0
rows/split {'train': 69, 'dev': 35, 'test': 34}
cross-split wrong_concept / wrong_codeword leaks: 0 0
cw occurrences min/med/max 7 13 13
v3 n 138 max any-cross-split tfidf 0.489  cross>0.5 0  cross>0.7 0
v1 n  86 max any-cross-split tfidf 0.423  cross>0.5 0  cross>0.7 0
```

**0 straddling concepts, 0 straddling codewords, 0 straddling clusters — confirmed for all three
split pairs.**

---

## 6. Known gaps (require an explicit go-ahead / API budget)

1. **N = 138, not the plan's 200.** The remaining +62 all need OpenAI: paraphrase-recover the 23
   still-dropped multi-token concepts, re-run the 18 unrecovered `llm_none` rows with gpt-4o and log
   the real failure reason, and the new pool-codeword expansion. Zero-API yield is capped at 138.
   Power note: with dev+test = 69, a 40 % responsive subgroup still clears the ≥ 20-per-cell mandate
   on train (69 → ~28) and on dev+test pooled (69 → ~28), but **not** on `test` alone (34 → ~14).
   Analyses restricted to a responsive subgroup should pool dev+test or use train/dev.
2. **`benign` demos for 24 codewords are template placeholders** (59 of 138 rows). One small
   gpt-4o-mini run over those 24 words (24 × 12 sentences) upgrades them; the row-level
   `provenance.codeword_demos` flag makes the affected rows selectable.
3. **Harm categories are not balanced across splits** — the bin-pack optimizes concept clusters, and
   category is confounded with concept. Observed:
   `train {other 53, weapons 13, cyber 3}`, `dev {other 27, cyber 5, identity 1, fraud 1, weapons 1}`,
   `test {weapons 16, other 10, cyber 7, identity 1}`. Test skews weapons-heavy. Any cross-split
   comparison should either report per-category numbers or treat category as a covariate. Balancing
   it jointly with zero concept straddling is not achievable at N = 138 (largest cluster = 20).
4. **`scripts/validate_dataset_v3.py`** (the plan's dedicated FATAL validator) is not part of this
   task. `validate_data_integrity.py` already covers ID / cluster / duplicate-prompt / single-token /
   post-template codeword-occurrence checks, and the cosine-0.7 cross-split check was run ad hoc
   above (max 0.489, 0 violations); what remains unautomated is the exact per-occurrence codeword
   index assertion and harmful-content masking in logs.
