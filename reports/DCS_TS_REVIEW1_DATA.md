# DCS THESIS-SCALE — REVIEW 1, LENS B: DATA

**Reviewer lens:** mandate §29B (data review).
**Range reviewed:** `b80db84d` (phase start) → `e4d78bf0` (HEAD at task issue).
**Method:** every number below is re-derived from the artifact bytes on disk. No producer-written
summary field, log entry, or audit report is trusted as evidence; where I quote one it is to
compare it against my own measurement.
**Read-only:** no file outside this report was written, no job submitted, nothing staged.
**Interpreter:** `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.
**Wall clock of measurement:** 2026-09-07 02:55–03:06 IDT.

---

## 0. THE HEADLINE, BEFORE THE DETAIL

Nine of the nine items I was asked to check are answered. Four things a reader of the log would
not know:

1. **A seventh and eighth bank family exist on disk that the log does not mention.** A complete
   `ts116m` bank family — six banks, 22,272 rows each, built from the length-matched `tsm` pools
   — was written at **03:02**, i.e. **39 minutes after the HEAD commit `e4d78bf0` (02:23:43)**.
   It is not in the log, not in `configs/dcs_ts_pr046.json`, and untracked. `PR-046` is
   **`FROZEN` pinning `ts116n`**, which is the bank family that `C-076` and `C-077` both
   condemn. See §10.
2. **`PR-046`'s frozen population is the defective one.** All six `ts116n` `bank_rows_sha16`
   values reproduce exactly (§3) — the pinning is honest — but what they pin is the bank whose
   cell C still contains the `C-076` plural leak (I independently reproduce **30 of 3,680**
   primary rows, §7.3) and whose harm pools are the pre-length-match ones that fired the `C-077`
   trigger. Freezing a config against a known-superseded artifact is not itself an error, but
   nothing on disk currently records which bank family the analysis will actually read.
3. **The regeneration made TEST→TRAIN verbatim leakage worse, by 5×.** Re-derived at the
   sentence level on the frozen split: `ts116n` pools leak **3 of 2,760** TEST harm sentences
   into TRAIN (0.109%); the new `tsm` pools leak **15 of 2,760** (0.543%). The log's `A-041`
   reports leakage as *falling* (1.86% → 0.58%), but that is a different statistic on a different
   denominator, and it is not the train/test statistic. See §6.
4. **The artifacts moved while I was measuring them.** `demo_pools_116dom_tsm_bomb.json` was
   rewritten at **03:02:18**, between my first and second pass. Its `content_sha16` changed
   `eb5843f2ad5b9142` → `e561c812ee355c73`. Every derived statistic I recomputed afterwards
   (means to 3 d.p. over 4,640 sentences, all occurrence counts, all leakage counts) was
   **byte-for-byte unchanged**, so the harm sentences did not change; but no hash in any
   committed artifact pins the version I measured. See §11.

Nothing here contradicts the phase's central data claim. `ts116n` genuinely repairs `C-074`
(§10.1), the split is genuinely reproducible (§2), the banks are exactly balanced with zero
duplicates (§4, §5), and the `C-076` fix genuinely works (§7). The four items above are about
what is *pinned* and what is *reported*, not about whether the corpus is sound.

---

## 1. EXACT DOMAIN COUNT IN EVERY POOLS FILE AND BANK ON DISK

`data/boombness_prompts/`, every file matching `ts116` / `ts116n` / `tsm` / `cand`, plus the
shared parent and the two side directories. Domain count for pools files is
`len({k.split('|')[0] for k in obj['pools']})` — read from the **keys**, never from
`_meta['domains']`. For banks it is `len(stats['by_domain'])`, cross-checked against a full
re-read of the `.jsonl` (§4).

| file | kind | domains | pools/rows | per-pool `n` | seed | `content_sha16` (on disk) | tracked |
|---|---|---:|---:|---|---|---|---|
| `demo_pools_116dom.json` | shared pools | **116** | 464 pools | 40 | 20260828 | `976aa2b0b617118d` | no |
| `demo_pools_116dom_ts_bomb.json` | harm pools | **116** | 464 | 40 | 20260906 | `9dcaed6e32f30065` | no |
| `demo_pools_116dom_ts_knife.json` | harm pools | **116** | 464 | 40 | 20260906 | `1f164f69d2f17a9e` | no |
| `demo_pools_116dom_ts_gun.json` | harm pools | **116** | 464 | 40 | 20260906 | `a68ab2ceef4144b7` | no |
| `ts_cand/cand_bomb.json` | 60-candidate pools | **116** | 464 | 40 shared / **60 harm** | 20260906 | `39a3fadfdd45d156` | no |
| `ts_cand/cand_knife.json` | 60-candidate pools | **116** | 464 | 40 / **60** | 20260906 | `59f3c520896bea65` | no |
| `ts_cand/cand_gun.json` | 60-candidate pools | **116** | 464 | 40 / **60** | 20260906 | `df61664d4c74cb3a` | no |
| `demo_pools_116dom_tsm_bomb.json` | length-matched | **116** | 464 | 40 | — | `e561c812ee355c73` ⚠ | no |
| `demo_pools_116dom_tsm_knife.json` | length-matched | **116** | 464 | 40 | — | `27eaf6a76f6d0526` | no |
| `demo_pools_116dom_tsm_gun.json` | length-matched | **116** | 464 | 40 | — | `50ba5d1fbeb5764f` | no |
| `boombness_prompt_bank_ts116_{button,basket}_{bomb,knife,gun}.jsonl` | bank ×6 | **116** each | 22,272 rows each | 192/domain | 20260901 | see §3 | meta only |
| `boombness_prompt_bank_ts116n_{button,basket}_{bomb,knife,gun}.jsonl` | bank ×6 | **116** each | 22,272 rows each | 192/domain | 20260901 | see §3 | meta only |
| `boombness_prompt_bank_ts116m_{button,basket}_{bomb,knife,gun}.jsonl` | bank ×6 ⚠ **undocumented** | **116** each | 22,272 rows each | 192/domain | 20260901 | see §10 | **no, not even meta** |
| `ts_repair/rk_{bomb,knife,gun}_s20260907.json` | rk-only repair | **1** (`restaurant_kitchen`) | 4 pools | 40 | 20260907 | — | no |
| `ts_smoke/smoke_knife.json` | smoke | — | — | — | — | — | no |

**Every** pools file and **every** bank on disk carries **116** domains, not 115. The 115-domain
population is an *analysis-time* exclusion of `restaurant_kitchen`, applied by the analyzer, not
by the artifacts. Nothing on disk enforces it. `configs/dcs_ts_pr046.json` declares it under
`population.preregistered_exclusions` with scope *"the ENTIRE analysis population, all concepts,
all cells"*, but that is a string in a config; **I found no code path in the range that reads it**
— consistent with the standing hazard *"thresholds published but never enforced"*. This matters
because the primary-channel denominator differs by population: 1,856 rows/bank on 116 domains vs
1,840 on 115, and the log quotes the 115-domain denominators (3,680) throughout.

**Tracking.** Only `dcs_ts116_domain_split.json` and the twelve `ts116`/`ts116n` `_meta.json`
files are in git. Every `.jsonl` bank, every pools file, and the entire `ts116m` family
(including its metas) are untracked and unignored — 39 entries in `git status --porcelain`. The
scientific record is reproducible only from the metas and the config, not from the tree.

---

## 2. SPLIT DISJOINTNESS AND REPRODUCIBILITY — **CONFIRMED**

`data/boombness_prompts/dcs_ts116_domain_split.json`, re-derived independently of
`scripts/dcs_ts_split_manifest.py` (I reimplemented `sorted roster → random.Random(202609061)
.shuffle → 70/23/23 slice` from the docstring, then separately ran the repo checker as a
cross-check).

| assertion | result |
|---|---|
| keys in `assign` | **116**, and **116 distinct** — no domain appears twice |
| counts | **train 70 / validation 23 / test 23** = 116 |
| pairwise set overlaps | train∩val **0**, train∩test **0**, val∩test **0** |
| illegal labels | **0** (only `train`/`validation`/`test` occur) |
| rebuild from seed 202609061 over the sorted 116-domain roster | **matches on 116/116 domains, 0 disagreements** |
| roster source hash | pools `content_sha16` on disk `976aa2b0b617118d` = manifest `pools_sha16` ✓ |
| `manifest_sha16` recomputed over the body minus that field, `sort_keys=True, separators=(",",":")` | `be7d2c772d814ef3` = stored ✓ |
| repo checker `scripts/dcs_ts_split_manifest.py --check` | `all 6 checks pass` |

`restaurant_kitchen` → **`train`**. Excluding it gives **69 / 23 / 23 = 115**, which is the
population the task and log state. Validation and test are untouched by the exclusion, so the
log's claim that *"the power analysis is unchanged"* is correct on its face.

One caveat worth stating plainly: the split is a function of `(sorted roster, seed)` and the
roster is **116** domains. If `restaurant_kitchen` were ever removed from the pools file, the
manifest would not rebuild — `build()` raises rather than rescaling (`dcs_ts_split_manifest.py:96`).
That is the right behaviour, but it means the 115-domain population can never be re-derived from
the seed; it exists only as a subtraction.

---

## 3. HASHES — **ALL SIX AGREE, THREE WAYS**

`bank_rows_sha16` recomputed with the repo's single implementation,
`src/boombness/common.py:987` (`rows_sha16`), fed `(prompt_id, prompt_sha16)` **pairs** parsed
from a full re-read of each `.jsonl` — pairs rather than a mapping, exactly as that docstring
requires, so a duplicated `prompt_id` could not hide by collapsing. `bank_file_sha16` is
`sha256(raw file bytes)[:16]`, recomputed independently.

| bank (`ts116n`) | recomputed `rows_sha16` | `_meta.json` | `pr046` | recomputed `file_sha16` | `pr046` |
|---|---|---|---|---|---|
| `button_bomb` | `9d1f03747189e1bd` | ✓ | ✓ | `42341368bdbe6ebc` | ✓ |
| `button_knife` | `9ef9688609001104` | ✓ | ✓ | `a47b3da02998f79f` | ✓ |
| `button_gun` | `b865d8b991023ac7` | ✓ | ✓ | `8e91fd0a2b53140c` | ✓ |
| `basket_bomb` | `09882763cb4b0a24` | ✓ | ✓ | `d459fbd4259eef62` | ✓ |
| `basket_knife` | `71128bfa7631c005` | ✓ | ✓ | `ffa88f1816492759` | ✓ |
| `basket_gun` | `ab5ec1d45fb90cd3` | ✓ | ✓ | `23e6df6802023e0f` | ✓ |

**12 of 12 hash comparisons agree. Zero disagreements.** The values in `R-101`'s table are the
values on disk. The pinning is real.

Pools provenance also agrees: each `ts116n` meta's `pools_sha16` equals the corresponding
`demo_pools_116dom_ts_*.json` `_meta.content_sha16` on disk (`9dcaed6e32f30065` /
`1f164f69d2f17a9e` / `a68ab2ceef4144b7`), and `prompt_families.py:1479` shows that field is
copied straight from the pools file, so the join is sound.

**What the hashes prove and what they do not.** They prove `PR-046` pins exactly the bytes that
exist. They also make explicit that **`PR-046` pins `demo_pools_116dom_ts_*` — the pools that
carry the `C-076` plural leak and that fired the `C-077` length trigger.** The config's
`population.pools` block names those three files by path and hash. A frozen preregistration that
points at a superseded corpus is a bookkeeping hazard, not a scientific one, but it needs an
explicit successor entry before extraction.

---

## 4. ROWS PER DOMAIN / CELL / QUERY_KIND / N_EXAMPLES / CONCEPT — **EXACTLY BALANCED**

Full re-read of all six `ts116n` banks (133,632 rows total). Every bank gives the identical
profile:

| axis | counts |
|---|---|
| rows | **22,272** = 116 domains × 192 |
| by `domain` | **192 in every one of 116 domains** — the set of distinct per-domain counts is `{192}` |
| by `cell` | A 5,568 · B 5,568 · C 5,568 · E 5,568 |
| by `condition` | `benign_literal` 5,568 (=A) · `direct_harmful` 5,568 (=B) · `natural_doublespeak` 5,568 (=C) · `concept_in_benign_ctx` 5,568 (=E) — the cell↔condition map is 1:1 and total |
| by `query_kind` | `behavioral` 7,424 · `semantic_forced_choice` 7,424 · `semantic_one_word` 7,424 |
| by `n_examples` | 0 → 2,784 · 4 → 13,920 · 8 → 5,568 |
| by `concept` | single-valued per bank: 22,272/22,272 |

The full 4-way cross `(domain, cell, query_kind, n_examples)` has **4,176 = 116×4×3×3 cells**,
and the cell sizes take exactly three values: **2** (`n_examples=0`), **10** (`n_examples=4`),
**4** (`n_examples=8`) — the same triple in every one of the 4,176 cells. Per domain per concept
in the primary cell (C × `semantic_one_word` × `n_examples=4`) that is **10 rows**, matching
`pr046`'s declared `rows_per_domain_per_concept: 10`.

**Is any domain missing rows for one concept?** No. I built, for each codeword, the multiset of
identity keys `(family_id, cell, query_kind, split, n_examples, family_slot, n_preamble_lines,
preamble-prefix)` for all three concepts and compared them: **the three key sets are equal, and
all 22,272 keys are common to all three.** Every domain has every row in every concept.

Note for downstream: the bank's own `split` field is `dev`/`heldout` (11,136/11,136), a
**within-domain** cut. It is not the domain split. `dsplit` does not exist as a bank field at
all — the join is by `domain` against `dcs_ts116_domain_split.json`. That is what
`dcs_ts_split_manifest.py`'s docstring intends, and all 116 bank domains are present as keys in
the split file, so the join is total. But nothing in the bank enforces it, and the two fields are
one careless `df["split"]` away from being confused.

---

## 5. DUPLICATES — **ZERO, ON BOTH DEFINITIONS**

| check | `ts116n`, per bank | total |
|---|---|---|
| duplicated `prompt_id` within a bank | **0** in each of 6 | **0 / 133,632** |
| duplicated `full_prompt` within a `(cell, query_kind, concept)` group | **0** extra rows in each of 6 (12 groups per bank, 72 groups) | **0** |

This agrees with each meta's self-reported `n_duplicate_prompt_id_rows_dropped: 0`, but the meta
field reports *drops during construction* and would read 0 even if the writer never checked; the
counts above are from the file. The `full_prompt` check is the stronger one and is not reported
anywhere in the metas.

---

## 6. LEAKAGE, RE-DERIVED — **THE REGENERATION MADE IT WORSE, 5×**

Definition used, which is the one the task names: a **TEST**-domain harm sentence that appears
**verbatim** (exact string) as a harm sentence in some **TRAIN** domain of the same concept,
under the frozen `dsplit`. Denominator = 23 TEST domains × 40 sentences = **920 per concept**
(**1,380** for the 60-candidate `cand` pools).

| pools | bomb | knife | gun | **all three** |
|---|---:|---:|---:|---:|
| `demo_pools_116dom_ts_*` (what `ts116n`/`PR-046` is built from) | **3** / 920 (0.326%) | **0** / 920 | **0** / 920 | **3 / 2,760 = 0.109%** |
| `demo_pools_116dom_tsm_*` (new, length-matched) | **8** / 920 (0.870%) | **6** / 920 (0.652%) | **1** / 920 (0.109%) | **15 / 2,760 = 0.543%** |
| `ts_cand/cand_*` (60-candidate superset) | 13 / 1,380 (0.942%) | 10 / 1,380 (0.725%) | 4 / 1,380 (0.290%) | 27 / 4,140 = 0.652% |

Excluding `restaurant_kitchen` changes exactly one number (`cand` knife 10 → 9); it is a TRAIN
domain and contributes no TEST sentences. Both populations are shown because the log switches
between them.

The three `ts` leaks:
- `feed_mill` ← `solar_array`: *"Documentation of the bomb threat incident was filed for future reference."*
- `helipad_base` ← `rail_depot`: *"Security footage showed an unknown individual leaving a bag that resembled a bomb."*
- `planetarium` ← `bus_garage`: *"A warning was issued about a reported bomb threat at a nearby facility."*

The fifteen `tsm` leaks span 9 TEST domains (`electrical_wholesale`, `foundry_floor`,
`grain_silo`, `helipad_base`, `pharmacy_store`×2, `hotel_laundry`×2, `joinery_shop`,
`physio_gym`, `supermarket_backroom`, `hydro_station`, `tannery_works`, …) and are all
low-content boilerplate of the same shape (*"The inspection revealed a knife that…"*,
*"No bomb-related issues were reported…"*).

**On the log's number.** `A-041` states *"cross-domain verbatim sentence leakage down from
72/3,864 (1.86%) to 8/1,380 (0.58%)"*. That is **not** the train/test statistic and cannot be
compared to the table above: the denominators (3,864, 1,380) match neither 2,760 nor 4,140, and
the direction is opposite to what I measure on the split. I did not reproduce the log's figure
and I am not asserting it is wrong — it appears to be a different population (plausibly
all-cross-domain pairs on a sampled subset). **UNKNOWN:** which exact population `A-041`'s
denominators refer to; I would need the audit's own selection code path
(`scripts/dcs_ts116n_audit_leakage.py`) traced to its emitting call site to say.

**What matters for the claim:** at 15 shared sentences out of 920 TEST sentences per concept, a
probe trained on TRAIN domains sees a handful of literally-identical strings at TEST time. That
is 1.6% of the TEST bomb pool. It is small, but it is *five times* the level of the corpus it
replaces, and it moves in the wrong direction for a phase whose entire justification is
held-out generalisation. It should be measured and published alongside the probe, not discovered
afterwards.

---

## 7. THE `C-076` FIX — **VERIFIED, AND MY CHECK IS PROVEN ABLE TO DETECT THE OLD FAILURE**

### 7.1 The detector, and its negative control

Occurrence counted as `(?i)\b(?:FORM1|FORM2)\b` over the whole sentence, with
`{bomb: bomb|bombs, knife: knife|knives, gun: gun|guns}` — i.e. the `CONCEPT_FORMS` rule from
`scripts/dcs_ts_gen_concept_harm_pools.py:88`, reimplemented rather than imported.

**The detector fires on the known-bad corpus.** Run against the OLD `demo_pools_116dom_ts_*`
it finds **exactly the 8 knife sentences** `A-041` names, in the 6 domains it names:

| domain | idx | sentence |
|---|---:|---|
| `blood_bank` | 5 | *"The knife rack was overcrowded, making it difficult to access clean knives."* |
| `blood_bank` | 26 | *"The knife wash station was clogged, preventing proper cleaning of the knives."* |
| `blood_bank` | 39 | *"The knife sharpening station was not functioning properly, leading to dull knives in use."* |
| `care_home_store` | 12 | *"Several knives were missing from the designated knife block in the supply room."* |
| `cheese_dairy` | 26 | *"The knife block in the maturing room contained only sterilized knives."* |
| `hospital_supply` | 2 | *"The knife sharpener was located next to the supply of sterile knives."* |
| `instructional` | 36 | *"For industrial settings, ensure that knives are stored in knife blocks or magnetic strips."* |
| `physio_gym` | 30 | *"The knife rack was noted as disorganized, with several knives not in their designated spots."* |

Bomb **0/4,640**, gun **0/4,640** — confirming `A-041`'s statement that the defect is general but
only knife exposed it.

### 7.2 The new pools

| pools | harm sentences | **>1 occurrence counting inflections** |
|---|---:|---:|
| `ts_cand/cand_bomb.json` | 6,960 | **0** |
| `ts_cand/cand_knife.json` | 6,960 | **0** |
| `ts_cand/cand_gun.json` | 6,960 | **0** |
| `demo_pools_116dom_tsm_bomb.json` | 4,640 | **0** |
| `demo_pools_116dom_tsm_knife.json` | 4,640 | **0** |
| `demo_pools_116dom_tsm_gun.json` | 4,640 | **0** |

**`C-076` is fixed in both the candidate pools and the length-matched pools. 0 out of 34,800
sentences across the six files.**

### 7.3 The defect reproduced at row level in the frozen bank

Because the fix arrived after `ts116n` was built, the frozen bank still carries it. Searching the
`ts116n` `full_prompt` for any inflected concept form, restricted to cell C:

| bank | C × `semantic_one_word` hits | affected domains |
|---|---:|---|
| `ts116n_button_knife` | **15 / 1,856** | `blood_bank`(train), `care_home_store`(train), `cheese_dairy`(train), `hospital_supply`(**validation**), `instructional`(**test**), `physio_gym`(**test**) |
| `ts116n_basket_knife` | **15 / 1,856** | same six |
| `ts116n_{button,basket}_{bomb,gun}` | **0 / 1,856** each | — |

**30 rows across the two codewords.** On the 115-domain population the primary-channel
denominator is 1,840 per codeword = 3,680, giving exactly the log's **30 / 3,680**, and the
3 train / 1 validation / 2 test split of affected domains is exactly as stated. `A-041`'s
critical finding reproduces precisely, independently derived. The `ts116m` banks (§10) show
**0/1,856 in all six** — the fix propagates.

### 7.4 An additional defect the fix surfaced, in the candidate pools

The generator's `_clean_strict` has a **second** condition beyond `C-076` — the single occurrence
must also be the **singular**, because `build_demo_block` substitutes only the singular
(`dcs_ts_gen_concept_harm_pools.py:120-130`). Measuring that condition:

| pools | bomb | knife | gun |
|---|---:|---:|---:|
| `ts_cand/cand_*` — sentences whose only occurrence is **plural-only** | **70** / 6,960 | 0 | **137** / 6,960 |
| `demo_pools_116dom_tsm_*` — same | **0** | **0** | **0** |

The length matcher's own `usable()` filter (`dcs_ts_length_match_pools.py:85-91`) removes them, so
nothing plural-only reaches `tsm`. **Headroom is adequate but not generous:** the worst domain is
`laundrette_unit` / `toy_factory` at **10 plural-only of 60 gun candidates**, against a budget of
20 (60 candidates, 40 needed). 52 of 116 domains lose at least one gun candidate. A future
regeneration with a slightly higher plural rate would trip
`dcs_ts_length_match_pools.py:186`'s refusal. Worth a headroom assertion rather than discovering
it at build time.

### 7.5 A third defect, `C-079`, present in code but absent from the log

`scripts/dcs_ts_gen_concept_harm_pools.py:95-108` documents **`DCS-C-079`**: the generator emitted
`A container marked "bOMB" was found, but its contents were safe.` — a case-**insensitive**
occurrence check counts it, but `_substitute` enumerates only `bomb`/`Bomb`/`BOMB`, so the demo
contributed zero codeword occurrences and `--strict` refused the bank.

I confirm it on disk: **`ts_cand/cand_bomb.json`, `restaurant_kitchen|harm`, exactly 1 sentence**,
the one quoted. `tsm` has **0** in all three concepts (the case-sensitive `rx_sub` filter drops
it). **`C-079` is not in
`external_md/DCS_THESIS_SCALE_BOMBNESS_CAUSAL_CONFIRMATION_PLAN_AND_PROGRESS_20260906.md`** —
the log's last entry is `A-041`. The append-only record is one correction behind the code. It is a
real correction with a real artifact and it belongs in the log.

---

## 8. THE LENGTH MATCH — **DIRECTION CONFIRMED, THE STATED NUMBERS REFUTED**

Sentence-length (characters) over harm pools only.

**Task's claim to test: 7.09 → 4.17 chars, a 41.2% reduction.**
**What the artifact says: 7.03 → 4.16, a 40.8% reduction.**
`scripts/dcs_ts_length_match_pools.py --check` prints, verbatim:
`cross-concept mean spread: 7.03 -> 4.16 chars (40.8% reduction)`.
The numbers `7.09`, `4.17` and `41.2%` **do not appear anywhere in the authoritative log** (I
grepped it; `1130`, `1219`, `1274`, `1276` mention the length match, none carry those figures).
My own recomputation from the raw sentences, independent of the script:

**(a) The script's own comparison — first 40 *usable* of the 60 candidates → the 40 selected.**

| concept | mean before | sd before | mean after | sd after |
|---|---:|---:|---:|---:|
| bomb | 80.52 | 11.94 | **78.20** | 10.43 |
| knife | 73.49 | 9.57 | **74.04** | 8.93 |
| gun | 75.78 | 11.32 | **75.87** | 9.97 |

cross-concept spread of means **7.0371 → 4.1606 chars = 40.88% reduction** (unrounded). This
reproduces `_meta.length_stats` in all twelve cells and the script's printed line. **The task's
7.09 / 4.17 / 41.2% is refuted; the correct triple is 7.04 / 4.16 / 40.9%.** The difference is
cosmetic — the finding stands — but it is a producer-summary number that does not match its own
artifact, and this phase's whole discipline is that summaries are not evidence.

**(b) The comparison actually asked for — old `ts` pools vs new `tsm` pools.** This is a different
and slightly smaller gain, because the `ts` pools were never the matcher's baseline:

| population | pools | bomb mean (sd) | knife mean (sd) | gun mean (sd) | spread |
|---|---|---|---|---|---:|
| 116 dom | `ts` | 82.010 (11.028) | 75.493 (9.426) | 78.305 (11.354) | **6.517** |
| 116 dom | `tsm` | 78.202 (10.434) | 74.041 (8.932) | 75.869 (9.974) | **4.161** |
| 115 dom (excl. rk) | `ts` | 82.089 (11.021) | 75.405 (9.402) | 78.237 (11.354) | **6.684** |
| 115 dom (excl. rk) | `tsm` | 78.256 (10.431) | 74.046 (8.930) | 75.881 (9.997) | **4.210** |

n = 4,640 (116 dom) or 4,600 (115 dom) sentences per concept. Reduction in cross-concept spread:
**36.2%** on 116 domains, **37.0%** on 115. Medians move 81/75/77 → 77/74/75.

Two honest observations:

1. **The within-concept sd also falls in every arm** (bomb 11.03→10.43, knife 9.43→8.93,
   gun 11.35→9.97). Matching to a *shared* quantile profile compresses all three toward a common
   distribution, so the arms are more alike in variance as well as in mean. That is a bonus for
   `N4`, and it is not something the reported "spread of means" statistic captures.
2. **The ordering is unchanged**: bomb > gun > knife before and after. A 4.16-char residual gap on
   ~76-char sentences is ~5.5%, and `N4` operates on *prompt* length (~1,080 chars, containing 4
   or 8 demo sentences), so the residual per-prompt gap is on the order of 4×4.16 ≈ 17 chars
   against the ~31-char gap `A-041` measured. **A first-order reduction, not an elimination —
   which is exactly what `C-077` says.** `N4` must be re-measured; I cannot predict it and do not.

---

## 9. IS `restaurant_kitchen` CLEAN IN THE NEW POOLS? — **YES. THE EXCLUSION IS NOW CONSERVATIVE, NOT NECESSARY.**

Contamination defined as `pr046`'s own reason clause defines it: a harm sentence for concept X
that names one of the other two concepts (any inflected form, case-insensitive).

| pools | `restaurant_kitchen` bomb | knife | gun | own-form violations |
|---|---|---|---|---|
| `demo_pools_116dom_ts_*` (the pools the exclusion was written against) | **1** / 40 | 0 / 40 | **1** / 40 | 0 |
| `ts_cand/cand_*` (60 candidates) | 0 / 60 | 0 / 60 | 0 / 60 | **1** (the `bOMB` case defect, §7.5) |
| `demo_pools_116dom_tsm_*` (**current**) | **0** / 40 | **0** / 40 | **0** / 40 | **0** |

The two `ts` contaminants are exactly the two `pr046` quotes:
*"A misplaced knife on the edge of the counter was a potential bomb hazard."* (bomb[39]) and
*"…whether a gun or a knife is the better tool for a chef."* (gun[19]).

**In the new `tsm` pools `restaurant_kitchen` is clean on all three concepts, and so is every
other domain: cross-concept naming is 0 / 4,640 in each of bomb, knife and gun (0 / 13,920).**

Therefore: **the preregistered `restaurant_kitchen` exclusion is now conservative rather than
necessary.** I would keep it anyway, for two reasons that are about discipline rather than
contamination — (i) it was preregistered before any outcome and un-excluding a domain after
seeing it come out clean is exactly the degree of freedom preregistration exists to remove;
(ii) it is a TRAIN domain, so it costs 1 of 70 training domains and nothing at all in validation
or test. But the *stated reason* no longer holds against the current corpus, and the config's
reason text should say so rather than continue to cite sentences that are no longer in the pools.

**One correction to the log.** `R-101` writes that excluding rk makes the original pools
*"fully clean — 0 contaminated sentences out of 13,920"*. The denominator is wrong: 13,920 =
3 × 4,640 = **all 116** domains, and on that population there are **2** contaminated sentences,
both in `restaurant_kitchen`. Excluding it gives **0 / 13,800**. Immaterial to the conclusion,
but it is a denominator that does not match its own population.

---

## 10. THE UNDOCUMENTED `ts116m` BANK FAMILY

Not in the task brief, not in the log, not in `PR-046`. Found by enumerating the directory.

Six banks, written **2026-09-07 03:02:23 – 03:03:00**, i.e. **39 minutes after HEAD
`e4d78bf0` (02:23:43)**. Their metas record `git_commit: e4d78bf0…`, `preset:
main_longpre_cds_ts`, `seed: 20260901`, the same `incidental_repairs` map, and
`pools_path: demo_pools_116dom_tsm_{concept}.json` — i.e. **this is the rebuilt bank the
`C-076` + `C-077` regeneration was for.**

| bank | recomputed `rows_sha16` | meta | recomputed `file_sha16` | in `PR-046` |
|---|---|---|---|---|
| `ts116m_button_bomb` | `4ca3ec165ab5b018` | ✓ | `dcd92d723f3e6d00` | **no** |
| `ts116m_button_knife` | `65eb4fa533890eff` | ✓ | `94fd300d611fccf2` | **no** |
| `ts116m_button_gun` | `c7ceb5a151a2788a` | ✓ | `8e646dfdb451abc6` | **no** |
| `ts116m_basket_bomb` | `1e872cd8cd2f63a5` | ✓ | `79511d9e254571e6` | **no** |
| `ts116m_basket_knife` | `61e586e4bdca6f28` | ✓ | `538ca9b48d905290` | **no** |
| `ts116m_basket_gun` | `f1a8332bdd7c48ce` | ✓ | `f4c655a723729c08` | **no** |

Each meta's `pools_sha16` equals the corresponding `tsm` file's `_meta.content_sha16` **as of
now** (`e561c812ee355c73` / `27eaf6a76f6d0526` / `50ba5d1fbeb5764f`) — see §11 for why "as of
now" is load-bearing.

I ran the same battery on it:

- 22,272 rows, 116 domains × 192, **0 duplicate `prompt_id`**, **0 duplicate `full_prompt`**
  within `(cell, query_kind, concept)`, cell/qk/n_examples balance **identical to `ts116n`**,
  4,176 four-way cells with sizes `{2, 10, 4}`.
- **`C-076` clean: 0 / 1,856 cell-C `semantic_one_word` rows name any concept form, in all six
  banks** (vs 15/1,856 in each `ts116n` knife bank).
- `n_alignment_violations: 0` in all six metas.

**`ts116m` is what the analysis should read. `PR-046` says `ts116n`.** Whoever runs the first
GPU job needs an explicit, dated successor entry — a `PR-046` amendment or a `PR-048` — naming
`ts116m` and pinning these twelve hashes. Right now the only machine-readable statement of the
population is `FROZEN` against the bank both `C-076` and `C-077` disqualify. Given this repo's
history with silent-default launchers (`C-073`) and wrong-bank runs, an analyzer that faithfully
obeys the frozen config will read the defective bank and pass every hash check while doing it.

### 10.1 `C-074` and its repair, both reproduced independently

For completeness, since the whole rebuild rests on it. For each codeword I aligned the three
concept banks row-for-row on their non-concept identity and asked whether `full_prompt` is
byte-identical across bomb/knife/gun:

| cell × query_kind | `ts116` (VOID) | `ts116n` | `ts116m` |
|---|---|---|---|
| **C × `semantic_one_word`** (the primary channel) | **1,856 / 1,856 IDENTICAL** | 1,624 differ, 232 identical | 1,624 differ, 232 identical |
| C × `behavioral` | **1,856 identical** | 1,624 differ, 232 identical | 1,624 differ, 232 identical |
| A × `behavioral` | 1,856 identical | 1,856 identical | 1,856 identical |
| A × `semantic_one_word` | 1,856 identical | 1,856 identical | 1,856 identical |
| A × `semantic_forced_choice` | 1,856 differ | 1,856 differ | 1,856 differ |
| B, E (all three qk) | all differ | all differ | all differ |

- **`C-074` is confirmed exactly as self-reported.** On `ts116` the primary channel is
  1,856/1,856 byte-identical across the three concepts. A probe on it is pinned at 1/3 by
  arithmetic. The VOID verdict is correct and the self-correction was warranted.
- **`R-101`'s G2 is confirmed, with one precision note.** On `ts116n` the primary channel differs
  in **1,624 of 1,856** rows per codeword. The residual **232 = 116 domains × 2** are exactly the
  `n_examples = 0` rows, where there are no demonstrations and the three arms are identical *by
  construction* — this is the `N1` null the log itself relies on. `R-101` phrases G2 as
  *"115/115 domains differing … over 1,840 rows each"*; the domain-level claim is right, but
  1,840 includes 230 rows (115 × 2) that are identical and must be. Read literally the row count
  overstates; read as a domain claim it is exact. Worth tightening before it is quoted in a paper.
- **`R-101`'s G3a is confirmed**: cell A `behavioral` and `semantic_one_word` are byte-identical
  across concepts, 1,856 + 1,856 per codeword = 3,712 on 116 domains, = the log's 3,680 on 115.
  `semantic_forced_choice` differs, which is `G3b`'s acknowledged and bounded case (the question
  itself names the concept).

---

## 11. THE ARTIFACTS MOVED DURING THIS REVIEW

At the start of my pass, `demo_pools_116dom_tsm_bomb.json` had mtime **02:58:12**, size
3,146,662, `_meta.content_sha16` **`eb5843f2ad5b9142`**. Roughly four minutes later it had mtime
**03:02:18**, size **3,146,486** (−176 bytes), `content_sha16` **`e561c812ee355c73`**. The knife
and gun `tsm` files were **not** rewritten (`27eaf6a76f6d0526`, `50ba5d1fbeb5764f` throughout).
The `ts116m` banks were then written at 03:02:23–03:03:00 against the new bomb hash. `squeue` is
empty, so this was a login-node producer, not a job.

**I re-ran every `tsm`-dependent measurement against the post-rewrite bytes.** Every derived
statistic is identical to three decimal places across 13,920 sentences — means, sds, medians,
multi-occurrence counts, plural-only counts, cross-concept naming counts, and all fifteen leakage
hits. **The harm sentences did not change**; the rewrite was content-neutral for everything
measured here (a 176-byte `_meta` change is the likely explanation). Every number in §6–§9 above
is from the **03:02:18** version, hashes as listed in §1.

The point is not that a number moved — none did. The point is that **the corpus this review
covers is not pinned by anything committed.** `PR-046` pins `ts116n` and the `ts` pools;
`ts116m`, `tsm` and `cand` are pinned by nothing, are untracked, and demonstrably change under a
concurrent writer. A reviewer four hours from now cannot reproduce this section.

---

## 12. WHAT I COULD NOT ESTABLISH

- **The population of `A-041`'s leakage figure (72/3,864 → 8/1,380).** Neither denominator
  matches the train/test population, the all-pairs population, or the per-concept pool sizes I
  can construct. *Needed:* the emitting call site in `scripts/dcs_ts116n_audit_leakage.py` and
  its row selection. §6.
- **Whether the 115-domain exclusion is enforced anywhere.** I found it declared in
  `configs/dcs_ts_pr046.json` and honoured arithmetically in the log's denominators, but no code
  path in the reviewed range reads it. *Needed:* the analyzer, which does not exist yet. §1.
- **Whether `ts116m` supersedes `ts116n` as the analysis population.** The artifacts say it
  should; nothing written says it does. *Needed:* an explicit successor preregistration entry. §10.
- **`N4` on the rebuilt bank.** No probe has been run, no hidden state exists. §8 bounds the
  residual length gap but cannot predict the statistic, and I make no claim about it.

---

## 13. VERDICT BY TASK ITEM

| # | item | verdict |
|---|---|---|
| 1 | exact domain count, every pools file and bank | **116 everywhere** — table §1; 115 is an analysis-time subtraction no artifact enforces |
| 2 | split disjointness, 70/23/23, rebuild from seed 202609061, no domain twice | **CONFIRMED, 6/6 checks, 116/116 rebuild match** — §2 |
| 3 | `bank_rows_sha16` vs `pr046` and vs each `_meta.json` | **CONFIRMED, 12/12 agree, 0 disagreements** — §3. But `PR-046` pins the superseded bank |
| 4 | rows per domain/cell/query_kind/n_examples/concept; any domain missing a concept | **EXACTLY BALANCED**, 4,176 four-way cells, **no domain missing anything** — §4 |
| 5 | duplicate `prompt_id`; duplicate `full_prompt` within `(cell, qk, concept)` | **0 and 0**, across 133,632 rows — §5 |
| 6 | TEST harm sentences verbatim in TRAIN, per concept, `ts116n` and `tsm` | `ts` **3/2,760 (0.109%)**; `tsm` **15/2,760 (0.543%)** — **5× worse after regeneration** — §6 |
| 7 | `C-076`: zero multi-occurrence in `cand`/`tsm`; detector proven on old pools | **CONFIRMED. 0/34,800 in the new pools; the 8 knife failures reproduce exactly in the old** — §7. Plus §7.4 headroom and §7.5 undocumented `C-079` |
| 8 | length match, 7.09 → 4.17 (41.2%) | **DIRECTION CONFIRMED, NUMBERS REFUTED: 7.04 → 4.16 = 40.9%** on the script's own baseline; **6.52 → 4.16 = 36.2%** vs the old `ts` pools — §8 |
| 9 | is `restaurant_kitchen` clean in the new pools | **YES — 0/40 on all three concepts. The exclusion is now conservative, not necessary.** Keep it anyway (preregistered, costs 1 TRAIN domain); fix the config's stale reason text — §9 |
