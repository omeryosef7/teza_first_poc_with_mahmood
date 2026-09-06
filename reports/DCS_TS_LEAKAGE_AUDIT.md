# DCS-TS Leakage Audit and Nuisance Baselines

Mandate section 6.6. CPU only: no GPU, no SLURM, no model, no network.
Producer: `scripts/dcs_ts_audit_leakage.py` (run with `--mutate` to reproduce the
RED-under-mutation table at the end).

Artifacts audited (built 2026-09-07, PHASE 3, entry R-098):

* `data/boombness_prompts/boombness_prompt_bank_ts116_{button,basket}_{bomb,knife,gun}.jsonl`
  — 22,272 rows each, 133,632 rows total, 116 domains.
* `data/boombness_prompts/dcs_ts116_domain_split.json` — `manifest_sha16=be7d2c772d814ef3`,
  field `dsplit`, 70 train / 23 validation / 23 test **domains**, seed 202609061.

Probe population as specified by the mandate: **cell C, `semantic_one_word`,
`n_examples=4`, classes {bomb, knife, gun}**, pooled over both codewords, trained on
the 70 TRAIN domains and tested on the 23 TEST domains of `dsplit`.
That is 6,960 rows = 116 domains x 60 rows/domain (10 prompt_ids x 3 concepts x 2
codewords); 4,200 train rows (70 domains) / 1,380 test rows (23 domains); the 23
validation domains (1,380 rows) are untouched.

Every number below was recomputed from the raw JSONL rows. No producer-written
summary field was used as evidence; `n_concept_occurrences` was used only as a
*target* to cross-check against our own regex recount (check C1b).

---

## 0. HEADLINE — the probe population is representationally vacuous

**CRITICAL.** In cell C `semantic_one_word`, the `full_prompt` is **byte-identical**
across bomb / knife / gun. The only fields that differ between the three banks for a
given `(codeword, prompt_id)` are `concept` and `target_semantic` — the labels
themselves. `prompt_sha16` is also identical, i.e. the producer's own hash agrees.

* 2,320/2,320 `(codeword, prompt_id)` triples in the probe population have identical
  `full_prompt` across the three concepts (check C9).
* Extended to **every** concept-free channel and **every** dose — cells {A, C} x
  {behavioral, semantic_one_word} x n_examples {0, 4, 8} — **14,848/14,848 triples are
  byte-identical**, covering 44,544 rows (check C13). Per-combination breakdown, all
  identical/total:
  A|behavioral n0 464/464, n4 2320/2320, n8 928/928;
  C|behavioral n0 464/464, n4 2320/2320, n8 928/928;
  A|semantic_one_word n0 464/464, n4 2320/2320, n8 928/928;
  C|semantic_one_word n0 464/464, n4 2320/2320, n8 928/928.
* Consequence, computed directly (check C12): the probe population's 6,960 rows
  collapse to **2,320 distinct texts, each appearing exactly 3 times carrying the label
  multiset {bomb, gun, knife}**. The Bayes-optimal accuracy of *any deterministic
  function of `full_prompt`* is therefore exactly **0.333333**.

This is not merely a bound on TF-IDF. A hidden-state probe reads a deterministic
function of the prompt tokens: identical prompt in, identical activations out. So on
this population **a representation probe is mathematically pinned to 1/3 as well** — it
cannot beat the nuisance bar, because the ceiling and the bar are the same number.
Any run that reports above-chance concept decoding on cell C `semantic_one_word` (or
`behavioral`) is reading its own labels, a cache key, or a row-order artifact — not a
representation.

This is the direct, expected price of the alignment fix described in the task brief
(the harm pools' `natural_word` is "bomb" for all 116 domains, and in cell C the
concept word is replaced by the codeword, so the knife/gun banks reduce to the bomb
bank's text). Alignment succeeded completely; it succeeded so completely that in the
concept-free channels there is nothing left to distinguish the concepts.

**Scope note (what this does NOT say).** It does not say the ts116 banks are unusable.
It says the *cell C `semantic_one_word` concept contrast* is unusable as a decoding
target. Cell C `semantic_forced_choice` does vary across concepts — but only because
the query names the concept ("...refer to a button or to a **bomb**?"). See section 1.

---

## 1. Concept-word occurrence table over `full_prompt`

Whole-word, case-insensitive match over the **entire** `full_prompt` (preamble + demo
block + query), not just `final_query_text`. Surface forms searched: bomb/bombs/
bombing/bombings, knife/knives, gun/guns/gunman/gunmen. Denominator is 3,712 rows for
every (cell, query_kind, concept) triple — 1,856 prompt_ids x 2 codewords, all three
doses pooled. 133,632 rows total.

| cell | query_kind | concept | rows | own concept word | any of the 3 | a *different* concept | own synonym | FLAG |
|---|---|---|---|---|---|---|---|---|
| A | behavioral | bomb | 3712 | 0 | 0 | 0 | 0 | — |
| A | behavioral | knife | 3712 | 0 | 0 | 0 | 80 | — |
| A | behavioral | gun | 3712 | 0 | 0 | 0 | 0 | — |
| A | semantic_one_word | bomb | 3712 | 0 | 0 | 0 | 0 | — |
| A | semantic_one_word | knife | 3712 | 0 | 0 | 0 | 80 | — |
| A | semantic_one_word | gun | 3712 | 0 | 0 | 0 | 0 | — |
| A | semantic_forced_choice | bomb | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| A | semantic_forced_choice | knife | 3712 | **3712** | 3712 | 0 | 80 | **NAMED** |
| A | semantic_forced_choice | gun | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| B | behavioral | bomb | 3712 | **3712** | 3712 | 0 | 130 | **NAMED** |
| B | behavioral | knife | 3712 | **3712** | 3712 | 0 | 68 | **NAMED** |
| B | behavioral | gun | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| B | semantic_one_word | bomb | 3712 | **3712** | 3712 | 0 | 130 | **NAMED** |
| B | semantic_one_word | knife | 3712 | **3712** | 3712 | 0 | 68 | **NAMED** |
| B | semantic_one_word | gun | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| B | semantic_forced_choice | bomb | 3712 | **3712** | 3712 | 0 | 130 | **NAMED** |
| B | semantic_forced_choice | knife | 3712 | **3712** | 3712 | 0 | 68 | **NAMED** |
| B | semantic_forced_choice | gun | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| C | behavioral | bomb | 3712 | 0 | 0 | 0 | 130 | — |
| C | behavioral | knife | 3712 | 0 | 0 | 0 | 68 | — |
| C | behavioral | gun | 3712 | 0 | 0 | 0 | 0 | — |
| C | semantic_one_word | bomb | 3712 | 0 | 0 | 0 | 130 | — |
| C | semantic_one_word | knife | 3712 | 0 | 0 | 0 | 68 | — |
| C | semantic_one_word | gun | 3712 | 0 | 0 | 0 | 0 | — |
| C | semantic_forced_choice | bomb | 3712 | **3712** | 3712 | 0 | 130 | **NAMED** |
| C | semantic_forced_choice | knife | 3712 | **3712** | 3712 | 0 | 68 | **NAMED** |
| C | semantic_forced_choice | gun | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| E | behavioral | bomb | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| E | behavioral | knife | 3712 | **3712** | 3712 | 0 | 80 | **NAMED** |
| E | behavioral | gun | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| E | semantic_one_word | bomb | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| E | semantic_one_word | knife | 3712 | **3712** | 3712 | 0 | 80 | **NAMED** |
| E | semantic_one_word | gun | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| E | semantic_forced_choice | bomb | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |
| E | semantic_forced_choice | knife | 3712 | **3712** | 3712 | 0 | 80 | **NAMED** |
| E | semantic_forced_choice | gun | 3712 | **3712** | 3712 | 0 | 0 | **NAMED** |

**Flagged: 24 of the 36 (cell x query_kind x concept) buckets, 89,088 of 133,632 rows
(66.67%), contain the row's own concept word in `full_prompt` at a rate of 3712/3712
(100.0%).** Those rows cannot be used to claim a hidden state *contains* the concept:
the prompt says it out loud. The flagged set is exactly {A, C} x semantic_forced_choice
plus all of cells B and E.

The 12 unflagged buckets — {A, C} x {behavioral, semantic_one_word}, 44,544 rows — have
**0/44,544** own-concept-word occurrences (check C1) and **0/44,544** occurrences of any
of the three concept words. But by section 0 they are also byte-identical across
concepts, so they carry zero concept information rather than "subtle" concept
information.

**The dichotomy is complete and there is no third case.** Across all 36 buckets the
own-concept rate is either 0/3712 or 3712/3712. There is no (cell x query_kind) in the
ts116 banks where the concept is recoverable from the prompt *and* not literally named
in it. That is the central structural fact this audit establishes.

`other concept` = 0 in all 36 buckets: no row ever contains a concept word belonging to
a different bank.

**Synonyms.** Own-concept synonyms were counted per-term so a generic term cannot
inflate a bucket. Only two terms ever fire, both from domain preamble/harm-pool prose:
"explosive"/"explosives" in bomb-bank rows (94 + 36 = 130/3712 rows in cells B and C;
0/3712 in cells A and E) and "blade"/"blades" in knife-bank rows (76 + 4 = 80/3712 in
cells A and E; 68/3712 in cells B and C). "gun" synonyms (firearm, pistol, rifle,
revolver, handgun, shotgun, ammunition) fire 0/3712 everywhere.
**These synonym hits are NOT leakage in the concept-free cells**: because the text is
byte-identical across banks there, the same 130 cell-C texts that contain "explosive"
are also the knife- and gun-labelled rows. The synonym is a property of the shared
context, not of the label. They *would* matter for cells B/E, where the text differs —
but there the concept word itself is present in 100% of rows anyway.

`n_concept_occurrences` cross-check: our independent regex recount of the base concept
word disagrees with the producer's field in **0/133,632** rows (check C1b). The
producer field is trustworthy — but the audit does not rely on it.

---

## 2. Length-only classifier

Logistic regression (standardised features), domain-grouped by `dsplit`,
train = 70 domains / 4,200 rows, test = 23 domains / 1,380 rows. Chance = 1/3.

| baseline | features | test acc | macro OvR AUROC | z vs chance | n_test |
|---|---|---|---|---|---|
| 2a length only | `n_chars` | **0.3333** | **0.5000** | 0.00 | 1380 |
| 2b token-free proxies | `n_chars`, `n_demos_emitted`, `n_preamble_lines` | **0.3333** | **0.5000** | 0.00 | 1380 |

Exactly at chance, and necessarily so: within the probe population all three feature
values are identical across the three concepts for a given prompt_id.

---

## 3. Prompt-text-only classifier (TF-IDF)

`TfidfVectorizer(ngram_range=(1,2), min_df=2, sublinear_tf=True)` over `full_prompt`,
multinomial logistic regression, same domain-grouped split.

| baseline | test acc | macro OvR AUROC | n features | n_test |
|---|---|---|---|---|
| 3a TF-IDF, unmasked | **0.3333** | **0.5000** | 26,852 | 1380 |
| 3b TF-IDF, concept words masked | **0.3333** | **0.5000** | 26,852 | 1380 |

**MASK GAP (cell C, semantic_one_word, n=4) = 0.3333 − 0.3333 = 0.0000.**

The mandate calls this the single most informative quantity in the report. It is
exactly zero, and the two arms are not merely close — the vocabulary is *unchanged* by
masking (26,852 features both times), because no concept word is present to mask. The
gap is zero for the strongest possible reason: the prompt neither names the answer nor
otherwise predicts it.

### 3c/3d — the same measurement where a leak provably exists (positive control)

A mask gap of zero is only meaningful if the machinery can register a non-zero one.
Same code path, same split, population changed to **cell B `semantic_one_word` n=4**
(6,960 rows; the concept word is present in 3712/3712 rows per bucket):

| baseline | test acc | macro OvR AUROC | n features | n_test |
|---|---|---|---|---|
| 3c cell B TF-IDF, unmasked | **1.0000** | **1.0000** | 27,560 | 1380 |
| 3d cell B TF-IDF, concept words masked | **0.3333** | **0.5000** | 26,144 | 1380 |

**Cell B mask gap = 0.6667.** The detector finds a real leak (check C10) and the mask
removes it entirely (check C11) — cell B collapses to exactly chance once the three
words are masked, which independently confirms that in cell B too the *only* textual
carrier of the concept is the concept word itself.

Contrast to carry forward: mask gap **0.0000** in cell C vs **0.6667** in cell B, from
one code path, on the same split, at the same n_test = 1380.

---

## 4. Template-ID-only classifier

Binary one-hot over `bank_block`, `family_slot`, `split`, `condition`, `query_kind`
only. Chance = 1/3.

| baseline | population | test acc | macro AUROC | n features | n_train | n_test |
|---|---|---|---|---|---|---|
| 4a template-id | probe population | **0.3333** | **0.5000** | 10 | 4200 | 1380 |
| 4b template-id | all of cell C (every query_kind, every dose; 33,408 rows) | **0.3333** | **0.5000** | 17 | 20160 | 6624 |

**At chance, as alignment requires — no CRITICAL finding here.** 4b is the stronger
version: it is run on a population where the template features genuinely vary (17
active feature values rather than 10, including all three query kinds and all three
doses), so its at-chance result is not an artifact of constant features. Alignment of
template metadata across the three concept banks is confirmed at 0/33,408 rows of
template-side leakage.

---

## 5. Codeword-only control (pipeline sanity check)

Same features, same domain-grouped split, same probe population, label switched to
`codeword` (button vs basket). Chance = 1/2.

| baseline | test acc | macro AUROC | n_test |
|---|---|---|---|
| 5a codeword from TF-IDF | **1.0000** | **1.0000** | 1380 |
| 5b codeword from TF-IDF, concept words masked | **1.0000** | **1.0000** | 1380 |
| 5c codeword from `n_chars` | **0.5000** | **0.5000** | 1380 |
| 5d codeword from template-id | **0.5000** | **0.5000** | 1380 |

The pipeline is not broken: on byte-identical machinery it recovers the codeword
perfectly from text (5a, check C6), and masking the *concept* words leaves it at 1.0000
as it should (5b) — the mask is targeted, not a blanket destruction of the text. 5c
lands at exactly 0.5000 because "button" and "basket" are both 6 characters, so the two
codeword banks have identical `n_chars` row for row; 5d at 0.5000 confirms template
metadata is also codeword-aligned. So: text distinguishes the codewords, length and
template do not, and nothing at all distinguishes the concepts.

---

## 6. The n_examples = 0 sharp test

Population: `n_examples=0`, cells {A, C} x {behavioral, semantic_one_word} — 928
prompt_ids per bank (232 x 2 cells x 2 query kinds), 5,568 rows pooled over 3 concepts
and 2 codewords. Domain-grouped: 3,360 train rows (70 domains) / 1,104 test rows (23
domains). Chance = 1/3.

| baseline | test acc | macro AUROC | n features | n_test |
|---|---|---|---|---|
| 6a TF-IDF | **0.3333** | **0.5000** | 9,215 | 1104 |
| 6b `n_chars` | **0.3333** | **0.5000** | 1 | 1104 |
| 6c template-id | **0.3333** | **0.5000** | 8 | 1104 |

All three land at exactly chance (checks C7, C7b, C7c). **No leak found.** The byte
identity underlying this test was verified independently rather than assumed: 464/464
triples identical for each of the four (cell x query_kind) combinations at n=0 (check
C13 breakdown), i.e. 1,856/1,856 triples over 5,568 rows.

Note that at n=0 the sharp test is *weaker* than it looks in this bank set, because
section 0 shows n=4 and n=8 are equally byte-identical. The n=0 test is meant to be the
one place where identity is guaranteed; here identity is everywhere.

---

## 7. Domain-level grouping

Check C8, re-derived from the row-level `domain` field joined against the manifest:

* train domains present in the fitted data: **70**; test domains: **23**; **overlap: 0**.
* 23 validation domains (1,380 probe rows) are never touched by any fit in this audit.
* 4,200 train rows + 1,380 test rows = 5,580 rows bound by the check (the remaining
  1,380 of the 6,960 are the validation domains).
* `manifest_sha16=be7d2c772d814ef3`, field `dsplit`, read from
  `dcs_ts116_domain_split.json`; the script hard-exits if `field_name != "dsplit"`.
* The within-domain `split` field (dev/heldout) is used only as a *nuisance feature* in
  the template-id baseline. It is never used to partition. All 116 domains straddle it;
  it is not a domain split and is not treated as one here.

Under the `corrupt_split` mutation (5 test domains forced into train as well) the check
goes RED — see the mutation table.

---

## 8. Check register

19 checks, 19 PASS, 0 FAIL. Every check fails loudly on a zero-row binding (the
`Checks.record` helper rewrites any check that bound 0 rows to FAIL with
"BOUND ZERO ROWS (vacuous check)"), and the `empty_population` mutation exercises that
path.

| check | result | rows bound | what it asserts |
|---|---|---|---|
| C1 concept-free channels have zero own concept word | PASS | 44,544 | 0/44,544 |
| C1b recount matches producer field | PASS | 133,632 | 0/133,632 disagreements |
| C2 length-only at chance | PASS | 1,380 | acc 0.3333, z=0.00 |
| C2b length proxies at chance | PASS | 1,380 | acc 0.3333, z=0.00 |
| C3 text-only at chance | PASS | 1,380 | acc 0.3333, z=0.00 |
| C4 masked text at chance | PASS | 1,380 | acc 0.3333, z=0.00 |
| C4b mask gap is zero | PASS | 1,380 | 0.3333 − 0.3333 = 0.0000 |
| C5 template-id at chance (probe pop) | PASS | 1,380 | acc 0.3333 |
| C5b template-id at chance (all cell C) | PASS | 6,624 | acc 0.3333 |
| C6 codeword positive control detects signal | PASS | 1,380 | acc 1.0000 ≥ 0.95 |
| C7 n=0 TF-IDF at chance | PASS | 1,104 | acc 0.3333 |
| C7b n=0 length at chance | PASS | 1,104 | acc 0.3333 |
| C7c n=0 template-id at chance | PASS | 1,104 | acc 0.3333 |
| C8 domain grouping disjoint | PASS | 5,580 | 70/23, overlap 0 |
| C9 probe-pop text identical across concepts | PASS | 2,320 triples | 2320/2320 |
| C10 leak detector finds a real leak (cell B) | PASS | 1,380 | acc 1.0000 |
| C11 masking removes the cell-B leak | PASS | 1,380 | 1.0000 → 0.3333 |
| C12 Bayes bound from text is chance | PASS | 6,960 | 0.333333 over 2,320 distinct texts |
| C13 all concept-free channels identical | PASS | 44,544 | 14,848/14,848 triples |

Statistical rule: a baseline is judged above chance only if the one-sided binomial
z of its test accuracy against 1/3 (or 1/2 for the codeword control) exceeds 3.0, or
its macro OvR AUROC exceeds 0.55. Every observed z was 0.00.

---

## 9. Mutation harness — proof the checks go RED

`python scripts/dcs_ts_audit_leakage.py --mutate`. Seven mutations, 15 check
transitions, **15/15 RED as required, 0 "DID NOT GO RED"**.

| mutation | what it does | check | before → after |
|---|---|---|---|
| `inject_concept_word` | appends the row's own concept word to `full_prompt` | C1 | PASS → FAIL |
| | | C3 | PASS → FAIL |
| | | C4b (mask gap) | PASS → FAIL |
| | | C12 (Bayes bound) | PASS → FAIL |
| | | C13 (identity) | PASS → FAIL |
| `length_leak` | pads `n_chars` by 500 x concept index | C2 | PASS → FAIL |
| | | C2b | PASS → FAIL |
| `template_leak` | appends the concept to `bank_block` | C5 | PASS → FAIL |
| | | C5b | PASS → FAIL |
| `corrupt_split` | forces 5 test domains into train as well | C8 | PASS → FAIL |
| `empty_population` | selects cell `Z`, so the population binds 0 rows | C9 | PASS → FAIL |
| | | C3 | PASS → FAIL |
| | | C2 | PASS → FAIL |
| `break_codeword_control` | erases the codeword from the text | C6 | PASS → FAIL |
| `unmask_cellB` | turns the concept mask into a no-op | C11 | PASS → FAIL |

The last two are the anti-vacuity mutations: they break the *positive* controls, proving
that C6 and C11 are capable of failing and are therefore worth something when they pass.

---

## 10. What is UNKNOWN

* **Whether knife and gun "install" behaviourally.** Untouched by this audit — it is a
  model-side question and this audit ran no model. Note however that section 0 makes it
  a strange question in the concept-free channels: the knife prompt *is* the bomb
  prompt, byte for byte, so any behavioural difference between them can only come from
  the label side (scoring/target), never from the input.
* **Whether a probe trained on cell C `semantic_forced_choice` measures anything but the
  named concept word.** Not measurable without a model; but the text-side prior is bad —
  the concept word is present in 3712/3712 rows there.
* **Tokenizer-level nuisances** (token counts, tokenizer-specific length). Not measured:
  measuring them requires a tokenizer, which is a model artifact. `n_chars` is a strict
  token-free proxy. To close this I would need the target tokenizer offline (no weights),
  which is out of scope for a CPU-only, no-model-loading audit.
* **Semantic synonym leakage beyond the hand-written lists** in `CONCEPT_SYNONYMS`.
  An embedding-based synonym sweep would need a model. In the concept-free cells this is
  moot (identical text), but it remains open for cells B/E.

---

## THE BAR

Strongest nuisance baseline on the probe population (cell C, `semantic_one_word`,
n_examples=4, 70 train domains / 23 test domains, 1,380 test rows) across the length,
text, masked-text and template-id families — all four tie at the floor:

**THE PROBE MUST BEAT: length-only / TF-IDF-text / masked-text / template-id (all tied) = 0.3333 (accuracy) / 0.5000 (AUROC).**

And the accompanying warning, which matters more than the bar: on this population the
Bayes-optimal accuracy of any function of the prompt is also **0.333333**, so a
representation probe **cannot** beat the bar. A reported number above 1/3 here is a
pipeline leak, not a result. If a concept probe is wanted, the population has to change
— and every alternative population in these banks names the concept in 3712/3712 rows.
