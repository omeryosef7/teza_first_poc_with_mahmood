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
band-only design rather than assuming it. Corpus-level two-pass disagreement ≈ **0.62 %**, not
5.4 %; the sprint's cited figure was one arm at n=37 and is not a constant. The judge runs at
`temperature=0`.

**Variance decomposition of a single-pass arm ASR at n=37, p≈0.15:**

| source | SD | share |
|---|---|---|
| sampling (prompt-to-prompt) | **0.0587** | 90–98 % |
| judge (typical / worst case) | 0.0091 / 0.0191 | 2.3 / 9.6 % |

**Sampling dominates judge noise by 3–6×.** Judge noise is real, secondary, and cheaply removable
(majority-vote over M=5 on the 4.65 % band).

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

These nulls rule out **only effects larger than ~0.19–0.27 ASR** — and the Doublespeak effect is
itself that size. Every "no effect" in the write-up must read "no effect larger than ~0.2 ASR
detectable at this n".

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
| binary ASR | 0/18 | 0.677 |
| graded score | 0/18 | 0.585 |

13.6 % tighter → variance ratio 0.746 → **effective n multiplier 1.34×** (n=37 behaves like n≈50).
Expected, because 92.7 % of rows sit at exactly 0.0/1.0, so the graded score is very nearly the
binary one.

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

**Scaling beyond 200 steps — diminishing, saturation NOT established.** Seed 42, interim:

| n paired | 200→600 mean Δ | improved | p | efficiency vs 5→200 |
|---|---|---|---|---|
| 14 | −0.079 | 9/14 | 0.363 | 25× worse per step |
| 18 | −0.122 | 13/18 | 0.133 | 16× worse per step |

Diminishing returns are robust; **saturation is not** — the estimate grew 54 % on four extra
prompts. The 2000-step descope argument rests on *efficiency*, not on "no further gain", and should
be decided at 37/37. **Do not quote** the log-linear extrapolation in the artifact: it is dominated
by the 5→200 jump and cannot represent saturation.

**Status.** 27/74 prompts. Seed 43 shards 2–3 and all of seed 44 owed. All completed runs verified:
600/600 steps, `n_train_tasks == 1`.

**Caveat.** Objective space only. Per §2 this licenses **no** behavioural claim.

---

## What §20 changes about the paper

1. **A necessity/usefulness distinction the program was conflating.** The refusal coordinate is
   necessary for the continuous attack yet useless as an optimization target. This reconciles the
   mechanism-targeting negatives with the mediation result instead of leaving them in tension.
2. **The objective-vs-behaviour dissociation**, distinct from representation-vs-behaviour: a 78 %
   change in the optimized quantity yields an unmeasurable behavioural change.
3. **Every behavioural negative must be restated as a bound** (~±0.2 ASR), because at n=37 the
   design has 0.05 power against its own reported effect size.
4. **Two methodological figures are corrected:** the 5.4 % judge-flip rate (actually ~0.6 % corpus
   two-pass, confined to a 4.65 % boundary band) and the assumption that a graded endpoint would
   restore power (1.34×).
5. **A powered null replaces an uninformative one.** The direction term's uselessness is now
   bounded at ≤23 % of the compute effect on a demonstrably sensitive endpoint, rather than resting
   on a binary-ASR contrast with 0.05 power. Where the behavioural question cannot be answered at
   this corpus size, the objective-space question can be — and the two must be reported as
   different claims (§2).
