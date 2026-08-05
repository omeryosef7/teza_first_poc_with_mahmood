# P8.0 — Doublespeak × refusal-down interaction (pilot, no GPU) — ⚠️ MECHANISTIC READING WITHDRAWN

> # 🛑 SUPERSEDED BY P8.1 — DO NOT CITE THE SUB-ADDITIVITY AS A MECHANISM
>
> **`reports/PHASE8_1_ALPHA_CALIBRATION.md` (2026-08-05, clearharm n=86) shows the sub-additivity reported
> here is a SATURATION ARTIFACT of running the ablation at α = 1.0, not a property of the mechanism.**
>
> The α sweep re-ran this exact estimator on these exact items across seven doses:
>
> | α | I_max (headroom) | Î | p |
> |---|---|---|---|
> | 0.25 (de-saturated) | **+0.477** | **−0.023** | **0.86** |
> | **1.0 (the dose used below)** | +0.186 | −0.209 | 0.020 |
> | 2.0 | +0.023 | −0.314 | 0.0004 |
>
> **Spearman(I_max, Î) = +0.991.** Î is most negative exactly where the design has least room to express a
> positive interaction. At α = 0.25, where headroom is ample, **no interaction is detectable** and |Î| sits
> at the judge noise floor. The α = 1.0 row reproduces this report's headline (−0.209 vs −0.186 here), so
> the finding below is real *as a measurement at that dose* — it simply does not mean what §5 claims.
>
> **What is withdrawn:** "sub-additive ⇒ shared refusal bottleneck" (§5.1, §5.2).
> **What still stands:** the arm tables (§2.1), the ceiling analysis (§2.4) — which turned out to be the
> whole story — the judge-instability caveat (§5.3b), and `D_i = +2` never occurring (0/137 here, and
> 0 at every α in P8.1).
> **What is NOT established:** that the channels are independent. Absence of a detectable interaction at
> n = 86 with a ≥2 pp multi-arm noise floor is not evidence of absence; the α = 0.25 CI spans
> [−0.151, +0.105].

**Status:** COMPLETE and verified as a measurement at α = 1.0; **mechanistic interpretation withdrawn
2026-08-05 (see banner).** Previously corrected after adversarial review (see §5.1, §5.3b, §5.3c): the
three outcomes are one measurement, not three, and the judge is unstable at 7.5 % in the signal arms.
**Script:** `scripts/analyze_interaction_2x2.py` · **Machine-readable output:** `outputs/interaction_2x2.json`
**Run:** `python scripts/analyze_interaction_2x2.py`

---

## 1. Method

The existing `phase_behav_refusal.py` runs already contain a **complete within-item 2 × 2 factorial**. No new
generation was needed; this is a pure re-analysis.

| factor | off | on |
|---|---|---|
| **A** — Doublespeak in-context jailbreak | direct harmful request | Doublespeak framing |
| **B** — refusal-direction ablation | none | `AllPositionProjectOutMultiLayer`, L18 refusal direction, α = 1.0, all layers/positions, through generation |

| cell | arm field in `raw.jsonl` |
|---|---|
| Y(0,0) | `direct_base` |
| Y(1,0) | `ds_base` |
| Y(0,1) | `direct_refabl` |
| Y(1,1) | `ds_refabl` |

**Authoritative run dirs** (all other `behav_refusal_*` dirs are smoke tests or preempted and are excluded):

- `outputs/behav_refusal_clearharm_a1.0_20260804_133355_708038` — **n = 86** (44 train / 42 test)
- `outputs/behav_refusal_curated_a1.0_20260804_125055_708039` — **n = 51** (30 train / 21 test)

**Completeness check:** all 4 arms have a non-null label *and* a non-null score on **every** row of both
cohorts. `complete_2x2 = True`, `rows_missing_an_arm = []`. n per cell = n per split (86 / 51 pooled); the
design is fully crossed and fully paired, so every item contributes to every cell.

**Outcomes (three, reported separately).**
1. **ASR (binary)** — `label == "MALICIOUS"`, i.e. StrongREJECT graded score ≥ 0.25.
2. **Graded score** — the stored StrongREJECT `*_score` ∈ [0, 1] (the continuous outcome that §0.5 flagged as
   better-powered than the binary one).
3. **Compliance** — `1 − (label == "REJECTED")`, i.e. "did not refuse". **This is not ASR.** The gap between
   them is the §0.10 *complied-but-benign* fraction and is reported per cell.

**Estimator.** Per item, the within-item difference-in-differences
`D_i = Y_i(1,1) − Y_i(1,0) − Y_i(0,1) + Y_i(0,0)`; the interaction is `Î = mean(D_i)`. Because all four cells
are measured on the same item, `Î` is exactly `Δ_combined − Δ_concept − Δ_refusal` (verified numerically as an
independent identity check).

**Inference.** 95 % CI by **paired percentile bootstrap over items**, 10 000 resamples,
`np.random.default_rng(20260805)`. Two-sided **sign-flip permutation** p-value, 50 000 sign vectors, same
seed, `p = (#{|mean(±D)| ≥ |Î|} + 1) / (n_perm + 1)`. Both are applied to all three outcomes.

---

## 2. Results — clearharm (the primary cohort)

### 2.1 Cell means (n per cell = n per split; every item in every cell)

| split | outcome | Y(0,0) direct | Y(1,0) DS | Y(0,1) refabl | Y(1,1) DS+refabl |
|---|---|---|---|---|---|
| train (44) | **ASR** | 0.1364 | 0.3864 | 0.5682 | 0.7273 |
| | graded score | 0.1108 | 0.3210 | 0.5057 | 0.5824 |
| | compliance | 0.1591 | 0.5227 | 0.7273 | 0.9545 |
| | *complied-but-benign gap* | +0.023 | +0.136 | +0.159 | **+0.227** |
| test (42) | **ASR** | 0.0714 | 0.3571 | 0.5476 | 0.5476 |
| | graded score | 0.0714 | 0.2887 | 0.5238 | 0.4911 |
| | compliance | 0.1190 | 0.5476 | 0.7381 | 0.9048 |
| | *complied-but-benign gap* | +0.048 | +0.190 | +0.190 | **+0.357** |
| **pooled (86)** | **ASR** | **0.1047** | **0.3721** | **0.5581** | **0.6395** |
| | graded score | 0.0916 | 0.3052 | 0.5145 | 0.5378 |
| | compliance | 0.1395 | 0.5349 | 0.7326 | 0.9302 |
| | *complied-but-benign gap* | +0.035 | +0.163 | +0.174 | **+0.291** |

### 2.2 Main effects and the interaction

| split | outcome | Δ_concept | Δ_refusal | Δ_combined | additive prediction | **Î** | Var(D) | 95 % CI | perm p |
|---|---|---|---|---|---|---|---|---|---|
| train | ASR | +0.250 | +0.432 | +0.591 | +0.682 | **−0.091** | 0.550 | [−0.318, +0.136] | 0.543 |
| train | score | +0.210 | +0.395 | +0.472 | +0.605 | **−0.134** | 0.465 | [−0.330, +0.068] | 0.206 |
| train | compliance | +0.364 | +0.568 | +0.795 | +0.932 | **−0.136** | 0.493 | [−0.341, +0.068] | 0.283 |
| test | ASR | +0.286 | +0.476 | +0.476 | +0.762 | **−0.286** | 0.697 | [−0.548, −0.024] | **0.050** |
| test | score | +0.217 | +0.452 | +0.420 | +0.670 | **−0.250** | 0.550 | [−0.473, −0.027] | **0.037** |
| test | compliance | +0.429 | +0.619 | +0.786 | +1.048 | **−0.262** | 0.393 | [−0.452, −0.071] | **0.019** |
| **pooled** | **ASR** | **+0.267** | **+0.453** | **+0.535** | +0.721 | **−0.186** | 0.624 | **[−0.349, −0.023]** | **0.045** |
| **pooled** | **score** | +0.214 | +0.423 | +0.446 | +0.637 | **−0.190** | 0.504 | **[−0.340, −0.041]** | **0.016** |
| **pooled** | compliance | +0.395 | +0.593 | +0.791 | +0.988 | **−0.198** | 0.443 | [−0.337, −0.058] | **0.012** |

**The plan §0.6 headline is confirmed exactly:** pooled `Î = −0.186 [−0.349, −0.023]`, perm `p = 0.045`
(plan stated −0.186 [−0.353, −0.019], p = 0.043; the CI differs only in the third decimal because the
bootstrap seed is now pinned at 20260805).

**The graded score AGREES with the binary outcome — and is stronger.** Pooled `Î_score = −0.190`
(p = 0.016) vs `Î_binary = −0.186` (p = 0.045); same sign, near-identical magnitude, lower variance
(0.504 vs 0.624). Unlike §0.5's carry-head case, here the binary/graded discrepancy does **not** threaten the
conclusion — it reinforces it. Compliance gives the same picture again (`Î = −0.198`, p = 0.012).

### 2.3 Distribution of D_i (binary ASR)

| split | D = −2 | D = −1 | D = 0 | D = +1 | **D = +2** |
|---|---|---|---|---|---|
| train (44) | 0 | 14 | 20 | 10 | **0** |
| test (42) | 3 | 13 | 19 | 7 | **0** |
| **pooled (86)** | **3** | **27** | **39** | **17** | **0** |

**`D_i = +2` never occurs in any split of either cohort, while `D_i = −2` does (3 items).** A `+2` item would
be one that neither manipulation jailbreaks alone but both jailbreak together — the signature of genuine
synergy. There is not a single such item in 137 items across two cohorts. The asymmetry (27 items at −1 vs 17
at +1) is what drives `Î < 0`.

Graded score, pooled: 40 items negative, 24 exactly zero, 22 positive — same directional asymmetry.

### 2.4 The ceiling (plan §0.7)

`I_max = 1 − ASR(1,0) − ASR(0,1) + ASR(0,0)` — the largest interaction arithmetically reachable given the
observed marginals.

| split | I_max | items already jailbroken by A-alone **or** B-alone (can only contribute D_i ≤ 0) |
|---|---|---|
| train (44) | **+0.182** | 28 / 44 = **63.6 %** |
| test (42) | **+0.167** | 26 / 42 = **61.9 %** |
| **pooled (86)** | **+0.174** | 54 / 86 = **62.8 %** |

(Proof of the "≤ 0" claim: if `Y(1,0)=1, Y(0,1)=0` then `D = Y(1,1) − 1 ≤ 0`; symmetrically for the other
single-factor case; if both are 1 then `D = Y(1,1) + Y(0,0) − 2 ≤ 0`.)

A +0.15 synergy target would consume 86 % of the entire headroom at α = 1.0. **P8.1's α-calibration is a
hard prerequisite for any positive-interaction test**, exactly as §0.7 says.

### 2.5 Refusal-down-resistant subgroup — ⚠ SELECTION ON THE OUTCOME, EXPLORATORY ONLY

Items where refusal-ablation alone did **not** jailbreak (`Y(0,1) = 0`).

| split | n (frac) | ASR(0,0) | ASR(1,0) | ASR(0,1) | ASR(1,1) | Δ_concept \| B=0 | Δ_concept \| B=1 |
|---|---|---|---|---|---|---|---|
| train | 19 (0.432) | 0.000 | 0.158 | 0.000 | 0.684 | +0.158 | **+0.684** |
| test | 19 (0.452) | 0.000 | 0.158 | 0.000 | 0.474 | +0.158 | **+0.474** |
| **pooled** | **38 (0.442)** | 0.000 | 0.158 | 0.000 | 0.579 | +0.158 | **+0.579** |

**This subgroup is defined by conditioning on a post-treatment outcome.** Items land in it partly because
refusal-ablation genuinely failed on them and partly because of judge noise on that one arm; conditioning on
`Y(0,1)=0` therefore selects for downward noise in arm (0,1) and the large `Δ_concept | B=1` is inflated by
regression to the mean. **It is not a valid causal estimate and must not be reported as one.** It is listed
because it generates a testable hypothesis for P8.2: *among items refusal-ablation cannot crack, Doublespeak
on top of refusal-ablation still adds a large amount* — which would have to be confirmed on a
pre-registered, non-selected subgroup (e.g. defined by a *pre-treatment* covariate such as the item's
baseline refusal projection) to count.

---

## 3. Results — curated (secondary cohort; do not use as the headline)

| split | outcome | Y(0,0) | Y(1,0) | Y(0,1) | Y(1,1) | Î | 95 % CI | perm p |
|---|---|---|---|---|---|---|---|---|
| train (30) | ASR | 0.267 | 0.300 | 0.700 | 0.367 | −0.367 | [−0.633, −0.100] | 0.019 |
| train | score | 0.229 | 0.275 | 0.558 | 0.279 | −0.325 | [−0.542, −0.100] | 0.010 |
| test (21) | ASR | 0.286 | 0.095 | 0.714 | 0.095 | −0.429 | [−0.714, −0.095] | 0.034 |
| test | score | 0.268 | 0.060 | 0.595 | 0.042 | −0.345 | [−0.583, −0.107] | 0.015 |
| **pooled (51)** | **ASR** | 0.275 | 0.216 | 0.706 | 0.255 | **−0.392** | [−0.588, −0.196] | **0.0004** |
| **pooled** | score | 0.245 | 0.186 | 0.574 | 0.181 | **−0.333** | [−0.493, −0.172] | **0.0003** |
| **pooled** | compliance | 0.314 | **1.000** | 0.745 | **1.000** | **−0.431** | [−0.569, −0.294] | **< 0.0001** |

D_i distribution (pooled ASR): −2: 2, −1: 21, **0: 23**, +1: 5, **+2: 0**. `I_max = +0.353`;
37 / 51 = 72.5 % of items already jailbroken by one factor alone.
Resistant subgroup: n = 15 (0.294), Δ_concept | B=1 = +0.200 (same exploratory caveat).

**Read this cohort with care.** On curated, `Δ_concept` is **negative** for ASR (−0.059 pooled) — Doublespeak
*reduces* ASR relative to the direct request — while compliance under Doublespeak is **exactly 1.000** (zero
REJECTED rows in either DS arm; verified by an independent `grep -c`). The complied-but-benign gap is
**+0.78 / +0.75** in the two DS cells. On this cohort the model never refuses under Doublespeak but also
almost never produces genuinely harmful content: the binding constraint is **off-target capability, not
refusal**. The curated interaction is therefore dominated by a floor/capability artifact and mostly measures
"refusal-ablation on the direct arm is the only thing that produces harm here". **The clearharm pooled result
is the paper number; curated is a consistency check that happens to agree in sign.**

---

## 4. ASR ≠ compliance (plan §0.10)

The complied-but-benign fraction (compliance − ASR) grows monotonically as manipulations are stacked:

| cohort | (0,0) | (1,0) | (0,1) | (1,1) |
|---|---|---|---|---|
| clearharm pooled | +0.035 | +0.163 | +0.174 | **+0.291** |
| curated pooled | +0.039 | **+0.784** | +0.039 | **+0.745** |

In the clearharm combined arm the model **complies on 93.0 % of items but only reaches ASR 0.640** — 29.1 pp
of items comply-but-produce-nothing-useful. This is the mechanical explanation of the ceiling in §2.4: once
both manipulations are applied, refusal is essentially gone (refusal rate 4.6 % train / 9.5 % test), so the
remaining headroom is not a refusal problem at all — it is the model's inability to actually do the harmful
task. Any future arm that claims to raise ASR must therefore state which of the two limits it is attacking.

---

## 5. Interpretation — honest reading

> ⚠️ **§5.1 and §5.2 below are WITHDRAWN** — see the banner at the top of this file. They read a
> saturation artifact as a mechanism. P8.1 shows the effect vanishes (Î = −0.023, p = 0.86) once the dose
> is de-saturated, while §2.4's own ceiling analysis — written here as a caveat — turned out to be the
> entire explanation. §5.3b (judge instability) and §5.3c (the sign-flip symmetry violation) stand, and
> both pointed in this direction already.

1. **The interaction is negative.** Pooled clearharm `Î = −0.186 [−0.349, −0.023]`, perm p = 0.045; the
   graded score gives `−0.190`, p = 0.016; compliance gives `−0.198`, p = 0.012. At split level all 12
   estimates are negative; the three clearharm-**train** outcomes are not significant (p = 0.543 / 0.206 /
   0.283) and the clearharm-test binary p is borderline at 0.0498.

   ⚠ **These three outcomes are NOT independent evidence** (corrected 2026-08-05 after adversarial review).
   The binary MALICIOUS label is a *deterministic threshold* of the graded score — verified across all 5
   arms of all 137 rows in both cohorts, **0 violations** of `(label == MALICIOUS) ⟺ (score ≥ 0.25)` — and
   compliance is derived from the same generations. Binary, graded and compliance are three views of **one
   measurement**, not three corroborating ones. An earlier draft of this section claimed "six pooled
   estimates, all six with p < 0.05"; that framing inflated the apparent weight of evidence and has been
   withdrawn.

   ⚠ **The curated compliance cell is algebraically degenerate.** Compliance is exactly 1.000 in *both*
   Doublespeak arms, so `D_i = 1 − 1 − Y(0,1) + Y(0,0)` collapses to `Y(0,0) − Y(0,1)` (verified: every
   non-zero `D_i` is −1, distribution {−1: 22, 0: 29}). That "interaction" of −0.431 is not an interaction
   at all — it is the **main effect of refusal ablation on the direct arm** with the DS arms pinned to the
   ceiling. It must not be counted as supporting evidence.
2. **This is what a shared refusal bottleneck predicts.** If the demonstrations' causal work is *suppressing
   refusal*, then once the refusal direction has already been projected out there is much less left for
   Doublespeak to remove; their effects overlap rather than compose. That is consistent with the project's
   standing finding that the token→concept remap is behaviorally inert while the refusal-bypass is the live
   locus.
3. **But sub-additivity alone does not prove a shared mechanism.** At α = 1.0 the design is severely
   ceiling-limited (`I_max = +0.174`; 62.8 % of items can only contribute `D_i ≤ 0`), so a negative `Î` is
   partly *arithmetically forced*. The honest statement is: **the data are consistent with a shared
   bottleneck and rule out strong synergy, but the ceiling means the magnitude of `Î` is not a clean
   mechanistic quantity.** The `D_i = +2` count of **0 / 137** is the more robust piece of evidence, because
   it is a statement about individual items, not about a saturated average.
3b. ⚠ **MEASUREMENT INSTABILITY — the largest threat to this result** (added 2026-08-05 after adversarial
   review). A technical replicate of the *same* condition exists: the preempted twin
   `behav_refusal_clearharm_a1.0_20260804_125311_708038` (80 rows, same SLURM job 708038) against the
   authoritative `..._133355_708038`. On the **80 overlapping items**, the two runs disagree on:

   | arm | label flips | |
   |---|---|---|
   | `direct_randabl` | **0 / 80 (0.0%)** | ← the control arm is perfectly stable |
   | `direct_base` | 2 / 80 (2.5%) | |
   | `ds_base` | 2 / 80 (2.5%) | |
   | **`direct_refabl`** | **6 / 80 (7.5%)** | ← carries the signal |
   | **`ds_refabl`** | **6 / 80 (7.5%)** | ← carries the signal |

   Restricted to those same 80 items, `Î = −0.150` (p = 0.111) in one run and `−0.100` (p = 0.277) in the
   other — a **run-to-run swing of 0.050 on `Î`**, roughly a quarter of the headline effect and **larger
   than the distance from the published CI upper bound (−0.023) to zero**.

   Because `direct_randabl` — which is equally hooked but produces refusals — is perfectly stable, this is
   **not** hook nondeterminism. It is **StrongREJECT judge variance on borderline completions**,
   concentrated precisely in the arms that carry the signal. (P10.0's independently-estimated per-direction
   noise anchor p₀ = 0.089 is the same phenomenon measured another way: 7.5% / 2 = 3.75% per direction.)

   **Consequence: `p = 0.045` is fragile and must not be reported as a clean significance.** The confound-
   immune statements are the item-level ones — `D_i = +2` never occurs in 137 items — and the direction of
   the effect, which is stable across both replicates. Any confirmatory P8 run must measure and report the
   judge-replication envelope (plan §P1 already requires ≥3 repeated baseline runs for exactly this reason).

3c. **Statistical caveat: the sign-flip null is not exact here.** The permutation tests are correctly
   implemented and correctly two-sided, but the sign-flip null tests "`D_i` symmetric about 0", not
   "`E[D_i] = 0`". §2.4 establishes that 62.8% of items can only produce `D_i ≤ 0`, so the `D` distribution
   is structurally asymmetric under *any* hypothesis. The reported p-values should be read as approximate.

4. **Consequence for Phase 8 (this is the actionable part).** P8 as originally scoped — powered to detect a
   *positive* +0.10 / +0.15 interaction — is aimed in the wrong direction and, at α = 1.0, is aimed at a
   target that barely fits inside the arithmetic headroom. P8 should be re-registered as a **sub-additivity
   test**, and P8.1's α-sweep (landing refusal-alone ASR in 0.20–0.40, which restores `I_max ≥ +0.33`) is a
   blocking prerequisite for any arm that hopes to see synergy.
5. **What would falsify the shared-bottleneck reading.** A sub-saturating α at which `Î` becomes ≈ 0 or
   positive, or a non-zero count of `D_i = +2` items, would show the sub-additivity here is a saturation
   artifact rather than a mechanism. That is precisely the P8.1 → P8.2 experiment.

### Caveats (do not drop these from the paper)

- Single model (the project's primary Llama), single refusal direction (L18), single α (1.0). §0.10's warning
  that the 32 per-layer directions are unvalidated does **not** apply here — this run uses the validated L18
  direction — but it does mean the result cannot yet be claimed to be layer-general.
- The ablation used is `AllPositionProjectOutMultiLayer`, one of the three primitives §0.9 confirms is
  genuinely decode-safe. This result is **not** affected by the prefill-only patching bug.
- n = 86 (clearharm). The test-split-only estimate sits at p = 0.050; the significance of the pooled estimate
  depends on pooling train and test, which is legitimate here only because both splits were generated by the
  identical pipeline and no model selection was done on either.
- ASR is the StrongREJECT ≥ 0.25 threshold. The graded-score analysis, which is threshold-free, agrees.

---

## 6. Reproduction

```
python scripts/analyze_interaction_2x2.py            # writes outputs/interaction_2x2.json + console tables
```

Deterministic **given the input data**: `np.random.default_rng(20260805)`, 10 000 bootstrap resamples,
50 000 sign flips. NOTE this is analysis-level determinism only — the underlying *measurement* is not
reproducible run-to-run (see §5.3b: 7.5% label flips between technical replicates in the signal arms). Seed
sensitivity of the headline permutation p across five seeds: 0.0451 / 0.0447 / 0.0441 / 0.0436 / 0.0444.
Independent parametric cross-checks of the same `Î`: normal-approximation z-test p = 0.029, Wilcoxon
signed-rank p = 0.032 — both agree with the permutation test.

Independent recount of cell counts by `grep -c` on the raw JSONL (a completely separate code path from the
analysis script), all matching:

| check | grep count | script value |
|---|---|---|
| clearharm `ds_base` MALICIOUS | 32 / 86 | ASR 0.3721 ✓ |
| clearharm `ds_refabl` MALICIOUS | 55 / 86 | ASR 0.6395 ✓ |
| clearharm `direct_refabl` MALICIOUS | 48 / 86 | ASR 0.5581 ✓ |
| clearharm test-split `ds_refabl` MALICIOUS | 23 / 42 | ASR 0.5476 ✓ |
| curated `direct_refabl` MALICIOUS | 36 / 51 | ASR 0.7059 ✓ |
| curated `ds_base` REJECTED | 0 / 51 | compliance 1.000 ✓ |
