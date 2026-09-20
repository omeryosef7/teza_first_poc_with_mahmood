# The button / basket dissociation: candidate explanations, each with the measurement that kills it

**Status: POST-HOC / EXPLORATORY.** Every number below is computed from artifacts already read and
committed. Plan 3.5 makes this ineligible for preregistration; it belongs in section B of the ledger,
never section A. Nothing here enters the claim table. No GPU job was launched. No file in
`reports/` or `configs/` was modified, and `src/boombness/score_behavior.py` was not touched.

**Author-run, 2026-09-20.** All commands run as
`bash -lc "source <miniconda>/etc/profile.d/conda.sh && conda activate poc_stage2 && cd <repo> && python <script>"`.
Analysis scripts: `/tmp/claude-47249/wk/an1.py` .. `an9.py` (scratch; regenerable from this document).

---

## 0. Validation of the analysis pipeline before any conclusion is drawn

Every per-domain quantity below is rebuilt from `domain_means` in the committed reports
(`KO_AXIS[d] - KO[d]`, averaged over domains) rather than read from the headline field. Two checks:

| cell | my domain-mean candidate | reported candidate | abs diff |
|---|---|---|---|
| button L20 TRAIN | +0.000404 | +0.000400 | 4.2e-06 |
| button L20 VALIDATION | +0.001323 | +0.001320 | 2.6e-06 |
| button L18 TRAIN | -0.000274 | -0.000270 | 4.5e-06 |
| basket L18 TRAIN | +0.002641 | +0.002640 | 1.0e-06 |
| basket L18 VALIDATION | +0.004005 | +0.004010 | 4.8e-06 |
| basket L20 TRAIN | +0.002943 | +0.002940 | 3.1e-06 |

(the residual is the reports' 5-dp rounding). And my rank routine, run on the p-scale with the
analyser's `>=` convention, **reproduces the committed rank in all eight cells** (section 10, column
1). The pipeline is therefore not the thing producing any difference reported here.

---

## 1. The facts in the brief, verified against the artifacts -- with one correction

| cell | artifact | candidate | n controls | rank | rank p |
|---|---|---|---|---|---|
| basket L18 TRAIN | `DCS_CSI_SUBSPACE_basket_train_n46.json` | +0.00264 | 46 | **1 of 47** | 0.0213 |
| basket L18 VALIDATION | `DCS_CSI_SUBSPACE_basket_validation_n46.json` | +0.00401 | 46 | **1 of 47** | 0.0213 |
| basket L20 TRAIN | `DCS_CSI_SUBSPACE_basket_train_L20.json` | +0.00294 | 10 | **1 of 11** | 0.0909 (floor) |
| button L20 TRAIN | `DCS_CSI_SUBSPACE_button_train_rank1.json` | +0.00040 | 10 | **4 of 11** | 0.3636 |
| button L20 VALIDATION | `DCS_CSI_SUBSPACE_button_validation.json` | +0.00132 | 10 | **4 of 11** | 0.3636 |
| button L18 TRAIN | `DCS_CSI_SUBSPACE_button_train_L18.json` | -0.00027 | 10 | **8 of 11** | 0.7273 |

**CORRECTION to the task brief.** The brief states basket VALIDATION as *"rank 1 of 31, p = 0.0323"*.
That is the **superseded 30-control** read (`DCS_CSI_SUBSPACE_basket_validation_n30.json`). S-103's
ledger entry records that D12 now reports **both** splits at 46 controls, and the committed
`..._validation_n46.json` gives **rank 1 of 47, p = 0.0213**, candidate +0.00401. I use the n46 file
throughout. This makes the held-out family **exactly matched** to TRAIN's, which matters for section 4.

---

## 2. What S-109's three killers forbid any new explanation

S-108 proposed that the dissociation is explained by basket converting captured displacement into
installation more efficiently; S-109 withdrew the interpretation (the sixteen numbers all stand).
Three independent killers, and what each rules out for anything proposed here:

1. **KILLER 1 -- the linear dose model has no pointwise predictive validity at the axis's own dose.**
   All sixteen `KO_ATk` arms sit at captured fraction 1/28 = 0.03571, indistinguishable from the
   axis's 0.0348, and at that fixed dose observed/predicted recovery spans **-24 % to +1304 %**, set
   purely by *which position* is touched. D10's R^2 = 0.997 is an average over **random** subsets and
   cannot calibrate a pointwise prediction (the repo's own S-066 caveat).
   *Forbidden here:* any explanation that divides a recovery by a captured-energy/amplitude fraction,
   or that treats recovery as linear-in-dose for a single named direction. **None of C1-C8 does.**
2. **KILLER 2 -- a statistic applied to the candidate must be applied to every control.** S-108's
   normalisation, applied family-wide, moved basket TRAIN from rank 1 to rank 8 of 47 and p 0.021 to
   0.170; it would have destroyed the sprint's only positive.
   *Forbidden here:* reporting any re-weighting of the candidate without recomputing every control
   under it and reporting the resulting rank. **C7 is the only re-weighting I compute, and section 10
   gives the full family-wide rank under five weighting schemes, including the two that hurt basket.**
3. **KILLER 3 -- "basket captures less than button" is measure-dependent.** It holds under
   mean-of-ratios (0.0324 vs 0.0348) and **inverts** under ratio-of-means (0.0499 vs 0.0445).
   *Forbidden here:* any explanation resting on a flat cross-codeword capture comparison.
   **C5 reports both measures side by side and rests on neither.**

Additionally, from S-109's surviving findings: **norm-matching is exact within every family**, which I
re-verified myself -- the spread of `written_norm.mean` across a whole family is 7.5e-05 to 7.8e-04 on
a mean of 0.058-0.070, i.e. **0.1-1.3 %**. *The rank test is already fully dose-controlled inside a
codeword and needs no further normalisation.*

---

## 3. The master table every candidate is tested against

Computed by me from the six committed reports (`an1.py`, `an7.py`):

| cell | BASE | KO | manip `KO-BASE` | pos. control `KO_FULL-KO` | recov. frac | candidate | cand/PC | ctrl mean | ctrl sd | **z** | cand / best ctrl |
|---|---|---|---|---|---|---|---|---|---|---|---|
| button L20 TRAIN | 0.67798 | 0.47240 | -0.20558 | +0.06955 | 0.338 | +0.00040 | 0.58 % | -0.000006 | 0.000902 | **+0.456** | 0.25x |
| button L20 VALIDATION | 0.67327 | 0.38232 | -0.29095 | +0.09508 | 0.327 | +0.00132 | 1.39 % | +0.000663 | 0.001353 | **+0.489** | 0.50x |
| button L18 TRAIN | 0.67704 | 0.46973 | -0.20730 | +0.10842 | 0.523 | -0.00027 | -0.25 % | +0.000068 | 0.000910 | **-0.376** | -0.18x |
| basket L18 TRAIN | 0.46852 | 0.23901 | -0.22951 | +0.12041 | 0.525 | +0.00264 | 2.19 % | +0.000502 | 0.000835 | **+2.561** | 1.11x |
| basket L18 VALIDATION | 0.40046 | 0.16952 | -0.23094 | +0.10370 | 0.449 | +0.00401 | 3.87 % | +0.000348 | 0.000713 | **+5.128** | 1.44x |
| basket L20 TRAIN | 0.47548 | 0.24010 | -0.23538 | +0.09391 | 0.399 | +0.00294 | 3.13 % | +0.000106 | 0.000566 | **+5.011** | 2.28x |
| **basket L18 TRAIN, restricted to the same 10 control arms** | - | - | - | - | - | +0.00264 | 2.19 % | +0.000692 | 0.001006 | **+1.939** | 1.23x |
| **basket L18 VALIDATION, restricted to the same 10 control arms** | - | - | - | - | - | +0.00401 | 3.87 % | +0.000467 | 0.000991 | **+3.567** | 1.44x |

`z = (candidate - mean(controls)) / sd(controls)` is the **family-size-free** statistic: it does not
improve merely by running more controls. The last two rows restrict basket's 46-control family to the
**identical ten arm names** button was run with (`KO_RAND0..5`, `KO_SHUF0..3`) -- the same 6 random /
4 shuffled composition -- so the comparison is matched on family size *and* on family composition.

---

## 4. C3 -- "the control families are not comparable; rank 4 of 11 and rank 1 of 47 are not the same test"

**Tested first and hardest, as instructed.** This is the candidate that would dissolve the whole
dissociation, so it gets four independent measurements.

### 4.1 What was basket's rank with only ten controls? -- ANSWERED, and it is 1

* **basket TRAIN, restricted to the same ten arm names: rank 1 of 11**, candidate +0.00264 against a
  best control of +0.00215 (`KO_SHUF2`). z = **+1.939**.
* **basket VALIDATION, same ten: rank 1 of 11**, +0.00401 against +0.00278 (`KO_SHUF3`). z = **+3.567**.
* Independently, the committed 10-control basket reads agree:
  `DCS_CSI_SUBSPACE_basket_validation.json` is **rank 1 of 11**, and
  `DCS_CSI_SUBSPACE_basket_train_L20.json` is **rank 1 of 11** at button's own layer.
  S-071 recorded basket TRAIN at exactly ten controls as **rank 1 of 11** on a different key
  intersection.

> **At matched family size (10), matched composition (6 random + 4 shuffled) and matched domains,
> basket is rank 1 and button is rank 4 -- on both splits, and rank 1 vs rank 8 at the shared layer
> L18.** The dissociation is present *before* basket ever gained its extra 36 controls.

### 4.2 Can button's rank at 46 controls be bounded from its 10-control distribution? -- YES

Two methods. (a) Beta-binomial predictive with a Jeffreys prior on the exceedance probability,
conditioned on the observed exceedances; (b) a normal fit to the observed control family.

| button cell | exceedances | posterior mean p | **E[rank at 46 controls]** | **P(rank 1 of 47)** |
|---|---|---|---|---|
| L20 TRAIN | 3 of 10 | 0.318 | **15.6** (normal fit 16.0) | **3.2e-03** (normal fit 1.3e-08) |
| L20 VALIDATION | 3 of 10 | 0.318 | **15.6** (normal fit 15.4) | **3.2e-03** (normal fit 3.0e-08) |
| L18 TRAIN | 7 of 10 | 0.682 | **32.4** (normal fit 30.7) | **6.5e-07** |

**The same projection is calibrated on basket's own data**, which is what makes it usable rather than
a guess: applied to basket's ten-control families it predicts E[rank at 46] = **2.22** (TRAIN) and
**1.01** (VALIDATION); the *actual* ranks once the 36 extra controls were run are **1** and **1**.

> **Button's candidate is not one long tail away from rank 1. On its own control distribution the
> expected rank at 46 controls is ~16 (own layer, both splits) and ~31 at L18, and the probability of
> rank 1 of 47 is at most 3.2e-03.** Extending button's family cannot manufacture a pass.

### 4.3 The nonparametric version, which needs no distributional assumption

Exceedance rate = fraction of the control family recovering at least as much as the candidate.
Clopper-Pearson 95 % CIs:

| cell | exceed | p_exceed | CI95 |
|---|---|---|---|
| button L20 TRAIN | 3/10 | 0.300 | [0.067, 0.652] |
| button L20 VALIDATION | 3/10 | 0.300 | [0.067, 0.652] |
| button L18 TRAIN | 7/10 | 0.700 | [0.348, 0.933] |
| button cw_query L20 TRAIN (S-097, different site) | 4/11 | 0.364 | [0.109, 0.692] |
| basket L18 TRAIN (46) | 0/46 | 0.000 | [0.000, 0.077] |
| basket L18 VALIDATION (46) | 0/46 | 0.000 | [0.000, 0.077] |
| basket, same 10 arms, either split | 0/10 | 0.000 | [0.000, 0.308] |

Fisher exact, one-sided, button vs basket (side by side; **never pooled** -- rule 3.3). Caveat: this
treats the controls of a family as independent draws, which they are only under exchangeability:

| comparison | p |
|---|---|
| own layers, full families (3/10 vs 0/46), TRAIN and VALIDATION alike | **0.0043** |
| own layers, **matched 10-control families** (3/10 vs 0/10) | **0.1053** |
| **both at L18**, matched 10 (7/10 vs 0/10) | **0.0015** |
| both at L18, 10 vs 46 | **3e-05** |
| both at L20, matched 10 (3/10 vs 0/10) | **0.1053** |

### 4.4 A domain-clustered CI on the difference of standardised effects

Paired domain bootstrap, 20 000 draws, seed 20260920, resampling the **same** 67 (or 23) domain
indices for both codewords -- legitimate because the domain sets are bit-identical (section 6) and
each codeword keeps its own statistic; only the difference is reported. The control *set* is held
fixed, so this CI does not include control-draw variability.

| contrast | button z | basket z | **delta z (basket - button)** | 95 % CI | frac(delta <= 0) |
|---|---|---|---|---|---|
| TRAIN, own layers, full families | 0.442 | 2.465 | **+2.023** | [-0.226, +4.288] | 0.0404 |
| TRAIN, own layers, **matched 10** | 0.443 | 1.894 | **+1.452** | [-0.440, +3.345] | 0.0655 |
| **TRAIN, both at L18**, 10 vs 46 | -0.373 | 2.459 | **+2.832** | [**+0.606**, +5.057] | 0.0058 |
| VALIDATION, own layers, full | 0.444 | 4.653 | **+4.209** | [**+0.630**, +7.078] | 0.0109 |
| VALIDATION, own layers, **matched 10** | 0.441 | 3.311 | **+2.871** | [**+0.267**, +4.977] | 0.0167 |

### VERDICT on C3

**C3 is REFUTED as the explanation, but it is not nothing.** Basket beats button at matched family
size on both splits and at both layers, so the pass is not bought with extra controls; and button's
own distribution projects to rank ~16 / ~31, not 1. *However*, the single cell the sprint's headline
is usually stated from -- **TRAIN, each codeword at its own layer** -- is the **weakest** evidence for
the dissociation: its delta-z CI includes zero (4.4) and its matched-family Fisher p is 0.105 (4.3).
The dissociation is carried by the **held-out split** and by the **shared-layer (L18)** comparison,
not by the TRAIN headline. That should be said out loud whenever the 1-of-47 vs 4-of-11 contrast is
quoted.

---

## 5. C2 -- headroom / base rates: "button's axis has less room to show an effect"

**Precise statement:** the candidate's measurable recovery is bounded by the whole-state positive
control `KO_FULL - KO`; if button's is smaller, an axis of equal quality shows a smaller effect.

**What it predicts that no other candidate does:** the candidate effect should order with the positive
control across all four (codeword x layer) cells.

**The killer measurement:** the four positive controls are already committed and they are *crossed*
with the codeword, so the prediction is directly falsifiable.

| ordered by headroom | positive control `KO_FULL - KO` | candidate | cand / PC |
|---|---|---|---|
| button L20 | +0.06955 | +0.00040 | 0.58 % |
| basket L20 | +0.09391 | **+0.00294** | 3.13 % |
| **button L18** | **+0.10842** | **-0.00027** | **-0.25 %** |
| basket L18 | +0.12041 | +0.00264 | 2.19 % |

> **KILLED. Button at L18 has 56 % more headroom than button at L20 and 15 % more than basket at L20,
> and its candidate is the only NEGATIVE one in the set.** Headroom does not order the candidates; the
> codeword does: {basket +0.00294, +0.00264} strictly above {button +0.00040, -0.00027} at every
> headroom level. Within each codeword the relation even runs *backwards* (basket: more headroom at
> L18, smaller cand/PC; button: more headroom at L18, negative candidate).

S-104 made the qualitative version of this point; the table above is its quantitative closure across
the now-complete 2x2.

---

## 6. C4 -- population / domain composition

**Precise statement:** the two codeword banks score different prompts or different domains, so the
codeword contrast is really a population contrast.

**Killer measurement:** compare the domain sets, the prompt family keys, and the per-row structure.

* `in_sample.KO_AXIS.fit_domains_sha16` is **`4614853e5636eb5f` in all six reports** -- the same fit
  population for both codewords and both splits.
* The `domain_means` key sets are **identical**: button L20 TRAIN == button L18 TRAIN ==
  basket L18 TRAIN == basket L20 TRAIN (67 domains), and button VALIDATION == basket VALIDATION (23).
* At the **prompt** level, reading the two `KO_AXIS` `results.jsonl` files directly: button has 670
  family keys, basket 670, **intersection 670, button-only 0, basket-only 0**. Same slots, same
  `n_examples`, same consistency/position/style cells, and `n_target_occurrences` = 5 in both.
* The codeword is **one token in both cases** (`' button'`, `' basket'`;
  `reports/DCS_CSI_CODEWORD_TOKEN_AUDIT.json`, and `surface_span_n_tokens` = 1 on every row). No
  tokenisation confound.

> **KILLED, comprehensively.** The two arms differ in exactly one thing at the input: which single
> token occupies the codeword slot. Everything else -- domains, prompts, slots, counts -- is identical.

What is *not* identical is the **model's response**: basket's BASE installation is 0.469 vs button's
0.678, and basket's KO sits at 0.239 vs button's 0.472. That is a genuine difference, and it is the
substance of C7 below -- but it is a property of the codeword, not of the population sampled.

---

## 7. C1 -- "basket's probe is simply a better probe"

**Precise statement:** the rank-1 direction is a better predictor of installation for basket, so it is
a better handle on whatever the knockout removes.

**Killer measurement:** the two sidecars record leave-one-out Spearman rho by layer and by rank on the
fit population. If the rank-1 fits are equally good, C1 dies.

| | basket L18 | basket L20 | button L20 | button L18 |
|---|---|---|---|---|
| `train_loo_rho_at_selected_layer` | **0.6525** | 0.6512 | 0.5935 | 0.5931 |
| **`train_loo_rho_by_rank.r1`** (the direction actually used) | **0.5629** | 0.5536 | **0.5021** | 0.5042 |
| best rank / its rho | r3 / 0.6407 | r3 / 0.6396 | r5 / 0.5767 | r5 / 0.5880 |
| r1 as a share of the best rank's rho | 87.9 % | 86.6 % | 87.1 % | 85.7 % |
| `max_abs_cosine(cand_rank1, cand_pls*)` | **0.6947** | 0.5970 | **0.5664** | 0.6594 |
| shuffled-control LOO rho range | -0.084 .. +0.079 | -0.080 .. +0.096 | -0.009 .. +0.055 | -0.091 .. +0.088 |
| `n_fit_rows` / `n_fit_domains` / `lambda` / `seed` | 670 / 67 / 100.0 / 20260915 | same | same | same |
| held-out score recorded in the sidecar | **none** | none | none | none |

**Result: PARTLY SUPPORTED, and it cannot be dismissed.** Basket's rank-1 probe is genuinely the
better probe -- **rho 0.5629 vs 0.5021, +12 % relative** -- and at its own layer it is more aligned
with its own multi-rank PLS solution (|cos| 0.695 vs 0.566). But the *relative* degradation from the
best rank down to rank 1 is the same for both (87.9 % vs 87.1 %), and both probes sit far above their
shuffled controls, so this is a difference of degree, not of kind.

**What would kill it, and what cannot be measured from committed artifacts:** neither sidecar records
a **held-out** rho. `CANNOT MEASURE` from the existing files. The decisive version -- does a 12 %
better probe buy a 4-6x larger standardised rescue effect? -- is a *quantitative* question the
sidecars cannot answer, and the direct experiment is E1 in section 12.

**One bound that is available:** a 12 % relative rho gap has to explain a **z gap of +0.456 -> +1.939
(matched families) or +2.561 (full)**, i.e. a 4.3-5.6x change in the standardised effect. No
calibration in this sprint maps rho onto rescue z, so **C1 cannot be scaled** -- only ranked as
plausible and unquantified.

---

## 8. C5 -- "the two rank-1 directions are different objects"

**Killer measurements**, computed by me: (a) cosine between the rank-1 axes, loaded from the `.pt`
artifacts on CPU; (b) captured amplitude and displacement, read from the `KO_AXIS` rows directly.

### (a) The axes themselves (`an6.py`, `cand_rank1`, unit-normalised, 4096-d)

| pair | cosine |
|---|---|
| **button L20 vs button L18** (same codeword, across layers) | **+0.7470** |
| **basket L18 vs basket L20** (same codeword, across layers) | **+0.7355** |
| **basket L18 vs button L18** (same layer, across codewords) | **+0.5569** |
| **basket L20 vs button L20** (same layer, across codewords) | **+0.4961** |
| basket L18 vs button L20 | +0.4119 |
| basket L20 vs button L18 | +0.4062 |

> Two codewords' axes overlap at |cos| ~ 0.50-0.56 -- neither the same direction nor orthogonal. And
> **the two codewords' axes are equally stable across layers (0.7355 vs 0.7470)**, so *"basket's axis
> is better conditioned"* is **not supported** by layer stability.

### (b) Dose bookkeeping, read from the rows myself (`an5.py`, `an4.py`)

| cell | rows | `delta_norm` mean | `proj_norm` mean | captured, MoR | captured, RoM | written norm |
|---|---|---|---|---|---|---|
| button L20 TRAIN | 670 | 1.52068 | 0.06771 | 0.03479 | 0.04453 | 0.06771 |
| button L20 VALIDATION | 230 | 1.53950 | 0.06933 | 0.03487 | 0.04503 | 0.06933 |
| button L18 TRAIN | 670 | 1.30090 | 0.06798 | 0.03872 | 0.05225 | 0.06798 |
| basket L18 TRAIN | 670 | 1.17153 | 0.05849 | 0.03237 | 0.04993 | 0.05849 |
| basket L18 VALIDATION | 230 | 1.17887 | 0.05882 | 0.03195 | 0.04989 | 0.05882 |
| basket L20 TRAIN | 670 | 1.36796 | 0.06027 | 0.02820 | 0.04406 | 0.06027 |

These reproduce S-108's and S-125's figures exactly, from the raw rows, by a path that reads nothing
but `rescue_liveness`. Reported as **amplitude**, never energy (S-109's correction: the field name
`captured_energy_frac_mean` is `mean(proj_norm / delta_norm)`; the energy fraction is its square,
~0.1 %). **Per KILLER 3 the cross-codeword capture comparison is measure-dependent and is not rested
on**: basket captures less under mean-of-ratios and *more* under ratio-of-means.

What *is* measure-robust, and is the useful number, is the candidate's excess over its own family's
random controls -- and it does **not** favour basket:

| cell | cand capture | random-control mean | **cand / random** |
|---|---|---|---|
| button L20 TRAIN | 0.03479 | 0.01289 | **2.70x** |
| button L20 VALIDATION | 0.03487 | 0.01285 | **2.71x** |
| button L18 TRAIN | 0.03871 | 0.01263 | **3.07x** |
| basket L18 TRAIN | 0.03237 | 0.01237 | **2.62x** |
| basket L18 VALIDATION | 0.03195 | 0.01240 | **2.58x** |
| basket L20 TRAIN | 0.02820 | 0.01280 | **2.20x** |

> **KILLED as a dose story.** Relative to its own family's random baseline, button's axis captures
> *more* of the displacement than basket's (2.70-3.07x vs 2.20-2.62x) and recovers less. The axes are
> genuinely different objects (cos ~ 0.50), but not because one of them spans more of the damage.

`written_norm.mean` spreads by only 0.1-1.3 % across an entire family, so norm-matching is exact and
no dose normalisation is admissible (S-109's surviving finding, re-verified here).

---

## 9. C6 (new) -- "the axis is on the causal carrier for basket and not for button"

**Precise statement:** basket's axis is aligned with whatever the whole-state rescue restores; button's
is not. **Prediction that distinguishes it:** the candidate's *per-domain profile* should track the
positive control's per-domain profile more closely than the controls do -- for basket only.

**The killer measurement, and it is a second, independent rank test on existing artifacts:** take
`corr_d(KO_AXIS - KO, KO_FULL - KO)` across domains and rank it inside the same control family.

| cell | Pearson r | Spearman | control mean r | control max r | **rank of r in the family** |
|---|---|---|---|---|---|
| button L20 TRAIN | 0.2281 | 0.2308 | -0.1200 | 0.0398 | **1 of 11** |
| button L20 VALIDATION | 0.3446 | 0.3755 | -0.0028 | 0.3271 | **1 of 11** |
| button L18 TRAIN | 0.2832 | 0.1754 | -0.0732 | 0.0534 | **1 of 11** |
| basket L18 TRAIN | 0.3057 | 0.3756 | 0.1022 | 0.5497 | **8 of 47** |
| basket L18 VALIDATION | 0.3387 | 0.3142 | 0.0368 | 0.4585 | **4 of 47** |
| basket L20 TRAIN | 0.4254 | 0.4518 | 0.0918 | 0.3029 | **1 of 11** |

> **C6 is KILLED, and it is killed in the direction nobody expected: on this statistic the
> dissociation REVERSES.** Button's axis is rank **1 of 11** for profile-alignment with the
> whole-state rescue at *both* layers and *both* splits, while basket's is rank 8 of 47 / 4 of 47.
> Whatever separates the codewords, it is **not** that only basket's axis points at the causal carrier.

**Caveats, stated because this is the most surprising number in the document.** (i) It is a different
statistic from the preregistered one and is POST-HOC. (ii) Button's families have only ten controls,
so "rank 1 of 11" here is floor-limited at 0.0909 exactly as elsewhere. (iii) Correlations between two
near-zero difference profiles can be driven by shared per-domain noise in the common `KO` term, which
is subtracted from both sides -- this inflates *all* the correlations, candidate and control alike, so
the *rank* is the defensible part and the raw r is not. (iv) button's control correlations are centred
**negative** (-0.12, -0.07) and basket's **positive** (+0.10), which is itself unexplained and is a
reason to treat this section as a lead, not a result.

---

## 10. C7 (new) -- "it is an artifact of the bounded probability endpoint"

**Precise statement:** installation is `sigmoid(logp_concept - logp_codeword)`. basket's KO sits at
p = 0.239 and button's at p = 0.472, and the sigmoid gain `p(1-p)` is 0.160 vs 0.205. The domain-mean
of a probability difference is therefore a gain-weighted average of logit differences, and the weights
differ systematically between codewords. If the dissociation lives in the weighting, it should vanish
on the logit scale.

**Killer measurement, applied family-wide per KILLER 2** -- every control re-weighted exactly as the
candidate is, and the resulting rank reported, including where it hurts basket. Delta-method rescaling
`d_logit = d_p / (p_KO (1-p_KO))`, with trimming because the weight blows up near the boundary:

| cell | p-scale (published) | logit, untrimmed | logit, trim p in (0.02,0.98) | trim (0.05,0.95) | trim (0.10,0.90) |
|---|---|---|---|---|---|
| button L20 TRAIN | 4 of 11 | 4 of 11 | 4 of 11 | 4 of 11 | 4 of 11 |
| button L20 VALIDATION | 4 of 11 | 4 of 11 | 4 of 11 | 4 of 11 | 4 of 11 |
| button L18 TRAIN | 8 of 11 | *3 of 11* | 6 of 11 | 8 of 11 | 8 of 11 |
| basket L18 TRAIN | **1 of 47** | 1 of 47 | **3 of 47** | **3 of 47** | 1 of 47 |
| basket L18 VALIDATION | **1 of 47** | 1 of 47 | 1 of 47 | 1 of 47 | 1 of 47 |
| basket L20 TRAIN | 1 of 11 | 1 of 11 | 1 of 11 | 1 of 11 | 1 of 11 |
| basket L18 TRAIN, matched 10 | 1 of 11 | 1 of 11 | 2 of 11 | 2 of 11 | 1 of 11 |
| basket L18 VALIDATION, matched 10 | 1 of 11 | 1 of 11 | 1 of 11 | 1 of 11 | 1 of 11 |

Mean candidate effect on the logit scale (trimmed at 0.05/0.95), with the positive control likewise:

| cell | domains kept | cand (logit) | pos. control (logit) | cand / PC |
|---|---|---|---|---|
| button L20 TRAIN | 63/67 | +0.00183 | +0.3358 | 0.55 % |
| button L20 VALIDATION | 23/23 | +0.00619 | +0.4516 | 1.37 % |
| button L18 TRAIN | 63/67 | -0.00210 | +0.5311 | -0.40 % |
| basket L18 TRAIN | 60/67 | +0.01357 | +0.7730 | 1.75 % |
| basket L18 VALIDATION | 18/23 | +0.02231 | +0.6704 | 3.33 % |
| basket L20 TRAIN | 60/67 | +0.01650 | +0.5843 | 2.82 % |

> **NOT KILLED, and NOT sufficient.** Re-expressing on the logit scale shrinks the cand/PC gap from
> 3.8x (2.19 % vs 0.58 %) to 3.2x -- so sigmoid gain explains **some** of the size of the gap -- but
> the dissociation survives all five weighting schemes: button never leaves rank 4 at its own layer,
> basket never leaves rank 1-3.

**The cost of this test, reported because KILLER 2 requires it:** basket's **TRAIN** pass is **not
robust** to trimming on the logit scale -- it moves from **rank 1 of 47 (p = 0.0213) to rank 3 of 47
(p = 0.0638)**, i.e. from PASSES to does-not-pass at alpha = 0.05, under two of the five schemes.
Basket **VALIDATION** and **basket at L20** are rank 1 under **all five**. button L18's flip to 3 of 11
under the untrimmed logit is the `1/(p(1-p))` blow-up on near-boundary domains and should be read as
instability of the transform, not as a result.
**Statement licensed: the basket TRAIN headline depends on how per-domain effects are weighted; the
held-out result does not.** Neither weighting is privileged -- the p-scale is the preregistered one and
stands; this is a robustness note, not a re-analysis.

---

## 11. C8 (new) -- "basket's rank test is simply better powered: same noise, bigger signal"

**Precise statement:** the control family's spread is a property of the *intervention scale*
(norm-matched writes of ~0.06 into 28 positions), not of the codeword; but the recoverable effect
(`KO_FULL - KO`) is ~1.7x larger for basket. So basket's test has a better signal-to-noise environment
for **any** direction, informative or not.

**Killer measurement:** decompose `z = A x B`, where `A = (cand - ctrl_mean)/PC` is the candidate's
excess share of the recoverable effect and `B = PC / ctrl_sd` is the family's signal-to-noise. If the
dissociation is power, B should carry it and A should be equal.

| cell | control sd | pos. control | **A** (excess share of PC) | **B** (PC / sd) | z = A x B |
|---|---|---|---|---|---|
| button L20 TRAIN | 0.000902 | 0.06955 | **+0.00591** | 77.1 | +0.456 |
| button L20 VALIDATION | 0.001353 | 0.09508 | **+0.00697** | 70.3 | +0.489 |
| button L18 TRAIN | 0.000910 | 0.10842 | **-0.00316** | 119.2 | -0.376 |
| basket L18 TRAIN | 0.000835 | 0.12041 | **+0.01776** | 144.2 | +2.561 |
| basket L18 VALIDATION | 0.000713 | 0.10370 | **+0.03528** | 145.3 | +5.128 |
| basket L20 TRAIN | 0.000566 | 0.09391 | **+0.03022** | 165.8 | +5.011 |
| basket L18 TRAIN, matched 10 | 0.001006 | 0.12041 | **+0.01619** | 119.8 | +1.939 |
| basket L18 VALIDATION, matched 10 | 0.000992 | 0.10370 | **+0.03412** | 104.5 | +3.567 |

> **PARTLY TRUE, and it is the largest quantified contributor after the codeword itself.** The control
> **sd is essentially codeword-independent** (0.00057-0.00135 everywhere), confirming that the noise
> floor is set by the intervention scale and not by the codeword. Basket's B is 1.2-2.4x button's.
> **But A -- the part that is about the direction -- is 2.7 to 5.1x larger for basket**, and at the
> matched-family comparison (basket +0.01619 vs button +0.00591) it is **2.7x**.

**The cleanest single refutation of the power story in this document:** button at L18 (B = 119.2) and
basket-at-10-controls (B = 119.8) have the same family SNR to **within half a percent**, and their A
values have **opposite signs** (-0.00316 vs +0.01619).

For completeness, the family composition at matched n = 10 is matched too (6 random + 4 shuffled in
both), and the shuffled/random sd ratio -- the structural finding of R5 / S-099 / S-100 -- is 1.20
(button L20 TRAIN), 0.65 (button L18 TRAIN), 1.95 (basket TRAIN, matched 10), 1.87 (basket TRAIN,
full 46). Shuffled-label fitting buys variance in both codewords.

---

## 12. What I could settle, what I could not, and the ranked shortlist

### Settled from committed artifacts

| candidate | verdict |
|---|---|
| **C3** control-family size | **REFUTED as the explanation** (matched-n rank 1 vs 4 on both splits; E[button rank at 46] ~ 16 / ~31) -- but it *does* dominate the TRAIN own-layer cell, whose delta-z CI includes zero |
| **C2** headroom / base rates | **KILLED** -- button L18 has the 2nd-largest headroom and the only negative candidate |
| **C4** population | **KILLED** -- identical domains, identical 670 prompt keys, single-token codewords in both |
| **C5** axis dose / geometry | **KILLED as a dose story** -- cand/random capture ratio is *higher* for button; axes equally layer-stable |
| **C6** "only basket's axis is on the causal carrier" | **KILLED, and reversed** -- button ranks 1 of 11 on profile-alignment at both layers and both splits |
| **C7** sigmoid-scale artifact | **NOT sufficient** -- survives five weighting schemes; but basket TRAIN's rank-1 is not robust to logit trimming |
| **C8** power (same noise, bigger signal) | **PARTLY TRUE** -- B contributes 1.2-2.4x; the residual 2.7-5.1x sits in A, at matched B with opposite signs |
| **C1** "basket's probe is better" | **STANDING, unquantified** -- rank-1 LOO rho 0.5629 vs 0.5021 (+12 %); no held-out rho recorded anywhere (`CANNOT MEASURE`); no calibration from rho to rescue z exists |

**After eight candidates, exactly one survives from the brief's list (C1), one is partly true (C8),
and one new one is a partial contributor (C7). Nothing explains a 2.7x gap in A at matched family
SNR.**

### The ranked shortlist

**E1 -- THE AXIS SWAP. Rescue button's knockout along BASKET's rank-1 axis, and basket's along
BUTTON's.** This has never been run (I grepped the sprint log for any cross-codeword axis rescue;
`DCS_CSI_PROMPT_TRANSFER_*` is sentence transfer, not axis transfer). It is the only experiment that
separates C1 ("the direction is better") from "the codeword's state is more rescuable by a
low-dimensional write" -- and at cos 0.50-0.56 the two axes are far enough apart for the swap to be
informative rather than a near-identity.
*Predictions, fixed here before any data:* if C1 is right, basket's axis applied to button should
outperform button's own axis, and button's axis on basket should underperform basket's own. If the
codeword's state is what matters, **both** arms should track the codeword they are *applied to*, not
the one they were *fit on*. A third outcome -- both swapped arms failing -- would say the axis is
codeword-specific in a way neither candidate predicts.
*Cost:* `BASE/KO/KO_SELF/KO_FULL` already exist for both codewords at both layers, so this is
**1 candidate arm + 10 norm-matched controls per direction = 22 new GPU arms**. Measured per-arm
walltime from `DONE.json` across 82 button TRAIN arms: **median 762 s (12.7 min)**, min 655 s --
so **~4.7 GPU-hours**, two jobs under the 8 h walltime. It needs one new basis artifact per direction
(the other codeword's `cand_rank1` re-normalised at the target layer plus matched controls) -- a CPU
build of exactly the kind job 897529 already did.
**Do this first: highest information per GPU-hour, and it attacks the one surviving candidate.**

**E2 -- EXTEND BUTTON'S CONTROL FAMILY TO 46 AT L18. The 46 bases already exist.**
`configs/dcs_csi_axis_button_behavioral_L18.json` contains **53 bases: `cand_rank1`, `ctrl_orth`,
5 PLS, 22 `ctrl_random`, 24 `ctrl_shuffled`** -- a full 46-control rank-1 family, built and committed,
of which **only 10 were ever run**. This converts my *projection* in 4.2 (E[rank] ~ 31 at L18) into a
measurement and removes the last version of C3 anyone can raise.
*Cost:* **36 new GPU arms x 12.7 min = ~7.6 GPU-hours**, two jobs. **Zero new basis-building.**
*What it kills:* if button lands rank 1-2 of 47 at L18, C3 is resurrected and D12's framing is in
serious trouble; my projection puts that at P <= 6.5e-07, so this is a cheap, high-value falsifier of
**my own analysis**. Note button's *own-layer* (L20) family would additionally need **33 new bases**
built first -- `configs/dcs_csi_axis_button_behavioral.json` holds only 8 random + 5 shuffled rank-1
controls (30 bases total, the rest being rank-5).

**E3 -- BASKET AT L20 TO 46 CONTROLS.** Already named in PR-CSI-002's prereg ("extend the L20 control
family to 46 to match D12 before any statement is made"). Basket at L20 is the *strongest* cell in
this document (z = +5.011, rank 1 of 11 under all five weighting schemes, LOO rank 1 in 67 of 67
drops) and it is the only basket cell still floor-limited.
*Cost:* the 46 bases **already exist** in `configs/dcs_csi_axis_basket_L20.json` (22 random +
24 shuffled). **36 arms x 12.7 min = ~7.6 GPU-hours.**
*Why third:* it strengthens a cell that is already unambiguous. E1 and E2 can change the conclusion;
this one mostly cannot.

*(A fourth, and the cheapest of all: a HELD-OUT button family at L18 does not exist and no held-out
button L18 arm has ever been run. VALIDATION arms cost a measured median of **294 s (4.9 min)** across
24 basket validation control arms, so a full 46-control held-out button L18 family is **~3.8
GPU-hours** -- cheaper than either TRAIN extension, and it would make the shared-layer comparison,
which is currently the strongest evidence for the dissociation, a two-split result.)*

---

## 13. The plain conclusion, unsoftened

> **On the evidence I gathered, the dissociation is REAL. It is not an artifact of unequal
> control-family sizes.**

At matched family size (10 controls), matched family composition (6 random + 4 shuffled), matched
domains (identical 67 / 23) and matched prompts (identical 670 keys), **basket is rank 1 of 11 and
button is rank 4 of 11 on both splits, and rank 1 vs rank 8 at the shared layer L18.** Button's own
control distribution projects to an expected rank of ~16 at 46 controls (~31 at L18), with
P(rank 1 of 47) <= 3.2e-03, by a projection method calibrated on basket's own 10-to-46 transition
(predicted 2.22 and 1.01; observed 1 and 1). Headroom, population, tokenisation, dose and
axis-to-carrier alignment are all measured and all fail to explain it -- and one of them (C6) runs the
*opposite* way.

**Three things must be said alongside it, and softening any of them would be dishonest:**

1. **The TRAIN, own-layer cell -- the one the headline is usually quoted from -- is the weakest
   evidence in the set.** Its delta-z CI is [-0.226, +4.288] (includes zero) and its matched-family
   Fisher p is 0.105. The dissociation is carried by the **held-out split** (delta-z CI
   [+0.630, +7.078]; matched-family [+0.267, +4.977]) and by the **shared-layer L18 comparison**
   (CI [+0.606, +5.057], Fisher p = 0.0015).
2. **Basket's TRAIN rank-1 is not robust to how per-domain effects are weighted.** Applied
   family-wide, a logit re-expression with trimming moves it from rank 1 of 47 (p = 0.0213) to rank 3
   of 47 (p = 0.0638). Basket's VALIDATION and L20 reads are rank 1 under every scheme tested.
3. **Nothing here explains the dissociation.** Eight candidates, five killed outright, one refuted as
   the explanation, one partial (power: 1.2-2.4x of a 4-6x gap), one standing and unquantified (a
   12 % better rank-1 probe, with no held-out rho recorded anywhere and no calibration from rho to
   rescue z). **The residual is still the codeword.**

---

## 14. What may NOT be said on the basis of this document

* Not *"the dissociation is explained"* -- it is not; six candidates are removed and the residual is
  unexplained.
* Not *"basket's axis is causal"* -- prohibition 19 stands; the candidate moves 2.2-3.9 % of what the
  whole state moves.
* Not *"button's axis is worse at pointing at the causal carrier"* -- section 9 measures the opposite.
* Not *"the codewords differ only in power"* -- section 11 shows A differs by 2.7x at matched family
  SNR, with opposite signs.
* Not *"the basket TRAIN pass is fragile"* as a bare claim -- the preregistered p-scale statistic
  stands; section 10 is a robustness note on a non-preregistered re-weighting, reported because
  KILLER 2 requires a transform to be shown on the candidate and the controls alike.
* Nothing here pools button and basket (rule 3.3). Every contrast is reported side by side.
* Nothing here replicates anything, nothing here is preregistered, and TEST is untouched.
