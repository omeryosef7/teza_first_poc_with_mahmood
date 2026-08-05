# P1b — ClearHarm Doublespeak split **v3**

Plan: `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md` §5 P1b (motivated by §0.4 concept-level leakage
and §0.5 power) and **§5 P8.5 (power)**.
Output: `data/splits/clearharm_doublespeak_v3.json`

| revision | builder | date | N | concepts | clusters | API |
|---|---|---|---|---|---|---|
| v3.0 | `scripts/build_split_v3.py` | 2026-08-05 | 138 | 45 | 40 | 0 calls |
| **v3.1 (current)** | **`scripts/expand_concepts_v3.py`** | **2026-08-05** | **324** | **224** | **215** | 496 calls, ≈ **$0.14** |

v3.1 **rebuilds the same file with the same logic** (`build_split_v3`'s functions are imported, not
reimplemented) over expanded material. §1–§3 below describe the design, which is unchanged; §4
describes the expansion; §5–§6 are the v3.1 verification and remaining gaps. v3.0's numbers are kept
in the tables for comparison.

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

| metric | **v1** (clearharm cohort) | **v3.0** | **v3.1** |
|---|---|---|---|
| examples | 86 | 138 | **324** |
| raw target concepts | 43 | 45 | **224** |
| distinct codewords | 21 | 45 | **224** |
| intent clusters | 86 (= 1 per row, vacuous) | 40 | **215** (normalized concept) |
| **concepts straddling train/test** | **14 / 43** | 0 / 45 | **0 / 224** |
| **codewords straddling train/test** | **17 / 21** | 0 / 45 | **0 / 224** |
| clusters straddling train/test | 0 *(vacuously)* | 0 | **0** *(by construction)* |
| rows whose concept straddles | **55 / 86** | 0 / 138 | **0 / 324** |
| rows whose codeword straddles | **77 / 86** | 0 / 138 | **0 / 324** |
| rows with either leak | **77 / 86 (90 %)** | 0 / 138 | **0 / 324** |

Consequence for the paper: **v1 supports no "unseen concept" and no "unseen codeword"
generalization claim** — 17 of its 21 codewords appear on both sides, so a test-set effect can be
memorized binding rather than a transferable mechanism. v3 is the split those claims need.
v1 remains untouched and frozen (md5 `435064eb…`); the numbers above are its documented limitation.

---

## 2. What v3 is

**6 conditions per example**: `doublespeak`, `neutral`, `direct`, `benign`, `shuffled`, `unrelated`.
Two cohorts, both carrying the full 6-condition structure and both ≥ 20 per side:

| cohort | what it is | N |
|---|---|---|
| `clearharm` | ClearHarm-native instruction, concept extracted/recovered from it | **170** |
| `generated` | new single-token harm concept + a one-line request, gpt-4o-mini (§4.3) | **154** |

| quantity | v3.0 | **v3.1** |
|---|---|---|
| examples (N) | 138 | **324** |
| prompt rows (N × 6 conditions) | 828 | **1944** |
| raw target concepts (all single-token) | 45 | **224** |
| intent clusters (= normalized concept) | 40 | **215** |
| split sizes (examples) | 69 / 35 / 34 | **train 162 / dev 82 / test 80** |
| clusters per split | 14 / 13 / 13 | **97 / 59 / 59** |
| concepts per split | 17 / 14 / 14 | **104 / 60 / 60** |
| codewords per split, **pairwise disjoint** | 17 / 14 / 14 | **104 / 60 / 60** |
| min examples per split | 34 ≥ 20 ✅ | **80 ≥ 20 ✅** |
| cohort × split | — | train {ch 85, gen 77} · dev {ch 43, gen 39} · test {ch 42, gen 38} |
| codeword occurrences in templated DS prompt | 7 / 13 / 13 | **min 7, median 13, max 15** (≥ 1 demo + 1 query) |
| rows with **placeholder** demos | 59 | **0** |

Cluster-size histogram (v3.1): `{1: 192, 2: 8, 3: 3, 4: 2, 5: 2, 6: 2, 7: 1, 8: 1, 13: 1, 14: 1,
15: 1, 20: 1}`, largest cluster 20. **192 of the 215 clusters are singletons**, which is exactly the
shape a concept-clustered design wants: the number of independent concept units is now 215, not 40.

### Power (plan §5 P8.5)

| driver | required n | v3.1 |
|---|---|---|
| binary McNemar, m = 5, p₀ = 0.093, ΔASR = 0.15 | 178 | ✅ 324 |
| graded score, m = 5, d = 0.075 | 208 | ✅ 324 |
| **interaction I = 0.15, m = 5** | **324** | ✅ **324** |
| resistant subgroup of 150–200 analysable items | 334–445 | ✗ (see §6.1) |
| interaction I = 0.10 | 729 | declared out of scope by the plan |

This is the number P8.1 was missing: its interaction CI was [-0.151, +0.105] on n = 86.

---

## 3. Design decisions (unchanged from v3.0)

**intent_cluster = normalized target concept.** Lowercased, with a plural collapsed onto its
singular when both are concepts (`build_split_v3.normalize_concept`, identical rule to the audit
script's `lemma`). 224 raw concepts → **215** clusters. Concept identity is the dominant leakage
channel in ClearHarm; the surface-paraphrase channel is weak (§1).

**Concept-level bin-pack, now per cohort.** `recover_clearharm_concepts.bin_pack` (greedy
largest-first over *whole* clusters, target 50/25/25) is run **once per cohort** and the assignments
merged — this keeps the 50/25/25 proportions inside each cohort so the validator's per-cohort
≥ 20/≥ 20 rule holds for both, and whole clusters still go to exactly one split, so straddling
remains impossible by construction. Result 162/82/80 = 50.0 % / 25.3 % / 24.7 %. A generated concept
whose *normalized* form collides with a ClearHarm concept is dropped rather than allowed to put one
cluster in two cohorts (0 such collisions survived into the build).

**Single-token, verified with the real tokenizer.** `meta-llama/Llama-3.1-8B-Instruct`, offline
(`HF_HOME=<repo>/.cache/huggingface`, `HF_HUB_OFFLINE=1`), space-prefixed form
`len(tok.encode(" "+w)) == 1`, for every one of the 224 concepts **and** 224 codewords.
Independently re-checked by `validate_data_integrity.py`.

**Codeword pool.** `/usr/share/dict/american-english` ∩ Llama-3.1 vocabulary, morphologically
filtered to benign count nouns (`build_split_v3.load_codeword_pool`):

| stage | v3.0 | v3.1 |
|---|---|---|
| dictionary words, lowercase alpha, ≥ 4 chars | 63,072 | 63,072 |
| … single-token under Llama-3.1 | 16,113 | 16,113 |
| … benign count nouns (morphological filter) | 2,192 | 2,192 |
| … minus banned (concept lexicon ∪ all v3 concepts ∪ every word in **any** instruction, ClearHarm *and* generated) | 2,098 | **2,059** |
| assigned (one per concept, each used once) | 45 | **224** |

**Codewords are pairwise disjoint per split** (each of the 224 is used exactly once; asserted for
all three split pairs). The assignment order is computed against the **frozen** on-disk
`_demo_cache.json` word set, not against the demos this expansion added — otherwise every re-run
would reshuffle all 224 codewords. Full inventory: `_meta.codewords_per_split`.

**Controls stay inside the split.** `shuffled` (wrong concept → same codeword) and `unrelated`
(same concept → wrong codeword) pick `wrong_concept` / `wrong_codeword` by cyclic rotation
**within the example's own split**. Verified: 0 cross-split `wrong_concept`, 0 cross-split
`wrong_codeword`.

---

## 4. The v3.1 expansion (`scripts/expand_concepts_v3.py`)

**The lesson driving the design:** the previous expansion recovered +60 % *rows* but only +2
*concepts* (43 → 45), because the recovered rows densified concepts that already existed. Rows are
not the goal — the split is concept-clustered, so every per-concept claim is bounded by the
**cluster** count. v3.1 therefore optimises concepts and reports both.

| stage | rows | concepts | Δ concepts |
|---|---|---|---|
| v3.0 baseline | 138 | 45 | — |
| + step 1 (paraphrase) + step 2 (re-extraction) | 170 | 70 | **+25** |
| + step 3 (new concepts) | **324** | **224** | **+154** |

### 4.1 Step 1 — the 23 still-dropped multi-token rows → +22 rows, +22 concepts

All 31 `multi_token` drops are single *words* that tokenize to 2–4 Llama tokens (8 had already been
recovered by the v3.0 lexicon fallback and were left untouched to minimise churn). gpt-4o is asked
for single-word near-synonyms **of the harmful noun only — the instruction is never sent to the
API** — and the instruction is then rewritten **locally** by a verbatim string replacement of the
noun plus a/an agreement. That is the minimal possible rewrite and makes the deviation from the
ClearHarm source string exactly auditable.

- outcome: **22 ok**, 1 `not_verbatim_after_rewrite` (a casing edge case; row stays dropped).
- provenance on the row: `concept_extraction = "paraphrased_for_single_token"`, plus
  `source_concept`, `source_instruction` (the original ClearHarm string) and
  `source_instruction_sha16`.
- measured deviation: `difflib` similarity between source and rewritten instruction
  **min 0.882 / median 0.922 / max 0.972**; asserted for all 22 that the original noun is gone and
  the new one is present.

### 4.2 Step 2 — the 62 `llm_none` rows, re-run with the reason logged → +10 rows, +3 concepts

`build_doublespeak_split._llm_pick_concept` wraps its call in `except Exception: return None`, so an
API error was indistinguishable from a genuine "no harmful noun here". Re-running the **same prompt**
on gpt-4o with every outcome recorded turns the silent tally into an auditable one:

| gpt-4o outcome on the 62 v1 `None`s | rows |
|---|---|
| `ok` (verbatim, single-token noun found) | **52** |
| `multi_token` (verbatim word is 2+ tokens) | 7 |
| `model_said_none` | 3 |
| **`api_error`** | **0** |

**So none of the v1 drops were transport failures** — the `except Exception` was not firing; the
losses were gpt-4o-mini's weaker extraction, and the stronger model recovers 52/62. Per the
minimal-churn policy the new answer is *used* only for rows that still had no concept at all (10
rows); for the 44 already recovered by the lexicon fallback the answer is stored with
`used=false` so the pre-existing rows do not silently change identity. The full 62-row log lives in
`data/expanded_concepts_v3.json:step2_rerun`.

**Final ClearHarm accounting: 170 of 179 rows kept, 9 dropped**, and every drop now has a reason:
`llm_none → multi_token` 5, `llm_none → model_said_none` 3, `multi_token → not_verbatim_after_rewrite` 1
(`_meta.clearharm_drop_reasons`).

### 4.3 Step 3 — new concepts → +154 rows, +154 concepts

`scripts/expand_concepts.py`'s end-to-end yield was **10.7 %** for two fixable reasons, both fixed
here:

1. it required **both** the concept **and** a model-invented codeword to be single-token. v3.1 asks
   for **concepts + instructions only** and draws codewords from the 2,059-word dictionary pool that
   `build_split_v3` already builds.
2. it sent `sorted(used_c)[:40]` as the avoid-list — the first 40 words *alphabetically* — so later
   batches kept re-proposing the same already-used words. v3.1 sends the **full** avoid-list every
   batch.

Batches are additionally conditioned on an under-represented harm category (ClearHarm is 127/179
`other_uncategorized`). Result over 29 batches of 20: **206 accepted / 588 returned = 35.0 % yield**
(3.3× the old rate), rejects `already_used 254, multi_token 116, bad_word 11,
no_verbatim_instruction 1`. Every accepted concept is alpha, ≥ 4 chars, single-token, unused, and
carries ≥ 1 instruction containing it verbatim (196 of 206 carry 2).

154 of the 206 are used to land the split on exactly N = 324; **the remaining 52 concepts are banked
in `data/expanded_concepts_v3.json` and cost nothing further** (see §6.1).

### 4.4 Step 5 — the placeholder-demo gap is closed

v3.0 had 59/138 rows whose `benign` condition used deterministic template demos (24 codewords had no
cached gpt-4o-mini demos). v3.1 generates real demos for **every** concept and **every** codeword:

| demo set | v3.0 gpt-4o-mini / placeholder | **v3.1** |
|---|---|---|
| concept demos (`doublespeak`) | 138 / 0 | **324 / 0** |
| wrong-concept demos (`shuffled`) | 138 / 0 | **324 / 0** |
| codeword demos (`benign`) | 79 / **59** | **324 / 0** |

**Placeholder count is 0.** The `benign` control is now usable on every row.

### 4.5 Cost and caching

Every call is cached in `data/expanded_concepts_v3.json` (which doubles as the resumable state
file), keyed the same way as `_demo_cache.json` (`word|num_demos|seed`), so nothing is paid for
twice; `--stage build` makes **0 API calls**. The read-only `_demo_cache.json` and
`_concept_cache.json` are never written (md5 unchanged: `71b3458f…`, `6f2bd03e…`); the new demos are
merged *over* them in memory and a `deepcopy` is handed to `build_item` so placeholder fills can
never be written back.

| tag | model | calls |
|---|---|---|
| `step1_synonyms` | gpt-4o | 23 |
| `step2_extract` | gpt-4o | 62 |
| `step3_generate` | gpt-4o-mini | 29 |
| `concept-demos` | gpt-4o-mini | 179 |
| `codeword-demos` | gpt-4o-mini | 203 |
| **total** | | **496** |

**Approximate spend ≈ $0.14** (gpt-4o $0.026 + gpt-4o-mini $0.117), from the token counts recorded
per call in `_meta.spend_usd_approx`. Demo-generation tokens are charged at the measured per-call
average because `prepare_demos.gen_demos` does not return a usage object; the two gpt-4o steps are
exact.

---

## 5. Verification

```
$ cd doublespeak_causality
$ HF_HOME=$PWD/../.cache/huggingface HF_HUB_OFFLINE=1 python scripts/expand_concepts_v3.py --stage build
[plan] items: clearharm=170 (drops {'llm_none:model_said_none': 3, 'multi_token:not_verbatim_after_rewrite': 1, 'llm_none:multi_token': 5})  generated=154 (154 concepts + 0 second-instruction rows)  TOTAL=324
[plan] bin-pack {'train': 162, 'dev': 82, 'test': 80}  clusters/split={'train': 97, 'dev': 59, 'test': 59}
[plan] codeword pool 2059 available; assigned 224, 21 with pre-existing cached demos; split sets disjoint
[build] 324 records x 6 conditions = 1944 prompt rows
[leak] v1: concepts_straddling=14/43 codewords_straddling=17/21 clusters_straddling=0 rows_any_leak=77 n_clusters=86/86
[leak] v3: concepts_straddling=0/224 codewords_straddling=0/224 clusters_straddling=0 rows_any_leak=0 n_clusters=215/324
[leak] v3_clearharm: concepts_straddling=0/70 codewords_straddling=0/70 clusters_straddling=0 rows_any_leak=0 n_clusters=64/170
[leak] v3_generated: concepts_straddling=0/154 codewords_straddling=0/154 clusters_straddling=0 rows_any_leak=0 n_clusters=151/154
[leak] pairwise straddling {'dev/train': {'concepts': 0, 'codewords': 0, 'clusters': 0}, 'dev/test': {'concepts': 0, 'codewords': 0, 'clusters': 0}, 'test/train': {'concepts': 0, 'codewords': 0, 'clusters': 0}}
[build] cross-split wrong_concept/wrong_codeword leaks: 0 0   cw occurrences min/med/max 7 13 15
[build] demo provenance {'concept_demos': {'gpt-4o-mini_cached': 324}, 'codeword_demos': {'gpt-4o-mini_cached': 324}, 'wrong_concept_demos': {'gpt-4o-mini_cached': 324}}
wrote .../data/splits/clearharm_doublespeak_v3.json: 324 records  {'dev': 82, 'train': 162, 'test': 80}
[spend] approximate OpenAI spend so far: {'total': 0.1426, 'gpt-4o': 0.0257, 'gpt-4o-mini': 0.117, 'n_calls': 496}
```

```
$ HF_HOME=$PWD/../.cache/huggingface HF_HUB_OFFLINE=1 python scripts/validate_data_integrity.py \
      --split data/splits/clearharm_doublespeak_v3.json --tokenizer meta-llama/Llama-3.1-8B-Instruct
== split integrity: data/splits/clearharm_doublespeak_v3.json ==
  ok    loaded 324 examples from data/splits/clearharm_doublespeak_v3.json
  ok    train/dev has 244 unique examples (>= 20)
  ok    test/heldout has 80 unique examples (>= 20)
  ok    cohort 'clearharm' train has 128 unique examples (>= 20)
  ok    cohort 'clearharm' test has 42 unique examples (>= 20)
  ok    cohort 'generated' train has 116 unique examples (>= 20)
  ok    cohort 'generated' test has 38 unique examples (>= 20)
  ok    no train/test example_id overlap
  ok    no intent_cluster overlap across train/test
  ok    no duplicate prompts across train/test
  ok    dataset_revision = clearharm@79464fb6b3c2a8ee925184f394f9636600349f88
  ok    all primary codewords/concepts are single-token

12 ok / 0 warn / 0 FATAL
```

Additional independent checks (the validator only folds dev into train and does not test
paraphrase similarity):

```
n 324  all 6 conditions non-empty in all rows: True  => 1944 prompt rows
unique example_ids 324
concept verbatim in original_request : 324/324      concept erased from neutral   : 324/324
codeword absent from original_request: 324/324      codeword in DS+neutral+benign : 324/324
direct contains concept              : 324/324      placeholder demos             : 0
pairwise straddling (concepts/codewords/clusters): train/dev 0/0/0  train/test 0/0/0  dev/test 0/0/0
cross-split wrong_concept / wrong_codeword leaks: 0 0
cw occurrences min/med/max 7 13 15
cross-split instruction TF-IDF: max 0.621   pairs>0.5 2   pairs>0.7 0
all-pairs  instruction TF-IDF: max 0.713   pairs>0.5 6
paraphrase fidelity (22 rows): difflib similarity(source, rewritten) min 0.882 / med 0.922 / max 0.972
```

**0 straddling concepts, 0 straddling codewords, 0 straddling clusters — confirmed for all three
split pairs — and 0 placeholder demos.**

Cross-split TF-IDF rose from 0.489 (v3.0) to **0.621**, because generated one-line requests share
more templated phrasing than ClearHarm's prose. It is still **0 pairs above the plan's 0.7
threshold**; the 2 pairs above 0.5 are different concepts sharing a request frame, which the
concept-level split already isolates.

**Regression check:** re-running the builder with the expansion state emptied reproduces v3.0
exactly (138 records, 45 concepts, 40 clusters, 69/35/34) — the expansion adds material, it does not
change the split logic.

---

## 6. Known gaps

1. **N = 324 exactly hits the interaction driver, not the resistant-subgroup driver.** §5 P8.5 also
   lists "resistant subgroup of 150–200 analysable items → n = 334–445", and the plan's own prose
   prefers N = 350–450. **52 further generated concepts are already banked** in
   `data/expanded_concepts_v3.json`, so N = 376 / 276 concepts is reachable with
   `--target-n 376`; that rebuild needs one small `--stage codewords` run (demos for the ~52 new
   codewords, ≈ $0.02) and no new concept generation. Raising N further requires new generation, and
   §4.3's yield curve was already decaying (last batches 1–9 accepts of 20) — the supply of *common,
   single-token* harmful nouns is the binding constraint, not budget.
2. **Two cohorts, not one.** 154 of 324 rows are model-generated one-line requests rather than
   ClearHarm-native prose; they are shorter and more templated (§5's TF-IDF note). `cohort` is on
   every row and both cohorts independently satisfy ≥ 20/≥ 20 with ~50/25/25 proportions, so any
   headline result **must** be reported split by cohort as well as pooled; a cohort × condition
   interaction would mean the generated arm is not exchangeable with ClearHarm.
3. **Harm-category balance is much improved but not exact.** v3.0's test split was 47 % weapons;
   v3.1 is `train {other 72, weapons 22, fraud 22, cyber 17, drugs 15, identity 14}`,
   `dev {other 43, cyber 10, identity 10, drugs 8, weapons 6, fraud 5}`,
   `test {other 28, weapons 19, cyber 12, fraud 11, identity 7, drugs 3}`. Test is still weapons-rich
   (23.8 % vs 13.6 % in train) because category is confounded with concept and the bin-pack optimises
   whole clusters. Treat category as a covariate or report per-category numbers.
4. **The 9 remaining ClearHarm drops are now explained, not silent** (§4.2), but they are still
   dropped: 5 rows whose only verbatim harmful noun is multi-token, 3 where gpt-4o reports no
   verbatim harmful noun, 1 casing failure. Recovering them needs a non-verbatim (semantic)
   substitution contract, which `ds_common.build_conditions` does not support.
5. **`scripts/validate_dataset_v3.py`** (the plan's dedicated FATAL validator) still does not exist.
   `validate_data_integrity.py` covers ID / cluster / duplicate-prompt / single-token /
   post-template codeword-occurrence checks; the pairwise-straddling, control-leakage, TF-IDF and
   paraphrase-fidelity checks above are asserted inside `expand_concepts_v3.py --stage build` (which
   fails loudly) but the TF-IDF one is still run ad hoc.
