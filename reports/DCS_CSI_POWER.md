# DCS-CSI POWER — domain-unit power / MDE for the behavioural (refusal) endpoint

**Question.** How many DOMAINS must a future experiment bank contain before the
exact sign-flip test on the native-refusal endpoint has 80% power?

**Producer.** `scripts/dcs_csi_power.py` (seed 20260915, alpha=0.05 two-sided,
4000 simulated experiments per cell). Machine-readable: `reports/DCS_CSI_POWER.json`.
Inputs: `reports/DCS_CSI_REDERIVE_PATCH_button.json`,
`reports/DCS_CSI_REDERIVE_PATCH_basket.json`, `reports/DCS_CONT_LINKING_POWER.json`.
Pure CPU; the whole analysis runs in ~16 s on the login node.

---

## 0. The unit, the test, and why the test is exact here

* The independence unit is the **DOMAIN**, not the row: D=90 domains, R=2 rows
  per domain, 180 rows. A domain's arm score is its within-domain refusal rate,
  an element of {0.0, 0.5, 1.0}.
* Arms are **paired by domain** — every domain appears in every arm.
* The confirmatory test is an **exact two-sided sign-flip randomisation test**
  over the paired domain differences. With **k** informative (nonzero-difference)
  domains the smallest attainable two-sided p is **2 / 2^k**. A design therefore
  needs enough *informative* domains, not merely enough domains.
* Because R=2, every difference is a multiple of 0.5 in [-1, 1]. Writing the
  statistic in half-units, the sign-flip null is the convolution of k1 Rademacher
  variables (from |d|=0.5 domains) and k2 doubled Rademacher variables (from
  |d|=1 domains) — a product of two binomial pmfs. So the exact p-value is
  computed **in closed form for any k**. Nothing in this report uses a normal
  approximation to the test; the Monte Carlo is only over *simulated experiments*.

---

## 1. The observed per-domain refusal-rate distribution (button, 90 domains)

| arm | rate 0.0 | rate 0.5 | rate 1.0 | domains with any refusal | refusal rows | domain-mean rate |
|---|---|---|---|---|---|---|
| ctrl          | 72 | 16 | 2 | 18 | 20 | 0.11111 |
| ko            | 84 |  4 | 2 |  6 |  8 | 0.04444 |
| rescue_clean  | 79 |  9 | 2 | 11 | 13 | 0.07222 |
| sizematch     | 81 |  7 | 2 |  9 | 11 | 0.06111 |

Three structural facts dominate everything below:

1. **The endpoint is rare.** 80% of domains are at 0.0 even in the most
   refusal-prone arm, so most domains carry no information about any contrast.
2. **The refusing sets are perfectly NESTED**: `ko ⊂ sizematch ⊂ rescue_clean ⊂ ctrl`
   at the domain level (verified: every ko-refusing domain also refuses in ctrl,
   rescue_clean and sizematch). This is what makes the paired design pay: under
   cross-arm independence the expected ctrl∩ko overlap would be ~1.2 domains;
   the observed overlap is 6, i.e. all of them.
3. **Two domains refuse at rate 1.0 in every single arm** — immovable refusers.
   They are permanently tied and can never be informative for any contrast, at
   any bank size. Roughly 2/90 of any future bank is dead weight for this test.

### Observed contrasts

| contrast | point (domain-mean) | k informative | n+ / n− / tied | attainable p-floor 2/2^k | exact p |
|---|---|---|---|---|---|
| ctrl − ko (KO de-refusal)        | 0.06667 | 12 | 12 / 0 / 78 | 0.000488 | **0.000488** |
| rescue_clean − ko (recovery)     | 0.02778 |  5 |  5 / 0 / 85 | 0.0625   | 0.0625 |
| sizematch − ko                   | 0.01667 |  3 |  3 / 0 / 87 | 0.25     | 0.25 |

Note the pathology this table exposes: **the recovery contrast and the sizematch
contrast are already at their p-floor.** Their observed p-values are not
"non-significant because the effect was small" — they are non-significant because
with k=5 and k=3 informative domains *no possible data pattern* could have
produced p ≤ 0.05. The experiment was structurally incapable of the verdict.

---

## 2–3. Power curve (alpha=0.05), expected informative k, and structural incapability

Model A (primary) resamples D domains **with replacement** from the 90 observed
joint (ctrl, ko, rescue_clean, sizematch) domain vectors, preserving the marginal
distribution, the nesting, and the immovable domains without modelling them.
"P(structurally incapable)" = P(2/2^k > 0.05) = P(k ≤ 5).

**KO de-refusal (ctrl − ko), true effect 0.0667**

| D | power | E[k] | P(structurally incapable) |
|---|---|---|---|
| 90   | 0.984 | 12.0 | 0.016 |
| 120  | 0.999 | 15.9 | 0.001 |
| 150  | 1.000 | 20.1 | 0.000 |
| 200  | 1.000 | 26.7 | 0.000 |
| 250  | 1.000 | 33.2 | 0.000 |
| 300  | 1.000 | 39.9 | 0.000 |
| 400–1000 | 1.000 | 53.4–133.1 | 0.000 |

**Recovery (rescue_clean − ko), true effect 0.0278**

| D | power | E[k] | P(structurally incapable) |
|---|---|---|---|
| 90   | 0.393 |  5.1 | **0.608** |
| 120  | 0.658 |  6.6 | 0.343 |
| 150  | 0.854 |  8.4 | 0.146 |
| 200  | 0.973 | 11.2 | 0.028 |
| 250  | 0.995 | 13.9 | 0.005 |
| 300  | 1.000 | 16.6 | 0.000 |
| 400–1000 | 1.000 | 22.3–55.7 | 0.000 |

**Size-match control (sizematch − ko), true effect 0.0167**

| D | power | E[k] | P(structurally incapable) |
|---|---|---|---|
| 90   | 0.084 |  3.0 | **0.916** |
| 150  | 0.371 |  4.9 | 0.629 |
| 200  | 0.663 |  6.7 | 0.338 |
| 250  | 0.835 |  8.3 | 0.165 |
| 300  | 0.936 | 10.0 | 0.064 |
| 500  | 0.999 | 16.6 | 0.001 |
| 1000 | 1.000 | 33.4 | 0.000 |

The single most actionable number in this report: **at the current D=90, a
recovery-style experiment has a 61% chance of being structurally incapable of
significance before a single token is generated**, and a sizematch-style contrast
a 92% chance. That failure mode is invisible in a p-value and is not fixed by
better modelling — only by more informative domains.

Model B (latent-Gaussian threshold model, see §8) reproduces these curves closely
(KO: 0.972 at D=90 vs 0.984; recovery: 0.369 vs 0.393), and reproduces the
observed k at D=90 (11.2 vs 12 for KO; 4.9 vs 5 for recovery) and the observed
effects (0.0664 vs 0.0667; 0.0274 vs 0.0278). The two models are not independent
evidence — B is calibrated to the same 90 domains — but their agreement shows the
answer is not an artefact of the bootstrap's discreteness.

---

## 4. Minimum D for 80% power

| effect | Model A (bootstrap) | Model B (latent) | power at today's D=90 |
|---|---|---|---|
| **(a) KO de-refusal (ctrl − ko)** | **D = 59** | D = 63 | 0.98 |
| **(b) Recovery (rescue_clean − ko)** | **D = 143** | D = 147 | 0.39 |
| (c) Size-match control (sizematch − ko) | D = 237 | — | 0.08 |

**Headline: ~60 domains for the KO de-refusal effect; ~150 domains for the
rescue-vs-KO recovery effect** (and ~240 if you want the size-match control to
be able to speak). The current bank of 90 is comfortably powered for (a) and
badly underpowered for (b).

### 4b. Do not read D=59 as "we could have used half the bank"

D=59 and D=143 are computed **at the observed point estimate**, which is the
classic observed-power trap. Repeating the calculation with the true effect set
to each end of the published bootstrap CI:

| effect assumed true | KO de-refusal | Recovery |
|---|---|---|
| CI95 lower  | 0.0333 → **D = 121** | 0.00556 → **D = 710** |
| point       | 0.0667 → D = 61      | 0.0278 → D = 149 |
| CI95 upper  | 0.100  → D = 45      | 0.0556 → D = 76 |

**Plan to the CI lower bound, not the point estimate.** A bank sized to guarantee
the KO effect under the pessimistic end needs ~120 domains; a bank that
guarantees the recovery effect under the pessimistic end needs ~700 and is not a
realistic target — at that end, headroom (§6), not sample size, is the only
affordable lever.

---

## 5. Minimum detectable effect (MDE), power 0.80

Base arm held at the observed ctrl rate 0.1111; effect expressed in
domain-mean refusal-rate units (with R=2 and equal weights this equals row-mean
refusal-rate units).

| D | MDE (domain-mean rate) | as fraction of the 0.111 base rate | latent threshold shift |
|---|---|---|---|
| 90  | **0.0455** | 41% of base | 0.288 |
| 180 | **0.0221** | 20% of base | 0.127 |
| 300 | **0.0134** | 12% of base | 0.074 |

Read this as: at today's D=90 you can only see effects that wipe out **at least
40% of the baseline refusal rate**. The KO de-refusal (0.0667 = 60% of base)
clears that bar; the recovery (0.0278 = 25% of base) does not, and the size-match
contrast (0.0167 = 15% of base) is far below it. Doubling to D=180 halves the
MDE; the MDE scales roughly as 1/D over this range, not 1/sqrt(D), because in
the rare-event regime the binding constraint is the *count* of informative
domains, which grows linearly in D.

---

## 6. Headroom vs domains — the trade-off

Sensitivity scenario: a codeword/bank chosen so the CTRL refusal rate is 2x or 3x
the observed 0.111, with the arm separations held fixed **on the latent scale**
(see assumption A4). Model B, power 0.80.

| scenario | ctrl rate | KO effect | min D (KO) | recovery effect | min D (recovery) | power at D=90 (recovery) |
|---|---|---|---|---|---|---|
| observed (x1) | 0.111 | 0.0667 | 61 | 0.0278 | **149** | 0.35 |
| **x2 headroom** | 0.222 | 0.1157 | 38 | 0.0513 | **80** | 0.90 |
| **x3 headroom** | 0.333 | 0.1523 | 28 | 0.0705 | **58** | 0.99 |

**The trade-off, plainly.** For the contrast that actually limits this project —
rescue-vs-KO recovery — **doubling the baseline refusal rate is worth about as
much as doubling the bank, and is roughly the same thing as cutting the required
D by 46% (149 → 80); tripling it cuts D by 61% (149 → 58).** Concretely:

* If you can find a codeword/bank with 2x headroom, the **existing 90 domains
  become adequately powered for the recovery effect** (0.90) with zero new GPU
  spend on data collection.
* If you cannot, you must roughly **double the bank to ~150 domains** to reach
  the same place, and ~240 domains if you also want the size-match control to be
  able to return a verdict rather than a p-floor.
* Headroom is the cheaper lever *and* the more robust one: it attacks the
  structural-incapability failure mode (§2–3) directly by converting tied domains
  into informative ones, whereas adding domains only buys informative domains at
  the observed rate of ~5.6% (recovery) per domain added.
* Caveat on how far this goes: headroom has diminishing returns because the
  latent-scale shift maps through a saturating Phi. It is a factor-of-2-to-3
  lever, not an order-of-magnitude one; it does not substitute for a bank of
  ~120+ domains if you need the KO effect guaranteed at its CI lower bound.

### The basket codeword is the worst case of exactly this

Basket has **1 movable refusal event in 180 rows** (ctrl 1 row / 1 domain, ko 0,
rescue_clean 1 row / 1 domain). k=1 for every contrast, so the attainable p-floor
is **1.0**: no D whatsoever makes the basket behavioural endpoint significant.
To reach even k≥6 in expectation (the minimum k at which p ≤ 0.05 is *attainable*
at all) you would need **D ≈ 540 domains** at the observed informative-domain
rate of 1.1%, and that only buys you the *possibility* of significance, not
power. **The basket arm is a headroom problem, not a sample-size problem, and
should not be costed as one.**

---

## 7. Reconciliation with `reports/DCS_CONT_LINKING_POWER.json` (the "~252")

**The numbers do not agree, and should not be expected to: they answer different
questions.** The prior file is not wrong.

| | DCS_CONT_LINKING_POWER | this analysis |
|---|---|---|
| endpoint | a continuous per-domain linking quantity | rare binary native refusal |
| estimator | Pearson r, Fisher-z (analytic + MC) | exact sign-flip randomisation over domain differences |
| effect | rho = 0.176 | 0.0667 (KO) / 0.0278 (recovery), domain-mean rate |
| effective information | all N domains contribute | only k informative domains contribute; 78/90 are tied |
| N available | 67 (knockout arms) | 90 |
| answer at 80% power | **N = 252** | **D = 59 (KO), 143 (recovery)** |

The gap is fully explained by three differences, in descending order of size:

1. **Different estimator and endpoint.** A correlation power calculation extracts
   information from every domain. The sign-flip test on a rare binary endpoint
   extracts information only from domains where the two arms actually disagree —
   here 12 of 90 (KO) and 5 of 90 (recovery). Same domain count, radically
   different effective N. The two "N needed" figures are not the same quantity.
2. **Different effect standardisation.** rho = 0.176 is a small standardised
   effect (r^2 ≈ 3% of variance). The KO de-refusal removes 60% of the baseline
   refusal rate and is, on its own scale, a large effect — hence a much smaller D.
3. **Different N base.** The linking analysis was limited to the 67 domains with
   usable continuous values in the knockout arms; the behavioural endpoint uses
   all 90.

**Practical reconciliation for planning.** Both analyses agree that the current
bank is on the wrong side of the 80% line *for their respective weakest target*,
and both land in the same order of magnitude, **10^2 domains**. A bank of
**~250–300 domains** would satisfy the linking requirement (252), the recovery
requirement (143), the size-match-control requirement (237), and the KO
requirement at its CI lower bound (121) simultaneously. If a single bank size has
to be chosen for a future sprint, **D ≈ 300** is the number that makes every
currently-known target powered; **D ≈ 150** is the minimum that unblocks the
recovery contrast alone.

---

## 8. Models, assumptions, and what would invalidate this

### Model A — empirical domain bootstrap (primary)
Resample D domains with replacement from the 90 observed joint domain vectors.
Assumption-light: it reproduces the marginals, the perfect nesting, and the
immovable domains for free.

### Model B — latent-Gaussian threshold model (needed for MDE and headroom)
Row (d,r) carries `x = sqrt(rho)*z_d + sqrt(1-rho)*u_{d,r}`, shared across arms;
arm a refuses that row iff `x > t_a`. Thresholds from the observed marginal row
rates: t_ctrl=1.2206, t_sizematch=1.5455, t_rescue=1.4594, t_ko=1.7013. The
domain intraclass correlation was grid-fitted to the observed per-arm counts of
(domains with ≥1 refusal) and (domains with 2 refusals): **rho = 0.45** (SSE 12.9).
Fit quality, predicted vs observed:

| arm | n_any pred / obs | n_both pred / obs |
|---|---|---|
| ctrl | 16.9 / 18 | 3.1 / 2 |
| ko | 7.2 / 6 | 0.8 / 2 |
| rescue_clean | 11.3 / 11 | 1.6 / 2 |
| sizematch | 9.7 / 9 | 1.3 / 2 |

### Assumptions, each with its failure mode

**A1 — Exchangeability.** Future domains are exchangeable with the 90 observed
ones (Model A) or drawn from the fitted latent law (Model B). *This is the biggest
assumption and it is not checkable from the present data.* The bootstrap can only
ever emit the 90 profiles that were measured, so **the simulation inherits their
idiosyncrasies wholesale** — including the particular 18 ctrl-refusing domains and
the particular 2 immovable ones. **Invalidated if** a scaled bank draws domains
from a different topical pool with a different baseline refusal propensity; the
D estimates would then be wrong in whichever direction the pool moves.

**A2 — R=2 rows per domain is fixed.** Adding rows *within* a domain is a
different lever and is not simulated. It would raise the resolution of each
domain's rate (breaking the {0, 0.5, 1} grid) and could convert some tied domains
into informative ones — plausibly cheaper than new domains. **Not costed here;
worth a follow-up.**

**A3 — Perfect nesting / no arm-specific noise (Model B only).** Arms are assumed
to differ only by a threshold shift on a shared latent. The observed data are
perfectly nested, which is *consistent with* but does not *prove* this. **If the
arms carried independent noise**, differences of both signs would appear, k would
rise but the statistic would be noisier; the net effect on D is not obviously
signed, and the sizematch/recovery D estimates would be the ones most affected.

**A4 — The headroom scenarios hold the LATENT separation fixed.** Multiplying the
ctrl rate by 2x/3x while holding `delta = t_ko − t_ctrl` constant says a
higher-baseline codeword moves the *same distance in latent units*. This is a
choice, and it is the favourable one. **If instead the probability-scale effect
stayed fixed** as the baseline rose, headroom would buy far less (the effect
would be a smaller fraction of a larger base and the D reductions in §6 would
largely evaporate). Treat §6 as an upper bound on what headroom buys.

**A5 — Single rho cannot fit both clustering statistics.** The model
under-predicts `n_both` for ko (0.8 vs 2) and over-predicts it for ctrl
(3.1 vs 2). The observed "2 domains at 1.0 in every arm" is more extreme
clustering than a one-parameter latent-Gaussian can express. **Consequence:**
Model B slightly understates the number of permanently-tied immovable domains,
so its D estimates are mildly optimistic. Model A does not have this problem,
and A and B agree to ~5%, which bounds the size of the discrepancy.

**A6 — alpha=0.05 two-sided, no multiplicity correction** across the several
contrasts a real sprint would run (KO, recovery, sizematch, plus per-bank
replications). **Correcting for multiplicity would raise every D in this report.**
At a Bonferroni-corrected alpha=0.0167 for three contrasts, the attainable
p-floor constraint alone requires k ≥ 7 rather than k ≥ 6.

**A7 — The refusal detector is treated as ground truth.** Detector agreement is
1.000 over 720 labels in this rederivation, so detector noise is not modelled.
**Invalidated if** a future bank uses a judge with the ~13% label-flip rate seen
elsewhere in this project; label noise attenuates the effect and would raise D
substantially.

**A8 — Power is computed for a *fixed* pre-registered contrast.** These numbers
do not license choosing the contrast after seeing the data.
