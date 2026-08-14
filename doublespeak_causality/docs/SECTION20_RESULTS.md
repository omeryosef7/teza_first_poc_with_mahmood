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

### 1b. The μ sweep is done, and the trade-off is sharply convex

**ESTABLISHED.** `asym_p201_ce_musweep.json` — 18 arms (5 μ values + free, × 3 seeds), every CE
number produced under a **single model load** as the scorer requires for a valid contrast. The
μ=1.0 anchor reproduces `asym_p201_ce_scores.json` exactly (`ce_progress_frac` 0.13206,
`dproj_test` 0.18678), so this table extends the published result rather than replacing it.

| μ | Δproj mean (sd) | suppressed | **CE cost** (sd) |
|---|---|---|---|
| 0.1 | −0.722 (0.189) | 76.5 % | **19.5 %** (37.9) |
| 0.3 | −0.328 (0.261) | 89.1 % | **34.5 %** (21.1) |
| **1.0** | −0.026 (0.192) | **99.0 %** | **76.9 %** (11.1) |
| 3.0 | −0.098 (0.139) | 96.6 % | **98.0 %** (0.9) |
| 10.0 | +0.001 (0.073) | 99.9 % | **100.7 %** (0.4) |

*(Suppression is measured against the free arm's 3-seed mean Δproj of −3.090. Cost is
1 − `ce_progress_frac`/free, per seed, then averaged.)*

**Three-quarters of the suppression is nearly free; the last percent costs everything.** 76.5 % of
the coordinate's free movement is removable for 19.5 % of the achievable CE reduction. Going from
there to 99 % costs 57 more points, and the final approach to a perfect pin consumes the rest —
at μ=10 the pinned prompt makes **no CE progress at all** (100.7 %, i.e. marginally worse than
baseline).

**Past μ=1 the penalty buys no additional suppression and destroys what CE progress remains.**
μ ∈ {1, 3, 10} hold the coordinate at −0.026, −0.098, +0.001 — mutually indistinguishable, and
μ=3 in fact suppresses *slightly less* than μ=1.0 — yet cost climbs 76.9 → 98.0 → 100.7 %. Paired
within seed, μ=3 and μ=10 are **0/3 cheaper** than μ=1.0 while μ=0.1 and μ=0.3 are **3/3 cheaper**.

**So the 78 % headline is the price of a near-total pin, and μ=1.0 sits at the knee of the curve** —
the limit stated below is now measured rather than conjectured. The coordinate as such is far
cheaper to suppress than that number suggests.

**Two caveats that belong with the numbers.** (i) The weak-μ end is *noisy*: sd 37.9 at μ=0.1,
including one seed at −8.6 % where the pinned run beat its own free arm. Penalty strength buys
reproducibility as well as tightness — sd falls monotonically 37.9 → 21.1 → 11.1 → 0.9 → 0.4.
(ii) Cost does **not** track achieved pin tightness across pooled runs (Spearman ρ = −0.50,
p = 0.14, n=10 at the time of testing); the claim rests on the μ-ordered means at n=3, not on that
correlation.

**Limits.** Objective space only, one budget (b=0.1), one parameterisation (`free`), one model.

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

### Scaling beyond 200 steps — the pre-registered 3-seed read (COMPLETE)

**All three seeds at 37/37; 111 runs verified 600/600 steps, `n_train_tasks == 1`, zero
violations.** `asym_p207_curve_200to600_3seed.json`, `asym_p207_curve_5to200_3seed.json`.

The statistic and the decision rule were fixed **before seeds 43/44 finished** (unit = the prompt,
per-seed deltas averaged before testing, so 3 × 37 paired diffs are not treated as 111 independent
units; the script hard-refuses to run below full coverage). Read once, here.

| contrast | seed 42 | seed 43 | seed 44 | **pooled (n=37 prompts)** |
|---|---|---|---|---|
| 5 → 200 | −0.9645 (p=1.1e-07) | −0.8825 (1.7e-07) | −0.9918 (1.1e-07) | **−0.9463, 37/37, p=1.5e-11** |
| **200 → 600** | −0.0723 (p=0.252) | −0.2224 (**0.0025**) | −0.0963 (0.071) | **−0.1303, 26/37, p=0.0023** |

**The 200→600 gain is real but small.** Pooled p = 0.0023 — so the earlier "null" reading from
seed 42 alone was underpowered, not correct. But only **1 of 3 seeds** reaches significance
individually, and the effect is **7.3× smaller** than the 5→200 jump measured on the same prompts.

### The 2000-step point is DESCOPED — 1 of 3 pre-registered criteria met
| # | criterion (fixed 2026-08-14, before the data) | result | verdict |
|---|---|---|---|
| 1 | pooled p < 0.05 | 0.0023 | **PASS** |
| 2 | ≥2/3 seeds individually significant and sign-consistent | 1/3 | **FAIL** |
| 3 | per-step efficiency within 10× of 5→200 | **14.9×** worse | **FAIL** |

Efficiency: 5→200 buys **0.004853** loss/step; 200→600 buys **0.000326**. The descope always
rested on efficiency rather than on "no further gain" — and the gain now demonstrably exists while
costing ~15× more per step. **Extending to 2000 steps is not justified**, and the reason is
sharper than a null would have been.

**Do not quote** the log-linear extrapolation (0.706 at 2000 steps). The measured 200→600 segment
is −0.1303 where the fit predicts ≈−0.55 over the same interval; the fit is dominated by the
5→200 jump and cannot represent the tail.

**Caveat.** Objective space only. Per §2 this licenses **no** behavioural claim — and §8's floor
result is the reason that caveat has teeth: on the behavioural endpoint the compute-matched arms
sit *below* random token strings.

**Caveat.** Objective space only. Per §2 this licenses **no** behavioural claim.

---

## 8. The pool "attack" is mostly a max-statistic artifact, and optimized suffixes barely beat random tokens (§20.5)

**ESTABLISHED.** `asym_p205_bestofk_existing.json` (`provisional: false`, no unmet conditions),
built by `asym_p205_bestofk_existing.py` with the floor from `asym_p205_make_randtok_floor.py`.

§20.5 was carried for weeks as "not started, 4–8 GPU-h". It was not: §7.5's `--mode transfer` runs
had already written a **37×37 source×target grid per (arm, seed)** — 1332 rows across 6 cells
(mechanism and matched_random at seeds 42/43/44) — so the pool statistic computes with **zero GPU**.
ASR@k is exact (`1 − C(n_fail,k)/C(n,k)` per target, then averaged), not resampled.

| arm | seed | ASR@1 | ASR@2 | ASR@1 (maj) | ASR@2 (maj) |
|---|---|---|---|---|---|
| matched_random | 42 | 0.1921 | 0.2485 | 0.1959 | 0.2524 |
| matched_random | 43 | 0.2203 | 0.2964 | 0.2095 | 0.2865 |
| matched_random | 44 | 0.2139 | 0.2740 | 0.2116 | 0.2695 |
| mechanism | 42 | 0.2156 | 0.2956 | 0.1976 | 0.2866 |
| mechanism | 43 | 0.1762 | 0.2706 | 0.1709 | 0.2625 |
| mechanism | 44 | 0.2208 | 0.3525 | 0.2299 | 0.3615 |

*(StrongREJECT ≥ 0.5. "maj" = §20.3's M=5 majority labels substituted for boundary-band rows.)*

**Mean k=2 gain: +0.0831 raw → +0.0839 majority-vote.** All three of the plan's mandatory
conditions are now met; the second was met from disk: §20.3's replicate pool
(`pool_total = 1998`) is the 666 diagonal rows **plus these 1332 transfer rows**, so 66 of its 93
band rows are `xfer_*` and carry M=5 majority labels. The false-positive-accumulation objection —
a max-statistic absorbing judge noise as k grows — **is answered empirically**: 14 individual
labels move and the pooled gain does not. Valid at threshold 0.5 only; §20.3's band was defined as
|score0 − 0.5| ≤ 2 steps.

### The floor, and what it does to that +0.084

A max over more draws rises by construction, so the third mandatory condition — a pool of
**un-optimized** suffixes drawn the same way — is what decides whether +0.084 means anything. No
such pool existed (the only random-ish condition on disk, `neutral_control`, has 20 023 rows over
549 tasks and **0 clearharm**; the `*_rand_*` arms are *optimized* against a random direction,
which is not a floor), so one was generated: **10 suffixes × 37 test prompts = 370 evaluations**,
16 random tokens each drawn uniformly from the ordinary vocabulary, scored through the byte-identical
evaluator path on a **3090** to match the class its pools ran on.

| | ASR@1 | ASR@2 | k=2 gain |
|---|---|---|---|
| arms (majority-vote, mean of 6 cells) | 0.2074 | 0.2913 | **+0.0839** |
| **randtok floor (K=10)** | **0.2351** | 0.2841 | **+0.0489** |
| | | | **excess +0.0350** |

**Roughly 60 % of the apparent pool gain is max-statistic inflation that random suffixes produce
just as readily.** The genuine advantage is **+0.035**, not +0.084.

**The floor also sits above most of the optimized arms.** Per-suffix floor ASR ranges 0.108–0.351
(sd 0.069 over 10 draws; SE of the mean ≈ 0.022), giving a floor of **0.2351 ± ~0.022**:

| condition | ASR | vs floor |
|---|---|---|
| vanilla, 200 steps, diagonal | 0.3333 | **clearly above** |
| mechanism, 200 steps, diagonal | 0.2793 | inside the floor's upper CI |
| matched_random, 200 steps, diagonal | 0.2703 | inside the floor's upper CI |
| all six transfer cells, ASR@1 | 0.171–0.230 | at or **below** |
| all three 5-step (compute-matched) arms | 0.126–0.180 | **below** by 0.07–0.13 |

Three consequences. **Transferred suffixes do not beat random tokens at all** — optimization on
prompt A buys nothing on prompt B. **The compute-matched arms underperform noise**, so §7.5's
compute-matched contrast compared two conditions that are both worse than random. And the floor's
own k-curve reaches **0.3784 at k=10**, so **pooling ten random suffixes beats the best single
optimized suffix** (0.3333). Only the full-budget `vanilla` diagonal clears the floor by a visible
margin.

**Two limitations that constrain what §20.5 can ever say from this grid:**
1. **Balanced k caps at 2.** Off-diagonal pools run 2–11 per target because the grid was sharded
   for eval cost, not designed as a pool; a max over unequal pools is not comparable across
   targets. Larger k means keeping only large-pool targets — a non-random subset. **A real pool
   attack at meaningful k needs a redesigned dense grid**, and its cost must be re-estimated from
   that design.
2. **The vanilla arm has no transfer rows at all**, so nothing from disk can include it.

**Do not cite** `..._with_replacement_ref_NOT_a_floor` from the artifact. It records 1−(1−p)², which
observed ASR@2 exceeds in all 6 cells — an estimator artifact (exact sampling *without* replacement
from pools of 2–11 versus a *with*-replacement reference), not a property of the attack. It is kept
only so the comparison is not re-derived and believed.

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
