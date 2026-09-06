# DCS gate G5 — leakage audit and nuisance baselines on the `ts116n` bank

**Script:** `scripts/dcs_ts116n_audit_leakage.py` (CPU only; no GPU, no model weights, no
SLURM, no network).
**Reproduce:** `python scripts/dcs_ts116n_audit_leakage.py --mutate --json <path>`
**Preregistration:** `configs/dcs_ts_pr046.json` (FROZEN, `DCS-PR-046`), read at runtime.
**Bank family:** `ts116n`, built 2026-09-07, entry R-101.
**Date of this run:** 2026-09-07.

`scripts/dcs_ts_audit_leakage.py` was **not** edited. Its logic is reused in the new file;
the assertions that were load-bearing there and are FALSE HERE BY DESIGN (cell-C byte
identity across concepts, Bayes bound == 1/3, "mask gap == 0 proves no leak") were replaced
rather than carried forward.

---

## 0. Read this before reusing any earlier leakage number

The previous bank family (`ts116`) drew the harm pool with the concept word *already*
replaced by the codeword. When a harm sentence was shared across concepts, the three arms
were **byte-identical**, so every text/length/register baseline was pinned to exactly 1/3 by
arithmetic (C-074). Every number in the old leakage audit was degenerate-at-chance **by
construction** and carries no information about `ts116n`.

`ts116n` generates the harm pool **per concept**: the manipulation lives in the predicates
("a package resembling a *bomb*" vs "confiscated a *knife* before boarding"), not in a word
that is substituted away. Cell C therefore differs across concepts in 115/115 domains (G2),
while cell A stays byte-identical (G3). **The consequence for this gate is that the nuisance
baselines are now real, and several of them are far above chance.** That is the finding.

---

## 1. Population, and how it was bound

| item | value |
|---|---|
| selection field | `cell == "C"` (**not** `condition == "natural_doublespeak"` — that binds zero rows, A-039) |
| `query_kind` | `semantic_one_word` |
| `n_examples` | 4 |
| classes | `bomb` / `knife` / `gun`, chance = 1/3 |
| codewords | `button` and `basket`, pooled |
| preregistered exclusion | `restaurant_kitchen`, dropped from **everything**, at load time |
| analysed domains | **115** = 69 train / 23 validation / 23 test |
| probe rows | **6900** = 115 domains x 10 rows x 2 codewords x 3 concepts |
| train rows | **4140** (69 domains) |
| test rows | **1380** (23 domains) |
| validation | **1380 rows / 23 domains — never read by this script** |
| split manifest | `dcs_ts116_domain_split.json`, `manifest_sha16 = be7d2c772d814ef3`, field `dsplit` |

All six `bank_rows_sha16` values recomputed **from the raw rows** (repo convention
`src/boombness/common.py:rows_sha16` — sha256 over per-row `prompt_sha16`, ordered by
`prompt_id`) match the preregistration exactly:
`button_bomb 9d1f03747189e1bd`, `button_knife 9ef9688609001104`, `button_gun b865d8b991023ac7`,
`basket_bomb 09882763cb4b0a24`, `basket_knife 71128bfa7631c005`, `basket_gun ab5ec1d45fb90cd3`.

---

## 2. HEADLINE

```
THE PROBE MUST BEAT: N5c_tfidf_demoblock_conceptmasked = 0.8870 / 0.9829
```

(the same TF-IDF over the whole `full_prompt` gives 0.8725 / 0.9751; both are computed on the
23 untouched test domains, trained on the 69 train domains, concept words masked.)

```
N4 VERDICT: length-only accuracy = 0.4174 (chance 0.3333, z = +6.62, macro OvR AUROC 0.5750)
            -- WELL ABOVE CHANCE. The preregistered length-matching rule IS TRIGGERED.
```

The prereg's `deferred_decision_rule` — *"If N4 length-only comes out well above chance,
over-generate and length-match the 40 kept sentences per pool — prompt-only and outcome-blind"*
— was recorded **before** N4 was measured. N4 is +8.4 accuracy points over chance at
z = +6.62 on 1380 held-out rows, i.e. not a borderline call. The rule fires.

---

## 3. Check ledger

29 checks. A check that binds zero rows is recorded as FAIL, never PASS. Checks are split into
**structural** (must pass; a failure is a defect in the bank or the alignment) and
**measurement** (the number is the deliverable; RED is an expected outcome on `ts116n` and is
labelled `MEASUREMENT` in the script output so it cannot be quietly reported as a pass).

### 3.1 Structural checks — 24 checks, 4 FAIL

| check | result | n bound | evidence |
|---|---|---|---|
| `G5_00_excluded_domain_absent_and_population_is_115` | PASS | 6900 | `restaurant_kitchen` rows = 0; distinct domains = 115; 69/23/23 |
| `G5_bank_rows_sha16_matches_preregistration` | PASS | 6 | all six recomputed hashes equal the frozen values |
| `G5_01_primary_channel_zero_own_and_any_concept_word` | **FAIL** | 11040 | 30/11040 own-concept rows, 30/11040 any-concept rows |
| `G5_01_bomb_primary_channel_zero_concept_word` | PASS | 3680 | own = 0, any = 0 |
| `G5_01_knife_primary_channel_zero_concept_word` | **FAIL** | 3680 | own = 30, any = 30 |
| `G5_01_gun_primary_channel_zero_concept_word` | PASS | 3680 | own = 0, any = 0 |
| `G5_01b_recount_matches_producer_field` | PASS | 132480 | 0 rows where our regex recount disagrees with `n_concept_occurrences` |
| `G5_01d_probe_population_n4_is_concept_word_free` | **FAIL** | 6900 | 16/6900 probe rows print their own concept word, 4 of them in TEST domains |
| `G5_07_domain_grouping_disjoint` | PASS | 5520 | 69 train / 23 test domains, overlap = 0 |
| `G5_08_no_cross_domain_sentence_leakage` | **FAIL** | 1380 | 8/1380 test rows share a verbatim demo sentence with a different-domain train row |
| `G5_08b_sentence_leakage_is_not_wholesale` | PASS | 1380 | 8/1380 = 0.58%, far below the 50% that would mean shared pools |
| `G5_06_N6_templateid_at_chance` | PASS | 1380 | acc 0.3333, AUROC 0.5000, z = 0.00 |
| `G5_06b_N6_templateid_all_cellC_at_chance` | PASS | 6624 | acc 0.3333, AUROC 0.5000, z = 0.00 |
| `G5_09_N1_n0_tfidf_at_chance` | PASS | 276 | acc 0.3333, AUROC 0.5000 |
| `G5_09b_N1_n0_length_at_chance` | PASS | 276 | acc 0.3333, AUROC 0.5000 |
| `G5_09c_N1_n0_hedge_register_at_chance` | PASS | 276 | acc 0.3333, AUROC 0.5000 |
| `G5_09d_N1_n0_templateid_at_chance` | PASS | 276 | acc 0.3333, AUROC 0.5000 |
| `G5_10_cellA_control_text_at_chance` | PASS | 1380 | acc 0.3333, AUROC 0.5000 |
| `G5_10b_cellA_control_length_at_chance` | PASS | 1380 | acc 0.3333, AUROC 0.5000 |
| `G5_10c_cellA_control_hedge_register_at_chance` | PASS | 1380 | acc 0.3333, AUROC 0.5000 |
| `G5_11_codeword_positive_control_detects_signal` | PASS | 1380 | button-vs-basket TF-IDF acc 1.0000 / AUROC 1.0000 |
| `G5_12_leak_detector_finds_a_real_text_leak` | PASS | 1380 | cell-B TF-IDF acc 1.0000 / AUROC 1.0000 |
| `G5_13_masker_deletes_every_printed_concept_word` | PASS | 6900 | 0/6900 cell-B rows retain a concept word after masking |
| `G5_05_probe_mask_gap_is_zero` | PASS | 1380 | 0.8725 − 0.8725 = 0.0000 |

### 3.2 Measurement checks — 5, all RED, all expected

| check | acc | macro AUROC | z vs 1/3 |
|---|---|---|---|
| `G5_02_N4_length_only_at_chance` | 0.4174 | 0.5750 | +6.62 |
| `G5_02b_N4_length_plus_structure_at_chance` | 0.4174 | 0.5750 | +6.62 |
| `G5_03_N5_text_masked_at_chance` | 0.8725 | 0.9751 | +42.49 |
| `G5_04_hedge_only_at_chance` | 0.4768 | 0.6350 | +11.31 |
| `G5_04b_register_only_at_chance` | 0.4406 | 0.6277 | +8.45 |

---

## 4. Item 1 — concept-word occurrence table over `full_prompt`

All six banks, `restaurant_kitchen` excluded, whole-word case-insensitive matching on
`bomb|bombs|bombing|bombings`, `knife|knives`, `gun|guns|gunman|gunmen`. Denominator is
**3680 rows** per (cell, query_kind, concept) = 115 domains x (10 + 2 + 4 slots across the
three doses) x 2 codewords. `own` = the row's own concept; `any` = any of the three;
`other` = a concept that is not the row's own; `syn` = own-concept synonym.

| cell x query_kind | concept | rows | own | any | other | syn |
|---|---|---|---|---|---|---|
| A x behavioral | bomb / knife / gun | 3680 each | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 80 / 0 |
| A x semantic_one_word | bomb / knife / gun | 3680 each | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 80 / 0 |
| A x semantic_forced_choice | bomb / knife / gun | 3680 each | 3680 / 3680 / 3680 | 3680 each | 0 / 0 / 0 | 0 / 80 / 0 |
| B x behavioral | bomb / knife / gun | 3680 each | 3680 each | 3680 each | 0 / 0 / 0 | 144 / 552 / 248 |
| B x semantic_one_word | bomb / knife / gun | 3680 each | 3680 each | 3680 each | 0 / 0 / 0 | 144 / 552 / 248 |
| B x semantic_forced_choice | bomb / knife / gun | 3680 each | 3680 each | 3680 each | 0 / 0 / 0 | 144 / 552 / 248 |
| **C x behavioral** | bomb / knife / gun | 3680 each | **0 / 30 / 0** | 0 / 30 / 0 | 0 / 0 / 0 | 144 / 552 / 248 |
| **C x semantic_one_word (primary)** | bomb / knife / gun | 3680 each | **0 / 30 / 0** | 0 / 30 / 0 | 0 / 0 / 0 | 144 / 552 / 248 |
| C x semantic_forced_choice | bomb / knife / gun | 3680 each | 3680 each | 3680 each | 0 / 0 / 0 | 144 / 552 / 248 |
| E x behavioral / one_word / forced_choice | bomb / knife / gun | 3680 each | 3680 each | 3680 each | 0 / 0 / 0 | 0 / 80 / 0 |

The forced-choice query kind names all three concepts in its option list, which is why cells
A/C are 3680/3680 there; that is the display channel, not the primary channel, and it is
expected. **No row anywhere names a concept that is not its own** (`other = 0` in all 36
buckets), so there is no cross-concept contamination.

### 4.1 SAY IT LOUDLY: the primary channel is NOT concept-word-free

> **The `knife` arm prints the word `knives` in 30/11040 cell-C x `semantic_one_word` rows —
> 16/6900 of them in the `n_examples = 4` probe population, of which 4 are in TEST domains.
> `bomb` is 0/3680 and `gun` is 0/3680. The contamination is one-sided.**

Mechanism: the builder substitutes the **singular** concept word for the codeword, and G1's
verifier counts `\bknife\b` occurrences per harm sentence and requires exactly one. A sentence
containing both `knife` and `knives` passes G1 (one singular hit) and emerges from substitution
with the plural intact. This is the matcher/scope bug class: the audit failed on the matcher,
not on the corpus. The identical `re.escape(cc)` pattern is why `bomb`/`bombs` and `gun`/`guns`
were not hit — the harm pools happen not to pair those forms in one sentence.

Affected rows, `n_examples = 4` probe population, per codeword (identical for `button` and
`basket`, so double each count for the pooled total of 16):

| domain | dsplit | rows per codeword |
|---|---|---|
| `blood_bank` | train | 3 |
| `care_home_store` | train | 1 |
| `cheese_dairy` | train | 1 |
| `hospital_supply` | validation | 1 |
| `instructional` | **test** | 1 |
| `physio_gym` | **test** | 1 |

The 8 distinct offending sentences (x2 codeword surfaces = 16):

- `The <CW> sharpener was located next to the supply of sterile knives.`
- `The <CW> rack was overcrowded, making it difficult to access clean knives.`
- `The <CW> wash station was clogged, preventing proper cleaning of the knives.`
- `The <CW> rack was noted as disorganized, with several knives not in their designated spots.`
- `Several knives were missing from the designated <CW> block in the supply room.`
- `For industrial settings, ensure that knives are stored in <CW> blocks or magnetic strips.`
- `The <CW> block in the maturing room contained only sterilized knives.`
- `The <CW> sharpening station was not functioning properly, leading to dull knives in use.`

**Magnitude and consequence.** 16/6900 = 0.23% of the probe population, 4/1380 = 0.29% of the
test rows. Concept-masking the text changes the TF-IDF baseline by exactly
0.0000 accuracy (0.8725 masked and unmasked, byte-identical confusion matrices), so the printed
plural contributes nothing measurable to the *text* bar. It is nevertheless a real leak on the
probe's own channel and it is reported as a defect, not waved away: 4 test rows in 2 test
domains (`instructional`, `physio_gym`) hand the label to any reader that can see the token
`knives`. Recommended remedy, prompt-only and outcome-blind: extend the substitution and the
G1 matcher to the full surface-form set (`knife|knives`, `bomb|bombs|bombing|bombings`,
`gun|guns|gunman|gunmen`) and rebuild, or drop those 6 domains' knife rows. **Until one of
those is done, any per-class result on the `knife` arm carries this asterisk.**

---

## 5. Item 2 — N4, length-only

Domain-grouped: fit on 4140 train rows (69 domains), evaluated on 1380 test rows (23 domains).
Multinomial logistic regression, features standardised on train only.

| baseline | features | accuracy | domain-mean acc | macro OvR AUROC | z vs 1/3 |
|---|---|---|---|---|---|
| `N4a_length_only_nchars` | `n_chars` | **0.4174** | 0.4174 | **0.5750** | +6.62 |
| `N4b_length_plus_structure` | `n_chars`, `n_demos_emitted`, `n_preamble_lines` | 0.4174 | 0.4174 | 0.5750 | +6.62 |
| `N4c_length_only_cellA_control` | `n_chars`, on the byte-identical cell-A population | 0.3333 | 0.3333 | 0.5000 | 0.00 |

`N4b` reproduces `N4a` to the digit because `n_demos_emitted` and `n_preamble_lines` are
**constant** across the probe population (4 and 10 respectively, verified per concept), so they
carry zero bits. The number is a one-feature result.

Per-class OvR AUROC: bomb 0.6198, knife 0.6254, gun 0.4797. The confusion matrix shows the
mechanism directly — the classifier over-predicts `bomb` (894 of 1380 predictions) because bomb
prompts are the longest:

| true \ pred | bomb | knife | gun |
|---|---|---|---|
| bomb | 366 | 56 | 38 |
| knife | 250 | 166 | 44 |
| gun | 278 | 138 | 44 |

Re-derived length descriptives on the probe population (mean +/- SD of `n_chars` over 2300 rows
per concept): **bomb 1085.7 +/- 65.9, gun 1074.3 +/- 72.3, knife 1055.0 +/- 67.6.** Mean demo
sentence length over the distinct demo sentences actually used in the probe population: bomb
84.1, gun 81.2, knife 76.4 characters — an independent re-derivation of the prereg's
prompt-only 82 / 78 / 75.

**Verdict, stated plainly: N4 is not near chance. It is well above chance** (+8.4 points,
z = +6.62, AUROC 0.575 vs 0.500) **and the preregistered length-matching rule is TRIGGERED.**
The cell-A control at exactly 0.3333 / 0.5000 shows the estimator is not manufacturing this;
the length gap is a property of the ts116n harm pools.

---

## 6. Item 3 — N5, prompt-text-only TF-IDF

Word 1-2 grams, `min_df=2`, sublinear TF, multinomial LR, vocabulary fit on TRAIN domains only.

| baseline | accuracy | domain-mean acc | macro OvR AUROC | features |
|---|---|---|---|---|
| `N5a_tfidf_fullprompt` (unmasked) | 0.8725 | 0.8725 | 0.9751 | 41639 |
| `N5b_tfidf_fullprompt_conceptmasked` | **0.8725** | 0.8725 | **0.9751** | 41639 |
| `N5c_tfidf_demoblock_conceptmasked` | **0.8870** | 0.8870 | **0.9829** | 31489 |
| `N5d_tfidf_cellA_control` | 0.3333 | 0.3333 | 0.5000 | — |

Masking is a **no-op to four decimal places** — same accuracy, same AUROC, byte-identical
confusion matrix — because outside the 16 rows of section 4.1 the concept word is simply not
present in cell C. **The masked number is therefore not a discount on the unmasked one; it is
the same number, and it is the bar.**

Restricting the text to the demonstration block (dropping the shared preamble and the shared
query, which are pure noise for this label) *raises* the baseline to 0.8870 / 0.9829. That is
the strongest nuisance baseline in this audit.

Per-class OvR AUROC for `N5c`: bomb 0.9956, knife 0.9877, gun 0.9655. Confusion:

| true \ pred | bomb | knife | gun |
|---|---|---|---|
| bomb | 440 | 6 | 14 |
| knife | 0 | 444 | 16 |
| gun | 16 | 104 | 340 |

**Quantified, as asked: with the concept words masked and the split domain-grouped, a bag of
word bigrams recovers the installed concept on 88.7% of held-out-domain rows at macro AUROC
0.983.** The hedging asymmetry is not a footnote — it is nearly the whole label.

---

## 7. Item 4 — hedge-only and register-only

Hand-specified features, no learned vocabulary. Hedge features are counts of exactly the five
patterns the preregistration measured (`resembl*`, `simulat*`, `drill(s)`, `false alarm`,
`look(s|ed|ing) like`). Register features are mean sentence length in characters, sentence
count, word count, type-token ratio, mean word length, counts of `, . ; : - ' " ( ?`, digit
count and uppercase count. 16 register features, 5 hedge features.

| baseline | n features | accuracy | macro OvR AUROC | z vs 1/3 |
|---|---|---|---|---|
| `H1_hedge_only_fullprompt` | 5 | **0.4768** | **0.6350** | +11.31 |
| `H2_register_only_fullprompt` | 16 | 0.4406 | 0.6277 | +8.45 |
| `H3_hedge_plus_register` | 21 | **0.5174** | **0.7159** | +14.44 |
| `H4_hedge_plus_register_cellA_control` | 21 | 0.3333 | 0.5000 | 0.00 |

Per-class AUROC for `H3`: bomb 0.7847, knife 0.7602, gun 0.6029.

**Five hand-written regexes beat chance by 14.3 points.** Twenty-one features with no lexical
content at all reach 51.7% / 0.716 — that is 43% of the way from chance to the full TF-IDF
bar on accuracy. So the leak is not only content: a substantial slice is pure **register**.
`H1`'s confusion matrix makes the mechanism unmistakable — with only hedge counts available the
classifier never predicts `gun` at all (0 of 1380 predictions), splitting everything between
`bomb` (hedged) and `knife` (unhedged):

| true \ pred | bomb | knife | gun |
|---|---|---|---|
| bomb | 230 | 230 | 0 |
| knife | 32 | 428 | 0 |
| gun | 82 | 378 | 0 |

Re-derived hedge rates over the **distinct demo sentences actually used in the probe
population** (not inherited from the prereg): **bomb 1228/9180 = 13.38%, gun 284/9196 = 3.09%,
knife 12/9182 = 0.13%.** This independently reproduces the prereg's prompt-only 14.1 / 3.4 / 0.2
and confirms the ~100x bomb:knife gap is real in the rows that will actually be extracted.

---

## 8. Item 5 — N6, template-id-only

Features: `bank_block`, `family_slot`, `split`, `condition`, `query_kind`, one-hot, nothing else.

| baseline | n train | n test | accuracy | macro AUROC |
|---|---|---|---|---|
| `N6a_templateid_probe_pop` | 4140 | 1380 | **0.3333** | **0.5000** |
| `N6b_templateid_all_cellC` (all doses, all query kinds) | 19872 | 6624 | **0.3333** | **0.5000** |

Exactly at chance, z = 0.00, on both populations. Alignment is intact; **the run is not VOID on
this criterion.** Note the population is exactly balanced (460 rows per concept in test), so
0.3333 here is the majority-class floor and there is nothing above it to find: in the probe
population `bank_block` is constant (`cds_n4_sow`), `condition` is constant
(`natural_doublespeak`), `family_slot` takes 5 values and `split` 2, and none of them varies
with concept. That is the definition of "at chance by construction".

---

## 9. Item 6 — N1, the `n_examples = 0` sharp test

Cell C, `semantic_one_word`, `n_examples = 0`: **1380 rows** (115 domains x 2 rows x 2 codewords
x 3 concepts), split domain-grouped into **828 train rows (69 domains) / 276 test rows (23
domains)**; the remaining 276 validation rows are not read. There are no demonstrations in these prompts, so nothing concept-specific can be
present.

| baseline | accuracy | macro AUROC |
|---|---|---|
| `N1a_n0_tfidf` | 0.3333 | 0.5000 |
| `N1b_n0_length` | 0.3333 | 0.5000 |
| `N1c_n0_hedge_register` | 0.3333 | 0.5000 |
| `N1d_n0_templateid` | 0.3333 | 0.5000 |

All four land exactly at chance on 276 test rows. This is the sharp test: remove the
demonstrations and every baseline that was above chance in sections 5-7 collapses to 1/3,
which localises the entire leak to the demonstration block.

---

## 10. Item 7 — domain grouping, and its mutation

`G5_07_domain_grouping_disjoint`: 69 train domains, 23 test domains, **overlap = 0**, 5520 rows
bound, `manifest_sha16 = be7d2c772d814ef3`. Validation (23 domains, 1380 probe rows) is loaded
by nothing in this script.

Proof the assertion can fail: mutation `corrupt_split` relabels the first 5 test domains so
that their rows are emitted into **both** the train and the test list. The check goes
PASS -> FAIL, reporting overlap = 5. See section 12.

---

## 11. Item 8 — cross-domain sentence leakage

Every probe row's `demo_block` was split into its sentences; a test row leaks if one of its
sentences appears verbatim in a train row belonging to a **different** domain.

| quantity | ts116n | previous bank |
|---|---|---|
| test rows sharing a demo sentence with a different-domain train row | **8 / 1380 (0.58%)** | 72 / 3864 (1.86%) |
| distinct leaked sentences | 8 (= 4 sentences x 2 codeword surfaces) | — |
| distinct test-domain demo sentences | 5518 | — |
| distinct train-domain demo sentences | 16536 | — |

All eight, with their concept, test domain and the train domain they collide with:

| concept | test domain | train domain | sentence (`<CW>` = `button`/`basket`, one row each) |
|---|---|---|---|
| bomb | `feed_mill` | `solar_array` | `Documentation of the <CW> threat incident was filed for future reference.` |
| bomb | `helipad_base` | `rail_depot` | `Security footage showed an unknown individual leaving a bag that resembled a <CW>.` |
| bomb | `planetarium` | `bus_garage` | `A warning was issued about a reported <CW> threat at a nearby facility.` |
| gun | `joinery_shop` | `council_depot` | `Documents regarding <CW> safety were distributed to all employees.` |

Four distinct English sentences, three of them in the `bomb` arm, one in `gun`, none in `knife`.
Each affected row shares **one of its four** demo sentences. The rate is a third of the previous
bank's, and `G5_08b` confirms it is not wholesale (0.58% vs the 50% that would indicate pools
shared across the split). It is still recorded as a FAIL against a zero-tolerance criterion,
because a domain-generic sentence like *"Documents regarding <CW> safety were distributed to all
employees"* is exactly the kind of string a TF-IDF baseline can memorise from train and reuse on
test.

---

## 12. Item 9 — the mutation harness (`--mutate`)

`python scripts/dcs_ts116n_audit_leakage.py --mutate` re-runs the entire audit under ten
deliberate corruptions and asserts that the named checks flip PASS -> FAIL. **16/16 targets went
RED; none was "DID NOT GO RED".**

| mutation | what it does | target check | baseline -> mutated |
|---|---|---|---|
| `inject_concept_word` | appends the row's own concept word to `full_prompt` | `G5_01_bomb_primary_channel_zero_concept_word` | PASS -> **FAIL** |
| | | `G5_01_gun_primary_channel_zero_concept_word` | PASS -> **FAIL** |
| | | `G5_05_probe_mask_gap_is_zero` | PASS -> **FAIL** |
| `length_leak` | pads `n_chars` by 500 x concept index | `G5_10b_cellA_control_length_at_chance` | PASS -> **FAIL** |
| `template_leak` | appends the concept to `bank_block` | `G5_06_N6_templateid_at_chance` | PASS -> **FAIL** |
| | | `G5_06b_N6_templateid_all_cellC_at_chance` | PASS -> **FAIL** |
| `corrupt_split` | emits 5 test domains into train as well | `G5_07_domain_grouping_disjoint` | PASS -> **FAIL** |
| `empty_population` | selects `cell == "Z"`, binding zero rows | `G5_00_excluded_domain_absent_and_population_is_115` | PASS -> **FAIL** |
| | | `G5_06_N6_templateid_at_chance` | PASS -> **FAIL** |
| | | `G5_08b_sentence_leakage_is_not_wholesale` | PASS -> **FAIL** |
| | | `G5_10_cellA_control_text_at_chance` | PASS -> **FAIL** |
| `break_codeword_control` | erases `button`/`basket` from the text | `G5_11_codeword_positive_control_detects_signal` | PASS -> **FAIL** |
| `unmask_cellB` | turns the concept masker into the identity | `G5_13_masker_deletes_every_printed_concept_word` | PASS -> **FAIL** |
| `hedge_leak` | adds a concept-graded hedge phrase to cell-A text | `G5_10c_cellA_control_hedge_register_at_chance` | PASS -> **FAIL** |
| `plant_shared_sentence` | copies a train-domain sentence into every test row | `G5_08b_sentence_leakage_is_not_wholesale` | PASS -> **FAIL** |
| `reintroduce_excluded_domain` | stops excluding `restaurant_kitchen` | `G5_00_excluded_domain_absent_and_population_is_115` | PASS -> **FAIL** |

Two design points behind this table, both consequences of "a check that cannot fail is worth
nothing":

* **Where the real bank is already RED, the mutation must be aimed at a sibling that is GREEN.**
  `G5_01` is FAIL at baseline (the `knives` leak), so a mutation cannot demonstrate it going red.
  The check is therefore also recorded **per concept**, and the two clean arms (`bomb`, `gun`)
  are the mutation targets — proving the detector fires, while the `knife` arm reports the
  genuine defect. Likewise the zero-tolerance sentence-leak check `G5_08` is FAIL at baseline
  (8 rows), so the mutation targets its companion `G5_08b`, which is GREEN at 0.58% and goes RED
  when a train sentence is planted in every test row.
* **The nuisance baselines that are legitimately above chance are mutated on a control
  population, not on the probe population.** Cell A x `semantic_one_word` x `n_examples = 4`
  (1380 test rows) is byte-identical across the three concepts by G3, so length, text, and
  hedge/register baselines there are exactly 0.3333 / 0.5000. `length_leak` and `hedge_leak`
  make that control go red, which is what proves those estimators can see a length or register
  signal when one exists — and therefore that the 0.4174 and 0.4768 measured on cell C are
  signal in the bank, not artefacts of the estimator.

Every check also fails loudly on zero binding: `Checks.record()` rewrites any `n_bound <= 0`
result to FAIL with `BOUND ZERO ROWS (vacuous check)`, which is what the `empty_population`
mutation exercises against four separate checks at once.

---

## 13. What this gate hands to the probe

1. **G5 does not VOID the run.** N6 template-id-only is exactly at chance on both populations
   (0.3333 / 0.5000, z = 0.00), the domain grouping is disjoint, and the `n_examples = 0`
   population is at chance on all four feature families.
2. **The bar is high and it is honest.** A masked bag-of-bigrams over the demonstration block
   reaches 0.8870 / 0.9829 across held-out domains. A linear probe on the codeword's hidden
   state that reports, say, 0.85 would be **worse than reading the prompt text**, and must not
   be published as evidence for CLAIM A.
3. **A large part of the bar is register, not content.** 21 hand-written non-lexical features
   reach 0.5174 / 0.7159; five hedge regexes alone reach 0.4768 / 0.6350. Any probe result
   should be reported alongside `H3`, not only alongside `N5`.
4. **N4 triggers the preregistered length-matching remedy** (0.4174 / 0.5750). The rule was
   frozen before the measurement, so applying it now is not a post-hoc choice.
5. **Two defects to fix before or alongside extraction**, both prompt-only:
   the singular-only substitution/matcher that leaves `knives` in 16/6900 probe rows
   (4 in test), and the 4 domain-generic sentences shared across the split (8/1380 test rows).
   Neither is large enough to explain an 0.887 baseline; both are real and neither should be
   inherited silently.

```
THE PROBE MUST BEAT: N5c_tfidf_demoblock_conceptmasked = 0.8870 / 0.9829
N4 VERDICT: length-only = 0.4174 accuracy / 0.5750 macro AUROC, z = +6.62 vs chance 1/3 --
            WELL ABOVE CHANCE; the preregistered length-matching rule IS TRIGGERED.
```
