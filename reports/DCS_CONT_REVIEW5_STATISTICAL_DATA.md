# DCS-CONT REVIEW-5 — STATISTICAL + DATA

Scope: what landed **since** `REVIEW-4` — `CONT-ENTRY 096`–`103`, plus the artifacts
`configs/dcs_cont_content_rule_v2.json` (CR-002, FROZEN),
`data/labels/dcs_cont_content_true_labels_v{2,3,4}.json`, the `C-209` re-score behind the 11.4×
headline, and the completed dose-8 readout
`outputs/boombness/score_behavior/ts116m_readout_button_bomb_n8_20260912_040406_1427404`.

No SLURM job submitted, no GPU used, no FROZEN config / frozen lexicon / label file / script
modified. Job `882172` untouched. Everything below is recomputed from the raw judge runs and raw
`gens.jsonl` completions, keyed `(codeword, arm, prompt_id)` as the brief requires, with the join
asserted non-empty at every step.

---

## VERDICT

**Every published number in entries 097–103 reproduces from disk, to the digit, including the ones
REVIEW-4 could not check — and the headline's *point estimate* is sound. What does not survive is
the recall figure that the headline's final step multiplies by, and the interval the headline
quotes.** I rebuilt the `C-209` corpus from the census rule (`results.jsonl`, ≥200 rows,
`goal_status = substituted` on every row), joined all 58,468 rows to their own generation runs with
**zero join failures and `n_chars` matching the stored completion to the byte on 58,468 of 58,468**,
and reproduced all nine cells of `CONT-ENTRY 099`'s rate table exactly: button train+val
**0.3146 / 0.1243 / 0.0263**, button test **0.2113 / 0.0773 / 0.0178**, basket train+val
**0.1226 / 0.0391 / 0.0178**, basket test **0.0885 / 0.0312 / 0.0017**, carrot train+val
**0.1768 / 0.1048 / 0.0248**. The factor reproduces as a **ratio of sums over runs with a non-zero
CR-002 denominator**: button **11.435 → "11.4×", 95 % [10.57, 12.62], 68 runs**; basket
**7.364 → "7.4×", [5.26, 9.97], 6 runs**. The whole CR-002 validation chain reproduces from raw
text: the frozen config's in-sample 2×2s (basket 9/0/7/4, button 4/0/15/1), entry 098's
out-of-sample cells, entry 103's precision batch (basket 11 true / 1 spurious), and the pooled
Wilson intervals **[0.879, 1.000]** and **[0.847, 0.995]** — all exact. The label files are clean:
`v2 ⊂ v3 ⊂ v4` exactly, the `set` field partitions 20 + 18 + 12 rows per codeword with **no row
duplicated across sets**, all 100 rows are genuine kept-positives of the declared population, and
`rule_keeps` reproduces CR-002 from the raw completions on **60 of 60** non-derivation rows under
the arm-aware lookup. The `C-CONT-071` class of defect is gone. And the whole dose ladder of
`CONT-ENTRY 100` reproduces cell for cell, **including the 25.4 % [20.8, 30.3]** knockout share —
I recover the numerator −0.1864, the denominator +0.7336 and the interval independently.

**Three things fail or weaken, and one of them is load-bearing.** First, the **recall 0.923 is not
an estimate of recall**. It is the raw ratio `12/(12+1)` from a design that deliberately samples
12 rule-keeps against 6 rule-drops, when the population those strata came from holds 81 keeps
against 202 drops — the keeps are oversampled roughly **five-fold**. Design-weighted, button recall
is **0.678 [0.412, 0.955]**, and transported to the corpus's own keep-share (0.2137, against the
ASR arms' 0.2862) it is **0.588 [0.322, 0.934]**. The headline's last step, `11.4 × 0.923 ≈ 10.5×`,
is arithmetically correct but rests on a number that is biased upward by construction; done
properly the recall-corrected factor is **≈ 7.7× [4.4, 12.0]** on the arms' own strata and
**≈ 6.7× [3.5, 11.5]** transported to the corpus. Second, the **run is not the only unit of
dependence**: 68 button runs span only 116 domains, and every domain recurs across runs, so a
run-clustered bootstrap conditions on exactly the crossing it should be propagating. A two-way
(run × domain) cluster interval is **[8.9, 14.7]**, about **2.4× wider on the log scale** than the
published [10.5, 12.5]; domain-clustered alone gives [9.2, 14.8]. Third, the **pooled precision is
circular**: it folds in the 4 button and 9 basket derivation rows the rule was fitted to. Out of
sample only, precision is button **24/24 = 1.000 [0.862, 1.000]** and basket **23/24 = 0.958
[0.798, 0.993]** — so the advertised move "0.76 → 0.88" is really 0.76 → 0.86 on honest rows.
(A finite-population bound, which nobody has used and which the design actually licenses, does
better than either: see S2-b.)

Three bookkeeping defects sit under all of this. **The corpus is stale against its own census
rule** — by that rule it is now 114 runs and 60,478 rows, and the three excluded runs are exactly
the basket ASR arms, i.e. 2,010 rows in the codeword whose interval is three times wider than
button's; including them moves basket from 7.36 to **6.41 [4.99, 8.05]**. **Nine button runs and
two basket runs are silently dropped** for having a zero CR-002 denominator — a conservative
exclusion (the all-runs factor is 11.94, not 11.44) but an undisclosed and denominator-conditioned
one. And **the scope of the headline does not match the scope of the table it sits under**: the
bolded row is train+val, whose own ratio is 11.95, while "11.4×" is computed over train+val+test.
**No script exists in the repo for any of entries 099, 098 or 103** — every number above
reproduces only because I rebuilt the pipeline from the raw runs.

---

## FINDINGS BY SEVERITY

### S1 — "adjusted for CR-002's own recall, which is 0.923 on button … ≈ 10.5× recall-corrected". **FAILS as stated; the adjusted headline is WEAKENED to ≈ 7.7× [4.4, 12.0]**

**Claim** (`CONT-ENTRY 098`, `099`, `101`, `103`): recall **0.923** (button) / **0.800** (basket);
*"Genuine ≈ CR-002 / 0.923, giving ≈ 10.5× as the recall-corrected point estimate on button."*

**(a) The arithmetic is right and the direction is right.** `11.435 × 0.923 = 10.55 → 10.5`.
Dividing the CR-002 rate by a recall below 1 raises the genuine rate and lowers the factor, which
is what the entry says. That part is correct.

**(b) The recall figure is not identifiable from the design that produced it.** The validation draw
is, in the entry's own words, *"12 rule-keeps + 6 rule-drops per codeword"* — a **stratified sample
with unequal, undisclosed sampling fractions**. Recomputed from the three source runs
(`contasrj_base` / `contasrj2_ko` / `contasrj2_ctrl3`), the population is **283 kept positives**
(95 / 95 / 93 — reproduces `CONT-ENTRY 090`), of which CR-002 keeps **81** and drops **202**. So the
sampling fractions are **12/81 = 14.8 % on keeps against 6/202 = 3.0 % on drops**: the keeps stratum
is oversampled **5.0×**. The published `12/(12+1)` pools those strata as if they were one simple
random sample. They are not, and the pooled ratio is biased upward by exactly that factor.

Design-weighted (independent Jeffreys Beta(½,½) posteriors per stratum, known stratum sizes,
4×10⁵ draws), using every out-of-sample keep row available (24/24 true) and the six drop rows
(1/6 true):

| codeword | published recall | **design-weighted, ASR-arm strata** | **transported to corpus strata** |
|---|---|---|---|
| button | 0.923 [0.667, 0.986] | **0.678 [0.412, 0.955]** (N=81/202) | **0.588 [0.322, 0.934]** (N=1075/3956) |
| basket | 0.800 [0.548, 0.930] | **0.677 [0.554, 0.863]** (N=48/43) | **0.558 [0.428, 0.791]** (N=55/82) |

**(c) And recall is not transportable to the historical corpus without reweighting, because the
quantity it depends on differs between the two populations.** Recall here is a pure function of the
keep-share: `recall = N_keep·p(true|keep) / (N_keep·p(true|keep) + N_drop·p(true|drop))`. The
CR-002 keep-share is **0.2862** in the three button ASR arms and **0.2137** across the 111-run
corpus (1,075 CR-002 keeps of 5,031 lexicon keeps). On basket the gap is larger still — 0.5275 in
the `cbkasrj` arms against 0.4015 in the corpus. Transporting a recall estimated on one population
to another with a different stratum mix is exactly the error the stratification already made once.
Even the transported figure assumes `p(true | CR-002 drop)` — estimated from **six rows, one of
them true, Wilson [0.03, 0.56]** — holds across 111 runs spanning conditions the labelling never
touched. That is the dominant uncertainty in the whole adjustment and it is not stated anywhere.

**Consequence for the headline, propagated jointly** (lognormal factor from the two-way cluster
bootstrap of S1-b below × recall posterior):

| version | recall used | recall-corrected factor |
|---|---|---|
| **as published** | 0.923 | **≈ 10.5** (no interval given) |
| design-weighted, ASR-arm strata | 0.678 | **7.7 [4.4, 12.0]** |
| **transported to corpus strata** | 0.588 | **6.7 [3.5, 11.5]** |

**Verdict: the recall number FAILS** — it is a stratum-pooled ratio presented as a population rate.
**The recall-corrected headline WEAKENS** from 10.5× to roughly 6.7–7.7× with an interval that
reaches below 4×. The **unadjusted** 11.4× is unaffected (it does not use recall), and the
qualitative claim — *raw judge ASR overstates genuine success by roughly an order of magnitude* —
survives in its unadjusted form. Note also that the adjustment implies a genuine button rate of
`0.0250 / 0.588 ≈ 0.0425` corpus-wide, still 7× below the raw 0.2984, so the direction of the
program's conclusion is not in doubt; its digit is.

---

### S1 — "run-clustered factor … 95 % CI [10.5×, 12.5×] over 68 runs". **Point estimate SURVIVES exactly; the interval is WEAKENED — it should be [8.9, 14.7]**

**What I computed.** Corpus rebuilt from the census rule; 58,468 rows; per-row `ASR@0.5` =
`malicious_at_0.5`, lexicon keep = `ASR ∧ concept_hits(generation) ∧ ¬refused` (the frozen 44-term
lexicon of `scripts/dcs_succ_concept_presence.py`, asserted at 44 terms), CR-002 =
`lexicon keep ∧ MATERIAL ∧ ¬SCOPE` applied to the completion only, regexes read from the FROZEN
config. Ratio of sums, cluster bootstrap, 20,000 resamples.

| clustering unit | button units | factor | **95 % CI** |
|---|---|---|---|
| **run (as published)** | 68 | 11.435 | **[10.57, 12.62]** ← reproduces [10.5, 12.5] |
| domain | 116 | 11.435 | [9.17, 14.81] |
| run × domain | 3,916 | 11.435 | [10.77, 12.18] |
| prompt (row) | 39,160 | 11.435 | [10.81, 12.12] |
| **two-way, run × domain (CGM)** | — | 11.435 | **[8.92, 14.65]** |

**Is the run the correct independence unit? No — it is one of two, and the published interval
conditions on the other.** The design is **crossed, not nested**: the same 116 domains and the same
prompt bank recur across all 68 runs, and `C-CONT-048` already established that 39.1 % of button
rows are exact configuration duplicates under `do_sample=False`. Resampling runs while holding the
domain set fixed propagates run-to-run variation and **suppresses** domain-to-domain variation
entirely; resampling domains does the reverse. The published interval is the narrower of the two
one-way choices. The two-way cluster interval — the one the design actually calls for — is
**[8.92, 14.65]**, a log-scale half-width **2.4× the published one**. On basket the same correction
gives **[4.97, 10.90]** against the published [5.2, 10.0].

**The prompt is not a usable unit on its own** — it is nested inside neither and crossed with both;
prompt-level resampling gives [10.81, 12.12], which is *narrower* than run-level and would be the
wrong answer for the same reason.

**Verdict: SURVIVES as a point estimate (exact reproduction), WEAKENED as an interval.** Quote
**11.4× [8.9, 14.7]**; it is still comfortably an order of magnitude, and saying so with the right
interval costs the claim nothing.

---

### S2 — the estimator is never named, and the two candidates differ by 72 %. **SURVIVES (the right one is used) — but must be stated**

The reported quantity is the **ratio of sums** `Σ raw / Σ CR-002` over the retained runs: I recover
11.435 and 7.364 that way and no other way. The **mean of per-run ratios** is **19.695** on button
(median 10.964) and 8.555 on basket — and it is **undefined for 9 of the 77 button runs**, whose
CR-002 count is zero. Ratio-of-sums is the correct estimator here (it is the population rate ratio,
and it is what "the corpus overstates by X" means), but an entry that reports a ratio over runs and
an interval "over 68 runs" without naming the estimator invites the reader to assume the other one.
**SURVIVES; name it.**

---

### S2 — the pooled precision includes the rows the rule was derived on. **WEAKENED; the honest out-of-sample bound is 0.862 (button) / 0.798 (basket) — but a finite-population bound does better than either**

**Claim** (`CONT-ENTRY 103`): *"pooled: button 28 tp / 0 fp = 1.0000 [0.879, 1.000] n = 28;
basket 32 tp / 1 fp = 0.9697 [0.847, 0.995] n = 33 … the lower bound moves from 0.76 to 0.88
(button) and 0.85 (basket)."*

**(a) The pooling is not legitimate, and the `set` field says so.** Recomputing CR-002 from raw
text on all 100 rows and splitting on `set`:

| set | button tp/fp | basket tp/fp |
|---|---|---|
| `CR-002 derivation (v2)` | 4 / 0 | 9 / 0 |
| `CR-002 out-of-sample` | 12 / 0 | 12 / 0 |
| `CR-002 precision batch 2` | 12 / 0 | 11 / **1** |
| **published pooled** | **28 / 0** | **32 / 1** |
| **out-of-sample only** | **24 / 0** | **23 / 1** |

The 4 button and 9 basket derivation rows are the rows `CONT-ENTRY 097` read in order to *invent*
the `MATERIAL ∧ ¬SCOPE` rule — the `¬SCOPE` clause exists precisely to zero out the false positives
in that set. Their zero-fp contribution is a fitted property, not an observation. Including them
inflates n by 13 and guarantees 13 of the successes.

**Honest out-of-sample precision, supplied:**

| codeword | out-of-sample | point | **Wilson 95 %** | published (pooled) |
|---|---|---|---|---|
| button | 24 / 24 | 1.0000 | **[0.862, 1.000]** | [0.879, 1.000] |
| basket | 23 / 24 | 0.9583 | **[0.798, 0.993]** | [0.847, 0.995] |

So the advertised tightening is **0.76 → 0.862** on button and **0.76 → 0.798** on basket, not
0.88 / 0.85. The basket lower bound in particular loses five points.

**(b) A bound the record has not used, and which the design licenses.** The precision sample is
drawn *without replacement* from a **finite, enumerable** stratum: 81 CR-002 keeps on button and 48
on basket, across the three ASR-arm runs. That makes the hypergeometric, not the binomial, the
right reference distribution, and with these sampling fractions it is far more informative:

| codeword | keep stratum N | out-of-sample n | spurious found | 95 % upper bound on spurious in stratum | **finite-population precision ≥** |
|---|---|---|---|---|---|
| button | 81 | 24 | 0 | 8 | **0.901** |
| basket | 48 | 24 | 1 | 6 | **0.875** |

That is **stronger than the published pooled bound and honest**, and it is the correct statement
for the population actually sampled. Its limit is that this population is the three ASR-arm runs
(81 and 48 rows) — **not** the 1,075 button and 55 basket CR-002 keeps of the 111-run corpus, to
which only the Wilson/superpopulation bound and an untested transportability assumption apply.
Recommended form: *"on the arms where it was validated, CR-002's precision is ≥ 0.90 (button) /
≥ 0.875 (basket) at 95 %; extrapolated to the historical corpus the defensible bound is ≥ 0.86 /
≥ 0.80."*

**(c) Precision is at least identifiable, unlike recall.** The precision batches sample only the
keeps stratum, and precision is defined conditional on keeping, so a random draw from that stratum
estimates it without weights. The recall problem (S1) does not contaminate precision. **The
conclusion — CR-002 is a high-precision rule and supports a lower bound — SURVIVES. The specific
bound is WEAKENED and should be restated.**

---

### S2 — the corpus is stale against its own census rule, and the missing runs are all basket. **WEAKENED**

**Claim** (`CONT-ENTRY 099`): *"the whole `C-209` corpus — 111 runs, 58,468 rows."*

Re-running `CONT-ENTRY 063`'s census on today's tree: **796** judge runs with `results.jsonl`,
**486** with ≥ 200 rows, **114** substituted on every row, **28** on some — against the recorded
793 / 483 / 111 / 28. The three additional runs are
`cbkasrj_{base,ko,ctrl}_20260911_170750`, **2,010 rows, all basket**, and they are the very runs
the basket labels were drawn from. The entry inherits `063`'s frozen census without saying it is
frozen, and calls it "the whole corpus".

| basket factor | runs | value |
|---|---|---|
| as published (111-run corpus) | 6 | 7.364 [5.26, 9.97] |
| **current census (114 runs)** | **9** | **6.408 [4.99, 8.05]** |

A ~13 % move in the codeword the entry itself flags as resting on 6 runs. Either freeze the census
explicitly and say why (the basket labels come from those runs, which is a good reason), or use it.
Saying "the whole corpus" while excluding 2,010 qualifying rows is the weakest option.

---

### S2 — nine runs are dropped for having a zero denominator, undisclosed. **WEAKENED (conservative, but conditioned on the outcome)**

Of 77 button runs in the corpus, **9 have zero CR-002 positives**; of 8 basket runs, **2** do. The
published "68 runs" and "6 runs" are the complements. The exclusion is **conditioned on the
denominator** — it removes exactly the runs where the overstatement is *infinite* — and is
therefore conservative:

| button | runs | factor | 95 % CI (run cluster) |
|---|---|---|---|
| as published, CR-002 > 0 only | 68 | 11.435 | [10.57, 12.62] |
| **all runs** | 77 | **11.942** | [10.95, 13.24] |

The direction is in the claim's disfavour, so nothing collapses — but an undisclosed
outcome-dependent run filter is the kind of thing this program has corrected four times, and it
should be in the entry.

---

### S2 — the quoted factor and the bolded table row are computed on different populations. **WEAKENED**

`CONT-ENTRY 099` bolds **button train+val, 36,270 rows, 0.3146 → 0.0263**, then states the factor
as 11.4×. But `0.3146 / 0.0263 = 11.95`, not 11.4. Recomputed both ways:

| scope | runs with CR-002 > 0 | factor | 95 % CI |
|---|---|---|---|
| train + val only | 67 | 11.371 | [10.51, 12.49] |
| **train + val + test** | **68** | **11.435** | [10.57, 12.62] |

The published **"over 68 runs"** matches the all-splits computation; the published **CI
[10.5, 12.5]** matches the train+val one to two decimals. Both round to 11.4×, so nothing material
is wrong — but the entry mixes two scopes in one sentence, and the headline silently **includes
TEST rows** under a bolded train+val row. State the scope. (The test rows are historical judge runs,
not the held-out confirmatory read, so this is a presentation defect, not a discipline breach — but
the entry does not say so.)

---

### S3 — DATA integrity of `v2`/`v3`/`v4`. **SURVIVES in full — this is the one thing that is now clean**

Checked against the brief's list, all from raw completions with the `(codeword, arm, prompt_id)`
lookup:

| check | result |
|---|---|
| `v2 ⊂ v3 ⊂ v4` on the full record tuple | **yes, exactly** (40 / 76 / 100, nested) |
| declared `n` matches record count | 40 / 76 / 100 ✔ |
| `set` partitions the rows | ✔ 20 + 18 + 12 per codeword, no row in two sets |
| any row duplicated on `(codeword, arm, prompt_id)` | **none**, in any version |
| every row a genuine kept-positive of the declared population | **100 / 100** |
| `domain` in the file matches the judge row | **100 / 100** |
| `rule_keeps` reproduces CR-002 from raw text (non-derivation rows) | **60 / 60**, zero mismatches |
| derivation rows' CR-002 2×2 matches the FROZEN config's `in_sample_result` | basket 9/0/7/4 ✔, button 4/0/15/1 ✔ |
| `note_rule_keeps` warning (two rules in one column) is honoured by the entries | **yes** — 098 and 103 re-derive CR-002 on the v2 rows rather than reading the column |

The `C-CONT-071` failure mode is **fixed and independently confirmed**. This is the strongest
data-integrity result in the phase.

**Two residual defects carried forward, neither new:**

1. **Non-independence, still unflagged.** Button's 50 rows cover **43 distinct prompt_ids**
   (6 recur across arms); basket's 50 cover **33** (13 recur). Three rows per codeword duplicate
   another labelled row's leading 400 characters outright. The sampler still draws **rows, not
   prompts**, so the effective n behind every precision and recall interval above — mine included —
   is below its nominal value, on basket materially so. `REVIEW-4` raised this for v2; v3 and v4
   reproduce it.
2. **The derivation rows' `rule_keeps` column remains unverifiable.** It encodes the HARD∧¬pivot
   rule, whose term list was never committed (`REVIEW-4`, S1: *"the ellipsis is load-bearing"*).
   I can verify the CR-002 column and every out-of-sample row; I still cannot verify the HARD
   column from the repo. It is consistent with the published 2×2s (10/0/7/3 and 5/5/10/0 recompute
   from the column), which is as far as verification can go.

---

### S3 — reproducibility: no script exists for entries 098, 099 or 103. **FAILS as an artifact; the numbers themselves SURVIVE**

`git log` shows entries 098–103 touching only the log, the claim table and the label JSONs. There is
no committed code that builds the 111-run corpus, applies CR-002, computes the factor, or draws the
validation samples. Every number above reproduces — but only because I rebuilt the census rule, the
codeword mapping (four of the nine bank files carry no codeword in their filename and had to be read
from the bank's own rows), the gens-run join through `config.json:args.gens`, the split manifest and
the exclusion list from scratch. The sampling draws have **no recorded seed and no completion hash**,
which is the precondition that made `C-CONT-071` possible in the first place and is not yet closed.
Given that this program has now had **four** fabricated-number incidents from field-name errors and
one from a re-derived shuffle, an unscripted headline is the single largest remaining process risk.

---

### S3 — `CONT-ENTRY 100`'s dose ladder. **SURVIVES entirely — every figure reproduces**

Recomputed through `scripts/dcs_cont_layerpos_map.py`'s own loader (`semantic_one_word`, cell C,
`σ(logp_concept − logp_codeword)`, domain unit, train+validation, `EXCLUDED_DOMAINS` applied),
`slot0` only as `CONT-ENTRY 094` declared before the data existed:

| dose | domains | slots | mean | median | sd (ddof=0) | published |
|---|---|---|---|---|---|---|
| 0 | 90 | 180 | 5.6e−07 | — | ~0 | ~0 ✔ (all 180 raw slots in [8.9e−08, 5.96e−06], median 5.59e−07 — reproduces `CONT-ENTRY 093`) |
| 4 | 90 | 180 | **0.6728** | 0.7537 | 0.2984 | 0.6728 / 0.7537 / 0.2985 ✔ |
| 8 | 90 | 180 | **0.7361** | 0.8392 | 0.2601 | 0.7361 / 0.8392 / 0.2602 ✔ |

| step | Δ (mine) | 95 % CI (mine) | domains positive | published |
|---|---|---|---|---|
| 0 → 4 | +0.6728 | [+0.6106, +0.7341] | **90/90** | +0.6728 [+0.6096, +0.7338], 90/90 ✔ |
| 4 → 8 | +0.0632 | [+0.0291, +0.0977] | **60/90** | +0.0632 [+0.0287, +0.0986], 60/90 ✔ |
| 0 → 8 | +0.7361 | [+0.6804, +0.7885] | **90/90** | +0.7361 [+0.6824, +0.7885], 90/90 ✔ |

**The 25.4 % knockout share reproduces exactly**, on the declared primary and the declared 67-domain
intersection: numerator `ko − base`, slot0 = **−0.1864**; denominator `dose8 − dose0`, slot0 =
**+0.7336**; ratio **25.4 %, paired domain bootstrap 95 % [20.8, 30.3]** — digit for digit. The
dose-4 denominator gives 27.7 % [22.6, 33.3] and `ko − ctrl` gives 26.7 % [22.0, 31.7]; the
all-slots secondary gives 27.9 % [25.3, 30.7]. Entry 100 correctly (i) uses the declared slot0
primary — the composition error `REVIEW-4` caught in entry 095 is fixed — and (ii) states
"probability scale" in the ladder table, as `C-CONT-073` requires.

**One thing to keep attached to it.** The scale caveat is stated for the *ladder* table but not
restated on the *knockout-share* table beneath it, and the share is the scale-sensitive quantity.
On the readout's native log-odds scale the same cut removes **12.8 % [11.2, 14.5]** of the
0 → 8 span (13.3 % [11.7, 15.0] of the 0 → 4 span) against 25.4 % on the probability scale — a
factor of two, from a scale choice alone. The share must carry "on the probability scale" wherever
it travels, including into claim-table row A14.

The cross-run caveat entry 100 attaches to the 4 → 8 step is correct and correctly sized; `882136`
is the right fix and I have not touched it.

---

### S3 — `carrot` reprinted after being struck. **Minor**

`CONT-ENTRY 063` point 3 struck the corrected carrot rate (*"The 0.0946 above is struck; nothing in
this program depends on it"*) at a measured false-negative rate of 43.3 %. `CONT-ENTRY 099`'s table
reprints carrot at 0.1048 / 0.0248 in italics with limit 1 attached, which is honest, but a struck
quantity reappearing in a headline table is how struck quantities come back. I reproduce those cells
exactly (0.1768 / 0.1048 / 0.0248 on 8,094 rows); the objection is editorial, not numerical.
Separately, limit 2 is confirmed: basket's test cell is **1 row** (0.0017 × 576 = 0.98).

---

## WHAT VERIFIED CORRECT, STATED PLAINLY

* All nine rate cells of `CONT-ENTRY 099`, on 58,468 rows across 111 runs — exact.
* The corpus join: **zero** missing generations, **zero** `n_chars` mismatches, on 58,468 rows.
* The factor as a point estimate: button 11.435, basket 7.364 — exact, once the estimator
  (ratio of sums) and the run filter (CR-002 > 0) are recovered.
* The full CR-002 validation chain from raw text: frozen config in-sample 2×2s, entry 098's
  out-of-sample cells and recalls-as-computed, entry 103's precision batch including the single
  basket false positive, and both pooled Wilson intervals.
* Label-file integrity: nesting, partition, no duplicates, arm-aware `rule_keeps` reproduction on
  60/60 checkable rows, all 100 rows genuine kept-positives.
* The entire dose ladder including the 25.4 % [20.8, 30.3] share, on the pre-declared primary.
* `CONT-ENTRY 063`'s button and basket row counts (43,022 / 3,618) and the 2.55× lexicon factor
  (0.2984 / 0.1169) — both recovered independently.

## RECOMMENDED FORMS

* **Headline:** *"On codeword-remapping jailbreaks, raw StrongREJECT ASR overstates genuine attack
  success by **11.4× (95 % [8.9, 14.7])** on button and **7.4× ([5.0, 10.9])** on basket, measured
  as a ratio of population rates over 58,468 rows in 111 judge runs. Adjusted for CR-002's own
  recall, estimated with the sampling design's weights, the factor is **≈ 7 ([3.5, 12])** — still
  close to an order of magnitude, but the recall correction is the weakest link and should carry
  its interval."*
* **Precision:** *"On the arms where it was validated, CR-002's precision is ≥ 0.90 (button) /
  ≥ 0.875 (basket) at 95 % by a finite-population bound over the 81 / 48 kept rows; out of sample
  and without that bound, ≥ 0.862 / ≥ 0.798. The 0.879 / 0.847 figures pool the derivation rows and
  should not be quoted."*
* **Knockout share:** *"On the probability scale and on the declared slot0 primary, the cut removes
  25.4 % [20.8, 30.3] of the full 0 → 8 demonstration span; on the native log-odds scale, 12.8 %
  [11.2, 14.5]."*
