# Section 20 — results, bounds, and blockers

Consolidated write-up of the §20 "next sprint" items. Organised by **claim**, with the evidence
and the limits attached to each. Every number is quoted from an artifact under
`doublespeak_causality/outputs/`, not from the execution log.

Status legend: **ESTABLISHED** (replicated, statistically supported) · **BOUNDED** (null, with an
equivalence bound) · **BLOCKED** (cannot be executed as specified) · **RUNNING**.

---

## 1. The refusal coordinate is necessary for the continuous attack — in objective space (§20.1)

**ESTABLISHED (objective space only).** `asym_p201_ce_scores.json`.

Two soft-prompt objectives at matched budget (`free`, b=0.1), 3 seeds, same GPU class:
`task` minimises target CE; `task_orth` minimises CE **plus a penalty pinning the refusal
projection at its per-prompt baseline** (μ=1.0).

| seed | baseline CE | `task_orth` CE | `task` CE | orth progress | task progress |
|---|---|---|---|---|---|
| 42 | 2.6543 | 2.3038 | 0.6685 | 13.2 % | 74.8 % |
| 43 | 2.6578 | 2.4464 | 1.3153 | 8.0 % | 50.5 % |
| 44 | 2.6569 | 2.2096 | 1.4087 | 16.8 % | 47.0 % |
| **mean** | **2.6564** | **2.3200** | **1.1308** | **12.7 %** | **57.4 %** |

**Pinning the refusal projection costs 78.0 % of the achievable CE reduction, 3/3 sign-consistent
(smallest gap +0.80).**

Manipulation checks both pass: the pin holds the projection at Δproj = −0.026 mean (seed 42 is
*positive*), while plain `task` moves it **−3.087** as a pure side effect, never being in its
objective. For scale, §7.5's *mechanism* objective — which explicitly targets this coordinate with
discrete tokens — achieved only **−0.354**.

**Limits.** μ=1.0 is one point on a trade-off curve and the pin binds hard, so 78 % is the cost of
a *near-total* pin, not of the coordinate as such. A μ sweep is owed.

## 2. That necessity does **not** transfer to behaviour (§20.1 follow-up)

**BOUNDED.** `asym_p201_softprompt_asr.json`. 222 generations judged; 0 empty, 0 judge failures,
`judge_model` = gpt-4o-mini on all 222.

| seed | n | b (task>orth) | c (orth>task) | ΔASR | McNemar p | Wilcoxon p | 90 % CI |
|---|---|---|---|---|---|---|---|
| 42 | 37 | 9 | 4 | +0.135 | 0.267 | 0.118 | [−0.027, +0.297] |
| 43 | 37 | 3 | 4 | −0.027 | 1.000 | 0.293 | [−0.135, +0.081] |
| 44 | 37 | 5 | 1 | +0.108 | 0.219 | 0.161 | [+0.000, +0.216] |

**2/3 sign-consistent, 0/3 significant, every CI spans 0.** A 78 % change in what the optimizer
minimises produces a behavioural change we cannot distinguish from zero.

This is the program's central dissociation one level down: **objective vs behaviour**, not
representation vs behaviour. §20.1 must not be cited as a behavioural result.

## 3. Per-prompt mediation: the projection drop does predict success — where it isn't optimized (§20.2)

**ESTABLISHED, with a caveat on n.**

| slice | partial r(success, drop \| baseline) | n | p | 95 % CI |
|---|---|---|---|---|
| mechanism + random (**optimized toward v**) | −0.066 | 222 | 0.332 | [−0.196, +0.067] |
| **vanilla (never optimized toward v)** | **−0.291** | 74 | **0.012** | [−0.489, −0.066] |

In the unconfounded arm, more refusal suppression → more jailbreak. The optimized arms show
nothing because conditioning on the optimizer's success restricts the range — the pre-registered
rank-1 risk, which is why the vanilla slice existed. The two CIs overlap, so the claim is **not**
"optimization destroys the association"; it is that the vanilla estimate is the unconfounded one
and is non-null.

Baseline projection remains the strongest single predictor (r = −0.326, p = 0.0046); final
projection r = −0.421, p = 1.9e-4.

### 3b. The mediation is MODALITY-SPECIFIC — it does not hold for continuous attacks

The §20.1 soft-prompt `task` arms share §20.2's causal structure exactly (optimized for compliance
only; projection moves as a side effect), giving a free replication in another modality:

| slice | partial r(success, drop \| baseline) | n | 95 % CI |
|---|---|---|---|
| **discrete GCG, vanilla** (§20.2) | **−0.291** | 74 | [−0.489, −0.066] |
| **continuous soft `task`** | **−0.008** | 111 | [−0.195, +0.180] |
| continuous soft `task_orth` | −0.170 | 111 | [−0.346, +0.018] |

**It does not replicate**, and at n=111 the soft arm *excludes* an effect as strong as the discrete
one — despite a larger drop range (−6.64 → +1.48 vs −4.87 → +0.67).

A saturating dose-response was hypothesised (soft prompts move the coordinate ~2× further: mean
−3.09 vs ≈−1.4) and tested by stratifying: at drop > −2 (n=30, mean −0.54) partial r = **+0.041**.
**Unsupported, but not falsified** — that CI is [−0.331, +0.401] and does not exclude −0.291.
Underpowered; saturation remains open.

**Well-powered side finding.** `task_orth` gives **r(success, baseline) = −0.512, p = 9.6e-09**:
when the attack cannot move the refusal coordinate, intrinsic prompt refusal propensity dominates
outcomes. In the unpinned `task` arm the same correlation is **−0.037 (p = 0.70)** — a −3.09 move
washes baseline out completely. This is a *behavioural* demonstration that the pin works, which
§2's ASR contrast (0/3 significant) could not provide.

**Synthesis of 1–3.** The refusal coordinate is **necessary** for the attack but **useless as an
optimization target**: plain task optimization already moves it −3.09 for free, ~9× further than
the discrete mechanism objective ever managed, so a direction term has nothing left to add. That
reconciles §20.1, §20.2 and §7.5/Gate D without any of them being wrong.

## 4. Judge reliability — the 5.4 % figure is superseded (§20.3)

**ESTABLISHED.** `asym_p203_judge_replicates.json`, M=5, 665 calls (15× cheaper than full-corpus).

| group | n | flipped | flip rate | mean score SD |
|---|---|---|---|---|
| intermediate band | 93 | 33 | **35.48 %** | 0.1047 |
| **extreme control** | 40 | **0** | **0.00 %** | 0.0023 |

Rows pinned at 0.0/1.0 are effectively deterministic (0/40, SD 0.0023), which **validates** the
band-only design rather than assuming it. *Prior art:* the `baseline_drift` runs already used
majority-vote judging and recorded per-condition flip rates; what is new here is the **band-only
targeting** and the **extreme-row control**, not replicate judging as such. Those runs also
locate the likely provenance of the 5.4 % figure — the `benign` condition alone shows 5.55 %, and
it is the condition whose ASR sits closest to 0.5. Corpus-level two-pass disagreement ≈ **0.62 %**, not
5.4 %; the sprint's cited figure was one arm at n=37 and is not a constant. The judge runs at
`temperature=0`.

**Variance decomposition of a single-pass arm ASR at n=37, p = 0.2107 (measured pooled ASR):**

| source | SD | share |
|---|---|---|
| sampling (prompt-to-prompt) | **0.0670** | 92.5–98.2 % |
| judge (typical / worst case) | 0.0091 / 0.0191 | 1.8 / 7.5 % |

**Sampling dominates judge noise by 3.5–7.4×.** Judge noise is real, secondary, and cheaply removable
(majority-vote over M=5 on the 4.65 % band).

**That removal was carried out, not just asserted** (`asym_p203_denoised_contrasts.json`). The
replicate run covers every band row (93/93, 0 missing) and extremes are validated deterministic, so
a fully denoised endpoint required no new API calls. Re-running all 18 §7.5 contrasts:

| | result |
|---|---|
| ΔASR moved | **7/18** (mean 0.031, max **0.054** = exactly 2 rows of 37) |
| significance flipped | **0/18** |

Every shift is an exact multiple of 1/37, confirming denoising flips whole rows rather than
smearing scores. **Caveat that limits the claim:** all 18 contrasts are null under both endpoints,
so "0 flips" was near-guaranteed — this demonstrates robustness *of nulls* only. A contrast near
threshold could be moved across by a 2-row shift. Practical consequence: individual ΔASR values
carry ~±0.05 of judge-attributable uncertainty *on top of* sampling — 54 % of the whole Doublespeak
effect — so they should not be quoted to three decimals.

## 5. Every behavioural negative is bounded at ~±0.2 ASR (§20.4)

**BOUNDED — provisional.** `asym_p204_equivalence.json`. 90 % CI = TOST region at α=0.05, paired
bootstrap over items.

| budget | contrast | mean Δ | equivalence bound |
|---|---|---|---|
| low | mechanism − matched random | +0.054 | 0.189 |
| low | mechanism − vanilla | +0.036 | 0.216 |
| low | matched random − vanilla | −0.018 | 0.189 |
| full | mechanism − matched random | +0.009 | 0.189 |
| full | mechanism − vanilla | −0.054 | **0.270** |
| full | matched random − vanilla | −0.063 | 0.216 |

These nulls rule out **only effects larger than ~0.19–0.27 ASR**. For scale, the **Doublespeak
effect itself is +0.100 ASR** (test split, majority-vote, n=30: doublespeak 0.800 vs direct 0.700 —
`baseline_drift_clearharm_…_741427/summary.json`). So the bounds are **1.9–2.7× the size of the
phenomenon the paper is about**: our behavioural nulls cannot exclude an effect two to three times
larger than Doublespeak. Every "no effect" in the write-up must read "no effect larger than ~0.2
ASR detectable at this n".

*Validation:* all 18 arm × seed ASR cells reproduce the §7.5 published table to 4 dp through an
independent code path.

## 6. §20.8 is BLOCKED, and no endpoint change fixes it

**BLOCKED.** Corpus ceiling is **179** (`data/clearharm/clearharm_179.csv`); the manifest already
uses 148 (dev 37 / train 74 / test 37). Keeping a disjoint 40-item train pool leaves **≈139**
held-out — not the 300 the plan assumes.

Paired McNemar power (α=.05, ρ=.5, 4000 sims):

| n | Δ=0.054 | Δ=0.10 | Δ=0.15 |
|---|---|---|---|
| 37 (current) | **0.05** | 0.15 | 0.30 |
| 139 (ceiling) | 0.29 | 0.64 | 0.92 |
| 300 (planned) | 0.62 | 0.95 | 1.00 |

At n=37, power against the effect §7.5 reports is **0.05 — the false-positive rate.**

**The graded endpoint does not rescue it** (`asym_p208_endpoint_compare.json`, same rows/pairing/
bootstrap, all 18 contrasts):

| endpoint | significant at .05 | mean 90 % CI width (SD units) |
|---|---|---|
| binary ASR | 0/18 | 0.598 |
| graded score | 0/18 | 0.585 |

Only **2.2 % tighter** → variance ratio 0.957 → **effective n multiplier 1.04×**. The graded
endpoint buys essentially nothing. Expected, because 92.7 % of rows sit at exactly 0.0/1.0, so the
graded score is very nearly the binary one.

*(An earlier version of this table reported 1.34×. That standardized the binary width by an
**assumed** binomial SD at p=0.15 while standardizing the graded width by its **empirical** SD.
The measured pooled ASR is 0.2107, giving an empirical binary SD of 0.405, not 0.357 — the
mismatch flattered the graded endpoint. Both are now divided by their own empirical pooled SD.)*

**Resolution.** Report behavioural results as **equivalence bounds, not point estimates**, and stop
describing 0/18-significant contrasts as findings in either direction. Only a second corpus buys
real behavioural power, at the cost of comparability plus its own templating and
direction-validation gate. **§20.6 and §20.4-pass-2 are blocked by the corpus, not the endpoint.**

## 7. Compute is the dominant effect, and the direction term buys ≤23 % of it (§20.7)

**ESTABLISHED (objective space).** `asym_p207_objective_curve.json`, `asym_p207_arm_contrasts.json`.

§7.5's central negative — the mechanism/direction term buys nothing — was measured on binary ASR
at **0.05 power**, an uninformative null. Re-asked on the optimization objective (best-so-far GCG
task loss; continuous, paired per-prompt, judge-free), at full n=37.

**The endpoint's sensitivity is demonstrated, not assumed.** Across all 9 arm × seed cells,
5 → 200 steps gives:

| arm | mean Δ | prompts improved | p |
|---|---|---|---|
| vanilla | −0.946 | 37/37, 36/37, 37/37 | 1.1e-07 ×2, 1.7e-07 |
| mechanism | −0.957 | 37/37 all seeds | 1.1e-07 |
| matched_random | −0.965 | 37/37 all seeds | 1.1e-07 |

**On that endpoint, 0 of 18 arm contrasts are significant** (9 at 5 steps, 9 at 200), and they are
*bounded*, not merely non-significant (paired bootstrap, 200 steps):

| contrast | worst bound (loss units) | as % of compute effect |
|---|---|---|
| mechanism − vanilla | 0.2151 | **22.7 %** |
| mechanism − matched_random | 0.1618 | 17.1 % |

> Any benefit from the direction term is at most ~23 % of what plain compute buys — on an endpoint
> that detects the compute effect at p = 1.1e-07.

This is the §20 result that most improves the paper: it converts the program's weakest claim from
*"we found nothing, with 5 % power"* into *"we found nothing, on an endpoint able to find something
4× smaller than what we sought."* §20.4's ±0.19–0.27 ASR bounds could not support that.

**Scaling beyond 200 steps — seed 42 is now FINAL at 37/37 and the 200→600 gain is NULL.**
`asym_p207_objective_curve_seed42_FINAL37.json` (`interim: false`, `n_paired: 37`).

| contrast | mean Δ | improved | p |
|---|---|---|---|
| 5 → 200 | **−0.9645** | **37/37** | **1.14e-07** |
| 5 → 600 | −1.0368 | 37/37 | 1.14e-07 |
| **200 → 600** | **−0.0723** | **22/37** | **0.252** |

Tripling the budget past 200 steps buys **no detectable objective-space gain**, on the same
endpoint and the same 37 prompts where 5→200 lands at p = 1.1e-07. This is the single
pre-committed read: the estimate was watched oscillate (−0.079 at n=14 → −0.122 at n=18 → −0.062
interim) and deliberately not re-read until full coverage, so it is reported once, here.

**The 2000-step point is descoped** — but on *seed 42 only*, and the decision is held one more
tick, because seed 43's **interim** 20/37 slice points the other way (−0.197, 14/20, p = 0.026).
That slice is not a random subsample (completion order tracks per-prompt optimization cost), which
is exactly the bias that made the earlier interim reads unstable, so it must not be scored until
37/37. Seed 43 has all four shards running; the call is cheap to defer and expensive to get wrong.

**Do not quote** the log-linear extrapolation (0.706 at 2000 steps): the completed seed now
*contradicts* it — the fit is dominated by the 5→200 jump, and the measured 200→600 segment is
flat where the fit predicts continued descent.

**Status.** 57/74 prompts (seed 42 **37/37 FINAL**, seed 43 20/37, all 4 shards running). Seed 44
is a separate curve point at 0/37 with shards 0–2 launched, 3 owed. All completed runs verified:
600/600 steps, `n_train_tasks == 1`.

**Caveat.** Objective space only. Per §2 this licenses **no** behavioural claim.

---

## What §20 changes about the paper

1. **A necessity/usefulness distinction the program was conflating.** The refusal coordinate is
   necessary for the continuous attack yet useless as an optimization target. This reconciles the
   mechanism-targeting negatives with the mediation result instead of leaving them in tension.
   The mediation is further **modality-specific** (§3b): it holds for discrete suffixes and is
   excluded at n=111 for continuous soft prompts, consistent with the coordinate acting as a
   **gate** rather than a dose — though the stratified test lacks power to establish that.
2. **The objective-vs-behaviour dissociation**, distinct from representation-vs-behaviour: a 78 %
   change in the optimized quantity yields an unmeasurable behavioural change.
3. **Every behavioural negative must be restated as a bound** (~±0.2 ASR), because at n=37 the
   design has 0.05 power against its own reported effect size.
4. **Two methodological figures are corrected:** the 5.4 % judge-flip rate (actually ~0.6 % corpus
   two-pass, confined to a 4.65 % boundary band) and the assumption that a graded endpoint would
   restore power (actually 1.04×).
5. **A powered null replaces an uninformative one.** The direction term's uselessness is now
   bounded at ≤23 % of the compute effect on a demonstrably sensitive endpoint, rather than resting
   on a binary-ASR contrast with 0.05 power. Where the behavioural question cannot be answered at
   this corpus size, the objective-space question can be — and the two must be reported as
   different claims (§2).
