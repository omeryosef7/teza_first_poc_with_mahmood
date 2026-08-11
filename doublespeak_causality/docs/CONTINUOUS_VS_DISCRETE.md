# CONTINUOUS vs DISCRETE REACHABILITY

*Asymmetry sprint deliverable (plan §15.3). Companion to `TOKEN_REACHABILITY_ANALYSIS.md`.*
*Figure A quantities were pre-registered in `ASYMMETRY_GAP_MATRIX.md` §E.6 before any Phase-2
run; nothing below was chosen after seeing an outcome.*

---

## 1. The question this phase separates

Three claims are usually collapsed into one:

```
activation-space reachable   ⊇?   continuous-INPUT reachable   ⊇?   discrete-TOKEN reachable
```

The program had established the first (ablating the refusal direction is causal, specific,
dose-dependent, quantization-robust, cross-family) and a negative on the third (a GCG
objective targeting the same direction ≈ a random direction). The middle term had never been
measured, so "the direction is not reachable from the input" and "the direction is not
reachable *by discrete search*" were indistinguishable.

Phase 2 optimizes a **universal 16-position suffix** — the same slot, the same placement, the
same frozen v3 train pool, and the same locked held-out test set the GCG matrix used — in two
progressively more constrained parameterizations:

| parameterization | what it bounds |
|---|---|
| **`free`** — unconstrained vectors in R^d per position, subject to an explicit per-position L2 budget on the perturbation from the initial suffix embedding | an upper bound on **continuous input** reachability |
| **`simplex`** — logits over the vocabulary; the embedding used is the softmax-weighted convex combination of embedding rows. Every real token sequence is a **vertex** of this simplex | an upper bound on **discrete token** reachability |
| **rounding probe** (§19.4) — project the simplex solution to its per-position argmax token and re-evaluate as an ordinary hard prompt | how much of that bound **survives discretization** |

The `simplex` design and its diagnostics (peak weight, blended-position count,
discretization retention, and the logit-budget sufficiency check) are reused from
`$DC/37_soft_prompt_objective.py`, which had already learned that an unconstrained `free`
parameterization makes such a gate vacuous.

**Measured quantity** (pre-registered): refusal projection at the `decision` position (last
prompt token), `hidden_states[19]` for the L18 axis — the position where the axis was fitted,
causally validated, and read out. Behaviour: binary ASR at StrongREJECT ≥ 0.5.

---

## 2. Result 1 — continuous input optimization reaches the direction, and does so SPECIFICALLY

Held-out test (n=37), 300 Adam steps, per-position L2 budget = 1.0 × mean init embedding
norm (binding at every step):

| soft-prompt objective | its own objective reached? | **Δ refusal projection (held-out)** |
|---|---|---|
| refusal direction (job 750364) | yes | **−20.09** |
| norm-matched random direction (job 750365), cos with v_refusal = +0.0055 | yes (own loss −12.8) | **−1.56** |

The optimizer is equally *able* to drive a random direction, so the 13× gap is not an
optimization artifact. For scale, **the entire discrete family** moves this same quantity by
only **−0.43 … −2.60** (execution log §19.1b).

> **Continuous input optimization is specific to the refusal axis. Discrete token
> optimization is at best marginally so** (−2.013 vs −1.204 for its matched random control,
> sign-unstable across seeds).

## 3. Result 2 — but at that dose the projection leaves the regime where it means anything

| pool | baseline | after | Δ | per-prompt sd |
|---|---|---|---|---|
| train (n=40) | +3.365 | −15.787 | −19.15 | 2.909 → **0.380** |
| held-out (n=37) | +4.417 | −15.675 | −20.09 | 2.497 → **0.249** |

**Behaviour: binary ASR = 0.0000, mean continuous StrongREJECT = 0.0000, refusal_rate =
0.0000, empty_rate = 0.0000** (0% null judges; mean response ≈ 501 chars). The model is
neither refusing nor complying.

The per-prompt standard deviation collapsing 2.5 → 0.25 is the tell: the soft prompt is not
*steering* the refusal state along its natural manifold, it is **overwriting** the
decision-position residual with a nearly prompt-independent vector far outside the direction's
natural range (harmful prompts sit at ≈ +3.4 … +4.4).

> **Methodological result worth stating on its own: a continuous soft prompt can drive a
> linear probe arbitrarily far without producing the behaviour the probe is supposed to
> index. Probe displacement is not evidence of mechanism control.**

This is plan §6.4's **CASE D**, which the plan explicitly says to investigate before claiming
a reachability explanation — hence the dose sweep in §5.

## 4. Result 3 — the rounding probe: 94 % of the effect dies on discretization

`simplex`, held-out, baseline **+4.418**:

| state | mean projection | Δ vs baseline | per-prompt sd |
|---|---|---|---|
| relaxed simplex optimum | −4.277 | **−8.694** | 0.178 |
| rounded to nearest tokens | +3.922 | **−0.496** | 2.386 |

> ### RETENTION AFTER DISCRETIZATION = **5.7 %**

Optimizer-validity diagnostics all pass: `budget_sufficient = True` (logit budget 150 ≫ the
2 × init_scale = 20 initialization gap, so the argmax *could* move), 44 % of positions did
change, `mean_peak_weight = 0.755`, `min_peak_weight = 0.070`, **6 of 16 positions blended**
(peak < 0.9). So the relaxed optimum buys its advantage with **off-manifold blending** —
convex combinations of tokens no real prompt can contain — and the rounded result lands
*inside* the range of 20 **unoptimized** random-token suffixes (−0.177 … −1.046).

---

## 5. Dose–response (plan §6.2)

Budget 1.0 saturates, so the budget sweep is the experiment, not a robustness check.
Held-out Δ refusal projection vs per-position L2 budget (as a multiple of the mean init
embedding norm 0.5679):

| budget_rel | L2 radius | Δ proj (held-out) | resulting projection | in natural range? | **ASR** | refusal_rate |
|---|---|---|---|---|---|---|
| 0.05 | 0.0284 | −1.07 | +3.35 | **yes** | 0.135–0.162 | 0.730 |
| **0.10** | 0.0568 | **−8.22** | −3.80 | no | **0.757–0.838** | **0.027** |
| 0.25 | 0.1420 | −8.95 | −4.53 | no | *(not judged)* | — |
| 1.00 | 0.5679 | −20.09 | −15.68 | no | **0.000** | 0.000 |
| *random dir @ 0.10* | 0.0568 | *−2.21* | *+2.21* | *yes* | ***0.081*** | *0.460* |

The ASR/dose relation is an **inverted U**: too little suppression leaves the model refusing
(refusal_rate 0.73 at budget 0.05); the right dose jailbreaks (0.757–0.838 at 0.10); too much
drives the residual so far off-manifold that the model neither refuses nor complies (ASR 0
*and* refusal_rate 0 at 1.00). Note the plateau in Δ projection between 0.10 and 0.25 (−8.22
vs −8.95) before the jump to −20.09 — the projection and the behaviour are not monotonically
linked, which is the same lesson as §3.

ASR ranges are given because two independent judge runs over identical generations disagreed
by up to 3 items in 37 (≈3.4 % per-item flip rate at `temperature=0`); see the execution log
entry on judge nondeterminism. All the differences above are far outside that band.

---

## 6. The control hierarchy (FIGURE A)

Pre-registered arms, all on the same axis (L18 → `hs[19]`), same position (`decision`), same
held-out split (n=37), each with its matched random control:

| arm | medium | scope | Δ refusal projection | specific vs its random control? |
|---|---|---|---|---|
| activation ablation (α=1) | activation | all positions, all layers | complete by construction | **yes** (random-ablation control flat; published) |
| **continuous soft prompt, budget 1.0** | continuous input | 16 suffix positions | **−20.09** | **yes** (−20.09 vs −1.56) |
| **continuous soft prompt, budget 0.10** | continuous input | 16 suffix positions | **−8.22** | **YES — ASR 0.757 vs 0.081 dose-matched random, ΔASR +0.676, p=6e-8** |
| continuous soft prompt, budget 0.05 | continuous input | 16 suffix positions | −1.07 | — |
| **simplex relaxation (token upper bound)** | continuous-in-token-simplex | 16 suffix positions | **−8.69** | — |
| **simplex, rounded to real tokens** | **discrete** | 16 suffix positions | **−0.50** | — |
| GCG refusal-optimized suffix | discrete | 16 suffix positions | −2.01 (3-seed mean) | marginal (vs −1.20; sign flips) |
| GCG random-direction suffix | discrete | 16 suffix positions | −1.20 | — |
| unoptimized random-token suffix | discrete | 16 suffix positions | −0.66 (20 draws) | — |
| GCG init suffix `' !'×16` | discrete | 16 suffix positions | **+1.02** (raises refusal) | — |

**D3 caveat, stated rather than hidden:** the activation arm is all-position / all-layer while
every input arm is 16 suffix positions at the input. That is an intervention-**scope**
difference on top of the medium difference, and it is why the gap between row 1 and row 2 must
not be read as "activation beats continuous input". The scope-matched activation arm
pre-registered in gap-matrix §E.7 is not yet run.

---

## 7. Verdict (Gate D) — FINAL

### The dose-matched specificity test
Budget **0.10** for both arms, same GPU class, same 300 steps, same frozen train pool, same
locked held-out test set (n=37). The only manipulated variable is the targeted direction:

| arm | Δ refusal projection | **binary ASR** | mean continuous SR | refusal_rate |
|---|---|---|---|---|
| **refusal direction** | **−8.22** | **0.7568** | 0.7095 | **0.027** |
| **norm-matched random** (cos = +0.0055) | **−2.21** | **0.0811** | 0.0709 | **0.4595** |

**Paired: ΔASR = +0.676, exact McNemar p = 5.96e-08, bootstrap 95 % CI [+0.514, +0.811].**
An order of magnitude above the measured StrongREJECT judge-noise floor (±0.03–0.08 at n=37).

### Verdict
> **CASE A — DISCRETE-TOKEN BOTTLENECK, with two measured mechanisms and a specific,
> behaviourally effective continuous counterexample.**
>
> * **Continuous input optimization** on the validated causal refusal direction is causal,
>   **specific** (ΔASR +0.676 vs a dose-matched random direction, p = 6e-8) and
>   **behaviourally effective** (ASR 0.757 vs a 0.243–0.351 vanilla baseline and a 0.405
>   best-ever GCG arm), with refusal_rate collapsing 0.46 → 0.03.
> * **Discrete token optimization** on the same direction, axis, position, split and budget
>   is neither: 3-seed mean ΔASR **+0.018** against its matched random control — *below the
>   judge's own noise floor*.
> * **H1 (input-reachability failure) is rejected**: the direction is *unusually easy* to
>   reach, 6.7×/7.1× the covariance-matched null.
> * The discrete failure has two independently measured causes: **the linear surrogate is
>   invalid at one-token step size** (Gate B) and **a perfect continuous solution in the token
>   simplex retains only 5.7 % after rounding** (§19.4).

The hierarchy **activation ⊇ continuous-input ⊇ discrete-token** is established on
**behaviour**, not only on the internal target, with specificity demonstrated at the
continuous level. This is plan §17 **RESULT 2**, in full.

### Confidence levels — these differ and must not be merged
* **CONFIRMATORY (locked test set):** *continuous optimization on the refusal direction
  specifically raises ASR far above a dose-matched random direction.* The contrast is paired
  at a **fixed budget shared by both arms**, so whatever procedure selected 0.10 applied
  identically to mechanism and control and cannot manufacture the difference.
* **EXPLORATORY:** *0.10 is the optimal budget.* The dose sweep was read on test, so this is
  a dose-response curve, not a validated optimum. A confirmatory dose needs freezing on the
  untouched v3 `dev` split (n=37).

### Limitations carried forward
* **Single seed (42)** at the winning dose; plan §6.1 asks for ≥3. Seeds 43/44 were cancelled
  to hold the 6-job cap and are queued.
* **D3 scope caveat:** the activation arm is all-position/all-layer while every input arm is
  16 suffix positions at the input. The scope-matched activation arm (gap matrix §E.7) has
  not been run, so row 1 vs row 2 of Figure A is not a clean medium comparison.
* The judge refused to score one generation ("I'm sorry, I can't assist with that",
  `strong_reject/evaluate.py:195`); it was counted as a parse failure, never silently as
  benign. `judge_null_frac` = 0.00 for both arms.
* The rounding probe measured retention of the **projection**, not of ASR; no generation was
  run with the rounded token suffix.
