# DCS-PR-051 — the paired positional contrast

**Is concept identity more decodable at the codeword's representation than at a downstream
position that is token-identical across concepts?**

Generated 2026-09-07 · `scripts/dcs_ts_pr051_positional.py` · governed by
`configs/dcs_ts_pr051.json` (FROZEN, `written_at_commit` 347f0920) · **CPU only. No GPU, no SLURM,
no network, no model weights.** Both read sites were already extracted; this document reads
representation caches, prompt banks and the split manifest, and nothing else.

The analyzer contains **no numeric gate literal**. `alpha`, `n_perm`, the chance level, the
nuisance floor, the layer and C grids, the split, the population filters, the exclusions, the
assumed-SD bracket, the demotion threshold and the multiplicity family are all fetched through
`scripts/dcs_ts_prereg.py::Prereg.require()`, which refuses rather than defaulting. The probe
conventions — run discovery via `DONE.json`, bank-sha verification against the pin, the
explained/unexplained missing-row rule, `select_hparams` with its `SELECTION_TRACE`,
`sign_test_two_sided`, `group_permutation_p`, `fmt_p` — are **imported** from the frozen probe
analyzer `scripts/dcs_ts_pr048_analysis.py`, not reimplemented.

---

## 0. The answer, in one place

| | |
|---|---|
| **W2 power verdict** | **ADEQUATELY POWERED.** Measured paired SD **0.0494** on validation, against the preregistration's own demotion ceilings of 0.188 (α) and 0.160 (Holm). Conjunctive MDE at that SD is **0.0395** accuracy. The contrast is **not** demoted to exploratory. |
| **paired difference** (`codeword_last` − `following`, 23 TEST domains) | **+0.0185**, 95 % CI (t) **[+0.0042, +0.0328]**, domain-bootstrap CI [+0.0054, +0.0326] |
| **permutation** (paired sign-flip of the SITE label, 10 000 draws, domain level) | two-sided **p = 0.0157** — floor 9.999 × 10⁻⁵ (156 exceedances, not at the floor) |
| **sign test** (ties dropped, n = 14 of 23) | k⁺ = 12, k⁻ = 2 — **p = 0.01294**, floor 1.221 × 10⁻⁴ |
| **nuisance floor for the difference** | **0.0** — cleared |
| **Holm, within the preregistered SECONDARY family (8 members)** | first-step α = 0.00625 — **NOT significant** |
| **interpretation** | uncorrected → `codeword >> control`; **under the preregistered correction → `codeword ≈ control`, GIST** |
| **absolute accuracy on TEST** | codeword_last **0.9446** (AUROC 0.9933) · following **0.9261** (AUROC 0.9895) |
| **checks** | **18/18 PASS**, **14/14 mutations RED** |

**The one unambiguous sentence** is in §8. Read §7 before it.

---

## 1. What this instrument is for

`A-043` S-3 recorded the gap this contrast exists to close. Two hypotheses make the *same*
prediction for the PR-048 primary:

* **H_bind** — the codeword is represented as BOMB, so identity is *localised at the codeword*;
* **H_gist** — the prompt is *about* bombs, so identity is available *everywhere* and the codeword
  position is not special.

A probe read at the codeword cannot separate them, because a gist representation is available at
the codeword too. Only a **contrast** against a downstream position that is token-identical across
concepts can. If H_gist is what is true, **CLAIM A must be narrowed to a decodability statement
about the PROMPT, not about the codeword** — a real and publishable outcome, not a failure.

### Why the pairing is the whole methodological argument

The absolute measurement in this phase is defeated by a nuisance floor. On knife-vs-gun a bag of
17 surface counts read off the prompt text reaches **0.7065** accuracy / 0.7479 AUROC without
touching a hidden state (`_y3_result.THE_BAR`); the 3-way surface floor elsewhere in the phase is
0.9217. **None of that applies here.** Both read sites see the **same prompt** — the same
demonstration block, the same register, the same character and token length, the same
TF-IDF-recoverable content — so every surface confound is **common to both arms and differences
out**. The preregistration says so itself, in `primary.nuisance_floor`:

> *"a paired difference has no surface floor: both sites see the SAME prompt, so any surface
> confound is common to both and differences it out"*
>
> *"this is precisely why the paired positional contrast is worth running — the confound that
> defeats the absolute measurement cancels in the difference"*

**The nuisance floor for the paired difference is 0.0, not 0.9217 and not 0.7065.** This is the
single strongest methodological argument the phase has: the confound that makes the absolute
number uninterpretable is exactly the confound the pairing removes. It is enforced, not merely
asserted — check `FLOOR` reads `primary.nuisance_floor.accuracy` and refuses anything but a
number, and mutation `surface_floor` (which substitutes the 0.7065 surface bar) turns it RED.

The floor cancels **surface** confounds. It does not cancel a *positional* one — a content
position beating a scaffold position for reasons unrelated to the codeword. That is precisely why
W3 moved the control off `--position last`; see §3.

---

## 2. W2 — power for a paired difference at n = 23 (the blocking gate)

W2 is `blocking: true, done: false` in the frozen config, and it is the reason
`dcs_ts_prereg.load(..., for_extraction=True)` still refuses. **It is answered here, first, before
any representation was loaded** (`--stop-after-w2` runs this section and stops). The frozen config
was **not** edited; the run loads with `for_extraction=False` and prints the refusal it would
otherwise get, and check `CHK-W1W3` confirms every *other* blocking item (W1, W3) is closed.

### Neither PR-048's nor PR-049's power transfers, and the reason is arithmetic

PR-048's power block sizes a **3-way absolute** accuracy against chance 1/3. PR-049's sizes a
**2-way absolute** accuracy against 0.5. The estimator here is a **paired difference against 0.0**,
whose sampling SD is the SD of the *within-domain difference*. That quantity is a different
variance component from either of theirs and is **not recoverable** from them: two accuracies with
between-domain SD 0.1406 each can produce a paired-difference SD anywhere from ~0 (perfectly
correlated) to 0.199 (independent). The prereg's own `power._no_measured_2way_sd` makes the
matching admission for the absolute 2-way case.

### Floors

| quantity | value |
|---|---|
| sign-test attainable floor, two-sided, n = 23 | **2.384 × 10⁻⁷** |
| permutation floor, exhaustive over all 2²³ sign assignments | 2.384 × 10⁻⁷ |
| permutation floor, Monte-Carlo at the preregistered `n_perm = 10000` | **9.999 × 10⁻⁵** |
| **the binding floor** | **9.999 × 10⁻⁵** — the Monte-Carlo one; the design could resolve **419× deeper** if the 2²³ sign flips were enumerated instead of sampled |

A note the prereg gets slightly wrong and this re-derivation corrects:
`power._sign_test_binding` says *"rejecting needs k ≥ 17 of 23 domains, π ≥ 0.788."* Re-derived
exactly: the sign test rejects at α = 0.05 from **k ≥ 17 of 23**, which is **π ≥ 0.7391**. The
figure **0.7880** is the π needed for **80 % power**, not the critical π. Both numbers are right;
the prereg pairs them as if they were the same quantity. Neither the design nor any conclusion
depends on it.

### MDE for a paired difference, 80 % power, α = 0.05

The success rule is **conjunctive** (permutation **and** sign test), so the design is only as
powered as its weaker arm; both arms are reported and the conjunctive column is their max.

| assumed paired SD | kind | perm arm | sign arm | **conjunctive MDE** |
|---|---|---|---|---|
| 0.0500 | ASSUMED | 0.0306 | 0.0400 | **0.0400** |
| 0.1406 | ASSUMED | 0.0859 | 0.1124 | **0.1124** |
| 0.2500 | ASSUMED | 0.1528 | 0.1999 | **0.1999** |
| 0.3439 | ASSUMED | 0.2102 | 0.2749 | **0.2749** |
| 0.1118 | **DERIVED** floor | 0.0683 | 0.0894 | **0.0894** |
| **0.0494** | **MEASURED** | 0.0302 | 0.0395 | **0.0395** |

**Which numbers are assumptions, stated plainly.**

* Every row marked **ASSUMED** is an assumption. The four SDs are the preregistration's own
  bracket (`power.mde_by_assumed_sd`), where 0.1406 is PR-048's 3-way between-domain value
  *borrowed* and 0.25 is a distribution-free ceiling. **There is no measured paired positional SD
  anywhere in this project's record**; before this run the estimator had never been fit.
* The **DERIVED** row is arithmetic, not an assumption. From Z2 of
  `reports/DCS_TS_PR050_PR051_BLOCKERS.md`, a per-domain accuracy on *m* rows has variance
  `sd_between² + p(1−p)/m`. A paired difference carries that binomial term **twice**, so with
  m = 40 rows per domain per site (10 family slots × 2 concepts × 2 codewords, all from the
  prereg) the observed paired SD cannot fall below `sqrt(2p(1−p)/m)` = **0.1118** at p = 0.5,
  0.1025 at p = 0.7, 0.0671 at p = 0.9, *even if the true per-domain difference were constant*.
  This bounds how small an MDE the design can ever have.
* The **MEASURED** row is measured — on the **23 validation domains**, at each site's own selected
  config, **before the test split was read**. It is 0.0494, which is *below* the p = 0.5 noise
  floor and consistent with the p = 0.9 one (0.0671): the two sites both run at ~0.91 on
  validation, and their errors are strongly correlated because they read the same rows. That
  correlation is what makes this contrast well powered.
* Two approximations, both labelled: the permutation arm's power is approximated by the one-sample
  t-test on the paired differences (asymptotically equivalent, conservative at small n), and
  converting the sign test's π to an accuracy δ assumes a normal paired difference — which it is
  not, since per-domain accuracies live on a 1/40 lattice. Neither approximation is load-bearing
  at the measured SD, where both arms have power ≈ 1.000 at the declared δ = 0.15.

### The verdict

The preregistration wrote its own demotion rule before any number existed
(`power.DEMOTION_CONTINGENCY`), and the analyzer **parses it out of the config and enforces it**
rather than quoting it:

> *"If the TRAIN-ONLY between-domain SD exceeds 0.188 (0.160 under Holm), conjunctive power falls
> below 0.8 and this contrast is DEMOTED TO EXPLORATORY."*

Measured paired SD **0.0494** < 0.160 < 0.188.

> **W2 VERDICT: ADEQUATELY POWERED.** Conjunctive MDE **0.0395** accuracy at the measured SD;
> conjunctive power at the declared δ = 0.15 is ≈ 1.000 at α and under Holm. The contrast is not
> demoted. Had the SD exceeded 0.188 the script would have printed the underpowered verdict and
> **returned without reading the test split** — that branch is in the code, not in the prose.

One honest limit on this verdict: the measured SD is a *validation* quantity used to size a *test*
estimator. On test the observed paired SD came out at 0.0330 — smaller still, so the sizing was if
anything conservative.

---

## 3. The two read sites

| | primary | control |
|---|---|---|
| `--position` | `codeword_last` | `following` |
| what it is | the last token of the last codeword occurrence | `rel_end −9`, `' actually'`, token id 3604 |
| extraction | `ts116m_full_*` (the PR-048 extraction) | `ts116m_following_*`, job 860925 |
| token-identical across concepts | n/a (this is the position that differs) | **yes** — W3, `reports/DCS_TS_PR050_PR051_BLOCKERS.md` |

The control position name is **parsed from `design.sites.control_site`**, not hardcoded, and check
`SITE-pos` verifies every run's `summary.json` `position` field against it; mutation
`wrong_position` turns it RED.

`design.sites.control_site` records why the control is `following` and not `last`: W3 measured that
`--position last` is the **generation-header terminator `'\n\n'` in 6840/6840 prompts** — pure chat
scaffold, five rungs past the last content token. A null at a scaffold token is a null about the
readout, not about the query. `following` is a **content** position that passes the same four
criteria (token-identical across concepts at matched `(codeword, prompt_id)`; strictly after every
codeword occurrence; decoding contains no concept word; present in every prompt) and was the token
role map's own nomination. It sits a **constant 9 tokens** downstream of the codeword in
6840/6840 prompts, so the contrast is between two fixed offsets, not two moving ones.

This matters for interpretation and is stated before the numbers: because the control is a content
position rather than scaffold, the `codeword >> control` branch is *less* under-determined than it
would have been at `last` — but it is still not free of the "content positions differ from one
another" alternative, since there is only one control position in the design.

---

## 4. Population, bound identically at both sites

Bound on the **field** `cell == "C"` (not `condition` — A-039 measured that the wrong field binds
**zero** rows), `query_kind == "semantic_one_word"`, `n_examples == 4`, concepts **knife and gun**
(`population._excluded_concept`: bomb is excluded from *this* contrast, declared before any probe
ran, because it is what makes the contrast register-clean), minus the three whole-population
preregistered exclusions.

| quantity | value |
|---|---|
| rows **per site** | **4520** = 113 domains × 2 codewords × 2 concepts × 10 family slots |
| domains analysed | **113** (`restaurant_kitchen` C-082, `subway_station` C-087, `school_campus` C-075/R-108 — all three sit in TRAIN) |
| split (`dsplit`) | **67 train / 23 validation / 23 test** |
| rows per split per site | 2680 / 920 / 920 |
| rows per domain per site | **40** (both concept arms equal in all 23 test domains) |
| **row sets across the two sites** | **IDENTICAL — 4520 of 4520, keyed on `(bank, prompt_id)`, and element-wise row-aligned** |

`primary.void` is *"the two sites analysed on different populations"*, so this is not a nicety.
Two checks enforce it. `ROWSET-identical` compares the key sets; `ROWORDER` asserts the two feature
matrices are element-wise aligned, so each domain's accuracy at the two sites is computed over the
same rows. The key is **`(bank, prompt_id)`, not `prompt_id`** — the four banks reuse the same 1130
ids, so keying on the id alone would compare 1130 keys where 4520 rows exist and would be blind to
an entire bank going missing. Same family as the matcher/scope bug class: the check's notion of a
row was not the row.

**Missing rows.** The three `basket` control runs each failed 3 rows and the three `basket`
primary runs each failed 30, all with `resolve:occurrence_count_mismatch` — the C-075
`basketball` defect, where the extractor found one more *token* occurrence of the codeword than
*text* occurrences and **refused rather than guessing**. That is correct behaviour. A blanket
`n_failed == 0` guard would refuse the whole analysis (R-108); a blanket "ignore failures" would
let an unexplained failure silently shrink the population. The rule enforced is the precise one:
**every absent population row must belong to a preregistered whole-population exclusion.** 12
absent rows examined across both sites, **0 unexplained**. Mutation `keep_excluded_domains` turns
it RED.

---

## 5. The probe, and both SELECTION_TRACEs

The **same frozen probe design** is fit **independently at each site**: multinomial logistic
regression, standardiser fit on TRAIN domains only, `max_iter = 2000`, trained on the 67 train
domains, `(layer, C)` selected on the **23 VALIDATION domains only, separately per site**, and each
site evaluated **once** on the 23 test domains. Grid: the preregistered 9 layers × 4 C values.
Check `GUARD-TEST` asserts the selection set contains zero test rows (measured FPR: 0.0467
validation-selected vs **0.4433** test-selected, a 9.5× inflation); mutation `select_on_test` turns
it RED.

### SELECTION_TRACE — `codeword_last`

```json
{"chosen": [9, 0.01], "best_acc": 0.9108695652173913, "worst_acc": 0.8673913043478261,
 "surface_range": 0.0434782608695652, "n_grid": 36, "n_tied_at_best": 1,
 "inert": false, "saturated": false, "_warning": ""}
```

### SELECTION_TRACE — `following`

```json
{"chosen": [10, 0.01], "best_acc": 0.9086956521739132, "worst_acc": 0.8445652173913045,
 "surface_range": 0.0641304347826087, "n_grid": 36, "n_tied_at_best": 1,
 "inert": false, "saturated": false, "_warning": ""}
```

**Neither surface is saturated and neither selection is inert.** `n_tied_at_best = 1/36` at both
sites, `best_acc` is 0.911 / 0.909 rather than 1.000, and the surfaces span 0.0435 and 0.0641. The
C-070 failure — a surface that is 1.000000 at all 36 grid points, so a strict `>` always returns
the first element and every pick is a grid-order tie-break reported for months as learned
localisation — **did not occur here**, and that is a measurement, not an absence of checking:
`select_hparams` computes `inert` and `n_tied_at_best` and the caller cannot drop them without
deleting a field.

Full validation surfaces (domain-mean accuracy, 23 domains; **cw** = `codeword_last`,
**fo** = `following`):

| layer | C=0.01 cw | C=0.1 cw | C=1 cw | C=10 cw | C=0.01 fo | C=0.1 fo | C=1 fo | C=10 fo |
|---|---|---|---|---|---|---|---|---|
| 6 | 0.8978 | 0.9000 | 0.9000 | 0.8978 | 0.8630 | 0.8707 | 0.8609 | 0.8446 |
| 7 | 0.8924 | 0.8935 | 0.8870 | 0.8870 | 0.8902 | 0.8837 | 0.8728 | 0.8717 |
| 8 | 0.8967 | 0.8935 | 0.8880 | 0.8870 | 0.8978 | 0.9000 | 0.8913 | 0.8837 |
| **9** | **0.9109** | 0.9087 | 0.8989 | 0.8935 | 0.8935 | 0.8891 | 0.8815 | 0.8728 |
| **10** | 0.8946 | 0.8946 | 0.8902 | 0.8859 | **0.9087** | 0.9033 | 0.8924 | 0.8707 |
| 11 | 0.8783 | 0.8848 | 0.8783 | 0.8728 | 0.8935 | 0.8924 | 0.8859 | 0.8717 |
| 12 | 0.8804 | 0.8761 | 0.8674 | 0.8674 | 0.9033 | 0.8913 | 0.8891 | 0.8783 |
| 13 | 0.8989 | 0.8880 | 0.8859 | 0.8870 | 0.8924 | 0.8815 | 0.8793 | 0.8870 |
| 14 | 0.8880 | 0.8826 | 0.8717 | 0.8750 | 0.8902 | 0.8793 | 0.8772 | 0.8815 |

The two surfaces are not identical — the control site peaks a layer later and is markedly worse at
layer 6 — but every one of the 72 grid points at both sites sits between 0.845 and 0.911. The
choice of grid point moves the answer by less than the difference between the sites' worst points.

---

## 6. The contrast

### Absolute, on TEST (descriptive — each is subject to the surface floors the pairing removes)

| site | domain-mean acc | row acc | balanced acc | AUROC | rows / domains |
|---|---|---|---|---|---|
| `codeword_last` | **0.9446** | 0.9446 | 0.9446 | 0.9933 | 920 / 23 |
| `following` | **0.9261** | 0.9261 | 0.9261 | 0.9895 | 920 / 23 |

### The paired statistic

**Statistic:** the paired per-domain difference `codeword_last − following` over the 23 TEST
domains. **Test:** paired domain-level permutation of the **SITE** label at the preregistered
`n_perm = 10000`. Exchanging the site label within a domain negates that domain's difference, so
the null is the set of 2²³ sign assignments, sampled at 10 000 draws. **Domain is the independence
unit** — check `UNIT` enforces it and mutation `row_level_unit` turns it RED; row-level permutation
has a measured FPR of 0.2000 in this design.

| quantity | value |
|---|---|
| mean paired difference | **+0.01848** |
| SD of the paired difference | 0.03304 |
| standard error | 0.00689 |
| **95 % CI (t, 22 df)** | **[+0.00419, +0.03277]** |
| 95 % CI (domain bootstrap, 10 000 resamples) | [+0.00543, +0.03261] |
| **nuisance floor for the difference** | **0.0000** — `clears_floor = True` |
| permutation, **two-sided** | **p = 0.015698** [floor 9.999 × 10⁻⁵], 156 exceedances |
| permutation, one-sided | p = 0.007599 [floor 9.999 × 10⁻⁵], 75 exceedances |
| null distribution | mean +2.6 × 10⁻⁶, SD 0.00768 — centred on zero, as a sign-flip null must be |
| **sign test**, ties dropped | k⁺ = 12, k⁻ = 2, **n_eff = 14** → **p = 0.012939** [floor 1.221 × 10⁻⁴] |
| sign test, ties counted as non-positive | k = 12 of 23 → p = 1.0 [floor 2.384 × 10⁻⁷] |

**Every p is printed beside its attainable floor, and none is at it.** The permutation p has 156
exceedances, so it is a measurement and not the design's arithmetic floor (C-069). Had it had zero
exceedances the analyzer would have printed `p < 1/(B+1)` rather than a bare number.

**On the two sign tests.** 9 of the 23 domains have a difference of **exactly zero**, so the
choice of tie rule is not cosmetic and both versions are shown. The tie-dropped version (n = 14) is
the standard sign test and is the one used for the conjunctive rule; the version that counts ties
against the alternative returns p = 1.0. **That 9-of-23 exact-tie count is itself a finding**: in
39 % of test domains the two sites classify identically, to the row.

### Per-domain differences (the independence unit, all 23)

Accuracies live on a 1/40 = 0.025 lattice, so a difference of +0.025 means the codeword site got
**one more row of forty** right.

| domain | `codeword_last` | `following` | diff |
|---|---|---|---|
| `instructional` | 0.875 | 0.775 | +0.100 |
| `tram_depot` | 0.900 | 0.825 | +0.075 |
| `foundry_floor` | 0.950 | 0.875 | +0.075 |
| `lifeboat_station` | 0.975 | 0.925 | +0.050 |
| `feed_mill` | 0.925 | 0.900 | +0.025 |
| `grain_silo` | 0.925 | 0.900 | +0.025 |
| `hotel_laundry` | 0.875 | 0.850 | +0.025 |
| `hydro_station` | 0.925 | 0.900 | +0.025 |
| `joinery_shop` | 0.925 | 0.900 | +0.025 |
| `lab_safety` | 0.900 | 0.875 | +0.025 |
| `pharmacy_store` | 0.950 | 0.925 | +0.025 |
| `tannery_works` | 0.950 | 0.925 | +0.025 |
| `art_gallery` | 1.000 | 1.000 | +0.000 |
| `bakery_plant` | 1.000 | 1.000 | +0.000 |
| `brewery_works` | 1.000 | 1.000 | +0.000 |
| `electrical_wholesale` | 0.950 | 0.950 | +0.000 |
| `laundrette_unit` | 0.950 | 0.950 | +0.000 |
| `physio_gym` | 0.875 | 0.875 | +0.000 |
| `planetarium` | 0.975 | 0.975 | +0.000 |
| `supermarket_backroom` | 1.000 | 1.000 | +0.000 |
| `wind_farm` | 1.000 | 1.000 | +0.000 |
| `veterinary_clinic` | 0.950 | 0.975 | −0.025 |
| `helipad_base` | 0.950 | 1.000 | −0.050 |

Rows, not percentages: the largest single-domain advantage anywhere in the table is **4 rows out of
40**, in one domain. Twelve domains gain 1–4 rows, nine are exact ties, two lose 1–2 rows.

### Multiplicity

`multiplicity` declares **PR-051 a member of the SECONDARY family, 8 members, Holm within the
family**. The most conservative first Holm step is **α/8 = 0.00625**. The two-sided permutation
p = 0.0157 and the sign-test p = 0.0129 are both **above** it, so **at the first Holm step the
difference does not survive the preregistered correction**.

Holm's later steps are looser (α/7 = 0.00714 … α/3 = 0.01667 … α/1 = 0.05), and both p-values would
clear the threshold from step 6 onward. So PR-051 *could* survive Holm — but only if it sits at
rank 6, 7 or 8 in the ascending ordering, i.e. **only if at least five of the other seven secondary
members reject first at their own, stricter thresholds**. That cannot be evaluated until every
secondary member has a p-value, and a declared member that is not run enters at p = 1.0
(`multiplicity._absent_members_enter_at_p_1`), which pushes PR-051 *earlier* in the ordering rather
than later. The first-step outcome is therefore reported here as the conservative bound, with the
condition under which it would flip stated rather than left implicit.

---

## 7. Interpretation — fixed in the preregistration, evaluated twice

`design._interpretation_fixed_before_the_numbers_exist` is a trichotomy written before any hidden
state existed at the control site. It is not restated in prose here; it is *selected among*, in
code, and both branches of the multiplicity rule are shown because they disagree.

| | verdict | the preregistration's fixed reading |
|---|---|---|
| **uncorrected, α = 0.05** | significant, positive → **codeword >> control** | *"consistent with binding: identity is localised where the codeword is"* |
| **Holm first step, α = 0.00625** | not significant → **codeword ≈ control** | *"consistent with GIST: the prompt topic is decodable throughout and the codeword position is not special. This would mean CLAIM A must be narrowed to a decodability statement about the prompt, NOT about the codeword."* |

`control >> codeword` is excluded: the difference is positive and its whole CI is above zero.

**The two branches disagree, and the preregistration declares the Holm correction.** Reporting only
the uncorrected branch, when the corrected one is the confirmatory one and it flips the answer,
would be choosing the answer after seeing it. Both are reported; **the corrected branch governs**,
on the conservative first-step evaluation described in §6 — it is the only step evaluable while the
rest of the secondary family is unrun.

Three things constrain how large "codeword >> control" can be read, none of them a softening of the
preregistered reading:

1. **The control site already reaches 0.9261.** The codeword site's advantage of +0.0185 closes
   **25 %** of the 0.0739 of headroom that remained. Concept identity is decodable at **92.6 %** at
   a position **nine tokens downstream** of the codeword that is **token-identical across
   concepts** and carries no concept token at all. Whatever is true of the codeword position, the
   identity is *also* sitting at a position that shares no content with it.
2. **W2 says the design would have seen a much larger effect if there were one.** The conjunctive
   MDE at the measured SD is 0.0395 — the observed 0.0185 is *under half* of it. The design was
   sized for δ = 0.15 and has power ≈ 1.000 there. So the small difference is a measurement of a
   small difference, not a failure to resolve a large one. This is what makes the "≈" branch
   informative rather than merely negative.
3. **The pairing removes surface confounds, not positional ones.** With one control position, a
   +0.0185 advantage for a content position that *contains* the codeword over a content position
   that *follows* it is consistent with binding, and equally consistent with any reason a
   codeword-bearing token would be marginally better than a later one. Separating those needs a
   second control at a different content offset, which does not exist in this design.

---

## 8. The sentence

> **The data support the second of the three preregistered interpretations — `codeword ≈ control`,
> GIST — so CLAIM A must be narrowed to a decodability statement about the PROMPT, not about the
> codeword: the paired advantage of the codeword site is +0.0185 (95 % CI [+0.0042, +0.0328]),
> which does not survive the preregistration's own Holm correction within the SECONDARY family
> (permutation p = 0.0157 and sign-test p = 0.0129, both above α/8 = 0.00625), is under half the
> conjunctive MDE of a design that has power ≈ 1.000 at the δ = 0.15 it was sized for, and closes
> only a quarter of the headroom left by a control site nine tokens downstream — token-identical
> across concepts, carrying no concept token — that already decodes concept identity at 0.9261.**
>
> Uncorrected at α = 0.05, the same data give a small but statistically real
> `codeword >> control`. That branch is reported in full in §7 and is not withdrawn; it is not the
> branch the preregistered correction leaves standing.

---

## 9. Verification ledger

**18/18 checks PASS.** Every check binds a counted set, and a check that binds zero rows is a
FAIL, never a PASS.

| check | n bound | claim |
|---|---|---|
| `PRE-frozen` | 17 | the preregistration is FROZEN and every pinned `*_sha16` verifies against the file on disk |
| `CHK-W1W3` | 3 | every blocking pre-analysis item other than W2 (which this run computes) is marked done |
| `BANK-sha` | 8 | every run's `bank_rows_sha16` equals the preregistration's pin |
| `SITE-pos` | 8 | each run was extracted at the position its site declares |
| `ATTN` | 8 | every run used the preregistered attention implementation (`eager`) |
| `KO` | 8 | every run is the no-knockout baseline |
| `FAILREPORT` | 8 | every run reports `failures.n_failed` |
| `POP-bind` | 4520 | the population binds rows, and the same number, at both sites |
| `MISS-explained` | 9052 | every population row absent from a cache belongs to a preregistered whole-population exclusion (12 absent, 0 unexplained) |
| `ROWSET-identical` | 4520 | the two sites are analysed on identical row sets, keyed on `(bank, prompt_id)` |
| `ROWORDER` | 4520 | the two sites' row sequences are element-wise identical |
| `SPLIT-shape` | 113 | the analysed split is 113 domains = 67 / 23 / 23 |
| `LEAK-domain` | 90 | no domain appears in both train and test |
| `GRID` | 36 | the selection grid is the preregistered 9 layers × 4 C values |
| `BALANCE` | 23 | every test domain carries both concept arms in equal numbers |
| `GUARD-TEST` | 920 | the hyperparameter selection set contains zero test rows |
| `UNIT` | 113 | the independence unit is DOMAIN |
| `FLOOR` | 1 | the nuisance floor for the paired difference is 0.0 |

**14/14 mutations turned a check RED.** An unreachable check is not a guard; `--mutate` exits
non-zero if any mutation fails to fire.

| mutation | check that went RED |
|---|---|
| `wrong_sha` — a run's `bank_rows_sha16` disagrees with the pin | `BANK-sha` |
| `wrong_position` — the control run is demanded at the primary position | `SITE-pos` |
| `wrong_attn` — a run used a different attention implementation | `ATTN` |
| `knockout_on` — a run has a knockout applied | `KO` |
| `empty_population` — the population binds zero rows | `POP-bind` |
| `keep_excluded_domains` — the preregistered exclusions are not applied | `MISS-explained` |
| `drop_control_rows` — the control site loses 5 rows | `ROWSET-identical` |
| `shuffle_control_order` — the control rows are no longer row-aligned | `ROWORDER` |
| `corrupt_split` — five test domains are also train | `SPLIT-shape` |
| `empty_grid` — the selection grid is empty | `GRID` |
| `unbalanced_domain` — a test domain loses one concept arm | `BALANCE` |
| `select_on_test` — selection reads the test split | `GUARD-TEST` |
| `row_level_unit` — the independence unit becomes the row | `UNIT` |
| `surface_floor` — the 0.7065 surface floor is applied to the paired difference | `FLOOR` |

### Reproduction

```
python3 scripts/dcs_ts_pr051_positional.py --stop-after-w2          # W2 only, no data loaded
python3 scripts/dcs_ts_pr051_positional.py --stop-after-selection   # never reads TEST
python3 scripts/dcs_ts_pr051_positional.py --mutate                 # the full contrast
```

The run is deterministic: the bootstrap and permutation RNG is seeded from `split.seed`
(202609061). The full run was executed twice and reproduced every figure in this document to the
printed precision; the second execution differed only in adding the Holm-branch interpretation to
the printed output, with no change to any estimator.

---

## 10. Scope limits and what this does not settle

* **One control position.** `following` is a content position that passes W3's four criteria, but
  it is the only control in the design. The contrast cannot separate "the codeword is special"
  from "a codeword-bearing content position is marginally better than a later content position".
* **Two concepts.** knife vs gun. `bomb` is excluded from this contrast by the preregistration
  (declared before any probe ran) because its hedging register is a confound for the *absolute*
  measurement — noting that the pairing would have cancelled that confound too, so the exclusion is
  conservative here rather than necessary.
* **One model.** Llama-3.1-8B-Instruct, `eager`, bfloat16, revision `0e9e39f2`. Qwen3-14B is absent
  from both caches and `HF_HUB_OFFLINE=1` makes any Qwen job fail at load, so this is a Llama-only
  result **by decision**, recorded as a scope limit and **not** as a model-specificity claim.
* **One dose.** `n_examples = 4`. Doses are separate preregistered cells and are never pooled.
* **The `_analyzer_status` claim in the frozen config does not cover this file.**
  `artifacts.analyzer` names `scripts/dcs_ts_pr048_analysis.py`, which implements the absolute
  probe, not the paired contrast. `scripts/dcs_ts_pr051_positional.py` was written **after** both
  extractions completed, so it does **not** carry the "committed before the outcome exists"
  property that PR-048's analyzer does. What it does carry: it imports every estimator and
  convention from the frozen analyzer rather than reimplementing them, contains no numeric gate
  literal, and its W2 gate and interpretation trichotomy are both taken from the frozen config.
  That is weaker than pre-commitment and is stated as such.
* **W2 remains `done: false` on disk.** The frozen configuration was not edited by this run, in
  either direction. §2 answers W2; closing the checklist item is a separate, deliberate act.
