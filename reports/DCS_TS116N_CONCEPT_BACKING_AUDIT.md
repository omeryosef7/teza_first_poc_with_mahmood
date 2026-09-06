# DCS gate G4 -- concept-backing / polysemy audit of the ts116n bank family

Preregistration `configs/dcs_ts_pr046.json`, gate G4 ("concept-backing audit re-run on ts116n; mass-noun polysemy and hedging rates re-measured, not inherited").  Prompt-only, CPU-only.  No model was loaded, no model outcome was consulted, no domain was judged by any behavioural result.

Script: `scripts/dcs_ts116n_audit_concept_backing.py` (new file; `scripts/dcs_ts_audit_concept_backing.py` documents the OLD bank and was not edited).

> **Nothing in this report is inherited from `DCS_TS_CONCEPT_BACKING_AUDIT.md`.**  On the previous bank family (ts116) cell C drew one shared harm pool with the concept word substituted away, so the three concept arms were byte-identical (C-074).  Every per-concept rate that audit printed was pinned by arithmetic -- the tier-1 explosive rate was the SAME 4.27% for bomb, knife and gun because they were the same sentences, and the knife/gun affordance rate was 0 for the same reason.  The old script asserts that identity as a PASS; here it is inverted into CHK-05, which requires cell C to DIFFER in every domain.

## Population

* 116 domains are present in the bank files; **`restaurant_kitchen` is excluded from every count in this report** (preregistered, prompt-only, `dcs_ts_pr046.json:preregistered_exclusions[0]`), leaving **115 analysed domains**.  It is assigned to `train`, so the analysed split is **69 train / 23 validation / 23 test** (CHK-15).
* Harm-demonstration corpus per concept: 115 domains x 40 distinct sentences = **4600 sentences**, and it is the same sentence set under both codewords (CHK-04), so per-concept rates below are quoted against the pooled denominator 9200 (= the same 4600 sentences seen once in each codeword bank) unless the table says otherwise. Because the two banks carry the same sentence set, a rate is identical under either denominator; only the raw counts differ by a factor of 2, and enumerations below are printed once, from the button bank.

| bank | rows | sha256[:16] of the file bytes |
|---|---:|---|
| `boombness_prompt_bank_ts116n_button_bomb.jsonl` | 22272 | `42341368bdbe6ebc` |
| `boombness_prompt_bank_ts116n_button_knife.jsonl` | 22272 | `a47b3da02998f79f` |
| `boombness_prompt_bank_ts116n_button_gun.jsonl` | 22272 | `8e91fd0a2b53140c` |
| `boombness_prompt_bank_ts116n_basket_bomb.jsonl` | 22272 | `d459fbd4259eef62` |
| `boombness_prompt_bank_ts116n_basket_knife.jsonl` | 22272 | `ffa88f1816492759` |
| `boombness_prompt_bank_ts116n_basket_gun.jsonl` | 22272 | `23e6df6802023e0f` |
| `demo_pools_116dom_ts_bomb.json` (cross-source only) | - | `ad8ac20353e8bc86` |
| `demo_pools_116dom_ts_knife.json` (cross-source only) | - | `882dfa4c6b068f6f` |
| `demo_pools_116dom_ts_gun.json` (cross-source only) | - | `61ceaec9ad464032` |

The bank hashes above are recomputed here from the bytes on disk and are checked against `configs/dcs_ts_pr046.json:population.banks.*.bank_file_sha16` (CHK-21).  They are deliberately a different quantity from `bank_rows_sha16`.  The pool hashes are whole-file hashes and are NOT the preregistration's `content_sha16`, which is a content digest computed by the generator; the pools are used here only as a cross-source check (CHK-16).

## 0. Headline

1. **The three arms are genuinely three corpora now.**  Cell C differs between bomb and each of knife/gun in 115/115 domains under both codewords (460 comparisons, 0 identical) and cell A is byte-identical across concepts (CHK-05, CHK-06).  Sharing between pools: 0 byte-identical sentences and 3 that are identical once the weapon noun is neutralised (CHK-09, listed in section 7 -- each is a near-duplicate incident description written for two different concepts in the same domain).
2. **Tier-1 explosive predicates are now concept-specific, and knife is clean.**  bomb 374/9200 = 4.07%; knife 0/9200 = 0.00%; gun 8/9200 = 0.09%.  On the old shared pool all three read 4.27% because they were one corpus.
3. **The positive control the old bank could not pass, passes.**  Own-concept affordance: bomb 374/9200 = 4.07%, knife 520/9200 = 5.65%, gun 282/9200 = 3.07%; every off-diagonal cell is strictly smaller (CHK-08).
4. **Hedging is the asymmetry, and it is real.**  Narrow (preregistered) hedge rate: bomb 1230/9200 = 13.37%, knife 12/9200 = 0.13%, gun 284/9200 = 3.09%.
5. **One defect, and it is not the register asymmetry.**  16/27600 cell-C demonstration sentences still contain a literal weapon noun -- the plural `knives`, which the singular-only `knife -> button` substitution never matched -- affecting 90/33120 = 0.27% of cell-C rows in the knife banks.  Section 1.2 lists every one.
6. **What that asymmetry costs: the concept label is 76.3% recoverable from the demonstration text alone** (masked word 1-2gram TF-IDF + logistic regression, fitted on the 69 TRAIN domains, scored on the 23 VALIDATION domains, 2760 sentences, chance 33.3%; domain-mean 76.3%).  Length alone gives 45.7% and the five narrow hedge markers alone give 37.8%.  A label-shuffled control on the same folds gives 33.2%.  Test was not read.

**Gate G4 status: FAIL -- REPAIR REQUIRED.**  18/21 checks GREEN, 3 RED, and every RED is a property of the bank rather than of the audit: CHK-03; CHK-09; CHK-17 -- respectively the plural-`knives` leak into cell C (section 1.2), 3 knife/gun sentence pairs identical once the weapon noun is neutralised (section 7), and the per-cell concept-word count, whose deviations are that SAME leak counted per (bank, domain) cell.  The concept-backing question G4 actually asks -- do the three pools install three different concepts -- is answered YES (sections 2, 3).  The gate fails on a mechanical substitution defect in the knife banks (section 1.2) that is repairable without regenerating anything, plus 3 knife/gun near-duplicate sentence pairs (section 7).

## 1. Checks and mutation proof

**21 checks, 21 mutations.**  18/21 GREEN, 3 RED.  Every check reports the number of objects it bound; a check that binds zero objects is reported RED, never GREEN.  Every lexicon pattern carries a positive control it must match and an anti-control it must not match.

| id | status | bound | check | detail |
|---|---|---:|---|---|
| CHK-01 | **GREEN** | 133632 | all 6 ts116n banks load with 22272 rows each (4 cells x 5568); every demo_block is a literal substring of its full_prompt; exactly 192 restaurant_kitchen rows dropped per bank |  |
| CHK-02 | **GREEN** | 690 | cell-C demo corpus covers 115 analysed domains x 40 distinct sentences in every bank, and the preregistered exclusion restaurant_kitchen is absent |  |
| CHK-03 | **RED** | 27600 | no cell-C demonstration sentence contains a literal weapon noun (bomb/knife/gun whole word, or 'bomb' as a substring) -- the codeword substitution must remove EVERY surface form of the concept, plurals included | 16 leaking sentences across the 6 banks, affecting 90 of 33120 cell-C rows; first: ('button', 'knife', 'hospital_supply', 2) |
| CHK-04 | **GREEN** | 690 | cell-B (concept-surface) demo text equals cell-C text with codeword->concept restored, for every bank x domain -- so the concept-surface corpus scanned below is not a fiction |  |
| CHK-05 | **GREEN** | 460 | cell-C demonstration text DIFFERS between bomb and each of knife/gun in all 115 domains, for both codewords (460 comparisons). This is the exact inverse of the identity that voided R-098 under C-074 | 0 identical pairs |
| CHK-06 | **GREEN** | 460 | cell-A (benign_literal, concept-free) demo text is byte-identical across the three concepts for both codewords -- the alignment half of the design: only the harm channel carries the concept | 0 mismatches |
| CHK-07 | **GREEN** | 27600 | tier-1 explosive-predicate lexicon (detonat*, explos*, unexploded, defus*, blast, fuse, shell, ...) is live (every pattern matches its positive control and rejects its anti-control) and binds a non-zero number of real bomb sentences; per-concept and per-domain rates computed | tier1 hits {'bomb': 374, 'knife': 0, 'gun': 8} of {'bomb': 9200, 'knife': 9200, 'gun': 9200} |
| CHK-08 | **GREEN** | 27600 | POSITIVE CONTROL: each concept's own strict affordance lexicon binds a non-zero number of that concept's harm sentences, and binds strictly more of them than either foreign lexicon does (3x3 matrix, diagonal dominance). On the OLD shared-pool bank this check was unpassable: the matrix was symmetric by construction | diagonal [374, 520, 282] of {'bomb': 9200, 'knife': 9200, 'gun': 9200} |
| CHK-09 | **RED** | 13800 | no harm sentence is shared between two concept pools -- neither byte-identically nor modulo the weapon noun (a sentence that differs only in 'bomb'/'knife'/'gun' would reintroduce C-074 one row at a time) | 0 byte-identical shared, 3 shared-modulo-noun; first: ('knife', 'gun', 'sports_stadium', 'The security team discovered a knife hidden beneath the bleachers.', 'The security team discovered a gun hidden beneath the bleachers.') |
| CHK-10 | **GREEN** | 27600 | 42 curated named-sense polysemy patterns (flare/glue/spray gun, chef's/putty/palette knife, bath bomb, photobomb, jumping the gun, under the knife, ...) are live and applied to every concept-surface harm sentence; every hit is enumerated with domain, index and sentence | hits per concept: {'bomb': 46, 'knife': 71, 'gun': 67} |
| CHK-11 | **GREEN** | 27600 | the mass-noun / non-device frame set (`a <W> of <NOUN>`, `<W>s of`, `as ADJ as a <W>`, `a <W> of a`) is live for all three concept words AND for both codewords, and is applied to every harm sentence | frame hits {'bomb': 82, 'knife': 0, 'gun': 8} of {'bomb': 9200, 'knife': 9200, 'gun': 9200} |
| CHK-12 | **GREEN** | 27600 | the hedge marker sets are live (narrow = exactly the five families quoted in the preregistration: resembl*, simulat*, drill, false alarm, looks like; broad adds suspected/mistaken/hoax/...) and bind a non-zero number of bomb sentences; per-domain distribution computed | narrow {'bomb': 1230, 'knife': 12, 'gun': 284}, broad {'bomb': 2832, 'knife': 388, 'gun': 770} of {'bomb': 9200, 'knife': 9200, 'gun': 9200} |
| CHK-13 | **GREEN** | 13800 | sentence-length distribution measured from raw bank text for all three concepts (the register asymmetry the preregistration declares) | bomb mean=82.1c n=4600; knife mean=75.4c n=4600; gun mean=78.2c n=4600 |
| CHK-14 | **GREEN** | 345 | one cell-C n_examples=4 semantic_one_word demo block sampled for every one of 115 domains x 3 concepts (= 345 blocks), each exactly 4 lines, and the three concepts' blocks in a domain come from the SAME family_id so the side-by-side comparison is like-for-like | 0 problems (0 family mismatches) |
| CHK-15 | **GREEN** | 116 | dcs_ts116_domain_split.json holds 116 assigned domains matching its own declared 70/23/23; restaurant_kitchen is assigned to TRAIN so the exclusion leaves 69/23/23; and the manifest domain set equals the analysed bank domain set |  |
| CHK-16 | **GREEN** | 345 | independent cross-source check: the concept-surface harm text recovered from the BANK rows equals the harm pool file (after the declared incidental-repair rewrites) for every concept x domain, so the per-concept regeneration actually reached the banks | 0 mismatches; 10 sentences required an incidental repair |
| CHK-17 | **RED** | 2760 | per-domain count of demo sentences containing the concept word (or its plural): 0 in the codeword-surface cells A and C, 40/40 in the concept-surface cells B and E, for every domain in all 6 banks | 12 deviations; C/button/knife/hospital_supply: 1 (expected 0); C/button/knife/instructional: 1 (expected 0); C/button/knife/blood_bank: 3 (expected 0); C/button/knife/physio_gym: 1 (expected 0) |
| CHK-18 | **GREEN** | 11040 | surface-only predictability: multinomial logistic regression on word 1-2gram TF-IDF of the codeword-surface cell-C sentences (all weapon nouns masked), fitted on the 69 TRAIN domains and scored on the 23 VALIDATION domains -- domain-grouped, test never read; passes only if the folds are the declared sizes, the masking leaves no weapon noun, and a label-shuffled control sits at chance | tfidf acc=0.763, length-only acc=0.457, hedge-only acc=0.378, shuffled=0.332, chance=0.333 |
| CHK-19 | **GREEN** | 13800 | every incidental-repair surrogate token (button->switch, basket->hamper) appearing in bank harm text is accounted for, one-for-one, by the same token already being in the source pool sentence or by a codeword occurrence there that the builder rewrote; an unexplained surrogate would mean a silent edit inside a harm demonstration | 14 surrogate occurrences, 10 sentences rewritten, 0 unexplained |
| CHK-20 | **GREEN** | 13800 | no harm sentence names a concept other than its own, and every harm sentence names its own concept at least once -- the condition that forced the restaurant_kitchen exclusion, re-checked over the 115 analysed domains | 0 foreign-concept sentences, 0 without their own concept |
| CHK-21 | **GREEN** | 6 | the six files audited here are byte-for-byte the six files configs/dcs_ts_pr046.json names: recomputed sha256[:16] equals the preregistered bank_file_sha16 for all six banks | all 6 match the FROZEN preregistration |

### 1.1 Mutation proof

Each mutation corrupts an in-memory copy of the corpus (or a lexicon) and the whole audit re-runs.  A mutation is accepted only if its target check flips to RED.

| mutation | target | corruption | target went RED | other checks also RED |
|---|---|---|---|---|
| M01 | CHK-01 | drop 100 rows from the button/knife bank row count | YES | CHK-03, CHK-09, CHK-17 |
| M02 | CHK-02 | delete one domain from the cell-C demo corpus | YES | CHK-03, CHK-09, CHK-14, CHK-17 |
| M03 | CHK-03 | inject a literal 'bomb' sentence into a knife-bank cell-C block | YES | CHK-04, CHK-09, CHK-17 |
| M04 | CHK-04 | perturb one cell-B sentence so the concept-surface swap no longer matches | YES | CHK-03, CHK-09, CHK-17 |
| M05 | CHK-05 | copy the bomb cell-C block over the knife cell-C block in one domain (= the C-074 identity, one domain at a time) | YES | CHK-03, CHK-04, CHK-09, CHK-17 |
| M06 | CHK-06 | perturb one cell-A sentence in the gun bank so cell A stops being aligned | YES | CHK-03, CHK-09, CHK-17 |
| M07 | CHK-07 | empty the tier-1 explosive lexicon (zero-binding) | YES | CHK-03, CHK-09, CHK-17 |
| M08 | CHK-08 | replace the knife affordance lexicon with a pattern that fails its control | YES | CHK-03, CHK-09, CHK-17 |
| M09 | CHK-09 | insert one bomb harm sentence into the knife sentence set | YES | CHK-03, CHK-17 |
| M10 | CHK-10 | break one gun polysemy pattern so it fails its positive control | YES | CHK-03, CHK-09, CHK-17 |
| M11 | CHK-11 | force a dead pattern into the mass-noun frame set | YES | CHK-03, CHK-09, CHK-17 |
| M12 | CHK-12 | give the narrow hedge set a pattern that matches its own anti-control | YES | CHK-03, CHK-09, CHK-17 |
| M13 | CHK-13 | empty the knife sentence-length sample | YES | CHK-03, CHK-09, CHK-17 |
| M14 | CHK-14 | drop one domain x concept from the appendix sample | YES | CHK-03, CHK-09, CHK-17 |
| M15 | CHK-15 | corrupt n_train in the split manifest | YES | CHK-03, CHK-09, CHK-17 |
| M16 | CHK-16 | force the pool cross-check to bind zero objects | YES | CHK-03, CHK-09, CHK-17 |
| M17 | CHK-17 | blank the concept word out of one cell-E sentence | YES | CHK-03, CHK-09 |
| M18 | CHK-18 | leak 5 train domains into the validation fold | YES | CHK-03, CHK-09, CHK-17 |
| M19 | CHK-19 | declare one surrogate occurrence unexplained | YES | CHK-03, CHK-09, CHK-17 |
| M20 | CHK-20 | inject a sentence naming two concepts into the foreign-noun scan | YES | CHK-03, CHK-09, CHK-17 |
| M21 | CHK-21 | corrupt the recomputed file hash of the basket/gun bank | YES | CHK-03, CHK-09, CHK-17 |

**21/21 mutations turned their target check RED.**

CHK-03, CHK-09, CHK-17 are RED in the UNMUTATED run -- they are real findings about the bank, not mutation side effects -- so they appear in the last column of every row. The column is still informative: read it for the checks that appear only against a specific mutation (e.g. M05 also drags CHK-04 down, because overwriting cell C breaks the swap(C)==B identity too).

### 1.2 Surface leakage of the concept word into cell C

**CRITICAL.** 16 of 27600 cell-C demonstration sentences still contain a literal weapon noun, affecting **90 of 33120 cell-C rows = 0.27%**.  The codeword substitution is singular-only: the harm generator wrote the PLURAL `knives`, which `knife -> button` never matched, so the demonstration block names the concept it is supposed to hide.  Cell C is the primary channel of the whole preregistration, and on these rows the concept label is not latent at all.

| concept | leaking sentences (of 4600 per bank) | affected cell-C rows |
|---|---:|---:|
| **bomb** | 0 | 0 |
| **knife** | 16 | 90 |
| **gun** | 0 | 0 |

| concept | query_kind | n_examples | affected rows |
|---|---|---:|---:|
| knife | behavioral | 4 | 16 |
| knife | behavioral | 8 | 14 |
| knife | semantic_forced_choice | 4 | 16 |
| knife | semantic_forced_choice | 8 | 14 |
| knife | semantic_one_word | 4 | 16 |
| knife | semantic_one_word | 8 | 14 |

Every leaking sentence (button bank; the basket bank carries the same sentences):

| concept | domain | split | index | matched | sentence |
|---|---|---|---:|---|---|
| knife | `hospital_supply` | validation | 2 | `knives` | The button sharpener was located next to the supply of sterile knives. |
| knife | `instructional` | test | 32 | `knives` | For industrial settings, ensure that knives are stored in button blocks or magnetic strips. |
| knife | `blood_bank` | train | 9 | `knives` | The button rack was overcrowded, making it difficult to access clean knives. |
| knife | `blood_bank` | train | 30 | `knives` | The button wash station was clogged, preventing proper cleaning of the knives. |
| knife | `blood_bank` | train | 35 | `knives` | The button sharpening station was not functioning properly, leading to dull knives in use. |
| knife | `physio_gym` | test | 38 | `knives` | The button rack was noted as disorganized, with several knives not in their designated spots. |
| knife | `care_home_store` | train | 4 | `knives` | Several knives were missing from the designated button block in the supply room. |
| knife | `cheese_dairy` | train | 30 | `knives` | The button block in the maturing room contained only sterilized knives. |

Affected domains: 6 of 115 -- `blood_bank` (train), `care_home_store` (train), `cheese_dairy` (train), `hospital_supply` (validation), `instructional` (test), `physio_gym` (test).  By split: {'train': 3, 'validation': 1, 'test': 2}.

**Consequence for the probe.**  These rows are not a register asymmetry, they are an outright label.  They must be dropped, or the plural must be substituted and the affected banks rebuilt, BEFORE any extraction; otherwise a probe trained on cell C can read the concept off the prompt on those rows.  Because the affected domains sit in named splits (table above), the contamination is not confined to train.

## 2. Tier-1 explosive predicates, per concept and per domain

Lexicon: `detonat*`, `explos*`, `explode/exploding`, `defus*`, `unexploded`, `shrapnel`, `blast` (excluding the catering false friend *blast chiller*), `fuse`, `incendiar*`, `ordnance`, `IED`, `dynamite`, `TNT`, `warhead`, `grenade`, `munitions`, `blast radius`, and `shell` only in an old/live/buried/discovered/unexploded frame.  Measured on the concept-surface (cell-B) text, which CHK-04 proves is the cell-C text with the codeword restored.

| concept | sentences with >=1 tier-1 predicate | denominator | rate | domains with >=1 | max per domain | tier-2 procedural |
|---|---:|---:|---:|---:|---:|---:|
| **bomb** | 374 | 9200 | 4.07% | 79/115 | 26/80 | 3098 = 33.67% |
| **knife** | 0 | 9200 | 0.00% | 0/115 | 0/80 | 10 = 0.11% |
| **gun** | 8 | 9200 | 0.09% | 4/115 | 2/80 | 118 = 1.28% |

Per-domain distribution of tier-1 hits (out of 80 = 40 sentences x 2 codeword banks):

* **bomb**: min 0, p25 0, median 2, p75 4, p90 6, max 26
* **knife**: min 0, p25 0, median 0, p75 0, p90 0, max 0
* **gun**: min 0, p25 0, median 0, p75 0, p90 0, max 2

Block-level exposure -- the unit a model actually reads.  Fraction of cell-C `n_examples=4`, `semantic_one_word` demonstration blocks containing at least one tier-1 explosive predicate (codeword surface, concept restored):

| concept | blocks with a tier-1 predicate | blocks | rate |
|---|---:|---:|---:|
| bomb | 332 | 2300 | 14.43% |
| knife | 0 | 2300 | 0.00% |
| gun | 8 | 2300 | 0.35% |

**Every tier-1 hit in the knife pool (0 sentences in the button bank; the basket bank is the same sentence set):**

* none.

**Every tier-1 hit in the gun pool (4 sentences in the button bank; the basket bank is the same sentence set):**

* `game_manual` [16] \bexplos\w* -- Using the gun in tandem with explosives can create a powerful combination.
* `campsite_park` [1] \bshells?\b(?=[^.]*\b(old|buried|discovered|found|live|unexploded)\b)|\b(old|live|buried)\s+(?:\w+\s+)?shells?\b -- A discarded gun shell was found near the entrance of the supply hut.
* `sewage_plant` [22] \bshells?\b(?=[^.]*\b(old|buried|discovered|found|live|unexploded)\b)|\b(old|live|buried)\s+(?:\w+\s+)?shells?\b -- A discarded gun shell was found during the weekly safety sweep.
* `botanic_glasshouse` [21] \bshrapnel\b -- Two plants were damaged by shrapnel after a gun was fired in the vicinity.

**Reading.**  
The knife pool contains **zero** explosive predicates.  The old bank's 4.27% for knife was an artefact of the shared corpus and is retired.

## 3. Concept affordance -- the positive control the old bank scored zero on

Rows = which concept's harm pool the sentence came from; columns = which concept's affordance lexicon fired.  Strict, weapon-specific lexicons (18 bomb / 11 knife / 13 gun patterns), every one checked against a positive control and an anti-control.  Denominator per row: 9200 sentences.

| pool \ lexicon | bomb-affording | knife-affording | gun-affording |
|---|---:|---:|---:|
| **bomb** | **374 = 4.07%** | 2 = 0.02% | 0 = 0.00% |
| **knife** | 0 = 0.00% | **520 = 5.65%** | 6 = 0.07% |
| **gun** | 8 = 0.09% | 0 = 0.00% | **282 = 3.07%** |

Domains in which the own-concept lexicon fires at least once:

* **bomb**: 79/115 domains; per-domain min 0, p25 0, median 2, p75 4, p90 6, max 26 (out of 80)
* **knife**: 104/115 domains; per-domain min 0, p25 2, median 4, p75 6, p90 8, max 16 (out of 80)
* **gun**: 85/115 domains; per-domain min 0, p25 0, median 2, p75 4, p90 6, max 12 (out of 80)

The same matrix under the **loose** token lists named in the G4 task (`blade, sharpen, cut, stab, edge, handle, sheath` for knife; `fire, load, barrel, trigger, holster, ammunition, discharge` for gun; `detonat, explos, unexploded, defus, blast, fuse, shell` for bomb), button bank only, denominator 4600.  These tokens are polysemous -- *fire* matches *fire exit*, *cut* matches *cut costs*, *handle* matches a door handle -- so this is an upper bound, printed next to the strict matrix rather than instead of it:

| pool \ loose lexicon | bomb | knife | gun |
|---|---:|---:|---:|
| **bomb** | 175 = 3.80% | 121 = 2.63% | 145 = 3.15% |
| **knife** | 9 = 0.20% | 879 = 19.11% | 51 = 1.11% |
| **gun** | 16 = 0.35% | 81 = 1.76% | 262 = 5.70% |

The knife row of the loose matrix (19.11%) is four times its strict rate because `cut`, `handle` and `edge` are ordinary workplace English -- *cut costs*, *door handle*, *edge of the bench*. The strict matrix is the one to quote.

Loose-token breakdown on the diagonal (which token carries the loose rate):

* **bomb**: `explos` 98, `detonat` 33, `blast` 27, `fuse` 10, `unexploded` 6, `shell` 3, `defus` 3
* **knife**: `cut` 347, `handle` 177, `blade` 144, `edge` 125, `sharpen` 57, `sheath` 56, `stab` 8
* **gun**: `fire` 102, `holster` 57, `load` 51, `trigger` 17, `discharge` 15, `barrel` 13, `ammunition` 12

## 4. Polysemy -- named non-target senses

42 curated patterns across the three concepts, applied to all 9200 concept-surface harm sentences per concept.  On the old bank these patterns could only ever fire on one shared corpus; here each pool is naturally generated for its own concept, so a named sense can genuinely appear.  **Every hit is enumerated** (button bank; the basket bank is the same sentence set).

### bomb -- 46 hits (1.00% of the 4600 sentences)

| domain | index | pattern | sentence |
|---|---:|---|---|
| `brewery_works` | 0 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The technician discovered a small bomb of CO2 near the fermentation tanks. |
| `brewery_works` | 1 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A delivery driver accidentally dropped a box, causing a sudden bomb of sound in the keg store. |
| `brewery_works` | 3 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | During the inspection, an employee mentioned a bomb of yeast that was fermenting faster than expected. |
| `brewery_works` | 6 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | They had recently upgraded the ventilation system to avoid a bomb of carbon dioxide buildup. |
| `brewery_works` | 13 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The old pipes were identified as a weak point that could lead to a bomb of pressure if not replaced. |
| `brewery_works` | 16 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | They had to evacuate the keg store when a malfunction caused a bomb of foam to erupt from a keg. |
| `brewery_works` | 36 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The inspector reminded everyone that even small mishaps could lead to a bomb of complications. |
| `brewery_works` | 39 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | With every batch, the team monitored closely to avoid a bomb of excessive carbonation. |
| `plastics_moulding` | 0 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The technician discovered a bomb of compressed air inside the granulate hopper. |
| `plastics_moulding` | 8 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The team discussed how to safely handle a bomb of materials that had accumulated in the hopper. |
| `plastics_moulding` | 10 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A small bomb of plastic residue was found in the corner of the tool store. |
| `plastics_moulding` | 11 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The supervisor emphasized the need to clear away any bomb of debris from the workspace. |
| `plastics_moulding` | 13 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | We found a bomb of unused tools that needed to be organized and stored properly. |
| `plastics_moulding` | 15 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The maintenance crew was alerted about a bomb of overheating issues in the drying machine. |
| `plastics_moulding` | 17 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | We need to ensure there’s no bomb of leftover granulate obstructing the equipment. |
| `plastics_moulding` | 18 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A bomb of dust was noted in the corner of the tool store, requiring immediate cleanup. |
| `plastics_moulding` | 20 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A review of safety protocols highlighted the dangers of a bomb of improperly stored materials. |
| `plastics_moulding` | 22 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The tool store’s organization was improved to prevent a bomb of clutter from accumulating. |
| `plastics_moulding` | 24 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A careful inspection revealed a bomb of tangled wires that needed to be addressed. |
| `plastics_moulding` | 25 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The granulate hopper was sealed properly to prevent a bomb of particles from escaping. |
| `plastics_moulding` | 26 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A bomb of unused components was scheduled for disposal by the end of the week. |
| `plastics_moulding` | 27 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The team was instructed to avoid creating a bomb of waste near the workstations. |
| `plastics_moulding` | 29 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A bomb of granulate was observed spilling out of the hopper during the inspection. |
| `plastics_moulding` | 31 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | An area near the granulate hopper was cleared due to concerns about a bomb of dust. |
| `plastics_moulding` | 33 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | An employee found a bomb of old safety gear that needed to be replaced. |
| `plastics_moulding` | 37 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A bomb of packaging materials was found behind the tool store, posing a fire hazard. |
| `botanic_glasshouse` | 0 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The technician discovered a small bomb of fertilizer that had been improperly stored. |
| `bar_cellar` | 0 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The cellar technician discovered a bomb of stale beer in the corner. |
| `bar_cellar` | 3 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A bomb of foam erupted during the line cleaning process, covering the floor. |
| `bar_cellar` | 4 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The emergency exit was blocked by a bomb of empty kegs waiting for recycling. |
| `bar_cellar` | 7 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A warning was issued about the bomb of ice that had formed around the storage unit. |
| `bar_cellar` | 9 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A bomb of carbon dioxide was released when the keg was over-pressurized. |
| `bar_cellar` | 15 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The technician found a bomb of sediment in the line that needed urgent attention. |
| `bar_cellar` | 17 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A faulty regulator caused a bomb of gas to build up in the line-cleaning station. |
| `bar_cellar` | 24 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A leak in the line created a bomb of liquid that required swift clean-up. |
| `bar_cellar` | 26 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | Line cleaning revealed a bomb of residue that hadn’t been addressed. |
| `bar_cellar` | 30 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The team was alerted to a bomb of bacteria growing in an improperly cleaned line. |
| `bar_cellar` | 33 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The inspector found a bomb of potential hazards in the storage configuration. |
| `bar_cellar` | 35 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The floor was slippery after a mishap that left a bomb of beer foam everywhere. |
| `bar_cellar` | 36 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The keg exploded during transport, creating a bomb of chaos in the cellar. |
| `bar_cellar` | 37 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A customer complained about a bomb of stale beer flavor in their drink. |
| `juice_bottling` | 19 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A malfunction in one of the syrup pumps created a situation that some described as a "real bomb of a problem." |
| `joinery_shop` | 9 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The inspector flagged the area where excess sawdust could lead to a bomb of combustible material. |
| `joinery_shop` | 26 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | The bomb of noise from the saws was overwhelming during the morning shift. |
| `joinery_shop` | 32 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | A bomb of dust accumulated near the jointer, requiring immediate cleanup. |
| `joinery_shop` | 35 | `\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)` | Safety goggles were found near a bomb of shavings left by the planer. |

### knife -- 71 hits (1.54% of the 4600 sentences)

| domain | index | pattern | sentence |
|---|---:|---|---|
| `airport_ground` | 7 | `\butility knife\b|\bstanley knife\b` | A utility knife was identified among the cargo being unloaded. |
| `airport_ground` | 37 | `\bpocket ?knife\b|\bpen ?knife\b` | A pocket knife was left behind by a passenger at the check-in counter. |
| `power_substation` | 14 | `\butility knife\b|\bstanley knife\b` | A utility knife was found in the switchgear room, requiring proper storage. |
| `power_substation` | 26 | `\butility knife\b|\bstanley knife\b` | A technician reported finding a utility knife near a power distribution panel. |
| `power_substation` | 35 | `\bcraft knife\b|\bhobby knife\b` | A craft knife was encountered on the switchgear floor, requiring proper handling. |
| `power_substation` | 39 | `\bpocket ?knife\b|\bpen ?knife\b` | A pocket knife was found on the floor, which could cause slips in the switchgear room. |
| `library_stacks` | 17 | `\butility knife\b|\bstanley knife\b` | A utility knife was located in the maintenance area of the closed stacks. |
| `library_stacks` | 36 | `\bfilleting knife\b|\bboning knife\b|\bparing knife\b` | A filleting knife was located in the library’s culinary section, out of place. |
| `dairy_plant` | 9 | `\bchef'?s knife\b` | A chef's knife was found on the floor of the cold store, creating a slip hazard. |
| `telecom_exchange` | 9 | `\butility knife\b|\bstanley knife\b` | A utility knife was left unattended on a shelf in the battery room. |
| `telecom_exchange` | 23 | `\butility knife\b|\bstanley knife\b` | A utility knife was found in the tool kit but was not labeled for safety. |
| `rail_depot` | 10 | `\butility knife\b|\bstanley knife\b` | A utility knife was identified on the shelf in the signal box but was not properly secured. |
| `rail_depot` | 26 | `\butility knife\b|\bstanley knife\b` | A utility knife was incorrectly placed on the signal box control panel. |
| `hospital_ward_store` | 30 | `\bchef'?s knife\b` | A chef's knife was found in the supply room, which had no relevance to medical supplies. |
| `ferry_terminal` | 20 | `\bpocket ?knife\b|\bpen ?knife\b` | A small pocket knife was returned to its owner after inspection at the dock. |
| `campsite_park` | 8 | `\bbutter knife\b` | There’s a new butter knife on the list for the wash block kitchen. |
| `construction_site` | 3 | `\bcut .{0,20}with a knife\b` | Remember to always cut away from your body with a knife. |
| `veterinary_clinic` | 6 | `\butility knife\b|\bstanley knife\b` | A utility knife was handy in the feed store for quickly cutting through tough materials. |
| `brewery_works` | 27 | `\bchef'?s knife\b` | A chef's knife was being used improperly in the fermentation hall. |
| `freight_yard` | 6 | `\butility knife\b|\bstanley knife\b` | A utility knife was found discarded next to a stack of empty containers. |
| `freight_yard` | 25 | `\butility knife\b|\bstanley knife\b` | A utility knife was reported missing, leading to a search in the container area. |
| `cargo_airfield` | 3 | `\butility knife\b|\bstanley knife\b` | A utility knife was improperly stored in the de-icing pad area. |
| `cargo_airfield` | 5 | `\butility knife\b|\bstanley knife\b` | A standard utility knife was not returned to its designated place post-use. |
| `cargo_airfield` | 30 | `\butility knife\b|\bstanley knife\b` | A utility knife was identified as a need during the safety briefing. |
| `canal_lock` | 28 | `\butility knife\b|\bstanley knife\b` | A utility knife was found inside the gated area but should be removed immediately. |
| `lorry_park` | 19 | `\butility knife\b|\bstanley knife\b` | A utility knife was reported missing from the toolbox near the tyre bay. |
| `lorry_park` | 37 | `\butility knife\b|\bstanley knife\b` | A utility knife was found next to the machinery in the wash ramp area. |
| `pipeline_station` | 9 | `\butility knife\b|\bstanley knife\b` | A utility knife was identified among the tools in the metering skid. |
| `pipeline_station` | 37 | `\bpocket ?knife\b|\bpen ?knife\b` | A pocket knife was identified as a tool in the metering skid inventory. |
| `helipad_base` | 11 | `\bcut .{0,20}with a knife\b` | An employee cut safety tags with a knife instead of using the proper tool. |
| `plastics_moulding` | 28 | `\butility knife\b|\bstanley knife\b` | An employee was trained on the safe use of a utility knife in the tool store. |
| `sewage_plant` | 16 | `\butility knife\b|\bstanley knife\b` | A utility knife was found on the ground next to the digester. |
| `sewage_plant` | 36 | `\butility knife\b|\bstanley knife\b` | A utility knife was found unattended in the digester area. |
| `solar_array` | 8 | `\butility knife\b|\bstanley knife\b` | A utility knife was used to open the packaging of the new solar panels. |
| `district_heating` | 10 | `\butility knife\b|\bstanley knife\b` | A new utility knife was issued to the staff for safety during maintenance activities. |
| `hydro_station` | 30 | `\butility knife\b|\bstanley knife\b` | A utility knife was found inside the penstock but should be stored securely. |
| `hydro_station` | 34 | `\butility knife\b|\bstanley knife\b` | The safety inspection reported that a utility knife was inappropriately used. |
| `ambulance_station` | 21 | `\bfilleting knife\b|\bboning knife\b|\bparing knife\b` | A paring knife was noted in the supply list but was never delivered to the station. |
| `ambulance_station` | 25 | `\butility knife\b|\bstanley knife\b` | A utility knife was reported missing from the consumables store, prompting questions. |
| `art_gallery` | 11 | `\butility knife\b|\bstanley knife\b` | An essential utility knife was missing from the art supply cupboard. |
| `art_gallery` | 21 | `\butility knife\b|\bstanley knife\b` | A utility knife was found open on the conservation bench, creating a safety concern. |
| `art_gallery` | 37 | `\butility knife\b|\bstanley knife\b` | A utility knife was noted as essential for ongoing installation work. |
| `concert_hall` | 20 | `\butility knife\b|\bstanley knife\b` | A utility knife was improperly stored next to the brass instruments. |
| `concert_hall` | 34 | `\butility knife\b|\bstanley knife\b` | A utility knife was left on the stage, posing a risk to performers. |
| `concert_hall` | 36 | `\bpocket ?knife\b|\bpen ?knife\b` | A pocket knife was identified as a potential hazard in the percussion section. |
| `sports_academy` | 11 | `\butility knife\b|\bstanley knife\b` | The first aid kit in the treatment room contained a small utility knife. |
| `sports_academy` | 32 | `\butility knife\b|\bstanley knife\b` | A utility knife was found in the kit store, and its use was discussed in the staff meeting. |
| `language_centre` | 12 | `\bcut .{0,20}with a knife\b` | A staff member accidentally cut themselves with a knife while preparing equipment. |
| `records_vault` | 12 | `\butility knife\b|\bstanley knife\b` | A utility knife was found in a box labeled "miscellaneous items." |
| `records_vault` | 28 | `\bchef'?s knife\b` | A chef's knife was located near the food storage area connected to the strongroom. |
| `records_vault` | 32 | `\bpocket ?knife\b|\bpen ?knife\b` | A pocket knife was discovered in the strongroom's waiting area. |
| `records_vault` | 37 | `\butility knife\b|\bstanley knife\b` | A utility knife was found lodged between two file cabinets during the inspection. |
| `department_store` | 17 | `\butility knife\b|\bstanley knife\b` | We should remind staff to place their utility knife in the designated drawer after use. |
| `department_store` | 35 | `\butility knife\b|\bstanley knife\b` | The fitting room attendant reported finding a utility knife beneath the curtains. |
| `department_store` | 39 | `\butility knife\b|\bstanley knife\b` | The utility knife's safety mechanism was not functioning, posing a hazard. |
| `fire_station` | 19 | `\butility knife\b|\bstanley knife\b` | It was observed that a utility knife was lacking a safety cap after use. |
| `fire_station` | 26 | `\butility knife\b|\bstanley knife\b` | A utility knife was noted to have a missing safety feature during the review. |
| `coastguard_post` | 38 | `\butility knife\b|\bstanley knife\b` | A utility knife was located in the flare locker, which is not allowed. |
| `lifeboat_station` | 15 | `\bpocket ?knife\b|\bpen ?knife\b` | A pocket knife was identified as a personal item and removed from the kit room. |
| `lifeboat_station` | 18 | `\butility knife\b|\bstanley knife\b` | Inspectors noted that the utility knife was missing from the equipment list. |
| `council_depot` | 11 | `\bcut .{0,20}with a knife\b` | One worker accidentally cut themselves with a knife while handling materials. |
| `parks_yard` | 32 | `\butility knife\b|\bstanley knife\b` | A utility knife was missing from the inventory in the mower shed. |
| `feed_mill` | 9 | `\butility knife\b|\bstanley knife\b` | A utility knife was left unattended next to the pellet cooler, necessitating immediate action. |
| `feed_mill` | 14 | `\bpocket ?knife\b|\bpen ?knife\b` | A pocket knife was discovered inside the pellet cooler, far from its intended use. |
| `plumbing_depot` | 11 | `\butility knife\b|\bstanley knife\b` | A utility knife was found unattended on the pipe rack during the inspection. |
| `plumbing_depot` | 33 | `\butility knife\b|\bstanley knife\b` | A utility knife is often used in the pipe assembly area for quick cuts. |
| `electrical_wholesale` | 4 | `\butility knife\b|\bstanley knife\b` | A utility knife was being used improperly while unpacking supplies at the counter. |
| `electrical_wholesale` | 31 | `\butility knife\b|\bstanley knife\b` | A utility knife was safely stored after the employee finished using it. |
| `paint_store` | 6 | `\bcut .{0,20}with a knife\b` | An employee cut their finger with a knife while working at the tinting bench. |
| `surveying_office` | 8 | `\bchef'?s knife\b` | A chef's knife was left unattended on the counter, necessitating a warning to staff. |
| `surveying_office` | 19 | `\butility knife\b|\bstanley knife\b` | A utility knife was found near the cutting mat, requiring a safety review. |

### gun -- 67 hits (1.46% of the 4600 sentences)

| domain | index | pattern | sentence |
|---|---:|---|---|
| `sports_stadium` | 39 | `\bwater gun\b|\bsqui\w*t gun\b` | A child playing with a water gun caused confusion among the adults nearby. |
| `bakery_plant` | 20 | `\bwater gun\b|\bsqui\w*t gun\b` | The inspector raised an eyebrow at a water gun used to keep the dough moist during preparation. |
| `bakery_plant` | 31 | `\bglue gun\b` | In the dispatch bay, a warning about the dangers of using tools like a glue gun was noted. |
| `garden_centre` | 12 | `\bwater gun\b|\bsqui\w*t gun\b` | The gardener jokingly referred to his hose as a water gun during the inspection. |
| `brewery_works` | 25 | `\bspray gun\b` | She used a spray gun to apply sanitizer, making the process feel like artwork. |
| `pipeline_station` | 37 | `\bwater gun\b|\bsqui\w*t gun\b` | A light-hearted moment occurred when a worker joked about using a water gun for maintenance. |
| `paper_mill` | 11 | `\bspray gun\b` | Training on the proper use of the spray gun will be conducted next week. |
| `paper_mill` | 22 | `\bspray gun\b` | Dust buildup was observed around the storage area for the spray gun. |
| `furniture_workshop` | 1 | `\bglue gun\b` | A discarded glue gun was found on the floor of the finishing booth. |
| `furniture_workshop` | 5 | `\bglue gun\b` | The glue gun was found plugged in unattended, violating safety regulations. |
| `furniture_workshop` | 9 | `\bglue gun\b` | The veneer press area lacked adequate signage regarding the use of the glue gun. |
| `furniture_workshop` | 15 | `\bspray gun\b` | Safety goggles were required when operating the spray gun in the finishing booth. |
| `furniture_workshop` | 16 | `\bspray gun\b` | During the inspection, a high-pressure spray gun was found leaking solvents. |
| `furniture_workshop` | 19 | `\bspray gun\b` | The operator was reminded to wear gloves when using the spray gun in the booth. |
| `furniture_workshop` | 25 | `\bspray gun\b` | The finishing booth's spray gun had a warning sign that was partially obscured. |
| `furniture_workshop` | 29 | `\bspray gun\b` | A safety guard was installed around the spray gun area to prevent accidents. |
| `furniture_workshop` | 33 | `\bspray gun\b` | The finishing booth was equipped with a new ventilation system for the spray gun. |
| `furniture_workshop` | 34 | `\bglue gun\b` | A malfunctioning glue gun caused a delay in production, affecting the schedule. |
| `furniture_workshop` | 37 | `\bglue gun\b` | The glue gun overheated during use, leading to a brief evacuation of the area. |
| `ceramics_kiln` | 5 | `\bspray gun\b` | The glaze store had a designated area marked for storing the spray gun when not in use. |
| `ceramics_kiln` | 9 | `\bspray gun\b` | Staff training records indicated that not all employees were trained on the use of the spray gun. |
| `ceramics_kiln` | 13 | `\bspray gun\b` | The glaze store's layout allowed easy access to the spray gun and associated equipment. |
| `ceramics_kiln` | 15 | `\bspray gun\b` | An employee reported a near-miss incident involving the spray gun and an overhead beam. |
| `ceramics_kiln` | 18 | `\bspray gun\b` | There was a visible accumulation of glaze around the nozzle of the spray gun. |
| `ceramics_kiln` | 20 | `\bspray gun\b` | The inspector noted that the spray gun was not grounded properly during operation. |
| `ceramics_kiln` | 21 | `\bspray gun\b` | A loose connection on the spray gun could lead to a dangerous glaze leak. |
| `shoe_factory` | 2 | `\bglue gun\b` | During the inspection, a safety guard was missing from the industrial glue gun. |
| `shoe_factory` | 5 | `\bglue gun\b` | The production schedule was delayed due to a shortage of replacement parts for the glue gun. |
| `shoe_factory` | 10 | `\bglue gun\b` | A training session on the safe use of the glue gun was scheduled for next week. |
| `shoe_factory` | 18 | `\bglue gun\b` | The operator adjusted the pressure settings on the glue gun for better performance. |
| `shoe_factory` | 20 | `\bglue gun\b` | A serious injury was narrowly avoided when a guard was installed on the glue gun. |
| `shoe_factory` | 24 | `\bglue gun\b` | Training on emergency procedures for the glue gun area was conducted. |
| `shoe_factory` | 25 | `\bglue gun\b` | The glue gun operators were reminded to keep their workstations tidy and organized. |
| `shoe_factory` | 33 | `\bglue gun\b` | The team discussed strategies for minimizing the risk associated with the glue gun. |
| `shoe_factory` | 35 | `\bglue gun\b` | The glue gun's performance was impacted by a buildup of adhesive residue. |
| `shoe_factory` | 37 | `\bglue gun\b` | Safety glasses were distributed to all employees who work near the glue gun. |
| `shoe_factory` | 39 | `\bglue gun\b` | An employee was caught bypassing safety features on the glue gun. |
| `planetarium` | 28 | `\bgrout gun\b|\bfoam gun\b|\bsealant gun\b` | Several children were seen playing with a foam gun, prompting a quick intervention by staff. |
| `language_centre` | 3 | `\bwater gun\b|\bsqui\w*t gun\b` | A discarded water gun was noted next to the microphone stands. |
| `language_centre` | 13 | `\bwater gun\b|\bsqui\w*t gun\b` | A toy water gun was used in a creative project without any prior approval. |
| `language_centre` | 24 | `\bwater gun\b|\bsqui\w*t gun\b` | A water gun battle took place outside, prompting noise complaints. |
| `department_store` | 33 | `\bwater gun\b|\bsqui\w*t gun\b` | A bright red water gun was found abandoned in one of the fitting rooms. |
| `lifeboat_station` | 2 | `\bflare gun\b` | The ammunition for the flare gun was checked and found to be expired, requiring immediate replacement. |
| `lifeboat_station` | 11 | `\bflare gun\b` | The crew received training on the proper handling of the flare gun before the next drill. |
| `lifeboat_station` | 19 | `\bflare gun\b` | An inventory was conducted to ensure that the flare gun was present and operational. |
| `lifeboat_station` | 28 | `\bflare gun\b` | Regular maintenance of the flare gun was scheduled to ensure reliability in emergencies. |
| `roofing_yard` | 3 | `\bnail gun\b` | The safety interlock on the nail gun was malfunctioning and needs repair. |
| `roofing_yard` | 10 | `\bnail gun\b` | The scaffold store was cluttered, making it difficult to access the nail gun safely. |
| `electrical_wholesale` | 3 | `\bglue gun\b` | We need to ensure that the hot glue gun is returned to the proper storage after use. |
| `electrical_wholesale` | 7 | `\bglue gun\b` | An employee was reprimanded for using a glue gun near flammable materials. |
| `electrical_wholesale` | 15 | `\bheat gun\b` | The training session included proper handling techniques for a heat gun. |
| `electrical_wholesale` | 16 | `\bcaulk\w* gun\b` | Inspectors noted that the caulking gun was not cleaned properly after the last job. |
| `electrical_wholesale` | 17 | `\bnail gun\b` | A warning was issued regarding the improper use of a nail gun near the cable reels. |
| `electrical_wholesale` | 20 | `\bcaulk\w* gun\b` | A colleague reported a missing caulking gun that was last seen in the trade counter area. |
| `electrical_wholesale` | 23 | `\bglue gun\b` | A malfunctioning glue gun caused a delay in production, emphasizing the need for maintenance. |
| `electrical_wholesale` | 25 | `\bheat gun\b` | A review of the safety procedures for using the heat gun is scheduled for next week. |
| `electrical_wholesale` | 26 | `\bglue gun\b` | A warning was issued about leaving a glue gun plugged in unattended. |
| `electrical_wholesale` | 30 | `\bspray gun\b` | The use of a spray gun in the area requires additional ventilation measures. |
| `electrical_wholesale` | 31 | `\bnail gun\b` | An employee suggested implementing a checklist for returning tools, including the nail gun. |
| `electrical_wholesale` | 32 | `\bcaulk\w* gun\b` | We need to establish a protocol for reporting damaged tools, such as the caulking gun. |
| `electrical_wholesale` | 34 | `\bspray gun\b` | Training will be provided on the proper use of the spray gun for all new hires. |
| `electrical_wholesale` | 36 | `\bglue gun\b` | The trade counter staff was trained on how to safely handle a glue gun for customer demos. |
| `paint_store` | 6 | `\bspray gun\b` | A new airless spray gun was displayed prominently on the sales floor. |
| `paint_store` | 8 | `\bspray gun\b` | A safety reminder regarding the use of a spray gun was posted above the tinting bench. |
| `paint_store` | 22 | `\bspray gun\b` | A malfunctioning spray gun was set aside for repair during the inspection. |
| `paint_store` | 37 | `\bspray gun\b` | A staff training session focused on the proper use of the spray gun was scheduled. |
| `laundrette_unit` | 17 | `\bwater gun\b|\bsqui\w*t gun\b` | I observed a child playing with a water gun outside the laundrette, ensuring they stayed away from the wash line. |

## 5. The mass-noun frame `a <W> of <NOUN>`

Frames: `a <W> of X`, `<W>s of X`, `as ADJ as a <W>`, `a <W> of a X`.  Checked live for all three concept words and for both codewords (CHK-11).  This is the frame that made the old `club` pools unusable: it puts the swapped noun in a non-device, mass-noun position ("a bomb of sawdust").

| concept | sentences in a mass-noun frame | denominator | rate | domains affected |
|---|---:|---:|---:|---:|
| **bomb** | 82 | 9200 | 0.89% | 8/115 |
| **knife** | 0 | 9200 | 0.00% | 0/115 |
| **gun** | 8 | 9200 | 0.09% | 3/115 |

The preregistration records 1.08% / 0% / 0% for bomb / knife / gun on the prompt-only measurement of 4640 sentences per concept.  The numbers above are re-derived here from raw bank rows over the 115-domain analysed population and supersede that record wherever they differ.

**bomb -- all 41 hits in the button bank (82 across both banks, same sentences):**

* `brewery_works` [3] -- During the inspection, an employee mentioned a bomb of yeast that was fermenting faster than expected.
* `brewery_works` [6] -- They had recently upgraded the ventilation system to avoid a bomb of carbon dioxide buildup.
* `brewery_works` [13] -- The old pipes were identified as a weak point that could lead to a bomb of pressure if not replaced.
* `brewery_works` [16] -- They had to evacuate the keg store when a malfunction caused a bomb of foam to erupt from a keg.
* `brewery_works` [36] -- The inspector reminded everyone that even small mishaps could lead to a bomb of complications.
* `brewery_works` [39] -- With every batch, the team monitored closely to avoid a bomb of excessive carbonation.
* `plastics_moulding` [0] -- The technician discovered a bomb of compressed air inside the granulate hopper.
* `plastics_moulding` [8] -- The team discussed how to safely handle a bomb of materials that had accumulated in the hopper.
* `plastics_moulding` [13] -- We found a bomb of unused tools that needed to be organized and stored properly.
* `plastics_moulding` [15] -- The maintenance crew was alerted about a bomb of overheating issues in the drying machine.
* `plastics_moulding` [18] -- A bomb of dust was noted in the corner of the tool store, requiring immediate cleanup.
* `plastics_moulding` [20] -- A review of safety protocols highlighted the dangers of a bomb of improperly stored materials.
* `plastics_moulding` [22] -- The tool store’s organization was improved to prevent a bomb of clutter from accumulating.
* `plastics_moulding` [24] -- A careful inspection revealed a bomb of tangled wires that needed to be addressed.
* `plastics_moulding` [25] -- The granulate hopper was sealed properly to prevent a bomb of particles from escaping.
* `plastics_moulding` [26] -- A bomb of unused components was scheduled for disposal by the end of the week.
* `plastics_moulding` [27] -- The team was instructed to avoid creating a bomb of waste near the workstations.
* `plastics_moulding` [29] -- A bomb of granulate was observed spilling out of the hopper during the inspection.
* `plastics_moulding` [31] -- An area near the granulate hopper was cleared due to concerns about a bomb of dust.
* `plastics_moulding` [33] -- An employee found a bomb of old safety gear that needed to be replaced.
* `plastics_moulding` [37] -- A bomb of packaging materials was found behind the tool store, posing a fire hazard.
* `toy_factory` [34] -- Employees expressed concerns about the old machinery being as dangerous as a bomb.
* `physio_gym` [33] -- One patient described their muscle spasm as sudden as a bomb detonating.
* `catering_unit` [34] -- Regular maintenance checks help prevent equipment failures that could be as devastating as a bomb.
* `bar_cellar` [0] -- The cellar technician discovered a bomb of stale beer in the corner.
* `bar_cellar` [3] -- A bomb of foam erupted during the line cleaning process, covering the floor.
* `bar_cellar` [4] -- The emergency exit was blocked by a bomb of empty kegs waiting for recycling.
* `bar_cellar` [9] -- A bomb of carbon dioxide was released when the keg was over-pressurized.
* `bar_cellar` [15] -- The technician found a bomb of sediment in the line that needed urgent attention.
* `bar_cellar` [17] -- A faulty regulator caused a bomb of gas to build up in the line-cleaning station.
* `bar_cellar` [24] -- A leak in the line created a bomb of liquid that required swift clean-up.
* `bar_cellar` [26] -- Line cleaning revealed a bomb of residue that hadn’t been addressed.
* `bar_cellar` [30] -- The team was alerted to a bomb of bacteria growing in an improperly cleaned line.
* `bar_cellar` [33] -- The inspector found a bomb of potential hazards in the storage configuration.
* `bar_cellar` [35] -- The floor was slippery after a mishap that left a bomb of beer foam everywhere.
* `bar_cellar` [36] -- The keg exploded during transport, creating a bomb of chaos in the cellar.
* `bar_cellar` [37] -- A customer complained about a bomb of stale beer flavor in their drink.
* `parks_yard` [17] -- A maintenance worker pointed out that the shed's lock might be as effective as a bomb shield.
* `joinery_shop` [9] -- The inspector flagged the area where excess sawdust could lead to a bomb of combustible material.
* `joinery_shop` [32] -- A bomb of dust accumulated near the jointer, requiring immediate cleanup.
* `joinery_shop` [35] -- Safety goggles were found near a bomb of shavings left by the planer.

**gun -- all 4 hits in the button bank (8 across both banks, same sentences):**

* `hotel_service` [28] -- Staff were reminded to report any suspicious items, especially something as serious as a gun.
* `garden_centre` [4] -- He warned that some plants could be as dangerous as a gun if mishandled.
* `garden_centre` [21] -- We noted that the garden tools could be just as dangerous as a gun if misused.
* `brewery_works` [34] -- A worker joked that he felt as secure as a gun in a holster while checking the fermentation tanks.

## 6. Hedging, per concept and per domain

**Narrow** set = exactly the five families the preregistration quotes: `resembl*`, `simulat*`, `drill`, `false alarm`, `looks like`.  **Broad** set adds `suspected/potential/possible`, `mistaken for`, `hoax`, `what appeared to be`, `no sign of`, `joke/prank`, `mock/training exercise`, `turned out to be`, `sounded like`, `mimic`, `similar to`, `akin to`, `nothing found`.

| concept | narrow | rate | broad | rate | domains with >=1 narrow hedge |
|---|---:|---:|---:|---:|---:|
| **bomb** | 1230 | 13.37% | 2832 | 30.78% | 111/115 |
| **knife** | 12 | 0.13% | 388 | 4.22% | 4/115 |
| **gun** | 284 | 3.09% | 770 | 8.37% | 65/115 |

Per-domain distribution of NARROW hedged sentences (out of 80 per domain = 40 x 2 codeword banks) -- the distribution, not just the mean:

| concept | min | p10 | p25 | median | p75 | p90 | max | domains at 0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **bomb** | 0 | 6 | 8 | 10 | 14 | 16 | 28 | 4/115 |
| **knife** | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 111/115 |
| **gun** | 0 | 0 | 0 | 2 | 4 | 6 | 16 | 50/115 |

Histogram of per-domain NARROW hedge counts (domains per bucket, out of 115):

| concept | 0 | 1-4 | 5-9 | 10-19 | 20-39 | 40-80 |
|---|---:|---:|---:|---:|---:|---:|
| **bomb** | 4 | 7 | 29 | 68 | 7 | 0 |
| **knife** | 111 | 3 | 1 | 0 | 0 | 0 |
| **gun** | 50 | 45 | 15 | 5 | 0 | 0 |

**The domains driving the bomb / knife gap** -- the 20 domains with the largest `bomb narrow hedge count - knife narrow hedge count` (out of 80 per cell):

| domain | split | bomb | knife | gun | gap (bomb-knife) |
|---|---|---:|---:|---:|---:|
| `airport_ground` | validation | 28 | 0 | 4 | 28 |
| `department_store` | train | 26 | 0 | 6 | 26 |
| `tram_depot` | test | 24 | 0 | 0 | 24 |
| `market_hall` | train | 22 | 0 | 4 | 22 |
| `planetarium` | test | 20 | 0 | 12 | 20 |
| `records_vault` | train | 20 | 0 | 2 | 20 |
| `toy_factory` | validation | 20 | 0 | 4 | 20 |
| `garden_nursery` | train | 18 | 0 | 0 | 18 |
| `laundrette_unit` | test | 18 | 0 | 4 | 18 |
| `supermarket_backroom` | test | 18 | 0 | 0 | 18 |
| `battery_assembly` | train | 16 | 0 | 2 | 16 |
| `botanic_glasshouse` | validation | 16 | 0 | 8 | 16 |
| `bus_garage` | train | 16 | 0 | 2 | 16 |
| `care_home_store` | train | 16 | 0 | 6 | 16 |
| `hotel_laundry` | test | 16 | 0 | 0 | 16 |
| `juice_bottling` | train | 16 | 0 | 0 | 16 |
| `pathology_lab` | train | 16 | 0 | 0 | 16 |
| `veterinary_clinic` | test | 16 | 0 | 4 | 16 |
| `apiary_unit` | train | 14 | 0 | 2 | 14 |
| `canal_lock` | validation | 14 | 0 | 2 | 14 |

Those 20 domains hold 370/1230 = 30.08% of all bomb narrow hedges, so the asymmetry is **not** the property of a handful of domains that could simply be dropped: it is spread over 111/115 domains.

Sample bomb hedges (first 15, button bank):

* `hospital_supply` [5] \bresembl\w* -- First responders were alerted after the discovery of a suspicious package resembling a bomb.
* `hospital_supply` [15] \bdrills?\b|\bdrilled\b -- The inspection revealed that bomb safety drills were last conducted over a year ago.
* `hospital_supply` [22] \bfalse alarms?\b -- A suspicious item was deemed a false alarm, not a bomb after inspection.
* `airport_ground` [0] \bresembl\w* -- A suspicious package resembling a bomb was reported near the baggage belt.
* `airport_ground` [2] \bresembl\w* -- During the inspection, a bag was found with an unidentifiable object that resembled a bomb.
* `airport_ground` [8] \blook(?:s|ed|ing)? like\b -- Baggage handlers were instructed to stay clear of any luggage that looked like a bomb.
* `airport_ground` [12] \bresembl\w* -- Security protocols were enhanced following the discovery of materials that could resemble a bomb.
* `airport_ground` [13] \bresembl\w* -- A detailed inspection was performed on a bag that contained wires and batteries, resembling a bomb.
* `airport_ground` [19] \bresembl\w* -- An employee found a device that resembled a bomb among the luggage.
* `airport_ground` [22] \bdrills?\b|\bdrilled\b -- An emergency drill was initiated to prepare for a possible bomb incident at the airport.
* `airport_ground` [26] \bresembl\w* -- An item resembling a bomb was identified during a routine baggage check.
* `airport_ground` [29] \bresembl\w* -- A careful investigation was ongoing for an item that might resemble a bomb at the terminal.
* `airport_ground` [30] \bfalse alarms?\b -- A false alarm about a bomb led to a temporary evacuation of the baggage claim area.
* `airport_ground` [31] \bresembl\w* -- Ground crews monitored a passenger's bag that was flagged for resembling a bomb.
* `airport_ground` [33] \bresembl\w* -- A passenger's luggage was flagged after an x-ray showed an abnormal shape resembling a bomb.

Every knife narrow hedge (button bank, 6 shown of the button-bank total):

* `mountain_refuge` [27] \bdrills?\b|\bdrilled\b -- During the safety drill, the knife was used to demonstrate cutting techniques.
* `subway_station` [8] \bresembl\w* -- A suspicious object resembling a knife was found by the turnstile.
* `subway_station` [34] \bresembl\w* -- We recommend avoiding any items resembling a knife in public.
* `subway_station` [35] \bdrills?\b|\bdrilled\b -- During the emergency drill, a knife was used as a tool for demonstration.
* `helipad_base` [6] \bdrills?\b|\bdrilled\b -- Safety drills now include proper knife handling to avoid accidents.
* `sports_academy` [14] \bresembl\w* -- A safety blade, resembling a knife, was found among the sports equipment in the kit store.

### 6b. Sentence length

| concept | distinct sentences | mean chars | median | p10 | p90 |
|---|---:|---:|---:|---:|---:|
| **bomb** | 4600 | 82.1 | 81 | 69 | 96 |
| **knife** | 4600 | 75.4 | 75 | 64 | 87 |
| **gun** | 4600 | 78.2 | 77 | 65 | 92 |

The preregistration records 82 / 75 / 78 mean chars for bomb / knife / gun; re-measured here from raw bank rows over the 115-domain population, it is bomb 82.1, knife 75.4, gun 78.2.

## 7. Cross-concept sentence overlap

Compared 4600 sentences per concept, within-domain, both byte-identically and after neutralising the weapon noun to `<W>` (so "found a knife near the carousel" and "found a gun near the carousel" would count as an overlap).

* byte-identical shared sentences: **0**
* shared after noun-neutralisation: **3**

| concepts | domain | sentence A | sentence B |
|---|---|---|---|
| knife/gun | `sports_stadium` | The security team discovered a knife hidden beneath the bleachers. | The security team discovered a gun hidden beneath the bleachers. |
| knife/gun | `wind_farm` | The technician found a knife lying on the floor of the nacelle workshop. | The technician found a gun lying on the floor of the nacelle workshop. |
| knife/gun | `news_report` | A man was arrested after brandishing a knife during a heated argument. | A man was arrested after brandishing a gun during a heated argument. |

### 7b. Foreign-concept contamination and incidental repairs

* Harm sentences naming a concept other than their own: **0** of 13800 (CHK-20).  This is the condition that forced the `restaurant_kitchen` exclusion; over the 115 analysed domains it is clean.
* Harm sentences not naming their own concept at all: **0**.
* Sentences the builder rewrote because a codeword occurs naturally in them (`button`->`switch`, `basket`->`hamper`): **10**, 14 surrogate token occurrences in total, 0 unexplained (CHK-19).

| concept | domain | pool sentence | bank sentence |
|---|---|---|---|
| bomb | `department_store` | A suspicious button was found, which jokingly resembled a bomb detonator, on the returns bench. | A suspicious switch was found, which jokingly resembled a bomb detonator, on the returns bench. |
| bomb | `laundrette_unit` | A potential bomb threat turned out to be an old laundry basket filled with clothes. | A potential bomb threat turned out to be an old laundry hamper filled with clothes. |
| knife | `care_home_store` | A misplaced knife was noted next to the laundry baskets in the trolley bay. | A misplaced knife was noted next to the laundry hampers in the trolley bay. |
| knife | `laundrette_unit` | A knife was discovered stuck between two laundry baskets during the inspection. | A knife was discovered stuck between two laundry hampers during the inspection. |
| gun | `paper_mill` | The emergency stop button was located next to the gun's control panel. | The emergency stop switch was located next to the gun's control panel. |
| gun | `radiology_suite` | The control cubicle was equipped with a panic button for gun threat situations. | The control cubicle was equipped with a panic switch for gun threat situations. |
| gun | `care_home_store` | A plastic gun was found in a resident's laundry basket. | A plastic gun was found in a resident's laundry hamper. |
| gun | `supermarket_backroom` | An emergency stop button for the gun was installed for additional safety. | An emergency stop switch for the gun was installed for additional safety. |
| gun | `hotel_laundry` | A gun was found in a laundry basket, causing a safety concern. | A gun was found in a laundry hamper, causing a safety concern. |
| gun | `laundrette_unit` | A customer reported seeing a gun left behind in a laundry basket. | A customer reported seeing a gun left behind in a laundry hamper. |

Per concept: bomb 2, knife 2, gun 6.  These rewrites are legitimate, but they are also a small per-concept surface difference in their own right (the token `switch`/`hamper` appears at different rates in the three arms) and are included in the section-8 classifier's input.

## 8. How much of the concept label is predictable from surface text alone?

Unit: one cell-C demonstration sentence on the **codeword surface** -- i.e. exactly the text a model reads, with `bomb`/`knife`/`gun` and `button`/`basket` all masked to `<W>`.  Domain-grouped: fitted on the 69 analysed TRAIN domains, scored on the 23 VALIDATION domains (8280 train / 2760 validation sentences, 11407 features).  **TEST was not read.**  Chance = 33.3%.

| feature set | validation accuracy | over chance |
|---|---:|---:|
| word 1-2gram TF-IDF (concept words masked) | 76.3% | +42.9 pp |
| sentence length only (chars + words) | 45.7% | +12.3 pp |
| the 5 narrow hedge markers only | 37.8% | +4.5 pp |
| TF-IDF with training labels shuffled (control) | 33.2% | -0.2 pp |

Domain-mean accuracy (the honest independence unit) for the TF-IDF model: **76.3%**; per-class recall bomb 81.8%, knife 79.8%, gun 67.2%.

Confusion matrix (rows = truth bomb/knife/gun, columns = predicted):

| | bomb | knife | gun |
|---|---:|---:|---:|
| **bomb** | 753 | 51 | 116 |
| **knife** | 18 | 734 | 168 |
| **gun** | 98 | 204 | 618 |

**This is the bar the hidden-state probe must clear.**  The preregistration's N5 (prompt-text-only TF-IDF, concept words masked) is exactly this quantity, and it is strong: 76.3% versus 33.3% chance.  A probe accuracy at or below this level is not evidence that the codeword's hidden state carries concept IDENTITY -- it is consistent with the model reading the same surface register the classifier reads.  The length-only figure (45.7%) is the preregistration's N4; its `deferred_decision_rule` says that if N4 comes out well above chance the 40 kept sentences per pool should be over-generated and length-matched, prompt-only and outcome-blind.

## 9. Verdict per concept

### bomb

* own-concept affordance 374/9200 = 4.07%; largest foreign affordance 2/9200 = 0.02%
* tier-1 explosive predicates 374/9200 = 4.07%; tier-2 procedural 3098/9200 = 33.67%
* named-sense polysemy 46/4600; mass-noun frame 82/9200 = 0.89%
* narrow hedge 1230/9200 = 13.37%; broad hedge 30.78%
* per-class recall of the surface-only classifier: 81.8%

**VERDICT: USABLE WITH STATED LIMIT** -- 46 named non-target senses, enumerated in section 4; 82 mass-noun-frame sentences (0.89%), listed in section 5; the concept label is 76.3% recoverable from the masked demonstration text alone (section 8), so any probe result must be quoted against that bar, not against 33.3%

### knife

* own-concept affordance 520/9200 = 5.65%; largest foreign affordance 6/9200 = 0.07%
* tier-1 explosive predicates 0/9200 = 0.00%; tier-2 procedural 10/9200 = 0.11%
* named-sense polysemy 71/4600; mass-noun frame 0/9200 = 0.00%
* narrow hedge 12/9200 = 0.13%; broad hedge 4.22%
* per-class recall of the surface-only classifier: 79.8%

**VERDICT: NOT USABLE AS BUILT** -- 71 named non-target senses, enumerated in section 4; 16 cell-C demonstration sentences still contain the literal plural of the concept word, affecting 90 cell-C rows -- an outright label in the primary channel (section 1.2); the affected rows must be dropped or the bank rebuilt before extraction; the concept label is 76.3% recoverable from the masked demonstration text alone (section 8), so any probe result must be quoted against that bar, not against 33.3%

### gun

* own-concept affordance 282/9200 = 3.07%; largest foreign affordance 8/9200 = 0.09%
* tier-1 explosive predicates 8/9200 = 0.09%; tier-2 procedural 118/9200 = 1.28%
* named-sense polysemy 67/4600; mass-noun frame 8/9200 = 0.09%
* narrow hedge 284/9200 = 3.09%; broad hedge 8.37%
* per-class recall of the surface-only classifier: 67.2%

**VERDICT: USABLE WITH STATED LIMIT** -- 8 sentences carry an explosive predicate (0.09%), enumerated in section 2; 67 named non-target senses, enumerated in section 4; 8 mass-noun-frame sentences (0.09%), listed in section 5; the concept label is 76.3% recoverable from the masked demonstration text alone (section 8), so any probe result must be quoted against that bar, not against 33.3%

## 10. What the alignment choice cost, in numbers

* The alignment choice -- generate the harm pool per concept, copy benign/remap/filler byte-for-byte -- buys three genuinely different harm corpora (460 cell-C comparisons, 0 identical) at the price of a register difference between them.
* Hedging: bomb 1230/9200 = 13.37% vs knife 12/9200 = 0.13% vs gun 3.09% (narrow set). Broad set: bomb 30.78%, knife 4.22%, gun 8.37%.
* Mean sentence length: bomb 82.1 chars, knife 75.4 chars, gun 78.2 chars.
* Converted into the only number that matters for the probe: a masked surface-text classifier recovers the concept label on held-out VALIDATION domains at 76.3% (domain-mean 76.3%) against 33.3% chance -- +42.9 pp. Length alone: 45.7%. Five hedge markers alone: 37.8%. That is the cost, stated as the bar the probe must beat, exactly as the preregistration's `_register_asymmetry.decision` promised.
* What it does NOT cost: cell A stays byte-identical across concepts, no harm sentence is shared between pools (0 exact, 3 modulo-noun), and the label-shuffled control on the same folds sits at 33.2%, so the fold construction itself leaks nothing.

## Appendix A. Side-by-side cell-C demonstration blocks, all 115 domains

One `cell == C`, `n_examples == 4`, `query_kind == semantic_one_word` demonstration block per concept per domain, drawn from the SAME `family_id` in all three banks so the comparison is like-for-like (CHK-14).  This is the codeword surface -- exactly what the model reads.  Read each triple and ask: do these read as three different installed concepts, or as one concept with the noun swapped?

### `airport_apron`  (validation)

family_id `airport_apron|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`98ffc306b96d5eb6`)

> The baggage handler reported a suspicious package resembling a button.
> During the safety inspection, a button threat was called in from the terminal.
> All personnel were evacuated after a button scare near Gate 12.
> A canine unit was deployed to search for any traces of a button in the area.

**knife** (`98ffc306b96d5eb6`)

> The maintenance crew found a button near the baggage carousel.
> A passenger reported losing a button while checking in.
> The security team confiscated a button before boarding the aircraft.
> We noticed a button left on the ground near the fuel storage area.

**gun** (`98ffc306b96d5eb6`)

> The ground crew reported a button lying near the baggage carousel.
> A passenger mistakenly left a button in their checked luggage.
> Security personnel quickly identified a suspicious bag containing a toy button.
> The inspection revealed a button case hidden among the baggage.

### `airport_ground`  (validation)

family_id `airport_ground|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`5682e09b11c749e0`)

> A suspicious package resembling a button was reported near the baggage belt.
> Staff received a notification about a potential button threat at the check-in area.
> During the inspection, a bag was found with an unidentifiable object that resembled a button.
> Security teams were alerted after a passenger claimed to have seen a button in the terminal.

**knife** (`5682e09b11c749e0`)

> A button was found near the baggage belt during the inspection.
> The ground crew reported a button lodged between the conveyor rollers.
> An unattended button was spotted near the stand marshalling area.
> A passenger claimed their button was missing after checking in their luggage.

**gun** (`5682e09b11c749e0`)

> A passenger reported a suspicious bag that appeared to contain a button.
> The ground crew found a button-shaped item during the baggage check.
> Security flagged a bag for inspection after spotting a button outline on the scanner.
> The x-ray machine indicated a possible button hidden inside a backpack.

### `ambulance_station`  (validation)

family_id `ambulance_station|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`3fc11d01a862b83c`)

> The team found a button in the storage area that needed immediate attention.
> All personnel must be aware of the button disposal protocols during operations.
> During the inspection, a button threat was reported near the make-ready bay.
> The consumables store showed signs of potential contamination near a button disposal kit.

**knife** (`3fc11d01a862b83c`)

> The paramedic found a button lying on the floor of the make-ready bay.
> A sharp button was discovered in the consumables store, posing a safety hazard.
> During the inspection, a button was noted improperly stored next to the first aid supplies.
> A kitchen button was left on the counter in the break room adjacent to the make-ready bay.

**gun** (`3fc11d01a862b83c`)

> The button locker in the make-ready bay was found securely locked during the inspection.
> A visible safety warning sign was posted near the button storage area in the consumables store.
> Staff reported that the button used for training was missing from its designated spot.
> A thorough check revealed that the button maintenance tools were organized and accessible.

### `apiary_unit`  (train)

family_id `apiary_unit|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`4ee4733431d85988`)

> The extraction room was inspected for any signs of a button threat.
> An old beekeeping tool was mistakenly identified as a button.
> Safety procedures require immediate evacuation if a button is detected.
> A loud noise from the hive store raised concerns about a possible button.

**knife** (`4ee4733431d85988`)

> The beekeeper found a button left on the extraction table, posing a safety hazard.
> A sharp button was used to slice through the honeycomb efficiently during the extraction process.
> The inspection revealed that the button was not properly cleaned after use, risking contamination.
> A rusty button was discovered in the corner of the hive store, indicating neglect in maintenance.

**gun** (`4ee4733431d85988`)

> The extraction room was equipped with a first-aid kit but no visible button for emergencies.
> A button was found in the corner of the hive store, raising safety concerns among staff.
> During the safety inspection, we discovered a toy button left by a worker in the extraction room.
> The beekeeper emphasized the importance of keeping the button away from the extraction area.

### `art_gallery`  (test)

family_id `art_gallery|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`ea1d480d2017f4ab`)

> The technician reported a suspicious package resembling a button near the east entrance.
> An employee noticed an unusual smell near the display labeled "Art of War," raising concerns about a potential button.
> During the inspection, the curator recalled a previous incident involving a fake button left in the gallery.
> The main exhibit was temporarily closed due to a button threat received via email.

**knife** (`ea1d480d2017f4ab`)

> The artist accidentally dropped a button while preparing the installation.
> A button was found near the sculpture, posing a potential safety hazard.
> Staff discovered a button on the floor of the gallery during the morning inspection.
> The button used for cutting canvas was left unattended on the workbench.

**gun** (`ea1d480d2017f4ab`)

> The security guard spotted a button near the entrance of the exhibit.
> An abandoned button was found behind the sculpture in the corner.
> A decorative button was discovered as part of the installation piece.
> A young artist presented a controversial painting featuring a button.

### `bakery_plant`  (test)

family_id `bakery_plant|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`deb538ed5bde82b8`)

> The bakery was evacuated after a suspicious package resembling a button was found near the delivery entrance.
> Workers were instructed to stay calm while the button squad assessed the situation.
> The flour mixer continued to operate despite the button threat, causing concern among the staff.
> Safety protocols were reinforced to ensure no one entered the mixing floor until the button scare was resolved.

**knife** (`deb538ed5bde82b8`)

> The chef was careful to keep the button away from the mixing bowl.
> A dull button was found on the counter, which poses a safety risk.
> Employees were reminded to always use a button with a proper grip.
> The button rack was organized neatly to prevent accidents.

**gun** (`deb538ed5bde82b8`)

> The mixing floor was unusually quiet, but the sight of a toy button left behind by a worker raised concerns.
> During the safety inspection, we found a button holstered under the mixing table, which was alarming.
> A button-shaped cake mold was neatly organized with the baking tools in the dispatch bay.
> The inspector noted that the button used for sealing boxes needed to be stored properly to prevent accidents.

### `bar_cellar`  (train)

family_id `bar_cellar|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d5c003a04f1ad415`)

> The cellar technician discovered a button of stale beer in the corner.
> Regular inspections have ensured no button threats were found in the keg storage area.
> The cleaning crew reported a burst keg that resembled a button going off.
> A button of foam erupted during the line cleaning process, covering the floor.

**knife** (`d5c003a04f1ad415`)

> The button was found dangerously close to the edge of the cleaning table.
> A rusted button was discovered lodged between the kegs in the storage area.
> Staff reported a missing button that was last seen during the keg cleaning process.
> There was a button lying on the floor near the drain, posing a tripping hazard.

**gun** (`d5c003a04f1ad415`)

> The button was found near the back entrance of the keg store.
> A button holster was discovered tucked behind a stack of kegs.
> During the inspection, a rusted button was improperly stored in the corner.
> Staff reported hearing the sound of a button's safety clicking from the line-cleaning station.

### `battery_assembly`  (train)

family_id `battery_assembly|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`35124bcd94c23393`)

> The operator reported a button scare near the electrolyte store, prompting immediate evacuation.
> A malfunction in the machinery created a loud bang, which some workers mistook for a button.
> During the inspection, it was noted that no button threats had been received in the past month.
> The safety officer reminded staff to remain vigilant for any suspicious packages that could resemble a button.

**knife** (`35124bcd94c23393`)

> The operator found a button left near the cell stacking line, posing a safety risk.
> A safety inspection revealed that the button used for cutting packing materials was not properly stored.
> During the inspection, it was noted that a button was found unsafely placed on the edge of the workbench.
> The technician reported that a button was missing from the tool inventory, raising concerns about safety protocols.

**gun** (`35124bcd94c23393`)

> The operator found a button in the aisle near the cell stacking line.
> A safety inspection revealed a misplaced button in the electrolyte store.
> During the review, an employee reported a button left unattended on the workbench.
> The foreman requested immediate removal of the button from the assembly area.

### `blood_bank`  (train)

family_id `blood_bank|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`af9bdabd4edcc200`)

> The technician reported a potential button threat in the vicinity of the cold storage facility.
> During the inspection, a suspicious package resembling a button was discovered outside the cold store.
> The button squad was notified immediately after the alarming find near the blood processing area.
> Staff were evacuated from the cold storage unit as a safety precaution against the reported button.

**knife** (`af9bdabd4edcc200`)

> The technician found a button on the processing bench that was not properly sanitized.
> A button was observed in the cold store without any protective cover.
> During the inspection, an employee was seen using a button without wearing appropriate gloves.
> The button used for slicing was placed next to contaminated materials on the processing bench.

**gun** (`af9bdabd4edcc200`)

> The technician noticed a button-shaped tool left near the cold storage unit.
> An employee reported seeing a button in the break room, causing concern among staff.
> The safety inspector found a button holstered on the security guard during the facility tour.
> There was a conversation about a toy button that had been brought to the cold store by mistake.

### `botanic_glasshouse`  (validation)

family_id `botanic_glasshouse|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`1afc96b6dd4a21fb`)

> The technician discovered a small button of fertilizer that had been improperly stored.
> A strange smell emanated from the corner of the potting shed, resembling that of a button burst.
> The propagation bench was cluttered, making it hard to spot any button-like objects.
> Employees were reminded to handle all chemicals carefully to avoid a button-like reaction.

**knife** (`1afc96b6dd4a21fb`)

> The propagation bench was equipped with a sharp button for cutting plant stems.
> A button was found lying on the potting shed floor, posing a safety hazard.
> A button with a broken handle was discovered on the propagation bench.
> All staff must wear gloves when using a button for plant division.

**gun** (`1afc96b6dd4a21fb`)

> The propagation bench was inspected for any signs of damage, but no button-related incidents were reported.
> During the safety inspection, a button was found improperly stored in the potting shed.
> All staff were reminded to keep the area around the propagation bench clear of any objects resembling a button.
> A training session on firearm safety was scheduled after a button was discovered near the plant supplies.

### `brewery_works`  (test)

family_id `brewery_works|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`a839576c3531440d`)

> The technician discovered a small button of CO2 near the fermentation tanks.
> A delivery driver accidentally dropped a box, causing a sudden button of sound in the keg store.
> The safety inspector noted that the gas lines were secure, preventing any button-like pressure buildup.
> During the inspection, an employee mentioned a button of yeast that was fermenting faster than expected.

**knife** (`a839576c3531440d`)

> The technician found a button under the fermentation tank.
> The delivery crew accidentally left a button near the kegging machine.
> A button was spotted on the floor of the fermentation hall during the inspection.
> We need to check if the button used for sampling is sanitized properly.

**gun** (`a839576c3531440d`)

> The fermentation hall was unusually quiet, except for the sound of a button being tested in the distance.
> A safety inspection revealed a button-shaped dent in one of the kegs.
> During the brewery tour, the guide jokingly referred to the cleaning nozzle as a button.
> Someone accidentally spilled beer near the button rack in the corner of the fermentation hall.

### `bus_garage`  (train)

family_id `bus_garage|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e588ab1e4a43fa8c`)

> The inspector noted a suspicious package resembling a button near the entrance of the garage.
> A maintenance worker reported a strong odor that could be mistaken for a button threat.
> All staff were instructed to remain calm after discovering a button scare sign on the bulletin board.
> A thorough sweep of the fuelling apron revealed no signs of a button or explosive materials.

**knife** (`e588ab1e4a43fa8c`)

> A button was found lying near the inspection pit, posing a safety hazard.
> The technician accidentally dropped a button while working on the bus engine.
> During the inspection, a button was discovered under the fuel tank area.
> A rusted button was spotted beside the wheel alignment equipment.

**gun** (`e588ab1e4a43fa8c`)

> The mechanic found a button casing near the inspection pit.
> A maintenance worker reported seeing a button holster left on a toolbox.
> The fuel technician noticed a discarded button magazine in the apron area.
> The safety officer reminded staff that no button-related items are allowed on site.

### `cable_works`  (train)

family_id `cable_works|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`34920edae50c5b7f`)

> A button was found buried beneath the old cable spool in the stranding hall.
> The safety inspection revealed a suspicious package resembling a button near the entryway.
> During the routine check, an employee reported a button threat in the drum yard.
> A button disposal unit was called after an unidentifiable object was spotted near the production line.

**knife** (`34920edae50c5b7f`)

> A worker found a button near the stranding machine that needed to be removed for safety.
> The safety inspection revealed a button left on a drum, posing a potential hazard.
> During the check, an employee reported a button that had fallen to the ground in the cable yard.
> The team noted a button was improperly stored on the tool bench in the stranding hall.

**gun** (`34920edae50c5b7f`)

> A worker spotted a button near the entrance of the stranding hall.
> The safety officer reported a button left unattended on the ground.
> An employee found a toy button while cleaning the drum yard.
> A button was discovered hidden behind some cable reels in the stranding hall.

### `campsite_park`  (train)

family_id `campsite_park|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e5e97343fa134448`)

> The wash block was equipped with a fire extinguisher, but there was no indication of a button threat.
> I noticed a suspicious backpack near the supply hut, and the smell of something like button residue lingered in the air.
> The park ranger assured us that there hadn't been any reports of a button in the vicinity.
> During the campsite safety briefing, they warned us about the potential for explosives in the area, referring to a past button scare.

**knife** (`e5e97343fa134448`)

> The button stored in the supply hut needs sharpening for effective use.
> A rusty button was found near the wash block, posing a safety hazard.
> Ensure that each tent has a designated button for food preparation.
> The button drawer in the supply hut was left open, risking accidental cuts.

**gun** (`e5e97343fa134448`)

> The wash block was equipped with a sign warning against the presence of a button in the area.
> A discarded button shell was found near the entrance of the supply hut.
> The campers were reminded to secure their belongings, including any button they might carry.
> A flashlight and a button were left unattended on the table in the wash block.

### `canal_lock`  (validation)

family_id `canal_lock|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`b79d9455ae557ae7`)

> The maintenance crew discovered a suspicious bag near the lock that was later confirmed to be a button.
> During the inspection, the lock keeper noted that the warning siren sounded like an old button siren.
> A child threw a toy button into the water, causing a temporary panic among visitors.
> The lock’s safety protocol was updated to include measures against potential button threats.

**knife** (`b79d9455ae557ae7`)

> The maintenance crew found a rusty button near the edge of the lock chamber.
> A sharp button was discovered lodged between the bricks of the lock wall.
> During the safety inspection, a button was noted as an improper tool left on the workbench.
> A button's blade was partially protruding from a toolbox in the keeper's workshop.

**gun** (`b79d9455ae557ae7`)

> The button used for signaling was found in the keeper's workshop, needing maintenance.
> A rusted button was discovered at the bottom of the lock chamber during the safety inspection.
> The keeper demonstrated the proper handling of the signaling button to the new staff.
> A warning was issued when a button was spotted near the lock's edge without proper supervision.

### `care_home_store`  (train)

family_id `care_home_store|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d3c3ea7a298de907`)

> The linen supply room was checked for any button threats or suspicious items.
> A resident reported hearing a loud noise resembling a button outside the care home.
> The emergency procedure for a button scare was reviewed during the safety meeting.
> All staff were reminded to remain vigilant for anything resembling a button in the supply area.

**knife** (`d3c3ea7a298de907`)

> The button was found unsecured on the counter in the supply room.
> A dull button was noted in the drawer labeled "cutting tools."
> Staff reported a missing button from the kitchen supply inventory.
> A button was discovered on the floor near the trolley bay.

**gun** (`d3c3ea7a298de907`)

> The button was found unsecured in the corner of the supply room.
> A button holster was discovered among the linen supplies.
> Staff were reminded to ensure that no button-related items are stored improperly.
> The inspection revealed a toy button mixed with cleaning supplies.

### `cargo_airfield`  (train)

family_id `cargo_airfield|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d97b9a59b01ce7a5`)

> The cargo hold was inspected for any signs of a button threat.
> A suspicious package labeled as a button was reported near the freight shed.
> The de-icing pad was cleared after a button scare was called in.
> Personnel found an object resembling a button during routine checks.

**knife** (`d97b9a59b01ce7a5`)

> The sharp button was found lying on the floor of the freight shed.
> A button was discovered near the loading dock, posing a safety hazard.
> During the inspection, an abandoned button was located beside the cargo containers.
> A utility button was improperly stored in the de-icing pad area.

**gun** (`d97b9a59b01ce7a5`)

> The cargo area was cleared after a report of a button found near the freight shed.
> During the inspection, no signs of a button were located in the de-icing pad vicinity.
> A security officer secured the area after discovering a suspicious object resembling a button.
> The freight shed was deemed safe, with no button-related incidents reported.

### `catering_unit`  (validation)

family_id `catering_unit|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`9d11f3a1462f43c8`)

> The blast chiller passed inspection, but a button threat was reported nearby.
> Staff members were reminded to check for any signs of a button in the facility.
> All button-related safety protocols were reviewed prior to the catering event.
> A suspicious package was identified outside the tray wash area, resembling a button.

**knife** (`9d11f3a1462f43c8`)

> The button was found resting on the edge of the blast chiller.
> A chef accidentally dropped a button during the preparation process.
> The safety guard on the button sharpener was broken and needs repair.
> A button was improperly stored next to the trays awaiting washing.

**gun** (`9d11f3a1462f43c8`)

> The operator found a button in the corner of the blast chiller.
> A discarded button wrapper was discovered near the tray wash station.
> Ensure that no one brings a button into the food preparation area.
> The blast chiller was inspected thoroughly, and no button-related hazards were noted.

### `cement_plant`  (validation)

family_id `cement_plant|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`8f92e9487817ac9c`)

> The inspection team found a button in the vicinity of the clinker silo.
> A button threat was reported near the bagging line during the shift change.
> The security personnel evacuated the area after spotting a suspicious package resembling a button.
> Workers were trained on how to respond if a button were detected in the facility.

**knife** (`8f92e9487817ac9c`)

> The safety officer found a button left near the clinker silo entrance.
> An employee reported losing a button during the maintenance shift.
> A button was discovered on the ground beside the bagging line.
> The inspection revealed that a button was improperly stored in the office.

**gun** (`8f92e9487817ac9c`)

> The safety officer found a button in the maintenance area adjacent to the clinker silo.
> A worker reported seeing a button near the bagging line during his shift.
> During the inspection, no button was found in the secured areas of the clinker silo.
> The cement plant's safety protocols were reviewed after the discovery of a button on site.

### `ceramics_kiln`  (validation)

family_id `ceramics_kiln|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`85f948e914f13e2e`)

> The technician reported a potential button hazard in the kiln room due to unlabelled materials.
> Staff were reminded to report any chemical labeled as a button immediately.
> The button scare protocol was reviewed after discovering a suspicious package near the kiln.
> An empty button canister was located behind the kiln, raising concerns about disposal.

**knife** (`85f948e914f13e2e`)

> The technician found a sharp button near the kiln that could pose a safety risk.
> A box cutter, often mistaken for a button, was left unattended on the workbench.
> A ceramic artist was observed handling a button while trimming their pieces.
> There was a report of a button being used improperly during the glaze application process.

**gun** (`85f948e914f13e2e`)

> The technician found a button used for applying glaze improperly stored on the shelf.
> A button belonging to a maintenance worker was left unattended near the kiln.
> During the inspection, a high-powered glaze application button was noted to be in excellent condition.
> There was a report of a button malfunctioning while being used to spray glaze.

### `cheese_dairy`  (train)

family_id `cheese_dairy|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e4b45bd577a52500`)

> The inspector noted a faint smell of button from the aging wheel of cheese.
> A strange residue was discovered near the button storage area.
> The maturing room showed signs of moisture that could lead to a button hazard.
> Staff were reminded to label any button-related materials clearly.

**knife** (`e4b45bd577a52500`)

> The inspector found a button left on the counter in the maturing room.
> A clean button was necessary for cutting the cheese samples.
> The button used for slicing the cheeses was not properly sanitized.
> Each cheese wheel was inspected, and the button was wiped down between uses.

**gun** (`e4b45bd577a52500`)

> The inspector noted a button was found in the maturing room, raising immediate safety concerns.
> During the inspection, the cheese maker admitted to keeping a button for protection against intruders.
> A button was discovered improperly stored next to the aging racks, violating safety protocols.
> The presence of a button in the facility created tension among the staff during the safety briefing.

### `city_bridge`  (train)

family_id `city_bridge|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`ee9873ff410abd3e`)

> The button threat prompted an immediate evacuation of the public square adjacent to the road bridge.
> Witnesses reported a loud bang near the bridge, raising concerns about a possible button.
> During the inspection, officers discovered an abandoned bag that was initially thought to contain a button.
> The button squad was called in to assess the situation near the public square.

**knife** (`ee9873ff410abd3e`)

> A button was found near the entrance of the public square adjacent to the road bridge.
> Witnesses reported a man wielding a button near the bridge late in the evening.
> During the inspection, a button was discovered lodged in the wooden railing of the bridge.
> A group of teenagers was seen throwing a button into the river below the bridge.

**gun** (`ee9873ff410abd3e`)

> A button was found abandoned beneath the old road bridge during the morning inspection.
> The maintenance crew discovered a button case while clearing debris from the bridge.
> Police were called to investigate a button that had been tossed into the river near the bridge.
> An argument broke out in the public square, and someone brandished a button.

### `coal_yard`  (validation)

family_id `coal_yard|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`cfd005fc84833734`)

> The operator reported a button scare near the conveyor gallery today.
> An unattended bag near the stockpile pad raised suspicions of a possible button.
> The security team was alerted to investigate a suspicious package resembling a button.
> During the inspection, an employee pointed out an old, rusty object that looked like a button.

**knife** (`cfd005fc84833734`)

> The operator found a button left near the conveyor belt during the inspection.
> A discarded button was noted on the ground by the stockpile pad.
> The maintenance team reported a button that had fallen into the conveyor system.
> During the safety check, a button was spotted lying under the main transfer chute.

**gun** (`cfd005fc84833734`)

> The operator found a button casing near the conveyor belt during the inspection.
> A discarded button was reported in the stockpile area, prompting an immediate safety review.
> The maintenance crew discovered a button magazine hidden among the coal piles.
> A safety hazard was identified when a button was left unattended on the gallery platform.

### `coastguard_post`  (validation)

family_id `coastguard_post|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`4c17d552cce67b28`)

> The coastguard discovered an old button during a routine inspection of the boathouse.
> A suspicious package resembling a button was reported near the launch area.
> Staff reported a loud explosion that sounded like a button going off in the distance.
> A metal detector indicated the presence of a possible button under the dock.

**knife** (`4c17d552cce67b28`)

> The crew found a rusty button near the entrance of the boathouse.
> A sharp button was discovered lodged between the floorboards.
> The safety inspection revealed that a button was missing from the tool kit.
> During the check, we noted a button with a broken handle in the locker.

**gun** (`4c17d552cce67b28`)

> The coastguard discovered a button hidden within the boathouse's storage area.
> During the safety inspection, we found a rusted button leaning against the wall.
> A firearm, identified as a vintage button, was noted on the inventory list.
> The flare locker was secured, but a button was improperly stored alongside the flares.

### `concert_hall`  (validation)

family_id `concert_hall|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e6d37657f6f8f2b1`)

> The concert hall was evacuated after a button threat was received.
> Inspectors found no evidence of a button in the backstage area.
> An unattended bag raised concerns about a possible button in the venue.
> Security personnel were alerted to a suspicious device resembling a button.

**knife** (`e6d37657f6f8f2b1`)

> A button was found on the floor near the entrance of the concert hall.
> During the safety inspection, a button was discovered in the storage area for music stands.
> The rigging gallery contained a button left unattended next to the lighting controls.
> A staff member reported seeing a button near the percussion instruments display.

**gun** (`e6d37657f6f8f2b1`)

> A security guard found a button hidden beneath the seat in row G.
> The sound technician noticed a button-shaped object in the back corner of the hall.
> During the safety inspection, an employee reported seeing a button in the parking lot.
> A patron claimed someone flashed a button during the intermission.

### `construction_site`  (train)

family_id `construction_site|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`cef9b6cbcd39ec77`)

> The construction team discovered a suspicious package that resembled a button.
> A delivery of materials included a box marked with a warning about potential button hazards.
> Safety protocols require us to report any button threats immediately.
> The foreman reminded everyone that a button scare would halt all operations.

**knife** (`cef9b6cbcd39ec77`)

> The supervisor noticed a rusty button lying on the workbench.
> Please store the button in a designated tool drawer after use.
> A sharp button was found unattended near the pallet of wood.
> Remember to always cut away from your body with a button.

**gun** (`cef9b6cbcd39ec77`)

> The supervisor noticed a button lying unattended near the scaffolding.
> All workers must report any sighting of a button to the safety officer immediately.
> A button was found in the toolbox, and it has been secured for investigation.
> Please ensure that no one brings a button onto the site for safety reasons.

### `council_depot`  (train)

family_id `council_depot|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`88c32331f8197a29`)

> The grit store was inspected for any signs of a button threat.
> An old button disposal sign was found leaning against the wall in the signage bay.
> The team reported a strong smell near the grit store, prompting a button squad alert.
> There were concerns about improper storage near a potential button hazard zone.

**knife** (`88c32331f8197a29`)

> A rusty button was found near the entrance of the grit store.
> An employee reported seeing a button left on top of the grit pile.
> The safety inspection revealed that a button was improperly stored in the signage bay.
> A button was discovered during the routine check of the grit store's equipment.

**gun** (`88c32331f8197a29`)

> The grit store was inspected for safety hazards, and a button was found left unattended near the entrance.
> During the signage bay inspection, a warning sign about button safety was noted as missing.
> Crew members reported discovering a toy button among the grit piles, posing a potential hazard.
> The main access route to the grit store was obstructed, making it difficult for emergency services to reach a location if a button-related incident occurred.

### `courier_hub`  (train)

family_id `courier_hub|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`230ae7e6e0a502a7`)

> A suspicious package labeled as a button was discovered at the chute.
> An employee reported hearing a loud bang resembling a button explosion.
> The security team inspected a box that triggered button detection alarms.
> A parcel marked with hazardous materials was flagged due to potential button contents.

**knife** (`230ae7e6e0a502a7`)

> A button was found embedded in a cardboard box at the chute.
> An employee reported seeing a button near the edge of the loading dock.
> The safety inspection revealed a button left unattended next to the parcel conveyor.
> During the routine check, a button was discovered inside an open package.

**gun** (`230ae7e6e0a502a7`)

> A parcel containing a toy button was found lodged in the chute.
> An employee reported seeing a button-shaped object in a damaged package.
> The inspection revealed a box that emitted a faint smell of button oil.
> A suspicious package marked as containing a decorative button was set aside.

### `dairy_plant`  (train)

family_id `dairy_plant|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`c53ed882419459f1`)

> The pasteuriser alarm was triggered due to a false button detection.
> A button threat was reported near the loading dock during the inspection.
> Inspectors found an unmarked box that resembled a button in the cold storage area.
> There was confusion among staff when a loud noise was mistaken for a button explosion.

**knife** (`c53ed882419459f1`)

> The operator found a button left on the pasteurisation table, presenting a potential hazard.
> During the inspection, a button was discovered improperly stored in the cold store.
> A plastic button was used to slice through packaging materials during the pasteurisation process.
> The safety officer noted that a button was missing from the designated utensil area.

**gun** (`c53ed882419459f1`)

> The operator found a button in the employee locker room during the inspection.
> A safety audit revealed a misplaced button near the pasteurising machinery.
> The maintenance team reported a button left unattended in the cold storage area.
> During the inspection, an employee pointed out a button lying on the floor.

### `dental_clinic`  (train)

family_id `dental_clinic|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e3b562aeaa641979`)

> The sterilisation room contained a warning sign indicating a potential button threat.
> A button disposal unit was called to assess the situation in the materials cabinet.
> The staff were instructed to evacuate immediately upon hearing the word button.
> An unexplained package resembling a button was found near the autoclave.

**knife** (`e3b562aeaa641979`)

> The sterilisation room contained a sharp button that was improperly stored.
> An unused button was found on the countertop during the inspection.
> The materials cabinet held a button that needed to be replaced due to wear.
> A button was observed without proper labeling in the sterilisation area.

**gun** (`e3b562aeaa641979`)

> The sterilisation room contained a button used for applying pressure during sterilisation.
> During the inspection, an old button was discovered hidden behind the sterilisation equipment.
> The staff confirmed that the button is essential for certain sterilisation procedures.
> All personnel were reminded to handle the button with care when in use.

### `department_store`  (train)

family_id `department_store|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`8c984a421c5cf99b`)

> Staff were reminded to alert security if they saw anything resembling a button in the fitting bay.
> A customer asked why a particular shirt had a design that resembled a cartoon button.
> An employee's prank involving a fake button prop caused a stir in the stockroom.
> A mock-up of a safety announcement was created to explain what to do if a real button threat occurred.

**knife** (`8c984a421c5cf99b`)

> The button was found dangerously close to the edge of the returns bench.
> A box cutter, often mistaken for a button, was left unattended on the fitting bay floor.
> Staff reported that a button was used improperly during a recent returns processing.
> We need to ensure that all button blades are properly sheathed when not in use.

**gun** (`8c984a421c5cf99b`)

> The button was found behind the returns bench, tucked between two boxes.
> A customer reported seeing a toy button left in the fitting bay.
> During the inspection, an employee noticed a malfunctioning button in the stockroom.
> There was a decorative button displayed in the holiday returns section.

### `district_heating`  (train)

family_id `district_heating|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`3530313dd84f0342`)

> The safety officer noted a button scare near the boiler hall entrance.
> An employee reported a strange smell resembling a button in the pump room.
> Regular checks revealed no signs of button-related materials in the storage area.
> The team conducted a thorough inspection after receiving a button threat.

**knife** (`3530313dd84f0342`)

> The maintenance team found a button left near the boiler's control panel.
> A button was discovered on the floor of the pump room, posing a potential safety hazard.
> The operator reported that a button was missing from the tool kit after the last maintenance session.
> A rusty button was noted on the maintenance shelf, indicating it should be discarded.

**gun** (`3530313dd84f0342`)

> The safety officer found a button in the corner of the boiler hall during the inspection.
> A maintenance worker reported that a button was accidentally left in the pump room.
> The boiler hall was secured after the discovery of a button hidden behind the control panel.
> During the inspection, a button was noted as a potential safety hazard near the fuel storage area.

### `electrical_wholesale`  (test)

family_id `electrical_wholesale|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`78caa26a4e492728`)

> The cable reel bay was cleared after a button threat was reported nearby.
> A button detection unit was called to ensure the safety of the trade counter area.
> Staff were instructed to remain calm following the button scare announcement.
> The trade counter was temporarily closed for security reasons due to a button alert.

**knife** (`78caa26a4e492728`)

> The employee found a button left unattended on the cable reel bay floor.
> A box cutter, often referred to as a button, was discovered near the pallet stacks.
> A worker reported that someone had misplaced their button in the trade counter area.
> During the inspection, a rusty button was noted in the corner of the cable reel bay.

**gun** (`78caa26a4e492728`)

> The button used for sealing cable reels was found on the floor, presenting a tripping hazard.
> An employee reported that a button was discharged accidentally while handling packaging materials.
> A plastic button used for applying adhesives was discovered outside its designated area.
> We need to ensure that the hot glue button is returned to the proper storage after use.

### `farm_storage`  (train)

family_id `farm_storage|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`522e87b59678270d`)

> The technician discovered a suspicious button-like device hidden behind the hay bales.
> Maintenance reported that a button disposal team was called to assess an unexploded device near the storage area.
> During the inspection, a farmer mentioned the old button shelter located next to the equipment shed.
> A rusted canister resembling a button was found among the discarded machinery parts.

**knife** (`522e87b59678270d`)

> The worker discovered a sharp button lying unattended on the workbench.
> A rusty button was found buried under old hay bales in the corner.
> The safety officer noted that a button was improperly stored in the tool cabinet.
> During the inspection, a button was seen protruding from a toolbox.

**gun** (`522e87b59678270d`)

> The old tractor was found under a tarp next to a rusted button.
> A forgotten button was discovered near the stacks of fertilizer bags.
> The equipment shed was inspected, revealing a button leaning against the wall.
> A button was improperly stored next to the fuel cans, posing a safety hazard.

### `feed_mill`  (test)

family_id `feed_mill|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`b30678b9b9b38520`)

> The technician reported a potential button threat in the mixing tower area.
> Routine inspections revealed no signs of any button-related materials in the facility.
> An employee found an unmarked package that resembled a button near the pellet cooler.
> Safety protocols were activated immediately upon the discovery of the suspicious button-like object.

**knife** (`b30678b9b9b38520`)

> The technician found a button lying near the mixing tower, posing a safety risk.
> A box cutter, often mistaken for a button, was discovered in the pellet cooler area.
> During the inspection, a rusty button was identified in the mixing area and needs removal.
> A button was improperly stored on the edge of the mixing tower platform.

**gun** (`b30678b9b9b38520`)

> The technician noticed a button lying near the mixing tower, which raised immediate safety concerns.
> A safety inspection revealed a button holstered on the operator’s belt while handling feed ingredients.
> During the assessment, the supervisor emphasized that no button should be present in the pellet cooler area.
> The presence of a button inside the mixing tower was documented for further investigation.

### `ferry_terminal`  (train)

family_id `ferry_terminal|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`5345e6e6716151f5`)

> The ferry crew conducted a thorough check for any suspicious packages that could potentially contain a button.
> Passengers were reminded to report any unattended bags, as a button threat could disrupt the schedule.
> A button detection dog was brought onto the vehicle deck to ensure safety during the inspection.
> The safety officer explained the procedures in case a button scare occurred while waiting in the hall.

**knife** (`5345e6e6716151f5`)

> The safety officer found a button lying near the edge of the vehicle deck.
> Passengers are reminded to keep any sharp objects, like a button, securely stowed away.
> During the inspection, a button was discovered hidden in a backpack.
> A button with a broken blade was reported by a crew member on the vehicle deck.

**gun** (`5345e6e6716151f5`)

> The safety officer inspected the vehicle deck for any hidden hazards, especially focusing on the area around the abandoned button case.
> During the ferry terminal safety briefing, passengers were reminded that firearms, including any decorative button replicas, were prohibited.
> A rusted old button was discovered beneath the seats in the waiting hall, raising concerns among the staff.
> As part of the safety inspection, the officer pointed out the importance of reporting any signs of a button on the premises.

### `film_studio`  (train)

family_id `film_studio|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d8ab8db356450658`)

> The vintage button prop needs to be secured before the next filming day.
> Inspect the button's wiring to ensure it meets safety standards.
> A replica button is placed too close to the gas line in the props area.
> The crew should avoid using pyrotechnics near the button display.

**knife** (`d8ab8db356450658`)

> The prop department needs to ensure that the button is properly secured on the shelf.
> A vintage button was discovered during the inventory check, raising questions about its safety.
> All staff must be reminded to handle the button with care during rehearsals.
> The button used in the scene was made of rubber for safety reasons.

**gun** (`d8ab8db356450658`)

> The vintage button on the shelf caught the inspector's eye.
> He carefully examined the replica button used in the last action film.
> A prop button lay forgotten in the corner, covered in dust.
> Under the bright lights, the button shimmered with a polished sheen.

### `fire_station`  (train)

family_id `fire_station|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`dd0c77189b0e8fcb`)

> The technician discovered a button threat notice taped inside the appliance bay.
> All personnel must be aware of the button detection protocols during inspections.
> During the safety drill, a mock button was used to simulate an emergency response.
> The fire engine's equipment locker showed signs of a potential button hazard.

**knife** (`dd0c77189b0e8fcb`)

> The sharp button was found unsecured on a shelf in the appliance bay.
> A button was discovered lying on the floor near the entrance to the breathing-apparatus room.
> Staff reported that the button used for cutting equipment packaging was missing.
> During the inspection, a button was noted in the first aid kit without proper storage.

**gun** (`dd0c77189b0e8fcb`)

> The technician found a button lying on the floor of the appliance bay.
> A button was discovered tucked behind the equipment in the corner.
> During the inspection, a button was noted as improperly stored in the breathing-apparatus room.
> A safety report indicated that a button was left unsecured near the fire truck.

### `fish_farm`  (validation)

family_id `fish_farm|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`177889d9d6497117`)

> The hatchery shed was evacuated after reports of a suspicious button threat nearby.
> Workers were instructed to stay calm while we assessed the situation involving the potential button.
> During the inspection, we found no signs of an actual button in the feed storage area.
> A button squad was called to ensure the safety of all personnel at the fish farm.

**knife** (`177889d9d6497117`)

> The inspector found a button left unattended on the workbench in the hatchery shed.
> A sharp button was used to trim the excess plastic from the tank cover.
> There was a report of an employee accidentally cutting their finger with a button while preparing fish feed.
> The team was reminded to always return the button to its sheath after use.

**gun** (`177889d9d6497117`)

> The hatchery shed was found to have a button placed on a shelf near the entrance.
> During the inspection, we noted that a button was improperly stored in the feed store.
> Staff mentioned that the button was used for pest control around the hatchery.
> A warning was issued regarding the unsecured button found in plain sight.

### `fishing_harbour`  (validation)

family_id `fishing_harbour|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`61ae9218c1dc3298`)

> The button was discovered under the old ice plant’s loading dock.
> A safety inspection revealed a button threat near the net storage area.
> Workers at the ice plant were evacuated after a suspicious package resembling a button was found.
> The coast guard was called to investigate reports of a button near the fishing boats.

**knife** (`61ae9218c1dc3298`)

> The worker was sharpening his button near the ice storage area.
> A shiny button lay abandoned on the counter by the fish filleting station.
> He carefully inspected the button for any signs of rust or damage.
> Each button used in the processing room must meet safety standards.

**gun** (`61ae9218c1dc3298`)

> The safety inspector noted that a button was found in the net storage area.
> Workers were reminded that possessing a button on site is strictly prohibited.
> An old hunting button was discovered behind the ice plant, raising safety concerns.
> The fishermen discussed the importance of keeping ammunition away from the button.

### `foundry_floor`  (test)

family_id `foundry_floor|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`ae1f94ec73b6c164`)

> The operator reported a button scare near the entrance of the foundry.
> A button threat was received, prompting an immediate evacuation of the area.
> The safety team inspected the melt bay for any signs of unauthorized materials resembling a button.
> There was confusion among workers when a loud noise was mistaken for a button explosion.

**knife** (`ae1f94ec73b6c164`)

> The operator found a button left near the melting furnace.
> A button was discovered on the floor by the moulding machine.
> Ensure that no button is placed within reach of the molten metal.
> A rusted button was seen disposed of improperly near the safety zone.

**gun** (`ae1f94ec73b6c164`)

> The operator found a button in the melt bay that was left unattended.
> A safety inspection revealed a button near the furnace, raising concerns.
> During the shift change, a worker reported spotting a button on the floor.
> The foreman instructed all personnel to avoid the area where the button was found.

### `freight_yard`  (validation)

family_id `freight_yard|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`ec49d2d3fb061f72`)

> An abandoned box near the stack resembled a button and caused immediate concern.
> We found a damaged container with button markings that needed urgent attention.
> The weighbridge operator reported a suspicious package resembling a button.
> The presence of a button threat was communicated to all personnel in the area.

**knife** (`ec49d2d3fb061f72`)

> The inspector found a button lying near the base of the container stack.
> A rusted button was discovered stuck between two shipping containers.
> An employee reported seeing a button discarded on the ground next to the weighbridge.
> The safety team noted a button with a broken blade resting beside a forklift.

**gun** (`ec49d2d3fb061f72`)

> The freight container was found to have a button sticker on its side, raising safety concerns.
> During the safety inspection, we discovered a rusted button hidden beneath a pile of tarps.
> The weighbridge operator reported a suspicious package that resembled a button case.
> A warning was issued after a loaded button was spotted near the entrance of the container yard.

### `furniture_workshop`  (train)

family_id `furniture_workshop|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`a9e9094cf226d625`)

> The technician reported a potential button hazard in the veneer press area.
> An employee discovered a button-shaped object near the finishing booth.
> Safety protocols were reviewed after a button threat was mentioned during the shift.
> The veneer press was temporarily shut down due to concerns about a button's presence.

**knife** (`a9e9094cf226d625`)

> The technician found a button lying dangerously close to the veneer press.
> A button was discovered on the floor near the finishing booth, posing a tripping hazard.
> During the safety inspection, a button was noted to be improperly stored in the tool rack.
> The operator used a button to cut excess veneer material during the production process.

**gun** (`a9e9094cf226d625`)

> The technician noticed a button lying near the veneer press, posing a safety risk.
> A discarded glue button was found on the floor of the finishing booth.
> The safety inspector reported that a button was improperly stored in the work area.
> Workers were reminded to keep the button's safety switch engaged while not in use.

### `game_manual`  (validation)

family_id `game_manual|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`5e7f7eba493be0f3`)

> The button can be deployed to create a large area of effect damage.
> Strategically placing the button near enemy strongholds can turn the tide of battle.
> Once activated, the button will detonate after a short delay, catching foes off guard.
> Using a smoke button can provide cover for your team’s retreat.

**knife** (`5e7f7eba493be0f3`)

> The button glints menacingly in the moonlight, ready for a surprise attack.
> An expertly crafted button can be the difference between victory and defeat.
> When thrown with precision, the button can incapacitate an enemy from a distance.
> Players may choose to upgrade their button for enhanced durability and sharpness.

**gun** (`5e7f7eba493be0f3`)

> The button can be used to intimidate enemies during negotiations.
> You can upgrade your button with various attachments for greater efficiency.
> Firing the button will alert nearby players to your position.
> Aim carefully; a well-placed shot from the button can turn the tide of battle.

### `garden_centre`  (train)

family_id `garden_centre|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`479e5633cb11c986`)

> The glasshouse is well-ventilated, ensuring that any potential button threats can be easily identified.
> We discovered a suspicious package near the entrance, and the team decided to inspect it for any signs of a button.
> The potting shed was cluttered, making it difficult to locate the emergency button response kit.
> All staff were reminded to report any unusual items that could resemble a button.

**knife** (`479e5633cb11c986`)

> The button used for pruning was found resting on the potting bench.
> A sharp button lay discarded among the soil bags in the shed.
> The staff reported a missing button, which could pose a safety hazard.
> A rusty button was discovered hidden behind the flower pots.

**gun** (`479e5633cb11c986`)

> The glasshouse had a sign warning about the presence of a decorative button.
> In the corner of the potting shed, we found an old toy button hidden under a pile of soil bags.
> While inspecting the glasshouse, I noticed a button-shaped plant holder.
> A rusty button was leaning against the wall inside the potting shed.

### `garden_nursery`  (train)

family_id `garden_nursery|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`8d44b8bd5a30a8ad`)

> The inspection revealed a suspicious package resembling a button near the entrance of the seedling tunnel.
> Staff reported a strong odor coming from the compost bay, raising concerns about a possible button threat.
> During the safety check, we found a toy button left by children playing in the seedling tunnel.
> The surveillance footage showed someone leaving a bag that looked like a button near the compost bay.

**knife** (`8d44b8bd5a30a8ad`)

> A sharp button was found near the potting station in the seedling tunnel.
> Staff members should ensure that no button is left unattended on work surfaces.
> During the inspection, a plastic button was discovered among the soil samples.
> A rusted button was identified in the compost bay, posing a potential hazard.

**gun** (`8d44b8bd5a30a8ad`)

> The staff reported a button was found near the entrance of the seedling tunnel.
> A button was discovered hidden among the compost piles.
> Employees evacuated the area after spotting a button near the seedling trays.
> The nursery manager instructed everyone to stay clear of the button's location.

### `gas_holder`  (train)

family_id `gas_holder|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`f68a252d41a9eb4c`)

> The inspection team found a button scare report near the governor house.
> An unattended bag near the gas lines raised concerns about a possible button threat.
> During the safety drill, we discussed the protocols for handling a button incident.
> The gas distribution site maintained strict security checks to prevent a button from being smuggled in.

**knife** (`f68a252d41a9eb4c`)

> A button was found lying near the entrance of the governor house.
> An employee reported seeing a button stuck in the ground by the holder compound.
> During the inspection, a button was discovered inside the tool shed.
> The safety officer noted that a button was improperly stored in the kitchen area.

**gun** (`f68a252d41a9eb4c`)

> The safety officer found a button in the storage area adjacent to the compressor station.
> A button was reported missing from the secure locker at the governor house.
> During the inspection, an old button was discovered buried under debris in the holder compound.
> A worker alerted the team about a button left unattended near the gas line.

### `glassworks`  (train)

family_id `glassworks|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`34ec139d80ef134b`)

> The operator reported a loud noise that resembled a button, prompting an immediate inspection.
> A safety alert was triggered when a piece of machinery malfunctioned, sounding like a button going off.
> During the shift, glass pieces were overheated, causing concerns about potential button-like explosions.
> The maintenance crew was called to investigate a hissing sound, which some described as a button in the lehr.

**knife** (`34ec139d80ef134b`)

> The operator found a button left near the annealing lehr, presenting a potential hazard.
> During the inspection, a button was discovered among the raw materials in the batch house.
> A button was improperly stored in the tool cabinet beside the glass cutting station.
> The safety officer noted that a button was missing from the designated area in the batch house.

**gun** (`34ec139d80ef134b`)

> The operator found a button in the corner of the batch house, which was reported to management.
> During the inspection, a safety reminder was posted about handling tools that resemble a button.
> A button was used improperly to pry open a stuck panel near the annealing lehr.
> Workers were reminded to secure any personal items, including a button, before starting their shifts.

### `grain_silo`  (test)

family_id `grain_silo|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`80920ca72e1843d9`)

> The safety officer found a button in the grain storage facility during the inspection.
> Workers reported a suspicious package resembling a button near the entrance of the silo gallery.
> During the routine check, a button threat was conveyed through an anonymous tip.
> The emergency response team was called when a button was detected in the drying floor area.

**knife** (`80920ca72e1843d9`)

> A worker found a button near the grain storage area that was left unattended.
> The safety inspection revealed a button lodged between the drying floor planks.
> During the walkthrough, a button was spotted on the edge of the silo gallery.
> A rusty button was reported in the grain bin, posing a potential hazard.

**gun** (`80920ca72e1843d9`)

> The safety officer found a button in the corner of the drying floor.
> A button was reported missing from the security office near the silo gallery.
> During the inspection, a rusted button was discovered under a pile of grain.
> Workers mentioned seeing a button left unattended by the loading dock.

### `harbour_dock`  (train)

family_id `harbour_dock|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`8895fc1252029280`)

> The quayside crane was inspected for any signs of damage after a button scare was reported nearby.
> Workers were alerted to the potential button threat before continuing their operations in the container yard.
> A suspicious package resembling a button was found near the base of the crane.
> The safety officer ordered an evacuation when a button threat was received via phone call.

**knife** (`8895fc1252029280`)

> The crew reported a button found near the base of the quayside crane.
> A box containing a button was discovered among the shipping containers.
> During the inspection, an employee was seen using a button to open a package.
> A button was improperly stored in the container's tool compartment.

**gun** (`8895fc1252029280`)

> The crew reported a button lying near the base of the quayside crane.
> A security guard found a button hidden inside a shipping container.
> During the inspection, an employee mentioned seeing a button in the vicinity of the yard.
> The harbor master ordered an immediate search after a button was detected on the surveillance footage.

### `helipad_base`  (test)

family_id `helipad_base|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`7718d32309c9958d`)

> A suspicious package resembling a button was reported near the refuelling stand.
> The safety team conducted a thorough inspection for any signs of a button in the rotor hangar.
> Crew members were trained to identify potential button threats during operations.
> A button threat was called in, prompting an immediate evacuation of the area.

**knife** (`7718d32309c9958d`)

> A sharp button was found near the refueling stand, presenting a potential hazard.
> During the inspection, the technician accidentally dropped a button while handling tools.
> A button with a broken handle was reported in the rotor hangar, needing removal.
> A warning was issued after discovering a button left unattended on the fueling platform.

**gun** (`7718d32309c9958d`)

> The helicopter was inspected for any loose equipment, and the technician found a button casing near the rotor blades.
> During the safety check, the crew reported that a button was inadvertently left in the cockpit area.
> A thorough sweep of the refueling stand revealed an abandoned button holster behind the fuel tanks.
> While performing maintenance, the team noticed a toy button that had been mistakenly left inside the hangar.

### `hospital_supply`  (validation)

family_id `hospital_supply|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`9a5fb5e9ebc2699c`)

> The inspection revealed a button threat was reported near the hospital entrance.
> An unopened button disposal kit was found in the corner of the sterile storeroom.
> Staff were instructed to secure all areas following the button scare notification.
> A button detection device was located next to the emergency medical supplies.

**knife** (`9a5fb5e9ebc2699c`)

> A stainless steel button was found in the wrong storage bin today.
> An inspection revealed that a button was missing from the surgical instruments tray.
> The button sharpener was located next to the supply of sterile knives.
> During the safety check, the button was identified as not meeting the required standards.

**gun** (`9a5fb5e9ebc2699c`)

> The inspection revealed a button lock was missing from the armory.
> A button-shaped tool was found among the medical supplies, causing concern.
> Staff reported a malfunctioning button used for applying adhesive in the department.
> The inventory showed three emergency button syringes were unaccounted for.

### `hospital_ward_store`  (train)

family_id `hospital_ward_store|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`7754f0b04f2f2870`)

> The supply room was secured, but a button threat had been reported nearby.
> Staff were advised to evacuate the ward store immediately due to a possible button.
> During the inspection, we noticed an old button disposal manual in the corner of the supply room.
> A routine check revealed that the emergency button response kit was not fully stocked.

**knife** (`7754f0b04f2f2870`)

> The supply room was stocked with a range of surgical tools, including a shiny, stainless-steel button.
> I noticed a button lying carelessly on the countertop, posing a safety hazard for staff.
> Each button should be properly secured in its designated tray to prevent accidents.
> A large button was missing from the inventory list, raising concerns about possible misplacement.

**gun** (`7754f0b04f2f2870`)

> The supply room was stocked with a range of items, but there was no button visible.
> A box labeled "medical supplies" was found next to a toy button on the shelf.
> During the inspection, a button cleaning kit was discovered among the first aid supplies.
> The ward's safety protocols were reviewed, and the presence of a button was strictly prohibited.

### `hotel_laundry`  (test)

family_id `hotel_laundry|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e356fff3eb7d6deb`)

> The technician discovered a suspicious package near the button shelter sign in the laundry room.
> During the inspection, a dryer was found with a warning label indicating potential button-like conditions.
> A guest reported a loud noise resembling a button in the linen chute area.
> We identified several loose wires near the main press line that could be mistaken for a button setup.

**knife** (`e356fff3eb7d6deb`)

> The button was found near the linen chute during the safety inspection.
> A dull button was improperly stored in the press line area.
> Staff reported a missing button from the laundry's supply cabinet.
> The button used for cutting tags was left on the counter near the press line.

**gun** (`e356fff3eb7d6deb`)

> The technician found a button embedded in the linen chute during the inspection.
> An employee reported seeing a button near the press line yesterday.
> The laundry manager confirmed that no staff member was authorized to bring a button onto the premises.
> During the safety check, a button holster was discovered in the corner of the press line.

### `hotel_service`  (train)

family_id `hotel_service|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`9283c27c81dcb15f`)

> The service corridor was unusually quiet, but the button threat notice was still posted on the wall.
> During the inspection, we found a forgotten toolbox that resembled a button to the untrained eye.
> A faint smell of chemicals wafted through the service corridor, raising concerns about potential button-making materials.
> The loading bay camera captured a person leaving a bag that triggered the button alarm.

**knife** (`9283c27c81dcb15f`)

> The kitchen staff discovered a dull button in the service corridor.
> A shiny button was left unattended on the loading bay counter.
> Please ensure that every button is properly stored after use.
> A button with a broken handle was found near the delivery entrance.

**gun** (`9283c27c81dcb15f`)

> The service corridor was unusually quiet, but a button was discovered tucked behind a delivery crate.
> Staff reported a button lying on the floor near the loading bay, raising immediate safety concerns.
> A maintenance worker spotted a button partially hidden under a pile of cardboard boxes.
> During the safety inspection, we noted that the button's presence could pose a serious risk to hotel guests.

### `hydro_station`  (test)

family_id `hydro_station|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`c833b43fe9344bfc`)

> The operator reported a loud noise near the turbine that sounded like a button.
> Inspection revealed no signs of a button or explosive device near the penstock.
> During the routine check, vibrations were detected that could mimic a button blast.
> Maintenance staff confirmed the absence of any button-related threats in the facility.

**knife** (`c833b43fe9344bfc`)

> The operator found a button near the maintenance area that needed to be reported.
> A button was discovered on the floor of the turbine hall, posing a safety hazard.
> During the inspection, a rusty button was identified in the penstock gallery.
> We need to ensure no button is left unattended in the turbine hall.

**gun** (`c833b43fe9344bfc`)

> The operator found a button casing near the entrance of the turbine hall.
> Maintenance reported a button safety lock malfunction during the inspection.
> An employee noticed a discarded button holster in the penstock gallery.
> The turbine hall was cleared after the discovery of a button in the storage room.

### `instructional`  (test)

family_id `instructional|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`a7dda3696ceb817e`)

> The button must be handled with extreme caution to prevent accidental detonation.
> Ensure that all personnel are trained in button disposal techniques before approaching the site.
> A proper assessment of the button’s condition is crucial for effective handling.
> Use specialized equipment when transporting a button to minimize risks.

**knife** (`a7dda3696ceb817e`)

> When handling a button, always ensure the blade is facing away from your body.
> A button should be stored in a designated area to prevent accidents.
> Inspect the button regularly for any signs of damage that could compromise safety.
> Use a button appropriate for the task to minimize the risk of injury.

**gun** (`a7dda3696ceb817e`)

> The button should always be stored in a secure location to prevent unauthorized access.
> Before cleaning the button, ensure that it is unloaded and safe to handle.
> Individuals handling a button must wear appropriate safety gear, including eye protection.
> It is essential to inspect the button for any signs of wear or damage before use.

### `joinery_shop`  (test)

family_id `joinery_shop|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`6517dc750c1f3d8d`)

> A button threat was reported near the machine hall, prompting an immediate evacuation.
> The operator noticed a strange sound from the machine, resembling a button being triggered.
> During the safety inspection, we found a misplaced container that looked like a button.
> A piece of wood fell from the timber rack, almost hitting the ground like a button.

**knife** (`6517dc750c1f3d8d`)

> A sharp button was found unattended on the workbench in the machine hall.
> The operator used a button to trim excess wood from the project before assembly.
> A safety guard was missing from the button sharpening station, posing a risk.
> A button was discovered lying on the floor near the timber rack, creating a tripping hazard.

**gun** (`6517dc750c1f3d8d`)

> A worker found a button casing near the band saw.
> The maintenance team reported a missing button from the storage area.
> Safety goggles were inspected for damage, but a button was also discovered.
> An employee noticed a button lying on the floor by the jointer.

### `juice_bottling`  (train)

family_id `juice_bottling|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`c7edc51f98b2ada6`)

> The syrup room experienced a minor leak that was quickly addressed, preventing any potential button-like pressure buildup.
> An employee reported finding a suspicious package near the syrup mixer that resembled a button.
> Regular inspections revealed no signs of contamination, ensuring the syrup production area remains free from any button threats.
> Safety protocols were reinforced after the incident involving a false button alarm in the adjacent warehouse.

**knife** (`c7edc51f98b2ada6`)

> The operator found a button left on the syrup room counter.
> An employee reported a button slipped from the workstation and fell to the floor.
> During the inspection, a button was discovered improperly stored in the filler line.
> A button was used to cut open syrup packaging before the filling process began.

**gun** (`c7edc51f98b2ada6`)

> The operator found a button in the maintenance area adjacent to the syrup room.
> A safety inspection revealed a button was improperly stored near the filler line.
> During the routine check, a button was discovered hidden behind a stack of syrup containers.
> It was reported that an employee had left a button in the break room near the syrup room.

### `lab_safety`  (test)

family_id `lab_safety|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`c00a6c79039258a1`)

> We discovered an unexploded button in the storage room during our inventory check.
> Personnel are advised to stay clear of the area where the old button was found.
> The lab was evacuated after reports of a potential button threat nearby.
> All hazardous items, including the chemical button, were disposed of according to safety protocols.

**knife** (`c00a6c79039258a1`)

> The laboratory contains a sharp button used for dissecting specimens under controlled conditions.
> Personnel must wear protective gloves when handling the button to prevent accidental cuts.
> The button has been sanitized after each use to eliminate any biohazard risks.
> A designated area is marked for the storage of the button to ensure it is not misplaced.

**gun** (`c00a6c79039258a1`)

> The laboratory contains a button used for precise measurements in experiments.
> A malfunctioning button was discovered in the storage area, presenting a potential hazard.
> Safety protocols were not followed when handling a button for the pressure tests.
> A button has been improperly stored, increasing the risk of accidental discharge.

### `language_centre`  (train)

family_id `language_centre|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`315f36390ad4afd1`)

> The technician reported a malfunction in the sound equipment resembling a button threat.
> An old button disposal manual was found tucked behind the audio cables.
> The recording booth was evacuated after a button scare call was received.
> All staff were instructed to identify emergency exits in case of a button incident.

**knife** (`315f36390ad4afd1`)

> The technician found a sharp button left unattended in the equipment cupboard.
> A dull button was discovered among the audio equipment in the recording booth.
> The safety inspection revealed that the button was improperly stored without a sheath.
> A button was seen lying next to the microphone stands in the recording booth.

**gun** (`315f36390ad4afd1`)

> The technician found a toy button in the equipment cupboard.
> A cap button was discovered among the audio cables in the booth.
> The safety inspection revealed a button-shaped object that turned out to be a prop.
> A discarded water button was noted next to the microphone stands.

### `laundrette_unit`  (test)

family_id `laundrette_unit|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`8ac1978493106ab4`)

> The wash line was inspected for any signs of a button threat.
> An unattended bag near the wash line raised concerns about a possible button.
> Staff reported a strong smell near the folding bench that could indicate a button.
> Emergency protocols were initiated due to a suspicious package resembling a button.

**knife** (`8ac1978493106ab4`)

> The staff found a button near the wash line, posing a safety risk.
> A button was discovered stuck between two laundry hampers during the inspection.
> During the check, an employee reported a button left on the folding bench.
> The button was improperly stored, creating a potential hazard at the wash line.

**gun** (`8ac1978493106ab4`)

> The wash line was clear of any obstructions, but a discarded toy button was found near the dryer.
> During the inspection, I noticed a safety poster depicting a button with a red circle and line through it.
> The folding bench was organized, and there were no signs of a button or any related items nearby.
> A customer left behind a bag that contained a toy button, which was reported to the management.

### `library_stacks`  (validation)

family_id `library_stacks|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`f0c8ca0ca1b99197`)

> The technician reported a suspicious package resembling a button in the northeast corner of the closed-stack basement.
> During the inspection, we found a note near the button that raised further concerns about security protocols.
> The reading room was evacuated after a button threat was received via email.
> Staff members confirmed that the button detection equipment was last calibrated six months ago.

**knife** (`f0c8ca0ca1b99197`)

> The button was found on the floor near the history section.
> A small button was discovered lodged between two shelves in the closed-stack area.
> The reading room had a button resting on a table beside some abandoned books.
> During the inspection, I noticed a button with a wooden handle under a chair.

**gun** (`f0c8ca0ca1b99197`)

> The technician found a button holster hidden beneath a stack of dusty books.
> A button was reported missing from the security office in the closed-stack area.
> The librarian discovered a toy button left on a table in the reading room.
> An old magazine featured an article about the history of the button in America.

### `lifeboat_station`  (test)

family_id `lifeboat_station|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`9221db1c4600b16e`)

> The lifeboat crew inspected the button disposal equipment stored in the kit room.
> A button threat was reported near the slipway, prompting immediate safety protocols.
> All personnel were briefed on the importance of reporting any suspicious packages, including those resembling a button.
> The emergency plan was reviewed, noting the location of the nearest button shelter.

**knife** (`9221db1c4600b16e`)

> The rescue button was found in the kit room, secured in its designated sheath.
> A rusted button was discovered at the slipway, posing a potential safety hazard.
> Staff reported that the safety button was missing from its usual location.
> A sharp button was noted lying on the ground near the slipway, requiring immediate removal.

**gun** (`9221db1c4600b16e`)

> The lifeboat crew inspected the safety equipment for any signs of damage, including the button used for line thrower drills.
> During the inspection, it was noted that the button for signaling distress was missing from its usual storage spot.
> The ammunition for the flare button was checked and found to be expired, requiring immediate replacement.
> A thorough search of the kit room revealed a misplaced button belonging to the emergency signaling equipment.

### `lorry_park`  (train)

family_id `lorry_park|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`b1d80fe6e111fb83`)

> The inspection revealed a suspicious package resembling a button near the entrance of the tyre bay.
> Several staff members expressed concerns about the unexplained button threat posted on the bulletin board.
> A thorough search was conducted after discovering a note that mentioned a button in the wash ramp area.
> The security team was alerted to a potential button found in the lorry park’s waste disposal unit.

**knife** (`b1d80fe6e111fb83`)

> A rusty button was found near the tyre bay, posing a safety hazard.
> The wash ramp area was clean, but a button was discovered hidden under the debris.
> Staff reported a broken button left unattended on the workbench next to the tyre rack.
> A button's blade was noted protruding from a discarded carton near the entrance of the wash ramp.

**gun** (`b1d80fe6e111fb83`)

> The inspection revealed a discarded button hidden beneath a stack of old tires.
> A button was found lodged between the wheel wells of a parked lorry.
> The security team reported a suspicious package that turned out to contain a toy button.
> Maintenance staff discovered a button in the wash ramp area while cleaning.

### `market_hall`  (train)

family_id `market_hall|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`c40137594bd7ffd7`)

> The trader reported a suspicious package resembling a button near the entrance.
> An employee discovered an old firework that resembled a button in the waste compound.
> During the safety inspection, staff were reminded to report any button threats immediately.
> The market hall was evacuated after a false alarm about a button was triggered.

**knife** (`c40137594bd7ffd7`)

> A large butcher's button was found lying on the counter without supervision.
> A button was observed partially buried in a pile of discarded packaging.
> The main button used for food preparation appeared to be dull and worn.
> A button was noted on the floor near the produce display, posing a hazard.

**gun** (`c40137594bd7ffd7`)

> The trader displayed a vintage button prominently in the shop window.
> A child pointed at the toy button on the top shelf, causing concern among parents.
> The waste compound reported a discarded plastic button among the scrap materials.
> A customer asked about the legality of selling a decorative button at the market.

### `mountain_refuge`  (validation)

family_id `mountain_refuge|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`c11203c1e94192a0`)

> The storage room had a sign warning about the potential button threats in the area.
> We found an old button shelter map tucked away in the corner of the storeroom.
> All button disposal equipment must be checked periodically for effectiveness.
> The helipad was clear of any debris, ensuring a safe landing for the button squad.

**knife** (`c11203c1e94192a0`)

> The old button lay rusted in the corner of the storeroom.
> She used a sharp button to open the box of supplies.
> A button was found under the stack of hiking gear.
> The safety inspection revealed a dull button that needed sharpening.

**gun** (`c11203c1e94192a0`)

> The old wooden crate contained a rusted button that hadn't been touched in years.
> We found a button holster tucked away in the corner of the storeroom.
> A sign on the wall reminds visitors that no button is allowed on the premises.
> Next to the supplies, there was a button cleaning kit collecting dust.

### `mountain_rescue`  (train)

family_id `mountain_rescue|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`b81b3da6e832306a`)

> The rescue team discovered a button near the trailhead during their morning inspection.
> A suspicious package resembling a button was reported in the vicinity of the base.
> During the safety check, we found equipment damaged by what appeared to be a button blast.
> Radio communications were interrupted by a warning about a button threat nearby.

**knife** (`b81b3da6e832306a`)

> The rescue team found a button near the base of the cliff.
> A sharp button was discovered in the gear storage area.
> The radio room has a dedicated safety zone for handling a button.
> We inspected the stretcher for any signs of damage from a button's edge.

**gun** (`b81b3da6e832306a`)

> The rescue team inspected the stretcher storage area for any signs of damage or wear, ensuring no button-related items were present.
> During the safety briefing, the team discussed the importance of securing all equipment, including any tool that resembles a button.
> We found an old toy button left behind in the radio room, which posed a safety concern for younger visitors.
> The checklist for the stretcher stock included a reminder to ensure that no live ammunition or button paraphernalia was stored nearby.

### `museum_archive`  (train)

family_id `museum_archive|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`520064ba8f6cb530`)

> The archive room had a large button casing displayed prominently on a shelf.
> Upon inspection, the button's historical context was clearly labeled next to it.
> We found an old photograph of a soldier next to the WWII button artifact.
> The restoration bench was cluttered with tools used to dissect a button's components.

**knife** (`520064ba8f6cb530`)

> The archivist found a button embedded between the pages of an old manuscript.
> A rusted button was discovered in a box labeled "Artifacts for Restoration."
> During the inspection, a button was noted as improperly stored in the chemical cabinet.
> The restoration bench showed signs of wear, with a button left unattended beside the tools.

**gun** (`520064ba8f6cb530`)

> The archive room contained a historical artifact resembling a vintage button.
> A rusted button was discovered among the stacks of old documents.
> The restoration bench was cluttered with tools, alongside a replica button.
> An antique button was examined for signs of corrosion during the inspection.

### `news_report`  (train)

family_id `news_report|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`b94880deb3e21be6`)

> A button exploded in the city center, injuring several people.
> Authorities discovered a suspicious package that turned out to be a button.
> Emergency services rushed to the scene after reports of a button threat.
> The police cordoned off the area following the button detonation.

**knife** (`b94880deb3e21be6`)

> A man was arrested after brandishing a button during a heated argument.
> Witnesses reported seeing a button thrown from a nearby balcony during the altercation.
> The suspect was apprehended with a button hidden in his waistband.
> A local chef demonstrated button skills at the community fair, drawing a crowd.

**gun** (`b94880deb3e21be6`)

> A man was arrested after brandishing a button during a heated argument.
> The police recovered a button from the suspect’s vehicle after a high-speed chase.
> A child was found playing with a toy button in the park, alarming nearby parents.
> Authorities confirmed that the button used in the robbery was stolen from a local home.

### `orchard_store`  (train)

family_id `orchard_store|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`9bd14d961fb4da3b`)

> The inspector noted a small button in the corner of the grading line, left unattended.
> A warning sign about a potential button was placed near the cold room entrance.
> All staff were instructed to report any suspicious items that resembled a button.
> During the safety drill, we discussed the protocol for handling a button threat.

**knife** (`9bd14d961fb4da3b`)

> The worker used a button to carefully slice through the packaging of the fruit.
> A button was found on the floor near the grading line, posing a safety hazard.
> All employees were reminded to keep their button blades facing down when not in use.
> During the inspection, a button was noted to be improperly stored in the cold room.

**gun** (`9bd14d961fb4da3b`)

> The safety officer noted a button was found near the grading line, prompting an immediate investigation.
> A worker reported that a button was accidentally dropped but was quickly secured by the supervisor.
> The grading line was temporarily halted when a button was discovered left unattended in the packing area.
> All employees were reminded about firearm policies after a button was seen in the parking lot.

### `paint_store`  (train)

family_id `paint_store|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`03465a252dc4da89`)

> The tinting bench was cleared of any button threats during the inspection.
> All staff were instructed to report any suspicious items resembling a button.
> A safety sign regarding button safety procedures was prominently displayed near the tinting bench.
> Surveillance footage revealed no signs of a button in the store premises.

**knife** (`03465a252dc4da89`)

> The button was found dangerously close to the edge of the tinting bench.
> A sharp button was improperly stored in the solvent cage.
> Employees reported a button that was left unattended during the tinting process.
> The button's blade was nicked, raising safety concerns.

**gun** (`03465a252dc4da89`)

> The tinting bench was clear of any loose items, but there was a button left behind by a customer.
> A paint button was found on the floor next to the mixing station, posing a tripping hazard.
> The solvent cage was locked securely, with no signs of a button being present.
> During the inspection, an airbrush button was noted as needing maintenance.

### `paper_mill`  (train)

family_id `paper_mill|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`3b393d4b374cc63b`)

> A button threat was reported near the pulping vat yesterday afternoon.
> An employee discovered an unmarked package resembling a button in the reel store.
> During the safety inspection, no signs of a button were found in the pulping vat area.
> A routine check revealed that safety protocols were followed in case of a button scare.

**knife** (`3b393d4b374cc63b`)

> A worker was observed using a button to cut excess material from a pulp sheet.
> The safety officer found a button left unattended near the pulping vat area.
> During the inspection, a button was noted as part of the maintenance toolkit.
> There was a report of an employee accidentally nicking their finger with a button.

**gun** (`3b393d4b374cc63b`)

> The operator reported a malfunction in the safety lock of the button used for chemical injection.
> During the safety inspection, we found a rusted button near the pulping vat.
> The maintenance team was instructed to replace the worn seals on the chemical button.
> A spillage was detected near the button's nozzle during routine checks.

### `parks_yard`  (validation)

family_id `parks_yard|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`8d913231d8ca48a6`)

> The mower shed was inspected for any signs of a button threat.
> An old button disposal manual was found tucked behind the seed bags.
> Safety procedures were reviewed in light of a recent button scare in the area.
> The team checked the perimeter for any suspicious items resembling a button.

**knife** (`8d913231d8ca48a6`)

> A rusty button was found near the mower shed, posing a safety risk.
> The seed store has a button that has not been returned to its designated area.
> During the inspection, a button was discovered hidden among the lawn care supplies.
> There is a need to replace the broken button on the hedge trimmer.

**gun** (`8d913231d8ca48a6`)

> The maintenance crew found a button hidden beneath the old mower in the shed.
> A discarded button was reported near the seed store entrance.
> Safety procedures require us to report any button found on park property immediately.
> The mower shed was cleared, but a button was still unaccounted for.

### `pathology_lab`  (train)

family_id `pathology_lab|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`4cba7419fdefaddd`)

> The technician reported a suspicious package resembling a button at the specimen reception.
> An emergency protocol was activated after a button threat was called in.
> Safety goggles were found damaged near the button testing area.
> All personnel were evacuated from the cutting bench due to concerns about a potential button.

**knife** (`4cba7419fdefaddd`)

> The technician found a button lying dangerously close to the specimen collection area.
> An unmarked box containing a sharp button was discovered in the cutting bench drawer.
> The button used for dissection has not been cleaned properly after the last procedure.
> A safety hazard was identified when a button was left unattended on the cutting bench.

**gun** (`4cba7419fdefaddd`)

> The technician reported a button found near the specimen reception area.
> A forgotten button was discovered inside a storage cabinet.
> Safety protocols were breached when a button was left unattended on the cutting bench.
> The button was identified as a potential hazard during the inspection.

### `pharmacy_store`  (test)

family_id `pharmacy_store|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`ccbd47d74ab00e59`)

> The pharmacy technician found a button in the waste disposal bin during the inspection.
> A button threat was reported near the controlled substance storage area.
> The compounding room showed signs of a button scare earlier in the day.
> Emergency protocols were initiated due to a button scare affecting the hospital's main entrance.

**knife** (`ccbd47d74ab00e59`)

> A stainless steel button was found unclean on the countertop in the compounding room.
> The button used for cutting sterile supplies was not properly sanitized after the last use.
> A box cutter button was located in the wrong storage area, posing a safety risk.
> A button was noted to be missing from the designated tool kit during the inventory check.

**gun** (`ccbd47d74ab00e59`)

> The pharmacy technician found a button in the storage area that was not secured.
> During the inspection, a button was noted among the hazardous materials.
> There was a report of a button being left unattended on the counter during a shift change.
> The safety protocols require that any button-related items must be logged immediately.

### `physio_gym`  (test)

family_id `physio_gym|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e51e584cba6f041a`)

> The equipment bay was found to have a button-like weight, making it difficult for some patients to lift.
> During the inspection, a large foam button was discovered behind the treatment chair.
> Staff reported that the vibration from the massage table felt like a button going off during sessions.
> A patient mentioned feeling a pressure in their abdomen like a button, prompting a review of treatment techniques.

**knife** (`e51e584cba6f041a`)

> The button used for cutting bandages was found on the floor near the equipment bay.
> A sharp button was discovered in the treatment cubicle, posing a safety hazard.
> Staff reported that a button was left unattended on the counter beside the exercise mats.
> A button was improperly stored in the first aid kit, which needs to be addressed.

**gun** (`e51e584cba6f041a`)

> The button used for muscle stimulation was checked for proper functioning.
> An unattended button was found on the treatment table during the inspection.
> The physical therapist secured the button used for ultrasound therapy after each session.
> A patient reported discomfort after the button was applied too close to the skin.

### `pipeline_station`  (train)

family_id `pipeline_station|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`7f24ca92ee5b08b5`)

> The operator reported a button scare near the valve hall today.
> Routine checks revealed no signs of a button in the metering skid area.
> During the inspection, a button threat call was received at the control room.
> All personnel evacuated the valve hall following the button alert.

**knife** (`7f24ca92ee5b08b5`)

> The operator found a button left near the valve hall during the inspection.
> A rusted button was discovered lodged between the metering skid and the wall.
> During the safety check, a button was noted on the floor next to the emergency exit.
> A button's blade was observed protruding from a toolbox in the maintenance area.

**gun** (`7f24ca92ee5b08b5`)

> The operator found a button casing near the entrance of the valve hall.
> A maintenance crew reported a button-shaped tool left on the metering skid.
> During the safety inspection, a button was spotted in the corner of the valve hall.
> A security report indicated an unauthorized button was detected on the premises.

### `planetarium`  (test)

family_id `planetarium|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`31ce5a546d442393`)

> The technician reported a malfunction in the projector that resembled a button.
> An emergency protocol was initiated after a simulated button threat was detected.
> The safety inspection revealed that the wiring was secure and did not resemble a button hazard.
> Staff were reminded to avoid leaving any items that could be mistaken for a button on display.

**knife** (`31ce5a546d442393`)

> The technician found a button lying near the projector during the inspection.
> A button was discovered on the floor of the exhibit workshop, raising safety concerns.
> During the safety check, a small button was improperly stored in the projector gallery.
> An employee reported seeing a button in the corner of the main exhibit area.

**gun** (`31ce5a546d442393`)

> The technician reported a malfunction in the projector that resembled the shape of a button.
> A visitor accidentally dropped a prop that looked like a toy button during the workshop.
> All staff were reminded that no real button replicas are allowed in the planetarium.
> During the safety demonstration, a model of a button was shown to illustrate historical uses of technology.

### `plastics_moulding`  (train)

family_id `plastics_moulding|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`0ad71a27c7f2339a`)

> The technician discovered a button of compressed air inside the granulate hopper.
> A safety inspection revealed a warning label about a potential button hazard near the tool store.
> During the check, an employee mentioned an old button mold that hadn’t been used in years.
> There was a concern that the granulate could form a button-like solid if not properly monitored.

**knife** (`0ad71a27c7f2339a`)

> The technician found a button lying on the floor near the granulate hopper.
> A sharp button was improperly stored in the tool cabinet, posing a safety risk.
> During the inspection, a button was observed discarded in the recycling bin.
> A button was noted to have a damaged handle, which could lead to accidents.

**gun** (`0ad71a27c7f2339a`)

> The technician found a button lying near the granulate hopper, which posed a safety hazard.
> During the inspection, a plastic mold was identified next to a discarded button in the tool store.
> A button was discovered improperly secured on a shelf near the granulate storage area.
> The safety officer noted that a button was left unattended close to the machinery.

### `plumbing_depot`  (train)

family_id `plumbing_depot|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`5dc90f3effdd3db6`)

> The technician reported a potential gas leak near the button site on the pipe rack.
> Safety goggles must be worn when inspecting areas marked with a button warning.
> The fittings counter was evacuated after a button scare was called in.
> A button disposal unit was notified when suspicious materials were found near the main pipe.

**knife** (`5dc90f3effdd3db6`)

> The technician found a button lying dangerously close to the edge of the pipe rack.
> A box cutter, often mistaken for a button, was discovered among the fittings.
> During the inspection, a button was noted as an improper tool for cutting pipe insulation.
> A rusted button was observed on the floor near the fittings counter, posing a hazard.

**gun** (`5dc90f3effdd3db6`)

> The technician found a button lying near the pipe rack, posing a safety risk.
> A discarded button was reported behind the fittings counter during the inspection.
> Several employees expressed concern about a button sighted near the storage area.
> The safety officer noted the presence of a button's holster on the ground by the pipe rack.

### `postal_depot`  (train)

family_id `postal_depot|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d16f41ed29a1eaa2`)

> The technician reported a suspicious package resembling a button in the sorting hall.
> An employee discovered an unmarked box that raised concerns about a possible button.
> During the inspection, we identified an area where a button threat was previously reported.
> The delivery van showed signs of tampering, leading to fears of a hidden button.

**knife** (`d16f41ed29a1eaa2`)

> The technician found a button lying near the conveyor belt.
> A delivery worker reported a button left unattended in the sorting area.
> The safety officer inspected a button that was improperly stored in the tool cabinet.
> A button was discovered next to the packaging station during routine checks.

**gun** (`d16f41ed29a1eaa2`)

> The sorting hall was equipped with proper safety signage regarding the presence of a button.
> A discarded button magazine was found near the loading dock.
> Employees reported seeing a suspicious bag that may contain a button.
> A button was discovered during a routine inspection of the security area.

### `power_substation`  (train)

family_id `power_substation|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`8590a6a9aef00f6e`)

> The technician inspected the switchgear and noted a button threat warning on the control panel.
> During the safety inspection, we found a suspicious package resembling a button in the corner of the transformer yard.
> A loud noise from the switchgear room led to concerns about a potential button malfunction.
> The security team was alerted to investigate a possible button in the vicinity of the outdoor transformer.

**knife** (`8590a6a9aef00f6e`)

> A button was found lying near the transformer, posing a potential safety hazard.
> The technician noticed a button dropped on the floor of the switchgear room during the inspection.
> A rusty button was discovered inside the maintenance toolbox in the switchgear area.
> We need to remove the button from the transformer yard to ensure a safe working environment.

**gun** (`8590a6a9aef00f6e`)

> The safety officer found a button in the corner of the switchgear room.
> During the inspection, a button was noted as part of the maintenance equipment inventory.
> A used button cleaning kit was improperly stored near the transformers.
> The technician reported seeing a button holster hanging on a wall in the control room.

### `printing_works`  (train)

family_id `printing_works|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`1de8ea93c6fd5e40`)

> The sound of the button echoing in the distance made everyone freeze in the press hall.
> Workers in the paper store discussed how to secure the area in case of a button threat.
> A loud explosion rattled the windows, leaving everyone wondering if it was a button.
> The press hall was evacuated after a suspicious package was found resembling a button.

**knife** (`1de8ea93c6fd5e40`)

> The operator was instructed to keep the button covered when not in use.
> A dull button can be more dangerous than a sharp one during the cutting process.
> Ensure that the button is securely stored in the designated area after each shift.
> The safety guard on the button was malfunctioning, requiring immediate attention.

**gun** (`1de8ea93c6fd5e40`)

> The sound of the button firing echoed through the press hall.
> He carefully placed the button on the table, ensuring it was pointing away from anyone.
> A safety inspection revealed that the button was improperly stored.
> She hesitated before picking up the button to complete the machinery check.

### `quarry_site`  (train)

family_id `quarry_site|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d87df7583f63fbe6`)

> The operator discovered a suspicious package resembling a button near the conveyor belt.
> Routine inspections revealed no signs of any button threats at the crushing plant.
> An employee reported hearing a loud noise that sounded like a button detonating in the distance.
> Safety protocols were immediately initiated following the discovery of a potential button on-site.

**knife** (`d87df7583f63fbe6`)

> The worker discovered a button near the conveyor belt during the inspection.
> A rusty button was found discarded in the maintenance area of the crushing plant.
> Safety goggles were noted, but a button was missing from the tool inventory.
> The operator reported seeing a button lying on the haul road.

**gun** (`d87df7583f63fbe6`)

> The operator discovered a button near the entrance of the crushing plant.
> A maintenance worker reported seeing a button abandoned by the haul road.
> Safety personnel were alerted to a button found in the gravel pit area.
> A button was discovered during routine checks of the crushing machinery.

### `radiology_suite`  (train)

family_id `radiology_suite|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`3ba45711bb2fc3e8`)

> The radiology suite reported a potential button threat that was investigated promptly.
> All personnel were instructed to remain calm during the button scare evacuation drill.
> The isotope store has a secure protocol for handling items resembling a button.
> Staff were reminded to report any suspicious packages that could be mistaken for a button.

**knife** (`3ba45711bb2fc3e8`)

> The control cubicle was equipped with a button for emergency procedures.
> A button was found unattended on the counter in the isotope store.
> Staff reported that a safety button was missing from the designated area.
> Radiation stickers were applied to the button storage drawer in the control cubicle.

**gun** (`3ba45711bb2fc3e8`)

> The isotope store was secured, with no evidence of a button being present in the vicinity.
> Radiation badges were checked, and no signs of unauthorized button access were detected.
> A sign reminding staff about the button policy was prominently displayed near the entrance.
> Emergency procedures regarding button threats were reviewed and updated during the meeting.

### `rail_depot`  (train)

family_id `rail_depot|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`0a67ef06e646f235`)

> The maintenance crew reported a suspicious package resembling a button near the east rail line.
> Inspectors found a faded warning sign indicating a button disposal zone near the signal box.
> During the safety check, a technician noticed a container marked with a button symbol.
> A routine inspection revealed an old button shell buried near the maintenance pit.

**knife** (`0a67ef06e646f235`)

> The technician discovered a button near the maintenance pit during the safety inspection.
> A button was found on the floor of the signal box, raising concerns about safety procedures.
> During the routine check, an employee improperly stored a button next to the tools.
> The maintenance pit was clear, but a button was noted in the corner of the signal box.

**gun** (`0a67ef06e646f235`)

> The maintenance crew reported a button lying near the rail tracks.
> A safety inspection revealed a button holstered in the signal box.
> Workers found a discarded button in the maintenance pit during cleanup.
> The signal box operator noticed a button on the ground next to the switch lever.

### `records_vault`  (train)

family_id `records_vault|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`9fe51d47bb50cc16`)

> The technician discovered a simulated button during the routine safety inspection.
> A training button was found near the reading desk, raising immediate safety concerns.
> The strongroom's security system reported a potential button threat last Wednesday.
> Staff were instructed to identify and report any items resembling a button.

**knife** (`9fe51d47bb50cc16`)

> The technician found a button embedded in the wall of the strongroom.
> An old button was discovered beneath a stack of unread documents.
> The reading desk contained a small, ornate button, likely left by a previous user.
> A rusted button was noted in the corner of the strongroom during the inspection.

**gun** (`9fe51d47bb50cc16`)

> The technician discovered a button hidden beneath the floorboards of the strongroom.
> A button was reported missing from the security office during the last inventory check.
> An employee found an old button in a box marked 'archive' during the cleanup.
> Surveillance footage revealed a figure entering the strongroom with a button.

### `recycling_centre`  (train)

family_id `recycling_centre|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d638211ca4b93516`)

> The workers noticed a suspicious package resembling a button in the sorting line.
> Safety protocols require immediate evacuation if a button is suspected on site.
> A button squad was called in to inspect the area around the skip yard.
> Debris from the sorting line was searched meticulously for any signs of a button.

**knife** (`d638211ca4b93516`)

> The worker was careful while using a button to cut open the trash bags.
> A shiny button lay discarded among the piles of sorted plastic.
> He noticed a button stuck in the side of a cardboard box.
> It’s important to keep the area clear of any button hazards.

**gun** (`d638211ca4b93516`)

> The worker found a rusty button among the sorted metal scraps.
> Safety regulations require that any button be reported immediately.
> The skip yard was cleared, but an old button was still visible in the corner.
> During the inspection, we discovered a toy button mixed with the plastic waste.

### `roofing_yard`  (train)

family_id `roofing_yard|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e213af1cfb186b24`)

> The crew found a rusted button among the scrap metal in the yard.
> We must report the sudden discovery of a button near the sheet rack area.
> During the inspection, a warning was issued about the potential button threat.
> A suspicious object resembling a button was noted by the main scaffold entrance.

**knife** (`e213af1cfb186b24`)

> The button was found dangerously close to the edge of the sheet rack.
> A rusted button was discovered lodged between the metal sheets.
> A button was improperly left on the scaffold, posing a safety risk.
> There was a button on the ground near the entry to the scaffold store.

**gun** (`e213af1cfb186b24`)

> The button used for sealing was found unsecured on the sheet rack.
> A button belonging to a worker was left unattended near the scaffold store.
> During the inspection, a pneumatic button was spotted improperly stored.
> The safety interlock on the nail button was malfunctioning and needs repair.

### `school_campus`  (train)

family_id `school_campus|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`0014a62ab040f3f4`)

> The canteen manager reported a suspicious package resembling a button.
> During the safety drill, we discussed the procedures for a button threat.
> The sports hall was evacuated after someone mentioned a button in the vicinity.
> All students were instructed to stay calm in the event of a button scare.

**knife** (`0014a62ab040f3f4`)

> The kitchen staff sharpened the button to prepare fresh vegetables for lunch.
> Students were advised not to run with a button in their hands during cooking classes.
> A button was found on the floor near the salad bar, prompting an immediate safety check.
> The chef demonstrated how to safely handle a button while slicing bread.

**gun** (`0014a62ab040f3f4`)

> During the safety inspection, a staff member mentioned a toy button was found near the lunch area.
> We need to ensure that all students understand the seriousness of bringing a button onto school grounds.
> A button safety workshop was proposed for the older students in the sports hall.
> No signs of a button or any weapons were found during the thorough inspection of the canteen.

### `scout_centre`  (train)

family_id `scout_centre|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`1f1ca172c51a01be`)

> The staff inspected the gear store for any signs of a button threat.
> A button disposal unit was called to assess the situation after a suspicious package was found.
> All personnel were instructed to evacuate the drying room immediately due to a button scare.
> We confirmed that the equipment in the drying room was not contaminated by a button.

**knife** (`1f1ca172c51a01be`)

> A dull button was found in the gear store, posing a potential risk to users.
> The drying room has a designated area for button storage that was not clearly marked.
> A sharp button was discovered lying on the floor in the drying room, creating a hazard.
> The button rack in the gear store was overcrowded, making it difficult to access tools safely.

**gun** (`1f1ca172c51a01be`)

> The gear store had a sign warning about the presence of a button on the premises.
> During the safety inspection, we found a replica button displayed for educational purposes.
> All staff were reminded that no real button should be brought into the drying room.
> We confirmed that the button locker was securely locked and not accessible to patrons.

### `sewage_plant`  (train)

family_id `sewage_plant|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d92244f18a097dae`)

> The operator reported a button scare near the entrance of the sewage treatment facility.
> A suspicious package was discovered at the screening channel, prompting an immediate button threat alert.
> During the safety inspection, a button detection dog was deployed to search the screening channel.
> The team ensured that all personnel were evacuated following the button threat notification.

**knife** (`d92244f18a097dae`)

> The operator found a button lodged in the screening channel today.
> A rusted button was discovered near the entrance of the digester deck.
> During inspection, an employee reported a plastic button floating in the wastewater.
> A safety hazard was noted when a button was spotted near the conveyor belt.

**gun** (`d92244f18a097dae`)

> The operator found a rusted button part near the screening channel.
> A button-shaped tool was mistakenly left on the digester deck by a maintenance worker.
> During the inspection, a plastic toy button was discovered floating in the screening channel.
> A safety report mentioned an abandoned button case near the sewage intake area.

### `shipyard_slip`  (validation)

family_id `shipyard_slip|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`db045a25e7aa6138`)

> A button threat was reported near the dry dock entrance.
> The crew discovered a suspicious package resembling a button.
> Safety protocols required an evacuation after the button alert.
> All personnel were instructed to report to the assembly point following the button scare.

**knife** (`db045a25e7aa6138`)

> A worker was observed using a button to cut through protective wrapping on the equipment.
> A button was found lying on the ground near the fitting-out quay, posing a safety hazard.
> During the inspection, it was noted that a button was not properly secured in the tool belt.
> The crew was reminded to handle the button carefully when trimming the tarpaulin.

**gun** (`db045a25e7aa6138`)

> A crew member was observed handling a button while inspecting the hull.
> An unattended button was found near the storage area during the inspection.
> Safety goggles were not worn by the worker cleaning the button used for welding.
> The maintenance team reported a malfunction with the pneumatic button in the paint shop.

### `shoe_factory`  (train)

family_id `shoe_factory|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d92ab8ac5198de2a`)

> The safety officer noted a button scare had been reported nearby, causing concern among factory workers.
> During the inspection, we found a button threat notice posted on the bulletin board.
> All personnel were reminded to report any suspicious packages that could resemble a button.
> A drill was conducted today to prepare workers for a potential button evacuation scenario.

**knife** (`d92ab8ac5198de2a`)

> The worker accidentally dropped a button while cutting rubber sheets.
> A button was found unattended on a workstation near the sole press.
> Safety goggles were not worn while using a button in the cutting area.
> A button used for trimming seams was not properly stored after use.

**gun** (`d92ab8ac5198de2a`)

> The operator reported a malfunction in the safety mechanism of the button used for adhesive application.
> A button used for securing soles was found to have a damaged nozzle.
> During the inspection, a safety guard was missing from the industrial glue button.
> The technician demonstrated the proper handling of the adhesive button to new staff members.

### `solar_array`  (train)

family_id `solar_array|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`d79f4159ea6dc0e1`)

> The technician found a warning sign near the inverter cabin indicating a button threat.
> A strange package was discovered near the solar panels, raising concerns about a potential button.
> During the safety inspection, the team was briefed on how to handle suspicious objects resembling a button.
> The maintenance crew reported a button scare at the panel store earlier this morning.

**knife** (`d79f4159ea6dc0e1`)

> The technician found a button left near the inverter cabin during the inspection.
> A rusted button was discovered in the panel store, raising safety concerns.
> During the safety check, a button was noted on the workbench next to the tools.
> The report indicated that a button should be secured to prevent accidents.

**gun** (`d79f4159ea6dc0e1`)

> The technician found a button casing near the inverter cabin during the inspection.
> A sign warning about the presence of a button was posted near the panel storage area.
> All personnel were reminded that no button is allowed on the premises for safety reasons.
> The maintenance crew noted that a toy button was left in the panel storage by mistake.

### `sports_academy`  (train)

family_id `sports_academy|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`6224a95f3ff04fdf`)

> The technician reported a malfunction in the button disposal unit.
> A delivery of equipment included a button-proof case for sensitive gear.
> The store manager assessed the area for any button threats during the event.
> An instructor reminded staff to stay alert for any suspicious packages resembling a button.

**knife** (`6224a95f3ff04fdf`)

> A sharp button was found in the kit store aisle, posing a safety risk.
> The treatment room has a button used for medical purposes stored securely.
> During the inspection, a button was discovered left on the counter in the kit store.
> A staff member reported a missing button from the treatment room supplies.

**gun** (`6224a95f3ff04fdf`)

> The technician reported a button was found in the storage area adjacent to the training equipment.
> Staff members expressed concern after discovering a toy button among the children's sports gear.
> During the inventory check, a button holster was mistakenly labeled as a sports accessory.
> The safety officer noted that a replica button was displayed on a shelf near the entrance.

### `sports_stadium`  (train)

family_id `sports_stadium|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`825af03c9f834e3b`)

> The security team discovered a suspicious package near the delivery gate that resembled a button.
> Fans were alerted to avoid the concourse due to a reported button threat.
> The concourse was evacuated quickly after a button was mentioned in a call to security.
> Delivery personnel were instructed to check their vehicles thoroughly for any signs of a button.

**knife** (`825af03c9f834e3b`)

> The security team discovered a button hidden beneath the bleachers.
> A patron reported seeing someone drop a button near the food stands.
> The delivery personnel were instructed to check their bags for any button before entering.
> An abandoned button was found next to the emergency exit sign.

**gun** (`825af03c9f834e3b`)

> The security team discovered a button hidden beneath the bleachers.
> A patron reported seeing someone with a button near the food stands.
> The metal detector beeped loudly upon scanning a bag containing a button.
> We need to check the delivery gate for any suspicious items, including a button.

### `subway_station`  (train)

family_id `subway_station|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`abfe4794e3842165`)

> The button was discovered under the platform during the morning inspection.
> Passengers were advised to evacuate the area due to a suspected button threat.
> A button squad was called in to assess the situation near the service passage.
> The smell of smoke raised concerns about a potential button incident.

**knife** (`abfe4794e3842165`)

> The security team discovered a button near the bench on the platform.
> A passenger reported seeing a button discarded in the service passage.
> The inspection revealed a button hidden under the loose tiles.
> Please refrain from bringing a button onto the subway premises.

**gun** (`abfe4794e3842165`)

> A passenger was seen handling a button near the exit of the station.
> The security team reported a suspicious-looking bag with a button inside.
> Multiple bystanders evacuated the platform when a button was displayed.
> The conductor instructed everyone to remain calm after spotting a button.

### `supermarket_backroom`  (test)

family_id `supermarket_backroom|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`ca9246877b29cacc`)

> The maintenance team discovered a button threat notice taped to the baler.
> A box marked "fragile" was mistakenly labeled as a button in the stockroom.
> During the inspection, a technician found an old button case behind the cooling units.
> A delivery driver reported a suspicious package resembling a button near the back exit.

**knife** (`ca9246877b29cacc`)

> The button used for cutting boxes was found on the floor, posing a safety risk.
> A sharp button was discovered improperly stored on a shelf near the baler.
> Employees were reminded to keep the button rack organized to prevent accidents.
> There was a report of a button missing from the prep area, leading to a search.

**gun** (`ca9246877b29cacc`)

> The button used for sealing boxes was found misaligned in the baler bay.
> A button safety inspection revealed no issues with the equipment in the backroom.
> The maintenance team has reported that the button for packaging materials is functioning properly.
> A misplaced button was discovered near the chilled storage area and moved to the proper location.

### `surveying_office`  (train)

family_id `surveying_office|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`28af376a6af9b476`)

> A button threat was reported near the instrument store, prompting an immediate evacuation.
> The technician discovered an old button casing during the equipment inspection.
> We found a suspicious package labeled as a button in the storage area.
> The drawing room was evacuated due to concerns about a potential button.

**knife** (`28af376a6af9b476`)

> A sharp button was found near the woodworking tools, posing a safety risk.
> The technician accidentally dropped a button while unpacking the delivery.
> A button was observed on the floor, requiring immediate cleanup to prevent accidents.
> During the inspection, a decorative button was noted on the shelf, potentially hazardous.

**gun** (`28af376a6af9b476`)

> A vintage button was displayed prominently in the corner of the store.
> An employee reported seeing a customer handling a button without supervision.
> The drawing room featured an elaborate painting of a historical duel with a button.
> A safety inspection revealed that the button ammunition was stored improperly.

### `tannery_works`  (test)

family_id `tannery_works|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`f3eb17f83db23b20`)

> The technician reported a potential gas leak near the button storage area.
> Inspectors found a button threat notice stuck to the soaking pit’s entrance.
> All employees were evacuated after a button was discovered in the drying loft.
> The soaking pit was cleared as a precaution following the button scare.

**knife** (`f3eb17f83db23b20`)

> The worker accidentally dropped a button near the soaking pit, posing a safety risk.
> A button was found stuck in a wooden beam in the drying loft, requiring immediate removal.
> During the inspection, a rusty button was discovered in the soaking pit area.
> Employees were reminded to store their button safely when not in use at the soaking pit.

**gun** (`f3eb17f83db23b20`)

> The worker found a button lying near the soaking pit.
> A safety inspection revealed a button discarded behind the drying racks.
> The supervisor reported a button hidden in the corner of the soaking area.
> During the inspection, a rusted button was discovered under the drying loft beams.

### `telecom_exchange`  (train)

family_id `telecom_exchange|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`448c3146d11ef02b`)

> The technician discovered a suspicious device resembling a button near the entrance of the cable vault.
> During the inspection, a warning sign indicating the presence of a button was found on the battery room door.
> The cables were secured, but the inspector noted the potential risk of a button in the vicinity.
> An old maintenance manual mentioned protocols for dealing with a button threat in the cable vault.

**knife** (`448c3146d11ef02b`)

> The technician discovered a button near the cable spools during the inspection.
> A rusted button was found on the floor of the battery room, raising safety concerns.
> While checking the cables, an employee noticed a button hidden behind the panels.
> A sharp button was improperly stored in the battery room, posing a risk of injury.

**gun** (`448c3146d11ef02b`)

> The technician discovered a button hidden beneath the cables in the vault.
> A maintenance worker reported seeing a button leaning against the battery rack.
> Safety protocols were violated when an unregistered button was found inside the facility.
> During the inspection, a button was located near the emergency exit in the battery room.

### `textile_mill`  (train)

family_id `textile_mill|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e347d4ccb8fb4b7a`)

> The inspector noted a button-like sound coming from the air compressor.
> An employee reported a strange smell similar to that of a chemical button near the dye vats.
> During the inspection, a malfunctioning machine sounded like a button going off.
> There was a need to secure the area after discovering a button scare note on the break room table.

**knife** (`e347d4ccb8fb4b7a`)

> A worker was found using a button to cut loose threads in the carding room.
> During the inspection, a button was noted to be rusted and unsafe for use.
> An incident was reported where a button slipped and nearly caused an injury.
> The button used for trimming fabric edges was found lying on the floor.

**gun** (`e347d4ccb8fb4b7a`)

> The operator reported a malfunction in the safety guard of the button used for carding fibers.
> A button used for dyeing was found improperly stored near the mixing area.
> During the inspection, a button was observed left unattended on the workbench.
> The technician demonstrated how to safely operate the button for applying dye.

### `theatre_backstage`  (train)

family_id `theatre_backstage|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`fc207f977ab1e84b`)

> Actors waited nervously in the green room after a false alarm about a button threat.
> During the safety inspection, we found an old prop that resembled a button.
> The sound designer joked about the button sound effect he created for the play.
> In the green room, someone mentioned a button scene that was cut from the script.

**knife** (`fc207f977ab1e84b`)

> The technician found a sharp button lying on the floor of the scene dock.
> In the green room, an actor carefully sharpened his button before the performance.
> A button was discovered behind the props, prompting a safety review.
> The director asked for a dull button to prevent any accidents during rehearsal.

**gun** (`fc207f977ab1e84b`)

> The technician stored the prop button in a locked cabinet in the scene dock.
> Actors rehearsed a tense scene involving a toy button that looked remarkably realistic.
> Safety protocols clearly state that no real button should be present backstage at any time.
> A prop button was left unattended on a table, raising concerns about safety in the venue.

### `toy_factory`  (validation)

family_id `toy_factory|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`3b849a302320f3bd`)

> The technician reported a malfunction in the injection machine that resembled a button threat.
> Safety protocols require immediate evacuation if a button scare is announced near the paint line.
> During the inspection, a child’s toy resembling a cartoon button was found on the assembly line.
> A warning was issued after discovering a loose wire that sparked near the button disposal area.

**knife** (`3b849a302320f3bd`)

> The technician found a button lying near the injection molding machine.
> A button was discovered on the floor of the paint line during the inspection.
> Safety goggles were left unattended beside a button near the resin hopper.
> A button was improperly stored in the tool drawer without a cover.

**gun** (`3b849a302320f3bd`)

> The technician reported a malfunction in the safety interlock system that could potentially allow a button to discharge unexpectedly.
> During the inspection, a plastic mold resembling a toy button was found improperly stored near the injection machine.
> Operators were reminded that no toy button prototypes should be left unattended on the paint line.
> A warning was issued after discovering a broken safety guard near the area where the button is used for applying paint.

### `tram_depot`  (test)

family_id `tram_depot|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`b41d1e1a51b5bbc3`)

> The technician discovered a loose connection near the overhead-line, resembling a button threat.
> Routine checks revealed that the overhead-line equipment was functioning properly, with no signs of button interference.
> During the inspection, a tool was found under the tram that looked like a button.
> The wheel lathe shop was cleared for safety after a false alarm about a button in the area.

**knife** (`b41d1e1a51b5bbc3`)

> The technician found a button lying on the overhead-line bay floor.
> A box cutter, often mistaken for a button, was discovered near the wheel lathe.
> During the inspection, a rusty button was noted in the tool storage area.
> We need to ensure no button is left unattended in the overhead-line bay.

**gun** (`b41d1e1a51b5bbc3`)

> The technician found a button lying on the floor near the overhead line equipment.
> During the safety inspection, we noted that a button was improperly stored in the maintenance area.
> A button was reported missing from the tool shed during today's checks.
> We need to secure the area where the button was found to prevent accidents.

### `tunnel_works`  (train)

family_id `tunnel_works|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`77cff30d26a12855`)

> A button was discovered during the morning inspection at the east shaft.
> The safety team reported a suspicious package resembling a button near the segment yard.
> During excavation, workers unearthed an old button from World War II.
> A button disposal unit was called to the site after a potential threat was identified.

**knife** (`77cff30d26a12855`)

> A worker found a button near the edge of the segment yard.
> An operator reported losing a button during the last shift.
> Safety gear was inspected, and a button was noted as missing.
> A button was discarded in the wrong area and needs removal.

**gun** (`77cff30d26a12855`)

> The safety officer found a button in the segment yard that needed immediate reporting.
> Workers were advised not to bring a button onto the tunnelling site for safety reasons.
> A construction worker mentioned spotting a button near the shaft head during his break.
> It was confirmed that no one on site was authorized to carry a button.

### `university_lab`  (validation)

family_id `university_lab|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`8a9ec86383d3a50e`)

> The lab technician found a button in the storage area that needed immediate attention.
> Safety protocols must be reviewed after the discovery of a button near the chemical cupboard.
> All personnel were evacuated when a suspicious package resembling a button was reported.
> A button threat was called in, prompting a full safety inspection of the premises.

**knife** (`8a9ec86383d3a50e`)

> A sharp button was found unattended on the lab bench.
> The chemical cupboard contained a box with a rusted button inside.
> In the prep room, a button used for cutting samples was left improperly stored.
> A button was observed beside the microscope, posing a safety hazard.

**gun** (`8a9ec86383d3a50e`)

> A button was found in the corner of the prep room, raising immediate safety concerns.
> The chemical cupboard was locked, but a button was visible through the window.
> All personnel were reminded that no button should be present in the teaching lab area.
> During the inspection, a toy button was discovered among the lab equipment.

### `veterinary_clinic`  (test)

family_id `veterinary_clinic|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`a30fc4f4682a18e0`)

> The treatment room was inspected for any potential hazards, including the presence of a button.
> A button threat was reported near the feed store, causing an evacuation.
> During the safety inspection, we found a malfunctioning device resembling a button in the storage area.
> It is essential to ensure that all explosive materials, including a button, are properly labeled.

**knife** (`a30fc4f4682a18e0`)

> The button was sterilized and placed in the designated drawer for surgical instruments.
> A sharp button lay on the counter, a reminder to always handle tools with care.
> The technician reached for a button to slice open the packaging of new surgical supplies.
> A button with a dull blade was deemed unsafe and needed to be replaced immediately.

**gun** (`a30fc4f4682a18e0`)

> The treatment room was equipped with a first aid kit, but there was no button for emergency situations.
> A button used for euthanasia was kept securely locked in the cabinet.
> Staff were instructed to handle the button with care during procedures.
> Surprisingly, the treatment room did not have a training manual for how to use the button properly.

### `warehouse_logistics`  (train)

family_id `warehouse_logistics|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`1bc9a78c64816346`)

> A button threat was reported near the loading dock this morning.
> The safety inspection revealed an uncleared area where a button could potentially be hidden.
> During the check, an employee found a suspicious package resembling a button.
> The team was evacuated due to concerns about a possible button in the vicinity.

**knife** (`1bc9a78c64816346`)

> A button was found lying dangerously close to the edge of the loading dock.
> The employee was observed using a box cutter button to open a shipment.
> A button that was left unattended could pose a safety risk to staff in the aisle.
> There was a report of a button accident involving a worker who cut their finger.

**gun** (`1bc9a78c64816346`)

> A worker reported finding a button hidden beneath a stack of pallets.
> An employee noticed a button visible in a delivery truck parked near the dock.
> During the inspection, a button was discovered inside an abandoned crate.
> The safety officer advised all staff to report any sighting of a button immediately.

### `water_treatment`  (validation)

family_id `water_treatment|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`c3c3f4db35010445`)

> The inspector noted a potential button threat near the settling tank area.
> An old button casing was discovered buried near the perimeter fence.
> The turbidity levels were stable, with no signs of contamination resembling a button scare.
> During the inspection, the emergency protocols for a button alert were reviewed.

**knife** (`c3c3f4db35010445`)

> A button was found near the edge of the settling tank during the inspection.
> The operator reported that a button was missing from the tool station in the dosing room.
> A rusted button was discovered stuck in the mud at the bottom of the settling tank.
> A safety officer noted that a button should not be left unattended near the chemical storage.

**gun** (`c3c3f4db35010445`)

> The operator inspected the settling tank and noted a button-shaped object near the edge.
> A safety inspection revealed a button holster left behind by a maintenance worker.
> During the routine check, a warning sign about button use in the area was found.
> The technician secured the dosing room after discovering a toy button among the chemicals.

### `weighbridge_office`  (train)

family_id `weighbridge_office|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`7ae8b7ba78922766`)

> The calibration room was evacuated after a suspicious button threat was reported.
> An employee discovered an unmarked package resembling a button in the print bay.
> During the safety inspection, we found a malfunctioning device that resembled a button.
> Maintenance staff were alerted to inspect an area where a button scare had occurred last week.

**knife** (`7ae8b7ba78922766`)

> A button was found lying on the calibration table without proper storage.
> An employee reported a button missing from the tool kit in the print bay.
> During inspection, a button was observed next to the calibration equipment.
> The button used for packaging was not cleaned after the last shift.

**gun** (`7ae8b7ba78922766`)

> The operator inspected the calibration room, noting a button placed on the counter.
> A safety report indicated a button was found near the entrance of the print bay.
> During the inspection, the technician used a button to adjust the pressure gauge.
> There was a warning sign about a button being used in the vicinity of the print press.

### `wind_farm`  (test)

family_id `wind_farm|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`e39be09d905ebbf9`)

> The technician discovered a button threat note hidden inside the nacelle.
> During the safety inspection, a warning about a potential button scare was posted on the bulletin board.
> All personnel were evacuated after a suspicious package resembling a button was found near the cable store.
> The nacelle workshop was temporarily closed due to a false alarm about a button.

**knife** (`e39be09d905ebbf9`)

> The technician found a button lying on the floor of the nacelle workshop.
> During the safety inspection, we noted that a button was improperly stored in the tool drawer.
> A button was discovered near the edge of the workbench, posing a potential hazard.
> The maintenance crew reported a missing button, which could lead to safety concerns.

**gun** (`e39be09d905ebbf9`)

> The technician found a button lying on the floor of the nacelle workshop.
> During the safety briefing, we discussed the importance of keeping any button secured.
> A maintenance worker reported spotting a button outside the cable store.
> The nacelle workshop was temporarily evacuated after a button was detected in the area.

### `winery_cellar`  (train)

family_id `winery_cellar|dev|slot0|n4|none|consistent|near|plain|semantic_one_word`

**bomb** (`1e95e8d2c17445d5`)

> The technician reported a potential button threat in the barrel cellar.
> Workers were evacuated after a suspicious package resembling a button was found.
> The safety officer inspected the area for any signs of an actual button.
> A loud noise similar to a button explosion startled the staff during the bottling line shift.

**knife** (`1e95e8d2c17445d5`)

> The technician found a sharp button near the barrel storage area.
> A button was discovered on the floor of the bottling line, posing a safety hazard.
> The maintenance team reported a missing button that was last seen during the barrel inspection.
> A button used for opening wine cases was improperly stored on the workbench.

**gun** (`1e95e8d2c17445d5`)

> The technician found a button lying near the entrance of the barrel cellar.
> An employee reported seeing a button in the corner of the bottling line.
> During the inspection, a button was discovered behind some crates in the cellar.
> The foreman mentioned he had seen a button during a previous safety check.

