# DCS-TS116N — ADVERSARIAL AUDIT OF THE ALIGNED CONCEPT BANK

**Mandate section 24. Target: the ts116n bank family (built 2026-09-07, entry R-101) and the
claim `DCS-PR-046` would put in front of Matan.**
Read-only audit. CPU only, no GPU, no model weights, no network (Llama-3.1-8B **tokenizer** only,
loaded offline from the local hub cache). Nothing outside this file was written; nothing was
staged or committed.

Analysed population, everywhere below unless stated otherwise:
`cell == "C"` × `query_kind == "semantic_one_word"` × `n_examples == 4`, **115 domains**
(`restaurant_kitchen` excluded per the frozen preregistered prompt-only exclusion),
**1,150 rows per concept arm per codeword**, 3,450 rows per codeword, 69 train / 23 validation /
23 test domains.

---

## 0. THE CLAIM UNDER ATTACK

> "In ts116n, for every matched domain, family, codeword and demonstration count, the prompt is
> byte-identical across bomb, knife and gun in everything except the harmful demonstrations,
> which are independently and naturally generated to install their own concept. Cell C differs
> across concepts in 115/115 domains while cell A is byte-identical in 3680/3680 rows. A probe
> trained on 69 held-out-by-domain train domains and evaluated on 23 untouched test domains
> therefore measures the identity of the installed concept in the codeword representation."

**VERDICT: the first two sentences are TRUE and I could not break them. The third sentence — the
one after "therefore" — is REFUTED.** The word "therefore" does not survive contact with the
bank. Three independent surface channels each recover the concept label from the raw prompt text
on the 23 untouched test domains, with no model involved:

| text-only classifier, 69 train domains → 23 untouched TEST domains | TEST domain-mean acc | chance |
|---|---|---|
| N5 concept-masked TF-IDF over the demo block (the preregistered N5) | **0.8884** | 0.3333 |
| a **23-word, 3-line hand-written regex** | **0.7942** | 0.3333 |
| **function words only** — every content word deleted | **0.7391** | 0.3333 |
| N4 length-only (4 length features, no text at all) | **0.5319** | 0.3333 |

All four are significant at the domain-level group permutation floor (`p < 1/(B+1) = 9.999e-05`,
B = 10,000). The third row is the one that matters: with *every content word removed* — no nouns,
no verbs, no concept words, no synonyms, only determiners, prepositions, auxiliaries and
punctuation — the concept label is still 73.9 % recoverable on domains the classifier has never
seen. **The three arms differ in discourse register, not only in which concept they name**, and
"the identity of the installed concept" is not what a probe that beats chance has been shown to
be reading.

---

## 1. WHAT I COULD NOT BREAK (integrity and alignment)

Every one of these re-derives from the raw `.jsonl` bytes, not from a producer-written summary
field.

**1.1 Provenance verifies bit-for-bit.** All six banks recompute to their published
`bank_rows_sha16` *and* `bank_file_sha16`:

| bank | rows | recomputed rows_sha16 | matches PR-046 |
|---|---|---|---|
| `ts116n_button_bomb`  | 22,272 | `9d1f03747189e1bd` | ✅ |
| `ts116n_button_knife` | 22,272 | `9ef9688609001104` | ✅ |
| `ts116n_button_gun`   | 22,272 | `b865d8b991023ac7` | ✅ |
| `ts116n_basket_bomb`  | 22,272 | `09882763cb4b0a24` | ✅ |
| `ts116n_basket_knife` | 22,272 | `71128bfa7631c005` | ✅ |
| `ts116n_basket_gun`   | 22,272 | `ab5ec1d45fb90cd3` | ✅ |

`prompt_sha16 == sha256(full_prompt)[:16]` in **133,632 / 133,632** rows, so `rows_sha16` really
does cover prompt content and not just row identity. The split manifest recomputes to
`be7d2c772d814ef3` (sha256 of the body minus `manifest_sha16`, `sort_keys`, compact separators)
and assigns 70/23/23 over 116 domains, with `restaurant_kitchen` and `school_campus` both in
train exactly as the PR states.

**1.2 Pool alignment is exact.** For each concept, **348 / 348** non-harm pools (benign, remap,
filler) are byte-identical to `demo_pools_116dom.json`; **116 / 116** harm pools differ. 0 keys
missing in either direction.

**1.3 Structural alignment is exact — the manipulation is confined to the demo block.**
At each of the 1,150 matched `prompt_id`s, splitting `full_prompt` on `demo_block`:

| | button | basket |
|---|---|---|
| prefix (preamble) byte-identical across bomb/knife/gun | **1150 / 1150** | **1150 / 1150** |
| suffix (query) byte-identical across bomb/knife/gun | **1150 / 1150** | **1150 / 1150** |
| demo block differs across all three arms | **1150 / 1150** | **1150 / 1150** |

The read site is aligned too: the last whole-word codeword occurrence sits exactly **25 characters
from the end of the prompt in all 3,450 rows of every arm** — i.e. it is the occurrence inside the
byte-identical query, not inside the demo block.

**Mutation (must go RED):** flipping one character in one of the 1,150 knife-arm prefixes takes
the prefix check from 1150/1150 to **1149/1150**. ✅ RED.

**1.4 Class balance and missing rows: clean.** All **36** `(cell, query_kind, n_examples)` combos
are present in all **696** `(codeword, concept, domain)` cells with an *identical* per-cell row
count (2 at n=0, 10 at n=4, 4 at n=8) — 0 missing cells, 0 ragged cells. `prompt_id` is unique
within each bank (22,272/22,272) and the `prompt_id` **set is identical across all six banks**.
In the primary cell, 0/1,160 matched ids have two arms sharing a `prompt_sha16`, and each arm has
1,160/1,160 distinct prompts. **NOT-A-DEFECT.**

**1.5 N6 (template-id-only) is at chance by construction.** `family_id` is identical across the
three arms at **1150/1150** matched ids. Any above-chance N6 would mean alignment is broken.

**1.6 The literal concept word never appears at the codeword surface.** In the primary cell,
`\bbomb\w*` / `\bgun\w*` return **0 / 1,150** rows in their own arms and 0 in the others.
(The knife arm is the exception — see F1.)

---

## 2. FINDINGS, RANKED

### F1 — CRITICAL. The demonstrations name their own concept by synonym in 308 / 3,450 primary rows (8.9 %), in 96 / 115 domains, and in 22 / 23 test domains. `G1` and `N3` as written do not see it.

`G1` checks *whole-word* `bomb` / `knife` / `gun`. The generation is natural English, so it reaches
for the category by a different word. Counted on the **demo block only** (the sole channel that
differs across arms), primary cell, 115 domains:

| arm | rows naming **its own** concept category | domains | TEST domains | the words |
|---|---|---|---|---|
| bomb  | **39 / 1150 (3.39 %)** | 31 / 115 | 6 / 23 | `explosives` 23, `explosive` 14, `detonator` 2, `grenade` 1 |
| knife | **147 / 1150 (12.78 %)** | 95 / 115 | 19 / 23 | `blade` 135, `blades` 9, **`knives` 8** |
| gun   | **122 / 1150 (10.61 %)** | 80 / 115 | 18 / 23 | `holster` 52, `firearms` 33, `firearm` 28, `ammunition` 12, `holstered` 5 |

By dsplit: bomb 21 train / 9 val / 9 test; knife 83 / 33 / 31; gun 65 / 30 / 27.

**A three-line synonym rule** (predict the arm whose category lexicon fires) fires on **313 / 3,450
rows (9.1 %)** and is **97.76 %** correct where it fires — 0.9826 train, 0.9726 validation,
**0.9706 on test (66/68)**. On those rows the label is simply written in the prompt.

**The 8 `knives` rows are a hard `N3` violation, not a synonym.** The build substitutes the concept
whole-word singular, so the irregular plural survives verbatim beside the codeword:

```
POOL knife blood_bank      (train)      "The knife rack was overcrowded, making it difficult to access clean knives."
POOL knife blood_bank      (train)      "The knife wash station was clogged, preventing proper cleaning of the knives."
POOL knife blood_bank      (train)      "The knife sharpening station was not functioning properly, leading to dull knives in use."
POOL knife care_home_store (train)      "Several knives were missing from the designated knife block in the supply room."
POOL knife cheese_dairy    (train)      "The knife block in the maturing room contained only sterilized knives."
POOL knife hospital_supply (validation) "The knife sharpener was located next to the supply of sterile knives."
POOL knife instructional   (test)       "For industrial settings, ensure that knives are stored in knife blocks or magnetic strips."
POOL knife physio_gym      (test)       "The knife rack was noted as disorganized, with several knives not in their designated spots."
```

In the bank these render as e.g. *"The **button** rack was overcrowded, making it difficult to
access clean **knives**."* — immediately above the query *"what does the word button actually
refer to?"*. 90 rows per knife bank carry `knives`; **8 of them are in the primary cell** (5 train,
1 validation, **2 test**: `instructional`, `physio_gym`), and both knife banks are affected
identically. PR-046 `N3` says "0 rows name their own concept in the primary channel". The measured
value is **8**, not 0. PR-046 `G1` says "every harm sentence carries exactly one whole-word target
concept and no other concept"; these eight carry two.

*Why CRITICAL rather than MAJOR:* it is not the effect size (masking the 30 synonyms leaves the N5
test accuracy at 0.8884, unchanged to four decimals — see F2, the leak is **not** what drives the
signal). It is that a preregistered null is stated as an exact zero, the gate that should catch it
is a whole-word match on three singular nouns, and the population it fails on includes 22 of the
23 test domains. A gate that reports 19/19 PASS while 8.9 % of the analysed rows name their own
class in plain English is the same failure mode as `C-074`: the check could only fail in one
direction. **It has to be re-run with a category lexicon before extraction, and the `knives` rows
have to be regenerated or the sentences dropped.**

*Mutations (must go RED):* the same scan with an empty lexicon returns **0** hits (not
self-fulfilling); planting `"A pistol was present."` into 5 clean gun rows moves the count
**122 → 127**, exactly +5. ✅ both RED.

### F2 — CRITICAL. The probe's bar is not 1/3, it is 0.8884 — and 0.7391 of it is pure syntactic register with every content word deleted.

Domain-grouped, fit on the 69 train domains, evaluated once on the 23 untouched test domains,
multinomial logistic regression on TF-IDF (1–2 grams, `min_df=2`, sublinear tf) of the demo block:

| view of the text | validation | **TEST domain-mean** | test domains > chance |
|---|---|---|---|
| mask `bomb/knife/gun/button/basket` only (= preregistered N5) | 0.9174 | **0.8884** | 23 / 23 |
| **+ mask 30 synonyms and hypernyms** (F1's lexicon) | 0.9188 | **0.8884** | 23 / 23 |
| **+ collapse every remaining content word to `X`** | 0.7116 | **0.7290** | 23 / 23 |
| **function words only, content words deleted entirely** (1–3 grams) | — | **0.7391** | 23 / 23 |

Domain-level group permutation on the test set (independently relabelling the three classes within
each test domain, B = 10,000): **p = 9.999e-05, which is the attainable floor** — report as
`p < 1/(B+1)`, never as a measurement.

What the register-only view actually contains:

```
bomb   The X X a X X was X X the X X X An X X X X was X in the X of the X X X X were X to X all ...
knife  A X X X was X in the X X X X X An X X that a X was X from the X X X X The X X was X X to ...
gun    The X X a X X was X from the X X A X X X was X X the X X X X X X X X a X X X for X X in ...
```

Two consequences.

1. **Masking the synonyms costs nothing (0.8884 → 0.8884).** F1 is a real defect but it is not the
   mechanism. The mechanism is that bomb, knife and gun demonstrations are written in three
   different *genres*, and the genre is legible in the function-word skeleton alone.
2. **The preregistration's own bar is met by the null, not by the probe.** PR-046 says
   "N5 concept-masked TF-IDF becomes strong and the probe MUST beat it." The bar is **0.8884 on
   test**, and 0.8884 is 83 % of the way from chance to ceiling. A probe reading 0.90 would clear
   it by 0.012 with a projected between-domain SD of 0.1406 and an MDE of 0.0925 — i.e. the
   phase is, as designed, powered to detect a 0.0925 move above 1/3 and *not* powered to detect
   the move above 0.8884 that the claim actually requires. **The reported success criterion
   ("significantly above 1/3") is the wrong criterion for the claim it is attached to.**

*Mutation (must go RED):* shuffling the labels before fitting collapses the register classifier to
**0.3174** and the N5 classifier to **0.3087**. ✅ RED. A constant feature gives exactly 0.3333.

### F3 — MAJOR. N4 fails its preregistered expectation. Length-only is 0.5319 on test, not "at chance", and PR-046's own deferred decision rule therefore fires.

PR-046 `nulls_required` N4: *"length-only classifier — expect: at chance."*

Measured, domain-grouped, 69 train → 23 untouched test domains, logistic regression on four
length features (`ntok_full`, `ntok_demo`, `nchar_full`, `nchar_demo`; Llama-3.1-8B tokenizer):

| feature set | validation | **TEST domain-mean** | test domains > chance |
|---|---|---|---|
| `ntok_full` alone | 0.3464 | 0.3841 | 12 / 23 |
| `ntok_demo` alone | 0.3507 | 0.3420 | 12 / 23 |
| `nchar_full` alone | 0.4058 | 0.4174 | 12 / 23 |
| `nchar_demo` alone | 0.4507 | 0.4551 | 15 / 23 |
| chars-per-token of the demo block | 0.5261 | 0.5000 | 19 / 23 |
| **all four length features** | 0.5464 | **0.5319** | **21 / 23** |

Domain-level group permutation, B = 10,000: **p = 9.999e-05 (floor)**.

Note *where* it comes from. Raw token length is a weak signal — `ntok_full` gives
η² = 0.0028 (bomb 197.20 ± 12.49, knife 195.59 ± 12.28, gun 196.74 ± 13.58; Cohen's d
bomb−knife +0.129, bomb−gun +0.035, knife−gun −0.089) and `ntok_demo` η² = 0.0109 (60.76 ± 6.85 /
59.15 ± 5.72 / 60.31 ± 6.77; d +0.255 / +0.067 / −0.184). Single-token-length classifiers are
duly near chance. The 0.53 comes from **characters per token** — bomb demonstrations use longer
words — which is a register statistic wearing a length costume. `button` and `basket` are both
single tokens, so every length number above is bit-identical between the two codewords.

**PR-046 records the remedy in advance and it is now triggered:** *"If N4 length-only comes out
well above chance, over-generate and length-match the 40 kept sentences per pool — prompt-only and
outcome-blind."* 0.5319 against 0.3333, +0.1986, is more than twice the phase MDE of 0.0925. The
rule was written before the measurement precisely so it could not be argued away afterwards. **It
should be executed before extraction.** I note that length-matching alone will not fix F2:
deleting length entirely (function-words-only view, no `X` placeholders) still gives 0.7391.

*Mutation (must go RED):* a constant feature gives **0.3333** exactly. ✅ RED.

### F4 — MAJOR. The register asymmetry is real, is larger than PR-046 says, and the published hedging rate is not reproducible from the recipe printed next to it.

PR-046 `_register_asymmetry` publishes `hedged_pct = {bomb 14.1, knife 0.2, gun 3.4}` and names the
lexicon: *"resembl\*, simulat\*, drill, false alarm, looks like"*. Measured on the stated
denominator (4,640 harm sentences per concept, 116 domains — reproduced exactly) that lexicon gives:

| | bomb | knife | gun |
|---|---|---|---|
| PR-046 published | 14.1 % | 0.2 % | 3.4 % |
| the PR's own 5-pattern lexicon, 4,640 sentences | **11.27 %** | **0.11 %** | **2.72 %** |
| the full 15-pattern `HEDGES` list in `scripts/dcs_ts_audit_concept_backing.py` | 18.21 % | 0.45 % | 4.78 % |
| the same, on the 4,640 demo sentences actually emitted into the primary cell | 11.21 % | 0.11 % | 2.72 % |

The other two published numbers **do** reproduce exactly — mean sentence chars bomb 82.0 (sd 11.0)
/ knife 75.5 (9.4) / gun 78.3 (11.4), and the mass-noun frame `a <W> of <NOUN>` 1.08 % / 0.00 % /
0.00 % on 116 domains. Only the hedging row does not, and no subset of the audit script's lexicon
that I could find lands on (14.1, 0.2, 3.4). A frozen preregistration that publishes a number no
stated recipe reproduces is the `feedback_published_threshold_never_enforced` pattern again.
On the 115 analysed domains the figures are 11.22 / 0.11 / 2.70 (narrow) and 18.17 / 0.46 / 4.74
(full).

**More importantly, the PR published the smaller of the two asymmetries.** Sentence-level rates,
115 analysed domains, 4,600 harm sentences per concept:

| frame | bomb | knife | gun |
|---|---|---|---|
| threat / alarm (`threat`, `scare`, `evacuat*`, `alert`, `hoax`, `suspicious`) | **41.07 %** | **0.41 %** | **3.83 %** |
| injury / cut (`cut*`, `sharp*`, `blade*`, `dull`, `laceration*`, `injur*`) | 0.37 % | **16.87 %** | 0.61 % |
| unreality (`toy`, `fake`, `prop`, `replica`, `mistaken`, `imitation`, `decorative`, `not a real`) | 2.78 % | 0.43 % | **5.89 %** |
| generic weapon (`weapon*`, `armed`) | 0.00 % | 0.04 % | **0.59 %** |
| hedging (PR lexicon) | 11.22 % | 0.11 % | 2.70 % |

The threat/alarm frame is a **100× gap** between bomb and knife and it is three times the size of
the hedging gap the PR chose to publish. There is also a syntactic-position asymmetry the PR does
not mention at all: characters between the *last* codeword in the demo block and the end of that
block are bomb 29.67 ± 20.98, knife 56.80 ± 20.61, gun 41.63 ± 21.75 — **Cohen's d bomb−knife
= −1.305**, by far the largest single effect in the bank. Bomb demonstrations put the codeword
late in the clause ("*a **button** threat was reported*"), knife demonstrations put it early with a
long tail ("*a **button** was found on the floor near the history section*"). This does not move
the read site (§1.3), but it changes the local syntactic context the read site attends back to.

The PR's decision to keep the asymmetry rather than match it away is defensible and I am not
arguing with it. What is not defensible is publishing 14.1 % as *the* size of the effect when the
same corpus carries a 41.07 % / 0.41 % frame the audit never looked for.

### F5 — MAJOR. Domain independence is not better than before. The 0.752 that the previous audit criticised came from the *shared* channels, which ts116n carries forward byte-for-byte.

Re-measured with the previous audit's statistic (TF vocabulary cosine over each domain's demo
sentences, stopwords and the concept word dropped, 6,555 pairs over 115 domains):

| corpus | median | mean | p90 | max | train↔test pairs (n=1,587) |
|---|---|---|---|---|---|
| ts116n harm, **bomb** | 0.3980 | 0.3829 | 0.5012 | 0.6380 | mean 0.3860 / max 0.6131 |
| ts116n harm, **knife** | 0.4125 | 0.4074 | 0.5481 | 0.7438 | mean 0.4145 / max 0.6719 |
| ts116n harm, **gun** | 0.3351 | 0.3386 | 0.4898 | 0.7166 | mean 0.3327 / max 0.6297 |
| old shared harm (the pool ts116n replaced) | 0.3732 | 0.3590 | 0.4950 | 0.7386 | mean 0.3658 / max 0.6381 |
| **shared benign** (byte-identical in all six ts116n banks) | **0.7864** | 0.7780 | 0.8386 | 0.9019 | mean 0.7845 / max 0.9013 |
| all valences, ts116n bomb arm | 0.6570 | 0.6542 | 0.7398 | 0.8479 | mean 0.6566 / max 0.8230 |
| all valences, old pools (**the previous audit's 0.752**) | 0.7235 | 0.7192 | 0.7935 | 0.8824 | mean 0.7239 / max 0.8646 |

So: the previous audit's headline 0.752 was an **all-valence** number, and it was dominated by the
**benign** pool at 0.7864 — which ts116n copies over unchanged. Per-concept independent generation
moved the harm third from 0.3732 to 0.335–0.413, i.e. **essentially nowhere**, and moved the
all-valence figure from 0.7235 to 0.6570 only because the harm third got slightly more varied.
**"The domains were never independent to begin with" survives ts116n intact.** In neither the old
nor the new pools is the split adversarial — train↔test cosines track the overall distribution —
but 30 domain pairs share a name token and straddle train/test, covering **13 of the 23 test
domains** (`bakery_plant`, `brewery_works`, `feed_mill`, `hotel_laundry`, `hydro_station`,
`lab_safety`, `laundrette_unit`, `lifeboat_station`, `pharmacy_store`, `tannery_works`,
`tram_depot`, `veterinary_clinic`, `wind_farm`), unchanged from the previous audit because the
split manifest is the same file.

Verbatim sentence sharing across domains **improved** and is now negligible: bomb 9 sentences in
>1 domain (6 straddling dsplits), knife 9 (4 straddling), gun 2 (1 straddling), against 11 (9
straddling) in the old shared harm pool — out of 4,600 sentence slots each.

### F6 — MAJOR (interpretive, not a bug). At the level of a single demo block, "which concept" is a *weaker* lexical axis than "which domain". The classifier wins on consistency, not on distance.

Jaccard over content words of two demo blocks (primary cell, `button`, 115 domains):

| pair type | n | mean J | median J |
|---|---|---|---|
| same domain, **same** concept, different draw from the same 40-sentence pool | 15,525 | **0.0849** | 0.0800 |
| same domain, **different** concept | 3,450 | **0.0724** | 0.0615 |
| different domain, same concept | 2,970 | 0.0500 | 0.0429 |
| different domain, different concept | 990 | 0.0314 | 0.0227 |

Changing the concept at a fixed domain costs only 0.0125 of Jaccard; changing the domain at a
fixed concept costs 0.0349 — nearly three times as much. Two demo blocks from the same concept and
domain are already 91.5 % lexically disjoint. The reason a 3-line regex nonetheless reaches 0.79 is
not that the arms are far apart, it is that the few words that *do* separate them (`threat`,
`scare`, `blade`, `dull`, `holster`, `toy`) recur in the same role across all 115 domains while
the domain vocabulary does not. This is exactly the property that makes the surface baseline
transfer to unseen domains — and it is exactly the property a hidden-state probe would also
exploit.

At matched `prompt_id`, cross-arm demo-block similarity: token Jaccard mean 0.1431 (bomb–knife) /
0.1552 (bomb–gun) / 0.1646 (knife–gun), max 0.4773; character `SequenceMatcher` ratio mean
0.2829 / 0.2890 / 0.3021, max 0.6700. Verbatim sentence sharing between arms at a matched id:
**3 of 13,800 sentence slots**. So `G2`'s "differs in 115/115" understates the situation: the arms
do not differ *slightly*, they share ~14 % of their vocabulary. **The manipulation is not "the
concept", it is "the whole demonstration text".** `G3a` did not miss anything (§1.3) — but `G2`
passing is compatible with an arbitrarily large confound, and nothing in the gate suite bounds it.

### F7 — MINOR. Cross-*concept* semantic contamination outside `restaurant_kitchen` is small but non-zero, and one instance is in validation.

Excluding `restaurant_kitchen`, the strict whole-word cross-concept check is clean:
**0 / 13,800 sentences** name a different concept by its own word (the only two hits in the whole
corpus, one in the bomb pool and one in the gun pool, are both `restaurant_kitchen` — the PR's
justification for the exclusion reproduces exactly). Extending to synonyms and hypernyms, the
genuine hits after manual adjudication are:

| pool | domain | dsplit | sentence |
|---|---|---|---|
| knife | `mountain_rescue` | train | "A knife should always be carried in a **holster** for safety." |
| knife | `plastics_moulding` | train | "An unused knife should be placed back in the **holster** after every use." |
| knife | `solar_array` | train | "The team agreed that a knife should always be returned to its **holster**." |
| knife | `mountain_rescue` | train | (`gunfire`, 1 primary row) |
| gun | `game_manual` | validation | "Using the gun in tandem with **explosives** can create a powerful combination." |

That is 5 sentences, 4 of them train, 1 validation, **0 in test**. Everything else my lexicon
flagged is a false positive of the matcher, not contamination — `blade`/`blades` in the bomb pool
(`joinery_shop`: "a broken **blade** on the saw") and the gun pool (`helipad_base`: "near the rotor
**blades**"), and `magazines` in the knife pool (`library_stacks`: reading magazines). I report the
adjudication rather than the raw count because the raw count is exactly the
`feedback_matcher_scope_bug_class` trap: a loose lexicon over-credits.

**Is one excluded domain enough?** For *cross-concept* contamination, yes — the answer is 5
train/validation sentences, and no test domain is affected. For *own-concept* contamination it is
emphatically not: F1's 96 contaminated domains dwarf the one that was excluded, and they were
never looked for. `restaurant_kitchen` was excluded for having a knife in the bomb pool; nobody
checked whether the knife pool has a blade in it. It does, in 95 of 115 domains.

Separately, the generic weapon frame is asymmetric: `weapon*`/`armed` appears in **27 / 1,150**
gun-arm primary rows (22 domains) versus 2 knife-arm and **0** bomb-arm. It is a gun-specific
register marker rather than cross-contamination, and it is already counted inside F1/F4.

### F8 — MINOR. `basket` collides with a *new* substring in ts116n that the frozen `school_campus` exclusion does not cover, and the collision is arm-asymmetric.

`n_codeword_occurrences` is substring-based. Re-counting whole-word `\bbasket\b`:

| bank | rows where the field over-counts | cause | dsplit |
|---|---|---|---|
| `basket_bomb` | 60 / 22,272 | `school_campus` → "basketball" | train |
| `basket_gun` | 60 / 22,272 | `school_campus` → "basketball" | train |
| `basket_knife` | 60 + **12** / 22,272 | `school_campus` → "basketball"; **`library_stacks` → "wastebasket"** | train; **validation** |

The `library_stacks`/`wastebasket` collision is new — it comes from the regenerated knife harm pool
and exists in **no other arm**. PR-046's `school_campus` exclusion is scoped to
"occurrence-ordinal and all-codeword-sites knockout analyses" and names only `school_campus`.
`library_stacks` is in **validation**, so it is inside the hyperparameter-selection population for
any codeword-site analysis, and because it is knife-only, a cross-arm knockout comparison at
`library_stacks` is not matched. 3 of the 12 rows are in the primary cell of `basket_knife`. It
does **not** move the probe's read site (the last codeword occurrence is always the query one,
§1.3), so the probe is unaffected. The exclusion list should be widened to
`{school_campus, library_stacks}` for the knockout analyses, or the counter should be made
whole-word.

### F9 — NOT-A-DEFECT (checked and clean)

- `G2` / `G3a` / `G3b` reproduce (§1.3): 1150/1150 aligned, 1150/1150 differing, in both codewords.
- Class balance, missing rows, duplicate ids, cross-arm prompt collisions: all clean (§1.4).
- `N6` template-id-only is at chance by construction (§1.5).
- No residual morphology of the substituted concept except `knives` — `\bbomb\w*` and `\bgun\w*`
  return 0 rows in the primary cell of every arm, so `bombing`, `gunfire`, `gunshot`, `gunman`
  never survive substitution in their own arm.
- The read site is byte-aligned: last codeword occurrence exactly 25 chars from the end in
  3,450/3,450 rows of each arm.
- `button` and `basket` are both single Llama-3.1 tokens (ids 2208 and 60864), and every length
  statistic is bit-identical between the two codewords.
- The harm-pool regeneration did **not** make cross-domain verbatim reuse worse; it improved
  (F5, 9/9/2 sentences vs 11).

---

## 3. ATTACK 7 — THE STRONGEST VERSION OF "THE PROBE WILL READ REGISTER, NOT CONCEPT IDENTITY"

**The argument.** Three text-only facts are now measured, all on the 23 untouched test domains,
all at the permutation floor:

1. Deleting every content word from the demonstrations still yields **0.7391**. Whatever
   distinguishes the arms is carried by clause structure, voice, tense, determiner and preposition
   distribution — the definition of register.
2. Masking the concept words *and* 30 synonyms and hypernyms changes N5 by **0.0000**
   (0.8884 → 0.8884). The signal does not live in any word that denotes the concept.
3. The corpus-level asymmetry is a genre asymmetry, not a lexical one: 41.07 % of bomb
   demonstrations are in the threat/alarm frame against 0.41 % of knife; 16.87 % of knife
   demonstrations are in the injury/cut frame against 0.37 % of bomb; the codeword sits 1.3 SD
   later in the clause in bomb than in knife.

A hidden state at the codeword in a Llama-3.1 middle layer is, among other things, a summary of
the preceding discourse. A linear probe that separates these three arms at layer 6–14 is therefore
consistent with two entirely different generative stories:

- **(A) concept identity** — the codeword's representation has been bound to the semantic entry for
  *bomb* / *knife* / *gun*, and the probe reads that binding; or
- **(B) discourse register** — the codeword's representation carries "this document is a
  threat-report" vs "this document is a sharps-safety notice" vs "this document is a
  weapons-policy notice", and the probe reads *that*.

Nothing in PR-046's primary statistic separates (A) from (B). Worse, the two are *positively
confounded by design*: the PR explicitly kept the register asymmetry on the grounds that "a bomb in
a workplace is overwhelmingly a SUSPECTED bomb", which is a statement that concept and register are
the same variable in this corpus. An above-chance probe is then uninformative about which one the
model encoded, and the honest reading of a 0.90 probe against an 0.8884 text baseline is "the probe
recovers what a bag of function words already recovers".

**What would distinguish them. Three experiments, in order of decisiveness.**

**E1 — Register-transfer, the decisive one (GPU, no new generation, ~1 extraction run).**
Build a fourth arm by **crossing register with concept**: take the bomb *predicates* and install the
*knife* concept in them, and vice versa — 40 sentences per domain per cell, generated by the same
generator at the same seed with an explicit frame instruction ("write these as incident-log threat
reports" / "as sharps-safety notices"). This yields six cells: (concept ∈ {bomb, knife}) ×
(register ∈ {threat, sharps, neutral}). Train the probe on the *natural* cells only and test on the
*crossed* cells. If the probe follows the **concept** into a foreign register it is reading (A);
if it follows the **register** it is reading (B). This is the only design that dissociates them,
because it breaks the correlation rather than measuring around it. It is prompt-side work — no new
mechanism, no new analyser — and it is the experiment I would spend the API budget on.

**E2 — The register-matched null, cheap and immediate (CPU, today).**
Fit the *function-word-only* classifier from F2 on train, freeze it, and record its **per-row
posterior** on every validation and test row. Then, in the frozen analyser, report the probe's
accuracy **stratified by, and additionally conditioned on, that posterior** — and report the probe's
partial accuracy on the subset of test rows where the register classifier is *wrong*. If the probe
is at chance exactly where register is uninformative, it is (B). This costs nothing, needs no new
generation, and can be preregistered before the test read. **It should be added to PR-046 as N9
before extraction.**

**E3 — The bar correction (analysis-only).**
Change the primary success criterion from "significantly above 1/3" to "significantly above the
**frozen, train-fit, text-only baseline**" — 0.8884 for N5, and the domain-level paired
permutation of (probe accuracy − N5 accuracy) at matched test domains as the statistic. The
current criterion cannot fail: N4 at 0.5319 and a 23-word regex at 0.7942 both already "succeed"
under it, and neither involves a model. Power must then be recomputed against the corrected MDE;
with the phase's own SD projection (0.1406) and 23 test domains, an 0.0925 MDE sits on top of an
0.8884 floor, i.e. the design as it stands is powered to detect an effect that would have to reach
0.98.

---

## 4. WHAT I TRIED AND COULD NOT BREAK

Listed so the null attacks are on the record and are not re-run.

- Reproducing all six `bank_rows_sha16`, all six `bank_file_sha16`, the split `manifest_sha16`, and
  `prompt_sha16` on all 133,632 rows — all match.
- Finding a matched `prompt_id` where the arms differ *outside* the demo block — 0 of 2,300
  (both codewords).
- Finding a matched `prompt_id` where two arms share a prompt — 0 of 1,160.
- Finding a missing or ragged `(codeword, concept, domain, cell, query_kind, n_examples)` cell —
  0 of 25,056 cell-combinations.
- Finding a non-harm pool that is not byte-identical to `demo_pools_116dom.json` — 0 of 1,044.
- Finding a harm pool that is identical across concepts — 0 of 348.
- Finding a duplicate `prompt_id` — 0 of 133,632.
- Finding residual `bomb*` / `gun*` morphology surviving the codeword substitution — 0 rows.
  (`knives` is the sole survivor; see F1.)
- Finding a read-site misalignment — the last codeword occurrence is 25 chars from the end in
  every row of every arm.
- Finding an adversarially hard train/test split — train↔test cosine tracks the within-split
  distribution in every concept.
- Finding whole-word cross-concept contamination outside `restaurant_kitchen` — 0 of 13,800.
- Finding that the harm-pool regeneration worsened cross-domain verbatim reuse — it improved it.

---

## 5. BOTTOM LINE FOR MATAN

The bank is **built correctly and is worth using**. The alignment claim is exact and I could not
dent it: the arms are byte-identical everywhere except the demonstrations, the pools are shared
where they should be shared, the hashes verify, and the row grid is complete. `C-074` is genuinely
fixed and none of the old degenerate-at-chance numbers should be carried forward.

But **the sentence beginning "therefore" must be deleted before this goes to a collaborator.** As
written it is refuted by four measurements on the untouched test domains, none of which involve a
model. The defensible version is:

> "…A probe trained on 69 held-out-by-domain train domains and evaluated on 23 untouched test
> domains measures whatever distinguishes the three demonstration corpora at the codeword. On this
> bank that includes the installed concept **and** a large, deliberately retained discourse-register
> asymmetry: a concept-masked TF-IDF baseline reaches 0.8884 on the same test domains, a 23-word
> regex reaches 0.7942, a length-only classifier reaches 0.5319, and a classifier with every
> content word deleted still reaches 0.7391. The probe's result is interpretable as concept
> identity only against those baselines, and only after the register-transfer control (E1) or the
> register-conditioned null (E2)."

Three things should happen **before** extraction, all prompt-side and all outcome-blind:

1. **Fix F1.** Regenerate or drop the 8 `knives` sentences, and re-run `G1` with a category
   lexicon (`explosive*`, `detonator`, `grenade`, `blade*`, `cleaver`, `machete`, `firearm*`,
   `holster*`, `ammunition`, `pistol`, `rifle`, `sidearm`, `weapon*`) rather than three singular
   nouns. 308 primary rows in 96 domains currently name their own class.
2. **Execute the F3 remedy that PR-046 already committed to** — length-match the 40 kept sentences
   per pool. N4 = 0.5319 against a 0.0925 MDE.
3. **Add N9 (register-conditioned null, E2) to the preregistration and correct the success
   criterion to E3** — "above 1/3" is a criterion that a regex passes.

The one thing that cannot be fixed prompt-side is F2/F6: concept and register are the same variable
in naturally generated incident-log English, and no amount of masking separates them. Only the
crossed design (E1) does.

---

### Reproduction

Everything above was computed from the raw bank `.jsonl` bytes and the pool JSONs; no
producer-written summary field was trusted except where explicitly compared against a recount.
Scripts used for this audit live in the session scratchpad and are not committed (this audit is
read-only). Classifier settings, stated once: multinomial logistic regression, `max_iter` 3000–5000,
`C = 1.0`, `TfidfVectorizer(ngram_range=(1,2), min_df=2, sublinear_tf=True)` except the
function-word view which uses `(1,3)`; features standardised for the length models; **fit on the 69
train domains only**, no domain ever split across train and test; domain-mean accuracy as the
statistic; group permutation by independently relabelling the three classes within each test
domain, B = 10,000, attainable floor 9.999e-05. Every check above binds a stated non-zero row
count, and the four that could conceivably be self-fulfilling were demonstrated RED under a
deliberate mutation (§1.3, F1, F2, F3).
