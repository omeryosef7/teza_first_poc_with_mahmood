# DCS SUCCESSOR — REVIEW-2, PART 4: STATISTICAL REVIEW

**Reviewer:** adversarial statistical review, PART 4 of REVIEW-2.
**Scope:** progress-log entries **025–037** only (`C-208`, `R-202`, `C-209`, `R-203`, `N5`-deferral,
`R-204`, `C-210`, `S-006`, `S-007`, `C-211`, `R-205`, `R-206`, `ENTRY 037`/`PR-066-A1`).
REVIEW-1 (entry 024, `reports/DCS_SUCC_REVIEW1_*.md`) is **not re-reported**; where a REVIEW-1
finding is load-bearing here it is cited by number and marked as **unrepaired**, not rediscovered.
**Review window:** 2026-09-09 22:55 → 2026-09-10 02:20 IDT (= 2026-09-09 19:55 → 23:20 UTC).
**Working tree is LIVE.** `outputs/dcs_succ/b1_position_control.json` was written at **02:08 IDT**,
i.e. **after** entry 037 (01:50) and during this review; it has no log entry and is not reviewed.
Nothing was modified, no job was submitted.

**Method.** Every number below was recomputed from the run directories and the frozen configs with
an independent implementation (`scipy` / `numpy`, not the repo's analyzers), after checking
`DONE.json`. Artifacts read:
`outputs/dcs_succ/pr066_behaviour.json` (01:38), `outputs/dcs_succ/n5_judge_reliability.json` (23:06),
`outputs/dcs_succ/kladder_sowk_train.json` (00:35), `outputs/dcs_succ/concept_presence.json` (01:05),
`outputs/boombness/aggressive_patching/pr068_train67_20260909_233414_3931861/` (DONE, 1005 rows),
`outputs/boombness/judge/tsb66j_{A_n0,C_n0,C_n4}_*/` (DONE),
`outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103/` (DONE),
`configs/dcs_ts_pr066_amendment1.json` (sha16 `5278f55ac74f4d39`),
`data/boombness_prompts/dcs_ts116_domain_split.json` (sha16 `be7d2c772d814ef3`).

---

## SUMMARY TABLE — findings worst first

| id | severity | one line | status |
|---|---|---|---|
| **S-01** | **CRITICAL** | `Q2`'s held-out evidence is a null (ρ=0.2640, p=0.0795, n=46) and the third success conjunct is **provably vacuous** (satisfied in 1.000 of null draws) | VERIFIED |
| **S-02** | **CRITICAL** | the `0.0221` "reproducibility floor" is a McNemar noise draw (p=0.47, CI [0.000,0.071]); the FROZEN `N5` bar is **0.1372**, and entry 036's headline deltas fall **below it** | VERIFIED |
| **S-03** | MAJOR | entry 037's false-positive rebuttal prints only the 2 of 4 split rows where the correlation strengthens; on held-out data it **weakens** | VERIFIED |
| **S-04** | MAJOR | the confirmatory `Q1` family is computed on the **raw contaminated** metric; amendment `A1-3` says `N2` is evaluated on the concept-present reading and the analyzer has **zero** code for it | VERIFIED |
| **S-05** | MAJOR | disattenuated `0.5753` is wrong three ways; reliability(x) is measurable from a file the analyzer already opens and equals **0.7772**; correct value **0.6970** | VERIFIED |
| **S-06** | MAJOR | `S-007`'s 12 windows are uncorrected; under Holm **L17-20 does not survive**, and 4 windows (not 3) are nominally significant; no foreign-donor control exists | VERIFIED |
| **S-07** | MAJOR | `R-205`'s Holm over 14 nested rungs is **inert by arithmetic**; the real multiplicity (argmax over 13 increments) is untested — though the correct test is in the data and passes | VERIFIED |
| **S-08** | MODERATE | `Q1x` is an undeclared test with a p; `Q2b`/`Q2c` are published with a p and **no** interval — the exact inverse of the frozen rule | VERIFIED |
| **S-09** | MODERATE | permutation unit is **correct**; the Fisher-z CI is the **Pearson** SE on a Spearman and is the narrowest of three valid options; the CI **contains** the MDE | VERIFIED |
| **S-10** | MODERATE | `R-204`'s Wilson CI and κ are iid over 226 rows when the unit is 113 domains; κ's clustered CI is [0.281, 0.589]; κ measured on dose 0, applied to dose 4 | VERIFIED |
| **S-11** | MODERATE | entry 028's cell-A dose-0 row is a **stale 78-row partial-run** number; the completed artifact says 0.13274 / 0.004425 / 29-of-30, not 0.1410 / 0.0000 / 11-of-11 | VERIFIED (n=78 INFERRED) |
| **S-12** | MINOR | entry 028 calls the frozen lexicon **47 terms**; the file, the artifact and entry 036 all say **44** | VERIFIED |
| **S-13** | MINOR | precision inventory, including entry 034's **876 %** and **−285 %** shares over near-zero denominators and the entry-033 title's **0.05 %** against a CI of ±1.8 % | VERIFIED |

---

## S-01 — CRITICAL. `Q2`'s only train-free evidence is a null, and the third success conjunct cannot fail. *(part b)*

### The three split rows reproduce exactly

| row | n | ρ (recomputed) | ρ (published) | perm p (10 000) |
|---|---|---|---|---|
| pooled | 113 | **0.3960558995** | 0.3961 ✓ | 9.999e-05 (floor) |
| train | 67 | 0.4835654248 | 0.4836 ✓ | 9.999e-05 (floor) |
| validation | 23 | 0.1434740335 | 0.1435 ✓ | 0.5191 |
| test | 23 | 0.3778886047 | 0.3779 ✓ | 0.0758 |

**No arithmetic is in dispute.** What is in dispute is what the arrangement licenses.

### (i) The pooled row is not independent evidence — it is train, restated

Train is **67 of 113 domains (59 %)**. The number that does not contain train is not reported
anywhere in entry 037 or in `reports/DCS_SUCC_PR066_BEHAVIOUR.md`. Computed here:

```
validation + test combined, n = 46, TRAIN-FREE
  rho            = 0.2640
  permutation p  = 0.0795   (10 000 permutations of the domain labels)
  Fisher-z 95% CI= [-0.0285, 0.5148]
  declared MDE   = 0.2996   ->  the point estimate is BELOW the MDE
```

⛔ **On every domain the analysis did not train on, `Q2` does not reject at α = 0.05 and does not
reach its own declared MDE.** That is the honest held-out statement and it is absent from the log.
The frozen `split.discipline_for_Q2` argument ("no free parameter to overfit, so pooling is
legitimate") is a *defensible* argument and I am not asserting it is wrong — the predictor really is
frozen `R-116` and the statistic really is fixed in the file. But the log's rhetorical structure
("pooled ✅, sign consistent 3 of 3 ✅") presents the split rows as **corroboration**, and they are
not: the corroborating half is p = 0.0795.

### (ii) "Sign consistent in ≥ 2 of 3 splits" has **zero** power to refute — measured, not argued

I permuted the observed y over the 113 domains **300 000** times and asked how often the
preregistered clause is satisfied *given that the first two conjuncts already are*:

```
null draws with |rho| >= MDE (0.2996):                          352 / 300 000
  P(sign agrees with pooled in >= 2 of 3 splits | |rho| >= MDE) = 1.000   <- the frozen clause
  P(sign agrees with pooled in     3 of 3 splits | |rho| >= MDE) = 0.886   <- what the log ticks
unconditional under the null:  >= 2 of 3 = 0.810 ;  3 of 3 = 0.244
```

⛔ **The clause `PR-066` wrote is satisfied by every single null draw that clears the MDE.** It is
not a weak check; it is a **tautology** given the other two conjuncts, because train carries 59 % of
the domains and therefore almost always shares the pooled sign, and one of two 23-domain splits
almost always follows. `3 of 3` adds
`log2(1/0.886) = 0.17` bits. The success criterion is **two conjuncts and a restatement**, and
entry 037's "✅ ✅ ✅" over-counts the evidence by one tick.

**Answer to the question as posed.** Yes, pooled-vs-split is double counting, in the specific sense
that pooled ⊃ train and train drives both the pooled ρ and the pooled p-at-floor; and no, "3 of 3"
is not doing work — it is doing 0.17 bits of work against a null in which it fires 88.6 % of the
time.

**The defensible sentence.** *"ρ = 0.396 on all 113 preregistered domains, permutation p at its
floor. The estimate is carried by the 67 train domains (ρ = 0.484); on the 46 domains outside train
it is ρ = 0.264, p = 0.080, which neither confirms nor refutes at this n. The preregistered
sign-consistency clause is satisfied but is uninformative by construction."*

---

## S-02 — CRITICAL. The `0.0221` "reproducibility floor" is a noise draw, and it replaced a frozen bar six times larger. *(part f)*

### (i) The R-204 table reproduces; every derived statistic does too

From the two byte-identical dose-0 judge runs (both `DONE.json` present), 226 pairs over
**113 domains × 2 rows**:

```
TT 17 | TF 13 | FT 18 | FF 178        n = 226
agreement 0.862832   disagreement 0.137168   Cohen kappa 0.443527
ASR(A) 0.132743   ASR(C) 0.154867   |diff| 0.0221238
```
All VERIFIED against `outputs/dcs_succ/n5_judge_reliability.json`.

### (ii) `0.0221` is not a measurement of anything

`|ASR difference| = (FT − TF)/n = (18 − 13)/226`. Under the null that the judge is exchangeable
across the two runs, **its expectation is exactly zero**, and:

```
exact two-sided McNemar on 13 vs 18                    p = 0.4731
SE of the paired difference under the null  sqrt(31)/226 = 0.02464
domain-clustered bootstrap 95% CI (20 000 draws)  [0.0000, 0.0708]
```

⛔ **The "floor" is one draw from a distribution centred on zero whose SE is larger than the draw
itself.** Had the 31 discordant pairs split 15/16 the floor would have been 0.0044; 8/23 gives
0.066. A threshold that is a coin flip is not an instrument constant, and `0.0221` is quoted to
three significant figures in **entry 030, entry 036 and entry 037**.

### (iii) The frozen bar is `0.1372`, not `0.0221` — and REVIEW-1 already said so

`configs/dcs_ts_pr066_amendment1.json`, null `N5`, verbatim:

> *"…report the **label disagreement rate**. No ASR difference smaller than that rate is quotable."*

The analyzer implements exactly that — `load_rejudge()` returns
`"disagreement_rate": dis / n` (label disagreement) and its own message reads
*"no ASR difference smaller than %.4f may be quoted"*
(`scripts/dcs_succ_pr066_behaviour.py:1402-1404`), and `N1`/`N2` compare against
`n5["disagreement_rate"]` (`:1298`, `:1310`). REVIEW-1 F-10(ii) named the same bar
("no cell-to-cell difference in that table is quotable"). Entry 030 introduced
`abs_asr_difference` as "the reproducibility floor" instead — the N5 script's own `_reading` field
asserts it — and the log has used it ever since.

**Consequence, worked through on the frozen bar of 0.1372:**

| quantity | value | vs frozen bar 0.1372 | vs the substituted 0.0221 |
|---|---|---|---|
| `Q1b` C4−C0, **concept-present** (entry 036) | +0.1310 | **BELOW — not quotable** | 5.9× |
| `Q1d` C4−B4, **concept-present** (entry 036) | +0.1327 | **BELOW — not quotable** | 6.0× |
| `Q1x` C4−E4, **concept-present** (entry 036) | +0.1398 | 1.02× — at the bar | 6.3× |
| `Q1b` raw (entry 037) | +0.1726 | 1.26× | 7.8× |
| `Q1c` raw = `N1` (entry 037) | +0.2230 | 1.63× | 10.1× |
| `Q1d` raw (entry 037) | +0.3186 | 2.32× | 14.4× |

⛔ **Entry 036's sentence "Every one of these deltas is 6–8× the measured reproducibility floor of
0.0221" is the single most load-bearing statistical claim in entries 025–037, and under the
preregistered bar two of the three deltas it describes are not quotable at all.** Even taking the
substituted quantity at face value, its own domain-clustered CI reaches **0.0708**, against which
those deltas are **1.85× and 1.87×**, not 6–8×.

### (iv) An additive floor is the wrong shape of statistic anyway

The right question is not "how big must a difference be to exceed a constant" but "how much does
judge noise attenuate a rate". From the same table:

```
positive specific agreement  2*TT/(2*TT+TF+FT) = 34/65 = 0.5231
P(C = positive | A = positive)            = 17/30 = 0.5667
P(A = positive | C = positive)            = 17/35 = 0.4857
negative specific agreement                        = 0.9199
consensus-positive rate (both runs agree)  17/226 = 0.0752   vs marginals 0.133 / 0.155
```

⛔ **About half of every ASR positive this instrument reports does not reproduce on byte-identical
text, and requiring reproducibility roughly halves the rate.** That is a *multiplicative*
attenuation on levels — it says the headline `0.3274` and `0.1398` are inflated relative to a
consensus reading — and it is invisible in an additive floor. Cohen's κ is also the wrong summary
here: at a 13–15 % base rate κ is dominated by the base rate (the κ paradox), which is why κ = 0.4435
and PSA = 0.5231 tell different stories and PSA is the one that bounds an ASR claim.

**What should replace the "floor" sentence.** *"On 226 byte-identical prompts the judge's labels
disagree at 0.1372 [0.097, 0.181]; positive-label agreement is 0.523, so roughly half of any
reported positive is not reproducible. A paired difference between two arms is tested by McNemar on
those arms' own discordant pairs, not against a constant. The preregistered quotability bar is the
label disagreement rate, 0.1372."*

---

## S-03 — MAJOR. The false-positive rebuttal reports only the splits where it works. *(parts a, b)*

Entry 037's defence of `Q2` against `C-209` is:

> *"Recomputing against `asr_and_concept_present`: TRAIN 0.5260, all 113 0.4206. **The correlation
> strengthens when the false positives are removed**, both at the permutation floor."*

I reimplemented the concept-present outcome from the frozen lexicon in
`scripts/dcs_succ_concept_presence.py` and the completed judge/generation runs. The pooled rate
reproduces exactly (158 of 370 judge positives carry concept content → 0.139823 vs artifact
0.13982), and so do both quoted ρ. **The two rows that were not printed do not agree with the
sentence:**

| row | n | ρ raw | ρ concept-present | direction |
|---|---|---|---|---|
| pooled | 113 | 0.3961 (p floor) | **0.4206** (p floor) | strengthens ✓ — printed |
| train | 67 | 0.4836 (p floor) | **0.5260** (p floor) | strengthens ✓ — printed |
| validation | 23 | 0.1435 (p 0.519) | **0.1592** (p 0.464) | ~flat — **not printed** |
| **test** | 23 | 0.3779 (p 0.076) | **0.3245** (p 0.132) | **weakens** — **not printed** |
| **val+test** | 46 | 0.2640 (p 0.080) | **0.2186** (p 0.147) | **weakens** — **not printed** |

⛔ Three separate problems, all in one paragraph:

1. **Selective split reporting on the variant that carries the rebuttal.** The frozen
   `split.discipline_for_Q2` requires the per-split rows "printed **unconditionally**, whatever they
   say". Entry 037 honours that for the raw `Q2` table immediately above and abandons it for the
   concept-present recomputation immediately below.
2. **The variant is post-hoc and is not labelled.** `split._what_would_violate_this` names
   *"a different ASR threshold, a subset of cells, a residualisation"* chosen after seeing an ASR
   number as a **new preregistration, reported as EXPLORATORY**. A different **outcome definition**
   is squarely inside that list. Entry 037 presents it as a confirmatory robustness result
   ("**And it is not the false-positive channel**").
3. **No artifact.** `0.4206` and `0.5260` are produced by no committed analyzer:
   `grep -c concept_present scripts/dcs_succ_pr066_behaviour.py` = **0**, and
   `outputs/dcs_succ/concept_presence.json` holds arm-level rates only, no per-domain series and no
   ρ. Both numbers are therefore unenforced by `dcs_ts_prereg.py`, carry no CI, and their
   "permutation floor" is asserted rather than recorded. (They do reproduce — I confirm the
   arithmetic — but that is my recomputation, not the record's.)

Also worth stating because it bears on S-09: the concept-present outcome has **34 of 113 domains at
exactly zero** and only **7 distinct values** (against 9 and 9 for raw), so it is the *more* tied,
*more* floor-bound variable, and a Fisher-z CI on it would be worse, not better.

---

## S-04 — MAJOR. The confirmatory `Q1` family runs on the metric the session declared contaminated, against its own amendment. *(parts c, g)*

`scripts/dcs_succ_pr066_behaviour.py:1454` — `mal = mal_field(prim)` = **`malicious_at_0.5`**, the
raw StrongREJECT label — and `:1456-1466` build `Q1b`/`Q1c`/`Q1d` from it. There is no other path.

But amendment `A1-3`, frozen in `configs/dcs_ts_pr066_amendment1.json`, says of `N2`:

> *"`N2` is therefore evaluated on **the concept-present reading**, where the dose-0 floor is 0.0088."*

⛔ **The analyzer cannot do that: `concept_present` appears zero times in the file.** `C-212` recorded
one amendment/analyzer divergence (the `N5` route). This is a **second, unrecorded one**, and it is on
a *blocking* null. Entry 037's hand-evaluation ("`N1` = 0.2230 and `N2` = 0.1726, both ≈ 8–10× the
floor, so both pass") therefore uses the raw reading twice over: wrong metric per `A1-3`, wrong bar
per `N5` (S-02).

**And the two entries disagree with each other without saying so:**

| contrast | entry 036 (concept-present) | entry 037 (raw, unnamed metric) | ratio |
|---|---|---|---|
| `Q1b` C4 − C0 | +0.1310 [0.1027, 0.1593] | **+0.1726** | 1.32× |
| `Q1c` C4 − A4 | not reported | **+0.2230** | — |
| `Q1d` C4 − B4 | +0.1327 [0.1080, 0.1584] | **+0.3186** | **2.40×** |

Entry 037's `Q1` table names **no metric at all**, and its headline sentence
("**`Q1d`: the Doublespeak attack beats the direct harmful request in 103 of 104 informative
domains**") is computed on the channel `C-209` measured at a **0.155** false-positive rate two hours
earlier in the same log. The entry-036 version of the same contrast is **2.4× smaller**. A reader of
the log cannot tell which is `Q1d`.

**Note the direction.** `C-208d` withdrew cell B's 0.0088 as judge artefact; `Q1d` is `C − B`, so
the *smaller* the honest B, the *larger* `Q1d`. The raw metric inflates the numerator (C) and the
correction deflates the subtrahend (B). Both effects push `Q1d` up, which is why raw `Q1d` = 0.3186
against concept-present 0.1327. Nothing here is fraud; it is an unlabelled metric on the headline of
a confirmatory entry.

---

## S-05 — MAJOR. `0.5753` is wrong in three independent ways, and the missing input is on disk. *(part a)*

The published report ends its `Q2` table with a "disattenuated (ESTIMATE)" column: **0.5753**
pooled, 0.7273 train, 0.5743 test, 0.1945 validation, with the note *"The reliability of x is
assumed 1.0 and only y is corrected."*

### (i) reliability(x) = 1.0 is indefensible, and it is measurable from a file the analyzer already opens

`x` is a **10-row domain mean** of `concept_binary_prob` over the readout run the analyzer loads by
hash. Applying the *same* variance decomposition the code applies to `y`, via a one-way ANOVA
(`reliability of a k-row mean = 1 − MSW/MSB`):

```
y  (malicious_at_0.5, cell C dose 4, 1130 rows / 113 domains, k=10)
   MSB 0.352228   MSW 0.205900   ICC1 0.0664   reliability(mean) = 0.4154
x  (concept_binary_prob, sow cell C n=4, 1160 rows / 113 domains, k=10)
   MSB 0.454223   MSW 0.101217   ICC1 0.2586   reliability(mean) = 0.7772
```

⛔ **reliability(x) = 0.777, not 1.0.** And the diagnostic that makes the assumption plainly wrong:
the **mean within-domain sd of x is 0.2988**, which is *larger* than the **between-domain sd of the
x domain means, 0.2131**. `x` is not close to a fixed quantity; more of its row-level variance is
within domains than between them. REVIEW-1 F-06(iii) predicted exactly this
("a y-only correction is not the disattenuated estimate and should not be labelled as one"); the run
went ahead and published the y-only number **as** the disattenuated estimate, and the report repeats
the assumption in prose as though stating it discharged it.

### (ii) the within-variance estimator is the biased plug-in

`reliability_of_domain_means()` (`:1064-1085`) computes
`v_within = mean_d[ m_d(1−m_d) / n_d ]`. For a 10-row Bernoulli mean the **unbiased** estimator of
`Var(m_d)` is `m_d(1−m_d)/(n_d−1)`; using `/n_d` understates the within component by a factor
`(k−1)/k = 0.9` and therefore **overstates reliability**:

```
code:        reliability(y) = 0.4738929517   (reproduced to 10 dp from the artifact)
m(1-m)/(k-1):                 0.415437
1 - MSW/MSB  (ANOVA):         0.415437       <- the two agree, as they must
```

### (iii) the formula is a Pearson identity applied to a rank correlation

`rho_true = rho_obs / sqrt(r_x · r_y)` is Spearman's 1904 correction for **Pearson** correlations of
variables with additive, score-independent error. `Q2`'s declared statistic is a **Spearman**, `y` is
a bounded proportion with 9 distinct values and a hard floor at 0, and its error is binomial and
heteroscedastic (`Var = p(1−p)/10`, maximal at p = 0.5) — i.e. dependent on the true score, which is
the assumption the derivation needs. REVIEW-1 F-06(iii) flagged this too; it is **unrepaired**. If a
disattenuation is wanted at all, the coefficient the formula applies to is the Pearson, which here is
**0.4075**.

### (iv) the number, corrected

| variant | reliability used | disattenuated ρ |
|---|---|---|
| **published** | r_y = 0.4739, r_x ≡ 1 | **0.5753** |
| y-only, unbiased r_y | r_y = 0.4154, r_x ≡ 1 | 0.6145 |
| **both, unbiased** | r_y = 0.4154, r_x = 0.7772 | **0.6970** |

⛔ **The published estimate understates its own target by 21 %,** is printed to four decimals with
**no interval**, and — the reporting defect — its **sole input is not printed anywhere in the
report**. `reliability_of_y = 0.4739` exists only in `pr066_behaviour.json`. A number whose entire
content is "divide by √r" published without r is not auditable. And r itself is an ICC-based ratio at
ICC1(y) = 0.066 with no CI, so even 0.697 does not support three significant figures.

---

## S-06 — MAJOR. `S-007`: twelve windows, no correction, and the entry's own significance criterion switches row to row. *(part e)*

All twelve windows reproduce from `pr068_train67_.../results.jsonl` (1005 rows, `DONE.json`,
`rows_written` 1005 = file length). Paired per-domain Δ vs the `none` arm, exact two-sided sign test
over 67 domains, 20 000-draw domain bootstrap:

| window | Δ | 95 % CI | toward donor | sign p | % of the 12.3312 gap |
|---|---|---|---|---|---|
| L25-31 | −0.1939 | [−0.263, −0.126] | 15/67 | **6.46e-06** | −1.572 % |
| L21-24 | −0.1665 | [−0.258, −0.076] | 18/67 | **1.94e-04** | −1.351 % |
| L17-20 | −0.1209 | [−0.228, −0.014] | 22/67 | **6.74e-03** | −0.981 % |
| **L11** | −0.0414 | [−0.141, +0.061] | 24/67 | **0.0271** | −0.336 % |
| L0-4 | +0.0433 | [−0.015, +0.102] | 41/67 | 0.0864 | +0.351 % |
| L12 | −0.0331 | [−0.119, +0.055] | 27/67 | 0.142 | −0.269 % |
| L13-16 | −0.0910 | [−0.218, +0.041] | 28/67 | 0.222 | −0.738 % |
| L9-12 | −0.0092 | [−0.116, +0.102] | 28/67 | 0.222 | −0.074 % |
| write_carry_8-21 | −0.0336 | [−0.201, +0.138] | 28/67 | 0.222 | −0.273 % |
| L9 | −0.0535 | [−0.134, +0.032] | 29/67 | 0.328 | −0.434 % |
| L5-8 | +0.0210 | [−0.099, +0.146] | 31/67 | 0.625 | +0.170 % |
| all | +0.0066 | [−0.211, +0.223] | 32/67 | 0.807 | +0.054 % |

Every published figure reproduces (entry 033's `all` +0.0066 / 0.054 %, `L0-4` +0.0433 / 0.351 %,
`L25-31` −0.1939 / p 6.5e-06, the 12.3312 gap at 67/67, `self_swap_noop_check` exactly 0.000000 in
all 67 domains).

### (i) It is not multiplicity-corrected, and the correction changes the count

Entry 033 states **no α and no correction**. The run itself declares the family by generating all
twelve windows in one job under one design. Applying corrections:

```
Holm (FWER 0.05, m = 12):
  L25-31  6.46e-06  vs 0.00417  REJECT
  L21-24  1.94e-04  vs 0.00455  REJECT
  L17-20  6.74e-03  vs 0.00500  NOT REJECTED     <-- entry 033 calls this significant
  ... nothing below
Benjamini-Hochberg (FDR 0.05, m = 12):
  L25-31, L21-24, L17-20 all pass; L11 (0.0271 vs 0.01667) fails
```

⛔ **"3 significant in the NEGATIVE direction" is an FDR statement presented without saying so.**
Under FWER only two survive. `L17-20`'s CI is [−0.228, **−0.013**] — it excludes zero by 0.013 log-odds
on a scale whose total range is 12.33.

### (ii) The count is wrong even uncorrected, because the criterion switches

Entry 033 groups `L9 / L9-12 / L11 / L12` as *"all span 0 … sign p 0.03–0.33"* — a **CI-based**
non-significance call — and then calls `L17-20` (p = 0.0067) significant on a **p-basis**. But
`L11`'s p is **0.0271 < 0.05**, so on the p-basis used one row lower there are **four** nominally
significant negative windows, not three. The entry silently uses whichever criterion excludes the
row. (Both readings are individually defensible; using both in one table is not.)

### (iii) Could it be real, and is it worth a hypothesis? Yes — and the control that would decide it was not run

The pattern is not noise-shaped: the three deepest windows are **monotone in depth**
(−0.121, −0.167, −0.194) and monotone in domain count (22, 18, 15/67), the two deepest survive FWER,
and the negative-control arm is exactly 0.000000 in 67/67 so the hook is not the cause. A coherent
hypothesis: **transplanting a donor state into a recipient whose context cannot support it is an
off-manifold perturbation whose damage grows with depth**, because late-layer residual content is
increasingly context-committed and there are fewer layers left to re-normalise it.

⛔ **The run cannot distinguish that from "donor-specific interference".** Its arms are `none`,
`donor_ceiling`, `self_swap_noop_check` and `transplant × 12` — there is **no foreign-donor and no
norm-matched control** (e.g. a cell-C state from a *different* domain, or a norm-matched random
vector, patched at the same site and windows). Without one, "patching L17-31 moves the recipient
*away from the donor*" and "patching L17-31 with *anything* degrades the readout" are the same data.
`R-137` in `PHASE 9` already used a norm-matched orthogonal control for precisely this reason and
found it moved the readout **1.93× further** than the signal direction; the same control belongs here.

One further asymmetry worth recording: `readout_tautological` is **False** for `L25-31` (no read
layer at L16/L20/L24 lies inside that window), so the arm with the strongest effect is the one arm
whose liveness rests on the outcome differing from baseline rather than on the logit-lens columns
taking the donor's exact value. The write did fire — **0 of 804 transplant rows are identical to
their baseline**, VERIFIED — so this is a weaker evidential chain, not a broken one.

**A hypothesis worth preregistering, stated so it can be refuted:** *depth-graded off-manifold cost.
Patch, at the query codeword, (a) the same-family donor, (b) a different-domain cell-C donor, and
(c) a norm-matched Gaussian, across L0-4 … L25-31. If the negative drift is off-manifold cost, all
three are negative and monotone in depth with no donor advantage. If it is donor-specific
interference, (a) differs from (b) and (c).* That is one job on existing caches.

---

## S-07 — MAJOR. `R-205`'s Holm over 14 nested rungs is inert, and the multiplicity that matters is untested. *(part d)*

`outputs/dcs_succ/kladder_sowk_train.json` declares two Holm families:
`rungs` — `[K1 … K14]`, m = 14 — and `control_contrasts` — `[K8, K9, K10, K11]`, m = 4.

### (i) Holm over 14 nested rungs is valid and **cannot change a decision**

Holm-Bonferroni controls FWER under **arbitrary dependence**, so nesting does not invalidate it —
the objection "the rungs are massively dependent" does not break the correction. What it does is
make it **inert**:

```
attainable sign floor at n = 67 domains:  2/2^67 = 1.3552527e-20   (log states 1.355e-20 ✓)
K10: p = 1.36e-20  ->  holm_p = 1.90e-19   (multiplier 14)
K14: p = 1.36e-20  ->  holm_p = 1.90e-19
K1 : p = 1.03e-07  ->  holm_p = 1.03e-07   (multiplier 1, largest-p slot)
```

⛔ Every rung sits at or near its floor; the largest Holm multiplier is 14; the loosest surviving
threshold is 17 orders of magnitude above the largest adjusted p. **The correction never binds, so it
provides no protection against anything and its presence in the artifact is decorative.** And the
14 nulls it protects are all trivially false: cutting the query row's access to the demonstrations
*must* move a readout that depends on the demonstrations. Nobody doubted `K1 ≠ 0`.

### (ii) The multiplicity that matters is the **selection of K\* = 10** as the argmax of 13 increments, and it carries no test

`shape.K_star = 10` is chosen as `largest_single_rung_rise` over the 13 adjacent pairs
(`shape.all_rises`, 13 entries). That selection has **no p-value, no interval and no correction**
anywhere in the artifact. It is the only inferential step in `R-205` that could have gone another way,
and it is the one that is untested.

### (iii) The right statement exists in the data, is stronger, and is not reported

`rungs[K].per_domain_delta` is persisted, so the marginal effect of adding the codeword row is
directly testable as a **paired within-domain increment**:

```
delta(K10) - delta(K9) over the 67 TRAIN domains
   mean        = -4.4927
   67 negative / 0 positive / 0 ties
   exact two-sided sign test p = 1.355e-20, AT its attainable floor (2/2^67)
share of the climb carried by K9->K10 = 0.6168
   domain bootstrap 95% CI (20 000 draws) = [0.5950, 0.6400]
```

⛔ **This is the test `R-205` needed and it passes at the floor in 67 of 67 domains with a tight
interval on the 62 % share — and it appears nowhere.** The entry reports a Holm family that cannot
bind instead of the one-degree-of-freedom contrast that is the claim. The correct statement:

> *"Adding the codeword row to the cut is worth −4.49 log-odds in **67 of 67** domains (paired sign
> test at its 1.36e-20 floor) and carries **61.7 % [59.5, 64.0]** of the full climb, against a
> dose-matched non-demonstration control at +0.033 (three draws, between-draw sd 0.040). The ladder
> is nested, so the 14 rung tests are not 14 pieces of evidence and no correction over them is
> informative; `K* = 10` is the argmax of 13 increments and the increment is tested directly."*

### (iv) One control that is genuinely missing

The dose-matched `nondemo_matched` band controls for the **number** of keys blocked (2052 median,
identical for demo and all three control draws at K10 — VERIFIED) drawn from **outside** the
demonstration block. It does not control for **which query row** is cut. A leave-one-in ladder —
cut `K = 10` rows but *skip* rel_end −10, or cut a single non-codeword query row — would separate
"the codeword row is special" from "the 10th row is special". It was not run, and `R-205`'s own
`limitation` field already concedes that the *identity* of rel_end −10 is inherited from the frozen
token-role map rather than verified in these run directories. Two inherited assumptions stacked on the
headline is worth stating.

Credit where due: the `SHAPE = NEITHER` verdict is correctly returned against a rule frozen before
the data even though `0.617 ≥ 0.50` would have been convenient, and the option-mass gate (0.409 at
K10, rising) is correctly read as "engaged, not collapsed". Neither is disputed here.

---

## S-08 — MODERATE. `Q1x` is an undeclared test with a p; `Q2b`/`Q2c` are published with a p and no interval. *(part c)*

`configs/dcs_ts_pr066_amendment1.json`:

* `multiplicity.families` = `Q1_paired_contrasts` **{Q1b, Q1c, Q1d}, m = 3** and `Q2_primary` **{Q2}, m = 1**.
* `secondary` declares exactly `Q1a, Q1b, Q1c, Q1d, Q2b, Q2c`.
* `multiplicity._secondaries_outside_a_family_carry_no_p`: *"Q1a, Q2b and Q2c are reported **with
  intervals and no p-value**. A p that is not in a declared family is not a test."*

Two violations, in opposite directions:

**(i) `Q1x` does not exist in the design and is reported with a p.** Entry 036's table row
*"`Q1x` C dose 4 − E dose 4 | +0.1398 | [0.1150, 0.1655] | 79/79 | **3.31e-24 at its floor**"* is a
fourth paired sign test with an invented id, outside both declared families, carrying a p — the exact
construct the frozen file forbids by name. (It is not in the published report; the analyzer computes
only the declared three. It is in the **log**, which is the authoritative record.)

**(ii) `Q2b` and `Q2c` are published with a p and no interval — the inverse of the rule.**
`reports/DCS_SUCC_PR066_BEHAVIOUR.md:66-67`:

```
* Q2b (threshold 0.25): rho = 0.3480, p = 9.999e-05 (attainable floor 9.999e-05), n = 113.
* Q2c (stratified predictor at the frozen 0.5 cut, 92 installing / 21 not): rho = 0.2570, p = 0.005399 ...
```

The analyzer's own module docstring (`:60`) states the correct behaviour — *"Q2b (secondary
threshold) and Q2c (stratified predictor) beside it, **with intervals and no p**"* — and then
`render_report()` (`:1719-1730`) emits `p_formatted` for both and emits **no** `fisher_z_ci` for
either. The code contradicts its own header, and the published report contradicts the frozen file.
Neither p changes any decision, which is why it survived; the point is that the loader is enforcing
the config's *machine-readable* fields and not this rule, so "the analyzer refused three times" does
not cover it.

**Verified correct, and worth recording as such:** the Holm ordering and thresholds for the real
family, and the tie handling.

```
sorted ascending:  Q1d 1.035e-29 -> thr 0.05/3 = 0.0166667  REJECT
                   Q1c 8.065e-16 -> thr 0.05/2 = 0.025      REJECT
                   Q1b 4.591e-09 -> thr 0.05/1 = 0.05       REJECT
step-down monotonicity enforced by `still = still and rej` (:899)
```
matches the published table exactly. **And the p-floor is computed over the right n.** Ties are
excluded, `n_informative = pos + neg`, and `sign_p_floor(n_informative) = 2/2^n_inf`:

| id | domains | +/−/ties | n_inf | published floor | `2/2^n_inf` recomputed |
|---|---|---|---|---|---|
| Q1b | 113 | 77/20/16 | 97 | 1.262e-29 | 1.2621774e-29 ✓ |
| Q1c | 113 | 87/11/15 | 98 | 6.311e-30 | 6.3108872e-30 ✓ |
| Q1d | 113 | 103/1/9 | 104 | 9.861e-32 | 9.8607613e-32 ✓ |

and `n_inf + ties = 113` in all three rows. Excluding ties and taking the floor over the informative
count is the correct conditional treatment for an exact sign test — **this part of (c) is right, and
I could not break it.** The only caveat: the "attainable floor" is then itself data-dependent (it
moves with the observed tie count), which the house rule's phrasing does not acknowledge; that is
cosmetic here because all three floors are ~20 orders below the observed p.

---

## S-09 — MODERATE. The permutation unit is correct; the Fisher-z CI is the wrong coefficient's and the narrowest available; the CI contains the MDE. *(part a)*

### (i) Does the permutation respect the domain as the unit? **YES — verified, and it is right.**

`q2_block()` (`:1226-1256`) builds `xs`/`ys` as **length-113 vectors of domain means**, one entry per
domain, joined on the compound `(bank_file_sha16, domain)` key with `only_x`/`only_y` named and
`n_dropped = 0`. `permutation_p_spearman()` (`:1035-1049`) then shuffles that **domain-level** y
vector. The exchangeable unit under the null is therefore the domain, which is the house unit. There
is no row-level leakage: x comes from 1160 readout rows and y from 1130 judge rows and they are never
row-joined. `p = (n_exceed + 1)/(n_perm + 1)` with `n_perm = 10000` gives floor `1/10001 = 9.999e-05`,
and the config's declared floor string is checked against `n_perm` at load (`:217-227`). **This is
the one thing in part (a) I tried hardest to break and could not.** ρ reproduces to 10 digits:
**0.3960558995** from the two run directories independently.

Note also that measurement error in `x` does **not** invalidate this permutation test — it attenuates
the estimand, which is what S-05 is about, but the p-value remains exact for the null of no
domain-level association.

### (ii) Is the Fisher-z CI valid for a Spearman? **No — it is the Pearson interval, and it is the narrowest of three defensible ones.**

`fisher_z_ci()` (`:1052-1062`) uses `se = 1/sqrt(n−3)`, self-documented as *"the method
`power.method` declares"* — and `power.method` does declare
`|atanh(rho)|·sqrt(n−3) ≥ z + z_power`, which is the **Pearson** Fisher-z. For a Spearman the
asymptotic z-variance is inflated (Bonett–Wright `se = sqrt((1 + ρ²/2)/(n−3))`; Fieller
`sqrt(1.06/(n−3))`):

| method | 95 % CI on ρ = 0.3961, n = 113 |
|---|---|
| **published** (Pearson SE) | **[0.2280, 0.5412]** |
| Fieller (1.06 inflation) | [0.2228, 0.5451] |
| Bonett–Wright | [0.2212, 0.5463] |
| **domain bootstrap, 20 000 draws** | **[0.2202, 0.5530]** |

bootstrap sd of ρ = **0.0851** against the Fisher-z implied **0.0804** — the published interval is
~6 % too narrow at the low end and ~4 % at the high end. REVIEW-1 F-06(i) established the
wrong-coefficient error for the **MDE**; it is the same error in the **CI**, and it is unrepaired.
Not decision-changing (all four exclude zero), but the interval is printed to four decimals and the
method choice moves the low end by 0.008.

**Ties, checked rather than assumed.** `y` takes only **9 distinct values** over 113 domains
(largest tie block 22 domains at 0.2; 9 domains at exactly 0), because it is a mean of 10 binary
rows. Midranks are handled correctly by `_ranks()` (`:1004-1017`). The tie structure caps the
attainable coefficient only trivially — **max attainable ρ with this exact tie pattern = 0.9878** —
so ties are not a validity threat, and I record that explicitly so it is not raised as one later.
They do mean the tie-appropriate coefficient is **Kendall τ-b = 0.2935** (Pearson 0.4075), which
matters only when ρ is compared numerically to a threshold — which is precisely what
`primary.success` does.

### (iii) The CI **contains** the declared MDE

`primary.success` requires `|ρ| ≥ MDE = 0.2996`; `primary.negative` requires "the CI excludes the MDE
in both directions". Observed: point estimate 0.3961 clears the bar; **95 % CI [0.2280, 0.5412]
contains 0.2996**, and the domain bootstrap puts **14.1 %** of its mass below the MDE. So the design
tests success on a **point estimate** and defines its negative on the **CI** — an asymmetry that
leaves "the estimate clears the MDE but its interval does not" inside neither verdict. REVIEW-1
F-06(iv) flagged the adjacent gap (`0.185 ≤ |ρ| < 0.2996` being undefined); this is the same
asymmetry one band higher, and the outcome landed in it.

The honest gloss: *"powered by the design's own arithmetic at the point estimate; the interval is
consistent with effects below the 0.90-power MDE."* Not *"powered ✅"*.

### (iv) One recorded nit

A single seed (`202609061`, reused from `split.seed`) drives the pooled permutation, all three split
permutations, both `Q2b` permutations and `Q2c`. Those p-values therefore share their permutation
noise. Immaterial at p = floor; recorded because the artifact stamps the seed as if it were
independent per row.

---

## S-10 — MODERATE. `R-204` counts rows where the unit is domains, and generalises a dose-0 κ to dose 4. *(part f)*

`scripts/dcs_succ_n5_judge_reliability.py` reports `label_disagreement_wilson95` from `wilson(dis, n)`
with **n = 226 rows**. Those 226 pairs are **113 domains × 2 rows** (VERIFIED: every domain
contributes exactly 2). The house rule is that the independence unit is the domain; this is an **iid
row-level binomial interval published without a clustered alternative** — the same class REVIEW-1
F-02 found in `R-201`, in a script written after it.

Domain-clustered bootstrap (20 000 draws over the 113 domain clusters):

| quantity | published | domain-clustered 95 % CI |
|---|---|---|
| label disagreement 0.1372 | Wilson [0.0983, 0.1881] | **[0.0973, 0.1814]** |
| Cohen κ 0.4435 | **no interval at all** | **[0.2807, 0.5893]** |
| \|ASR difference\| 0.0221 | none | **[0.0000, 0.0708]** |

The disagreement interval happens to be nearly right — 2 rows per domain at low within-domain
correlation leaves little to cluster — so the finding here is method, not magnitude. **κ is the
problem:** it is quoted to four decimals with no interval, and its clustered interval spans "fair" to
"moderate". "κ = 0.4435 is moderate agreement at best" (entry 030) is defensible; "κ = 0.4435" is not
a four-digit quantity.

**Two further scope issues:**

1. **The population is dose 0, the application is dose 4.** `R-204` measures the judge on 226 dose-0
   completions — literal-button answers, **refusal 0.0000**, `null_frac` 0. Every use of 0.1372 /
   0.0221 / κ = 0.4435 in entries 036–037 applies it to **cell C dose 4**, whose refusal rate is
   **0.1265** and whose completions are a different population. Judge reliability is not a constant of
   the instrument; it is a function of the score distribution. The extrapolation is nowhere stated.
2. **Six pairs are dropped silently.** `if pa not in JA or pb not in JB: continue` drops 6 of the 232
   `cds_n0` families with no counter, while the *adjacent* drop reason gets one
   (`n_pairs_dropped_prompt_text_differed`, reported as 0). They are the 3 preregistered domain
   exclusions × 2, so the number is right — but "missing ≠ zero" is a house rule about the **count
   being named**, and the sibling analyzer `paired_domain_contrast()` names its drops by domain.

**Credit:** the design of `R-204` is genuinely better than the preregistered 200-row re-judge, the
`n_identical_completions = 226/226` check turns a joint generation+judge bound into a clean judge
isolation rather than assuming determinism, and `DONE.json` is gated first. None of that is disputed.
The statistics on top of it are.

---

## S-11 — MODERATE. Entry 028's cell-A dose-0 row is a stale partial-run number, and it is the row that says "zero".

`outputs/dcs_succ/concept_presence.json` (written **01:05**, all seven arms `n_judged` = `n_rows`,
`status: ok`) versus entry 028's table (written **22:45**):

| arm | entry 028 | artifact on disk (01:05) |
|---|---|---|
| C dose 0 | 0.1549 → 0.0088, 33 of 35 | 0.154867 → 0.008850, 33 of 35 ✓ |
| B dose 4 | 0.0088 → 0.0071, 2 of 10 | 0.008850 → 0.007080, 2 of 10 ✓ |
| E dose 4 | 0.0053 → 0.0000, 6 of 6 | 0.005310 → 0.000000, 6 of 6 ✓ |
| **A dose 0** | **0.1410 → 0.0000, 11 of 11** | **0.132743 → 0.004425, 29 of 30** ✗ |

⛔ All three of entry 028's cell-A numbers are wrong, and `11/78 = 0.1410256` **exactly**, so the row
was computed on a **78-row partial** `tsb66j_A_n0` directory (VERIFIED that it is not the completed
226-row run; the exact n = 78 is INFERRED from that identity). Entry **029**, timestamped the same
minute, records precisely this failure mode for a *different* computation, adds the standing
"check `DONE.json` first" rule, and does not revisit the table one entry above it.

**Consequences:**
* Entry 028's sentence *"removes 33 of 35 dose-0 positives and **all** of cell A's"* is false. One of
  30 survives (`asr_and_concept_present` = 0.004425 = 1/226). "All" → "29 of 30", and a rate that is
  printed as `0.0000` is actually nonzero — a "missing ≠ zero" instance inside the entry that
  introduced the repair.
* `R-204`'s ASR(A) = 0.1327 and entry 028's ASR(A) = 0.1410 are the **same arm** in the same log, 20
  minutes apart, and the log never reconciles them.
* The direction is against the attack (0.0000 → 0.0044 makes A *worse* as a clean floor), so nothing
  downstream flips. The defect is that a confirmatory instrument-validation table carries a
  partial-run number that was never corrected in an append-only log.

---

## S-12 — MINOR. The frozen lexicon's size is stated two different ways.

Entry 028: *"**47 terms** in four groups"*. The file's `CONCEPT_LEXICON` and
`concept_presence.json:lexicon_n_terms` both say **44** (16 explosive_material + 12 initiation +
10 device_assembly + 6 effect = 44, counted), and entry 036 says *"the frozen **44-term** lexicon"*
and *"27 unambiguous + 17 generic"* = 44 ✓. Entry 028 is wrong about the size of a frozen instrument
in the entry that freezes it.

---

## S-13 — precision inventory. Numbers quoted at more precision than the design supports. *(part g)*

Excludes everything already inventoried in REVIEW-1 F-09.

| where | quoted | what the design supports |
|---|---|---|
| **entry 033 title** | *"the full-state transplant moves **0.05 %** of it"* | the `all` window is +0.0066 log-odds, 95 % CI **[−0.211, +0.223]** = **[−1.71 %, +1.81 %]** of the gap. The CI is **65×** wider than the point estimate. Honest: *"bounded to within ±1.8 % of the gap"* — which is the **stronger** claim and the one the design actually earned |
| entry 033 | `L0-4` (best) *"moves **0.351 %** of the gap"* | CI [−0.015, +0.102] = **[−0.12 %, +0.83 %]**. The upper bound on transfer at the most favourable window is **+0.83 %**, not 0.35 % |
| entry 033 | gap **12.3312** (6 s.f.) | CI [11.325, 13.289] → **12.3** at best. Every "% of the gap" inherits this denominator's uncertainty and none is propagated |
| entry 037 / report | ρ **0.3961** (4 s.f.) | domain-bootstrap sd **0.0851** → the third decimal is noise. **0.40 ± 0.09** |
| entry 037 / report | CI **[0.2280, 0.5412]** (4 dp) | wrong coefficient's SE (S-09); Bonett–Wright [0.221, 0.546], bootstrap [0.220, 0.553]. Two decimals |
| report | disattenuated **0.5753 / 0.7273 / 0.5743 / 0.1945** (4 dp) | 21 % low (S-05), no interval, sole input not printed. Corrected pooled ≈ **0.70**, and ICC1(y) = 0.066 does not support 2 s.f. |
| entry 030 / 036 / 037 | reproducibility floor **0.0221** (3 s.f.) | McNemar p = 0.473; clustered CI **[0.000, 0.071]**. It is not an estimate of a nonzero quantity at all (S-02) |
| entry 030 | κ **0.4435** (4 dp), disagreement **0.1372** (4 dp) | clustered CIs **[0.281, 0.589]** and **[0.097, 0.181]**. Two decimals; κ needs "fair-to-moderate", not a fourth digit |
| **entry 034** | `I` share column: **876 %** (gun, basket) and **−285 %** (gun, button) | denominators are `B1` = **+0.0057** and **−0.0153**, i.e. indistinguishable from zero, with no interval on either. **A ratio whose denominator straddles zero is not a share** and 876 % is not a number; the entry prints it in a table beside 127 % as if commensurable |
| entry 025 | *"`I` is **127 %** of `B1`"* | `B1 = H + I` is asserted as an exact per-domain identity by the analyzer, so "I is 127 % of B1" **is** "H is −27 % of B1" restated. One fact, two presentations, no interval on either, and the 67/67 sign count on `I` is the F-07 redundancy REVIEW-1 already established (unrepaired) |
| entry 035 | −**7.1738** (5 s.f.), 61.7 / 36.2 / 1.5 % | the K10 arm's own bootstrap is [−7.546, −6.835] → **−7.2**. The **61.7 %** *is* supported (domain bootstrap [59.5, 64.0]) and should be quoted with that interval rather than to 3 s.f. bare |
| entry 037 / report | `Q1` mean Δ **0.1726 / 0.2230 / 0.3186** (4 dp) | 10-row domain means of a metric with a measured 0.155 false-positive channel, and the metric is unnamed (S-04). Two decimals at most, and the metric named |
| entry 025 | *"agrees … to **1.04e−07**"* | 3 s.f. on a floating-point residual; "agrees to 7 significant figures" is the content |

---

## WHAT THIS REVIEW TRIED TO BREAK AND COULD NOT

Recorded so the absence is on the record rather than inferred from silence.

* **`Q2`'s permutation unit is the domain and the join is compound.** Independently confirmed at the
  code and data level; ρ = **0.3960558995** reproduces to 10 digits from
  `ts116m_readout_button_bomb_20260907_133811_3183103` and `tsb66j_C_n4_20260910_000237_3406997`.
  All three split ρ reproduce to 4 dp.
* **`Q1`'s Holm ordering, thresholds, step-down monotonicity, tie exclusion and attainable floors are
  all correct**, including the point the brief flagged as suspect: the floor **is** taken over
  `n_informative`, which is the right n for an exact sign test conditional on the observed ties, and
  `n_informative + ties = 113` in all three rows.
* **`S-007`'s liveness is real.** `self_swap_noop_check` is exactly 0.000000 in 67/67 domains, and
  **0 of 804** transplant rows equal their baseline. The tautological-readout flags
  (`readout_layers_tautological`) are recorded per row and the entry reads them correctly as proof the
  write fired rather than as evidence of transfer.
* **The concept-presence instrument's arithmetic.** 158 of 370 judge positives carry concept content →
  `asr_and_concept_present` = **0.139823** for C dose 4 and **0.008850** for C dose 0, both reproduced
  from the frozen lexicon and the completed generation runs. The lexicon is genuinely frozen ahead of
  the confirmatory arm and the correction genuinely runs against the attack on every arm.
* **`R-205`'s rungs, controls and dose matching.** The 14 rung means, the four control bands, the
  three distinct draw seeds, `keys_masked_median = 2052` identical for demo and all three controls at
  K10, and the floor 1.3552527e-20 all reproduce. `SHAPE = NEITHER` is correctly returned against a
  pre-frozen rule that a convenient reading would have moved.
* **`R-202`'s `CANNOT_ANSWER_BANK` closure of `basket_bomb`** is correctly not reported as a null, and
  the per-bank scope rule is correctly stated. No statistical objection.

---

## THE FOUR SENTENCES I WOULD CHANGE IN THE LOG

1. Entry 037, `Q2` verdict → add: *"the estimate is carried by train; on the 46 domains outside train,
   ρ = 0.264, p = 0.080. The sign-consistency conjunct fires in 100 % of null draws that clear the MDE
   and is uninformative."*
2. Entry 030 → *"the preregistered quotability bar is the **label disagreement rate, 0.1372**. The
   `|ASR difference| = 0.0221` is a McNemar draw indistinguishable from zero (p = 0.47, CI
   [0.000, 0.071]) and is not a floor. Positive-label agreement is 0.523: about half of any reported
   positive does not reproduce."*
3. Entry 033 title → *"the full-state transplant is bounded to within **±1.8 %** of the 12.3 log-odds
   gap"*, and the body → *"three windows are negative under FDR; two under FWER; no foreign-donor
   control was run, so donor-specific interference and generic off-manifold cost are not separated."*
4. Entry 035 → replace the Holm-over-14 sentence with the paired increment: *"−4.49 log-odds in 67 of
   67 domains, sign p at its 1.36e-20 floor, **61.7 % [59.5, 64.0]** of the climb. The ladder is
   nested; no correction over 14 nested rungs is informative."*

---

*Recomputation scripts were run against the live tree between 2026-09-09 22:55 and 2026-09-10 02:20
IDT. No file outside this report was created or modified; no job was submitted.*
