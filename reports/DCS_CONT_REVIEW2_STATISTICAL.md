# DCS-CONT REVIEW-2 — STATISTICAL

Adversarial re-computation of the statistical claims in
`external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md`,
CONT-ENTRY 049–063. Everything below was **recomputed from the artifacts on disk**, not read out
of the log. Python `poc_stage2`, CPU only, no SLURM, **no TEST split was read** (the search corpus
`cont1_behavioral_button_bomb_…` contains 2800 train + 920 validation rows and zero test rows, which
I verified before doing anything else — CONT-ENTRY 062 is correct on that point).

Scripts used for this review live in the session scratchpad (`extract.py`, `f5a–f5f.py`, `asr.py`,
`slope.py`, `joint.py`, `c209.py`, `c209b.py`); they are review instruments, not repo artifacts, and
nothing in `configs/` or `scripts/` was edited.

---

## VERDICT

Every headline number in entries 049–063 that I attacked **reproduced to the digit** — `rho_loo =
+0.6241` with λ=1e2 in 67/67 nested folds, the refit within-domain null (`p50 = −0.0094`,
`max = +0.1696`, `p = 0.0050`), the VALIDATION transfer `+0.6784` with 22/23 domains positive and
`p = 0.00050`, the DR-070 primary `+0.002985` with bootstrap CI `[−0.0299, +0.0358]`, the
within/between slopes `+0.1400` / `+0.2670`, and the C-209 re-score `43 022` rows / `0.2984` →
`0.1169`. The statistical machinery behind F5 is **sound**: the within-domain permutation null
preserves exactly the structure it should and destroys exactly the one being tested; the pooled
670-slot Spearman is *not* inflated by within-domain dependence (it equals the mean of the 67
per-domain Spearmans to three decimals); within-domain centring biases the statistic slightly
*downward*, not upward; and the "22 of 23 domains" sign statistic is legitimate and strong
(permutation mean 11.5, sd 2.4). The missing family-wise correction on F5's TRAIN search, which I
supplied, does not change its verdict (family-wise `p95 = 0.2434` against an observed `+0.6241`).
**Two claims do not survive contact.** First, *"regularisation buys 0.078"*: the so-called
"unregularised covariance direction" is mathematically the **λ→∞ limit of the very ridge it is
compared to** (I confirm ridge at λ=1e12 returns `+0.5453` on TRAIN and `+0.6135` on VALIDATION —
the comparator's exact values), so the claim is inverted in name, and when I supply the CI it asked
for, the VALIDATION difference is `+0.0650`, 95 % CI **`[−0.0031, +0.1312]`** — it includes zero, and
F5 beats the comparator in only **13 of 23** validation domains. Second, the dissociation's
quantitative half: propagating the *slope's own* sampling error — which neither entry 049 nor 050
does — gives measured − within-prediction = `+0.0331`, 95 % CI `[−0.0022, +0.0683]`, **p = 0.069**,
and measured − between-prediction = `+0.0604`, `p = 0.011`. C-CONT-032's downgrade is therefore
**correct and if anything still too generous to entry 049**: even the between-domain version, once
the slope is treated as estimated rather than known, is a `p ≈ 0.01` result and not the "outside the
CI by 2.1× its half-width" that was written. **The dissociation is qualitative only, as claimed.**
Finally, the C-209 re-score quotes two rates over 43 022 rows with **no uncertainty of any kind**
while those rows carry only 2742 distinct prompts and a measured **design effect of 24.9**; I supply
the missing intervals below.

---

## FINDINGS BY SEVERITY

### S1 (claim fails as stated) — "regularisation buys 0.078 over the unregularised covariance direction"

**Claim.** CONT-ENTRY 059: *"**+0.6241 vs +0.5463** — regularisation buys 0.078 over the
unregularised covariance direction at the same site and layer."* CONT-ENTRY 061 repeats it on
VALIDATION (`+0.6784` vs `+0.6135`) and `configs/dcs_cont_dr072_f5_confirmation.json` promotes it to
a **prespecified confirmation criterion**: *"if `rho_test(F5) <= rho_test(comparator)` the
regularisation claim is NOT CONFIRMED"*.

**Test 1 — what the comparator actually is.** The comparator, as implemented in
`scripts/dcs_cont_f5_confirm.py` (`comp_pred = Xt @ (Xf.T @ yf)`), is the covariance direction
`w = X'y`. Dual-form ridge has `alpha = (K + λI)^-1 y → y/λ` as `λ → ∞`, so `pred → X_t X_f' y / λ`,
which is the covariance direction up to a positive scale — and Spearman is scale-invariant.

**Number I got.** Ridge at λ = 1e12, run through the identical LOO pipeline:

| population | covariance direction | ridge λ = 1e12 | ridge λ = 1e6 |
|---|---|---|---|
| TRAIN (LOO by domain) | **+0.5453** | **+0.5453** (identical to 1e-9) | +0.5454 |
| VALIDATION (λ fixed) | **+0.6135** | **+0.6135** | — |

⇒ The "unregularised" comparator is the **most-regularised** member of the same one-parameter
family. The sentence *"regularisation buys 0.078"* is **backwards**: what buys 0.078 is choosing a
*finite* λ instead of an infinite one — i.e. **less** shrinkage, not more. The honest statement is
*"tuning λ buys 0.078 over the shrink-to-marginal-direction limit."*

**Test 2 — the CI that does not exist.** Domain-level bootstrap (B = 4000, resampling domains, which
is the declared independence unit).

| population | ρ(F5) − ρ(comparator) | 95 % CI | P(diff ≤ 0) | domains where F5 wins |
|---|---|---|---|---|
| **VALIDATION** (λ fixed, honest out-of-sample) | **+0.0650** | **[−0.0031, +0.1312]** | 0.032 | **13 / 23** |
| TRAIN (LOO, λ nested-selected) | +0.0788 | [+0.0409, +0.1191] | 0.0000 | 47 / 67 |
| TRAIN, mean per-domain ρ difference | +0.0682 | [+0.0253, +0.1131] | 0.0015 | 47 / 67 |

**Survives / weakened / fails.** **FAILS as stated, on two counts.** (i) The name is wrong and
inverts the mechanism. (ii) On the only population where λ was not tuned, the 95 % CI **includes
zero**, and the per-domain sign test is 13/23 (binomial p = 0.34) — the gap is carried by the
pooled-rank statistic, not by a majority of domains. The TRAIN interval excludes zero but is
computed on LOO predictions fitted using every domain and with λ chosen on the same curve, so it is
optimistic by construction. Correct reading: *"the tuned ridge scores ~0.07 higher than the marginal
direction; on held-out domains that margin is +0.065 with 95 % CI [−0.003, +0.131] and is not
distinguishable from zero."*

**Consequence for DR-072 (frozen; reported, not fixed).** The prespecified comparator gate is a bare
sign comparison on a quantity whose sampling sd on 23 domains is about half its point estimate. If
the true margin is the validation point estimate the gate passes with high probability; if the true
margin is near zero it is a coin flip. Either outcome on TEST will be close to uninformative about
"regularisation", and a *failed* gate would not be evidence against F5. I am recording this, not
touching the frozen config.

---

### S1 (uncertainty missing, and it changes the reading) — C-209 re-score: two rates over 43 022 non-independent rows, no CI

**Claim.** CONT-ENTRY 063: *"`button` ASR **0.2984 → 0.1169** across 43 022 rows, a factor of
2.55"*, presented as *"what is now measured rather than suspected is the size"*.

**Test.** Re-derived the run selection from disk (793 judge runs with `results.jsonl`; 483 with
≥ 200 rows; **111** with `goal_status = substituted` on every row — the entry's counts reproduce
exactly), split by `target_surface`, then re-scored each run's completions through the frozen
44-term lexicon by resolving each judge run's `--gens` directory out of its `metadata.json`.

**Numbers I got.**

| | reported | mine | coverage |
|---|---|---|---|
| button rows | 43 022 | 43 022 (77 runs) | ✅ exact |
| button ASR@0.5 | 0.2984 | 0.2984 (12 838/43 022) | ✅ exact |
| button corrected | 0.1169 | 0.1158 | 74/77 runs, 41 012 rows resolvable to a gens dir |
| basket / carrot rows | 3 618 / 11 828 | 3 618 / 11 828 | ✅ exact |

**Dependence structure of those 43 022 rows.**

* distinct `prompt_id`: **2 742** (mean multiplicity 15.7, max **74**);
* distinct (prompt, arm, cell, dose) configurations: 26 202 — **39.1 % of rows are exact
  configuration duplicates**, and with `ds_common.py:1013` setting `do_sample=False` these are
  byte-identical generations re-counted;
* 116 domains, 77 runs.

**Design effect and the intervals that are missing.** Taking the **run** as the clustering unit
(n = 77; the domain is nested inside it and prompts recur across runs):

| quantity | pooled | naive binomial 95 % CI | **run-clustered 95 % CI** | design effect |
|---|---|---|---|---|
| raw ASR@0.5 | 0.2952 | [0.2908, 0.2996] | **[0.2733, 0.3166]** | **24.9** |
| `asr_and_concept_present` | 0.1158 | [0.1127, 0.1189] | **[0.1042, 0.1271]** | **14.8** |
| ratio raw/corrected | 2.55 | — | **[2.46, 2.66]** | — |

**Survives / weakened / fails.** The *arithmetic* survives exactly. The *presentation* is
**weakened**: two rates and a ratio are quoted as measurements with no uncertainty, on rows where the
naive binomial interval would be **5× too narrow**. Supplying them: the corrected button rate is
**0.1169, 95 % CI [0.104, 0.127]** (run-clustered), and the factor is **2.55, 95 % CI [2.46, 2.66]**.
Two further cautions the entry should carry: the run is a *convenience* unit (these are our own
77 runs, unequally weighted, spanning arms with deliberately different interventions — the interval
describes dispersion across our runs, not across prompts or models); and the 1.8 % / 0.7 % / 43.3 %
false-negative rates in the same entry are ratios over the same clustered rows and also carry no
interval. The qualitative conclusions (codeword-dependence of both error channels; `carrot`
withdrawn) are unaffected — 43.3 % vs 1.8 % is far outside any plausible clustering correction.

---

### S2 (claim survives; a missing correction supplied) — multiple comparisons on the F5 search

**Claim.** CONT-ENTRY 059 quotes F5's TRAIN significance as a **single-cell** within-domain
permutation null: `p50 = −0.0094`, `p95 = +0.0917`, `max = +0.1696`, `p = 0.0050`.

**What was actually selected.** Three nested choices: (i) the site × layer, whose argmax
`cw_demo_mean|L24` came from the 380-cell `within_domain_FULLDEPTH` map; (ii) the λ, off a 6-point
ladder; (iii) the family (raw state vs the contrasts). No max-statistic null is applied to (i)+(ii)
jointly anywhere.

**Test.** I built the family-wise null the entry does not have: **38 site×layer cells** (19 layers at
`cw_demo_mean`, 20 sites at L24) **× 6 λ = 228 cells**, 200 within-domain permutations, **refitting
the ridge under each permutation** (the C-CONT-002 discipline), tracking `max |rho|` over the whole
grid per permutation.

**Numbers I got.** Single-cell null (reproduced): `p50 = −0.0094`, `p95 = +0.0955`, `max = +0.1696`,
`p = 0.0050` — identical to the entry except the p95, which differs only by a percentile-index
convention. **Family-wise over 228 cells: `p50 = 0.1502`, `p95 = 0.2434`, `p99 = 0.3040`,
`max = 0.3608`; family-wise `p = 0.0050`** (the 200-permutation floor). Observed top cells:
`cw_demo_mean|L24|λ=1e2 = +0.6241`, `L26 = +0.6215`, `L22 = +0.6200`, `L20|λ=1e1 = +0.6193` — a broad
plateau, not a spike, so L24 is not a lucky draw off a noisy surface.

**Survives / weakened / fails.** **SURVIVES.** The correction was missing and is now supplied; it
raises the threshold by 2.5× and F5 clears it by a factor of 2.6. Record the family-wise number
alongside the single-cell one rather than the single-cell one alone.

**Other places I checked for a missing max-statistic correction:**

| where | family-wise null present? | verdict |
|---|---|---|
| `dcs_cont_layerpos_map.py` | ✅ global max over reportable families, 1520 cells, confounded comparator excluded | correct, and the `⛔ SCORE AGAINST THE PERMUTED LABELS` comment is the right discipline |
| `within_domain_FULLDEPTH_button_bomb.json` | ⚠️ **per-family only (380 cells each); no `global` key** | the argmax *within* `raw_C` (entry 056's `+0.5463` peak, p95 = 0.2908) is correctly priced; choosing *which family* to report is not. Immaterial here (0.5463 vs a 0.29 threshold), but `dcs_cont_layerpos_map.py` computes a global max and this one does not — an inconsistency between two sibling maps. |
| `logitlens_control_train_button_bomb.json` (F7, entry 059) | ❌ **no permutation null of any kind**, 48 cells | the four quoted logit-lens ρ (+0.4146 … +0.4982) are uncorrected argmaxes. Harmless *here* because the missing correction biases F7 **upward** and F7 still lost to the raw state — but the refutation should say "F7 loses even before correcting for its own search". |
| entry 056, *"`C − B` overtakes the raw state"* (0.5466 vs 0.5463) | ❌ no null on the **difference** | the entry itself calls it "neck-and-neck", which is the correct non-claim. No action. |
| entry 056, *"`mean4` peaks at `rel-6\|L30`"* | ❌ argmax **location** with no interval | a peak location quoted with no bootstrap; flagged as an uncertainty that does not exist anywhere in the phase. |
| CONT-ENTRY 061 VALIDATION `p = 0.00050` | n/a — single prespecified cell | **correct**: selection happened on TRAIN, so no multiplicity correction is owed on VALIDATION. |

---

### S2 (claim survives) — F5's pooled 670-slot Spearman is a legitimate statistic

**Claim (attacked).** Is Spearman over 670 within-domain-centred slots with only 67 domains inflated
by within-domain structure, given the 10 slots inside a domain are not independent?

**Test (a1) — does the permutation null preserve the right structure?** The null permutes `y` labels
**within** domain. After within-domain centring every domain mean is exactly 0 in both `x` and `y`;
the permutation leaves `x` untouched, leaves each domain's *multiset* of `y` deviations untouched,
and leaves the domain block structure untouched. It destroys precisely the within-domain
slot↔slot pairing, which is the null hypothesis. It is an **exact** conditional test, and it is the
only structure that should be destroyed. **The null is correct.** (On VALIDATION the predictor is
additionally held fixed, so permuting labels is the complete null; the config's note on this is
right.)

**Test (a2) — is the pooled statistic inflated relative to a per-domain one?**

| | pooled Spearman | mean per-domain Spearman | Fisher-z mean, back-transformed |
|---|---|---|---|
| TRAIN LOO | **+0.6241** | **+0.6244** | — |
| VALIDATION | **+0.6784** | **+0.6105** | +0.6807 |

**Supplied CIs (domain-level bootstrap, B = 4000):** VALIDATION pooled ρ **[+0.5703, +0.7601]**;
VALIDATION mean per-domain ρ [+0.4946, +0.7149]; TRAIN mean per-domain ρ **[+0.5680, +0.6758]**.

**Survives / weakened / fails.** **SURVIVES.** The pooled statistic tracks the per-domain average to
three decimals on TRAIN and is within 0.07 of it on VALIDATION — there is no inflation from pooling.
What *is* missing everywhere is an **interval**: the phase quotes ρ point estimates with permutation
p-values and never a CI. Supplied above. Note that the pooled ρ and the "22/23 domains" statistic are
two views of the same data, not independent corroboration.

---

### S3 (claim survives) — "positive in 22 of 23 domains" with n = 10 per domain

**Claim.** CONT-ENTRY 061: per-domain ρ *"positive in 22 of 23 domains"*, cited as evidence the
effect is not carried by a few domains.

**Test.** The exact within-domain permutation distribution of the **count of positive per-domain
ρ** (predictor fixed, 2000 permutations), rather than an assumed Binomial(23, ½).

**Numbers I got.** Null count: **mean 11.53, sd 2.40**; `P(count ≥ 22) ≤ 1/2001 = 0.00050`. The
null's mean of 11.5 confirms the Binomial(23, ½) reference is essentially right — ties at ρ = 0 with
n = 10 are rare enough not to bias the sign test. The 23 per-domain ρ are
`+0.78 +0.55 +0.38 +0.87 +0.82 +0.78 +0.85 +0.81 +0.45 +0.43 +0.87 +0.90 +0.36 +0.26 +0.33 +0.24
+0.68 +0.49 +0.79 +0.72 +0.92 +0.87 −0.12`. On TRAIN the same statistic is **66/67 positive**.

**Survives / weakened / fails.** **SURVIVES.** A single domain's ρ at n = 10 is noisy (null sd
≈ 0.33), but the *aggregate sign* over 23 independent domains is a legitimate and strong statistic,
and the exact null confirms it. The right caveat is only that it establishes *consistency of sign*,
not magnitude — and it is not independent of the pooled ρ.

---

### S3 (claim survives) — within-domain centring of `y` creates no upward artifact

**Claim (attacked).** Does centring `y` within domain before pooling manufacture the correlation?

**Test.** Three ways. (i) The refit permutation null on TRAIN is computed on exactly the centred
quantities: its centre is **`p50 = −0.0094`** — centring biases the statistic very slightly
**downward**, consistent with the `−1/(n−1)` correlation that centring induces among within-domain
residuals. On VALIDATION the fixed-predictor null centres at `+0.0058` (mean `+0.0044`, sd 0.0718).
(ii) Scoring the *same fixed predictor* against **raw, uncentred** `y` on VALIDATION gives
**+0.6139** vs **+0.6784** centred — the centred number is *higher*, i.e. removing the between-domain
(topic) component **strengthens** the association rather than manufacturing it. (iii) 75.5 % of
validation `y` variance is within-domain, so centring is not removing most of the signal either.

**Survives / weakened / fails.** **SURVIVES.** There is no centring artifact, and the direction of
the bias is the opposite of the one that would matter.

---

### S1 (claim survives; the log's own downgrade is correct and should go further) — the headline dissociation

**Claims.** CONT-ENTRY 049 §2: the same cut drops installation by **−0.2150 in 67/67 domains**
(basket: −0.2435, 67/67) while moving ASR by **+0.0030, CI [−0.030, +0.036]**. CONT-ENTRY 049 §3:
the prediction *"lies OUTSIDE the measured CI by 2.1× its half-width"*. CONT-ENTRY 050 /
C-CONT-032 downgrades §3 because the within-domain prediction of **−0.030** *"sits essentially on the
lower CI bound (−0.0299)"*.

**Test 1 — is the ASR CI computed with DOMAIN as the independence unit?** Recomputed the DR-070
primary end-to-end from the three judge runs plus `cp_per_arm.json`, aggregating to the domain first.

```
n domains 67, rows/domain 10        ASR base 0.1418 | ko 0.1418 | ctrl 0.1388
PRIMARY (ko − ctrl) = +0.002985      sd across domains 0.1414   se 0.01727
domain bootstrap 95% CI  [−0.0299, +0.0358]      (reported: [−0.029851, +0.035821]) ✅ exact
t-based 95% CI           [−0.0309, +0.0368]
per-domain diffs: 16 negative, 30 exactly zero, 21 positive
```

`scripts/dcs_cont_asr_primary.py:84` bootstraps the **67 per-domain paired differences**, and
`perm_p` is a sign-flip test on the same 67 values. The declaration
`configs/dcs_cont_dr070_intervened_asr.json` prespecifies `"independence_unit": "DOMAIN"` and the
MDE. ⇒ **The CI is correctly computed at the domain unit.** ✅ **SURVIVES.**

**Test 2 — is the study powered for the effect the installation drop predicts?** From the observed
`se = 0.01727`:

| target effect | source | power at α = 0.05 |
|---|---|---|
| −0.0301 | within-domain slope × −0.2150 | **0.414** |
| −0.0574 | between-domain slope × −0.2150 | 0.914 |
| −0.0689 | entry 049's slope × −0.2150 | 0.979 |

Observed MDE at 80 % power = **0.0484** (the frozen declaration's prespecified 0.0531 is slightly
conservative — the realised sd of the paired difference, 0.1414, came in under the declared 0.1553).
Domains needed for 80 % power at −0.0301: **173**, i.e. **2.6×** the 67 available. ⇒ **The study is
powered against the between-domain prediction and is NOT powered against the within-domain one
(41 % power).** CONT-ENTRY 050 §5's "roughly 4× the rows per domain" is also right and consistent:
the observed domain-level sd (0.1414) is almost exactly the pure-binomial value for 10 rows at a
14 % base rate (0.155), so essentially all of the domain-level variance is within-domain sampling
noise, and 4× rows would halve the se. CONT-ENTRY 051 §2's point that those rows cannot be bought —
`do_sample=False`, 10 rows/domain in the bank — is the binding constraint. ✅ entry 050's power
reading **SURVIVES**.

**Test 3 — adjudicating C-CONT-032 properly.** Both 049 §3 and 050 §2 compare a *point* prediction to
the measured CI, treating the slope as a known constant. It is an estimate on the same 67 domains.
I recomputed the slopes and then bootstrapped the **gap** (`measured − slope × shift`) with the
slope and the intervention effect resampled **together** over domains (B = 4000):

```
within-domain slope  +0.1400  95% CI [+0.0709, +0.2122]   perm p = 0.0010   (reported +0.1400, p=0.0006) ✅
between-domain slope +0.2670  95% CI [+0.0992, +0.4734]                      (reported +0.2670)          ✅
predicted ASR change, WITHIN  : −0.0301, CI [−0.0456, −0.0153]
predicted ASR change, BETWEEN : −0.0574, CI [−0.1018, −0.0213]
measured ASR change           : +0.0030, CI [−0.0299, +0.0358]

JOINT DOMAIN BOOTSTRAP of the gap
  measured − WITHIN  prediction = +0.0331   95% CI [−0.0022, +0.0683]   two-sided p = 0.069
  measured − BETWEEN prediction = +0.0604   95% CI [+0.0132, +0.1129]   two-sided p = 0.011
```

**Adjudication.**
1. **C-CONT-032 is right, and for a better reason than it gives.** The within-domain prediction is
   not merely "on the CI bound" — once its *own* error is propagated, the gap between what the
   observational relationship predicts and what the intervention produced is `+0.0331` with
   `p = 0.069`. **Not established.** (The "on the bound" framing is itself fragile: the prediction
   −0.0301 is 0.0002 outside the *bootstrap* lower bound −0.0299 and 0.0008 *inside* the t-based
   lower bound −0.0309. Nothing can rest on which side of a bound a number falls at that margin, and
   the entry is right not to try.)
2. **Entry 049 §3 was overstated by more than its own withdrawal admits.** Even the between-domain
   version, once the slope is an estimate, is `p = 0.011` — not the `~4σ` that "outside the CI by
   2.1× its half-width" implies. Separately, that phrase mis-describes its own arithmetic: the
   prediction −0.0689 is 2.19 half-widths from the *point estimate* and only 1.19 half-widths
   *outside the CI*. §3 is already withdrawn, so this is a note on the wording, not a live claim.
3. **The qualitative dissociation stands untouched.** −0.2150 in 67/67 domains (and −0.2435 in 67/67
   on basket) against +0.0030 with a CI that excludes anything larger than 3.6 points is a large
   unanimous change in one quantity and no detectable change in the other, and it depends on no
   slope. ✅ **CONT-ENTRY 049 §2 SURVIVES.** The dissociation is **qualitative only**, exactly as
   entry 050 §3 states.

---

### S3 (verification, no defect) — F5's TRAIN estimate and nested λ selection reproduce exactly

| quantity | reported | recomputed |
|---|---|---|
| λ ladder at `cw_demo_mean\|L24` (1e1…1e6) | +0.6114 / **+0.6241** / +0.5880 / +0.5527 / +0.5461 / +0.5454 | **identical, all six** |
| nested inner-LOO ρ | +0.6241 | **+0.6241** |
| λ selected per outer fold | 1e2 in 67/67 | **1e2 in 67/67** |
| refit within-domain null | p50 −0.0094, p95 +0.0917, max +0.1696, p 0.0050 | p50 −0.0094, p95 +0.0955, max **+0.1696**, **p 0.0050** |
| VALIDATION ρ / comparator | +0.6784 / +0.6135 | **+0.6784 / +0.6135** |
| VALIDATION per-domain | mean +0.6105, median +0.7212, 22/23 | **identical** |
| VALIDATION permutation | p50 +0.0058, p95 +0.1193, max +0.2356, p 0.00050 | p50 +0.0058, p95 +0.1208, max **+0.2356**, **p 0.00050** |

The only differences are the p95 quantile, which is an index convention on a 200- or 2000-element
sorted array, not a different null. **No defect.**

Two provenance notes while verifying: (i) the comparator `+0.5463` quoted in entry 059 comes from
`within_domain_FULLDEPTH_button_bomb.json`'s `raw_C_NULLMODEL`, which uses a slightly different
LOO direction estimator (norm-normalised, held-out `ybar`) than the ridge pipeline; the like-for-like
number from the ridge pipeline itself is `+0.5453`. The gap (0.078 vs 0.079) is immaterial, but the
two numbers put in the same sentence come from two estimators. (ii) `within_domain_train_*.json` is
built on the `cont3nb` corpus while `within_domain_FULLDEPTH_*.json` and everything F5 is built on
`cont1` — the FULLDEPTH file is the right one for the comparison and is the one entry 059 used.

---

### S3 (design note on a frozen config; reported, not fixed) — DR-072's point prediction is decorative

`configs/dcs_cont_dr072_f5_confirmation.json` states `point_prediction: "rho_test in [0.55, 0.70]"`
but the `decision_rule` for CONFIRMED is only `rho_test > 0 AND p < 0.05 AND ≥ 60 % of TEST domains
positive`. A `rho_test` of, say, +0.20 would satisfy all three and be declared **CONFIRMED** while
falling far outside the prespecified prediction interval. The interval carries no decision weight.
Supplied for the record: the VALIDATION domain-bootstrap CI of the pooled ρ is **[+0.570, +0.760]**,
which already straddles the upper edge of `[0.55, 0.70]`, so a TEST value above 0.70 would be
unremarkable sampling variation and should not be read as either confirmation or anomaly. The config
is FROZEN and I have not touched it.

---

## WHAT I DID NOT CHECK

* **Nothing on the TEST split.** The search corpus has zero test rows; job `878972`'s TEST
  extraction was not read and DR-072 was not executed.
* The **basket** ASR arms (`877545/6/7`) were still running; the basket `−0.2435` installation drop
  was taken from the log and not recomputed.
* The `−0.2150` installation effect and its CI `[−0.2348, −0.1961]` were taken from entry 049 as
  given; I recomputed only the ASR side of the dissociation and the slopes.
* **3 of 77** button judge runs could not be resolved to a generation directory, so my corrected
  C-209 figure covers 41 012 of 43 022 rows (0.1158 vs the reported 0.1169). The reported number is
  the more complete one; the run-level per-run corrected rates behind it were **not persisted to
  disk** by the entry-063 re-score, which is why the interval above had to be re-derived rather than
  read off. Persisting per-run counts would make that number auditable.
