# PAPER OUTLINE V2 — after the Asymmetry sprint

*Deliverable §15.8. Supersedes `docs/PAPER_OUTLINE_V1.md`. Written 2026-08-12.*
*Phase 3 is COMPLETE (position-corrected arms + the λ=10 probe). §5.3 is resolved: both
alternatives to §5.2's explanation are ruled out.*

---

## The change from V1

**V1's spine was a negative:** *"a refusal direction is causal in activation space but is not a
usable token-space objective."* That framing had two weaknesses this sprint exposed — the
token-space objective was **misconfigured** (it read a fixed absolute position, correct for 1
of 40 prompts), and the negative's effect size sat **below the judge's own noise floor**, so
it was never measurable at n=37 regardless of mechanism.

**V2's spine is a positive with a mechanism:** *the direction is unusually reachable from the
input and continuous optimization exploits it to jailbreak at ASR 0.78 — the failure is
specific to **discrete** search, and we measure why.*

That converts a "we tried and it didn't work" paper into a "here is where the boundary lies
and here is the quantity that draws it" paper.

---

## Title (working)
**Reachable but not optimizable: a causal refusal direction is easy to steer continuously and
hard to reach with discrete tokens**

## Abstract (one paragraph, from the claim table)
> A linear refusal direction in Llama-3.1-8B is causal in activation space, and it is
> **unusually easy to reach from input embeddings** — 4.7× more sensitive to suffix
> perturbations than a covariance-matched control and 14× more than an isotropic one, at
> percentile ≥ 0.99 on both splits. A continuous 16-position soft prompt targeting it reaches
> **ASR 0.78** on a locked held-out set versus **0.15** for a dose-matched random direction
> (mean ΔASR **+0.63** over three seeds, no sign flips, all p < 1e-4). Yet a discrete GCG
> suffix targeting the *same* direction performs like a random direction (mean ΔASR **+0.018**
> — below the StrongREJECT judge's own label-flip noise). The gap is not reachability. We show
> two measured causes: the **first-order surrogate discrete search depends on is invalid at
> the granularity of a single token** (r = 0.84 at a tenth of a token-step, ≈ 0 at a full one),
> and a **perfect solution inside the token simplex retains only 5.7 % of its effect once
> rounded** to real tokens. Interpretability-derived directions can be genuine causal handles
> and still be unusable by the discrete optimizers red-teaming actually runs.

---

## 1. Introduction
The interpretability-guided-security promise: if a jailbreak's mechanism is a decodable
internal direction, it should guide both attack and defense. We test that promise end to end
and find the promise holds for **intervention** and for **continuous** input control, and
breaks for **discrete** search — with a measurable reason.

## 2. Background
Doublespeak / in-context representation hijacking (arXiv 2512.03771); refusal directions
(Arditi/RepE diff-of-means); GCG; StrongREJECT. Prior program result: the concept circuit is
real but behaviourally epiphenomenal, and refusal suppression is the causal locus.

## 3. Setup
ClearHarm **v3 leakage-0** (cluster-disjoint; train pool 40 frozen, dev 37 untouched, test 37
locked). Llama-3.1-8B-Instruct bf16 primary; Phi-4-mini-reasoning cross-family. Refusal axis
L18 → `hs[19]`, fitted at the decision token. **StrongREJECT ≥ 0.5** throughout.

### 3.1 Measurement hygiene (a short subsection that earns its space)
Three things we had to fix before any number meant what it said, each of which is a general
hazard:
* a representation objective that read **one absolute token index** taken from the first
  training example (correct for 1 of 40 prompts, silently zero for another);
* **two different ASR thresholds** (0.25 / 0.5) reported under one name — recomputable from
  stored continuous scores, and conclusion-neutral here (27 contrasts, 0 sign flips);
* a **judge that flips ~3.4 % of labels between runs** at `temperature=0`, giving ±0.03–0.08
  on ASR at n=37 — which is larger than several previously reported effects.

## 4. The direction is unusually reachable (Gate C)
`‖Jᵀv‖` against four control families; **4.71× / 4.91×** (train / test) the corrected
covariance-matched control, percentile 0.990; **14.1× / 14.9×** isotropic. Replicates on
**Phi** (5.56×, pct 1.000) and under **4-bit NF4** (13.25×, pct 1.000).
**Figure B.** → H1 (input-reachability failure) is rejected.

*Includes the negative result that the naive covariance-matched control is rank-1 degenerate
(97–99 % mutually parallel) — a trap for anyone building "in-distribution random" controls.*

## 5. The medium matters
### 5.1 Continuous input control works, and is specific (Gate D) — **the paper's centrepiece**
Universal 16-position soft prompt, dose-matched arms. **ASR 0.78 vs 0.15**, ΔASR **+0.63**,
3 seeds, 2 GPU classes, no sign flips, all p < 1e-4. Inverted-U dose response; at excessive
dose the projection moves −20 and behaviour **collapses to neither refusing nor complying** —
probe displacement is not mechanism control. **Figure A.**

### 5.2 Discrete search does not (and why)
* **Gate B / the ε-scan.** r = 0.84 at ε = 0.10 → ≈ 0 / −0.32 at ε = 1.0 (one real token
  substitution) — *worse* than a covariance-matched null. **Figure B2.**
* **The rounding probe.** Token-simplex optimum retains **5.7 %** after discretization; the
  rounded result lands inside the range of *unoptimized* random-token suffixes.
* **Cross-family scope, stated in the paper body.** On Phi (both splits) the surrogate
  degrades substantially but does not collapse (0.535→0.214 train, 0.567→0.125 test). So H2′'s
  **qualitative core** — most surrogate validity is lost before one-token step size — holds in
  both families, while its **sharp form** — the mechanism ends up worse-predicted than a
  matched null — is **Llama-only**.

### 5.3 Was the discrete negative just a bug, or just a weak λ? *(Phase 3 — RESOLVED)*
Two alternatives to §5.2's explanation are now ruled out on independent grounds.

**(a) The position defect.** The published objective read one absolute token index taken from
`train_tasks[0]` — the intended token for 1 of 40 prompts. Re-running it position-corrected,
everything else identical, changed the behavioural result by **+0.009 vs +0.018** — i.e. nothing,
both sign-unstable. The defect was a **confound, not the cause**.

**(b) The objective was too weakly weighted.** At the published λ=0.25 the mechanism term is only
**0.370 %** of the loss candidate selection minimizes, so the negative might have meant only "this
λ is too small." Re-run at **λ=10 (≈40×)**, 3 seeds: ΔASR **+0.622 / −0.162 / +0.189** — **sign
consistency 2/3, FAILS.** At λ=10 the term carries **24–34 %** of the selection loss and drives the
held-out projection past zero in all three seeds, so the objective demonstrably *works internally*;
behaviour simply does not follow stably. All three |ΔASR| exceed the judge noise floor, so the
instability is **real, not measurement noise**.

*A methodological point worth the space:* the random arms span **0.054–0.351 (6.5×)**, so the one
spectacular seed (+0.622, p=1.6e-06) owes as much to an unusually **weak random arm** as to a
strong mechanism arm. Reporting ΔASR alone would have hidden that, and a mean over three
sign-disagreeing seeds (+0.216) estimates nothing.

**So §5.2 stands as the explanation**, and it now survives both of its sharpest alternatives.

### 5.4 Is the failure about UNIVERSALITY? (§7.5, per Mahmood) — **no**
The negative is a *universal*-suffix result, so we tested the easier per-prompt threat model: one
suffix optimized per prompt, 3 arms × 3 seeds, at the full budget **and** at a compute-matched
budget (the full-budget arm spends ~37× the universal arm's compute, so the matched arm is what
makes the comparison legitimate — the random arm alone gains **+0.216 ASR** from that compute).

* **Behaviour:** ΔASR sign-inconsistent at both budgets, 0/3 significant; neither direction arm
  reliably beats plain task-loss GCG.
* **Transfer:** per-prompt suffixes transfer (off-diagonal 0.173–0.200 ≥ universal held-out 0.162),
  and their prompt-specificity is matched by a random direction.
* **Mechanism:** the projection endpoint is **3/3 sign-consistent** (mean −0.354, Holm-surviving in
  one seed).

**So the representation moves and the behaviour does not — a cleaner dissociation than §5.1's,
with optimizer, budget and prompts held identical.** Removing the universality constraint does not
rescue the objective; the failure is downstream of the representation.

## 6. Generality of the causal locus (Gate F)
Refusal ablation raises ASR on **5/5** concept pairs (median specific ΔASR **+0.414**, 4/5
significant after Holm) using the frozen concept-agnostic axis. Concept-circuit ablation is
null everywhere — **but only 1 of 5 pairs had enough attack headroom for that null to mean
anything**, so we claim generality for the actuator and *not* for the dissociation.
**Figure D.**

## 7. The defense does not follow (Gate G)
Concept-as-detector + refusal-as-actuator. On train the two-signal gate appears to
Pareto-dominate; **the Bernoulli and shuffled-feature controls match its over-refusal
saving**, and on test nothing reduces ASR against a floor baseline. Honest negative, and a
demonstration of why the controls were necessary. **Figure E.**

## 8. Limitations
Held-out n = 37–42 with a ±0.03–0.08 judge band; one base point for the geometry; the
scope-matched activation arm (all-position/all-layer vs 16 input positions) not run; the
optimal continuous dose was read on test and is exploratory; the concept circuit ablated is
bomb-localized; H2′ is not cross-family.

## 9. Conclusion
Intervening on a direction, steering it from the input, and optimizing tokens toward it are
three different capabilities with three different difficulties. The first two work. The third
fails for a reason we can measure, and that reason is a property of the discrete step size,
not of the direction.

---

## Figure list
| # | Content | Status |
|---|---|---|
| A | activation vs continuous vs discrete (Δprojection ‖ ΔASR) | done |
| B | ‖Jᵀv‖ vs four control families, both splits | done |
| B2 | ε-scan — the surrogate's collapse before token scale | done |
| C | cross-prompt gradient coherence | done |
| D | multi-concept dissociation with power grading | done |
| E | defense Pareto with matched controls | done |

## What a reviewer will ask, and where it is answered
1. *"Is the continuous result just a bigger perturbation budget?"* — §5.1 dose-matched arms.
2. *"Is your random control fair?"* — §4, four families, incl. the degeneracy correction.
3. *"Did you just misconfigure GCG?"* — §5.3, the pre-registered position-corrected re-run.
4. *"Does the judge support these differences?"* — §3.1, the measured noise floor.
5. *"Does any of it generalize?"* — §6 (yes, for the actuator), §4 (yes, cross-family and
   cross-precision), §5.2 (**no** for the surrogate-invalidity mechanism).
