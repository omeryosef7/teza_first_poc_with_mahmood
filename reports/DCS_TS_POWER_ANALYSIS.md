# DCS thesis-scale POWER ANALYSIS — power before GPU

**Mandate section 20. This gates spend.**
Produced 2026-09-07, PHASE 3, against the R-098 aligned banks.
Everything below is CPU-only prompt/artifact analysis. No model was loaded, no GPU, no network.

- **Instrument:** `scripts/dcs_ts_power.py`
- **Reproduce:** `python scripts/dcs_ts_power.py --all --reps 300`
- **Falsifiability harness:** `python scripts/dcs_ts_power.py --selftest` → `SELFTEST VERDICT: PASS — every check is falsifiable` (§7)
- **Python:** numpy 2.4.6 / scipy 1.17.1 / scikit-learn 1.9.0

---

## VERDICT (details in §8)

> **YES — the flagship test is adequately powered at 70/23/23, and the split should NOT be changed,**
> **provided four reporting rules are adopted with it.** At 23 test domains the design detects any
> true per-domain mean accuracy at or above **0.426** (delta **0.0925** over the 1/3 chance line) with
> power 0.80 at alpha 0.05, under the best available SD estimate (0.1514). The previously published
> effect was **0.7485** (delta **0.4152**) — a **4.5x** margin over the MDE. Even a *quartered* effect
> (accuracy 0.437) is detected with power 0.87.
>
> **The failure that must never recur is not power. It is resolution.** The old headline
> `p = 0.004975124378109453` was `1/201`, the arithmetic floor at `n_perm = 200`. That floor is a
> property of the permutation count, not of the data, and it is unchanged by going to 116 domains.
> **Set `n_perm = 10000` for the flagship** (floor `9.999e-05`) and never report a floor as a value.
>
> The one genuine risk to the 23-domain choice is that the between-domain SD is itself estimated from
> **six** domains; its 95% chi-square upper bound is **0.3439**, at which the MDE degrades to **0.2102**
> and a halved effect is detected with power 0.76 rather than 1.000. §8 gives the trigger that would
> make 58/29/29 the right call, and it is a trigger observable on TRAIN domains before any test-set
> read.

---

## 0. What actually binds (re-derived from raw bank rows, not from `_meta.json`)

The flagship cell is `cell == "C"` AND `query_kind == "semantic_one_word"` AND `n_examples == 4`.
Note the trap: `cell` in these banks is the single letter `C`; the string `natural_doublespeak`
lives in the **`condition`** field. Selecting on the long form binds **zero rows** — that is
mutation `M_CELL` in §7, and it is exactly the class of silent-empty-set defect this project has
shipped four times.

| bank | flagship rows | domains | rows/domain | bank_block | within-domain `split` |
|---|---|---|---|---|---|
| `ts116_button_bomb`  | 1160 | 116 | 10 | `cds_n4_sow` | dev 580 / heldout 580 |
| `ts116_button_knife` | 1160 | 116 | 10 | `cds_n4_sow` | dev 580 / heldout 580 |
| `ts116_button_gun`   | 1160 | 116 | 10 | `cds_n4_sow` | dev 580 / heldout 580 |
| `ts116_basket_bomb`  | 1160 | 116 | 10 | `cds_n4_sow` | dev 580 / heldout 580 |
| `ts116_basket_knife` | 1160 | 116 | 10 | `cds_n4_sow` | dev 580 / heldout 580 |
| `ts116_basket_gun`   | 1160 | 116 | 10 | `cds_n4_sow` | dev 580 / heldout 580 |

All 116/116 domains in every bank are covered by `dcs_ts116_domain_split.json`
(`manifest_sha16 be7d2c772d814ef3`, field `dsplit`, seed 202609061, 70 train / 23 validation / 23 test).

**The single most consequential number in this document:**

| quantity | value |
|---|---|
| rows per domain **per concept** in the flagship cell | **10** |
| test rows per domain for the 3-way probe, **one** codeword | **30** |
| test rows per domain for the 3-way probe, **both** codewords | **60** |
| total test rows, 23 domains x 2 codewords | 1380 |

The old 6-domain design had **57** test rows per domain. The new design has **30** (or 60 with both
codewords) — *fewer rows per domain, far more domains*. That trade is correct for a domain-level
estimand, but it means the per-domain accuracy is noisier and the SD grid below must account for it.

Within one domain the 10 rows differ **only** by demonstration slot (5 slots) and by the within-domain
`split` (dev/heldout). `bank_block`, `condition`, `demo_valence`, `strength`, `consistency`,
`role_style`, `example_position` are all constant. These rows are near-replicates. See §4.

---

## 1. The attainable p-FLOOR at n_test = 23

### 1a. Two-sided sign test over per-domain above-chance indicators

Exact binomial at p0 = 0.5, re-derived by exhaustive enumeration of all 2^n sign patterns
(check `K3`).

| n domains | smallest attainable two-sided p | distinct p-values available |
|---|---|---|
| 6 | **0.03125** | 7 |
| 12 | 0.00048828125 | 13 |
| **23** | **2.384185791015625e-07** | 24 |
| 38 | 7.275957614183426e-12 | 39 |
| 116 | 2.407412430484045e-35 | 117 |

At n = 6 the sign test **cannot** return anything below 0.031 — so the old headline
`p = 0.004975` provably did not come from the sign test, and 6/6 domains was worth exactly
p = 0.031, not p = 0.005. At n = 23 the floor is 2.4e-07, five orders of magnitude below alpha:
the sign test's resolution is no longer a binding constraint.

Rejection threshold at n = 23, alpha 0.05 two-sided: **k >= 17 of 23 domains above chance**
(re-derived, not assumed). MDE in per-domain success probability: **pi = 0.788** at power 0.80
(n=6: 0.964; n=29: 0.772; n=38: 0.731).

⚠ **The sign test's null is mis-specified here and should not be the flagship instrument.**
Its p0 = 0.5 assumes a per-domain accuracy median exactly at chance. The pure-noise simulation
(§6) measures the realised probability that a test domain lands *strictly above* 1/3 at
**0.4352**, not 0.5 — because with 30 rows the binomial has an atom at exactly 1/3 and is
right-skewed. Using p0 = 0.5 is therefore **conservative** at this design, but it is conservative
by an unaudited amount. **Use the sign test descriptively ("k/23 domains above chance") and let
the group permutation carry the inference.**

### 1b. Group permutation

Estimator: `p = (1 + #{null >= obs}) / (B + 1)`. Its attainable floor is `1/(B+1)`.

| B (`n_perm`) | floor `1/(B+1)` | smallest *measured* (non-floor) p, `2/(B+1)` | MC SE at p=0.05 | MC SE at p=0.005 | rel. SE at p=0.005 |
|---|---|---|---|---|---|
| 200 | **0.004975124378109453** | 0.00995 | 0.01541 | 0.004987 | **99.7%** |
| 1000 | 0.000999000999000999 | 0.001998 | 0.006892 | 0.002230 | 44.6% |
| 2000 | 0.0004997501249375312 | 0.0009995 | 0.004873 | 0.001577 | 31.5% |
| **10000** | **9.999000099990002e-05** | 0.00019998 | 0.002179 | 0.0007053 | **14.1%** |

**The previous phase's headline `p = 0.004975124378109453` is exactly the B=200 floor.** At B=200 a
p-value of 0.005 has a Monte-Carlo relative standard error of 99.7% — it carries essentially no
information about the size of the tail. Note also that at B=200 the estimator cannot distinguish
"one permutation beat the observation" from "the observation is the single most extreme point in a
space of 6^23 = 7.9e17 relabelings".

**Recommendation: `n_perm = 10000` for the flagship**, with the reporting rule below. B=2000 is the
absolute minimum and is acceptable only for secondary/exploratory contrasts.

> **REPORTING RULE (mandatory).** If zero permutations reach the observed statistic, report
> **`p < 1/(B+1)`** with B stated. Never print `1/(B+1)` as if it were a measured value. Every
> permutation p in every artifact must be published next to its floor.

### 1c. A property of n=23 that fixes an old defect for free

The group-permutation exchangeability space is `(k!)^n`. The degenerate "global relabel" case
(the same permutation drawn in every domain, which reproduces the observed accuracy exactly and
which `C-058`/`PR-039` had to condition away by hand) has null mass `k!/(k!)^n`:

| n | 3-class mass | 2-class mass |
|---|---|---|
| 6 | 1.286e-04 | **0.03125** ← this is what contaminated the three 2-class contrasts |
| 12 | 2.756e-09 | 4.883e-04 |
| **23** | **7.598e-18** | **2.384e-07** |
| 116 | 3.255e-90 | 2.407e-35 |

At n = 23 the global-relabel degeneracy is 2.4e-07 even for a 2-class contrast. The
`EXCLUDE_GLOBAL_RELABELS` conditioning is no longer load-bearing and can be reported either way
without changing any conclusion. Keep it on for continuity; document that it no longer matters.

---

## 2. MDE for the domain-level estimator

### 2a. What the SD estimate is, and where it comes from

The **only** empirical per-domain accuracies in the record are the OLD 6-domain ones, re-derived
here from `outputs/boombness/dcs_analysis/dcs_bombness_specificity.json` field
`P2_primary.per_domain` (mean recomputed as 0.7485380116959064, matching the published value to
0.0):

| domain | accuracy |
|---|---|
| city_bridge | 0.7719298245614035 |
| farm_storage | 0.8421052631578947 |
| game_manual | 0.5438596491228070 |
| instructional | 0.9298245614035088 |
| lab_safety | 0.7719298245614035 |
| news_report | 0.6315789473684210 |

Denominator recovered from the common divisor of the accuracies: **m_old = 57 rows/domain**.

**⚠ THESE ARE ASSUMPTIONS, NOT MEASUREMENTS OF THE NEW BANKS.** They come from the UNALIGNED
6-domain corpora in which 948 of 1008 cell-C rows differed across concepts. The new aligned banks
pay for alignment with bomb-derived knife/gun demonstration text; whether knife and gun install at
all is an open empirical question. If they install more weakly, both the mean and the between-domain
SD will differ from these numbers.

Variance decomposition (observed spread = true between-domain spread + binomial sampling noise):

| quantity | value |
|---|---|
| observed sample SD across 6 domains | **0.14020460213792754** |
| binomial within-domain variance at m=57 | 0.003014872772369006 |
| implied **between-domain SD** | **0.12900564983087193** |
| projected SD at the new m = 30 (1 codeword) | **0.15138280256695957** |
| projected SD at the new m = 60 (2 codewords) | **0.14063998471507422** |

**The SD is itself estimated from 6 domains, i.e. 5 df.** Its chi-square 95% CI is
**[0.0875, 0.3439]**. The upper end is the honest planning value for a pessimist.

A second, independent anchor from the same artifact: the `P2_basket_lexical_transfer` contrast
(the *second codeword*, the closest analogue to what the new banks test) gives mean **0.6974**,
sample SD **0.15140157751202657** — a lower mean and a slightly larger SD than the primary. This is
the more conservative of the two anchors and it is the one used in the headline MDE.

### 2b. MDE at n = 23

Minimum detectable mean offset above 1/3, one-sample t, alpha 0.05 two-sided, power 0.80:

| assumed SD | source of that SD | MDE (delta over 1/3) | implies mean accuracy |
|---|---|---|---|
| 0.05 | optimistic | 0.0306 | 0.364 |
| 0.10 | optimistic | 0.0611 | 0.394 |
| **0.1402** | old 6-domain observed SD | **0.0857** | **0.419** |
| 0.15 | round number | 0.0917 | 0.425 |
| **0.1514** | **projected, m=30, 1 codeword (HEADLINE)** | **0.0925** | **0.426** |
| 0.1406 | projected, m=60, 2 codewords | 0.0859 | 0.419 |
| 0.20 | pessimistic | 0.1223 | 0.456 |
| 0.25 | pessimistic | 0.1528 | 0.486 |
| **0.3439** | **95% chi-square upper bound on the 6-domain SD** | **0.2102** | **0.543** |
| 0.3333 | distribution-free bound (see below) | 0.2038 | 0.537 |

**Distribution-free bound.** Per-domain accuracies of a probe that never falls below chance lie in
[1/3, 1]; a variable confined to an interval of width w has sample SD at most w/2, so
**SD <= 1/3**, giving a worst-case MDE at n=23 of **0.2038** (mean accuracy 0.537) that assumes
nothing at all about the distribution. Even under this bound, the previously published 0.7485 is
detected with power 1.000. *(If one refuses even the "never below chance" premise and allows
[0, 1], the bound is SD <= 0.5, but that admits per-domain accuracies of 0, which the old record
contradicts in 6/6 domains.)*

---

## 3. Power curves over n_test

Power of the one-sample t-test against chance, alpha 0.05 two-sided. `delta` = true mean accuracy
minus 1/3. **The 0.4152 column is the old published effect; it is off the right edge of every table
at power 1.000.**

**SD = 0.1514 (headline: projected for m=30, one codeword)**

| n_test | d=0.05 | d=0.10 | d=0.15 | d=0.20 | d=0.25 | d=0.30 | d=0.40 | MDE |
|---|---|---|---|---|---|---|---|---|
| 6 | 0.102 | 0.261 | 0.500 | 0.735 | 0.894 | 0.968 | 0.999 | 0.2172 |
| 12 | 0.182 | 0.550 | 0.877 | 0.986 | 0.999 | 1.000 | 1.000 | 0.1345 |
| **23** | **0.328** | **0.857** | **0.995** | **1.000** | **1.000** | **1.000** | **1.000** | **0.0925** |
| 29 | 0.404 | 0.930 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0816 |
| 38 | 0.509 | 0.977 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0707 |
| 58 | 0.696 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0567 |
| 116 | 0.941 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0397 |

**SD = 0.1406 (projected for m=60, both codewords)**

| n_test | d=0.05 | d=0.10 | d=0.15 | d=0.20 | d=0.25 | MDE |
|---|---|---|---|---|---|---|
| 6 | 0.110 | 0.294 | 0.558 | 0.794 | 0.931 | 0.2017 |
| 12 | 0.203 | 0.613 | 0.919 | 0.994 | 1.000 | 0.1249 |
| **23** | **0.371** | **0.903** | **0.998** | **1.000** | **1.000** | **0.0859** |
| 29 | 0.456 | 0.959 | 1.000 | 1.000 | 1.000 | 0.0758 |
| 38 | 0.570 | 0.990 | 1.000 | 1.000 | 1.000 | 0.0656 |
| 58 | 0.759 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0526 |
| 116 | 0.967 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0369 |

**SD = 0.3439 (the pessimistic case: 95% chi-square upper bound on a 5-df SD estimate)**

| n_test | d=0.05 | d=0.10 | d=0.15 | d=0.20 | d=0.25 | d=0.30 | d=0.40 | MDE |
|---|---|---|---|---|---|---|---|---|
| 6 | 0.060 | 0.090 | 0.141 | 0.214 | 0.305 | 0.410 | 0.629 | 0.4933 |
| 12 | 0.075 | 0.152 | 0.282 | 0.452 | 0.631 | 0.785 | 0.955 | 0.3056 |
| **23** | **0.102** | **0.266** | **0.516** | **0.760** | **0.915** | **0.979** | **1.000** | **0.2102** |
| 29 | 0.118 | 0.327 | 0.621 | 0.856 | 0.965 | 0.995 | 1.000 | 0.1853 |
| 38 | 0.141 | 0.415 | 0.745 | 0.937 | 0.992 | 0.999 | 1.000 | 0.1605 |
| 58 | 0.193 | 0.586 | 0.904 | 0.992 | 1.000 | 1.000 | 1.000 | 0.1287 |
| 116 | 0.342 | 0.874 | 0.997 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0902 |

Curves for SD in {0.08, 0.10, 0.1402, 0.20, 0.25} are in the script's stdout; they interpolate
monotonically between the tables above.

**Reading of the curves.** The 23-vs-29 difference is small everywhere (MDE 0.0925 -> 0.0816, an
11.8% improvement, bought with 12 fewer training domains). The 23-vs-58 difference is large
(MDE 0.0925 -> 0.0567, 38.7%) but 58 test domains leaves only 58 for train+validation combined.
**The knee of the curve for a plausible effect is well below n=23**: at any delta >= 0.15 —
i.e. a mean accuracy of 0.483, which is *less than half* the old excess over chance — even n=12
delivers power 0.877. The 70/23/23 allocation is not the constraint on this experiment.

---

## 4. ICC and the row-level temptation

### 4a. Estimated ICC of the correctness indicator

Re-derived from the six OLD per-domain accuracies (§2a): between-domain variance of the true
per-domain accuracy 0.016647, total variance of the 0/1 correctness indicator
`pbar(1-pbar) = 0.7485 x 0.2515 = 0.18825`.

> **ICC (correctness indicator) = 0.08841608017135857**

Design effect `DEFF = 1 + (m-1) x ICC` and effective sample size if rows were treated as
independent:

| design | m rows/domain | n domains | N rows | DEFF | **n_eff** | z inflation if rows treated iid |
|---|---|---|---|---|---|---|
| old 6-domain | 57 | 6 | 342 | 5.951 | **57.5** | 2.440 |
| new, 1 codeword | 30 | 23 | 690 | 3.564 | **193.6** | 1.888 |
| **new, 2 codewords** | **60** | **23** | **1380** | **6.217** | **222.0** | **2.493** |
| new, 2 codewords, all 116 domains | 60 | 116 | 6960 | 6.217 | 1119.6 | 2.493 |

**Read the second-to-last row.** A row-level analysis of the flagship test would advertise
**1380** independent observations. The design carries **222**. Adding the second codeword moves
n_eff from 193.6 to 222.0 — a 15% gain for a doubling of rows, which is the correct way to think
about it: **rows are nearly free and nearly worthless; domains are expensive and are the whole
sample.**

### 4b. How badly a row-level p overstates significance at this design

Multiply the z-statistic by `sqrt(DEFF) = 2.493` (m=60, 23 domains):

| honest domain-level p | what a row-level p would print |
|---|---|
| 0.05 | **1.02e-06** |
| 0.01 | **1.34e-10** |
| 0.001 | **2.32e-16** |

A domain-level "marginal at 0.05" becomes a row-level "p ~ 1e-06". **Any p in this phase that is
not computed with the domain as the unit is wrong by roughly five orders of magnitude and must be
treated as retracted on sight.**

### 4c. An ICC that is measured, not assumed — from the raw prompts

The ICC above is inherited from the old, unaligned corpora. Here is one measured directly on the
new banks' flagship cell (one-way ANOVA over 116 domains, 60 rows per domain, 6960 rows, both
codewords, all three concepts):

| feature | n_domains | n_rows/domain | MS_between | MS_within | **ICC** |
|---|---|---|---|---|---|
| `n_chars` | 116 | 60 | 287047.81 | 708.57 | **0.8707** |
| `n_target_occurrences` | 116 | 60 | 0.0 | 0.0 | *constant across all 6960 rows — ICC undefined* |
| `n_preamble_lines` | 116 | 60 | 0.0 | 0.0 | *constant across all 6960 rows — ICC undefined* |
| `n_demos_emitted` | 116 | 60 | 0.0 | 0.0 | *constant across all 6960 rows — ICC undefined* |

**87.1% of the prompt-length variance in the flagship cell is between-domain.** This is not the ICC
of the neural readout — that is **UNKNOWN** before extraction and would need the residual-stream
states to measure — but it bounds the problem from the input side: the stimuli in this cell are
domain-locked, and three of the four structural counters are literally constant, so *nothing* in
the prompt structure distinguishes the 10 rows of a (domain, concept) group except the
demonstration slot and the dev/heldout sentence cut. **Expect the readout ICC to be at least as
high as the 0.088 inherited estimate and plausibly much higher; 0.088 is the optimistic end.**
The FPR simulation in §6 is therefore run with a strong (domain, concept) group random effect
rather than with iid rows.

**What would resolve the UNKNOWN:** one small extraction of residual-stream states for the
flagship cell on the 70 TRAIN domains only, followed by a one-way ANOVA of the per-row probe margin
across domains. That is a train-only measurement and costs no test-set exposure.

---

## 5. The secondary estimands, more briefly

### 5a. Diff-in-means AUROC

Per-domain AUROC standard error (Hanley–McNeil), with 10 rows per class per domain (one codeword)
and 20 (both):

| true AUROC | SE, 10 vs 10 (1 codeword) | SE, 20 vs 20 (2 codewords) |
|---|---|---|
| 0.60 | 0.1291 | 0.0902 |
| 0.70 | 0.1193 | 0.0833 |
| 0.80 | 0.1020 | 0.0710 |
| 0.90 | 0.0740 | 0.0514 |

A *single domain's* AUROC is nearly uninformative (SE ~0.10 at a true 0.80). The estimand must be
the **mean over 23 test domains**, tested against 0.5 with the same domain-level machinery. MDE for
the domain-mean AUROC at n=23, power 0.80:

| SD of per-domain AUROC | detectable mean AUROC |
|---|---|
| 0.05 | 0.531 |
| 0.08 | 0.549 |
| 0.10 | 0.561 |
| 0.15 | 0.592 |
| 0.20 | 0.622 |

**Use both codewords for this estimand** — it cuts the per-domain SE by ~30% at no additional GPU
cost beyond the second bank's forward passes.

### 5b. Causal patching (paired, per-domain, 23 test domains)

Estimand: per-domain paired difference (patched minus clean), tested with a paired t / Wilcoxon
signed-rank at n=23.

| n | MDE in units of the paired-difference SD (= Cohen's dz) |
|---|---|
| 6 | 1.435 |
| 12 | 0.889 |
| **23** | **0.611** |
| 29 | 0.539 |
| 38 | 0.467 |
| 58 | 0.374 |
| 116 | 0.262 |

**At n = 23 the patch must move per-domain accuracy by at least 0.611 SD of the paired
difference.** In accuracy units: 0.061 if the paired SD is 0.10, **0.092 if it is 0.15**, 0.122 if
it is 0.20. A full concept swap should clear this by a wide margin; a *partial mediation* of, say,
30% of a 0.415 effect (0.125) clears it only if the paired SD stays below 0.204.
**⚠ This is the estimand most at risk at n=23** — a partial-mediation result is exactly the kind
of thing 23 domains can leave ambiguous. Pre-register the paired SD you expect, and if the
patching arm is the scientific priority, that is the argument for 58/29/29, not the concept probe.

Wilcoxon signed-rank two-sided floor: n=6 → 0.03125; n=12 → 4.883e-04; **n=23 → 2.384e-07**;
n=38 → 7.276e-12. Not a binding constraint at n=23.

---

## 6. False-positive calibration on pure noise (the full pipeline)

**Simulation.** 116 domains x 3 concepts x 10 rows. Features are pure noise carrying (i) a domain
random effect shared by every row of a domain at every layer and (ii) a (layer, domain, concept)
group random effect — the real nuisance structure, since all 10 rows of one concept in one domain
share a demonstration pool. **No concept signal exists anywhere.** The pipeline is the real one:
standardize on train, multinomial logistic on 70 TRAIN domains, select over a **36-candidate**
grid (12 layers x 3 values of C), evaluate the mean per-domain accuracy on 23 TEST domains, and
compute the group permutation p (relabel the 3 concept groups within each test domain, B=200,
`p = (1+#{>=obs})/(B+1)`). 300 replicates. Both arms are scored from the *same* fitted candidates,
so the comparison is paired.

| arm | selection set | perm unit | n_test | reps | rejections | **FPR at nominal 0.05** | Clopper–Pearson 95% CI | covers 0.05? |
|---|---|---|---|---|---|---|---|---|
| **A (the design)** | **VALIDATION** | group | 23 | 300 | 14/300 | **0.0467** | **[0.0257, 0.0771]** | **YES** |
| B (malpractice) | **TEST** | group | 23 | 300 | 133/300 | **0.4433** | [0.3863, 0.5015] | NO |
| C (diagnostic) | VALIDATION | **row** | 23 | 100 | 20/100 | **0.2000** | [0.1267, 0.2918] | NO |
| D (diagnostic) | VALIDATION | group | **6** | 100 | 6/100 | 0.0600 | [0.0223, 0.1260] | YES |

**Findings.**

1. **Selecting hyperparameters on VALIDATION is calibrated.** FPR 0.0467, CI [0.0257, 0.0771],
   median p 0.4900, null mean accuracy 0.3331 against a chance of 0.3333. The 70/23/23 discipline
   in the manifest does exactly what it claims.
2. **Selecting on TEST inflates the FPR 9.5x** — 0.4433 against 0.0467, with the null mean
   accuracy pushed from 0.3331 to 0.3893 by selection alone. The previous phase measured 3–5x;
   this simulation measures **9.5x** because the selection grid here is 36 candidates
   (12 layers x 3 C) rather than a handful. **The inflation scales with the size of the selection
   space, so "we only picked a layer" is not a defence.** Almost half of all pure-noise runs would
   have produced a publishable p.
3. **Permuting ROWS instead of GROUPS inflates the FPR 4.3x** (0.2000 vs 0.0467) even with the
   accuracy still aggregated per domain. This is the §4 ICC point demonstrated end-to-end: the
   group permutation is load-bearing, not a stylistic choice.
4. **n_test = 6 was never an FPR problem** (0.0600, CI [0.0223, 0.1260], covers nominal). The old
   6-domain design was *calibrated* and *underpowered-in-resolution*. Its defect was that a p could
   not go below 1/201 and a sign test could not go below 0.031 — not that it lied about its
   type-I rate. This distinction matters for how the old results should be described.
5. The realised probability that a null test domain lands strictly above chance is **0.4352**
   (arm A), not 0.5 — the calibration number for §1a's sign test.

---

## 7. The falsifiability harness

`python scripts/dcs_ts_power.py --selftest` runs six checks, each of which (i) raises `ZeroBinding`
rather than passing if it binds to an empty set, (ii) re-derives from raw bank rows or raw
per-domain accuracies rather than from a producer-written summary field, and (iii) is demonstrated
to go RED under a named deliberate mutation.

| check | baseline | mutation | result under mutation |
|---|---|---|---|
| `K1 flagship_binding` — 6 banks x (1160 rows, 116 domains, 10/domain) | GREEN | `M_CELL`: select the cell with the long-form `natural_doublespeak` string | **RED** — `ZeroBinding: CHECK BOUND TO ZERO ROWS: flagship cell button_bomb` |
| `K2 perm_floor_is_1_over_Bplus1` — an unbeatable observation returns exactly `1/(B+1)` at B in {200,1000,2000,10000} | GREEN | `M_NAIVEP`: estimator `#{>=obs}/B` | **RED** — floor becomes 0 at every B |
| `K3 sign_floor_matches_bruteforce` — floor matches exhaustive enumeration of all 2^n sign patterns at n in {6,12,20}, and floor(6) > 0.005 | GREEN | `M_ONESIDED`: report the one-sided floor | **RED** — 0.015625 vs bruteforce 0.03125 |
| `K4 mde_delivers_80pct_power` — the analytic MDE at n=23, SD=0.10 achieves 0.80 in 4000 simulated draws | GREEN (MDE 0.06113, simulated power 0.7895) | `M_NOBETA`: MDE drops the type-II term | **RED** — MDE 0.04324, simulated power 0.5045 |
| `K5 icc_positive_and_deff_gt_1` | GREEN (icc 0.088416, DEFF 6.2165, n_eff 222.0 of N=1380) | `M_NOICC`: force ICC = 0 | **RED** — DEFF 1.0000, n_eff 1380.0 |
| `K6 pipeline_fpr_covers_nominal_0.05` (120 reps) | GREEN (FPR 0.0500, CI [0.0186, 0.1057]) | `M_TESTSEL`: select on TEST | **RED** — FPR 0.4667, CI [0.3751, 0.5599] |
| `K6` (same check) | GREEN | `M_ROWPERM`: row-level permutation null | **RED** — FPR 0.2167, CI [0.1467, 0.3011] |

`SELFTEST VERDICT: PASS — every check is falsifiable.`

---

## 8. RECOMMENDATION

### Is the flagship test adequately powered at 70/23/23?

# YES — keep 70/23/23. Do not change the split.

At the headline SD (0.1514, projected for 30 test rows per domain from the only per-domain
accuracies in the record) the design detects a true mean accuracy of **0.426** with power 0.80 at
alpha 0.05, and the effect it is chasing was **0.7485**. The margin is **4.5x**. A halved effect
(0.541) is detected with power 1.000; a quartered effect (0.437) with power 0.87. Under the
distribution-free bound (SD <= 1/3, assuming nothing) the MDE is still only 0.537 and the old
effect is detected at power 1.000. Reallocating to 58/29/29 buys an MDE improvement from 0.0925 to
0.0816 — **11.8%** — at the cost of 12 training domains, and does not change the answer for any
effect size that this experiment is plausibly about.

### The four rules that must ship with that YES

1. **`n_perm = 10000` for the flagship** (floor `9.999e-05`; MC relative SE at p=0.005 falls from
   99.7% to 14.1%). B=2000 is the floor for any secondary contrast. **Every permutation p in every
   artifact is published next to its floor `1/(B+1)`, and a zero-exceedance result is reported as
   `p < 1/(B+1)`, never as the floor's numeric value.** This is the single rule that prevents the
   `0.004975` incident from recurring; note it is a *reporting* rule, and no number of domains
   substitutes for it.
2. **The domain is the unit, everywhere, with no exceptions.** DEFF is **6.22** at 60 rows per
   domain; the design's 1380 test rows carry **222** independent observations. A row-level p of
   1.02e-06 is what an honest domain-level p of 0.05 looks like after the mistake. The permutation
   must relabel **groups** (concept x domain), not rows — row permutation was measured at
   FPR 0.200 against a nominal 0.05.
3. **Hyperparameters — layer, band, C, class-weight, readout position, threshold — are selected on
   the 23 VALIDATION domains and nowhere else.** Measured: validation-selection FPR 0.0467
   (CI [0.0257, 0.0771], calibrated); test-selection FPR 0.4433, a **9.5x** inflation. The
   inflation grows with the selection space, so restricting to "we only chose a layer" does not
   help. The `discipline` field already in `dcs_ts116_domain_split.json` says this; §6 is the
   measurement that makes it enforceable.
4. **Use BOTH codewords (button and basket) in the flagship.** It raises rows per domain from 30 to
   60, cuts the projected SD from 0.1514 to 0.1406, improves the MDE from 0.0925 to 0.0859 (7.1%),
   raises n_eff from 193.6 to 222.0, and converts the codeword from a fixed nuisance into a
   generalization axis at no extra domain cost. Report the two codewords separately as well as
   pooled — `P2_basket_lexical_transfer` at 0.6974 vs `P2_primary` at 0.7485 in the old record says
   the two codewords are not interchangeable.

### Additional instrument choices

5. **The group permutation is the flagship inferential instrument. The sign test is descriptive
   only** — its p0 = 0.5 does not match the measured null probability of 0.4352 that a domain lands
   strictly above chance at m=30. Report "k of 23 domains above chance" as a robustness statement
   (k >= 17 would be nominally significant at 0.05 on its own terms) and do not use it as the
   headline p.
6. **The `EXCLUDE_GLOBAL_RELABELS` conditioning is no longer load-bearing** at n=23 (degenerate
   mass 7.6e-18 for 3 classes, 2.4e-07 for 2 classes, versus 0.031 at n=6 with 2 classes, which is
   what contaminated the old 2-class contrasts). Keep it for continuity; state that it no longer
   affects any conclusion.
7. **`split` (dev/heldout) is a within-domain sentence cut and is NOT an independence unit.** All
   116/116 domains straddle it in every bank (580 dev / 580 heldout per bank in the flagship cell).
   Only `dsplit` from `be7d2c772d814ef3` may be used to define train/validation/test.

### The one condition under which this recommendation flips to 58/29/29

The between-domain SD is estimated from **six** domains (5 df); its 95% chi-square upper bound is
**0.3439**, at which the n=23 MDE degrades to **0.2102** (mean accuracy 0.543) and a halved effect
is detected with power 0.760 rather than 1.000.

> **TRIGGER — checkable on TRAIN domains only, before any test-set read.** After extraction, compute
> the per-domain probe accuracy across the **70 TRAIN domains** under nested leave-one-domain-out.
> If the observed between-domain SD there exceeds **0.25**, *or* the train-LODO mean accuracy is
> below **0.55**, the 23-domain test set is underpowered for the residual effect and the split
> should be rebuilt as **58/29/29** *before* the confirmatory run — which changes the MDE from
> 0.2102 to 0.1287 at SD=0.3439. Rebuilding the split after any test-set read is not a repair, it
> is a new experiment.

Changing the split is free **today** and impossible after extraction. The trigger above is the
mechanism that keeps that option open without spending the test set to decide.

### What this analysis does NOT license

- It says nothing about whether knife and gun **install**. The knife/gun demonstrations are
  bomb-demonstration text with the word swapped; if they install weakly, the effect size — not the
  power — is the binding constraint, and no allocation of 116 domains fixes that. A 3-way probe
  that separates bomb from a knife/gun pair that never installed would be measuring a two-class
  problem with a degenerate third class.
- The readout ICC is **UNKNOWN**. §4c measures only the stimulus-side ICC (`n_chars` = 0.8707) and
  §4a inherits 0.088 from the old unaligned corpora. If the true readout ICC is nearer the
  stimulus figure, DEFF at m=60 rises from 6.22 toward ~52 and n_eff falls from 222 toward ~27 —
  which would not change the domain-level analysis at all (that is the point of using the domain as
  the unit) but would make any row-level claim catastrophically wrong.
- The simulation in §6 calibrates the **pipeline**, not the extractor. It cannot detect a bug in
  the state extraction, a leaked prompt_id join (remember: button and basket share all 22272
  prompt_ids — join on `(bank_file_sha16, prompt_id)`), or a mislabeled concept column.

---

## 9. Assumptions, in one place

| # | assumption | value used | provenance | if wrong |
|---|---|---|---|---|
| A1 | between-domain SD of per-domain accuracy | 0.1290 (→ 0.1514 at m=30, 0.1406 at m=60) | derived from the 6 OLD per-domain accuracies in `dcs_bombness_specificity.json`, m=57 recovered from the common denominator | §3's SD=0.3439 table is the pessimistic case; §8's trigger is the mitigation |
| A2 | the old effect transfers to the aligned banks | mean 0.7485 (or 0.6974 for the second codeword) | OLD **unaligned** corpora — 948/1008 cell-C rows differed across concepts | the whole point of the new banks is that this may not hold; MDE, not power, is then the relevant number |
| A3 | ICC of the correctness indicator | 0.0884 | same 6 old domains | §4c argues this is the optimistic end; the domain-level analysis is insensitive to it |
| A4 | 3 concepts x 10 rows per domain in the flagship cell | 30 (or 60 with both codewords) | **MEASURED** on all six new banks (§0) | not an assumption |
| A5 | 70/23/23 domain split | `be7d2c772d814ef3` | **MEASURED** from the manifest (§0) | not an assumption |
| A6 | pure-noise features carry domain and (domain, concept) group effects | tau_domain 1.0, tau_group 1.2, 8 dims, 12 layers, 36-candidate grid | modelling choice in §6 | the validation arm is calibrated across the range tested (tau_group 0.0/0.7/1.2); the *magnitude* of the test-selection inflation depends on grid size, its *direction* does not |
